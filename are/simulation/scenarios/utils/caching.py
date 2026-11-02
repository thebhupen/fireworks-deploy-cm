# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import xxhash
from dotenv import load_dotenv

from are.simulation.scenarios.config import ScenarioRunnerConfig
from are.simulation.scenarios.scenario import Scenario
from are.simulation.scenarios.validation_result import ScenarioValidationResult

load_dotenv()

logger = logging.getLogger(__name__)


def get_run_id(scenario: Scenario, runner_config: ScenarioRunnerConfig | None) -> str:
    """
    Generate a unique run ID for the scenario and configuration.
    """
    # Generate config hash for unique filename
    config_hash = ""
    if runner_config is not None:
        config_hash = f"_{runner_config.get_config_hash()}"

    # Include run number in filename if present
    if hasattr(scenario, "run_number") and scenario.run_number is not None:
        return f"{scenario.scenario_id}_run_{scenario.run_number}{config_hash}"
    return f"{scenario.scenario_id}{config_hash}"


@dataclass
class CachedScenarioResult:
    """Cached representation of a scenario result."""

    # Core result data
    success: bool | None
    exception_type: str | None
    exception_message: str | None
    export_path: str | None
    rationale: str | None

    # Cache metadata
    cache_key: str
    scenario_id: str
    run_number: int | None

    # Configuration hash for validation
    config_hash: str
    scenario_hash: str

    @classmethod
    def from_scenario_result(
        cls,
        scenario_result: ScenarioValidationResult,
        scenario: Scenario,
        runner_config: ScenarioRunnerConfig,
    ) -> "CachedScenarioResult":
        """Create a cached result from a scenario validation result."""
        cache_key = _generate_cache_key(runner_config, scenario)
        config_hash = _generate_config_hash(runner_config)
        scenario_hash = _generate_scenario_hash(scenario)

        return cls(
            success=scenario_result.success,
            exception_type=(
                type(scenario_result.exception).__name__
                if scenario_result.exception
                else None
            ),
            exception_message=(
                str(scenario_result.exception) if scenario_result.exception else None
            ),
            export_path=scenario_result.export_path,
            rationale=scenario_result.rationale,
            cache_key=cache_key,
            scenario_id=scenario.scenario_id,
            run_number=getattr(scenario, "run_number", None),
            config_hash=config_hash,
            scenario_hash=scenario_hash,
        )

    def to_json(self) -> str:
        """Serialize the cached result to JSON."""
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "CachedScenarioResult":
        """Deserialize a cached result from JSON."""
        data = json.loads(json_str)
        return cls(**data)

    def to_scenario_result(self) -> ScenarioValidationResult:
        """Convert back to a ScenarioValidationResult."""
        exception = None
        if self.exception_type and self.exception_message:
            # Create a generic exception with the cached message
            exception = Exception(f"{self.exception_type}: {self.exception_message}")

        return ScenarioValidationResult(
            success=self.success,
            exception=exception,
            export_path=self.export_path,
            rationale=self.rationale,
        )


def _generate_cache_key(runner_config: ScenarioRunnerConfig, scenario: Scenario) -> str:
    """Generate a unique cache key for the scenario and configuration."""
    return get_run_id(scenario=scenario, runner_config=runner_config)


def _generate_config_hash(runner_config: ScenarioRunnerConfig) -> str:
    """Generate a hash of the runner configuration to validate cache compatibility."""
    # Include all configuration that could affect results
    config_dict = {
        "model": runner_config.model,
        "model_provider": runner_config.model_provider,
        "agent": runner_config.agent,
        "oracle": runner_config.oracle,
        "max_turns": runner_config.max_turns,
        "a2a_app_prop": runner_config.a2a_app_prop,
        "a2a_app_agent": runner_config.a2a_app_agent,
        "a2a_model": runner_config.a2a_model,
        "simulated_generation_time_mode": runner_config.simulated_generation_time_mode,
        # Add tool augmentation config if present
        "tool_augmentation": (
            runner_config.tool_augmentation_config.model_dump()  # type: ignore
            if runner_config.tool_augmentation_config
            else None
        ),
        "env_events_config": (
            runner_config.env_events_config.model_dump()  # type: ignore
            if runner_config.env_events_config
            else None
        ),
    }

    config_json = json.dumps(config_dict, sort_keys=True)
    return xxhash.xxh64(config_json.encode()).hexdigest()[:16]


def _generate_scenario_hash(scenario: Scenario) -> str:
    """Generate a hash of the scenario to detect changes."""
    # Include key scenario properties that affect results
    scenario_dict = {
        "scenario_id": scenario.scenario_id,
        "seed": scenario.seed,
        "nb_turns": scenario.nb_turns,
        "config": scenario.config,
        "has_a2a_augmentation": scenario.has_a2a_augmentation,
        "additional_system_prompt": scenario.additional_system_prompt,
        "tags": [str(tag) for tag in scenario.tags],
        # Include events structure (simplified to avoid circular references)
        "events_count": len(scenario.events) if scenario.events else 0,
        "event_types": (
            [str(event.event_type) for event in scenario.events]
            if scenario.events
            else []
        ),
    }

    scenario_json = json.dumps(scenario_dict, sort_keys=True)
    return xxhash.xxh64(scenario_json.encode()).hexdigest()[:16]


def _get_cache_dir() -> Path:
    """Get the cache directory path."""
    # Use environment variable or default to user cache directory
    cache_dir = os.environ.get("ARE_SIMULATION_CACHE_DIR")
    if cache_dir:
        return Path(cache_dir)

    # Default to a cache directory in the user's home
    home_dir = Path.home()
    return home_dir / ".cache" / "simulation" / "scenario_results"


def _get_cache_file_path(cache_key: str) -> Path:
    """Get the full path for a cache file."""
    cache_dir = _get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{cache_key}.json"


def maybe_load_cached_result(
    runner_config: ScenarioRunnerConfig,
    scenario: Scenario,
) -> ScenarioValidationResult | None:
    """Try to load a cached result for the scenario and configuration."""
    try:
        cache_key = _generate_cache_key(runner_config, scenario)
        cache_file = _get_cache_file_path(cache_key)

        if not cache_file.exists():
            return None

        # Load and validate the cached result
        with open(cache_file, "r") as f:
            cached_result = CachedScenarioResult.from_json(f.read())

        # Validate that the cache is still valid
        current_config_hash = _generate_config_hash(runner_config)
        current_scenario_hash = _generate_scenario_hash(scenario)

        if (
            cached_result.config_hash != current_config_hash
            or cached_result.scenario_hash != current_scenario_hash
        ):
            logger.debug(
                f"Cache invalidated for {scenario.scenario_id} due to config/scenario changes"
            )
            return None

        logger.info(f"Loading cached result for scenario {scenario.scenario_id}")
        return cached_result.to_scenario_result()

    except Exception as e:
        logger.warning(f"Failed to load cached result for {scenario.scenario_id}: {e}")
        return None


def write_cached_result(
    runner_config: ScenarioRunnerConfig,
    scenario: Scenario,
    result: ScenarioValidationResult,
) -> None:
    """Write a scenario result to cache."""
    try:
        cached_result = CachedScenarioResult.from_scenario_result(
            result, scenario, runner_config
        )

        cache_file = _get_cache_file_path(cached_result.cache_key)

        with open(cache_file, "w") as f:
            f.write(cached_result.to_json())

        logger.debug(f"Cached result for scenario {scenario.scenario_id}")

    except Exception as e:
        logger.warning(f"Failed to cache result for {scenario.scenario_id}: {e}")


def clear_cache() -> None:
    """Clear all cached scenario results."""
    try:
        cache_dir = _get_cache_dir()
        if cache_dir.exists():
            for cache_file in cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cleared scenario result cache")
    except Exception as e:
        logger.warning(f"Failed to clear cache: {e}")


def get_cache_stats() -> dict[str, Any]:
    """Get statistics about the cache."""
    try:
        cache_dir = _get_cache_dir()
        if not cache_dir.exists():
            return {"cache_dir": str(cache_dir), "file_count": 0, "total_size": 0}

        cache_files = list(cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        return {
            "cache_dir": str(cache_dir),
            "file_count": len(cache_files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
    except Exception as e:
        logger.warning(f"Failed to get cache stats: {e}")
        return {"error": str(e)}
