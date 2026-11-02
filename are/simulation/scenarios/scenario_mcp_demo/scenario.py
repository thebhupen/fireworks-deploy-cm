# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import datetime
import os
from pathlib import Path

from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.apps.mcp.mcp_app import MCPApp
from are.simulation.apps.sandbox_file_system import SandboxLocalFileSystem
from are.simulation.scenarios.scenario import Scenario
from are.simulation.scenarios.utils.registry import register_scenario
from are.simulation.types import CapabilityTag


@register_scenario("scenario_mcp_demo")
class ScenarioMCPDemo(Scenario):
    """
    A demo scenario that showcases various utility tools.

    This scenario demonstrates how to use different math, text, and utility tools
    to perform various tasks.
    """

    start_time: float | None = datetime.datetime.now().timestamp()
    tags: tuple[CapabilityTag, ...] = (CapabilityTag.Exploration,)

    def init_and_populate_apps(self, *_, **kwargs) -> None:
        """
        Initialize and populate the apps used in this scenario.
        """
        # Create the standard apps
        agent_user_interface = AgentUserInterface()
        fs = SandboxLocalFileSystem(sandbox_dir=kwargs.get("sandbox_dir", None))

        # Create apps for different tool categories
        script_dir = Path(__file__).parent

        def desc(name, description):
            if name == "divide":
                return f"{description} (note: this tool does not work with negative numbers)."
            return description

        # Math tools app
        math_server = script_dir / "math_server.py"
        math_app = MCPApp(
            name="MathTools",
            server_command="python",
            server_args=[str(math_server)],
            description_modifier=desc,
        )

        # Text tools app
        text_server = script_dir / "text_server.py"
        text_app = MCPApp(
            name="TextTools",
            server_command="python",
            server_args=[str(text_server)],
        )

        # Utility tools app
        utility_server = script_dir / "utility_server.py"
        utility_app = MCPApp(
            name="UtilityTools",
            server_command="python",
            server_args=[str(utility_server)],
        )

        # Todo tracking app - with read-only option for demonstration
        todo_server = script_dir / "todo_server.py"
        todo_app = MCPApp(
            name="TodoApp",
            server_command="python",
            server_args=[str(todo_server)],
        )

        # Read-only version of the todo app (only exposes list_todos)
        todo_readonly_app = MCPApp(
            name="TodoReadOnly",
            server_command="python",
            server_args=[str(todo_server)],
            only_read_only=True,  # Only expose read-only tools
        )

        # Only create code_app if MCP_SERVER_URL environment variable is set
        code_app = None
        code_app_url = os.environ.get("MCP_SERVER_URL", None)
        if code_app_url:
            code_app = MCPApp(
                name="RunPythonCode",
                server_url=code_app_url,
            )

        # Create a README file explaining the scenario
        with fs.open("README.txt", "w") as file:
            file.write(
                """
Tools Demo Scenario
================

This scenario demonstrates various tools organized into separate servers, each focusing on a specific category.

Available Tool Categories:

1. Math Tools (MathTools):
   - add, subtract, multiply, divide, square_root
   - All tools are read-only and operate in a closed mathematical domain

2. Text Tools (TextTools):
   - reverse_text, count_words, to_uppercase, to_lowercase
   - All tools are read-only and operate on text input

3. Utility Tools (UtilityTools):
   - get_current_time, generate_random_number, format_json
   - Includes both read-only tools and tools that modify their input

4. Todo Tracking Tools (TodoApp):
   - add_todo: Create new todo items
   - list_todos: View existing todo items
   - complete_todo: Mark todo items as completed
   - delete_todo: Remove todo items from the list
   - Demonstrates tools with different annotation properties (read-only, destructive, idempotent)

5. Read-Only Todo Tools (TodoReadOnly):
   - A filtered version of the Todo app that only exposes read-only tools (list_todos)
   - Demonstrates the only_read_only filter feature


Example questions:

- What is the sum of 5 and 10?
- Format the sample.json file
- How many days between next Friday and the 10th of December 2030?
- What's the 140th Fibonacci number?
- Create a todo list with 3 items and mark one as completed
- Show me the difference between TodoApp and TodoReadOnly

Tool Annotations:
Each tool includes annotations that describe its behavior:
- readOnlyHint: Whether the tool modifies its environment
- destructiveHint: Whether modifications are destructive or additive
- idempotentHint: Whether repeated calls with the same arguments have the same effect
- openWorldHint: Whether the tool interacts with external entities

To run the demo, you need to run the python code mcp server script, do not use the npx script, the deno one works:
```
deno run \
  -N -R=node_modules -W=node_modules --node-modules-dir=auto \
  jsr:@pydantic/mcp-run-python sse
```

Have fun exploring these tools!
"""
            )

        # Create a sample JSON file for the format_json tool
        with fs.open("sample.json", "w") as file:
            file.write(
                '{"name":"John","age":30,"city":"New York","skills":["python","javascript","html"],"address":{"street":"123 Main St","zip":"10001"}}'
            )

        # Create a sample text file for the text tools
        with fs.open("sample.txt", "w") as file:
            file.write(
                "The quick brown fox jumps over the lazy dog. This is a sample text file for demonstrating text manipulation tools."
            )

        # Register all apps with the scenario
        self.apps = [
            agent_user_interface,
            fs,
            math_app,
            text_app,
            utility_app,
            todo_app,
            todo_readonly_app,
        ]

        if code_app:
            self.apps.append(code_app)
