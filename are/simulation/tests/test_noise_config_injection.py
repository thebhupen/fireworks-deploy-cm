# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Unit tests for noise configuration injection.

Tests that the --noise flag properly creates the correct noise configurations.
"""

import unittest

from are.simulation.cli.utils import create_noise_configs
from are.simulation.scenarios.utils.scenario_expander import EnvEventsConfig
from are.simulation.types import ToolAugmentationConfig


class TestNoiseConfigInjection(unittest.TestCase):
    """Test that noise configs are properly created and have correct types."""

    def test_create_noise_configs_returns_correct_types(self):
        """Test that create_noise_configs returns the correct config types."""
        tool_config, env_config = create_noise_configs()

        # Verify correct types are returned
        self.assertIsInstance(tool_config, ToolAugmentationConfig)
        self.assertIsInstance(env_config, EnvEventsConfig)

    def test_tool_augmentation_config_properties(self):
        """Test that tool augmentation config has expected properties."""
        tool_config, _ = create_noise_configs()

        # Test that it's the right type
        self.assertIsInstance(tool_config, ToolAugmentationConfig)

        # Test that it has the expected attributes (these come from the actual implementation)
        self.assertTrue(hasattr(tool_config, "tool_failure_probability"))
        self.assertTrue(hasattr(tool_config, "apply_tool_name_augmentation"))
        self.assertTrue(hasattr(tool_config, "apply_tool_description_augmentation"))

    def test_env_events_config_properties(self):
        """Test that environment events config has expected properties and default values."""
        _, env_config = create_noise_configs()

        # Test that it's the right type
        self.assertIsInstance(env_config, EnvEventsConfig)

        # Test expected default values (from the actual implementation)
        self.assertEqual(env_config.num_env_events_per_minute, 10)
        self.assertEqual(env_config.env_events_seed, 0)

        # Test that the values are of correct types
        self.assertIsInstance(env_config.num_env_events_per_minute, int)
        self.assertIsInstance(env_config.env_events_seed, int)

        # Test that values are in expected ranges
        self.assertGreater(env_config.num_env_events_per_minute, 0)
        self.assertGreaterEqual(env_config.env_events_seed, 0)

    def test_noise_configs_are_different_instances(self):
        """Test that multiple calls to create_noise_configs return separate instances."""
        tool_config1, env_config1 = create_noise_configs()
        tool_config2, env_config2 = create_noise_configs()

        # Should be different object instances (not the same reference)
        self.assertIsNot(tool_config1, tool_config2)
        self.assertIsNot(env_config1, env_config2)

        # But should have the same values (for env_config at least)
        self.assertEqual(
            env_config1.num_env_events_per_minute, env_config2.num_env_events_per_minute
        )
        self.assertEqual(env_config1.env_events_seed, env_config2.env_events_seed)


if __name__ == "__main__":
    unittest.main()
