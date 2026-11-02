# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from are.simulation.scenarios.config import ScenarioRunnerConfig
from are.simulation.scenarios.scenario import Scenario
from are.simulation.scenarios.utils.caching import (
    CachedScenarioResult,
    _generate_cache_key,
    _generate_config_hash,
    _generate_scenario_hash,
    _get_cache_dir,
    _get_cache_file_path,
    clear_cache,
    get_cache_stats,
    get_run_id,
    maybe_load_cached_result,
    write_cached_result,
)
from are.simulation.scenarios.validation_result import ScenarioValidationResult


def create_mock_scenario(
    scenario_id: str = "test_scenario",
    seed: int = 42,
    nb_turns: int = 5,
    run_number: int | None = None,
    has_a2a_augmentation: bool = False,
    additional_system_prompt: str | None = None,
) -> Mock:
    """Create a mock scenario for testing."""
    scenario = Mock(spec=Scenario)
    scenario.scenario_id = scenario_id
    scenario.seed = seed
    scenario.nb_turns = nb_turns
    scenario.config = {"test": "config"}
    scenario.has_a2a_augmentation = has_a2a_augmentation
    scenario.additional_system_prompt = additional_system_prompt
    scenario.tags = ["tag1", "tag2"]
    scenario.events = []

    if run_number is not None:
        scenario.run_number = run_number
    else:
        # Make sure hasattr returns False when run_number is not set
        del scenario.run_number

    return scenario


def create_mock_runner_config(
    model: str = "test_model",
    model_provider: str = "test_provider",
    agent: str = "test_agent",
    oracle: bool = True,
    max_turns: int = 10,
) -> Mock:
    """Create a mock runner config for testing."""
    config = Mock(spec=ScenarioRunnerConfig)
    config.model = model
    config.model_provider = model_provider
    config.agent = agent
    config.oracle = oracle
    config.max_turns = max_turns
    config.a2a_app_prop = 0.5
    config.a2a_app_agent = None
    config.a2a_model = None
    config.simulated_generation_time_mode = None
    config.tool_augmentation_config = None
    config.env_events_config = None

    # Mock the get_config_hash method
    config.get_config_hash.return_value = "test_hash_12345678"

    return config


def create_mock_validation_result(
    success: bool = True,
    exception: Exception | None = None,
    export_path: str | None = "/tmp/test_export.json",
    rationale: str | None = "Test passed",
) -> ScenarioValidationResult:
    """Create a mock validation result for testing."""
    return ScenarioValidationResult(
        success=success,
        exception=exception,
        export_path=export_path,
        rationale=rationale,
    )


def test_get_run_id_without_run_number():
    """Test get_run_id for scenario without run_number."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()

    run_id = get_run_id(scenario, config)
    assert run_id == "test_scenario_test_hash_12345678"


def test_get_run_id_with_run_number():
    """Test get_run_id for scenario with run_number."""
    scenario = create_mock_scenario(run_number=3)
    config = create_mock_runner_config()

    run_id = get_run_id(scenario, config)
    assert run_id == "test_scenario_run_3_test_hash_12345678"


def test_get_run_id_with_none_config():
    """Test get_run_id with None config."""
    scenario = create_mock_scenario()

    run_id = get_run_id(scenario, None)  # type: ignore
    assert run_id == "test_scenario"


def test_cached_scenario_result_from_scenario_result():
    """Test creating CachedScenarioResult from ScenarioValidationResult."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()
    validation_result = create_mock_validation_result()

    cached_result = CachedScenarioResult.from_scenario_result(
        validation_result, scenario, config
    )

    assert cached_result.success is True
    assert cached_result.exception_type is None
    assert cached_result.exception_message is None
    assert cached_result.export_path == "/tmp/test_export.json"
    assert cached_result.rationale == "Test passed"
    assert cached_result.scenario_id == "test_scenario"
    assert cached_result.run_number is None
    assert cached_result.cache_key == "test_scenario_test_hash_12345678"


def test_cached_scenario_result_with_exception():
    """Test CachedScenarioResult with exception."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()
    exception = ValueError("Test error")
    validation_result = create_mock_validation_result(
        success=False, exception=exception
    )

    cached_result = CachedScenarioResult.from_scenario_result(
        validation_result, scenario, config
    )

    assert cached_result.success is False
    assert cached_result.exception_type == "ValueError"
    assert cached_result.exception_message == "Test error"


def test_cached_scenario_result_json_roundtrip():
    """Test JSON serialization and deserialization of CachedScenarioResult."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()
    validation_result = create_mock_validation_result()

    cached_result = CachedScenarioResult.from_scenario_result(
        validation_result, scenario, config
    )

    # Serialize to JSON
    json_str = cached_result.to_json()
    assert isinstance(json_str, str)
    assert "test_scenario" in json_str

    # Deserialize from JSON
    restored_result = CachedScenarioResult.from_json(json_str)

    assert restored_result.success == cached_result.success
    assert restored_result.scenario_id == cached_result.scenario_id
    assert restored_result.cache_key == cached_result.cache_key
    assert restored_result.config_hash == cached_result.config_hash
    assert restored_result.scenario_hash == cached_result.scenario_hash


def test_cached_scenario_result_to_scenario_result():
    """Test converting CachedScenarioResult back to ScenarioValidationResult."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()
    validation_result = create_mock_validation_result()

    cached_result = CachedScenarioResult.from_scenario_result(
        validation_result, scenario, config
    )

    restored_validation_result = cached_result.to_scenario_result()

    assert restored_validation_result.success == validation_result.success
    assert restored_validation_result.export_path == validation_result.export_path
    assert restored_validation_result.rationale == validation_result.rationale
    assert restored_validation_result.exception is None  # No exception in original


def test_cached_scenario_result_to_scenario_result_with_exception():
    """Test converting CachedScenarioResult with exception back to ScenarioValidationResult."""
    cached_result = CachedScenarioResult(
        success=False,
        exception_type="ValueError",
        exception_message="Test error",
        export_path=None,
        rationale="Test failed",
        cache_key="test_key",
        scenario_id="test_scenario",
        run_number=None,
        config_hash="config_hash",
        scenario_hash="scenario_hash",
    )

    restored_validation_result = cached_result.to_scenario_result()

    assert restored_validation_result.success is False
    assert restored_validation_result.exception is not None
    assert "ValueError: Test error" in str(restored_validation_result.exception)


def test_generate_cache_key():
    """Test cache key generation."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()

    cache_key = _generate_cache_key(config, scenario)
    assert cache_key == "test_scenario_test_hash_12345678"


def test_generate_config_hash():
    """Test configuration hash generation."""
    config = create_mock_runner_config()

    config_hash = _generate_config_hash(config)
    assert isinstance(config_hash, str)
    assert len(config_hash) == 16  # xxhash truncated to 16 chars


def test_generate_config_hash_consistency():
    """Test that identical configs produce identical hashes."""
    config1 = create_mock_runner_config()
    config2 = create_mock_runner_config()

    hash1 = _generate_config_hash(config1)
    hash2 = _generate_config_hash(config2)

    assert hash1 == hash2


def test_generate_config_hash_different_configs():
    """Test that different configs produce different hashes."""
    config1 = create_mock_runner_config(model="model1")
    config2 = create_mock_runner_config(model="model2")

    hash1 = _generate_config_hash(config1)
    hash2 = _generate_config_hash(config2)

    assert hash1 != hash2


def test_generate_scenario_hash():
    """Test scenario hash generation."""
    scenario = create_mock_scenario()

    scenario_hash = _generate_scenario_hash(scenario)
    assert isinstance(scenario_hash, str)
    assert len(scenario_hash) == 16  # xxhash truncated to 16 chars


def test_generate_scenario_hash_consistency():
    """Test that identical scenarios produce identical hashes."""
    scenario1 = create_mock_scenario()
    scenario2 = create_mock_scenario()

    hash1 = _generate_scenario_hash(scenario1)
    hash2 = _generate_scenario_hash(scenario2)

    assert hash1 == hash2


def test_generate_scenario_hash_different_scenarios():
    """Test that different scenarios produce different hashes."""
    scenario1 = create_mock_scenario(scenario_id="scenario1")
    scenario2 = create_mock_scenario(scenario_id="scenario2")

    hash1 = _generate_scenario_hash(scenario1)
    hash2 = _generate_scenario_hash(scenario2)

    assert hash1 != hash2


def test_get_cache_dir_with_env_var():
    """Test cache directory with environment variable set."""
    with patch.dict(os.environ, {"ARE_SIMULATION_CACHE_DIR": "/custom/cache/dir"}):
        cache_dir = _get_cache_dir()
        assert cache_dir == Path("/custom/cache/dir")


def test_get_cache_dir_default():
    """Test default cache directory."""
    with patch.dict(os.environ, {}, clear=True):
        cache_dir = _get_cache_dir()
        expected = Path.home() / ".cache" / "simulation" / "scenario_results"
        assert cache_dir == expected


def test_get_cache_file_path():
    """Test cache file path generation."""
    with patch(
        "are.simulation.scenarios.utils.caching._get_cache_dir"
    ) as mock_get_cache_dir:
        mock_cache_dir = Path("/tmp/test_cache")
        mock_get_cache_dir.return_value = mock_cache_dir

        with patch.object(Path, "mkdir") as mock_mkdir:
            cache_file = _get_cache_file_path("test_key")

            assert cache_file == mock_cache_dir / "test_key.json"
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


def test_maybe_load_cached_result_file_not_exists():
    """Test loading cached result when file doesn't exist."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            result = maybe_load_cached_result(config, scenario)
            assert result is None


def test_maybe_load_cached_result_success():
    """Test successfully loading a cached result."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()
    validation_result = create_mock_validation_result()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            # Write a cached result first
            write_cached_result(config, scenario, validation_result)

            # Now try to load it
            loaded_result = maybe_load_cached_result(config, scenario)

            assert loaded_result is not None
            assert loaded_result.success == validation_result.success
            assert loaded_result.export_path == validation_result.export_path
            assert loaded_result.rationale == validation_result.rationale


def test_maybe_load_cached_result_config_hash_mismatch():
    """Test cache invalidation when config hash doesn't match."""
    scenario = create_mock_scenario()
    config1 = create_mock_runner_config(model="model1")
    config2 = create_mock_runner_config(model="model2")
    validation_result = create_mock_validation_result()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            # Write cache with config1
            write_cached_result(config1, scenario, validation_result)

            # Try to load with config2 (different config)
            loaded_result = maybe_load_cached_result(config2, scenario)

            assert loaded_result is None  # Should be None due to config mismatch


def test_maybe_load_cached_result_scenario_hash_mismatch():
    """Test cache invalidation when scenario hash doesn't match."""
    scenario1 = create_mock_scenario(scenario_id="scenario1")
    scenario2 = create_mock_scenario(scenario_id="scenario2")
    config = create_mock_runner_config()
    validation_result = create_mock_validation_result()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            # Write cache with scenario1
            write_cached_result(config, scenario1, validation_result)

            # Try to load with scenario2 (different scenario)
            loaded_result = maybe_load_cached_result(config, scenario2)

            assert loaded_result is None  # Should be None due to scenario mismatch


def test_maybe_load_cached_result_invalid_json():
    """Test handling of corrupted cache files."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            # Create a corrupted cache file
            cache_key = _generate_cache_key(config, scenario)
            cache_file = _get_cache_file_path(cache_key)
            with open(cache_file, "w") as f:
                f.write("invalid json content")

            # Should handle the exception and return None
            result = maybe_load_cached_result(config, scenario)
            assert result is None


def test_write_cached_result():
    """Test writing cached result to file."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()
    validation_result = create_mock_validation_result()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            write_cached_result(config, scenario, validation_result)

            # Verify the file was created
            cache_key = _generate_cache_key(config, scenario)
            cache_file = _get_cache_file_path(cache_key)
            assert cache_file.exists()

            # Verify the content is valid JSON
            with open(cache_file, "r") as f:
                data = json.load(f)
                assert data["success"] is True
                assert data["scenario_id"] == "test_scenario"


def test_write_cached_result_exception_handling():
    """Test write_cached_result handles exceptions gracefully."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()
    validation_result = create_mock_validation_result()

    # Mock _get_cache_file_path to raise an exception
    with patch(
        "are.simulation.scenarios.utils.caching._get_cache_file_path"
    ) as mock_get_cache_file_path:
        mock_get_cache_file_path.side_effect = PermissionError("Permission denied")

        # Should not raise an exception
        write_cached_result(config, scenario, validation_result)


def test_clear_cache():
    """Test clearing all cached results."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            # Create some cache files
            (Path(temp_dir) / "cache1.json").write_text("{}")
            (Path(temp_dir) / "cache2.json").write_text("{}")
            (Path(temp_dir) / "other_file.txt").write_text("not json")

            assert len(list(Path(temp_dir).glob("*.json"))) == 2

            clear_cache()

            # Only JSON files should be removed
            assert len(list(Path(temp_dir).glob("*.json"))) == 0
            assert (Path(temp_dir) / "other_file.txt").exists()


def test_clear_cache_nonexistent_dir():
    """Test clearing cache when directory doesn't exist."""
    with patch(
        "are.simulation.scenarios.utils.caching._get_cache_dir"
    ) as mock_get_cache_dir:
        mock_get_cache_dir.return_value = Path("/nonexistent/path")

        # Should not raise an exception
        clear_cache()


def test_clear_cache_exception_handling():
    """Test clear_cache handles exceptions gracefully."""
    with patch(
        "are.simulation.scenarios.utils.caching._get_cache_dir"
    ) as mock_get_cache_dir:
        mock_cache_dir = MagicMock()
        mock_cache_dir.exists.return_value = True
        mock_cache_dir.glob.side_effect = PermissionError("Permission denied")
        mock_get_cache_dir.return_value = mock_cache_dir

        # Should not raise an exception
        clear_cache()


def test_get_cache_stats_empty_cache():
    """Test cache stats for empty cache directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            stats = get_cache_stats()

            assert stats["cache_dir"] == temp_dir
            assert stats["file_count"] == 0
            assert stats["total_size"] == 0
            assert stats["total_size_mb"] == 0


def test_get_cache_stats_with_files():
    """Test cache stats with cache files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            # Create some cache files
            (Path(temp_dir) / "cache1.json").write_text('{"test": "data1"}')
            (Path(temp_dir) / "cache2.json").write_text('{"test": "data2"}')

            stats = get_cache_stats()

            assert stats["cache_dir"] == temp_dir
            assert stats["file_count"] == 2
            assert stats["total_size"] > 0


def test_get_cache_stats_nonexistent_dir():
    """Test cache stats when directory doesn't exist."""
    with patch(
        "are.simulation.scenarios.utils.caching._get_cache_dir"
    ) as mock_get_cache_dir:
        nonexistent_path = Path("/nonexistent/path")
        mock_get_cache_dir.return_value = nonexistent_path

        stats = get_cache_stats()

        assert stats["cache_dir"] == str(nonexistent_path)
        assert stats["file_count"] == 0
        assert stats["total_size"] == 0


def test_get_cache_stats_exception_handling():
    """Test get_cache_stats handles exceptions gracefully."""
    with patch(
        "are.simulation.scenarios.utils.caching._get_cache_dir"
    ) as mock_get_cache_dir:
        mock_get_cache_dir.side_effect = PermissionError("Permission denied")

        stats = get_cache_stats()

        assert "error" in stats
        assert "Permission denied" in stats["error"]


def test_scenario_with_events():
    """Test scenario hash generation with events."""
    scenario = create_mock_scenario()

    # Create mock events
    event1 = Mock()
    event1.event_type = "user_message"
    event2 = Mock()
    event2.event_type = "agent_action"

    scenario.events = [event1, event2]

    scenario_hash = _generate_scenario_hash(scenario)
    assert isinstance(scenario_hash, str)
    assert len(scenario_hash) == 16


def test_full_cache_workflow():
    """Test the complete cache workflow: write, load, invalidate."""
    scenario = create_mock_scenario()
    config = create_mock_runner_config()
    validation_result = create_mock_validation_result()

    with tempfile.TemporaryDirectory() as temp_dir:
        with patch(
            "are.simulation.scenarios.utils.caching._get_cache_dir"
        ) as mock_get_cache_dir:
            mock_get_cache_dir.return_value = Path(temp_dir)

            # Initially no cache
            result = maybe_load_cached_result(config, scenario)
            assert result is None

            # Write to cache
            write_cached_result(config, scenario, validation_result)

            # Should now load from cache
            result = maybe_load_cached_result(config, scenario)
            assert result is not None
            assert result.success == validation_result.success

            # Check cache stats
            stats = get_cache_stats()
            assert stats["file_count"] == 1

            # Clear cache
            clear_cache()

            # Should no longer load from cache
            result = maybe_load_cached_result(config, scenario)
            assert result is None

            # Cache should be empty
            stats = get_cache_stats()
            assert stats["file_count"] == 0
