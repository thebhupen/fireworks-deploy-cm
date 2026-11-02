# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import os
from types import NoneType
from typing import Any, Union

from are.simulation.utils import check_type, is_optional_type

IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


def is_on_ci() -> bool:
    """
    Returns True if the current environment is a CI environment: either Github
    CI or running inside RE.
    """
    return (
        IN_GITHUB_ACTIONS
        or os.path.exists("/re_cwd")
        or os.getenv("ARE_SIMULATION_FORCE_CI") == "1"
    )


def test_is_optional_type():
    assert not is_optional_type(None)
    assert not is_optional_type(NoneType)
    assert not is_optional_type(str)
    assert not is_optional_type(str | int)
    assert not is_optional_type(list[str])
    # Underlying type is optional, not the list itself.
    assert not is_optional_type(list[str | None])
    assert not is_optional_type(dict[str, int])
    # Underlying type is optional, not the dict itself.
    assert not is_optional_type(dict[str, int | None])

    assert is_optional_type(str | None)
    assert is_optional_type(None | str)
    assert is_optional_type(str | int | None)
    assert is_optional_type(list[str] | None)
    assert is_optional_type(dict[str, int] | None)
    assert is_optional_type(Union[str, None])
    assert is_optional_type(Union[None, str])


def test_check_type():
    # Primitives and NoneType.
    assert check_type(42, Any)
    assert check_type(42, int)
    assert not check_type(42, str)
    assert check_type(None, NoneType)
    # Optionals.
    assert check_type(None, str | None)
    assert check_type("abc", str | None)
    assert not check_type(42, str | None)
    # Lists.
    assert check_type(["abc", "def"], list[str])
    assert not check_type(["abc", 42], list[int])
    assert not check_type(["abc", 42], list[str])
    # Sets.
    assert check_type({"abc", "def"}, set[str])
    assert not check_type({"abc", 42}, set[int])
    assert not check_type({"abc", 42}, set[str])
    # Dicts.
    assert check_type({"a": 0, "d": 1}, dict[str, int])
    assert not check_type({"a": 0, "d": "e"}, dict[str, int])
    # Tuples.
    assert check_type(("abc", 42), tuple[str, int])
    assert not check_type(("abc", "abc"), tuple[str, int])
    assert not check_type(("abc", "def"), tuple[str])
    assert not check_type(("abc"), tuple[str, int])
    # Nested.
    assert check_type(
        [
            {"a": 0, "b": 1},
            {"c": 2, "d": 3},
        ],
        list[dict[str, int | None]],
    )
    assert not check_type(
        [
            {"a": 0, "b": 1},
            {"c": 2, "d": "3"},
        ],
        list[dict[str, int | None]],
    )
    assert check_type(
        [
            {"a": 0, "b": 1},
            {"c": 2, "d": None},
        ],
        list[dict[str, int | None]],
    )
    assert not check_type(
        [
            {"a": 0, "b": 1},
            {"c": 2, "d": "3"},
        ],
        list[dict[str, int | None]],
    )
