# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


# Copied from https://github.com/huggingface/transformers/blob/v4.47.0/src/transformers/agents/agents.py

from functools import lru_cache

from packaging import version

from are.simulation.tools import Tool

DEFAULT_TOOL_DESCRIPTION_TEMPLATE = """
- {{ tool.name }}: {{ tool.description }}
    Takes inputs: {{tool.inputs}}
    Returns an output of type: {{tool.output_type}}
"""


def get_tool_description_with_args(
    tool: Tool, description_template: str = DEFAULT_TOOL_DESCRIPTION_TEMPLATE
) -> str:
    compiled_template = compile_jinja_template(description_template)
    rendered = compiled_template.render(
        tool=tool,
    )
    return rendered


@lru_cache
def compile_jinja_template(template):
    try:
        import jinja2
        from jinja2.exceptions import TemplateError
        from jinja2.sandbox import ImmutableSandboxedEnvironment
    except ImportError:
        raise ImportError("template requires jinja2 to be installed.")

    if version.parse(jinja2.__version__) < version.parse("3.1.0"):
        raise ImportError(
            "template requires jinja2>=3.1.0 to be installed. Your version is "
            f"{jinja2.__version__}."
        )

    def raise_exception(message):
        raise TemplateError(message)

    jinja_env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True)
    jinja_env.globals["raise_exception"] = raise_exception
    return jinja_env.from_string(template)


class Toolbox:
    """
    The toolbox contains all tools that the agent can perform operations with, as well as a few methods to
    manage them.

    Args:
        tools (`list[Tool]`):
            The list of tools to instantiate the toolbox with
    """

    def __init__(self, tools: list[Tool]):
        self._tools = {tool.name: tool for tool in tools}

    @property
    def tools(self) -> dict[str, Tool]:
        """Get all tools currently in the toolbox"""
        return self._tools

    def show_tool_descriptions(
        self, tool_description_template: str = DEFAULT_TOOL_DESCRIPTION_TEMPLATE
    ) -> str:
        """
        Returns the description of all tools in the toolbox

        Args:
            tool_description_template (`str`, *optional*):
                The template to use to describe the tools. If not provided, the default template will be used.
        """
        return "\n".join(
            [
                get_tool_description_with_args(tool, tool_description_template)
                for tool in self._tools.values()
            ]
        )

    def add_tool(self, tool: Tool):
        """
        Adds a tool to the toolbox

        Args:
            tool (`Tool`):
                The tool to add to the toolbox.
        """
        if tool.name in self._tools:
            raise KeyError(f"Error: tool '{tool.name}' already exists in the toolbox.")
        self._tools[tool.name] = tool

    def remove_tool(self, tool_name: str):
        """
        Removes a tool from the toolbox

        Args:
            tool_name (`str`):
                The tool to remove from the toolbox.
        """
        if tool_name not in self._tools:
            raise KeyError(
                f"Error: tool {tool_name} not found in toolbox for removal, should be instead one of {list(self._tools.keys())}."
            )
        del self._tools[tool_name]

    def update_tool(self, tool: Tool):
        """
        Updates a tool in the toolbox according to its name.

        Args:
            tool (`Tool`):
                The tool to update to the toolbox.
        """
        if tool.name not in self._tools:
            raise KeyError(
                f"Error: tool {tool.name} not found in toolbox for update, should be instead one of {list(self._tools.keys())}."
            )
        self._tools[tool.name] = tool

    def clear_toolbox(self):
        """Clears the toolbox"""
        self._tools = {}

    def __repr__(self):
        toolbox_description = "Toolbox contents:\n"
        for tool in self._tools.values():
            toolbox_description += f"\t{tool.name}: {tool.description}\n"
        return toolbox_description
