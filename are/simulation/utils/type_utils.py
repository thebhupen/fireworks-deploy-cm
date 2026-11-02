# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import inspect
from functools import wraps
from types import NoneType, UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints


def is_optional_type(t: Any) -> bool:
    """
    Check if a type is an Optional type (Union with None).

    :param t: The type to check
    :type t: Any
    :return: True if the type is Optional, False otherwise
    :rtype: bool
    """
    return get_origin(t) in {Union, UnionType} and NoneType in get_args(t)


def check_type(value, expected_type):
    """
    Check if a value matches the expected type, with support for complex types.

    This function supports checking against Union types, container types like
    list, set, dict, and tuple, and handles Any type as always matching.

    :param value: The value to check
    :param expected_type: The expected type
    :return: True if the value matches the expected type, False otherwise
    """
    if expected_type == Any:
        return True
    origin = get_origin(expected_type)
    expected_args = get_args(expected_type)
    if origin in {Union, UnionType}:
        # Optionals are handled here as well.
        return any(check_type(value, t) for t in expected_args)
    if origin is not None:
        if origin in {list, set}:
            return isinstance(value, (list, set)) and all(
                check_type(item, get_args(expected_type)[0]) for item in value
            )
        elif origin is dict:
            return isinstance(value, dict) and all(
                check_type(k, get_args(expected_type)[0])
                and check_type(v, get_args(expected_type)[1])
                for k, v in value.items()
            )
        elif origin is tuple:
            return (
                isinstance(value, tuple)
                and len(value) == len(get_args(expected_type))
                and all(
                    check_type(v, t) for v, t in zip(value, get_args(expected_type))
                )
            )
    return isinstance(value, expected_type)


def type_check(func):
    """
    Decorator to check function arguments against their type annotations.

    This decorator inspects the function's type hints and validates that all
    arguments passed to the function match their expected types.

    :param func: The function to decorate
    :return: The decorated function that performs type checking
    :raises TypeError: If an argument doesn't match its expected type
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        signature = inspect.signature(func)
        bound_args = signature.bind(*args, **kwargs)
        type_hints = get_type_hints(func)

        for name, value in bound_args.arguments.items():
            if name in type_hints:
                expected_type = type_hints[name]
                if not check_type(value, expected_type):
                    raise TypeError(
                        f"Argument '{name}' must be of type {expected_type}, got {type(value)}"
                    )

        return func(*args, **kwargs)

    return wrapper
