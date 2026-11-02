# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from collections import defaultdict, deque
from typing import Callable

from are.simulation.data_handler.models import ExportedHuggingFaceMetadata
from are.simulation.scenarios.scenario import Scenario, ScenarioValidationResult
from are.simulation.scenarios.utils.turn_conditions import (
    is_send_message_to_user,
    turn_condition_wrapper,
)
from are.simulation.types import (
    AbstractEnvironment,
    AbstractEvent,
    CompletedEvent,
    ConditionCheckEvent,
    OracleEvent,
)

from .scenario import ScenarioImportedFromJson

logger = logging.getLogger(__name__)


def build_event_id_to_turn_idx(
    scenario: Scenario,
    is_end_of_turn_event: Callable[[AbstractEvent], bool] = is_send_message_to_user,
):
    """
    Build a dictionary to store the turn of each event
    The turn of an event is the number of event send_message_to_user among its ancestors
    The dictionary and the number of turns are stored to the scenario
    Args:
        scenario (Scenario): The scenario object.
    """
    if scenario.events is None:
        raise ValueError("Events not found")
    visited_events = set()
    # Initialize a dictionary to store the turn of each event
    event_id_to_turn_idx = defaultdict(lambda: 0)
    # Initialize a queue with event without dependencies
    queue = deque([e for e in scenario.events if not e.dependencies])
    # Perform BFS on events
    while queue:
        event = queue.popleft()
        # If the event has not been visited yet
        if event.event_id not in visited_events:
            event_id_to_turn_idx[event.event_id] = 0
            # Mark it as visited
            visited_events.add(event.event_id)
            if event.dependencies:
                event_id_to_turn_idx[event.event_id] = max(
                    [event_id_to_turn_idx[e.event_id] for e in event.dependencies],
                )
                # Check if there is a end of turn event among the dependencies
                if any(
                    is_end_of_turn_event(e)
                    for e in event.dependencies  # type: ignore
                ):
                    event_id_to_turn_idx[event.event_id] += 1
            # Add the successors to the queue
            queue.extend(
                e for e in event.successors if e.event_id not in visited_events
            )
    # Convert the defaultdict back to a regular dictionary
    event_id_to_turn_idx = dict(event_id_to_turn_idx)
    # Set the number of turns
    nb_turns = (max(event_id_to_turn_idx.values()) if event_id_to_turn_idx else 0) + 1
    # Append event_id_to_turn_idx and number of turn to scenario
    scenario.nb_turns = nb_turns  # type: ignore
    scenario.event_id_to_turn_idx = event_id_to_turn_idx  # type: ignore


class BenchmarkScenarioImportedFromJson(ScenarioImportedFromJson):
    """
    This is a special class used for importing scenarios from JSON files.
    """

    # Multi turn parameters
    nb_turns: int | None = None  # Number of turns in the scenario
    event_id_to_turn_idx: dict[str, int] | None = (
        None  # Dictionary to store the turn of each event
    )
    oracle_run_event_log: list[CompletedEvent] | None = (
        None  # Event log of a run in oracle mode
    )
    _turns_initialized: bool = False
    hf_metadata: ExportedHuggingFaceMetadata | None = None

    def build_turn_trigger(
        self,
        trigger_condition: Callable[
            [AbstractEnvironment, int], tuple[bool, dict[str, str]]
        ],
        is_end_of_turn_event: Callable[[AbstractEvent], bool] = is_send_message_to_user,
    ):
        """
        Modify the events to trigger the turns with trigger condition
        """
        assert self.event_id_to_turn_idx is not None, "Turn index must be set"
        # Get all end of turn events
        end_of_turn_events = {
            self.event_id_to_turn_idx[event.event_id]: event
            for event in self.events
            if is_end_of_turn_event(event)
        }
        d_events = dict()
        # Build the turn trigger events
        assert self.nb_turns is not None, "Number of turns must be set"
        for turn_idx in range(1, self.nb_turns):
            # Get dependencies
            dependencies = (
                d_events[f"condition_turn_{turn_idx - 1}"] if turn_idx > 1 else None
            )
            # Get successors
            successors = end_of_turn_events[turn_idx - 1].successors[:]
            if any(isinstance(e, OracleEvent) for e in successors):
                raise ValueError(
                    f"Scenario {self.scenario_id} has a end of turn event with oracle successors"
                )
            # Remove end of turn events from successors
            for successor_event in successors:
                successor_event.dependencies = [
                    e
                    for e in successor_event.dependencies
                    if not is_end_of_turn_event(e)
                ]
            # Build a condition for the turn
            d_events[f"condition_turn_{turn_idx}"] = (
                ConditionCheckEvent.from_condition(
                    condition=turn_condition_wrapper(
                        trigger_condition=trigger_condition,
                        turn_idx=turn_idx,
                        scenario_id=self.scenario_id,
                    ),  # type: ignore
                    every_tick=1,
                    timeout=None,
                )
                .with_id(f"condition_turn_{turn_idx}")
                .depends_on(dependencies)
                .followed_by(
                    events=successors,
                    delay_seconds=[
                        (
                            e.event_relative_time
                            if e.event_relative_time is not None
                            else 0.0
                        )
                        for e in successors
                    ],
                )
            )
        # Check that all non oracle events do not depend on any oracle event
        for event in self.events:
            if type(event) is not OracleEvent and event.dependencies:
                # Non oracle events must not depend on any oracle event now
                if any(type(e) is OracleEvent for e in event.dependencies):
                    raise ValueError(
                        f"Event {event.event_id} depends on an oracle event. This is not expected."
                    )
        # Update the events
        for key, event in d_events.items():
            self.events.append(event.with_id(key))

    def build_validation_fn(
        self,
        validation_fn: Callable[[AbstractEnvironment], ScenarioValidationResult],
        offline_validation: bool = False,
    ):
        """
        Build a validation function for the scenario
        """

        def online_wrapped_validation_fn(
            env: AbstractEnvironment,
        ) -> ScenarioValidationResult:
            """
            Perform the validation only for the last turn of the scenario
            since in the online mode, a validation is performed at the end of each turn
            in the trigger condition.
            """
            return validation_fn(env)

        def offline_wrapped_validation_fn(
            env: AbstractEnvironment,
        ) -> ScenarioValidationResult:
            """
            Perform the validation for all the turns of the scenario
            since in the offline mode, no intermediate validation is performed
            between the turns.
            """
            assert self.nb_turns is not None, "Number of turns must be set"
            # Evaluate all the turns
            result = ScenarioValidationResult(success=False)
            for turn_idx in range(self.nb_turns):
                logger.info(f"Validating turn {turn_idx + 1} / {self.nb_turns}")
                # We expect that validation_fn at each call validates the current turn
                # and updates its internal state to evaluate the next turn at the next call
                result = validation_fn(env)
                if not result.success:
                    return result
            return result

        self.validate = (
            offline_wrapped_validation_fn
            if offline_validation
            else online_wrapped_validation_fn
        )

    def initialize_turns(
        self,
        trigger_condition: (
            Callable[[AbstractEnvironment, int], tuple[bool, dict[str, str]]] | None
        ) = None,
        validation_fn: (
            Callable[[AbstractEnvironment], ScenarioValidationResult] | None
        ) = None,
        is_end_of_turn_event: Callable[[AbstractEvent], bool] = is_send_message_to_user,
        offline_validation: bool = False,
    ):
        """
        Initialize the turns.
        """
        if not self._initialized:
            raise ValueError("Scenario must be initialized before initializing turns")
        if self._turns_initialized:
            return
        # Build the event id to turn index dictionary
        build_event_id_to_turn_idx(
            scenario=self,
            is_end_of_turn_event=is_end_of_turn_event,
        )
        # Modify the events graph to trigger turns
        if trigger_condition is not None:
            self.build_turn_trigger(
                trigger_condition=trigger_condition,
                is_end_of_turn_event=is_end_of_turn_event,
            )
        else:
            logger.warning(
                "Trigger condition is not provided. Building turn triggers is skipped"
            )
        # Build the validation function
        if validation_fn is not None:
            self.build_validation_fn(
                validation_fn, offline_validation=offline_validation
            )
        else:
            logger.warning(
                "Validation function is not provided. Building validation function is skipped"
            )
            # Add dummy validation function
            self.validate = lambda env: ScenarioValidationResult(success=None)
        # Set the flag
        self._turns_initialized = True
