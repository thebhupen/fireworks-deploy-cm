# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import logging

import fsspec
import fsspec.core

from are.simulation.benchmark.huggingface_loader import huggingface_scenario_iterator
from are.simulation.benchmark.local_loader import local_scenario_iterator
from are.simulation.data_handler.importer import JsonScenarioImporter
from are.simulation.data_handler.models import ExportedHuggingFaceMetadata
from are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario import (
    BenchmarkScenarioImportedFromJson,
)
from are.simulation.types import CompletedEvent
from are.simulation.utils.countable_iterator import CountableIterator

APPS_TO_SKIP = ["SandboxLocalFileSystem"]
DEFAULT_DATASET_SPLIT = "test"

logger: logging.Logger = logging.getLogger(__name__)


def load_scenario(
    scenario_json: str | bytes,
    scenario_path: str,
    load_completed_events: bool,
    hf_metadata: ExportedHuggingFaceMetadata | None = None,
) -> tuple[BenchmarkScenarioImportedFromJson | None, list[CompletedEvent] | None]:
    """Load a scenario from JSON data.

    :param scenario_json: The JSON data containing the scenario definition
    :param scenario_path: Path identifier for the scenario (for logging purposes)
    :param load_completed_events: Whether to load completed events for offline validation
    :param hf_metadata: Optional HuggingFace metadata to attach to the scenario
    :return: Tuple of (scenario, completed_events) or (None, None) if loading fails
    :rtype: tuple[BenchmarkScenarioImportedFromJson | None, list[CompletedEvent] | None]
    """
    scenario_importer = JsonScenarioImporter()
    try:
        scenario, completed_events, _ = scenario_importer.import_from_json_to_benchmark(
            scenario_json,
            apps_to_skip=APPS_TO_SKIP,
            load_completed_events=load_completed_events,
        )

        if scenario is None:
            logger.error(f"Failed to import scenario from {scenario_path}")
            return None, None

        scenario.hf_metadata = hf_metadata
        return scenario, completed_events

    except Exception as e:
        logger.error(f"Failed to load scenario {scenario_path}: {str(e)}", exc_info=e)
        return None, None


def _extract_directory_scenario_paths(
    fs,
    dataset_path: str,
    dataset_config: str | None = None,
    dataset_split: str | None = None,
) -> list[str]:
    """Extract scenario paths from a directory containing JSON files."""
    path = [dataset_path]
    if dataset_config:
        path.append(dataset_config)
    if dataset_split:
        path.append(dataset_split)
    path = fs.sep.join(path)
    if not fs.isdir(path):
        raise FileNotFoundError(f"Dataset directory '{path}' not found.")

    try:
        files = fs.listdir(path, detail=False)
        return [file for file in files if file.endswith(".json") and fs.isfile(file)]
    except Exception as e:
        raise FileNotFoundError(f"Error accessing directory '{path}': {str(e)}")


def _extract_jsonl_scenario_paths(fs, dataset_path: str) -> list[str]:
    """Extract scenario paths from a JSONL file containing trace_id references."""
    scenario_paths = []
    try:
        with fs.open(dataset_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    json_data = json.loads(line.strip())
                    scenario_path = json_data.get("trace_id")
                    if scenario_path is None:
                        logger.warning(f"Missing 'trace_id' in line {line_num}")
                        continue

                    if not fs.isfile(scenario_path) or not scenario_path.endswith(
                        ".json"
                    ):
                        logger.warning(
                            f"Invalid scenario path in line {line_num}: {scenario_path}"
                        )
                        continue

                    scenario_paths.append(scenario_path)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON line {line_num}: {e}")
                    continue
    except Exception as e:
        raise FileNotFoundError(f"Error reading jsonl file '{dataset_path}': {str(e)}")

    return scenario_paths


def _extract_scenario_paths(
    fs,
    dataset_path: str,
    dataset_config: str | None = None,
    dataset_split: str | None = None,
) -> list[str]:
    """
    Extract scenario paths from either a directory or JSONL file.

    Args:
        fs: Filesystem object
        dataset_path: Path to dataset directory or JSONL file
        dataset_config: Optional config name for directory datasets
        dataset_split: Optional split name for directory datasets

    Returns:
        List of scenario file paths

    Raises:
        FileNotFoundError: If dataset path is invalid or inaccessible
        AssertionError: If dataset_config is provided for JSONL files
    """
    # Directory case
    if fs.isdir(dataset_path):
        return _extract_directory_scenario_paths(
            fs, dataset_path, dataset_config, dataset_split
        )

    # JSONL file case
    if fs.isfile(dataset_path) and dataset_path.endswith(".jsonl"):
        if dataset_config is not None:
            raise ValueError("Dataset config not supported for JSONL files.")
        return _extract_jsonl_scenario_paths(fs, dataset_path)

    # Invalid path
    raise FileNotFoundError(
        f"Invalid dataset path '{dataset_path}'. Expected a directory or JSONL file."
    )


def find_scenario_paths(
    dataset_path: str,
    dataset_config: str | None = None,
    dataset_split: str | None = None,
) -> tuple[fsspec.AbstractFileSystem, list[str]]:
    """Find scenario paths in a dataset directory or JSONL file.

    This function locates scenario files in the specified dataset path, which can be
    either a directory containing JSON files or a JSONL file with trace_id references.

    :param dataset_path: Path to the dataset directory or JSONL file
    :param dataset_config: Optional config name (subdirectory) for directory datasets
    :param dataset_split: Optional split name (subdirectory) for directory datasets
    :return: Tuple of (filesystem_object, list_of_scenario_paths)
    :rtype: tuple[fsspec.AbstractFileSystem, list[str]]
    """
    logger.info(f"Finding scenarios in {dataset_path}.")
    fs, path = fsspec.core.url_to_fs(dataset_path)
    scenario_paths = _extract_scenario_paths(fs, path, dataset_config, dataset_split)
    return fs, scenario_paths


def setup_scenarios_iterator(
    dataset_path: str | None,
    dataset_config: str | None,
    dataset_split: str | None,
    hf: str | None,
    hf_revision: str | None,
    load_completed_events: bool = False,
    limit: int | None = None,
    **kwargs,
) -> CountableIterator[tuple[BenchmarkScenarioImportedFromJson, list[CompletedEvent]]]:
    """Set up and return the appropriate scenarios iterator based on input parameters.

    This function determines whether to use a local or HuggingFace dataset iterator
    based on the provided parameters.

    :param dataset_path: Path to local dataset directory or JSONL file (mutually exclusive with hf)
    :param dataset_config: Config name (subdirectory) for the dataset
    :param dataset_split: Split name (subdirectory) for the dataset
    :param hf: HuggingFace dataset name (mutually exclusive with dataset_path)
    :param hf_revision: Revision of the HuggingFace dataset
    :param load_completed_events: Whether to load completed events for offline validation
    :param limit: Maximum number of scenarios to load
    :return: Iterator of scenarios and their completed events
    :rtype: Iterator[tuple[BenchmarkScenarioImportedFromJson, list[CompletedEvent]]]
    :raises ValueError: If neither dataset_path nor hf is specified
    :raises AssertionError: If hf is specified but dataset_config is not
    """

    # Import scenarios
    if hf is not None:
        assert dataset_config is not None, (
            "Config must be specified for HuggingFace datasets."
        )

        hf_kwargs = {}

        scenarios = huggingface_scenario_iterator(
            dataset_name=hf,
            dataset_config=dataset_config,
            dataset_split=dataset_split or "test",
            dataset_revision=hf_revision,
            load_completed_events=load_completed_events,
            limit=limit,
            **hf_kwargs,
        )
    elif dataset_path is not None:
        scenarios = local_scenario_iterator(
            dataset_path=dataset_path,
            dataset_config=dataset_config,
            dataset_split=dataset_split,
            load_completed_events=load_completed_events,
            limit=limit,
        )
    else:
        raise ValueError(
            "One of dataset_path (-d) or HuggingFace datasets (--hf) must be specified."
        )

    return scenarios
