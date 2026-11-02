# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from unittest.mock import MagicMock, patch

import pytest

from are.simulation.apps.system import SystemApp
from are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario import (
    BenchmarkScenarioImportedFromJson,
)
from are.simulation.scenarios.scenario_imported_from_json.utils import (
    create_placeholder,
    extract_execution_metadata,
    extract_placeholders,
    flag_same_tool_used_in_same_turn,
    is_oracle_event,
    preprocess_scenario,
    preprocess_scenario_for_execution_without_oracle,
    preprocess_scenario_str_for_execution_without_oracle,
)
from are.simulation.types import (
    AbstractEvent,
    Event,
    EventType,
    ExecutionMetadata,
    OracleEvent,
    PlaceholderMetadata,
)
from are.simulation.validation import BaseJudgeConfig


class TestPreprocessScenario:
    def test_adds_system_app_if_missing(self):
        """Test that preprocess_scenario adds SystemApp if it's missing."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        # Need to use a non-empty list for the condition in preprocess_scenario to work
        scenario.apps = [MagicMock(name="OtherApp")]
        scenario.events = []

        # Execute
        preprocess_scenario(scenario)

        # Assert
        assert len(scenario.apps) == 2
        assert isinstance(scenario.apps[1], SystemApp)

    def test_does_not_add_system_app_if_present(self):
        """Test that preprocess_scenario doesn't add SystemApp if it's already present."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        system_app = SystemApp()
        scenario.apps = [MagicMock(name="OtherApp"), system_app]
        scenario.events = []

        # Execute
        preprocess_scenario(scenario)

        # Assert
        assert len(scenario.apps) == 2

    def test_sets_duration_if_not_none(self):
        """Test that preprocess_scenario sets duration if `max_duration` is not none."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = []
        max_duration = 100

        # Execute
        preprocess_scenario(scenario, max_scenario_duration=max_duration)

        # Assert
        assert scenario.duration == max_duration

    def test_does_not_set_duration_if_none(self):
        """Test that preprocess_scenario doesn't set duration if it's `max_duration` is none."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = []
        scenario.duration = 50
        max_duration = None

        # Execute
        preprocess_scenario(scenario, max_scenario_duration=max_duration)

        # Assert
        assert scenario.duration == 50

    def test_initializes_scenario(self):
        """Test that preprocess_scenario initializes the scenario."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = []

        # Execute
        preprocess_scenario(scenario)

        # Assert
        scenario.initialize.assert_called_once()

    @patch("are.simulation.scenarios.scenario_imported_from_json.utils.Environment")
    @patch("are.simulation.scenarios.scenario_imported_from_json.utils.JudgeFactory")
    def test_runs_oracle_mode_if_oracle_events_present(
        self, mock_judge_factory, mock_env_class
    ):
        """
        Test that preprocess_scenario runs in oracle mode if OracleEvents are present and judge config is not None.
        """
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = [OracleEvent(event_id="test_oracle_event")]

        mock_env = MagicMock()
        mock_env_class.return_value = mock_env
        mock_env.event_log.list_view.return_value = []

        mock_judge = MagicMock()
        mock_judge.trigger_condition = MagicMock()
        mock_judge.validate = MagicMock()
        mock_judge.validate_current_turn = MagicMock()
        mock_judge_factory.return_value = lambda _: mock_judge
        judge_config = MagicMock(spec=BaseJudgeConfig)

        # Execute
        preprocess_scenario(scenario, judge_config=judge_config)

        # Assert
        mock_env_class.assert_called_once()
        mock_env.run.assert_called_once_with(scenario)
        mock_env.stop.assert_called_once()
        scenario.soft_reset.assert_called_once()
        assert hasattr(scenario, "oracle_run_event_log")

    @patch("are.simulation.scenarios.scenario_imported_from_json.utils.Environment")
    def test_raises_exception_if_oracle_run_fails(self, mock_env_class):
        """Test that preprocess_scenario raises an exception if oracle run fails."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = [OracleEvent(event_id="test_oracle_event")]

        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        # Create a failed event
        failed_event = MagicMock()
        failed_event.failed.return_value = True
        failed_event.metadata.exception = "Test exception"
        mock_env.event_log.list_view.return_value = [failed_event]

        # Execute and Assert
        with pytest.raises(Exception, match="Oracle run failed:"):
            preprocess_scenario(
                scenario,
                judge_config=MagicMock(spec=BaseJudgeConfig),
            )

    @patch("are.simulation.scenarios.scenario_imported_from_json.utils.JudgeFactory")
    def test_sets_judge_if_judge_config_provided(self, mock_judge_factory):
        """
        Test that preprocess_scenario sets the judge if judge_config is provided and env has oracle events.
        """
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = [OracleEvent(event_id="test_oracle_event")]

        mock_env = MagicMock()
        with patch(
            "are.simulation.scenarios.scenario_imported_from_json.utils.Environment",
            return_value=mock_env,
        ):
            mock_env.event_log.list_view.return_value = []

            mock_judge = MagicMock()
            mock_judge_factory.return_value = lambda _: mock_judge

            judge_config = MagicMock(spec=BaseJudgeConfig)

            # Execute
            preprocess_scenario(scenario, judge_config=judge_config)

            # Assert
            mock_judge_factory.assert_called_once()
            assert scenario.judge == mock_judge

    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.utils.is_send_message_to_user"
    )
    @patch("are.simulation.scenarios.scenario_imported_from_json.utils.Environment")
    @patch("are.simulation.scenarios.scenario_imported_from_json.utils.JudgeFactory")
    def test_initializes_turns_with_judge(
        self, mock_judge_factory, mock_env_class, mock_is_send_message_to_user
    ):
        """Test that preprocess_scenario initializes turns with judge."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = [OracleEvent(event_id="test_oracle_event")]

        mock_env = MagicMock()
        mock_env.event_log.list_view.return_value = []
        mock_env_class.return_value = mock_env

        mock_judge = MagicMock()
        mock_judge.trigger_condition = MagicMock()
        mock_judge.validate = MagicMock()
        mock_judge.validate_current_turn = MagicMock()
        mock_judge_factory.return_value = lambda _: mock_judge
        judge_config = MagicMock(spec=BaseJudgeConfig)

        # Execute
        preprocess_scenario(scenario, judge_config=judge_config)

        # Assert
        scenario.initialize_turns.assert_called_once_with(
            trigger_condition=mock_judge.trigger_condition,
            validation_fn=mock_judge.validate,
            offline_validation=False,
            is_end_of_turn_event=mock_is_send_message_to_user,
        )
        mock_judge.initialize_state.assert_called_once_with(scenario)

    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.utils.is_send_message_to_user"
    )
    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.utils.JudgeFactory",
    )
    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.utils.Environment",
    )
    def test_initializes_turns_with_offline_validation(
        self, mock_env_class, mock_judge_factory, mock_is_end_of_turn_event
    ):
        """
        Test that preprocess_scenario initializes turns with offline validation.
        """
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = [OracleEvent(event_id="test_oracle_event")]

        mock_env = MagicMock()
        mock_env_class.return_value = mock_env
        mock_env.event_log.list_view.return_value = []

        mock_judge = MagicMock()
        mock_judge.trigger_condition = MagicMock()
        mock_judge.validate = MagicMock()
        mock_judge.validate_current_turn = MagicMock()
        mock_judge_factory.return_value = lambda _: mock_judge

        judge_config = MagicMock(spec=BaseJudgeConfig)

        # Execute
        preprocess_scenario(
            scenario, judge_config=judge_config, offline_validation=True
        )

        # Assert
        scenario.initialize_turns.assert_called_once_with(
            trigger_condition=None,
            validation_fn=mock_judge.validate_current_turn,
            offline_validation=True,
            is_end_of_turn_event=mock_is_end_of_turn_event,
        )

    def test_initializes_turns_without_judge_and_oracle_event(self):
        """
        Test that preprocess_scenario initializes turns without judge and oracle events.
        """
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = []  # No oracle events

        # Execute
        preprocess_scenario(scenario, judge_config=None)

        # Assert
        scenario.initialize_turns.assert_called_once()
        # Check that the arguments match the expected dummy functions
        args, kwargs = scenario.initialize_turns.call_args
        assert kwargs["trigger_condition"] is None
        assert kwargs["validation_fn"] is None

    def test_initializes_turns_without_judge_with_oracle_event(self):
        """
        Test that preprocess_scenario initializes turns without judge and oracle events.
        """
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.apps = []
        scenario.events = [OracleEvent(event_id="test_oracle_event")]

        # Execute
        preprocess_scenario(scenario, judge_config=None)

        # Assert
        scenario.initialize_turns.assert_called_once()
        # Check that the arguments match the expected dummy functions
        args, kwargs = scenario.initialize_turns.call_args
        assert callable(kwargs["trigger_condition"])
        assert kwargs["validation_fn"] is None

        # Test the dummy trigger condition
        result, data = kwargs["trigger_condition"](None, None)
        assert result is True
        assert data == {}


class TestIsOracleEvent:
    def test_returns_true_for_oracle_event(self):
        """Test that is_oracle_event returns True for an oracle event."""
        # Setup
        event = {"class_name": "OracleEvent"}

        # Execute
        result = is_oracle_event(event)

        # Assert
        assert result is True

    def test_returns_false_for_non_oracle_event(self):
        """Test that is_oracle_event returns False for a non-oracle event."""
        # Setup
        event = {"class_name": "Event"}

        # Execute
        result = is_oracle_event(event)

        # Assert
        assert result is False

    def test_returns_false_for_event_without_class_name(self):
        """Test that is_oracle_event returns False for an event without class_name."""
        # Setup
        event = {}

        # Execute
        result = is_oracle_event(event)

        # Assert
        assert result is False


class TestCreatePlaceholder:
    def test_creates_placeholder_metadata(self):
        """Test that create_placeholder creates a PlaceholderMetadata object."""
        # Setup
        placeholder_event = MagicMock(spec=AbstractEvent)
        placeholder_event.event_id = "placeholder_event_id"

        parent_event = MagicMock(spec=OracleEvent)
        parent_event.event_id = "parent_event_id"
        parent_event.action_desc.function = "test_function"
        parent_event.action_desc.app = "test_app"

        event_id_to_turn_idx = {
            "placeholder_event_id": 1,
            "parent_event_id": 0,
        }

        # Execute
        result = create_placeholder(
            placeholder_event, parent_event, event_id_to_turn_idx
        )

        # Assert
        assert isinstance(result, PlaceholderMetadata)
        assert result.parent_tool_name == "test_app__test_function"
        assert result.parent_turn_idx == 0
        assert result.parent_event_id == "parent_event_id"
        assert result.placeholder_turn_idx == 1
        assert result.placeholder_event_id == "placeholder_event_id"

    def test_raises_exception_if_function_name_not_found(self):
        """Test that create_placeholder raises an exception if function name is not found."""
        # Setup
        placeholder_event = MagicMock(spec=AbstractEvent)
        placeholder_event.event_id = "placeholder_event_id"

        parent_event = MagicMock(spec=OracleEvent)
        parent_event.event_id = "parent_event_id"
        parent_event.action_desc = MagicMock()
        delattr(parent_event.action_desc, "function")  # Remove function attribute
        parent_event.action_desc.app = "test_app"

        event_id_to_turn_idx = {
            "placeholder_event_id": 1,
            "parent_event_id": 0,
        }

        # Execute and Assert
        with pytest.raises(Exception, match="Function name not found for event:"):
            create_placeholder(placeholder_event, parent_event, event_id_to_turn_idx)

    def test_raises_exception_if_app_name_not_found(self):
        """Test that create_placeholder raises an exception if app name is not found."""
        # Setup
        placeholder_event = MagicMock(spec=AbstractEvent)
        placeholder_event.event_id = "placeholder_event_id"

        parent_event = MagicMock(spec=OracleEvent)
        parent_event.event_id = "parent_event_id"
        parent_event.action_desc.function = "test_function"
        delattr(parent_event.action_desc, "app")  # Remove app attribute

        event_id_to_turn_idx = {
            "placeholder_event_id": 1,
            "parent_event_id": 0,
        }

        # Execute and Assert
        with pytest.raises(Exception, match="App name not found for event:"):
            create_placeholder(placeholder_event, parent_event, event_id_to_turn_idx)


class TestFlagSameToolUsedInSameTurn:
    def test_returns_true_if_same_tool_used_in_same_turn(self):
        """Test that flag_same_tool_used_in_same_turn returns True if the same tool is used in the same turn."""
        # Setup
        placeholder = PlaceholderMetadata(
            parent_tool_name="test_app__test_function",
            parent_turn_idx=0,
            parent_event_id="parent_event_id",
            placeholder_turn_idx=1,
            placeholder_event_id="placeholder_event_id",
        )

        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.event_id_to_turn_idx = {
            "parent_event_id": 0,
            "other_event_id": 0,
        }

        # Create another event with the same tool in the same turn
        other_event = MagicMock(spec=OracleEvent)
        other_event.event_id = "other_event_id"
        other_event.action_desc.function = "test_function"
        other_event.action_desc.app = "test_app"

        scenario.events = [other_event]

        # Execute
        result = flag_same_tool_used_in_same_turn(placeholder, scenario)

        # Assert
        assert result is True

    def test_returns_false_if_different_tool_used_in_same_turn(self):
        """Test that flag_same_tool_used_in_same_turn returns False if a different tool is used in the same turn."""
        # Setup
        placeholder = PlaceholderMetadata(
            parent_tool_name="test_app__test_function",
            parent_turn_idx=0,
            parent_event_id="parent_event_id",
            placeholder_turn_idx=1,
            placeholder_event_id="placeholder_event_id",
        )

        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.event_id_to_turn_idx = {
            "parent_event_id": 0,
            "other_event_id": 0,
        }

        # Create another event with a different tool in the same turn
        other_event = MagicMock(spec=OracleEvent)
        other_event.event_id = "other_event_id"
        other_event.action_desc.function = "different_function"
        other_event.action_desc.app = "test_app"

        scenario.events = [other_event]

        # Execute
        result = flag_same_tool_used_in_same_turn(placeholder, scenario)

        # Assert
        assert result is False

    def test_returns_false_if_same_tool_used_in_different_turn(self):
        """Test that flag_same_tool_used_in_same_turn returns False if the same tool is used in a different turn."""
        # Setup
        placeholder = PlaceholderMetadata(
            parent_tool_name="test_app__test_function",
            parent_turn_idx=0,
            parent_event_id="parent_event_id",
            placeholder_turn_idx=1,
            placeholder_event_id="placeholder_event_id",
        )

        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.event_id_to_turn_idx = {
            "parent_event_id": 0,
            "other_event_id": 1,  # Different turn
        }

        # Create another event with the same tool in a different turn
        other_event = MagicMock(spec=OracleEvent)
        other_event.event_id = "other_event_id"
        other_event.action_desc.function = "test_function"
        other_event.action_desc.app = "test_app"

        scenario.events = [other_event]

        # Execute
        result = flag_same_tool_used_in_same_turn(placeholder, scenario)

        # Assert
        assert result is False

    def test_raises_exception_if_event_id_to_turn_idx_not_found(self):
        """Test that flag_same_tool_used_in_same_turn raises an exception if event_id_to_turn_idx is not found."""
        # Setup
        placeholder = PlaceholderMetadata(
            parent_tool_name="test_app__test_function",
            parent_turn_idx=0,
            parent_event_id="parent_event_id",
            placeholder_turn_idx=1,
            placeholder_event_id="placeholder_event_id",
        )

        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.event_id_to_turn_idx = None

        # Execute and Assert
        with pytest.raises(ValueError, match="Event id to turn not found"):
            flag_same_tool_used_in_same_turn(placeholder, scenario)


class TestExtractPlaceholders:
    def test_extracts_placeholders(self):
        """Test that extract_placeholders extracts placeholders from events."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.event_id_to_turn_idx = {
            "event1": 0,
            "event2": 1,
            "oracle_event": 0,
        }

        # Create a user event with a placeholder
        user_event = MagicMock(spec=Event)
        user_event.event_id = "event1"
        user_event.event_type = EventType.USER
        user_event.action.args = {"arg1": "{{oracle_event}}"}

        # Create an oracle event that the placeholder refers to
        oracle_event = MagicMock(spec=OracleEvent)
        oracle_event.event_id = "oracle_event"
        oracle_event.action_desc.function = "test_function"
        oracle_event.action_desc.app = "test_app"

        # Add events to scenario
        scenario.events = [user_event, oracle_event]

        # Mock flag_same_tool_used_in_same_turn to return False
        with patch(
            "are.simulation.scenarios.scenario_imported_from_json.utils.flag_same_tool_used_in_same_turn",
            return_value=False,
        ):
            # Execute
            placeholders, same_tool_flag = extract_placeholders(scenario)

            # Assert
            assert len(placeholders) == 1
            assert placeholders[0].parent_event_id == "oracle_event"
            assert placeholders[0].placeholder_event_id == "event1"
            assert same_tool_flag is False

    def test_extracts_placeholders_with_same_tool_flag(self):
        """Test that extract_placeholders sets same_tool_flag if the same tool is used in the same turn."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.event_id_to_turn_idx = {
            "event1": 0,
            "event2": 1,
            "oracle_event": 0,
        }

        # Create a user event with a placeholder
        user_event = MagicMock(spec=Event)
        user_event.event_id = "event1"
        user_event.event_type = EventType.USER
        user_event.action.args = {"arg1": "{{oracle_event}}"}

        # Create an oracle event that the placeholder refers to
        oracle_event = MagicMock(spec=OracleEvent)
        oracle_event.event_id = "oracle_event"
        oracle_event.action_desc.function = "test_function"
        oracle_event.action_desc.app = "test_app"

        # Add events to scenario
        scenario.events = [user_event, oracle_event]

        # Mock flag_same_tool_used_in_same_turn to return True
        with patch(
            "are.simulation.scenarios.scenario_imported_from_json.utils.flag_same_tool_used_in_same_turn",
            return_value=True,
        ):
            # Execute
            placeholders, same_tool_flag = extract_placeholders(scenario)

            # Assert
            assert len(placeholders) == 1
            assert placeholders[0].parent_event_id == "oracle_event"
            assert placeholders[0].placeholder_event_id == "event1"
            assert same_tool_flag is True

    def test_extracts_placeholders_with_complex_pattern(self):
        """Test that extract_placeholders extracts placeholders with complex patterns."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.event_id_to_turn_idx = {
            "event1": 0,
            "event2": 1,
            "oracle_event": 0,
        }

        # Create a user event with a placeholder with a complex pattern
        user_event = MagicMock(spec=Event)
        user_event.event_id = "event1"
        user_event.event_type = EventType.USER
        user_event.action.args = {"arg1": "{{oracle_event.result}}"}

        # Create an oracle event that the placeholder refers to
        oracle_event = MagicMock(spec=OracleEvent)
        oracle_event.event_id = "oracle_event"
        oracle_event.action_desc.function = "test_function"
        oracle_event.action_desc.app = "test_app"

        # Add events to scenario
        scenario.events = [user_event, oracle_event]

        # Mock flag_same_tool_used_in_same_turn to return False
        with patch(
            "are.simulation.scenarios.scenario_imported_from_json.utils.flag_same_tool_used_in_same_turn",
            return_value=False,
        ):
            # Execute
            placeholders, same_tool_flag = extract_placeholders(scenario)

            # Assert
            assert len(placeholders) == 1
            assert placeholders[0].parent_event_id == "oracle_event"
            assert placeholders[0].placeholder_event_id == "event1"
            assert same_tool_flag is False

    def test_raises_exception_if_event_id_to_turn_idx_not_found(self):
        """Test that extract_placeholders raises an exception if event_id_to_turn_idx is not found."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        scenario.event_id_to_turn_idx = None

        # Execute and Assert
        with pytest.raises(ValueError, match="Event id to turn not found"):
            extract_placeholders(scenario)


class TestExtractExecutionMetadata:
    def test_extracts_execution_metadata(self):
        """Test that extract_execution_metadata extracts execution metadata from a scenario."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)

        # Mock extract_placeholders to return some placeholders and a same_tool_flag
        placeholders = [MagicMock(spec=PlaceholderMetadata)]
        same_tool_flag = True

        with patch(
            "are.simulation.scenarios.scenario_imported_from_json.utils.extract_placeholders",
            return_value=(placeholders, same_tool_flag),
        ):
            # Execute
            result = extract_execution_metadata(scenario)

            # Assert
            assert isinstance(result, ExecutionMetadata)
            assert result.placeholders == placeholders
            assert result.has_placeholder_conflicts is True


class TestPreprocessScenarioForExecutionWithoutOracle:
    def test_preprocesses_scenario_for_execution_without_oracle(self):
        """Test that preprocess_scenario_for_execution_without_oracle preprocesses a scenario for execution without oracle."""
        # Setup
        scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)

        # Mock preprocess_scenario
        with patch(
            "are.simulation.scenarios.scenario_imported_from_json.utils.preprocess_scenario"
        ) as mock_preprocess:
            # Mock extract_execution_metadata
            mock_metadata = MagicMock(spec=ExecutionMetadata)
            with patch(
                "are.simulation.scenarios.scenario_imported_from_json.utils.extract_execution_metadata",
                return_value=mock_metadata,
            ) as mock_extract:
                # Execute
                result = preprocess_scenario_for_execution_without_oracle(scenario)

                # Assert
                mock_preprocess.assert_called_once_with(scenario, judge_config=None)
                mock_extract.assert_called_once_with(scenario)
                assert scenario.execution_metadata == mock_metadata
                assert result == scenario


class TestPreprocessScenarioStrForExecutionWithoutOracle:
    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.utils.JsonScenarioImporter"
    )
    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.utils.preprocess_scenario_for_execution_without_oracle"
    )
    @patch("are.simulation.scenarios.scenario_imported_from_json.utils.Environment")
    @patch(
        "are.simulation.scenarios.scenario_imported_from_json.utils.JsonScenarioExporter"
    )
    def test_preprocesses_scenario_str_for_execution_without_oracle(
        self, mock_exporter_class, mock_env_class, mock_preprocess, mock_importer_class
    ):
        """Test that preprocess_scenario_str_for_execution_without_oracle preprocesses a scenario string for execution without oracle."""
        # Setup
        scenario_str = "test_scenario_str"

        # Mock importer
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        mock_importer.import_from_json_to_benchmark.return_value = (
            mock_scenario,
            None,
            None,
        )

        # Mock preprocessor
        mock_preprocess.return_value = mock_scenario

        # Mock environment
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env

        # Mock exporter
        mock_exporter = MagicMock()
        mock_exporter_class.return_value = mock_exporter
        mock_exporter.export_to_json.return_value = "processed_scenario_str"

        # Execute
        result = preprocess_scenario_str_for_execution_without_oracle(scenario_str)

        # Assert
        mock_importer.import_from_json_to_benchmark.assert_called_once_with(
            scenario_str, load_completed_events=False
        )
        mock_preprocess.assert_called_once_with(mock_scenario)
        mock_env_class.assert_called_once()
        mock_exporter.export_to_json.assert_called_once_with(
            env=mock_env,
            scenario=mock_scenario,
            scenario_id=mock_scenario.scenario_id,
            runner_config=None,
        )
        assert result == "processed_scenario_str"
