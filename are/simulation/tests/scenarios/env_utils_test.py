# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Tests for the expand_env_vars function in env_utils.py.

This test suite verifies the functionality of the environment variable
expansion utility function using pytest.

Note:
    - os module is imported for environment variable handling via monkeypatch
    - pytest is imported for its fixtures (particularly monkeypatch)
"""

from are.simulation.scenarios.utils.env_utils import expand_env_vars


def test_simple_string_expansion(monkeypatch):
    """
    Test expanding a simple environment variable in a string.

    Verifies that a basic environment variable reference is correctly
    replaced with its value from the environment.
    """
    monkeypatch.setenv("TEST_VAR", "test_value")
    result = expand_env_vars("Value is ${TEST_VAR}")
    assert result == "Value is test_value"


def test_string_with_default_value(monkeypatch):
    """
    Test expanding an environment variable with a default value.

    Verifies that:

    - When an environment variable is not set, the default value is used
    - When an environment variable is set, its value is used instead of the default
    """
    # Environment variable is not set, should use default
    result = expand_env_vars("Value is ${MISSING_VAR:-default_value}")
    assert result == "Value is default_value"

    # Environment variable is set, should use that instead of default
    monkeypatch.setenv("MISSING_VAR", "actual_value")
    result = expand_env_vars("Value is ${MISSING_VAR:-default_value}")
    assert result == "Value is actual_value"


def test_missing_var_without_default():
    """
    Test behavior when an environment variable is missing and no default is provided.

    Verifies that when no default is provided and the variable doesn't exist,
    the original reference is preserved in the output.
    """
    # When no default is provided and the variable doesn't exist, the original reference should remain
    result = expand_env_vars("Value is ${NONEXISTENT_VAR}")
    assert result == "Value is ${NONEXISTENT_VAR}"


def test_multiple_vars_in_string(monkeypatch):
    """
    Test expanding multiple environment variables in a single string.

    Verifies that:

    - Multiple variables in a single string are all expanded correctly
    - A mix of existing and non-existing variables with defaults works as expected
    """
    monkeypatch.setenv("VAR1", "first")
    monkeypatch.setenv("VAR2", "second")
    result = expand_env_vars("${VAR1} and ${VAR2}")
    assert result == "first and second"

    # Mix of existing and non-existing variables with defaults
    monkeypatch.delenv("VAR2", raising=False)
    result = expand_env_vars("${VAR1} and ${VAR2:-default}")
    assert result == "first and default"


def test_dictionary_expansion(monkeypatch):
    """
    Test expanding environment variables in a dictionary.

    Verifies that environment variables in dictionary values are expanded
    correctly, including in nested dictionaries.
    """
    test_dict = {
        "url": "https://${HOST}:${PORT}",
        "auth": {
            "token": "Bearer ${TOKEN:-default_token}",
            "user": "${TEST_USER:-anonymous}",  # Using TEST_USER instead of USER to avoid conflicts
        },
    }

    # Ensure TEST_USER is not set
    monkeypatch.delenv("TEST_USER", raising=False)

    monkeypatch.setenv("HOST", "example.com")
    monkeypatch.setenv("PORT", "8080")
    monkeypatch.setenv("TOKEN", "secret")

    result = expand_env_vars(test_dict)

    expected = {
        "url": "https://example.com:8080",
        "auth": {
            "token": "Bearer secret",
            "user": "anonymous",  # TEST_USER not set, should use default
        },
    }

    assert result == expected


def test_allowed_env_vars_restriction(monkeypatch):
    """
    Test that only allowed environment variables are expanded when allowed list is provided.

    Verifies that:
    - Variables in the allowed list are expanded normally
    - Variables not in the allowed list remain as literal placeholders
    - Default values are ignored for non-allowed variables
    - The restriction works in nested structures (dicts and lists)
    """
    # Set up environment variables
    monkeypatch.setenv("HF_TOKEN", "secret_token")
    monkeypatch.setenv("OTHER_VAR", "other_value")
    monkeypatch.setenv("THIRD_VAR", "third_value")

    # Test simple string with mixed allowed/disallowed variables
    result = expand_env_vars("${HF_TOKEN} ${OTHER_VAR}", allowed=["HF_TOKEN"])
    assert result == "secret_token ${OTHER_VAR}"

    # Test with default values - allowed variable should expand, disallowed should remain as placeholder
    result = expand_env_vars(
        "${HF_TOKEN:-default1} ${OTHER_VAR:-default2}", allowed=["HF_TOKEN"]
    )
    assert result == "secret_token ${OTHER_VAR:-default2}"

    # Test with non-existent allowed variable with default
    result = expand_env_vars(
        "${HF_TOKEN} ${MISSING_VAR:-default}", allowed=["HF_TOKEN", "MISSING_VAR"]
    )
    assert result == "secret_token default"

    # Test with non-existent allowed variable without default
    result = expand_env_vars(
        "${HF_TOKEN} ${MISSING_VAR}", allowed=["HF_TOKEN", "MISSING_VAR"]
    )
    assert result == "secret_token ${MISSING_VAR}"

    # Test in dictionary structure
    test_dict = {
        "auth": {
            "token": "Bearer ${HF_TOKEN}",
            "other": "${OTHER_VAR:-default_other}",
        },
        "config": {
            "third": "${THIRD_VAR}",
            "allowed": "${HF_TOKEN:-fallback}",
        },
    }

    result = expand_env_vars(test_dict, allowed=["HF_TOKEN"])
    expected = {
        "auth": {
            "token": "Bearer secret_token",  # HF_TOKEN is allowed, should expand
            "other": "${OTHER_VAR:-default_other}",  # OTHER_VAR not allowed, should remain as placeholder
        },
        "config": {
            "third": "${THIRD_VAR}",  # THIRD_VAR not allowed, should remain as placeholder
            "allowed": "secret_token",  # HF_TOKEN is allowed, should expand
        },
    }

    assert result == expected

    # Test in list structure
    test_list = [
        "${HF_TOKEN}",
        "${OTHER_VAR:-list_default}",
        ["nested_${HF_TOKEN}", "nested_${THIRD_VAR}"],
    ]

    result = expand_env_vars(test_list, allowed=["HF_TOKEN"])
    expected = [
        "secret_token",  # HF_TOKEN is allowed
        "${OTHER_VAR:-list_default}",  # OTHER_VAR not allowed
        ["nested_secret_token", "nested_${THIRD_VAR}"],  # Mixed in nested list
    ]

    assert result == expected


def test_allowed_empty_list(monkeypatch):
    """
    Test that when allowed list is empty, no variables are expanded.
    """
    monkeypatch.setenv("TEST_VAR", "test_value")

    result = expand_env_vars("${TEST_VAR} and ${OTHER_VAR:-default}", allowed=[])
    assert result == "${TEST_VAR} and ${OTHER_VAR:-default}"


def test_allowed_none_expands_all(monkeypatch):
    """
    Test that when allowed is None (default), all variables are expanded as before.
    """
    monkeypatch.setenv("VAR1", "value1")
    monkeypatch.setenv("VAR2", "value2")

    # Test with allowed=None (explicit)
    result = expand_env_vars("${VAR1} ${VAR2} ${MISSING:-default}", allowed=None)
    assert result == "value1 value2 default"

    # Test without allowed parameter (should behave the same)
    result = expand_env_vars("${VAR1} ${VAR2} ${MISSING:-default}")
    assert result == "value1 value2 default"


def test_list_expansion(monkeypatch):
    """
    Test expanding environment variables in a list.

    Verifies that environment variables in list items are expanded correctly,
    including in nested lists.
    """
    test_list = [
        "${VAR1:-default1}",
        "prefix_${VAR2}_suffix",
        ["nested_${VAR3:-default3}"],
    ]

    monkeypatch.setenv("VAR2", "value2")

    result = expand_env_vars(test_list)

    expected = [
        "default1",  # VAR1 not set, use default
        "prefix_value2_suffix",  # VAR2 is set
        ["nested_default3"],  # VAR3 not set, use default in nested list
    ]

    assert result == expected


def test_non_string_values():
    """
    Test that non-string values are returned unchanged.

    Verifies that numeric values, booleans, and None are returned as-is
    without any processing.
    """
    assert expand_env_vars(123) == 123
    assert expand_env_vars(True) is True
    assert expand_env_vars(None) is None


def test_complex_nested_structure(monkeypatch):
    """
    Test expanding environment variables in a complex nested structure.

    Verifies that environment variables are correctly expanded in a complex
    nested structure with dictionaries and lists at multiple levels.
    """
    complex_structure = {
        "server": {
            "host": "${HOST:-localhost}",
            "port": "${PORT:-8080}",
            "env": {"DEBUG": "${DEBUG:-false}", "LOG_LEVEL": "${LOG_LEVEL:-info}"},
        },
        "auth": {
            "headers": {
                "Authorization": "Bearer ${API_KEY}",
                "Custom-Header": "${CUSTOM_HEADER:-default-header}",
            }
        },
        "options": [
            "${OPT1:-opt1}",
            "${OPT2:-opt2}",
            {"nested": "${NESTED:-nested-default}"},
        ],
    }

    monkeypatch.setenv("HOST", "example.com")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("API_KEY", "secret_key")
    monkeypatch.setenv("OPT2", "custom_opt2")

    result = expand_env_vars(complex_structure)

    expected = {
        "server": {
            "host": "example.com",  # From environment
            "port": "8080",  # Default
            "env": {
                "DEBUG": "true",  # From environment
                "LOG_LEVEL": "info",  # Default
            },
        },
        "auth": {
            "headers": {
                "Authorization": "Bearer secret_key",  # From environment
                "Custom-Header": "default-header",  # Default
            }
        },
        "options": [
            "opt1",  # Default
            "custom_opt2",  # From environment
            {"nested": "nested-default"},  # Default
        ],
    }

    assert result == expected
