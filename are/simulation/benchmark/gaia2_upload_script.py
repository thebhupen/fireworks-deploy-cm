#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Standalone script to upload GAIA2 results to HuggingFace and compute report stats.

This script takes the output directory from a GAIA2 run and:
1. Loads all the JSONL results and trace files
2. Reconstructs the results structure expected by the upload functions
3. Uploads to HuggingFace using the existing upload utilities
4. Generates report statistics

Usage:
    python gaia2_upload_script.py --output_dir ~/gaia2_run_clem --hf_upload 'meta-agents-research-environments/test_leader_traces_submit' --model llama4v-17b-maverick_agents2
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from are.simulation.benchmark.hf_upload_utils import (
    generate_submission_summary,
    upload_consolidated_results_to_hf,
)
from are.simulation.benchmark.report_stats import (
    combine_results_to_dataframe,
    generate_json_stats_report,
    generate_validation_report,
)
from are.simulation.scenarios.config import MultiScenarioRunnerConfig
from are.simulation.scenarios.validation_result import (
    MultiScenarioValidationResult,
    ScenarioValidationResult,
)

logger = logging.getLogger(__name__)


def load_trace_file(trace_path: str) -> str | None:
    """Load trace data from a JSON file."""
    try:
        with open(trace_path, "r") as f:
            return f.read()
    except Exception as e:
        logger.warning(f"Failed to read trace file {trace_path}: {e}")
        return None


def parse_jsonl_results(jsonl_path: str) -> list[dict[str, Any]]:
    """Parse JSONL results file."""
    results = []
    try:
        with open(jsonl_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))
    except Exception as e:
        logger.error(f"Failed to parse JSONL file {jsonl_path}: {e}")
    return results


def create_scenario_validation_result(
    jsonl_entry: dict[str, Any], trace_data: str | None
) -> ScenarioValidationResult:
    """Create a ScenarioValidationResult from JSONL entry and trace data."""
    metadata = jsonl_entry.get("metadata", {})

    # Determine success based on status
    status = metadata.get("status", "no_validation")

    if status == "success":
        success = True
    elif status == "failed":
        success = False
    else:
        success = None  # exception or no_validation

    # Create a temporary file path for the trace data if it exists
    export_path = None
    if trace_data:
        export_path = jsonl_entry.get("trace_id")  # Use the original trace path

    return ScenarioValidationResult(
        success=success,
        rationale=metadata.get("rationale"),
        exception=(
            None
            if not metadata.get("has_exception", False)
            else Exception("Unknown exception")
        ),
        export_path=export_path,
    )


def reconstruct_results_from_output_dir(
    output_dir: str, model: str, model_provider: str = "unknown"
) -> dict[tuple[str, str, float, bool, bool], MultiScenarioValidationResult]:
    """Reconstruct the results structure from the output directory."""
    results = {}
    output_path = Path(output_dir)

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Define phase mappings
    phase_configs = {
        "standard": {
            "a2a_app_prop": 0.0,
            "has_tool_augmentation": False,
            "has_env_events": False,
        },
        "agent2agent": {
            "a2a_app_prop": 1.0,
            "has_tool_augmentation": False,
            "has_env_events": False,
        },
        "noise": {
            "a2a_app_prop": 0.0,
            "has_tool_augmentation": True,
            "has_env_events": True,
        },
    }

    # Iterate through phase directories
    for phase_dir in output_path.iterdir():
        if not phase_dir.is_dir():
            continue

        phase_name = phase_dir.name
        if phase_name not in phase_configs:
            logger.warning(f"Unknown phase directory: {phase_name}")
            continue

        phase_config = phase_configs[phase_name]

        # Iterate through config directories within each phase
        for config_dir in phase_dir.iterdir():
            if not config_dir.is_dir():
                continue

            config_name = config_dir.name
            jsonl_path = config_dir / "output.jsonl"

            if not jsonl_path.exists():
                logger.warning(f"No output.jsonl found in {config_dir}")
                continue

            logger.info(f"Processing {phase_name}/{config_name}")

            # Parse JSONL results
            jsonl_results = parse_jsonl_results(str(jsonl_path))

            # Build scenario results dictionary
            scenario_results = {}

            for entry in jsonl_results:
                scenario_id = entry["metadata"]["scenario_id"]
                run_number = entry["metadata"]["run_number"]
                trace_path = entry.get("trace_id")

                # Load trace data
                trace_data = None
                if trace_path and os.path.exists(trace_path):
                    trace_data = load_trace_file(trace_path)

                # Create scenario validation result
                scenario_result = create_scenario_validation_result(entry, trace_data)

                # Use tuple key (scenario_id, run_number)
                scenario_key = (scenario_id, run_number)
                scenario_results[scenario_key] = scenario_result

            # Create a basic MultiScenarioRunnerConfig
            run_config = MultiScenarioRunnerConfig(
                model=model,
                model_provider=model_provider,
                agent="default",
                oracle=False,
                export=True,
                output_dir=str(config_dir),
                trace_dump_format="hf",
                a2a_app_prop=phase_config["a2a_app_prop"],
                a2a_app_agent="",
                a2a_model=None,
                simulated_generation_time_mode="measured",
            )

            # Create MultiScenarioValidationResult
            multi_result = MultiScenarioValidationResult(
                scenario_results=scenario_results, run_config=run_config
            )

            # Create result key
            result_key = (
                phase_name,
                config_name,
                phase_config["a2a_app_prop"],
                phase_config["has_tool_augmentation"],
                phase_config["has_env_events"],
            )

            results[result_key] = multi_result
            logger.info(
                f"Loaded {len(scenario_results)} scenario results for {phase_name}/{config_name}"
            )

    return results


def main():
    parser = argparse.ArgumentParser(description="Upload GAIA2 results to HuggingFace")
    parser.add_argument(
        "--input_dir", required=True, help="Directory containing GAIA2 results"
    )
    parser.add_argument(
        "--output_dir", required=True, help="Directory to save computed statistics"
    )
    parser.add_argument("--hf_upload", help="HuggingFace dataset name to upload to")
    parser.add_argument(
        "--hf_public", action="store_true", help="Make the dataset public"
    )
    parser.add_argument(
        "--model", required=True, help="Model name used for the evaluation"
    )
    parser.add_argument("--model_provider", default="unknown", help="Model provider")
    parser.add_argument(
        "--original_dataset",
        default="meta-agents-research-environments/gaia2",
        help="Original dataset name",
    )
    parser.add_argument("--split", default="test", help="Dataset split")
    parser.add_argument("--log_level", default="INFO", help="Logging level")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info(f"Loading results from {args.input_dir}")

    # Reconstruct results from input directory
    results = reconstruct_results_from_output_dir(
        args.input_dir, args.model, args.model_provider
    )

    if not results:
        logger.error("No results found in output directory")
        return 1

    logger.info(f"Loaded {len(results)} result configurations")

    # Create output directory for statistics
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate local report statistics
    logger.info("Generating report statistics...")
    df = combine_results_to_dataframe(results)

    # Generate validation report
    validation_report = generate_validation_report(
        df, args.model, args.model_provider, 3
    )
    print("\n" + "=" * 80)
    print("VALIDATION REPORT")
    print("=" * 80)
    print(validation_report)

    # Generate JSON stats report
    json_stats = generate_json_stats_report(df, args.model, args.model_provider)

    # Save JSON stats to file
    stats_path = os.path.join(args.output_dir, "computed_stats.json")
    with open(stats_path, "w") as f:
        json.dump(json_stats, f, indent=2)
    logger.info(f"Saved computed statistics to {stats_path}")

    # Save validation report to file
    report_path = os.path.join(args.output_dir, "validation_report.txt")
    with open(report_path, "w") as f:
        f.write(validation_report)
    logger.info(f"Saved validation report to {report_path}")

    # Upload to HuggingFace if requested
    if args.hf_upload:
        logger.info(f"Uploading to HuggingFace dataset: {args.hf_upload}")
        success = upload_consolidated_results_to_hf(
            results,
            args.hf_upload,
            args.model,
            args.model_provider,
            args.hf_public,
            args.original_dataset,
            args.split,
        )

        if success:
            logger.info("Upload completed successfully!")
            logger.info("The upload includes:")
            logger.info("  - Trace data organized by configuration")
            logger.info("  - README.md with validation report")
            logger.info("  - computed_stats.json with detailed statistics")
        else:
            logger.error("Upload failed!")
            return 1
    else:
        # Generate local submission summary
        logger.info("Generating local submission summary...")
        generate_submission_summary(
            args.output_dir,
            results,
            args.model,
            args.model_provider,
            3,
        )

    logger.info("Script completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
