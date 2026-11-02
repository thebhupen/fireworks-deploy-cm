# HuggingFace Demo MCP Scenario

This scenario loads the HuggingFace demo universe and populates it with additional MCP (Model Context Protocol) apps.

## Overview

The `ScenarioHuggingFaceDemoMCP` scenario extends the base HuggingFace demo by allowing you to add custom MCP apps through a JSON configuration file. This enables you to integrate both local and remote MCP servers into your simulation without modifying the scenario code.

## Usage

### Basic Usage

To run the scenario with the default HuggingFace demo apps:

```bash
uvx --from meta-agents-research-environments  are-gui -s scenario_hf_demo_mcp -a default
```

### Adding Custom MCP Apps

To add custom MCP apps to the scenario:

1. Create a JSON file following the Claude MCP definition format (see example below)
2. Set the `MCP_APPS_JSON_PATH` environment variable to point to your JSON file
3. Run the scenario

```bash
# Set the environment variable
export MCP_APPS_JSON_PATH=/path/to/your/mcp_apps.json

# Run the scenario
uvx --from meta-agents-research-environments  are-gui -s scenario_hf_demo_mcp -a default
```

Alternatively, you can add the environment variable to your `.env` file:

```
MCP_APPS_JSON_PATH=/path/to/your/mcp_apps.json
```

## MCP Apps JSON Format

The JSON file should follow this structure:

```json
{
  "mcpServers": {
    "app-name-1": {
      "command": "python",
      "args": [
        "/path/to/mcp_server.py",
        "--option1",
        "value1"
      ],
      "env": {
        "ENV_VAR1": "value1",
        "ENV_VAR2": "value2"
      }
    },
    "app-name-2": {
      "type": "sse",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer your-token-here"
      }
    }
  }
}
```

### Local MCP Servers

For local MCP servers that run as a subprocess:

```json
"app-name": {
  "command": "python",
  "args": [
    "/path/to/mcp_server.py",
    "--option1",
    "value1"
  ],
  "env": {
    "ENV_VAR1": "value1"
  }
}
```

- `command`: The command to run the server
- `args`: List of arguments to pass to the command
- `env`: (Optional) Environment variables for the server process

### Remote MCP Servers (SSE)

For remote MCP servers accessible via HTTP Server-Sent Events:

```json
"app-name": {
  "type": "sse",
  "url": "https://api.example.com/mcp",
  "headers": {
    "Authorization": "Bearer your-token-here",
    "Custom-Header": "value"
  }
}
```

- `type`: Set to "sse" for Server-Sent Events
- `url`: The URL of the remote MCP server
- `headers`: (Optional) HTTP headers for authentication and other purposes

## Example JSON Configuration

Here's a complete example with both local and remote MCP servers:

```json
{
  "mcpServers": {
    "calendar": {
      "command": "python",
      "args": [
        "/path/to/are_simulation_mcp_server.py",
        "--apps",
        "are.simulation.apps.calendar.CalendarApp",
        "--name",
        "Meta Agents Research Environments Calendar"
      ]
    },
    "scenario-tools": {
      "command": "python",
      "args": [
        "/path/to/are_simulation_mcp_server.py",
        "--scenario",
        "scenario_tutorial"
      ]
    },
    "api-server": {
      "type": "sse",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}
```

## Environment Variables

The scenario supports the following environment variables:

- `MCP_APPS_JSON_PATH`: Path to the JSON file containing MCP app configurations

You can set these variables in your shell or in a `.env` file in the project root.

## Notes

- The scenario will automatically load and create MCP apps from the JSON file if the `MCP_APPS_JSON_PATH` environment variable is set.
- If the JSON file is not found or contains invalid data, the scenario will log an error but continue to run with the default apps.
- Environment variables in the JSON file (like `${API_KEY}`) will be expanded using the current environment.
