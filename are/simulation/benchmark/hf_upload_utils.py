# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from pathlib import Path
from typing import Any

import pyarrow as pa
import yaml
from datasets import Dataset, DatasetInfo
from datasets.splits import Split

from are.simulation.benchmark.hf_config_utils import create_config_name
from are.simulation.benchmark.report_stats import (
    build_trace_rows_polars,
    combine_results_to_dataframe,
    generate_json_stats_report,
    generate_validation_report,
    generate_validation_report_content,
)
from are.simulation.scenarios.validation_result import (
    MultiScenarioValidationResult,
    ScenarioValidationResult,
)

logger = logging.getLogger(__name__)


def get_scenario_result_info(
    scenario_result: ScenarioValidationResult,
) -> tuple[float | None, str]:
    """Shared function to determine score and status from a ScenarioValidationResult.

    :param scenario_result: A ScenarioValidationResult object
    :type scenario_result: ScenarioValidationResult
    :returns: Tuple of (score, status) where score is 1.0 for success, 0.0 for failure, None for exception/no validation; status is "success", "failed", "exception", or "no_validation"
    :rtype: tuple[float | None, str]
    """
    if scenario_result.success is True:
        return 1.0, "success"
    elif scenario_result.success is False:
        return 0.0, "failed"
    else:  # scenario_result.success is None
        # Distinguish between actual exceptions and cases with no validation
        if scenario_result.exception is not None:
            return None, "exception"
        else:
            return None, "no_validation"


def build_trace_rows(
    scenario_results: dict[tuple[str, int | None], ScenarioValidationResult],
    result_key: tuple[str, str, float, bool, bool],
    multi_scenario_result: MultiScenarioValidationResult,
) -> list[dict[str, Any]]:
    """Convert scenario results to HuggingFace dataset rows.

    :param scenario_results: Dictionary mapping (scenario_id, run_number) to ScenarioValidationResult
    :type scenario_results: dict[tuple[str, int | None], ScenarioValidationResult]
    :param result_key: Tuple containing (phase_name, config, a2a_app_prop, has_tool_augmentation, has_env_events)
    :type result_key: tuple[str, str, float, bool, bool]
    :param multi_scenario_result: MultiScenarioValidationResult containing the run config
    :type multi_scenario_result: MultiScenarioValidationResult
    :returns: List of dictionaries representing dataset rows
    :rtype: list[dict[str, Any]]
    """
    import json

    # Unpack the result key
    phase_name, config, a2a_app_prop, has_tool_augmentation, has_env_events = result_key

    # Serialize the run config to JSON
    run_config_json = json.dumps(
        multi_scenario_result.run_config.model_dump(), indent=2
    )

    rows = []
    for scenario_key, scenario_result in scenario_results.items():
        # Deconstruct the tuple key to get scenario_id and run_number
        scenario_id, run_number = scenario_key

        # Load trace data if available
        data = None
        if scenario_result.export_path:
            try:
                with open(scenario_result.export_path, "r") as f:
                    data = f.read()
            except Exception as e:
                logger.warning(
                    f"Failed to read trace file {scenario_result.export_path}: {e}"
                )
                data = None

        # Get score and status using shared function
        score, status = get_scenario_result_info(scenario_result)

        # Build the row with enhanced metadata
        row = {
            "scenario_id": scenario_id,
            "run_number": run_number,
            "task_id": scenario_id,
            "score": score,
            "status": status,
            "data": data,
            "has_exception": scenario_result.exception is not None,
            "exception_type": (
                type(scenario_result.exception).__name__
                if scenario_result.exception
                else None
            ),
            "exception_message": (
                str(scenario_result.exception) if scenario_result.exception else None
            ),
            "rationale": scenario_result.rationale,
            "config": config,
            "phase_name": phase_name,
            "a2a_app_prop": a2a_app_prop,
            "has_app_noise": has_tool_augmentation,
            "has_env_noise": has_env_events,
            "run_config": run_config_json,
        }

        # Remove None values to keep the dataset clean
        row = {k: v for k, v in row.items() if v is not None}
        rows.append(row)

    return rows


def create_hf_schema() -> pa.Schema:
    """Create the PyArrow schema for HuggingFace dataset uploads.

    :returns: PyArrow schema with all possible fields
    :rtype: pa.Schema
    """
    schema_fields = [
        ("scenario_id", pa.string()),  # Real scenario ID
        ("run_number", pa.int64()),  # Run number as separate column
        ("task_id", pa.string()),  # Full task ID with run suffix
        ("score", pa.float64()),  # Score (nullable)
        ("status", pa.string()),  # Status indicator
        ("data", pa.string()),  # Trace data (nullable)
        ("run_type", pa.string()),  # Type of run (nullable)
        ("config", pa.string()),  # Configuration used (nullable)
        ("phase_name", pa.string()),  # Phase name (standard, agent2agent, noise)
        ("a2a_app_prop", pa.float64()),  # Agent2Agent proportion
        (
            "has_app_noise",
            pa.bool_(),
        ),  # Tool augmentation flag (renamed from has_tool_augmentation)
        (
            "has_env_noise",
            pa.bool_(),
        ),  # Environment events flag (renamed from has_env_events)
        ("run_config", pa.string()),  # Complete run configuration as JSON
        ("has_exception", pa.bool_()),  # Exception flag
        ("exception_type", pa.string()),  # Exception type (nullable)
        ("exception_message", pa.string()),  # Exception message (nullable)
        ("rationale", pa.string()),  # Validation rationale (nullable)
    ]
    return pa.schema(schema_fields)


def generate_validation_report_wrapper(
    results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult],
    model: str,
    model_provider: str,
    num_runs: int = 3,
) -> str:
    """Generate a validation report using polars-based operations.

    :param results: Dictionary mapping (phase_name, config, a2a_app_prop, has_tool_augmentation, has_env_events) tuples to results
    :type results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult]
    :param model: Model name used
    :type model: str
    :param model_provider: Provider used
    :type model_provider: str
    :param num_runs: Number of runs per scenario for display
    :type num_runs: int
    :returns: Formatted report string
    :rtype: str
    """
    # Convert to DataFrame and use polars-based reporting
    df = combine_results_to_dataframe(results)
    return generate_validation_report(df, model, model_provider, num_runs)


def generate_gaia2_dataset_readme(
    results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult],
    model: str,
    model_provider: str,
    original_dataset: str,
    split: str,
) -> str:
    """Generate README.md content for GAIA2 submission HuggingFace dataset.

    Includes proper YAML frontmatter with configs and dataset_info sections.

    :param results: Dictionary mapping (phase_name, config, a2a_app_prop, has_tool_augmentation, has_env_events) tuples to results
    :type results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult]
    :param model: Model name used
    :type model: str
    :param model_provider: Provider used
    :type model_provider: str
    :param original_dataset: Original dataset name
    :type original_dataset: str
    :param split: Dataset split used
    :type split: str
    :returns: README.md content as string with proper datacard header
    :rtype: str
    """
    # Generate configs and dataset_info for YAML frontmatter
    configs_info = []
    dataset_info = []

    # Group results by config to match the upload structure
    configs_to_process = set()
    for result_key, result in results.items():
        phase_name, config, a2a_app_prop, has_tool_augmentation, has_env_events = (
            result_key
        )
        config_name = create_config_name(config, phase_name)

        configs_to_process.add(config_name)

    # Create schema for feature definitions
    schema = create_hf_schema()

    # Generate configs and dataset_info sections
    for config_name in configs_to_process:
        # Config section
        config_entry = {
            "config_name": config_name,
            "data_files": [{"split": split, "path": f"{config_name}/{split}-*"}],
        }
        configs_info.append(config_entry)

        # Dataset info section
        features = []
        for field in schema:
            # Map PyArrow types to HuggingFace dataset dtype strings
            if field.type == pa.string():
                dtype_str = "string"
            elif field.type == pa.int64():
                dtype_str = "int64"
            elif field.type == pa.float64():
                dtype_str = "float64"
            elif field.type == pa.bool_():
                dtype_str = "bool"
            else:
                # Fallback for any other types
                dtype_str = str(field.type)

            feature_entry = {
                "name": field.name,
                "dtype": dtype_str,
            }
            features.append(feature_entry)

        dataset_info_entry = {
            "config_name": config_name,
            "features": features,
            "splits": [
                {
                    "name": split,
                }
            ],
        }
        dataset_info.append(dataset_info_entry)

    # Generate YAML frontmatter
    frontmatter = {"configs": configs_info, "dataset_info": dataset_info}

    yaml_header = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

    # Generate the main README content
    readme_content = f"""---
{yaml_header}---

# GAIA2 Leaderboard Submission

**Model:** {model}
**Provider:** {model_provider}
**Original Dataset:** {original_dataset}
**Split:** {split}

## Run Configuration

This submission includes all required evaluation scenarios for GAIA2 leaderboard:

- **Standard runs**: All capability configs (execution, search, adaptability, time, ambiguity)
- **Agent2Agent runs**: All configs with `--a2a_app_prop 1.0`
- **Noise runs**: All configs with noise augmentation enabled
- **Number of runs per scenario**: 3 (for variance analysis)
- **Trace format**: HuggingFace compatible

## Results Summary

"""

    # Generate validation report content with markdown formatting
    df = combine_results_to_dataframe(results)
    validation_content = generate_validation_report_content(
        df, header_format="###", header_prefix="", header_suffix=""
    )

    # Add the validation report content to README
    readme_content += validation_content

    readme_content += """

## Dataset Structure

This dataset contains traces from all GAIA2 evaluation scenarios. Each row represents one scenario run with the following fields:

- `scenario_id`: The base scenario identifier
- `run_number`: Run number (1-3) for variance analysis
- `task_id`: Full task identifier including run suffix
- `score`: Success score (1.0 for success, 0.0 for failure, null for exceptions)
- `status`: Run status ("success", "failed", "exception", or "no_validation")
- `data`: Complete trace data in JSON format
- `phase_name`: Phase type ("standard", "agent2agent", or "noise")
- `config`: Configuration used (execution, search, adaptability, time, ambiguity)
- `a2a_app_prop`: Agent2Agent proportion used (0 or 1.0)
- `has_app_noise`: Whether tool augmentation was enabled
- `has_env_noise`: Whether environment events were enabled
- Additional metadata fields for exceptions and validation rationale

## Citation

If you use this dataset, please cite the GAIA2 benchmark paper and acknowledge the model evaluation.
"""

    return readme_content


def generate_json_stats_report_wrapper(
    results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult],
    model: str,
    model_provider: str,
) -> dict:
    """Generate a computer-readable JSON report using polars-based operations.

    :param results: Dictionary mapping (phase_name, config, a2a_app_prop, has_tool_augmentation, has_env_events) tuples to results
    :type results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult]
    :param model: Model name used
    :type model: str
    :param model_provider: Provider used
    :type model_provider: str
    :returns: Dictionary containing structured statistics for computer processing
    :rtype: dict
    """
    # Convert to DataFrame and use polars-based reporting
    df = combine_results_to_dataframe(results)
    return generate_json_stats_report(df, model, model_provider)


def generate_submission_summary(
    output_dir: str,
    results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult],
    model: str,
    model_provider: str,
    num_runs: int = 3,
) -> None:
    """Generate a submission summary file with information for leaderboard submission.

    :param output_dir: Directory where results are stored
    :type output_dir: str
    :param results: Dictionary mapping (phase_name, config, a2a_app_prop, has_tool_augmentation, has_env_events) tuples to results
    :type results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult]
    :param model: Model name used
    :type model: str
    :param model_provider: Provider used
    :type model_provider: str
    :param num_runs: Number of runs per scenario for display
    :type num_runs: int
    """
    import os

    summary_path = os.path.join(output_dir, "submission_summary.md")

    with open(summary_path, "w") as f:
        f.write("# GAIA2 Leaderboard Submission Summary\n\n")
        f.write(f"**Model:** {model}\n")
        f.write(f"**Provider:** {model_provider}\n\n")

        f.write("## Run Configuration\n\n")
        f.write("This submission includes all required evaluation scenarios:\n\n")
        f.write(
            "- **Standard runs**: All capability configs "
            "(execution, search, adaptability, time, ambiguity)\n"
        )
        f.write("- **Agent2Agent runs**: All configs with `--a2a_app_prop 1.0`\n")
        f.write("- **Noise runs**: All configs with noise augmentation enabled\n")
        f.write(
            f"- **Number of runs per scenario**: {num_runs} (for variance analysis)\n"
        )
        f.write("- **Split**: test\n")
        f.write("- **Trace format**: HuggingFace compatible\n\n")

        f.write("## Results Summary\n\n")

        # Generate validation report content with markdown formatting
        df = combine_results_to_dataframe(results)
        validation_content = generate_validation_report_content(
            df, num_runs, header_format="###", header_prefix="", header_suffix=""
        )

        # Add the validation report content to the summary
        f.write(validation_content)

        f.write("\n")

        f.write("## Directory Structure\n\n")
        f.write("```\n")
        f.write("gaia2_results/\n")
        f.write("├── standard/           # Standard capability runs\n")
        f.write("│   ├── execution/\n")
        f.write("│   ├── search/\n")
        f.write("│   ├── adaptability/\n")
        f.write("│   ├── time/\n")
        f.write("│   └── ambiguity/\n")
        f.write("├── agent2agent/        # A2A runs with --a2a_app_prop 1\n")
        f.write("│   ├── execution/\n")
        f.write("│   ├── search/\n")
        f.write("│   └── ...\n")
        f.write("├── noise/              # Noise runs with --noise\n")
        f.write("│   ├── execution/\n")
        f.write("│   ├── search/\n")
        f.write("│   └── ...\n")
        f.write("└── submission_summary.md  # This file\n")
        f.write("```\n\n")

        f.write("## Next Steps\n\n")
        f.write("1. Review the results in each subdirectory\n")
        f.write(
            "2. Ensure all traces have been uploaded to HuggingFace "
            "(if --hf_upload was specified)\n"
        )
        f.write(
            "3. Submit to the GAIA2 leaderboard with the HuggingFace dataset link\n"
        )

    logger.info(f"Submission summary saved to: {summary_path}")


def upload_consolidated_results_to_hf(
    results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult],
    dataset_name: str,
    model: str,
    model_provider: str,
    public: bool,
    original_dataset: str,
    split: str,
) -> bool:
    """Upload consolidated results from all phases to HuggingFace as separate configs/partitions.

    Uses polars-based data processing for improved performance and cleaner code.

    :param results: Dictionary mapping (phase_name, config, a2a_app_prop, has_tool_augmentation, has_env_events) tuples to results
    :type results: dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult]
    :param dataset_name: Name of the dataset to upload to
    :type dataset_name: str
    :param model: Model name used
    :type model: str
    :param model_provider: Provider used
    :type model_provider: str
    :param public: Whether to make the dataset public
    :type public: bool
    :param original_dataset: Original dataset name
    :type original_dataset: str
    :param split: Dataset split used
    :type split: str
    :returns: True if upload succeeded, False otherwise
    :rtype: bool
    """

    logger.info("Uploading all results as separate configs to HuggingFace...")

    # Convert to DataFrame for easier processing
    df = combine_results_to_dataframe(results)

    # Generate enhanced README content for GAIA2 submission
    readme_content = generate_gaia2_dataset_readme(
        results, model, model_provider, original_dataset, split
    )

    # Calculate overall success rate for commit message
    if not df.is_empty():
        total_successful = len(df.filter(df["status"] == "success"))
        total_scenarios = len(df)
        overall_success_rate = (
            total_successful / total_scenarios if total_scenarios > 0 else 0.0
        )
    else:
        total_successful = 0
        total_scenarios = 0
        overall_success_rate = 0.0

    commit_msg = (
        f"GAIA2 submission for {model} on {original_dataset}:{split} = "
        f"{overall_success_rate:.2f}% ({total_successful}/{total_scenarios})"
    )

    # Group results by config and create separate datasets for each config
    configs_to_upload = {}

    if not df.is_empty():
        # Group by phase and config to create config names
        for phase_name in df.select("phase_name").unique().to_series():
            for config in (
                df.filter(df["phase_name"] == phase_name)
                .select("config")
                .unique()
                .to_series()
            ):
                config_name = create_config_name(config, phase_name)

                if config_name not in configs_to_upload:
                    configs_to_upload[config_name] = []

                # Filter DataFrame for this specific config
                config_df = df.filter(
                    (df["phase_name"] == phase_name) & (df["config"] == config)
                )

                # Convert to HuggingFace rows format
                rows = build_trace_rows_polars(config_df)
                configs_to_upload[config_name].extend(rows)

    logger.info(
        f"Will upload {len(configs_to_upload)} configs: {list(configs_to_upload.keys())}"
    )

    # Create schema
    schema = create_hf_schema()

    success = True

    # Upload each config separately
    for config_name, rows in configs_to_upload.items():
        try:
            logger.info(f"Uploading config '{config_name}' with {len(rows)} rows...")

            # Create table and dataset for this config
            table = pa.Table.from_pylist(rows, schema=schema)

            hf_split = Split.TEST if split == "test" else Split.VALIDATION

            dataset = Dataset(
                table,
                split=hf_split,
                info=DatasetInfo(description=readme_content),
            )

            # Upload with config parameter
            dataset.push_to_hub(
                dataset_name,
                config_name=config_name,
                split=split,
                commit_message=f"{commit_msg} - config: {config_name}",
                commit_description=readme_content,
                private=not public,
            )

            logger.info(f"Successfully uploaded config '{config_name}'")

        except Exception as e:
            logger.error(f"Failed to upload config '{config_name}': {e}")
            success = False

    # Upload README and JSON report using HuggingFace Hub
    if success:
        try:
            import json

            from huggingface_hub import HfApi

            api = HfApi()

            # Upload dataset card (README)
            api.upload_file(
                path_or_fileobj=readme_content.encode(),
                path_in_repo="README.md",
                repo_id=dataset_name,
                repo_type="dataset",
                commit_message=f"Update dataset card for {model} results",
            )
            logger.info(f"Successfully uploaded dataset card to {dataset_name}")

            # Generate and upload JSON report
            json_stats = generate_json_stats_report_wrapper(
                results, model, model_provider
            )
            json_content = json.dumps(json_stats, indent=2)

            api.upload_file(
                path_or_fileobj=json_content.encode(),
                path_in_repo="computed_stats.json",
                repo_id=dataset_name,
                repo_type="dataset",
                commit_message=f"Upload computed statistics for {model} results",
            )
            logger.info(f"Successfully uploaded JSON statistics to {dataset_name}")

        except Exception as upload_error:
            logger.warning(f"Failed to upload README or JSON report: {upload_error}")
            # Continue anyway as the main dataset upload succeeded

    if success:
        logger.info(f"Successfully uploaded all configs to {dataset_name}")
        return True
    else:
        logger.error(f"Failed to upload some configs to {dataset_name}")

        # Try to save locally as fallback
        try:
            output_ds_path = Path("./gaia2_results") / dataset_name.replace("/", "_")

            for config_name, rows in configs_to_upload.items():
                config_path = output_ds_path / config_name
                config_path.mkdir(parents=True, exist_ok=True)

                table = pa.Table.from_pylist(rows, schema=schema)

                dataset = Dataset(
                    table,
                    info=DatasetInfo(description=readme_content),
                )
                dataset.save_to_disk(config_path)

            # Also save the README.md file
            readme_path = output_ds_path / "README.md"
            with open(readme_path, "w") as f:
                f.write(readme_content)

            logger.info(
                f"Saved dataset locally to {output_ds_path}. "
                "You can upload it manually to HuggingFace Hub."
            )
            return False
        except Exception as save_error:
            logger.error(f"Failed to save dataset locally: {save_error}")

        return False
