# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from typing import Type

from are.simulation.validation.base import BaseJudge
from are.simulation.validation.configs import (
    BaseJudgeConfig,
    GraphPerEventJudgeConfig,
    InContextJudgeConfig,
    ScriptedGraphPerEventJudgeConfig,
)
from are.simulation.validation.judge import GraphPerEventJudge, InContextJudge


class JudgeFactory:
    def __init__(self) -> None:
        self.judge_classes: dict[Type[BaseJudgeConfig], Type[BaseJudge]] = {
            ScriptedGraphPerEventJudgeConfig: GraphPerEventJudge,
            GraphPerEventJudgeConfig: GraphPerEventJudge,
            InContextJudgeConfig: InContextJudge,
        }

    def __call__(self, config: BaseJudgeConfig) -> BaseJudge:
        judge_class = self.judge_classes.get(type(config), None)
        if judge_class is None:
            raise ValueError(f"No judge class found for config {type(config)}")
        return judge_class(config)
