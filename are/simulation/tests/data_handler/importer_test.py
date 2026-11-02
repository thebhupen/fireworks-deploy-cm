# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from unittest.mock import MagicMock, patch

import pytest

from are.simulation.data_handler.importer import JsonScenarioImporter
from are.simulation.data_handler.models import (
    TRACE_V1_VERSION,
    ExportedAction,
    ExportedActionArg,
    ExportedApp,
    ExportedCompletedEvent,
    ExportedEvent,
    ExportedEventMetadata,
    ExportedHint,
    ExportedTrace,
    ExportedTraceDefinitionMetadata,
    ExportedTraceMetadata,
)
from are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario import (
    BenchmarkScenarioImportedFromJson,
)
from are.simulation.scenarios.scenario_imported_from_json.scenario import (
    ScenarioImportedFromJson,
)
from are.simulation.types import CapabilityTag, CompletedEvent, HintType


def test_map_action():
    """Test the map_action static method."""
    action_data = {
        "action_id": "test_action_id",
        "app": "TestApp",
        "args": [
            {"name": "param1", "value": "42", "value_type": "int"},
            {"name": "param2", "value": "hello", "value_type": "str"},
        ],
        "function": "test_function",
        "operation_type": "READ",
    }
    app_name_to_class = {"TestApp": "TestAppClass"}

    result = JsonScenarioImporter.map_action(action_data, app_name_to_class)

    assert result["action_id"] == "test_action_id"
    assert result["class_name"] == "TestAppClass"
    assert result["args"]["param1"] == 42  # Should be converted to int
    assert result["args"]["param2"] == "hello"
    assert result["function_name"] == "test_function"
    assert result["operation_type"] == "READ"


def test_map_action_with_none_args():
    """Test the map_action static method with None args."""
    action_data = {
        "action_id": "test_action_id",
        "app": "TestApp",
        "args": None,
        "function": "test_function",
        "operation_type": "READ",
    }
    app_name_to_class = {"TestApp": "TestAppClass"}

    result = JsonScenarioImporter.map_action(action_data, app_name_to_class)

    assert result["action_id"] == "test_action_id"
    assert result["class_name"] == "TestAppClass"
    assert result["args"] == {}
    assert result["function_name"] == "test_function"
    assert result["operation_type"] == "READ"


def test_map_action_with_none_app():
    """Test the map_action static method with None app."""
    action_data = {
        "action_id": "test_action_id",
        "app": None,
        "args": [{"name": "param1", "value": "42", "value_type": "int"}],
        "function": "test_function",
        "operation_type": "READ",
    }
    app_name_to_class = {"TestApp": "TestAppClass"}

    result = JsonScenarioImporter.map_action(action_data, app_name_to_class)

    assert result["action_id"] == "test_action_id"
    assert result["class_name"] == "ConditionCheckAction"
    assert result["args"]["param1"] == 42
    assert result["function_name"] == "test_function"
    assert result["operation_type"] == "READ"


def test_map_event_metadata():
    """Test the map_event_metadata static method."""
    metadata_data = {
        "exception": "TestException",
        "exception_stack_trace": "Test stack trace",
        "return_value": "Test return value",
        "return_value_type": "str",
    }

    result = JsonScenarioImporter.map_event_metadata(metadata_data)

    assert result["exception"] == "TestException"
    assert result["exception_stack_trace"] == "Test stack trace"
    assert result["return_value"] == "Test return value"
    assert result["return_value_type"] == "str"


def test_map_event():
    """Test the map_event static method."""
    input_json = {
        "event_id": "test_event_id",
        "event_time": 123456789,
        "event_type": "ACTION",
        "dependencies": ["dep1", "dep2"],
        "metadata": {
            "exception": None,
            "exception_stack_trace": None,
            "return_value": "Test return value",
            "return_value_type": "str",
        },
        "action": {
            "action_id": "test_action_id",
            "app": "TestApp",
            "args": [{"name": "param1", "value": "42", "value_type": "int"}],
            "function": "test_function",
            "operation_type": "READ",
        },
    }
    app_name_to_class = {"TestApp": "TestAppClass"}

    result = JsonScenarioImporter.map_event(input_json, app_name_to_class)

    assert result["event_id"] == "test_event_id"
    assert result["event_time"] == 123456789
    assert result["event_type"] == "ACTION"
    assert result["dependencies"] == ["dep1", "dep2"]
    assert result["metadata"]["exception"] is None
    assert result["metadata"]["exception_stack_trace"] is None
    assert result["metadata"]["return_value"] == "Test return value"
    assert result["action"]["action_id"] == "test_action_id"
    assert result["action"]["class_name"] == "TestAppClass"
    assert result["action"]["args"]["param1"] == 42
    assert result["action"]["function_name"] == "test_function"
    assert result["action"]["operation_type"] == "READ"


def test_map_event_without_metadata_and_action():
    """Test the map_event static method without metadata and action."""
    input_json = {
        "event_id": "test_event_id",
        "event_time": 123456789,
        "event_type": "ACTION",
        "dependencies": ["dep1", "dep2"],
    }
    app_name_to_class = {"TestApp": "TestAppClass"}

    result = JsonScenarioImporter.map_event(input_json, app_name_to_class)

    assert result["event_id"] == "test_event_id"
    assert result["event_time"] == 123456789
    assert result["event_type"] == "ACTION"
    assert result["dependencies"] == ["dep1", "dep2"]
    assert "metadata" not in result
    assert "action" not in result


def create_mock_exported_trace():
    """Helper function to create a mock ExportedTrace for testing."""
    return ExportedTrace(
        version=TRACE_V1_VERSION,
        metadata=ExportedTraceMetadata(
            definition=ExportedTraceDefinitionMetadata(
                scenario_id="test_scenario_id",
                seed=42,
                start_time=123456789,
                duration=3600,
                time_increment_in_seconds=1,
                run_number=2,  # Add run_number for testing
                hints=[
                    ExportedHint(
                        hint_type="TASK_HINT",
                        content="Test hint",
                        associated_event_id="event1",
                    )
                ],
                config="test_config_value",
                has_a2a_augmentation=True,
                has_tool_augmentation=True,
                has_env_events_augmentation=True,
                has_exception=True,
                exception_type="ValueError",
                exception_message="Test exception message",
                tags=["Execution"],
                hf_metadata=None,
            ),
            annotation=None,
            execution=None,
        ),
        apps=[
            ExportedApp(
                name="TestApp",
                class_name="TestAppClass",
            ),
            ExportedApp(
                name="TestApp1",
                class_name="TestAppClass",
            ),
        ],
        events=[
            ExportedEvent(
                event_id="event1",
                class_name="Event",
                event_relative_time=1.0,
                event_time=123456789,
                event_type="USER",
                dependencies=[],
                action=ExportedAction(
                    action_id="action1",
                    app="TestApp",
                    args=[
                        ExportedActionArg(
                            name="param1",
                            value="42",
                            value_type="int",
                        )
                    ],
                    function="test_function",
                    operation_type="READ",
                ),
            )
        ],
        completed_events=[
            ExportedCompletedEvent(
                event_id="event1",
                event_time=123456789,
                event_relative_time=1.0,
                class_name="Event",
                event_type="AGENT",
                dependencies=[],
                metadata=ExportedEventMetadata(
                    exception=None,
                    exception_stack_trace=None,
                    return_value="Test return value",
                    return_value_type="str",
                ),
                action=ExportedAction(
                    action_id="action1",
                    app="TestApp",
                    args=[
                        ExportedActionArg(
                            name="param1",
                            value="42",
                            value_type="int",
                        )
                    ],
                    function="test_function",
                    operation_type="WRITE",
                ),
            )
        ],
        world_logs=[],
    )


@patch("are.simulation.types.CompletedEvent.from_dict")
def test_import_from_json(mock_completed_event_from_dict):
    """Test the import_from_json method."""
    # Setup the mock to return a custom CompletedEvent
    mock_completed_event = MagicMock(spec=CompletedEvent)
    mock_completed_event.event_id = "event1"
    mock_completed_event_from_dict.return_value = mock_completed_event

    importer = JsonScenarioImporter()
    mock_trace = create_mock_exported_trace()
    json_str = mock_trace.model_dump_json()

    scenario, completed_events, world_logs = importer.import_from_json(json_str)

    assert isinstance(scenario, ScenarioImportedFromJson)
    assert scenario.scenario_id == "test_scenario_id"
    assert scenario.seed == 42
    assert scenario.start_time == 123456789
    assert scenario.duration == 3600
    assert scenario.time_increment_in_seconds == 1
    assert scenario.run_number == 2  # Test run_number is properly imported
    assert len(scenario.hints) == 1
    assert scenario.hints[0].hint_type == HintType.TASK_HINT
    assert scenario.hints[0].content == "Test hint"
    assert scenario.hints[0].associated_event_id == "event1"
    assert scenario.tags == (CapabilityTag.Execution,)

    # Test the new fields added to ExportedTraceDefinitionMetadata
    assert scenario.config == "test_config_value"
    assert scenario.has_a2a_augmentation is True
    assert scenario.has_tool_augmentation is True
    assert scenario.has_env_events_augmentation is True
    assert scenario.has_exception is True
    assert scenario.exception_type == "ValueError"
    assert scenario.exception_message == "Test exception message"

    assert len(scenario.serialized_apps) == 2
    assert scenario.serialized_apps[0].name == "TestApp"
    assert scenario.serialized_apps[0].class_name == "TestAppClass"
    assert len(scenario.serialized_events) == 1
    assert scenario.serialized_events[0].event_id == "event1"
    assert len(completed_events) == 1
    assert completed_events[0] == mock_completed_event
    assert len(world_logs) == 0

    # Verify that CompletedEvent.from_dict was called with the correct parameters
    mock_completed_event_from_dict.assert_called_once()


def test_import_from_json_unsupported_version():
    """Test the import_from_json method with an unsupported version."""

    importer = JsonScenarioImporter()
    mock_trace = create_mock_exported_trace()
    mock_trace.version = "unsupported_version"
    json_str = mock_trace.model_dump_json()

    with pytest.raises(Exception, match="Unsupported version: unsupported_version"):
        importer.import_from_json(json_str)


def test_import_from_json_without_loading_completed_events():
    """Test the import_from_json method without loading completed events."""
    importer = JsonScenarioImporter()
    mock_trace = create_mock_exported_trace()
    json_str = mock_trace.model_dump_json()

    scenario, completed_events, world_logs = importer.import_from_json(
        json_str, load_completed_events=False
    )

    assert isinstance(scenario, ScenarioImportedFromJson)
    assert len(completed_events) == 0


def test_import_from_json_with_apps_to_skip_and_keep():
    """Test the import_from_json method with apps_to_skip and apps_to_keep."""
    importer = JsonScenarioImporter()
    mock_trace = create_mock_exported_trace()
    json_str = mock_trace.model_dump_json()

    apps_to_skip = ["TestApp1"]
    apps_to_keep = ["TestApp"]

    scenario, _, _ = importer.import_from_json(
        json_str,
        apps_to_skip=apps_to_skip,
        apps_to_keep=apps_to_keep,
        load_completed_events=False,
    )

    assert scenario.apps_to_skip == apps_to_skip
    assert scenario.apps_to_keep == apps_to_keep


def test_import_from_json_to_benchmark():
    """Test the import_from_json_to_benchmark method."""
    importer = JsonScenarioImporter()
    mock_trace = create_mock_exported_trace()
    json_str = mock_trace.model_dump_json()

    scenario, completed_events, world_logs = importer.import_from_json_to_benchmark(
        json_str,
        load_completed_events=False,
    )

    assert isinstance(scenario, BenchmarkScenarioImportedFromJson)
    assert scenario.scenario_id == "test_scenario_id"
    assert scenario.seed == 42
    assert scenario.start_time == 123456789
    assert scenario.duration == 3600
    assert scenario.time_increment_in_seconds == 1
    assert scenario.run_number == 2  # Test run_number is properly imported
    assert len(scenario.hints) == 1
    assert scenario.tags == (CapabilityTag.Execution,)
    assert len(scenario.serialized_apps) == 2
    assert len(scenario.serialized_events) == 1
    assert len(completed_events) == 0
    assert len(world_logs) == 0


def test_run_number_import_export():
    """Test that run_number is properly handled in import/export cycle."""
    importer = JsonScenarioImporter()

    # Test with run_number present
    mock_trace_with_run = create_mock_exported_trace()
    mock_trace_with_run.metadata.definition.run_number = 5
    json_str_with_run = mock_trace_with_run.model_dump_json()

    scenario_with_run, _, _ = importer.import_from_json(
        json_str_with_run,
        load_completed_events=False,
    )
    assert scenario_with_run.run_number == 5

    # Test with run_number as None
    mock_trace_no_run = create_mock_exported_trace()
    mock_trace_no_run.metadata.definition.run_number = None
    json_str_no_run = mock_trace_no_run.model_dump_json()

    scenario_no_run, _, _ = importer.import_from_json(
        json_str_no_run,
        load_completed_events=False,
    )
    assert scenario_no_run.run_number is None

    # Test benchmark import as well
    scenario_benchmark_with_run, _, _ = importer.import_from_json_to_benchmark(
        json_str_with_run,
        load_completed_events=False,
    )
    assert scenario_benchmark_with_run.run_number == 5

    scenario_benchmark_no_run, _, _ = importer.import_from_json_to_benchmark(
        json_str_no_run,
        load_completed_events=False,
    )
    assert scenario_benchmark_no_run.run_number is None
