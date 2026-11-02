# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import pytest

from are.simulation.agents.default_agent.tools.json_action_executor import (
    JsonActionExecutor,
)
from are.simulation.apps import App
from are.simulation.exceptions import FormatError
from are.simulation.tool_utils import app_tool


class DummyApp(App):
    @app_tool()
    def add(self, a: int, b: int) -> int:
        """
        Add two numbers
        :param a: first number
        :param b: second number
        :return: sum of a and b
        """
        return a + b

    @app_tool()
    def multiply(self, a: int, b: int) -> int:
        """
        Multiply two numbers
        :param a: first number
        :param b: second number
        :return: product of a and b
        """
        return a * b


def test_fail_multiple_actions_json():
    json_executor = JsonActionExecutor()

    json_multiple_action = """
    Thought: I will add 2 and 3

    Action:
    ```json
    {
        "tool": "DummyApp__add",
        "args": {
            "a": 2,
            "b": 3
        }
    }
    ```

    Action:
    ```json
    {
        "tool": "DummyApp__add",
        "args": {
            "a": 2,
            "b": 3
        }
    }
    ```
    """

    with pytest.raises(FormatError):
        json_executor.extract_action(json_multiple_action, split_token="Action:")
