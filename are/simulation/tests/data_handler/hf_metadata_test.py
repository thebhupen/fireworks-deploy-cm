# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
from unittest.mock import MagicMock, patch

import pytest
from datasets import IterableDatasetDict

from are.simulation.data_handler.exporter import JsonScenarioExporter
from are.simulation.data_handler.importer import JsonScenarioImporter
from are.simulation.data_handler.models import (
    TRACE_V1_VERSION,
    ExportedHuggingFaceMetadata,
)


@pytest.fixture
def mock_scenario():
    """Create a mock scenario with HuggingFace metadata."""
    scenario = MagicMock()
    scenario.scenario_id = "test_scenario"
    scenario.duration = 100
    scenario.start_time = 0
    scenario.seed = 42
    scenario.time_increment_in_seconds = 1.0
    scenario.hints = []
    scenario._initial_apps = {
        "app1": {
            "class_name": "App1",
            "serialized_state": json.dumps({"state": "value"}),
        }
    }
    scenario.events = []

    # Set config as a string instead of MagicMock
    scenario.config = "test_config"

    # Set other attributes that might be accessed
    scenario.run_number = None
    scenario.has_a2a_augmentation = False
    scenario.tool_augmentation_config = None
    scenario.env_events_config = None

    # Add HuggingFace metadata
    scenario.hf_metadata = ExportedHuggingFaceMetadata(
        dataset="test_dataset",
        split="test_split",
        revision="test_revision",
    )

    return scenario


@pytest.fixture
def mock_env():
    """Create a mock environment."""
    env = MagicMock()
    env.event_log.list_view.return_value = []
    env.event_queue.future_events = []
    return env


@pytest.fixture
def dummy_json():
    # Create a JSON string with HF metadata but no apps
    return json.dumps(
        {
            "version": TRACE_V1_VERSION,
            "metadata": {
                "definition": {
                    "scenario_id": "test_scenario",
                    "duration": 100,
                    "start_time": 0,
                    "hints": [],
                    "hf_metadata": {
                        "dataset": "test_dataset",
                        "split": "test_split",
                        "revision": "test_revision",
                    },
                },
                "simulation": {},
                "annotation": {
                    "date": 0,
                },
            },
            "apps": [],
            "events": [],
            "completed_events": [],
            "world_logs": [],
        }
    )


def test_export_with_hf_metadata_no_apps(mock_scenario, mock_env):
    """Test that apps are not included in the export when export_apps=False and HF metadata is present."""
    exporter = JsonScenarioExporter()

    # Export with export_apps=False
    json_str = exporter.export_to_json(
        env=mock_env,
        scenario=mock_scenario,
        scenario_id=mock_scenario.scenario_id,
        runner_config=None,
        export_apps=False,
    )

    # Parse the JSON and check that apps is an empty list
    exported_data = json.loads(json_str)
    assert len(exported_data["apps"]) == 0

    # Check that HF metadata is included
    assert exported_data["metadata"]["definition"]["hf_metadata"] is not None
    assert (
        exported_data["metadata"]["definition"]["hf_metadata"]["dataset"]
        == "test_dataset"
    )


def test_export_with_hf_metadata_with_apps(mock_scenario, mock_env):
    """Test that apps are included in the export when export_apps=True, even with HF metadata."""
    exporter = JsonScenarioExporter()

    # Export with export_apps=True
    json_str = exporter.export_to_json(
        env=mock_env,
        scenario=mock_scenario,
        scenario_id=mock_scenario.scenario_id,
        runner_config=None,
        export_apps=True,
    )

    # Parse the JSON and check that apps are included
    exported_data = json.loads(json_str)
    assert len(exported_data["apps"]) == 1
    assert exported_data["apps"][0]["name"] == "app1"


def test_export_without_hf_metadata_warning(mock_scenario, mock_env, caplog):
    """Test that a warning is logged when export_apps=False but there's no HF metadata."""
    # Remove HF metadata
    mock_scenario.hf_metadata = None

    exporter = JsonScenarioExporter()

    # Export with export_apps=False but no HF metadata
    json_str = exporter.export_to_json(
        env=mock_env,
        scenario=mock_scenario,
        scenario_id=mock_scenario.scenario_id,
        runner_config=None,
        export_apps=False,
    )

    # Check that a warning was logged
    assert any(
        "export_apps=False but no HuggingFace metadata found" in record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    )

    # Parse the JSON and check that apps are still included despite export_apps=False
    exported_data = json.loads(json_str)
    assert len(exported_data["apps"]) == 1


@patch("datasets.load_dataset")
def test_import_with_hf_metadata_no_apps(mock_load_dataset, dummy_json):
    """Test that apps are fetched from HuggingFace when importing a scenario with HF metadata but no apps."""
    # Create a mock dataset
    mock_dataset = MagicMock(spec=IterableDatasetDict)

    mock_dataset.__getitem__.return_value = [
        {
            "scenario_id": "test_scenario",
            "data": json.dumps(
                {
                    "apps": {
                        "app1": {
                            "class_name": "App1",
                            "serialized_state": json.dumps({"state": "value"}),
                        }
                    }
                }
            ),
        }
    ]
    mock_load_dataset.return_value = mock_dataset

    # Import the scenario
    importer = JsonScenarioImporter()
    scenario, _, _ = importer.import_from_json_to_benchmark(
        dummy_json, load_completed_events=False
    )

    # Check that load_dataset was called with the correct parameters
    mock_load_dataset.assert_called_once_with(
        "test_dataset",
        revision="test_revision",
        streaming=True,
    )

    # Check that the scenario has the HF metadata
    assert scenario.hf_metadata is not None
    assert scenario.hf_metadata.dataset == "test_dataset"

    # Check that the apps were fetched from HuggingFace
    assert scenario.serialized_apps is not None
    assert len(scenario.serialized_apps) == 1


@patch("datasets.load_dataset")
def test_import_with_hf_metadata_no_apps_failure(mock_load_dataset, dummy_json):
    """Test that an exception is raised when apps can't be fetched from HuggingFace."""
    # Make load_dataset raise an exception
    mock_load_dataset.side_effect = Exception("Failed to load dataset")

    # Import the scenario - should raise an exception
    importer = JsonScenarioImporter()
    with pytest.raises(ValueError):
        importer.import_from_json_to_benchmark(dummy_json)
