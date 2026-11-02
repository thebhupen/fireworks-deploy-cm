# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from dataclasses import dataclass, replace
from enum import Enum
from typing import Any


class DifficultyLevel(str, Enum):
    LEVEL_1: str = "level_1"  # type: ignore
    LEVEL_2: str = "level_2"  # type: ignore
    LEVEL_3: str = "level_3"  # type: ignore


@dataclass
class UserContext:
    """
    Context of a user. It contains the following fields:
    - profile: Information about the user's profile.
    - relations: Information about the user's relations.
    - relation_profiles: User's relation profiles.
    - conversations: User's conversations.
    - assistant_calls: User calls to the assistant.
    """

    profile: dict[str, Any] = ()  # type: ignore
    relations: list[dict[str, Any]] = ()  # type: ignore
    relation_profiles: list[dict[str, Any]] = ()  # type: ignore
    events: list[dict[str, Any]] = ()  # type: ignore
    conversations: list[dict[str, Any]] = ()  # type: ignore
    assistant_calls: list[str] = ()  # type: ignore

    def as_dict(self):
        return {k: self.__dict__[k] for k in self.__dict__}

    def replace(self, **kwargs):
        return replace(self, **kwargs)
