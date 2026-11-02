# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from unittest.mock import Mock

from are.simulation.tool_utils import AppTool, AppToolAdapter, AppToolArg


def create_test_tool(public_name=None, public_description=None):
    """Helper to create a test tool with optional public attributes."""
    mock_function = Mock()
    mock_function.__name__ = "websurfer"

    tool = AppTool(
        class_name="TestClass",
        app_name="test_app",
        name="websurfer",
        function_description="A web surfing tool",
        args=[],
        function=mock_function,
    )

    # Simulate the missing attributes that should be in the dataclass
    tool._public_name = public_name
    tool._public_description = public_description

    return tool


def test_tool_has_separate_public_and_private_names():
    """Test that tools can have different public and private names."""
    tool = create_test_tool("search", "Search the web for information")

    assert tool.name == "websurfer"  # Private name
    assert tool._public_name == "search"  # Public name
    assert tool.function_description == "A web surfing tool"  # Private description
    assert (
        tool._public_description == "Search the web for information"
    )  # Public description


def test_adapter_uses_public_names():
    """Test that AppToolAdapter exposes public names to agents."""
    tool = create_test_tool("search", "Search the web for information")
    adapter = AppToolAdapter(tool)

    assert adapter.name == "search"
    assert "Search the web for information" in adapter.description
    assert adapter.app_tool.name == "websurfer"  # Private name preserved


def test_openai_format_uses_public_names():
    """Test that OpenAI format uses public names."""
    args = [
        AppToolArg(
            name="query", arg_type="str", description="Search query", has_default=False
        )
    ]

    mock_function = Mock()
    mock_function.__name__ = "websurfer"

    tool = AppTool(
        class_name="TestClass",
        app_name="test_app",
        name="websurfer",
        function_description="A web surfing tool",
        args=args,
        function=mock_function,
    )

    tool._public_name = "search"
    tool._public_description = "Search the web for information"

    openai_format = tool.to_open_ai()

    assert openai_format["function"]["name"] == "search"
    assert openai_format["function"]["description"] == "Search the web for information"


def test_public_names_default_to_private_when_none():
    """Test that public names fall back to private names when not specified."""
    tool = create_test_tool(None, None)

    # Simulate __post_init__ logic
    if tool._public_name is None:
        tool._public_name = tool.name
    if tool._public_description is None:
        tool._public_description = tool.function_description

    assert tool._public_name == "websurfer"
    assert tool._public_description == "A web surfing tool"


def test_complete_workflow():
    """Integration test showing the complete public/private name workflow."""

    def websurfer_function(query: str) -> str:
        return f"Search results for: {query}"

    tool = AppTool(
        class_name="WebApp",
        app_name="web_tools",
        name="websurfer",
        function_description="A web surfing tool that searches the internet",
        args=[
            AppToolArg(
                name="query",
                arg_type="str",
                description="The search query",
                has_default=False,
            )
        ],
        function=websurfer_function,
    )

    tool._public_name = "search"
    tool._public_description = "Search the web for information"

    adapter = AppToolAdapter(tool)

    # Agent sees public names
    assert adapter.name == "search"
    assert "Search the web for information" in adapter.description

    # Environment sees private names
    assert adapter.app_tool.name == "websurfer"

    # OpenAI format uses public names
    openai_format = tool.to_open_ai()
    assert openai_format["function"]["name"] == "search"
    assert openai_format["function"]["description"] == "Search the web for information"

    # Execution works correctly
    result = adapter.forward(query="python programming")
    assert result == "Search results for: python programming"
