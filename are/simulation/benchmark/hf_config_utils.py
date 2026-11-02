# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Utilities for handling config name suffix manipulation in GAIA2 benchmark.

This module centralizes the logic for creating and parsing config names with suffixes
to avoid duplication between hf_upload_utils.py and huggingface_loader.py.
"""

# Define the suffixes used for different phases
AGENT2AGENT_SUFFIX = "_a2a"
NOISE_SUFFIX = "_noise"

# Phase names
PHASE_STANDARD = "standard"
PHASE_AGENT2AGENT = "agent2agent"
PHASE_NOISE = "noise"


def create_config_name(base_config: str, phase_name: str) -> str:
    """
    Create a config name with appropriate suffix based on the phase.

    Args:
        base_config: The base config name (e.g., "execution", "search")
        phase_name: The phase name ("standard", "agent2agent", "noise")

    Returns:
        Config name with appropriate suffix

    Examples:
        >>> create_config_name("execution", "standard")
        "execution"
        >>> create_config_name("execution", "agent2agent")
        "execution_a2a"
        >>> create_config_name("execution", "noise")
        "execution_noise"
    """
    if phase_name == PHASE_STANDARD:
        return base_config
    elif phase_name == PHASE_AGENT2AGENT:
        return f"{base_config}{AGENT2AGENT_SUFFIX}"
    elif phase_name == PHASE_NOISE:
        return f"{base_config}{NOISE_SUFFIX}"
    else:
        # For any other phase, use the phase name as suffix
        return f"{base_config}_{phase_name}"


def parse_config_name(config_name: str) -> tuple[str, str]:
    """
    Parse a config name to extract the base config and phase.

    Args:
        config_name: The config name (potentially with suffix)

    Returns:
        Tuple of (base_config, phase_name)

    Examples:
        >>> parse_config_name("execution")
        ("execution", "standard")
        >>> parse_config_name("execution_a2a")
        ("execution", "agent2agent")
        >>> parse_config_name("execution_noise")
        ("execution", "noise")
        >>> parse_config_name("execution_custom")
        ("execution", "custom")
    """
    if config_name.endswith(AGENT2AGENT_SUFFIX):
        base_config = config_name[: -len(AGENT2AGENT_SUFFIX)]
        return base_config, PHASE_AGENT2AGENT
    elif config_name.endswith(NOISE_SUFFIX):
        base_config = config_name[: -len(NOISE_SUFFIX)]
        return base_config, PHASE_NOISE
    elif "_" in config_name:
        # Handle other custom suffixes
        parts = config_name.split("_", 1)  # Split on first underscore only
        base_config = parts[0]
        phase_name = parts[1]
        return base_config, phase_name
    else:
        # No suffix, it's a standard config
        return config_name, PHASE_STANDARD


def get_base_config(config_name: str) -> str:
    """
    Extract the base config name from a potentially suffixed config name.

    This is a convenience function that just returns the base config part.

    Args:
        config_name: The config name (potentially with suffix)

    Returns:
        The base config name without any suffix

    Examples:
        >>> get_base_config("execution")
        "execution"
        >>> get_base_config("execution_a2a")
        "execution"
        >>> get_base_config("execution_noise")
        "execution"
        >>> get_base_config("execution_custom")
        "execution"
    """
    base_config, _ = parse_config_name(config_name)
    return base_config


def is_artificial_config(config_name: str) -> bool:
    """
    Check if a config name represents an artificial config (has a suffix).

    Args:
        config_name: The config name to check

    Returns:
        True if the config has a suffix (is artificial), False otherwise

    Examples:
        >>> is_artificial_config("execution")
        False
        >>> is_artificial_config("execution_a2a")
        True
        >>> is_artificial_config("execution_noise")
        True
    """
    _, phase_name = parse_config_name(config_name)
    return phase_name != PHASE_STANDARD
