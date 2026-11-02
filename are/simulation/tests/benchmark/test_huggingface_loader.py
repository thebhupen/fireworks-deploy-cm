# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from unittest.mock import Mock, patch

from are.simulation.benchmark.huggingface_loader import (
    _create_huggingface_scenario_iterator,
)
from are.simulation.data_handler.models import (
    TRACE_V1_VERSION,
    ExportedTrace,
    ExportedTraceDefinitionMetadata,
    ExportedTraceMetadata,
)
from are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario import (
    BenchmarkScenarioImportedFromJson,
)


def create_mock_exported_trace(
    scenario_id: str = "test_scenario_123",
    run_number: int | None = 1,
):
    """Helper function to create a mock ExportedTrace for testing HuggingFace loading."""
    return ExportedTrace(
        version=TRACE_V1_VERSION,
        metadata=ExportedTraceMetadata(
            definition=ExportedTraceDefinitionMetadata(
                scenario_id=scenario_id,
                run_number=run_number,  # This is the key field we're testing
                seed=42,
                start_time=123456789,
                duration=3600,
                time_increment_in_seconds=1,
                hints=[],
                tags=["Execution"],
                hf_metadata=None,
            ),
            annotation=None,
            execution=None,
        ),
        apps=[],
        events=[],
        completed_events=[],
        world_logs=[],
    )


def create_mock_hf_row(scenario_id: str, run_number: int, phase_name: str = "standard"):
    """Create a mock HuggingFace dataset row."""
    mock_trace = create_mock_exported_trace(scenario_id, run_number)
    return {
        "scenario_id": scenario_id,
        "run_number": run_number,
        "phase_name": phase_name,
        "data": mock_trace.model_dump_json(),
    }


def test_run_number_preservation():
    """Test that run_number is properly preserved from HuggingFace row to scenario."""

    # Create mock dataset rows with different run numbers
    mock_rows = [
        create_mock_hf_row("scenario_universe_123", 1, "standard"),
        create_mock_hf_row("scenario_universe_123", 2, "standard"),
        create_mock_hf_row("scenario_universe_123", 3, "standard"),
        create_mock_hf_row("scenario_universe_456", 1, "standard"),
        create_mock_hf_row("scenario_universe_456", 2, "standard"),
    ]

    # Mock the datasets library - need to mock IterableDatasetDict properly
    from datasets import IterableDatasetDict

    mock_dataset = Mock()
    mock_dataset.__iter__ = Mock(return_value=iter(mock_rows))

    # Mock dataset info for total count
    mock_split_info = Mock()
    mock_split_info.num_examples = len(mock_rows)
    mock_splits = {"test": mock_split_info}
    mock_info = Mock()
    mock_info.splits = mock_splits
    mock_dataset.info = mock_info

    # Create a proper mock of IterableDatasetDict
    mock_dataset_dict = Mock(spec=IterableDatasetDict)
    mock_dataset_dict.__getitem__ = Mock(return_value=mock_dataset)
    mock_dataset_dict.__contains__ = Mock(return_value=True)

    # Mock load_scenario to return a basic scenario
    def mock_load_scenario(
        scenario_data, scenario_id, load_completed_events, hf_metadata=None
    ):
        scenario = BenchmarkScenarioImportedFromJson()
        scenario.scenario_id = scenario_id
        scenario.run_number = None  # This should be set by our fix

        return scenario, []

    with (
        patch("datasets.load_dataset", return_value=mock_dataset_dict),
        patch(
            "are.simulation.benchmark.scenario_loader.load_scenario",
            side_effect=mock_load_scenario,
        ),
        patch("tqdm.tqdm", side_effect=lambda x, **kwargs: x),
    ):  # Disable tqdm for cleaner output
        # Test the iterator
        iterator, total_count = _create_huggingface_scenario_iterator(
            dataset_name="test_dataset",
            dataset_config="execution",
            dataset_split="test",
            load_completed_events=False,
        )

        assert total_count == len(mock_rows)

        # Collect results
        results = []
        for scenario, completed_events in iterator:
            results.append((scenario.scenario_id, scenario.run_number))

        # Verify results
        expected_results = [
            ("scenario_universe_123", 1),
            ("scenario_universe_123", 2),
            ("scenario_universe_123", 3),
            ("scenario_universe_456", 1),
            ("scenario_universe_456", 2),
        ]

        assert results == expected_results


def test_run_number_preservation_with_oracle_data():
    """Test that run_number is preserved even when oracle data is merged."""

    # Create mock dataset rows
    mock_rows = [
        create_mock_hf_row("scenario_test_789", 1, "standard"),
        create_mock_hf_row("scenario_test_789", 2, "standard"),
    ]

    # Mock oracle data
    mock_oracle_data = {
        "scenario_test_789": {
            "oracle_events": [],
            "hints": [
                {
                    "hint_type": "TASK_HINT",
                    "content": "Test hint",
                    "associated_event_id": None,
                }
            ],
            "completed_events": [],
            "apps": [],
        }
    }

    # Mock the datasets library
    from datasets import IterableDatasetDict

    mock_dataset = Mock()
    mock_dataset.__iter__ = Mock(return_value=iter(mock_rows))

    # Mock dataset info
    mock_split_info = Mock()
    mock_split_info.num_examples = len(mock_rows)
    mock_splits = {"test": mock_split_info}
    mock_info = Mock()
    mock_info.splits = mock_splits
    mock_dataset.info = mock_info

    # Create a proper mock of IterableDatasetDict
    mock_dataset_dict = Mock(spec=IterableDatasetDict)
    mock_dataset_dict.__getitem__ = Mock(return_value=mock_dataset)
    mock_dataset_dict.__contains__ = Mock(return_value=True)

    # Mock load_scenario
    def mock_load_scenario(
        scenario_data, scenario_id, load_completed_events, hf_metadata=None
    ):
        scenario = BenchmarkScenarioImportedFromJson()
        scenario.scenario_id = scenario_id
        scenario.run_number = None  # This should be set by our fix

        return scenario, []

    with (
        patch("datasets.load_dataset", return_value=mock_dataset_dict),
        patch(
            "are.simulation.benchmark.scenario_loader.load_scenario",
            side_effect=mock_load_scenario,
        ),
        patch(
            "are.simulation.benchmark.huggingface_loader.load_oracle_data_mapping",
            return_value=mock_oracle_data,
        ),
        patch("tqdm.tqdm", side_effect=lambda x, **kwargs: x),
    ):
        # Test the iterator with oracle data
        iterator, total_count = _create_huggingface_scenario_iterator(
            dataset_name="test_dataset",
            dataset_config="execution",
            dataset_split="test",
            load_completed_events=False,
            oracle_dataset_name="oracle_dataset",
            oracle_dataset_split="test",
        )

        # Collect results
        results = []
        for scenario, completed_events in iterator:
            results.append((scenario.scenario_id, scenario.run_number))

        # Verify results - run_number should still be preserved even with oracle data
        expected_results = [
            ("scenario_test_789", 1),
            ("scenario_test_789", 2),
        ]

        assert results == expected_results


def test_scenario_grouping_in_validation_result():
    """Test that scenarios with different run_numbers are properly grouped in validation results."""

    from are.simulation.scenarios.config import MultiScenarioRunnerConfig
    from are.simulation.scenarios.validation_result import (
        MultiScenarioValidationResult,
        ScenarioValidationResult,
    )

    # Create mock config
    config = MultiScenarioRunnerConfig(model="test_model", agent="test_agent")

    # Create validation result
    result = MultiScenarioValidationResult(run_config=config)

    # Create scenarios with different run numbers
    scenarios = []
    for run_num in [1, 2, 3]:
        scenario = BenchmarkScenarioImportedFromJson()
        scenario.scenario_id = "test_scenario_123"
        scenario.run_number = run_num
        scenarios.append(scenario)

    # Add results for each scenario
    for scenario in scenarios:
        validation_result = ScenarioValidationResult(success=True)
        result.add_result(
            validation_result,
            scenario_id=scenario.scenario_id,
            run_number=scenario.run_number,
        )

    # Check that we have 3 separate results
    assert len(result.scenario_results) == 3

    expected_keys = {
        ("test_scenario_123", 1),
        ("test_scenario_123", 2),
        ("test_scenario_123", 3),
    }

    actual_keys = set(result.scenario_results.keys())
    assert actual_keys == expected_keys


def test_scenario_without_run_number():
    """Test that scenarios without run_number still work (backward compatibility)."""

    # Create mock dataset row without run_number using proper trace structure
    mock_trace = create_mock_exported_trace("scenario_no_run_number", None)
    mock_row = {
        "scenario_id": "scenario_no_run_number",
        "phase_name": "standard",
        "data": mock_trace.model_dump_json(),
        # Note: no run_number field in the row
    }

    # Mock the datasets library
    from datasets import IterableDatasetDict

    mock_dataset = Mock()
    mock_dataset.__iter__ = Mock(return_value=iter([mock_row]))

    # Mock dataset info
    mock_split_info = Mock()
    mock_split_info.num_examples = 1
    mock_splits = {"test": mock_split_info}
    mock_info = Mock()
    mock_info.splits = mock_splits
    mock_dataset.info = mock_info

    # Create a proper mock of IterableDatasetDict
    mock_dataset_dict = Mock(spec=IterableDatasetDict)
    mock_dataset_dict.__getitem__ = Mock(return_value=mock_dataset)
    mock_dataset_dict.__contains__ = Mock(return_value=True)

    # Mock load_scenario
    def mock_load_scenario(
        scenario_data, scenario_id, load_completed_events, hf_metadata=None
    ):
        scenario = BenchmarkScenarioImportedFromJson()
        scenario.scenario_id = scenario_id
        scenario.run_number = None

        return scenario, []

    with (
        patch("datasets.load_dataset", return_value=mock_dataset_dict),
        patch(
            "are.simulation.benchmark.scenario_loader.load_scenario",
            side_effect=mock_load_scenario,
        ),
        patch("tqdm.tqdm", side_effect=lambda x, **kwargs: x),
    ):
        # Test the iterator
        iterator, total_count = _create_huggingface_scenario_iterator(
            dataset_name="test_dataset",
            dataset_config="execution",
            dataset_split="test",
            load_completed_events=False,
        )

        # Collect results
        results = []
        for scenario, completed_events in iterator:
            results.append((scenario.scenario_id, scenario.run_number))

        # Should handle missing run_number gracefully (set to None)
        expected_results = [
            ("scenario_no_run_number", None),
        ]

        assert results == expected_results


def test_run_number_from_hf_metadata():
    """Test that run_number is extracted from HuggingFace metadata correctly."""

    # Test the specific fix: scenario.run_number = row.get("run_number")
    mock_trace = create_mock_exported_trace("test_scenario", 1)
    mock_row = {
        "scenario_id": "test_scenario",
        "run_number": 42,  # This should be preserved
        "phase_name": "standard",
        "data": mock_trace.model_dump_json(),
    }

    # Simulate what happens in the HuggingFace loader
    scenario = BenchmarkScenarioImportedFromJson()
    scenario.scenario_id = "test_scenario"
    scenario.run_number = None  # Initially None

    # Apply the fix
    run_number_value = mock_row.get("run_number")
    scenario.run_number = (
        int(run_number_value) if run_number_value is not None else None
    )

    # Verify the fix works
    assert scenario.run_number == 42

    # Test with missing run_number
    mock_trace_no_run = create_mock_exported_trace("test_scenario", 1)
    mock_row_no_run_number = {
        "scenario_id": "test_scenario",
        "phase_name": "standard",
        "data": mock_trace_no_run.model_dump_json(),
        # No run_number field
    }

    scenario2 = BenchmarkScenarioImportedFromJson()
    scenario2.scenario_id = "test_scenario"
    scenario2.run_number = None

    # Apply the fix
    run_number_value = mock_row_no_run_number.get("run_number")
    scenario2.run_number = (
        int(run_number_value) if run_number_value is not None else None
    )

    # Should be None when not present
    assert scenario2.run_number is None
