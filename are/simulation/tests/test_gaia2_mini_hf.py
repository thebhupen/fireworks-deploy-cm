# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import pytest
from tqdm import tqdm

from are.simulation.benchmark.huggingface_loader import huggingface_scenario_iterator
from are.simulation.data_handler.exporter import JsonScenarioExporter
from are.simulation.data_handler.importer import JsonScenarioImporter
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario import (
    BenchmarkScenarioImportedFromJson,
)
from are.simulation.tests.utils import IN_GITHUB_ACTIONS
from are.simulation.types import CompletedEvent
from are.simulation.utils.streaming_utils import stream_pool

# Default to the number of processors on the machine
MAX_CONCURRENT_SCENARIOS = None


def _run_scenario_object(
    scenario: BenchmarkScenarioImportedFromJson, scenario_identifier: str
) -> tuple[str, str | None, list[str]]:
    """Run a scenario object (shared logic between file-based and HF-based scenarios)."""
    try:
        scenario.initialize()
    except Exception as e:
        return (
            scenario_identifier,
            scenario.scenario_id,
            [f"Initialization error: {str(e)}"],
        )

    try:
        env = Environment(
            EnvironmentConfig(
                oracle_mode=True,
                queue_based_loop=True,
                start_time=scenario.start_time,
            )
        )
        env.run(scenario)
        env.stop()
    except Exception as e:
        return (
            scenario_identifier,
            scenario.scenario_id,
            [f"Execution error: {str(e)}"],
        )

    failures = [
        f"Event error: {str(e.metadata.exception)}"
        for e in env.event_log.list_view()
        if e.failed()
    ]

    return scenario_identifier, scenario.scenario_id, failures


def _run_scenario_from_hf_tuple(
    scenario_tuple: tuple[BenchmarkScenarioImportedFromJson, list[CompletedEvent]],
) -> tuple[str, str | None, list[str]]:
    """Run a scenario from a HuggingFace tuple (scenario, completed_events)."""
    scenario, _ = scenario_tuple
    return _run_scenario_object(scenario, scenario.scenario_id)


def _run_import_export_from_hf_tuple(
    scenario_tuple: tuple[BenchmarkScenarioImportedFromJson, list[CompletedEvent]],
) -> tuple[str, str | None, list[str]]:
    """
    Run import/export test on a scenario from a HuggingFace tuple.

    This function performs a complete import/export test cycle:
    1. Takes a scenario and completed events from HuggingFace
    2. Initializes the scenario
    3. Exports it to JSON
    4. Re-imports from the exported JSON
    5. Runs the re-imported scenario in oracle mode to verify it works

    Args:
        scenario_tuple: Tuple of (scenario, completed_events) from HuggingFace

    Returns:
        A tuple containing:
        - The scenario ID (used as identifier)
        - The scenario ID (or None if not available)
        - A list of error messages (empty if test succeeded)
    """
    scenario, completed_events = scenario_tuple
    scenario_id = scenario.scenario_id

    # Initialize the original scenario
    try:
        scenario.initialize()
    except Exception as e:
        return (
            scenario_id,
            scenario_id,
            [f"Original scenario initialization error: {str(e)}"],
        )

    # Export the scenario to JSON
    try:
        scenario_exporter = JsonScenarioExporter()
        env = Environment()
        env.event_log = env.event_log.from_list_view(completed_events)
        exported_json = scenario_exporter.export_to_json(
            env=env,
            scenario=scenario,
            scenario_id=scenario.scenario_id,
            runner_config=None,
        )
    except Exception as e:
        return scenario_id, scenario_id, [f"Export error: {str(e)}"]

    # Import the scenario back from the exported string
    try:
        scenario_importer = JsonScenarioImporter()
        reimported_scenario, _, _ = scenario_importer.import_from_json_to_benchmark(
            exported_json,
            apps_to_skip=["SandboxLocalFileSystem"],  # Too slow to run
        )
    except Exception as e:
        return scenario_id, scenario_id, [f"Re-import error: {str(e)}"]

    if reimported_scenario is None:
        return scenario_id, scenario_id, ["Re-imported scenario is None"]

    # Initialize the re-imported scenario
    try:
        reimported_scenario.initialize()
    except Exception as e:
        return (
            scenario_id,
            scenario_id,
            [f"Re-imported scenario initialization error: {str(e)}"],
        )

    if len(reimported_scenario.events) == 0:
        return scenario_id, scenario_id, ["Re-imported scenario has no events."]

    # Run the re-imported scenario in oracle mode
    try:
        env = Environment(
            EnvironmentConfig(
                oracle_mode=True,
                queue_based_loop=True,
                start_time=reimported_scenario.start_time,
            )
        )
        env.run(reimported_scenario)
        env.stop()
    except Exception as e:
        return scenario_id, scenario_id, [f"Execution error: {str(e)}"]

    # Check for failures in the event log
    failures = [
        f"Event error: {str(e.metadata.exception)}"
        for e in env.event_log.list_view()
        if e.failed()
    ]

    return scenario_id, scenario_id, failures


def _test_scenarios_from_iterator(
    scenario_iterator, total_count: int | None, description: str
):
    """
    Test scenarios from an iterator (shared logic for file-based and HF-based scenarios).

    Args:
        scenario_iterator: Iterator yielding (scenario, completed_events) tuples
        total_count: Total number of scenarios (for progress bar)
        description: Description for the progress bar
    """
    failed_scenarios = []

    # Use streaming utils for parallel processing
    with stream_pool(
        scenario_iterator,
        _run_scenario_from_hf_tuple,
        max_workers=MAX_CONCURRENT_SCENARIOS or 4,
        timeout_seconds=300,  # 5 minute timeout per scenario
    ) as results:
        with tqdm(
            total=total_count,
            desc=description,
            unit="scenario",
        ) as pbar:
            for scenario_tuple, result, error in results:
                scenario, _ = scenario_tuple
                scenario_id = scenario.scenario_id

                if error is not None:
                    failed_scenarios.append(
                        f"Scenario {scenario_id} failed with error: {str(error)}"
                    )
                elif result is not None:
                    _, _, failures = result
                    if failures:
                        failure_details = ", ".join(failures)
                        failed_scenarios.append(
                            f"Scenario {scenario_id} failed: {failure_details}"
                        )
                pbar.update(1)

    if failed_scenarios:
        fail_count = len(failed_scenarios)
        total_scenarios = total_count or "unknown"
        pytest.fail(
            f"Had {fail_count} failed scenarios out of {total_scenarios}: "
            + ", ".join(failed_scenarios),
            pytrace=False,
        )


def _test_import_export_from_iterator(
    scenario_iterator, total_count: int | None, description: str
):
    """
    Test import/export functionality for scenarios from an iterator.

    Args:
        scenario_iterator: Iterator yielding (scenario, completed_events) tuples
        total_count: Total number of scenarios (for progress bar)
        description: Description for the progress bar
    """
    failed_scenarios = []

    # Use streaming utils for parallel processing
    with stream_pool(
        scenario_iterator,
        _run_import_export_from_hf_tuple,
        max_workers=MAX_CONCURRENT_SCENARIOS or 4,
        timeout_seconds=300,  # 5 minute timeout per scenario
    ) as results:
        with tqdm(
            total=total_count,
            desc=description,
            unit="scenario",
        ) as pbar:
            for scenario_tuple, result, error in results:
                scenario, _ = scenario_tuple
                scenario_id = scenario.scenario_id

                if error is not None:
                    failed_scenarios.append(
                        f"Scenario {scenario_id} failed with error: {str(error)}"
                    )
                elif result is not None:
                    _, _, failures = result
                    if failures:
                        failure_details = ", ".join(failures)
                        failed_scenarios.append(
                            f"Scenario {scenario_id} failed: {failure_details}"
                        )
                pbar.update(1)

    if failed_scenarios:
        fail_count = len(failed_scenarios)
        total_scenarios = total_count or "unknown"
        pytest.fail(
            f"Had {fail_count} import/export scenarios out of {total_scenarios}: "
            + ", ".join(failed_scenarios),
            pytrace=False,
        )


@pytest.mark.skipif(not IN_GITHUB_ACTIONS, reason="Only runs in GitHub Actions")
@pytest.mark.parametrize("split", ["test", "validation"])
def test_gaia2_mini_scenarios_hf(split: str):
    """Test GAIA2 mini scenarios from HuggingFace (for GitHub Actions)."""
    # Load scenarios from HuggingFace dataset
    scenario_iterator = huggingface_scenario_iterator(
        dataset_name="meta-agents-research-environments/gaia2",
        dataset_config="mini",
        dataset_split=split,
        load_completed_events=False,
        limit=None,  # Load all scenarios
    )

    # Test scenarios using the shared iterator-based logic
    _test_scenarios_from_iterator(
        scenario_iterator,
        scenario_iterator.total_count,
        "Processing GAIA2 mini scenarios from HuggingFace",
    )


@pytest.mark.skipif(not IN_GITHUB_ACTIONS, reason="Only runs in GitHub Actions")
@pytest.mark.parametrize("split", ["test", "validation"])
def test_gaia2_mini_import_export_hf(split: str):
    """Test GAIA2 mini import/export functionality from HuggingFace (for GitHub Actions)."""
    # Load scenarios from HuggingFace dataset
    scenario_iterator = huggingface_scenario_iterator(
        dataset_name="meta-agents-research-environments/gaia2",
        dataset_config="mini",
        dataset_split=split,
        load_completed_events=True,  # Need completed events for export
        limit=None,  # Load all scenarios
    )

    # Test import/export using the shared iterator-based logic
    _test_import_export_from_iterator(
        scenario_iterator,
        scenario_iterator.total_count,
        "Testing GAIA2 mini import/export from HuggingFace",
    )
