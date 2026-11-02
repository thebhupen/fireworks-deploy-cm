#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
CLI Command MCP server for use with Meta Agents Research Environments MCPApp.

This server dynamically creates MCP tools that wrap CLI commands.
It parses the help output of the CLI to discover commands and parameters.
"""

import json
import logging
import re
import shlex
import subprocess
from dataclasses import dataclass, field

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools.base import Tool as MCPTool
from mcp.server.fastmcp.tools.tool_manager import ToolManager
from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase, FuncMetadata
from pydantic import Field, create_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class CommandParam:
    """
    Represents a parameter for a CLI command.

    :param name: Name of the parameter
    :param help_text: Help text describing the parameter
    :param is_positional: Whether this is a positional argument
    :param is_required: Whether this parameter is required
    :param default: Default value for the parameter if any
    :param choices: List of valid choices for the parameter if any
    """

    name: str
    help_text: str = ""
    is_positional: bool = False
    is_required: bool = False
    default: str | None = None
    choices: list[str] | None = None


@dataclass
class CliCommand:
    """
    Represents a CLI command with its parameters and help text.

    :param name: Name of the command
    :param help_text: Help text describing the command
    :param params: List of parameters for this command
    """

    name: str
    help_text: str = ""
    params: list[CommandParam] = field(default_factory=list)


class CLIToolManager(ToolManager):
    """
    A custom ToolManager for CLI commands that creates MCP tools from CLI commands.

    This approach provides better type information and parameter handling than the default tool manager.
    """

    def __init__(self, cli_command: str, commands: dict[str, CliCommand]):
        """
        Initialize the CLIToolManager.

        :param cli_command: The CLI command to wrap (e.g., "tasks")
        :param commands: A dictionary mapping command names to CliCommand objects
        """
        super().__init__(warn_on_duplicate_tools=False)
        self.cli_command = cli_command
        self.commands = commands
        self._register_cli_tools()

    def _register_cli_tools(self):
        """
        Register all CLI commands as MCP tools.
        """
        for cmd_name, cmd in self.commands.items():
            self._register_cli_tool(cmd_name, cmd)

    def _register_cli_tool(self, cmd_name: str, cmd: CliCommand) -> MCPTool:
        """
        Register a CLI command as an MCP tool.

        :param cmd_name: The name of the command
        :param cmd: The CliCommand object
        :return: The created MCPTool object
        """

        # Create a wrapper function that executes the CLI command
        async def wrapper(**kwargs):
            try:
                # Build the command arguments
                cmd_args = [self.cli_command, cmd_name]

                # Add positional arguments in the correct order
                positional_params = [p for p in cmd.params if p.is_positional]
                for param in positional_params:
                    if param.name in kwargs:
                        cmd_args.append(str(kwargs[param.name]))

                # Add optional arguments
                optional_params = [p for p in cmd.params if not p.is_positional]
                for param in optional_params:
                    if param.name in kwargs and kwargs[param.name] is not None:
                        value = kwargs[param.name]
                        if isinstance(value, bool):
                            if value:
                                cmd_args.append(f"--{param.name}")
                        else:
                            cmd_args.append(f"--{param.name}")
                            # Handle arguments with spaces by quoting them
                            if isinstance(value, str) and " " in value:
                                cmd_args.append(shlex.quote(str(value)))
                            else:
                                cmd_args.append(str(value))

                # Run the command
                try:
                    # Log the command being executed for debugging
                    cmd_str = " ".join(cmd_args)
                    logger.debug(f"Executing: {cmd_str}")

                    result = subprocess.run(
                        cmd_args, capture_output=True, text=True, check=True
                    )
                    return result.stdout
                except subprocess.CalledProcessError as e:
                    error_msg = f"Error running command {' '.join(cmd_args)}: {e}"
                    logger.error(error_msg)
                    # Return both stdout and stderr for better error reporting
                    output = e.stdout if e.stdout else ""
                    if e.stderr:
                        output += f"\nError output:\n{e.stderr}"
                    return f"{output}\n\nCommand failed with exit code {e.returncode}"
            except Exception as e:
                return f"Error executing command: {str(e)}"

        # Set the wrapper's name and docstring
        wrapper.__name__ = f"{cmd_name}_command"
        wrapper.__doc__ = cmd.help_text

        # Create parameter info for the wrapper function
        parameters = {}
        required_params = []

        # Create field definitions for the argument model
        field_definitions = {}

        for param in cmd.params:
            # All CLI parameters are strings

            # Create parameter info for MCP
            parameters[param.name] = {
                "type": "string",  # All CLI parameters are strings
                "description": param.help_text or "",
            }

            # Add to required params if it's a positional argument
            if param.is_required:
                required_params.append(param.name)

            # Create field definition for pydantic model
            field_info = {}
            if param.help_text:
                field_info["description"] = param.help_text
            if not param.is_required:
                field_info["default"] = None

            field_definitions[param.name] = (str, Field(**field_info))

        # Create the argument model
        arg_model = create_model(
            f"{cmd_name}Arguments",
            **field_definitions,
            __base__=ArgModelBase,
        )

        # Create FuncMetadata with our custom arg_model
        custom_metadata = FuncMetadata(arg_model=arg_model)

        # Create and register the tool
        tool = MCPTool(
            fn=wrapper,
            name=cmd_name,
            title=cmd_name,
            description=cmd.help_text,
            parameters={
                "type": "object",
                "properties": parameters,
                "required": required_params,
            },
            fn_metadata=custom_metadata,
            is_async=True,
            context_kwarg=None,
            annotations=None,
        )

        self._tools[cmd_name] = tool
        return tool


class CLIMCPServer:
    """
    MCP server that wraps a CLI command.
    """

    def __init__(self, cli_command: str, server_name: str | None = None):
        """
        Initialize the CLI MCP server.

        :param cli_command: The CLI command to wrap (e.g., "tasks")
        :param server_name: Optional name for the MCP server
        """
        self.cli_command = cli_command
        self.server_name = server_name or f"{cli_command.capitalize()} MCP Server"
        self.mcp = FastMCP(self.server_name)
        self.commands: dict[str, CliCommand] = {}

        # Discover commands and their parameters
        self._discover_commands()

        # Create a custom tool manager and replace the default one
        self.tool_manager = CLIToolManager(
            cli_command=self.cli_command, commands=self.commands
        )
        self.mcp._tool_manager = self.tool_manager

        # Register resources
        self._register_resources()

    def _discover_commands(self) -> None:
        """
        Discover all commands available in the CLI.
        """
        # Run the CLI command with --help to get the list of commands
        help_output = self._run_command([self.cli_command, "--help"])

        # Parse the help output to extract commands
        commands = self._parse_main_help(help_output)

        # For each command, get its parameters
        for cmd_name in commands:
            cmd_help = self._run_command([self.cli_command, cmd_name, "--help"])
            cmd_params = self._parse_command_help(cmd_help)
            self.commands[cmd_name] = CliCommand(
                name=cmd_name, help_text=commands[cmd_name], params=cmd_params
            )

    def _parse_main_help(self, help_text: str) -> dict[str, str]:
        """
        Parse the main help output to extract commands and their descriptions.

        This method makes the following assumptions about the help format:

        1. Primary format: Commands are listed in curly braces like {cmd1,cmd2,cmd3}
           followed by individual descriptions on separate lines.
        2. Alternative format: Commands are listed as indented items, with the command
           name followed by its description on the same line.
        3. Fallback format: Commands are listed as non-indented items at the beginning
           of lines, followed by descriptions.

        The parser tries these formats in order and uses the first one that works.
        It filters out lines that look like options (starting with '-') or section
        headers (like 'usage:', 'options:', etc.).

        :param help_text: The help text from running the CLI command with --help
        :return: A dictionary mapping command names to their descriptions
        """
        commands = {}

        # First try to find commands section with curly braces (common format)
        commands_section_match = re.search(r"\{([^}]+)\}", help_text)

        if commands_section_match:
            # Extract the command names
            command_names = commands_section_match.group(1).split(",")
            command_names = [cmd.strip() for cmd in command_names]

            # Extract descriptions for each command
            for cmd in command_names:
                # Look for a line that starts with the command name followed by whitespace
                cmd_desc_match = re.search(rf"\s+{re.escape(cmd)}\s+(.*)", help_text)
                description = cmd_desc_match.group(1).strip() if cmd_desc_match else ""
                commands[cmd] = description
        else:
            # Alternative approach: look for indented command listings
            # This pattern looks for lines that start with whitespace followed by a word
            # that's not preceded by a dash (to exclude options)
            cmd_lines = re.findall(r"^\s+(?!-+)(\S+)\s+(.*?)$", help_text, re.MULTILINE)
            for cmd_name, description in cmd_lines:
                # Skip if it looks like an option or not a command
                if cmd_name.startswith("-") or cmd_name in ["usage:", "options:"]:
                    continue
                commands[cmd_name] = description.strip()

        # If we still don't have commands, try another approach for subcommand-style CLIs
        if not commands:
            # Look for lines that might be commands (non-option words followed by description)
            possible_commands = re.findall(r"^(\S+)\s+(.*?)$", help_text, re.MULTILINE)
            for cmd_name, description in possible_commands:
                # Skip if it looks like a section header or not a command
                if cmd_name.lower() in [
                    "usage:",
                    "options:",
                    "commands:",
                    "positional",
                    "arguments:",
                ]:
                    continue
                # Skip if it starts with a dash (option)
                if cmd_name.startswith("-"):
                    continue
                commands[cmd_name] = description.strip()

        return commands

    def _parse_command_help(self, help_text: str) -> list[CommandParam]:
        """
        Parse the command help output to extract parameters.

        This method makes the following assumptions about the help format:

        1. Parameters are divided into two sections: "positional arguments" and "options"
        2. Positional arguments are listed with their name followed by a description
        3. Optional arguments (options) start with one or more dashes (e.g., -h, --help)
        4. Long-form options (--name) are preferred over short-form options (-n)
        5. Help text for a parameter may span multiple lines, with continuation lines indented
        6. Positional arguments are considered required, while options are considered optional
        7. The help flag (-h, --help) is filtered out as it's handled automatically

        The parser handles both standard argparse-style help output and similar formats.
        It extracts parameter names, descriptions, and whether they are positional or optional.

        :param help_text: The help text from running the CLI command with <command> --help
        :return: A list of CommandParam objects
        """
        params = []

        # Extract positional arguments
        positional_section = re.search(
            r"positional arguments:(.*?)(?:\n\n|\n[^\s])", help_text, re.DOTALL
        )
        if positional_section:
            positional_text = positional_section.group(1).strip()
            for line in positional_text.split("\n"):
                line = line.strip()
                if not line or line.startswith("-"):
                    continue

                # Extract parameter name and help text
                param_match = re.match(r"\s*(\S+)\s+(.*)", line)
                if param_match:
                    name, help_text = param_match.groups()
                    params.append(
                        CommandParam(
                            name=name,
                            help_text=help_text,
                            is_positional=True,
                            is_required=True,  # Assume positional args are required
                        )
                    )

        # Extract optional arguments
        options_section = re.search(
            r"options:(.*?)(?:\n\n|\n[^\s]|$)", help_text, re.DOTALL
        )
        if options_section:
            options_text = options_section.group(1).strip()
            current_param = None

            for line in options_text.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Check if this line defines a new parameter
                param_match = re.match(r"(-[^,\s]+(?:,\s*-[^,\s]+)*)\s+(.*)", line)
                if param_match:
                    # Extract parameter flags and help text
                    flags, help_text = param_match.groups()

                    # Get the parameter name (without the dashes)
                    # Prefer long form (--name) over short form (-n)
                    flag_parts = [f.strip() for f in flags.split(",")]
                    long_flags = [f for f in flag_parts if f.startswith("--")]
                    short_flags = [
                        f
                        for f in flag_parts
                        if f.startswith("-") and not f.startswith("--")
                    ]

                    if long_flags:
                        name = long_flags[0][2:]  # Remove '--'
                    elif short_flags:
                        name = short_flags[0][1:]  # Remove '-'
                    else:
                        name = flags.strip("-")

                    # Check if this is a help flag
                    if name in ["h", "help"]:
                        continue

                    # Create the parameter
                    current_param = CommandParam(
                        name=name,
                        help_text=help_text,
                        is_positional=False,
                        is_required=False,  # Assume optional args are not required
                    )
                    params.append(current_param)
                elif current_param:
                    # This line continues the help text for the current parameter
                    current_param.help_text += " " + line

        return params

    def _run_command(self, cmd_args: list[str]) -> str:
        """
        Run a command and return its output.

        :param cmd_args: The command arguments to run
        :return: The command output as a string
        """
        try:
            # Log the command being executed for debugging
            cmd_str = " ".join(cmd_args)
            logger.debug(f"Executing: {cmd_str}")

            result = subprocess.run(
                cmd_args, capture_output=True, text=True, check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = f"Error running command {' '.join(cmd_args)}: {e}"
            logger.error(error_msg)
            # Return both stdout and stderr for better error reporting
            output = e.stdout if e.stdout else ""
            if e.stderr:
                output += f"\nError output:\n{e.stderr}"
            return f"{output}\n\nCommand failed with exit code {e.returncode}"

    def _register_resources(self) -> None:
        """
        Register MCP resources.
        """

        # Register a resource for listing all available commands
        @self.mcp.resource(f"{self.cli_command}://commands")
        def get_commands() -> str:
            """
            Get a list of all available commands.

            :return: JSON string containing all available commands and their details
            """
            commands_list = [
                {
                    "name": cmd.name,
                    "description": cmd.help_text,
                    "parameters": [
                        {
                            "name": param.name,
                            "description": param.help_text,
                            "is_positional": param.is_positional,
                            "is_required": param.is_required,
                            "default": param.default,
                            "choices": param.choices,
                        }
                        for param in cmd.params
                    ],
                }
                for cmd in self.commands.values()
            ]
            return json.dumps(commands_list, indent=2)

        # Register a resource for getting help on a specific command
        @self.mcp.resource(f"{self.cli_command}://help/{{command_name}}")
        def get_command_help(command_name: str) -> str:
            """
            Get help for a specific command.

            :param command_name: Name of the command to get help for
            :return: JSON string containing command details and parameters
            """
            if command_name not in self.commands:
                return json.dumps(
                    {"error": f"Command '{command_name}' not found"}, indent=2
                )

            cmd = self.commands[command_name]
            command_info = {
                "name": cmd.name,
                "description": cmd.help_text,
                "parameters": [
                    {
                        "name": param.name,
                        "description": param.help_text,
                        "is_positional": param.is_positional,
                        "is_required": param.is_required,
                        "default": param.default,
                        "choices": param.choices,
                    }
                    for param in cmd.params
                ],
            }
            return json.dumps(command_info, indent=2)

        # Register a resource for getting general help
        @self.mcp.resource(f"help://{self.cli_command}")
        def get_help() -> str:
            """
            Get help on using the CLI MCP server.

            :return: Help text describing available commands and resources
            """
            help_text = f"""
{self.server_name}

This server provides MCP tools that wrap the '{self.cli_command}' CLI command.

Available commands:
"""
            for cmd_name, cmd in self.commands.items():
                help_text += f"- {cmd_name}: {cmd.help_text}\n"

            help_text += f"""
For more information on a specific command, use the resource:
{self.cli_command}://help/{{command_name}}

To see all commands with their parameters, use the resource:
{self.cli_command}://commands
"""
            return help_text

    def run(self) -> None:
        """
        Run the MCP server.
        """
        self.mcp.run()


if __name__ == "__main__":
    import sys

    # Use command line argument as CLI command if provided, otherwise default to "tasks"
    cli_command = sys.argv[1] if len(sys.argv) > 1 else "tasks"
    server_name = f"{cli_command.capitalize()} MCP Server"

    logger.info(f"Starting MCP server for CLI command: {cli_command}")
    server = CLIMCPServer(cli_command, server_name)
    server.run()
