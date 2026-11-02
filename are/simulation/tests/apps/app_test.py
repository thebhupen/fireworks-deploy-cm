# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from unittest.mock import MagicMock, patch

import pytest

from are.simulation.apps.app import App, ToolType
from are.simulation.tool_utils import ToolAttributeName


def test_app_initialization():
    """Test basic App initialization"""
    app = App(name="TestApp")
    assert app.name == "TestApp"
    assert isinstance(app._tool_registries, dict)
    assert len(app._tool_registries) == 4


def test_app_initialization_no_name():
    """Test App initialization without explicit name"""
    app = App()
    assert app.name == "App"


def test_register_to_env():
    """Test registering app to environment"""
    app = App("TestApp")
    mock_event_handler = MagicMock()
    mock_time_manager = MagicMock()
    app.register_time_manager(mock_time_manager)
    app.register_to_env("", mock_event_handler)
    assert app.add_event_callbacks.get("") == mock_event_handler
    assert app.time_manager == mock_time_manager


def test_get_implemented_protocols():
    """Test default protocol implementation"""
    app = App()
    assert app.get_implemented_protocols() == []


@pytest.mark.parametrize(
    "tool_type,attribute",
    [
        (ToolType.APP, ToolAttributeName.APP),
        (ToolType.USER, ToolAttributeName.USER),
        (ToolType.ENV, ToolAttributeName.ENV),
        (ToolType.DATA, ToolAttributeName.DATA),
    ],
)
def test_get_tools(tool_type: ToolType, attribute: ToolAttributeName):
    """Test getting tools for different tool types"""
    app = App()

    with patch.object(app, "get_tools_with_attribute") as mock_get:
        mock_get.return_value = [MagicMock()]

        tools = app._get_or_initialize_tools(tool_type, attribute)
        assert len(tools) == 1
        mock_get.assert_called_once_with(attribute=attribute, tool_type=tool_type)

        tools = app._get_or_initialize_tools(tool_type, attribute)
        assert len(tools) == 1
        mock_get.assert_called_once()


def test_app_name():
    """Test app_name method"""
    app = App("TestApp")
    assert app.app_name() == "TestApp"


def test_state_methods():
    """Test state-related methods"""
    app = App()
    assert app.get_state() is None
    app.load_state({})
    app.reset()


def test_env_control_methods():
    """Test environment control methods"""
    app = App()
    app.pause_env()
    app.resume_env()
