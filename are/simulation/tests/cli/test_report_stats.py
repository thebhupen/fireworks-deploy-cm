# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import polars as pl
import pytest

from are.simulation.benchmark.report_stats import (
    _calculate_cross_run_stats,
    _calculate_pass_at_k_stats,
    _calculate_run_duration_stats,
    _calculate_success_rate_stats,
    _count_runs_by_type,
    build_trace_rows_polars,
    calculate_statistics,
    combine_results_to_dataframe,
    generate_json_stats_report,
    generate_validation_report,
    generate_validation_report_content,
    generate_validation_report_header,
)
from are.simulation.scenarios.config import MultiScenarioRunnerConfig
from are.simulation.scenarios.validation_result import (
    MultiScenarioValidationResult,
    ScenarioValidationResult,
)


@pytest.fixture
def mock_run_config():
    """Create a mock MultiScenarioRunnerConfig for testing."""
    config = Mock(spec=MultiScenarioRunnerConfig)
    config.model = "test-model"
    config.model_provider = "test-provider"
    config.agent = "test-agent"
    return config


@pytest.fixture
def sample_scenario_results():
    """Create sample scenario validation results for testing."""
    return [
        ScenarioValidationResult(success=True, rationale="Success case"),
        ScenarioValidationResult(success=False, rationale="Failure case"),
        ScenarioValidationResult(
            success=None, exception=ValueError("Test error"), rationale="Exception case"
        ),
        ScenarioValidationResult(success=None, rationale="No validation case"),
    ]


@pytest.fixture
def sample_multi_scenario_result(mock_run_config):
    """Create a sample MultiScenarioValidationResult for testing."""
    result = MultiScenarioValidationResult(run_config=mock_run_config)

    # Add various scenario results
    result.scenario_results = {
        ("scenario_1", 1): ScenarioValidationResult(
            success=True, rationale="Success 1", export_path="/path/1"
        ),
        ("scenario_1", 2): ScenarioValidationResult(
            success=False, rationale="Failure 1"
        ),
        ("scenario_2", 1): ScenarioValidationResult(
            success=True, rationale="Success 2"
        ),
        ("scenario_2", 2): ScenarioValidationResult(
            success=True, rationale="Success 2b"
        ),
        ("scenario_3", 1): ScenarioValidationResult(
            success=None, exception=ValueError("Test error")
        ),
        ("scenario_4", 1): ScenarioValidationResult(
            success=None, rationale="No validation"
        ),
    }

    # Update counts
    result.successful_count = 3
    result.failed_count = 1
    result.exception_count = 1
    result.no_validation_count = 1

    return result


@pytest.fixture
def sample_results_dict(sample_multi_scenario_result):
    """Create a sample results dictionary for combine_results_to_dataframe."""
    return {
        ("phase1", "execution", 0.5, True, False): sample_multi_scenario_result,
        ("phase2", "search", 0.3, False, True): sample_multi_scenario_result,
    }


@pytest.fixture
def sample_dataframe():
    """Create a sample polars DataFrame for testing statistics functions."""
    data = [
        {
            "base_scenario_id": "scenario_1",
            "run_number": 1,
            "success_numeric": 1.0,
            "success_bool": True,
            "status": "success",
            "has_exception": False,
            "exception_type": None,
            "exception_message": None,
            "rationale": "Success 1",
            "export_path": "/path/1",
            "model": "test-model",
            "model_provider": "test-provider",
            "agent": "test-agent",
            "phase_name": "phase1",
            "config": "execution",
            "a2a_app_prop": 0.5,
            "has_tool_augmentation": True,
            "has_env_events": False,
            "run_duration": 120.5,
            "job_duration": 300.0,
        },
        {
            "base_scenario_id": "scenario_1",
            "run_number": 2,
            "success_numeric": 0.0,
            "success_bool": False,
            "status": "failed",
            "has_exception": False,
            "exception_type": None,
            "exception_message": None,
            "rationale": "Failure 1",
            "export_path": None,
            "model": "test-model",
            "model_provider": "test-provider",
            "agent": "test-agent",
            "phase_name": "phase1",
            "config": "execution",
            "a2a_app_prop": 0.5,
            "has_tool_augmentation": True,
            "has_env_events": False,
            "run_duration": 95.3,
            "job_duration": 300.0,
        },
        {
            "base_scenario_id": "scenario_2",
            "run_number": 1,
            "success_numeric": 1.0,
            "success_bool": True,
            "status": "success",
            "has_exception": False,
            "exception_type": None,
            "exception_message": None,
            "rationale": "Success 2",
            "export_path": None,
            "model": "test-model",
            "model_provider": "test-provider",
            "agent": "test-agent",
            "phase_name": "phase2",
            "config": "search",
            "a2a_app_prop": 0.3,
            "has_tool_augmentation": False,
            "has_env_events": True,
            "run_duration": 150.7,
            "job_duration": 300.0,
        },
        {
            "base_scenario_id": "scenario_3",
            "run_number": 1,
            "success_numeric": None,
            "success_bool": None,
            "status": "exception",
            "has_exception": True,
            "exception_type": "ValueError",
            "exception_message": "Test error",
            "rationale": None,
            "export_path": None,
            "model": "test-model",
            "model_provider": "test-provider",
            "agent": "test-agent",
            "phase_name": "phase1",
            "config": "execution",
            "a2a_app_prop": 0.5,
            "has_tool_augmentation": True,
            "has_env_events": False,
            "run_duration": 30.2,
            "job_duration": 300.0,
        },
    ]
    return pl.DataFrame(data)


class TestCombineResultsToDataframe:
    """Test the combine_results_to_dataframe function."""

    def test_combine_results_empty_dict(self):
        """Test with empty results dictionary."""
        result = combine_results_to_dataframe({})
        assert result.is_empty()
        assert len(result.columns) == 20  # Expected schema columns

    def test_combine_results_with_data(self, sample_results_dict):
        """Test with actual data."""
        result = combine_results_to_dataframe(sample_results_dict)
        assert not result.is_empty()
        assert len(result) == 12  # 6 scenarios × 2 phases

        # Check that metadata columns are added
        assert "phase_name" in result.columns
        assert "config" in result.columns
        assert "a2a_app_prop" in result.columns
        assert "has_tool_augmentation" in result.columns
        assert "has_env_events" in result.columns


class TestCountRunsByType:
    """Test the _count_runs_by_type function."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pl.DataFrame()
        counts = _count_runs_by_type(empty_df)

        expected = {
            "total_runs": 0,
            "validated_runs": 0,
            "success_runs": 0,
            "failed_runs": 0,
            "exception_runs": 0,
            "no_validation_runs": 0,
        }
        assert counts == expected

    def test_with_sample_data(self, sample_dataframe):
        """Test with sample data."""
        counts = _count_runs_by_type(sample_dataframe)

        # Expected counts from sample data:
        # - Total: 4 runs
        # - Validated: 3 runs (non-null success_numeric)
        # - Success: 2 runs
        # - Failed: 1 run
        # - Exception: 1 run
        # - No validation: 0 runs
        expected = {
            "total_runs": 4,
            "validated_runs": 3,
            "success_runs": 2,
            "failed_runs": 1,
            "exception_runs": 1,
            "no_validation_runs": 0,
        }
        assert counts == expected

    def test_run_type_assumptions(self, sample_dataframe):
        """Test that our assumptions about run types are correct."""
        counts = _count_runs_by_type(sample_dataframe)

        # Key assumption: total_runs = validated_runs + exception_runs + no_validation_runs
        assert counts["total_runs"] == (
            counts["validated_runs"]
            + counts["exception_runs"]
            + counts["no_validation_runs"]
        )

        # Key assumption: validated_runs = success_runs + failed_runs
        assert counts["validated_runs"] == (
            counts["success_runs"] + counts["failed_runs"]
        )


class TestCalculateSuccessRateStats:
    """Test the _calculate_success_rate_stats function."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        # Create empty DataFrame with expected schema
        empty_df = pl.DataFrame(
            schema={
                "success_numeric": pl.Float64,
                "run_number": pl.Int64,
                "base_scenario_id": pl.Utf8,
                "phase_name": pl.Utf8,
                "a2a_app_prop": pl.Float64,
                "has_tool_augmentation": pl.Boolean,
                "has_env_events": pl.Boolean,
                "run_duration": pl.Float64,
                "job_duration": pl.Float64,
            }
        )
        stats = _calculate_success_rate_stats(empty_df)

        expected = {
            "success_rate": 0.0,
            "success_rate_std": 0.0,
            "success_rate_sem": 0.0,
        }
        assert stats == expected

    def test_with_sample_data(self, sample_dataframe):
        """Test with sample data."""
        stats = _calculate_success_rate_stats(sample_dataframe)

        # From sample data: 2 successes out of 3 validated runs = 66.67%
        assert abs(stats["success_rate"] - 66.66666666666667) < 0.001
        assert stats["success_rate_std"] >= 0.0
        assert stats["success_rate_sem"] >= 0.0

    def test_only_validated_runs_counted(self):
        """Test that only validated runs (non-null success_numeric) are counted."""
        data = [
            {
                "success_numeric": 1.0,
                "status": "success",
                "run_number": 1,
                "base_scenario_id": "s1",
                "phase_name": "test",
                "run_duration": 100.0,
                "job_duration": 300.0,
            },
            {
                "success_numeric": 0.0,
                "status": "failed",
                "run_number": 1,
                "base_scenario_id": "s2",
                "phase_name": "test",
                "run_duration": 150.0,
                "job_duration": 300.0,
            },
            {
                "success_numeric": None,
                "status": "exception",
                "run_number": 1,
                "base_scenario_id": "s3",
                "phase_name": "test",
                "run_duration": 75.0,
                "job_duration": 300.0,
            },
            {
                "success_numeric": None,
                "status": "no_validation",
                "run_number": 1,
                "base_scenario_id": "s4",
                "phase_name": "test",
                "run_duration": 50.0,
                "job_duration": 300.0,
            },
        ]
        df = pl.DataFrame(data)

        stats = _calculate_success_rate_stats(df)

        # Only the first 2 runs should be counted: 1 success out of 2 = 50%
        assert stats["success_rate"] == 50.0


class TestCalculateRunDurationStats:
    """Test the _calculate_run_duration_stats function."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pl.DataFrame(
            schema={
                "run_duration": pl.Float64,
            }
        )
        stats = _calculate_run_duration_stats(empty_df)

        expected = {
            "avg_run_duration": 0.0,
            "avg_run_duration_std": 0.0,
        }
        assert stats == expected

    def test_with_sample_data(self, sample_dataframe):
        """Test with sample data."""
        stats = _calculate_run_duration_stats(sample_dataframe)

        # From sample data: durations are 120.5, 95.3, 150.7, 30.2
        # Average should be around 99.175
        expected_avg = (120.5 + 95.3 + 150.7 + 30.2) / 4
        assert abs(stats["avg_run_duration"] - expected_avg) < 0.001
        assert stats["avg_run_duration_std"] >= 0.0

    def test_only_non_null_duration_counted(self):
        """Test that only runs with non-null run_duration are counted."""
        data = [
            {
                "run_duration": 100.0,
                "base_scenario_id": "s1",
                "phase_name": "test",
            },
            {
                "run_duration": 200.0,
                "base_scenario_id": "s2",
                "phase_name": "test",
            },
            {
                "run_duration": None,
                "base_scenario_id": "s3",
                "phase_name": "test",
            },
        ]
        df = pl.DataFrame(data)

        stats = _calculate_run_duration_stats(df)

        # Only the first 2 runs should be counted: (100 + 200) / 2 = 150
        assert stats["avg_run_duration"] == 150.0


class TestCalculatePassAtKStats:
    """Test the _calculate_pass_at_k_stats function."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        # Create empty DataFrame with expected schema
        empty_df = pl.DataFrame(
            schema={
                "success_numeric": pl.Float64,
                "base_scenario_id": pl.Utf8,
                "phase_name": pl.Utf8,
            }
        )
        stats = _calculate_pass_at_k_stats(empty_df)

        expected = {
            "pass_at_k": 0,
            "pass_at_k_percent": 0.0,
            "pass_k": 0,
            "pass_k_percent": 0.0,
            "total_scenarios": 0,
        }
        assert stats == expected

    def test_with_sample_data(self, sample_dataframe):
        """Test with sample data."""
        stats = _calculate_pass_at_k_stats(sample_dataframe)

        # From sample data:
        # - scenario_1: 50% success rate (1 success, 1 failure) -> Pass@k but not Pass^k
        # - scenario_2: 100% success rate (1/1) -> Both Pass@k and Pass^k
        # - scenario_3: exception (not counted in validated scenarios)
        # Total scenarios: 3 (including non-validated ones)

        assert stats["total_scenarios"] == 3
        assert stats["pass_at_k"] == 2  # scenarios 1, 2 have at least one success
        assert stats["pass_k"] == 1  # only scenario 2 has all successes
        assert abs(stats["pass_at_k_percent"] - 66.66666666666667) < 0.001
        assert abs(stats["pass_k_percent"] - 33.33333333333333) < 0.001


class TestCalculateCrossRunStats:
    """Test the _calculate_cross_run_stats function."""

    def test_macro_vs_micro_difference(self):
        """Test that macro and micro calculations produce different results when appropriate."""
        # Create capability stats where one capability has more runs than another
        capability_stats = {
            "cap1": {
                "success_rate": 100.0,  # 100% success rate
                "validated_runs": 1,  # but only 1 run
            },
            "cap2": {
                "success_rate": 0.0,  # 0% success rate
                "validated_runs": 9,  # but 9 runs
            },
        }

        # Create corresponding DataFrame
        data = []
        # Cap1: 1 success
        data.append(
            {
                "config": "cap1",
                "success_numeric": 1.0,
                "run_number": 1,
                "phase_name": "test_phase",
            }
        )
        # Cap2: 9 failures
        for i in range(9):
            data.append(
                {
                    "config": "cap2",
                    "success_numeric": 0.0,
                    "run_number": 1,
                    "phase_name": "test_phase",
                }
            )

        df = pl.DataFrame(data)

        macro_stats = _calculate_cross_run_stats(df, capability_stats, "macro")
        micro_stats = _calculate_cross_run_stats(df, capability_stats, "micro")

        # Macro: (100 + 0) / 2 = 50%
        assert macro_stats["macro_success_rate"] == 50.0

        # Micro: (100*1 + 0*9) / (1+9) = 10%
        assert micro_stats["micro_success_rate"] == 10.0

    def test_invalid_aggregation_type(self):
        """Test that invalid aggregation type raises ValueError."""
        df = pl.DataFrame([{"config": "test", "success_numeric": 1.0, "run_number": 1}])
        capability_stats = {"test": {"success_rate": 100.0, "validated_runs": 1}}

        with pytest.raises(ValueError, match="Unknown aggregation_type"):
            _calculate_cross_run_stats(df, capability_stats, "invalid")


class TestCalculateStatistics:
    """Test the main calculate_statistics function."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pl.DataFrame()
        stats = calculate_statistics(empty_df)

        assert "per_capability" in stats
        assert "global" in stats
        assert stats["per_capability"] == {}
        assert stats["global"]["total_scenarios"] == 0

    def test_with_sample_data(self, sample_dataframe):
        """Test with sample data."""
        stats = calculate_statistics(sample_dataframe)

        assert "per_capability" in stats
        assert "global" in stats

        # Check that capabilities are present
        assert "execution" in stats["per_capability"]
        assert "search" in stats["per_capability"]

        # Check structure of per-capability stats
        for capability_stats in stats["per_capability"].values():
            assert "total_scenarios" in capability_stats
            assert "success_rate" in capability_stats
            assert "success_rate_std" in capability_stats
            assert "success_rate_sem" in capability_stats
            assert "pass_at_k" in capability_stats
            assert "pass_k" in capability_stats
            assert "avg_run_duration" in capability_stats
            assert "avg_run_duration_std" in capability_stats

        # Check global stats structure
        global_stats = stats["global"]
        assert "total_scenarios" in global_stats
        assert "macro_success_rate" in global_stats
        assert "micro_success_rate" in global_stats
        assert "macro_success_rate_std" in global_stats
        assert "micro_success_rate_std" in global_stats
        assert "macro_success_rate_sem" in global_stats
        assert "micro_success_rate_sem" in global_stats
        assert "avg_run_duration" in global_stats
        assert "avg_run_duration_std" in global_stats
        assert "job_duration" in global_stats

    def test_mini_capability_phase_separation(self):
        """Test that mini capability is properly separated by phase."""
        data = [
            # Mini capability in agent2agent phase
            {
                "base_scenario_id": "scenario_1",
                "run_number": 1,
                "success_numeric": 1.0,
                "success_bool": True,
                "status": "success",
                "has_exception": False,
                "exception_type": None,
                "exception_message": None,
                "rationale": "Success in agent2agent",
                "export_path": None,
                "model": "test-model",
                "model_provider": "test-provider",
                "agent": "test-agent",
                "phase_name": "agent2agent",
                "config": "mini",
                "a2a_app_prop": 1.0,
                "has_tool_augmentation": False,
                "has_env_events": False,
                "run_duration": 100.0,
                "job_duration": 300.0,
            },
            # Mini capability in noise phase
            {
                "base_scenario_id": "scenario_2",
                "run_number": 1,
                "success_numeric": 0.0,
                "success_bool": False,
                "status": "failed",
                "has_exception": False,
                "exception_type": None,
                "exception_message": None,
                "rationale": "Failure in noise",
                "export_path": None,
                "model": "test-model",
                "model_provider": "test-provider",
                "agent": "test-agent",
                "phase_name": "noise",
                "config": "mini",
                "a2a_app_prop": 0.0,
                "has_tool_augmentation": True,
                "has_env_events": True,
                "run_duration": 150.0,
                "job_duration": 300.0,
            },
        ]
        df = pl.DataFrame(data)

        stats = calculate_statistics(df)

        # Check that mini capabilities are separated by phase
        assert "mini_agent2agent" in stats["per_capability"]
        assert "mini_noise" in stats["per_capability"]
        assert "mini" not in stats["per_capability"]  # Should not have generic mini

        # Check that the display names include phase information
        assert (
            stats["per_capability"]["mini_agent2agent"]["capability"]
            == "mini (agent2agent)"
        )
        assert stats["per_capability"]["mini_noise"]["capability"] == "mini (noise)"

        # Check that each phase has the correct statistics
        a2a_stats = stats["per_capability"]["mini_agent2agent"]
        noise_stats = stats["per_capability"]["mini_noise"]

        assert a2a_stats["success_rate"] == 100.0  # 1 success out of 1
        assert noise_stats["success_rate"] == 0.0  # 0 success out of 1

    def test_non_mini_capability_unchanged(self):
        """Test that non-mini capabilities work the same as before."""
        data = [
            {
                "base_scenario_id": "scenario_1",
                "run_number": 1,
                "success_numeric": 1.0,
                "success_bool": True,
                "status": "success",
                "has_exception": False,
                "exception_type": None,
                "exception_message": None,
                "rationale": "Success",
                "export_path": None,
                "model": "test-model",
                "model_provider": "test-provider",
                "agent": "test-agent",
                "phase_name": "standard",
                "config": "execution",
                "a2a_app_prop": 0.0,
                "has_tool_augmentation": False,
                "has_env_events": False,
                "run_duration": 100.0,
                "job_duration": 300.0,
            },
        ]
        df = pl.DataFrame(data)

        stats = calculate_statistics(df)

        # Non-mini capabilities should use the config name as the key
        assert "execution" in stats["per_capability"]
        assert "execution_standard" not in stats["per_capability"]

        # Display name should be the same as config for non-mini
        assert stats["per_capability"]["execution"]["capability"] == "execution"

    def test_mixed_capabilities_and_phases(self):
        """Test with a mix of mini and non-mini capabilities across phases."""
        data = [
            # Standard execution capability
            {
                "base_scenario_id": "scenario_1",
                "run_number": 1,
                "success_numeric": 1.0,
                "success_bool": True,
                "status": "success",
                "has_exception": False,
                "exception_type": None,
                "exception_message": None,
                "rationale": "Success",
                "export_path": None,
                "model": "test-model",
                "model_provider": "test-provider",
                "agent": "test-agent",
                "phase_name": "standard",
                "config": "execution",
                "a2a_app_prop": 0.0,
                "has_tool_augmentation": False,
                "has_env_events": False,
                "run_duration": 120.0,
                "job_duration": 300.0,
            },
            # Mini in agent2agent phase
            {
                "base_scenario_id": "scenario_2",
                "run_number": 1,
                "success_numeric": 0.0,
                "success_bool": False,
                "status": "failed",
                "has_exception": False,
                "exception_type": None,
                "exception_message": None,
                "rationale": "Failure",
                "export_path": None,
                "model": "test-model",
                "model_provider": "test-provider",
                "agent": "test-agent",
                "phase_name": "agent2agent",
                "config": "mini",
                "a2a_app_prop": 1.0,
                "has_tool_augmentation": False,
                "has_env_events": False,
                "run_duration": 90.0,
                "job_duration": 300.0,
            },
            # Mini in noise phase
            {
                "base_scenario_id": "scenario_3",
                "run_number": 1,
                "success_numeric": 1.0,
                "success_bool": True,
                "status": "success",
                "has_exception": False,
                "exception_type": None,
                "exception_message": None,
                "rationale": "Success",
                "export_path": None,
                "model": "test-model",
                "model_provider": "test-provider",
                "agent": "test-agent",
                "phase_name": "noise",
                "config": "mini",
                "a2a_app_prop": 0.0,
                "has_tool_augmentation": True,
                "has_env_events": True,
                "run_duration": 110.0,
                "job_duration": 300.0,
            },
        ]
        df = pl.DataFrame(data)

        stats = calculate_statistics(df)

        # Should have 3 separate capability entries
        assert len(stats["per_capability"]) == 3
        assert "execution" in stats["per_capability"]
        assert "mini_agent2agent" in stats["per_capability"]
        assert "mini_noise" in stats["per_capability"]

        # Check that global stats aggregate correctly
        assert stats["global"]["total_scenarios"] == 3
        assert stats["global"]["validated_runs"] == 3

    def test_json_text_report_consistency(self, sample_dataframe):
        """Test that JSON and text reports use the same statistics."""
        # Generate both reports
        json_report = generate_json_stats_report(
            sample_dataframe, "test-model", "test-provider"
        )
        text_report = generate_validation_report(
            sample_dataframe, "test-model", "test-provider"
        )

        # Both should use the same underlying statistics
        json_stats = json_report["statistics"]

        # Verify that the statistics are consistent
        assert "per_capability" in json_stats
        assert "global" in json_stats

        # The text report should contain the same numerical values
        global_stats = json_stats["global"]
        assert f"{global_stats['macro_success_rate']:.1f}%" in text_report
        assert f"{global_stats['micro_success_rate']:.1f}%" in text_report


class TestRunTypeAssumptions:
    """Test our key assumptions about run types and counting."""

    def test_total_runs_breakdown(self, sample_dataframe):
        """Test that total runs = validated + exception + no_validation."""
        stats = calculate_statistics(sample_dataframe)
        global_stats = stats["global"]

        assert global_stats["total_runs"] == (
            global_stats["validated_runs"]
            + global_stats["exception_runs"]
            + global_stats["no_validation_runs"]
        )

    def test_validated_runs_breakdown(self, sample_dataframe):
        """Test that validated runs = success + failed."""
        stats = calculate_statistics(sample_dataframe)
        global_stats = stats["global"]

        assert global_stats["validated_runs"] == (
            global_stats["success_runs"] + global_stats["failed_runs"]
        )

    def test_success_rate_only_from_validated_runs(self):
        """Test that success rate is calculated only from validated runs."""
        data = [
            # 2 validated runs: 1 success, 1 failure -> 50% success rate
            {
                "success_numeric": 1.0,
                "status": "success",
                "run_number": 1,
                "config": "test",
                "phase_name": "test_phase",
                "base_scenario_id": "s1",
                "run_duration": 120.0,
                "job_duration": 300.0,
            },
            {
                "success_numeric": 0.0,
                "status": "failed",
                "run_number": 1,
                "config": "test",
                "phase_name": "test_phase",
                "base_scenario_id": "s2",
                "run_duration": 90.0,
                "job_duration": 300.0,
            },
            # 2 non-validated runs: should not affect success rate
            {
                "success_numeric": None,
                "status": "exception",
                "run_number": 1,
                "config": "test",
                "phase_name": "test_phase",
                "base_scenario_id": "s3",
            },
            {
                "success_numeric": None,
                "status": "no_validation",
                "run_number": 1,
                "config": "test",
                "phase_name": "test_phase",
                "base_scenario_id": "s4",
            },
        ]
        df = pl.DataFrame(data)

        stats = calculate_statistics(df)

        # Success rate should be 50% (1 success out of 2 validated runs)
        # Not 25% (1 success out of 4 total runs)
        assert stats["per_capability"]["test"]["success_rate"] == 50.0

    def test_exception_runs_excluded_from_success_rate(self):
        """Test that exception runs are excluded from success rate calculations."""
        data = [
            {
                "success_numeric": 1.0,
                "status": "success",
                "run_number": 1,
                "config": "test",
                "phase_name": "test_phase",
                "base_scenario_id": "s1",
            },
            {
                "success_numeric": None,
                "status": "exception",
                "run_number": 1,
                "config": "test",
                "phase_name": "test_phase",
                "base_scenario_id": "s2",
                "run_duration": 75.0,
                "job_duration": 300.0,
            },
        ]
        df = pl.DataFrame(data)

        stats = calculate_statistics(df)

        # Success rate should be 100% (1 success out of 1 validated run)
        # Exception run should not be counted in the denominator
        assert stats["per_capability"]["test"]["success_rate"] == 100.0
        assert stats["per_capability"]["test"]["validated_runs"] == 1
        assert stats["per_capability"]["test"]["exception_runs"] == 1


class TestGenerateValidationReportHeader:
    """Test the generate_validation_report_header function."""

    def test_header_generation(self):
        """Test header generation with model and provider."""
        header = generate_validation_report_header("test-model", "test-provider")

        assert "GAIA2 Validation Report" in header
        assert "test-model" in header
        assert "test-provider" in header


class TestGenerateValidationReportContent:
    """Test the generate_validation_report_content function."""

    def test_content_generation(self, sample_dataframe):
        """Test content generation with sample data."""
        content = generate_validation_report_content(sample_dataframe)

        assert "Macro success rate" in content
        assert "Micro success rate" in content
        assert "Execution" in content
        assert "Search" in content
        assert "Global Summary" in content

    def test_different_header_formats(self, sample_dataframe):
        """Test different header format options."""
        # Test markdown format
        content_md = generate_validation_report_content(
            sample_dataframe, header_format="###", header_prefix="", header_suffix=""
        )
        assert "### Execution" in content_md

        # Test with prefix and suffix
        content_custom = generate_validation_report_content(
            sample_dataframe,
            header_format="####",
            header_prefix="Capability: ",
            header_suffix=" Results",
        )
        assert "#### Capability: Execution Results" in content_custom


class TestGenerateValidationReport:
    """Test the generate_validation_report function."""

    def test_validation_report_generation(self, sample_dataframe):
        """Test validation report generation."""
        report = generate_validation_report(
            sample_dataframe, "test-model", "test-provider"
        )

        assert "GAIA2 Validation Report" in report
        assert "test-model" in report
        assert "test-provider" in report
        assert "Macro success rate" in report
        assert "Micro success rate" in report


class TestGenerateJsonStatsReport:
    """Test the generate_json_stats_report function."""

    def test_json_report_structure(self, sample_dataframe):
        """Test JSON report structure."""
        report = generate_json_stats_report(
            sample_dataframe, "test-model", "test-provider"
        )

        assert "metadata" in report
        assert "statistics" in report
        assert "run_configurations" in report

        # Check metadata
        assert report["metadata"]["model"] == "test-model"
        assert report["metadata"]["model_provider"] == "test-provider"
        assert "timestamp" in report["metadata"]
        assert report["metadata"]["report_version"] == "3.0"

        # Check statistics structure
        assert "per_capability" in report["statistics"]
        assert "global" in report["statistics"]

    def test_empty_dataframe_json_report(self):
        """Test JSON report with empty DataFrame."""
        empty_df = pl.DataFrame()
        report = generate_json_stats_report(empty_df, "test-model", "test-provider")

        assert report["run_configurations"] == []
        assert report["statistics"]["global"]["total_scenarios"] == 0


class TestBuildTraceRowsPolars:
    """Test the build_trace_rows_polars function."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        empty_df = pl.DataFrame()
        rows = build_trace_rows_polars(empty_df)
        assert rows == []

    def test_with_sample_data(self, sample_dataframe):
        """Test with sample data."""
        rows = build_trace_rows_polars(sample_dataframe)

        assert len(rows) == len(sample_dataframe)

        # Check first row structure
        first_row = rows[0]
        expected_keys = {
            "scenario_id",
            "run_number",
            "task_id",
            "score",
            "status",
            "data",
            "has_exception",
            "exception_type",
            "exception_message",
            "rationale",
            "config",
            "phase_name",
            "a2a_app_prop",
            "has_app_noise",
            "has_env_noise",
        }
        assert set(first_row.keys()).issubset(expected_keys)

    def test_trace_file_reading(self, sample_dataframe):
        """Test reading trace files when export_path is provided."""
        # Create a temporary file with test data
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            test_data = {"test": "data"}
            f.write(json.dumps(test_data))
            temp_path = f.name

        try:
            # Update the DataFrame to include the temp file path
            df_with_path = sample_dataframe.with_columns(
                pl.when(pl.col("export_path") == "/path/1")
                .then(pl.lit(temp_path))
                .otherwise(pl.col("export_path"))
                .alias("export_path")
            )

            rows = build_trace_rows_polars(df_with_path)

            # Find the row with the trace file
            row_with_data = next((row for row in rows if row.get("data")), None)
            assert row_with_data is not None
            assert json.dumps(test_data) in row_with_data["data"]

        finally:
            # Clean up
            Path(temp_path).unlink()

    @patch("are.simulation.benchmark.report_stats.logger")
    def test_trace_file_reading_error(self, mock_logger, sample_dataframe):
        """Test handling of file reading errors."""
        # Update DataFrame with non-existent file path
        df_with_bad_path = sample_dataframe.with_columns(
            pl.when(pl.col("export_path") == "/path/1")
            .then(pl.lit("/nonexistent/path"))
            .otherwise(pl.col("export_path"))
            .alias("export_path")
        )

        rows = build_trace_rows_polars(df_with_bad_path)

        # Should still return rows, but with None data
        assert len(rows) == len(df_with_bad_path)

        # Check that warning was logged
        mock_logger.warning.assert_called()

    def test_none_values_filtered_out(self):
        """Test that None values are filtered out of the final rows."""
        data = [
            {
                "base_scenario_id": "test",
                "run_number": 1,
                "success_numeric": 1.0,
                "status": "success",
                "has_exception": False,
                "exception_type": None,  # This should be filtered out
                "exception_message": None,  # This should be filtered out
                "rationale": "Test rationale",
                "config": "test",
                "phase_name": "test",
                "a2a_app_prop": 0.5,
                "has_tool_augmentation": True,
                "has_env_events": False,
                "export_path": None,  # This should be filtered out
            }
        ]
        df = pl.DataFrame(data)
        rows = build_trace_rows_polars(df)

        assert len(rows) == 1
        row = rows[0]

        # None values should be filtered out
        assert "exception_type" not in row
        assert "exception_message" not in row
        assert "data" not in row  # export_path was None, so no data


class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_pipeline(self, sample_results_dict):
        """Test the full pipeline from results dict to final reports."""
        # Convert to DataFrame
        df = combine_results_to_dataframe(sample_results_dict)
        assert not df.is_empty()

        # Calculate statistics
        stats = calculate_statistics(df)

        assert stats["global"]["total_scenarios"] > 0
        assert len(stats["per_capability"]) > 0

        # Generate reports
        validation_report = generate_validation_report(
            df, "test-model", "test-provider"
        )
        json_report = generate_json_stats_report(df, "test-model", "test-provider")

        assert "GAIA2 Validation Report" in validation_report
        assert json_report["metadata"]["model"] == "test-model"

        # Build trace rows
        trace_rows = build_trace_rows_polars(df)
        assert len(trace_rows) == len(df)

    def test_edge_case_all_successful(self):
        """Test edge case where all scenarios are successful."""
        data = [
            {
                "base_scenario_id": f"scenario_{i}",
                "run_number": 1,
                "success_numeric": 1.0,
                "success_bool": True,
                "status": "success",
                "has_exception": False,
                "exception_type": None,
                "exception_message": None,
                "rationale": f"Success {i}",
                "export_path": None,
                "model": "test-model",
                "model_provider": "test-provider",
                "agent": "test-agent",
                "phase_name": "test_phase",
                "config": "test_config",
                "a2a_app_prop": 0.5,
                "has_tool_augmentation": False,
                "has_env_events": False,
                "run_duration": 100.0,
                "job_duration": 300.0,
            }
            for i in range(5)
        ]
        df = pl.DataFrame(data)

        stats = calculate_statistics(df)
        assert stats["global"]["macro_success_rate"] == 100.0
        assert stats["global"]["micro_success_rate"] == 100.0

    def test_edge_case_all_failed(self):
        """Test edge case where all scenarios fail."""
        data = [
            {
                "base_scenario_id": f"scenario_{i}",
                "run_number": 1,
                "success_numeric": 0.0,
                "success_bool": False,
                "status": "failed",
                "has_exception": False,
                "exception_type": None,
                "exception_message": None,
                "rationale": f"Failure {i}",
                "export_path": None,
                "model": "test-model",
                "model_provider": "test-provider",
                "agent": "test-agent",
                "phase_name": "test_phase",
                "config": "test_config",
                "a2a_app_prop": 0.5,
                "has_tool_augmentation": False,
                "has_env_events": False,
                "run_duration": 100.0,
                "job_duration": 300.0,
            }
            for i in range(5)
        ]
        df = pl.DataFrame(data)

        stats = calculate_statistics(df)
        assert stats["global"]["macro_success_rate"] == 0.0
        assert stats["global"]["micro_success_rate"] == 0.0
