# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import os
import re
from typing import Any


def expand_env_vars(
    value: str | dict | list | Any, allowed: list[str] | None = None
) -> Any:
    """
    Recursively expand environment variables in strings, lists, and dictionaries.

    Environment variables are specified in the format ``${VAR_NAME}`` or
    ``${VAR_NAME:-default_value}``. If the environment variable is not set and
    no default is provided, the original string is returned.

    :param value: The value to expand environment variables in
    :type value: str | dict | list | Any
    :param allowed: List of allowed environment variable names to expand. If None, all variables are allowed.
    :type allowed: list[str] | None
    :return: The value with environment variables expanded
    :rtype: Any

    Examples
    --------

    Simple string expansion::

        >>> os.environ["API_KEY"] = "secret_key"
        >>> expand_env_vars("Bearer ${API_KEY}")
        'Bearer secret_key'

    Using default values::

        >>> expand_env_vars("${MISSING_VAR:-default_value}")
        'default_value'

    Expanding variables in dictionaries::

        >>> expand_env_vars({"url": "https://${HOST:-localhost}:${PORT:-8080}"})
        {'url': 'https://localhost:8080'}

    Expanding variables in lists::

        >>> expand_env_vars(["${VAR1:-one}", "${VAR2:-two}"])
        ['one', 'two']

    Restricting allowed variables::

        >>> expand_env_vars("${HF_TOKEN} ${OTHER_VAR}", allowed=["HF_TOKEN"])
        'token_value ${OTHER_VAR}'
    """
    if isinstance(value, str):
        # Pattern to match ${VAR_NAME} or ${VAR_NAME:-default_value}
        pattern = r"\${([^}^{]+?)(?::-([^}]+))?}"

        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2)

            # Check if this variable is allowed to be expanded
            if allowed is not None and var_name not in allowed:
                # Return the original placeholder if not allowed
                return match.group(0)

            # Get the environment variable value or use the default
            env_value = os.environ.get(var_name)
            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                # If no default and env var doesn't exist, return the original
                return f"${{{var_name}}}"

        # Replace all environment variables in the string
        return re.sub(pattern, replace_var, value)

    elif isinstance(value, dict):
        # Recursively expand environment variables in dictionary values
        return {k: expand_env_vars(v, allowed) for k, v in value.items()}

    elif isinstance(value, list):
        # Recursively expand environment variables in list items
        return [expand_env_vars(item, allowed) for item in value]

    else:
        # Return other types unchanged
        return value
