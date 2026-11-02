# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from are.simulation.apps.contacts import Contact
from are.simulation.scenarios.scenario import Scenario
from are.simulation.scenarios.validation_result import ScenarioValidationResult
from are.simulation.types import (
    AbstractEnvironment,
    CompletedEvent,
    CompletedOracleEvent,
    EventType,
)
from are.simulation.validation.configs import (
    BaseEventJudgeConfig,
    BaseJudgeConfig,
    BaseToolJudgeConfig,
)
from are.simulation.validation.judgment import Judgment
from are.simulation.validation.utils.trace_utils import injected_traceable

logger: logging.Logger = logging.getLogger(__name__)

from are.simulation.agents.agent_log import ErrorLog


@dataclass
class BaseJudgeState:
    # Flag if initialized
    initialized: bool = False
    # Turn
    nb_turns: int = -1
    turn_idx: int = -1
    last_turn_success: bool = True
    last_turn_rationale: str = ""
    # Scenario data
    scenario_start_time: float = 0.0
    scenario_tasks: list[str] = field(default_factory=list)
    user_details: Contact | None = None
    # Oracle events
    turn_to_oracle_events: list[list[CompletedOracleEvent]] = field(
        default_factory=list
    )
    turn_to_oracle_graph: list[dict[str, list[str]]] = field(default_factory=list)
    oracle_event_id_to_turn_idx: dict[str, int] = field(default_factory=dict)
    # Agent events
    turn_to_agent_events: list[list[CompletedEvent]] = field(default_factory=list)

    @property
    def agent_events(self) -> list[CompletedEvent]:
        return [event for events in self.turn_to_agent_events for event in events]

    @property
    def current_turn_agent_events(self) -> list[CompletedEvent]:
        return self.turn_to_agent_events[self.turn_idx]

    @property
    def current_turn_oracle_events(self) -> list[CompletedOracleEvent]:
        return self.turn_to_oracle_events[self.turn_idx]

    @property
    def current_turn_oracle_graph(self) -> dict[str, list[str]]:
        return self.turn_to_oracle_graph[self.turn_idx]


class BaseJudge(ABC):
    """
    Base class for a judge. A judge compares an agent and oracle event log for a given scenario.
    """

    def __init__(self, config: BaseJudgeConfig):
        self.tracer = config.tracer
        self.state = BaseJudgeState()
        self.error_logs: list[ErrorLog] = []

    @abstractmethod
    def initialize_state(self, scenario: Scenario) -> None:
        pass

    @abstractmethod
    def __call__(self, env: AbstractEnvironment) -> Judgment:
        pass

    def validate(self, env: AbstractEnvironment) -> ScenarioValidationResult:
        if not self.state.initialized:
            raise ValueError("Judge must be initialized before validation")

        # Early returns for failure conditions
        if not self.state.last_turn_success:
            logging.warning("Last turn was already rejected, skipping validation")
            return ScenarioValidationResult(
                success=False, rationale=self.state.last_turn_rationale
            )

        is_last_turn = (self.state.turn_idx + 1) == (self.state.nb_turns - 1)
        if not is_last_turn:
            logging.info(
                f"Validation called at turn {self.state.turn_idx} but nb_turns is {self.state.nb_turns}"
            )

            # Use the injected_traceable decorator for tracing
            @injected_traceable(
                trace_type="judge", tags=["judge"], log_input_args=False
            )
            def inner_call(self) -> Judgment:
                return Judgment(
                    success=False,
                    failure=f"Validation called at turn {self.state.turn_idx} but nb_turns is {self.state.nb_turns}",
                )

            judgment = inner_call(self)
            return ScenarioValidationResult(
                success=False, rationale=str(judgment.failure)
            )

        # Judge the current turn (last turn)
        return self.validate_current_turn(env)

    def validate_current_turn(
        self, env: AbstractEnvironment
    ) -> ScenarioValidationResult:
        if not self.state.initialized:
            raise ValueError("Judge must be initialized before validation")
        try:
            judgment = self(env)
        except Exception as e:
            self.error_logs.append(
                ErrorLog(
                    error=str(type(e).__name__),
                    exception=str(e),
                    category=type(e).__name__,
                    agent=self.__class__.__name__,
                    timestamp=env.time_manager.time(),
                    agent_id="unknown",
                )
            )
            logger.error(e)
            return ScenarioValidationResult(
                success=False, exception=e, rationale="Exception"
            )
        return ScenarioValidationResult(
            success=bool(judgment.success),
            rationale=str(judgment.failure),
        )

    def trigger_condition(
        self, env: AbstractEnvironment, turn_idx: int
    ) -> tuple[bool, dict[str, str]]:
        judgment = self(env)
        return bool(judgment.success), judgment.agent_event_id_to_oracle_event_id


class ToolJudge(ABC):
    """
    Base class for a tool judge. A tool judge compares a agent and oracle event representing a tool call.
    It decides if the two actions of the events, representing a tool call match.
    """

    def __init__(self, config: BaseToolJudgeConfig, judge_type: str) -> None:
        self.tool_name = config.tool_name
        self.judge_type = judge_type
        self.tracer = config.tracer

    @abstractmethod
    def compare(
        self, agent_event: CompletedEvent, oracle_event: CompletedOracleEvent, **kwargs
    ) -> bool | None:
        pass

    def __call__(
        self, agent_event: CompletedEvent, oracle_event: CompletedOracleEvent, **kwargs
    ) -> bool | None:
        @injected_traceable(
            trace_type=f"{self.judge_type}_judge", tags=["judge"], log_input_args=False
        )
        def inner_call(
            self,
            agent_event: CompletedEvent,
            oracle_event: CompletedOracleEvent,
            **kwargs,
        ) -> bool | None:
            # Check tool name
            agent_tool_name = agent_event.tool_name
            oracle_tool_name = oracle_event.tool_name
            if oracle_tool_name != self.tool_name:
                raise ValueError(
                    f"Oracle tool name {oracle_tool_name} does not match config tool name {self.tool_name}"
                )
            if agent_tool_name != oracle_tool_name:
                return False

            return self.compare(agent_event, oracle_event, **kwargs)

        return inner_call(self, agent_event, oracle_event, **kwargs)


class EventJudge(ABC):
    """
    Base class for an event judge. An event judge compares a agent and oracle events and decides if the two match.
    """

    def __init__(
        self, config: BaseEventJudgeConfig, event_type: EventType, judge_type: str = ""
    ) -> None:
        self.judge_type = judge_type
        self.event_type = event_type
        self.tracer = config.tracer

    @abstractmethod
    def compare(
        self, agent_event: CompletedEvent, oracle_event: CompletedOracleEvent, **kwargs
    ) -> bool | None:
        pass

    def __call__(
        self, agent_event: CompletedEvent, oracle_event: CompletedOracleEvent, **kwargs
    ) -> bool | None:
        oracle_agent_tool_name = oracle_event.tool_name
        agent_event_tool_name = agent_event.tool_name
        if oracle_agent_tool_name != agent_event_tool_name:
            # We reject if the tool are not the same.
            # This should be done at the tool judge level but we do it here for cleaner logging.
            return False

        trace_type = f"{oracle_agent_tool_name}_vs_{agent_event_tool_name}"

        @injected_traceable(trace_type=trace_type, tags=["judge"], log_input_args=False)
        def inner_call(
            self,
            agent_event: CompletedEvent,
            oracle_event: CompletedOracleEvent,
            **kwargs,
        ) -> bool | None:
            # Check event type
            if oracle_event.event_type != self.event_type:
                raise ValueError(
                    f"Oracle type {oracle_event.event_type.value} does not match config type {self.event_type.value}"
                )
            if agent_event.event_type != oracle_event.event_type:
                return False

            return self.compare(agent_event, oracle_event, **kwargs)

        return inner_call(self, agent_event, oracle_event, **kwargs)
