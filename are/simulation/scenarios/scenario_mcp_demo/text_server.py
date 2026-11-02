#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Text tools MCP server for use with Meta Agents Research Environments MCPApp.

This server provides text manipulation operations as MCP tools.
"""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

NAME = "Text Tools MCP Server"

# Create an MCP server
mcp = FastMCP(NAME)


# Text tools
@mcp.tool(
    annotations=ToolAnnotations(
        title="Text Reverser",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=True,  # Calling it multiple times with same args has same result
        openWorldHint=False,  # Operates in a closed text domain
    )
)
def reverse_text(text: str) -> str:
    """Reverse the characters in a string."""
    return text[::-1]


@mcp.tool(
    annotations=ToolAnnotations(
        title="Word Counter",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=True,  # Calling it multiple times with same args has same result
        openWorldHint=False,  # Operates in a closed text domain
    )
)
def count_words(text: str) -> int:
    """Count the number of words in a string."""
    return len(text.split())


@mcp.tool(
    annotations=ToolAnnotations(
        title="Text Uppercaser",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=True,  # Calling it multiple times with same args has same result
        openWorldHint=False,  # Operates in a closed text domain
    )
)
def to_uppercase(text: str) -> str:
    """Convert a string to uppercase."""
    return text.upper()


@mcp.tool(
    annotations=ToolAnnotations(
        title="Text Lowercaser",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=True,  # Calling it multiple times with same args has same result
        openWorldHint=False,  # Operates in a closed text domain
    )
)
def to_lowercase(text: str) -> str:
    """Convert a string to lowercase."""
    return text.lower()


@mcp.resource("help://text")
def get_text_help() -> str:
    """Get help on text tools."""
    return """
Text Tools:
- reverse_text(text): Reverse the characters in a string
- count_words(text): Count the number of words in a string
- to_uppercase(text): Convert a string to uppercase
- to_lowercase(text): Convert a string to lowercase
"""


@mcp.prompt()
def format_text(text: str, style: str = "default") -> str:
    """
    Prompt for formatting text.

    Args:
        text: The text to format.
        style: The formatting style (default, formal, casual, technical).
    """
    return f"""
Please format the following text in a {style} style:

{text}

Provide the formatted text and explain the changes you made.
"""


# Run the server if executed directly
if __name__ == "__main__":
    mcp.run()
