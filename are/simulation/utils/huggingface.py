# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging

from datasets import IterableDataset, load_dataset

logger = logging.getLogger(__name__)


def get_huggingface_dataset_configs(dataset_name: str) -> list[str] | None:
    """
    List available configs in a Huggingface dataset.

    Args:
        dataset_name: The name of the Huggingface dataset

    Returns:
        A list of config names
    """
    try:
        from datasets import get_dataset_config_names

        config_names = get_dataset_config_names(dataset_name)
        return config_names
    except Exception as e:
        logger.exception(
            f"Failed to list configs from Huggingface dataset {dataset_name}",
            exc_info=e,
        )
        return None


def get_huggingface_dataset_splits(
    dataset_name: str, dataset_config: str
) -> list[str] | None:
    """
    List available configs in a Huggingface dataset.

    Args:
        dataset_name: The name of the Huggingface dataset
        dataset_config: The config name of the Huggingface dataset

    Returns:
        A list of splits
    """
    try:
        from datasets import get_dataset_split_names

        split_names = get_dataset_split_names(dataset_name, dataset_config)
        return split_names
    except Exception as e:
        logger.exception(
            f"Failed to list splits from Huggingface dataset {dataset_name}/{dataset_config}",
            exc_info=e,
        )
        return None


def list_huggingface_scenarios(
    dataset_name: str, dataset_config: str, dataset_split: str
) -> list[str] | None:
    """
    List available scenarios in a Huggingface dataset.

    Args:
        dataset_name: The name of the Huggingface dataset
        dataset_config: The config name of the Huggingface dataset
        dataset_split: The split of the Huggingface dataset

    Returns:
        A list of scenario IDs
    """
    try:
        logger.info(
            f"Loading scenarios from Huggingface dataset {dataset_name}/{dataset_config}/{dataset_split}"
        )
        ds = load_dataset(
            dataset_name,
            name=dataset_config,
            split=dataset_split,
            streaming=True,
            columns=["scenario_id"],
        )

        assert isinstance(ds, IterableDataset), (
            f"wrong type for the dataset {dataset_name}/{dataset_config}"
        )

        # Get all scenario IDs from the dataset
        scenario_ids = []
        for row in ds:
            scenario_id = row.get("scenario_id")
            if scenario_id:
                scenario_ids.append(scenario_id)

        return scenario_ids
    except Exception as e:
        logger.exception(
            f"Failed to list scenarios from Huggingface dataset {dataset_name}/{dataset_config}/{dataset_split}: {e}"
        )
        return None


def get_scenario_from_huggingface(
    dataset_name: str, dataset_config: str, dataset_split: str, scenario_id: str
) -> str | None:
    """
    Get a specific scenario from a Huggingface dataset.

    Args:
        dataset_name: The name of the Huggingface dataset
        dataset_config: The config name of the Huggingface dataset
        dataset_split: The split of the Huggingface dataset
        scenario_id: The ID of the scenario to retrieve

    Returns:
        The scenario data as a JSON string, or None if not found
    """
    try:
        logger.info(
            f"Loading scenario {scenario_id} from Huggingface dataset {dataset_name}/{dataset_config}/{dataset_split}"
        )

        # Load the dataset
        ds = load_dataset(
            dataset_name, name=dataset_config, split=dataset_split, streaming=True
        )
        assert isinstance(ds, IterableDataset), (
            f"Looks like the {dataset_name} is not compatible."
        )

        # Find the scenario with the given ID
        for row in ds:
            if row.get("scenario_id") == scenario_id:
                scenario_data = row.get("data")
                if scenario_data:
                    return scenario_data
                else:
                    logger.error(
                        f"Scenario {scenario_id} found but has no data in dataset {dataset_name}/{dataset_config}/{dataset_split}"
                    )
                    return None

        logger.error(
            f"Scenario {scenario_id} not found in dataset {dataset_name}/{dataset_config}/{dataset_split}"
        )
        return None

    except Exception as e:
        logger.exception(
            f"Failed to get scenario {scenario_id} from Huggingface dataset {dataset_name}/{dataset_config}/{dataset_split}: {e}"
        )
        return None


def load_scenario_from_huggingface_for_cli(
    dataset_name: str, dataset_config: str, dataset_split: str, scenario_id: str
):
    """
    Load a scenario from HuggingFace for CLI usage.

    This function provides a common interface for CLI tools to load scenarios
    from HuggingFace datasets, using the same approach as the
    huggingface_scenario_iterator but for single scenarios.

    Args:
        dataset_name: The name of the Huggingface dataset
        dataset_config: The config name of the Huggingface dataset
        dataset_split: The split of the Huggingface dataset
        scenario_id: The ID of the scenario to retrieve

    Returns:
        Tuple of (BenchmarkScenarioImportedFromJson, list[CompletedEvent])
        or (None, None) if not found
    """
    from are.simulation.benchmark.scenario_loader import load_scenario
    from are.simulation.data_handler.models import ExportedHuggingFaceMetadata

    try:
        # Get the scenario data as JSON string
        scenario_data = get_scenario_from_huggingface(
            dataset_name, dataset_config, dataset_split, scenario_id
        )

        if scenario_data is None:
            return None, None

        # Use the benchmark scenario loader to create the scenario object
        scenario, completed_events = load_scenario(
            scenario_data,
            scenario_id,
            load_completed_events=False,  # CLI doesn't need completed events
            hf_metadata=ExportedHuggingFaceMetadata(
                dataset=dataset_name,
                split=dataset_split,
                revision=None,
            ),
        )

        return scenario, completed_events

    except Exception as e:
        logger.exception(
            f"Failed to load scenario {scenario_id} from HuggingFace dataset "
            f"{dataset_name}/{dataset_config}/{dataset_split}: {e}"
        )
        return None, None


def parse_huggingface_url(url: str) -> dict[str, str] | None:
    """
    Parse a HuggingFace URL in the format: hf://datasets/dataset_name/config/split/scenario_id

    :param url: The HuggingFace URL to parse
    :return: Dictionary with parsed components or None if invalid format
    """
    if not url.startswith("hf://datasets/"):
        return None

    # Remove the hf://datasets/ prefix
    path = url[len("hf://datasets/") :]
    parts = path.split("/")

    if len(parts) < 4:
        return None

    # Extract components: dataset_name/config/split/scenario_id
    # Handle dataset names that might contain slashes (e.g., "meta-agents-research-environments/gaia2")
    if len(parts) == 4:
        dataset_name, config, split, scenario_id = parts
    elif len(parts) == 5:
        # Handle dataset names with organization (e.g., "meta-agents-research-environments/gaia2")
        dataset_name = f"{parts[0]}/{parts[1]}"
        config, split, scenario_id = parts[2], parts[3], parts[4]
    else:
        return None

    return {
        "dataset_name": dataset_name,
        "config": config,
        "split": split,
        "scenario_id": scenario_id,
    }
