#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Utility tools MCP server for use with Meta Agents Research Environments MCPApp.

This server provides various utility operations as MCP tools.
"""

import datetime
import json
import random

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

NAME = "Utility Tools MCP Server"

# Create an MCP server
mcp = FastMCP(NAME)


# Utility tools
@mcp.tool(
    annotations=ToolAnnotations(
        title="Current Time Provider",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=False,  # Different results each time
        openWorldHint=True,  # Interacts with the external world (time)
    )
)
def get_current_time() -> str:
    """Get the current time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool(
    annotations=ToolAnnotations(
        title="Random Number Generator",
        readOnlyHint=True,  # This tool doesn't modify its environment
        idempotentHint=False,  # Different results each time
        openWorldHint=True,  # Interacts with external randomness source
    )
)
def generate_random_number(min_value: int = 1, max_value: int = 100) -> int:
    """Generate a random number between min_value and max_value (inclusive)."""
    return random.randint(min_value, max_value)


@mcp.tool(
    annotations=ToolAnnotations(
        title="JSON Formatter",
        readOnlyHint=False,  # This tool modifies its input
        destructiveHint=False,  # It performs additive updates (formatting), not destructive ones
        idempotentHint=True,  # Formatting the same JSON multiple times gives the same result
        openWorldHint=False,  # Operates in a closed domain
    )
)
def format_json(json_str: str) -> str:
    """Format a JSON string with proper indentation."""
    try:
        parsed = json.loads(json_str)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")


@mcp.resource("data://sample")
def get_sample_data() -> str:
    """Get sample data."""
    data = {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ],
        "products": [
            {"id": 101, "name": "Laptop", "price": 999.99},
            {"id": 102, "name": "Smartphone", "price": 499.99},
            {"id": 103, "name": "Headphones", "price": 99.99},
        ],
    }
    return json.dumps(data, indent=2)


@mcp.resource("help://utility")
def get_utility_help() -> str:
    """Get help on utility tools."""
    return """
Utility Tools:
- get_current_time(): Get the current time
- generate_random_number(min_value, max_value): Generate a random number
- format_json(json_str): Format a JSON string with proper indentation
"""


# Run the server if executed directly
if __name__ == "__main__":
    mcp.run()
