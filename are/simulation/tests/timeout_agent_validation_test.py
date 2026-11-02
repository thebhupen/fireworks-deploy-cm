# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Test that agent validation timeout works as expected for different timescales
"""

import datetime
from dataclasses import field
from typing import cast

from are.simulation.apps.system import SystemApp
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.scenarios.scenario import Scenario, ScenarioValidationResult
from are.simulation.types import (
    AbstractEnvironment,
    AbstractEvent,
    AgentValidationEvent,
    CapabilityTag,
    EventRegisterer,
)

time_units_to_value_in_seconds = {
    "seconds": 1,
    "hours": 3600,
}


def get_time_delta(value, time_increment_in_seconds):
    return datetime.timedelta(seconds=value * time_increment_in_seconds)


class ScenarioTestTimeoutAgentValidationMilestone(Scenario):
    """
    The agent should call get_current_time() before the agent validation timeout.
    """

    scenario_id: str = "scenario_test_timeout_agent_validation_milestone"
    start_time: float | None = 0
    duration: float | None = 10
    time_increment_in_seconds: int = 1
    tags: tuple[CapabilityTag, ...] = (CapabilityTag.Planning,)
    test_case: str = field(default="correct")

    def init_and_populate_apps(self, *args, **kwargs) -> None:
        self.apps = [SystemApp()]

    def agent_validation_milestone(self, absolute_time, timeout):
        def val_func(env: AbstractEnvironment, event: AbstractEvent) -> bool:
            try:
                if hasattr(event, "action") and hasattr(event.action, "app"):  # type: ignore
                    return event.action.app.__class__.__name__ == SystemApp.__name__  # type: ignore
                else:
                    return False
            except Exception:
                return False

        event_val = AgentValidationEvent(
            milestones=[val_func],
            timeout=timeout,
        ).at_absolute_time(absolute_time)

        return event_val

    # Build the scenario by defining events and actions
    def build_events_flow(self) -> None:
        system = cast(SystemApp, self.get_typed_app(SystemApp))

        d_events = dict()

        with EventRegisterer.capture_mode():
            next_dt = datetime.datetime.fromtimestamp(
                self.start_time or 0, tz=datetime.timezone.utc
            ) + get_time_delta(2, self.time_increment_in_seconds)
            if self.test_case == "correct":
                delayed_dt = next_dt + get_time_delta(
                    2, self.time_increment_in_seconds
                )  # this is within the timeout
                d_events["on_time_correct_oracle"] = (
                    system.get_current_time()
                    .oracle()
                    .at_absolute_time(delayed_dt.timestamp())
                )
            elif self.test_case == "incorrect":
                delayed_dt = next_dt + get_time_delta(
                    8, self.time_increment_in_seconds
                )  # this exceeds the timeout
                d_events["delayed_incorrect_oracle"] = (
                    system.get_current_time()
                    .oracle()
                    .at_absolute_time(delayed_dt.timestamp())
                )

            d_events["agent_validation"] = self.agent_validation_milestone(
                absolute_time=next_dt.timestamp(), timeout=5
            )
            self.events = [e.with_id(key) for key, e in d_events.items()]


class ScenarioTestTimeoutAgentValidationMinefield(Scenario):
    """
    The agent should not call get_current_time() after the agent minefield field starts, but can do it after the timeout.
    """

    scenario_id: str = "scenario_test_timeout_agent_validation_minefield"
    start_time: float | None = 0
    duration: float | None = 10
    time_increment_in_seconds: int = 1
    tags: tuple[CapabilityTag, ...] = (CapabilityTag.Planning,)
    test_case: str = field(default="correct")

    def init_and_populate_apps(self, *args, **kwargs) -> None:
        self.apps = [SystemApp()]

    def agent_validation_minefield(self, timeout):
        def val_func(env: AbstractEnvironment, event: AbstractEvent) -> bool:
            try:
                if hasattr(event, "action") and hasattr(event.action, "app"):  # type: ignore
                    return event.action.app.__class__.__name__ == SystemApp.__name__  # type: ignore
                else:
                    return False
            except Exception:
                return False

        event_val = AgentValidationEvent(
            minefields=[val_func],
            timeout=timeout,
        )

        return event_val

    # Build the scenario by defining events and actions
    def build_events_flow(self) -> None:
        system = cast(SystemApp, self.get_typed_app(SystemApp))

        d_events = dict()

        with EventRegisterer.capture_mode():
            d_events["agent_minefield"] = self.agent_validation_minefield(
                timeout=5,
            )
            if self.test_case == "correct":
                correct_dt = datetime.datetime.fromtimestamp(
                    self.start_time or 0, tz=datetime.timezone.utc
                ) + get_time_delta(6, self.time_increment_in_seconds)
                d_events["on_time_correct_oracle"] = (
                    system.get_current_time()
                    .oracle()
                    .at_absolute_time(correct_dt.timestamp())
                )
            elif self.test_case == "incorrect":
                incorrect_dt = datetime.datetime.fromtimestamp(
                    self.start_time or 0, tz=datetime.timezone.utc
                ) + get_time_delta(1, self.time_increment_in_seconds)
                d_events["incorrect_oracle"] = (
                    system.get_current_time()
                    .oracle()
                    .at_absolute_time(incorrect_dt.timestamp())
                )

            self.events = [e.with_id(key) for key, e in d_events.items()]


def run_scenario(
    scenario: Scenario,
) -> tuple[str, Exception | None, ScenarioValidationResult | None]:
    print(f"\n\nRunning scenario: {scenario.scenario_id}")
    print(scenario)

    scenario.initialize()
    env = Environment(
        EnvironmentConfig(
            oracle_mode=True,
            queue_based_loop=False,
            time_increment_in_seconds=scenario.time_increment_in_seconds,
            start_time=scenario.start_time,
        )
    )
    try:
        env.run(scenario, wait_for_end=False)
        env.join()
        val_result: ScenarioValidationResult = scenario.validate(env)
        return scenario.scenario_id, None, val_result
    except Exception as e:
        return scenario.scenario_id, e, None


def test_agent_validation_timeout_milestone():
    for unit, time_increment_in_seconds in time_units_to_value_in_seconds.items():
        scenario = ScenarioTestTimeoutAgentValidationMilestone()
        scenario.start_time = 0
        scenario.duration = 10 * time_increment_in_seconds
        scenario.time_increment_in_seconds = time_increment_in_seconds
        scenario.test_case = "correct"
        scenario.initialize()
        name, exception, val_result = run_scenario(scenario)
        if val_result is None:
            assert False, f"Scenario {name} finished with no validation result"
        assert exception is None and val_result.success, (
            f"Scenario {name} with time increments in {unit} with correct oracle failed with exception {exception}"
        )

        scenario.initialize()
        scenario = ScenarioTestTimeoutAgentValidationMilestone()
        scenario.start_time = 0
        scenario.duration = 10 * time_increment_in_seconds
        scenario.time_increment_in_seconds = time_increment_in_seconds
        scenario.test_case = "incorrect"
        name, exception, val_result = run_scenario(scenario)
        if val_result is None:
            assert False, f"Scenario {name} finished with no validation result"
        assert exception is not None or val_result.success is False, (
            f"Scenario {name} with time increments in {unit} with incorrect oracle passed when it should have failed with timeout exception"
        )


def test_agent_validation_timeout_minefield():
    for unit, time_increment_in_seconds in time_units_to_value_in_seconds.items():
        scenario = ScenarioTestTimeoutAgentValidationMinefield()
        scenario.start_time = 0
        scenario.duration = 10 * time_increment_in_seconds
        scenario.time_increment_in_seconds = time_increment_in_seconds
        scenario.test_case = "correct"
        scenario.initialize()
        name, exception, val_result = run_scenario(scenario)
        if val_result is None:
            assert False, f"Scenario {name} finished with no validation result"
        assert exception is None and val_result.success, (
            f"Scenario {name} with time increments in {unit} with correct oracle failed with exception {exception}"
        )

        scenario.initialize()
        scenario = ScenarioTestTimeoutAgentValidationMinefield()
        scenario.start_time = 0
        scenario.duration = 10 * time_increment_in_seconds
        scenario.time_increment_in_seconds = time_increment_in_seconds
        scenario.test_case = "incorrect"
        name, exception, val_result = run_scenario(scenario)
        if val_result is None:
            assert False, f"Scenario {name} finished with no validation result"
        assert exception is not None or val_result.success is False, (
            f"Scenario {name} with time increments in {unit} with incorrect oracle passed when it should have failed with timeout exception"
        )


if __name__ == "__main__":
    # PYTHONPATH='.' python are.simulation/tests/timeout_agent_validation_test.py
    # test_agent_validation_timeout_milestone()
    test_agent_validation_timeout_minefield()
