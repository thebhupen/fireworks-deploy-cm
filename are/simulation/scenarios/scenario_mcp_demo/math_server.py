#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Math tools MCP server for use with Meta Agents Research Environments MCPApp.

This server provides mathematical operations as MCP tools.
"""

import math

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

NAME = "Math Tools MCP Server"

# Create an MCP server
mcp = FastMCP(NAME)


# Math tools
@mcp.tool(
    annotations=ToolAnnotations(
        title="Addition Tool",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=True,  # Calling it multiple times with same args has same result
        openWorldHint=False,  # Operates in a closed mathematical domain
    )
)
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


@mcp.tool(
    annotations=ToolAnnotations(
        title="Subtraction Tool",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=True,  # Calling it multiple times with same args has same result
        openWorldHint=False,  # Operates in a closed mathematical domain
    )
)
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


@mcp.tool(
    annotations=ToolAnnotations(
        title="Multiplication Tool",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=True,  # Calling it multiple times with same args has same result
        openWorldHint=False,  # Operates in a closed mathematical domain
    )
)
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


@mcp.tool(
    annotations=ToolAnnotations(
        title="Division Tool",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=True,  # Calling it multiple times with same args has same result
        openWorldHint=False,  # Operates in a closed mathematical domain
    )
)
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


@mcp.tool(
    annotations=ToolAnnotations(
        title="Square Root Calculator",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=True,  # Calling it multiple times with same args has same result
        openWorldHint=False,  # Operates in a closed mathematical domain
    )
)
def square_root(x: float) -> float:
    """Calculate the square root of a number."""
    if x < 0:
        raise ValueError("Cannot calculate square root of a negative number")
    return math.sqrt(x)


@mcp.resource("help://math")
def get_math_help() -> str:
    """Get help on math tools."""
    return """
Math Tools:
- add(a, b): Add two numbers
- subtract(a, b): Subtract b from a
- multiply(a, b): Multiply two numbers
- divide(a, b): Divide a by b
- square_root(x): Calculate the square root of a number
"""


@mcp.prompt()
def calculate(expression: str) -> str:
    """
    Prompt for performing calculations.

    Args:
        expression: The mathematical expression to calculate.
    """
    return f"""
Please calculate the result of the following mathematical expression:

{expression}

Show your work step by step, and provide the final answer.
"""


# Run the server if executed directly
if __name__ == "__main__":
    mcp.run()
