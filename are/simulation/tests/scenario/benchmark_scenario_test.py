# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from unittest.mock import MagicMock, patch

import pytest

from are.simulation.scenarios.scenario import ScenarioValidationResult
from are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario import (
    BenchmarkScenarioImportedFromJson,
    build_event_id_to_turn_idx,
    is_send_message_to_user,
)
from are.simulation.types import AbstractEnvironment, OracleEvent


class TestBuildEventIdToTurnIdx:
    def test_empty_events(self):
        """Test build_event_id_to_turn_idx with empty events."""
        scenario = MagicMock()
        scenario.events = []

        build_event_id_to_turn_idx(scenario)

        assert scenario.nb_turns == 1
        assert scenario.event_id_to_turn_idx == {}

    def test_single_event_no_dependencies(self):
        """Test build_event_id_to_turn_idx with a single event with no dependencies."""
        scenario = MagicMock()
        event = MagicMock()
        event.event_id = "event1"
        event.dependencies = []
        scenario.events = [event]

        build_event_id_to_turn_idx(scenario)

        assert scenario.nb_turns == 1
        assert scenario.event_id_to_turn_idx == {"event1": 0}

    def test_multiple_events_with_dependencies(self):
        """Test build_event_id_to_turn_idx with multiple events with dependencies."""
        scenario = MagicMock()

        # Create events
        event1 = MagicMock()
        event1.event_id = "event1"
        event1.dependencies = []

        event2 = MagicMock()
        event2.event_id = "event2"
        event2.dependencies = [event1]

        event3 = MagicMock()
        event3.event_id = "event3"
        event3.dependencies = [event2]

        # Set up successors
        event1.successors = [event2]
        event2.successors = [event3]
        event3.successors = []

        scenario.events = [event1, event2, event3]

        build_event_id_to_turn_idx(scenario)

        assert scenario.event_id_to_turn_idx == {"event1": 0, "event2": 0, "event3": 0}
        assert scenario.nb_turns == 1

    def test_with_send_message_to_user_event(self):
        """Test build_event_id_to_turn_idx with a send_message_to_user event."""
        scenario = MagicMock()

        # Create events
        event1 = MagicMock()
        event1.event_id = "event1"
        event1.dependencies = []

        # Mock send_message_to_user event
        event2 = MagicMock()
        event2.event_id = "event2"
        event2.dependencies = [event1]

        event3 = MagicMock()
        event3.event_id = "event3"
        event3.dependencies = [event2]

        # Set up successors
        event1.successors = [event2]
        event2.successors = [event3]
        event3.successors = []

        scenario.events = [event1, event2, event3]

        # Mock is_send_message_to_user to return True for event2
        def is_send_message_to_user_mock(event):
            return event.event_id == "event2"

        build_event_id_to_turn_idx(scenario, is_send_message_to_user_mock)

        assert scenario.event_id_to_turn_idx == {"event1": 0, "event2": 0, "event3": 1}
        assert scenario.nb_turns == 2

    def test_with_multiple_turns(self):
        """Test build_event_id_to_turn_idx with multiple turns."""
        scenario = MagicMock()

        # Create events for turn 0
        event1 = MagicMock()
        event1.event_id = "event1"
        event1.dependencies = []

        # Mock send_message_to_user event for turn 0
        event2 = MagicMock()
        event2.event_id = "event2"
        event2.dependencies = [event1]

        # Create events for turn 1
        event3 = MagicMock()
        event3.event_id = "event3"
        event3.dependencies = [event2]

        # Mock send_message_to_user event for turn 1
        event4 = MagicMock()
        event4.event_id = "event4"
        event4.dependencies = [event3]

        # Create events for turn 2
        event5 = MagicMock()
        event5.event_id = "event5"
        event5.dependencies = [event4]

        # Set up successors
        event1.successors = [event2]
        event2.successors = [event3]
        event3.successors = [event4]
        event4.successors = [event5]
        event5.successors = []

        scenario.events = [event1, event2, event3, event4, event5]

        # Mock is_send_message_to_user to return True for event2 and event4
        def is_send_message_to_user_mock(event):
            return event.event_id in ["event2", "event4"]

        build_event_id_to_turn_idx(scenario, is_send_message_to_user_mock)

        assert scenario.event_id_to_turn_idx == {
            "event1": 0,
            "event2": 0,
            "event3": 1,
            "event4": 1,
            "event5": 2,
        }
        assert scenario.nb_turns == 3


class TestBenchmarkScenarioImportedFromJson:
    def test_initialize_turns_without_initialization(self):
        """Test initialize_turns without prior initialization."""
        scenario = BenchmarkScenarioImportedFromJson()
        scenario._initialized = False

        with pytest.raises(
            ValueError, match="Scenario must be initialized before initializing turns"
        ):
            scenario.initialize_turns()

    def test_initialize_turns_already_initialized(self):
        """Test initialize_turns when turns are already initialized."""
        scenario = BenchmarkScenarioImportedFromJson()
        scenario._initialized = True
        scenario._turns_initialized = True

        # Should not raise an error and just return
        scenario.initialize_turns()

    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario.build_event_id_to_turn_idx"
    )
    def test_initialize_turns_without_trigger_condition(
        self, mock_build_event_id_to_turn_idx
    ):
        """Test initialize_turns without a trigger condition."""
        scenario = BenchmarkScenarioImportedFromJson()
        scenario._initialized = True
        scenario._turns_initialized = False

        with patch.object(scenario, "build_turn_trigger") as mock_build_turn_trigger:
            with patch.object(
                scenario, "build_validation_fn"
            ) as mock_build_validation_fn:
                scenario.initialize_turns()

                # Check that build_event_id_to_turn_idx was called
                mock_build_event_id_to_turn_idx.assert_called_once()

                # Check that build_turn_trigger was not called
                mock_build_turn_trigger.assert_not_called()

                # Check that build_validation_fn was not called
                mock_build_validation_fn.assert_not_called()

                # Check that _turns_initialized is True
                assert scenario._turns_initialized is True

                # Check that validate is set to a dummy function
                assert callable(scenario.validate)
                mock_env = MagicMock(spec=AbstractEnvironment)
                result = scenario.validate(mock_env)
                assert result.success is None

    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario.build_event_id_to_turn_idx"
    )
    def test_initialize_turns_with_trigger_condition(
        self, mock_build_event_id_to_turn_idx
    ):
        """Test initialize_turns with a trigger condition."""
        scenario = BenchmarkScenarioImportedFromJson()
        scenario._initialized = True
        scenario._turns_initialized = False

        # Mock trigger condition
        trigger_condition = MagicMock(return_value=(True, {}))

        with patch.object(scenario, "build_turn_trigger") as mock_build_turn_trigger:
            scenario.initialize_turns(trigger_condition=trigger_condition)

            # Check that build_event_id_to_turn_idx was called
            mock_build_event_id_to_turn_idx.assert_called_once()

            # Check that build_turn_trigger was called with the trigger condition
            mock_build_turn_trigger.assert_called_once_with(
                trigger_condition=trigger_condition,
                is_end_of_turn_event=is_send_message_to_user,
            )

            # Check that _turns_initialized is True
            assert scenario._turns_initialized is True

    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario.build_event_id_to_turn_idx"
    )
    def test_initialize_turns_with_validation_fn(self, mock_build_event_id_to_turn_idx):
        """Test initialize_turns with a validation function."""
        scenario = BenchmarkScenarioImportedFromJson()
        scenario._initialized = True
        scenario._turns_initialized = False

        # Mock validation function
        validation_fn = MagicMock(return_value=ScenarioValidationResult(success=True))

        with patch.object(scenario, "build_validation_fn") as mock_build_validation_fn:
            scenario.initialize_turns(validation_fn=validation_fn)

            # Check that build_event_id_to_turn_idx was called
            mock_build_event_id_to_turn_idx.assert_called_once()

            # Check that build_validation_fn was called with the validation function
            mock_build_validation_fn.assert_called_once_with(
                validation_fn, offline_validation=False
            )

            # Check that _turns_initialized is True
            assert scenario._turns_initialized is True

    def test_build_turn_trigger(self):
        """Test build_turn_trigger method."""
        scenario = BenchmarkScenarioImportedFromJson()
        scenario.scenario_id = "test_scenario"
        scenario.events = []
        scenario.event_id_to_turn_idx = {"event1": 0, "event2": 0, "event3": 1}
        scenario.nb_turns = 2

        # Create mock events
        event1 = MagicMock()
        event1.event_id = "event1"
        event1.dependencies = []
        event1.successors = []

        event2 = MagicMock()
        event2.event_id = "event2"
        event2.dependencies = []
        event2.successors = []

        event3 = MagicMock()
        event3.event_id = "event3"
        event3.dependencies = [event2]
        event3.successors = []
        event3.event_relative_time = 1.0

        # Mock is_send_message_to_user to return True for event2
        def is_send_message_to_user_mock(event):
            return event.event_id == "event2"

        # Add events to scenario
        scenario.events = [event1, event2, event3]

        # Mock trigger condition
        trigger_condition = MagicMock(return_value=(True, {}))

        # Call build_turn_trigger
        scenario.build_turn_trigger(
            trigger_condition=trigger_condition,
            is_end_of_turn_event=is_send_message_to_user_mock,
        )

        # Check that a condition check event was added to the scenario
        assert len(scenario.events) == 4
        assert scenario.events[3].event_id == "condition_turn_1-CHECK_0"

    def test_build_turn_trigger_with_oracle_successors(self):
        """Test build_turn_trigger with oracle successors."""
        scenario = BenchmarkScenarioImportedFromJson()
        scenario.scenario_id = "test_scenario"
        scenario.events = []
        scenario.event_id_to_turn_idx = {"event1": 0, "event2": 0, "event3": 1}
        scenario.nb_turns = 2

        # Create mock events
        event1 = MagicMock()
        event1.event_id = "event1"
        event1.dependencies = []
        event1.successors = []

        event2 = MagicMock()
        event2.event_id = "event2"
        event2.dependencies = []
        event2.successors = []

        # Create a mock OracleEvent
        oracle_event = OracleEvent(event_id="oracle_event")

        # Set event2's successors to include the oracle event
        event2.successors = [oracle_event]

        # Mock is_send_message_to_user to return True for event2
        def is_send_message_to_user_mock(event):
            return event.event_id == "event2"

        # Add events to scenario
        scenario.events = [event1, event2, oracle_event]

        # Mock trigger condition
        trigger_condition = MagicMock(return_value=(True, {}))

        # Call build_turn_trigger should raise ValueError
        with pytest.raises(
            ValueError,
            match="Scenario test_scenario has a end of turn event with oracle successors",
        ):
            scenario.build_turn_trigger(
                trigger_condition=trigger_condition,
                is_end_of_turn_event=is_send_message_to_user_mock,
            )

    def test_build_validation_fn_online(self):
        """Test build_validation_fn for online validation."""
        scenario = BenchmarkScenarioImportedFromJson()

        # Mock validation function
        validation_fn = MagicMock(return_value=ScenarioValidationResult(success=True))

        # Call build_validation_fn
        scenario.build_validation_fn(validation_fn, offline_validation=False)

        # Check that validate is set to a function
        assert callable(scenario.validate)

        # Create mock environment
        env = MagicMock()

        # Call validate
        result = scenario.validate(env)

        # Check that validation_fn was called with env
        validation_fn.assert_called_once_with(env)

        # Check that result is the result of validation_fn
        assert result.success is True

    def test_build_validation_fn_offline(self):
        """Test build_validation_fn for offline validation."""
        scenario = BenchmarkScenarioImportedFromJson()
        scenario.nb_turns = 3

        # Mock validation function
        validation_fn = MagicMock(return_value=ScenarioValidationResult(success=True))

        # Call build_validation_fn
        scenario.build_validation_fn(validation_fn, offline_validation=True)

        # Check that validate is set to a function
        assert callable(scenario.validate)

        # Create mock environment
        env = MagicMock()

        # Call validate
        result = scenario.validate(env)

        # Check that validation_fn was called multiple times (once for each turn)
        assert validation_fn.call_count == 3

        # Check that result is the result of the last validation_fn call
        assert result.success is True

    def test_build_validation_fn_offline_early_failure(self):
        """Test build_validation_fn for offline validation with early failure."""
        scenario = BenchmarkScenarioImportedFromJson()
        scenario.nb_turns = 3

        # Mock validation function to return failure on the second call
        validation_fn = MagicMock(
            side_effect=[
                ScenarioValidationResult(success=True),
                ScenarioValidationResult(success=False),
                ScenarioValidationResult(success=True),
            ]
        )

        # Call build_validation_fn
        scenario.build_validation_fn(validation_fn, offline_validation=True)

        # Check that validate is set to a function
        assert callable(scenario.validate)

        # Create mock environment
        env = MagicMock()

        # Call validate
        result = scenario.validate(env)

        # Check that validation_fn was called only twice (stops after failure)
        assert validation_fn.call_count == 2

        # Check that result is the failure result
        assert result.success is False
