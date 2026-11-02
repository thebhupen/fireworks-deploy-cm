# MCP Demo Scenario

This scenario demonstrates the Model Context Protocol (MCP) integration with Meta Agents Research Environments, showcasing various tools organized into separate specialized servers.

## Overview

The MCP Demo Scenario provides a collection of tools across different domains, each hosted in a separate MCP server. This modular approach demonstrates:

1. How to organize tools by functionality
2. How to use tool annotations to describe tool behavior
3. How to filter tools based on their properties (e.g., read-only tools)
4. How to dynamically create MCP tools that wrap CLI commands

## Read-Only Filtering

The scenario demonstrates the ability to filter tools based on their `readOnlyHint` annotation:

- **TodoApp**: Exposes all todo tools
- **TodoReadOnly**: Exposes only the `list_todos` tool (filtered using `only_read_only=True`)

This feature is useful for safety-critical applications or when you want to ensure that tools won't make any changes to their environment.

## Running the Scenario

To run the scenario:

1. Start Meta Agents Research Environments with the MCP demo scenario:
   ```
   uvx --from meta-agents-research-environments are-gui -s scenario_mcp_demo -a default
   ```

2. The scenario will automatically start the MCP servers and register the apps.

3. You can then interact with the tools through the Meta Agents Research Environments interface.

## Implementation Details

The scenario is implemented using the following components:

- **MCPApp**: A Meta Agents Research Environments app that connects to an MCP server and exposes its tools
- **FastMCP**: A Python implementation of the MCP server
- **ToolAnnotations**: A class that provides metadata about tool behavior

Each server is implemented as a separate Python script that creates an MCP server and registers tools with appropriate annotations.

## Server Types

The scenario includes several types of MCP servers:

### Static Tool Servers

These servers have predefined tools with fixed functionality:

- **math_server.py**: Mathematical operations (add, subtract, multiply, etc.)
- **text_server.py**: Text manipulation tools (reverse, uppercase, etc.)
- **utility_server.py**: Utility functions (get time, random numbers, etc.)
- **todo_server.py**: Todo list management (add, list, complete, delete)

### Dynamic CLI Wrapper Server

The **cli_mcp_server.py** demonstrates how to dynamically create MCP tools that wrap CLI commands:

1. It parses the help output of a CLI command to discover available subcommands
2. For each subcommand, it parses the help output to discover parameters
3. It creates MCP tools that wrap these subcommands, with appropriate annotations
4. It provides resources for help and metadata about the commands

#### Using the CLI Wrapper Server

The CLI wrapper server can be used with any CLI command that follows a standard help format:

```bash
uv run cli_mcp_server.py <cli_command>
```

For example:
```bash
uv run cli_mcp_server.py tasks  # Wraps the 'tasks' CLI command
uv run cli_mcp_server.py git    # Wraps the 'git' CLI command
```

The server will automatically discover all available commands and their parameters, and create MCP tools for each command.
