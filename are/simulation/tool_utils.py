# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import ast
import inspect
import logging
import re
from dataclasses import asdict, dataclass
from enum import Enum
from random import Random
from types import NoneType, UnionType
from typing import Any, Callable, Union, get_args, get_origin, get_type_hints

import docstring_parser
from termcolor import colored

from are.simulation.tools import Tool
from are.simulation.utils import check_type

# Constants
APPTOOL_ATTR_NAME = "_are_simulation_app_tool"

logger = logging.getLogger(__name__)


def adapt_type(t: str):
    if t == "int":
        return "integer"
    elif t == "float":
        return "number"
    return t


@dataclass
class AppToolArg:
    name: str
    arg_type: str
    description: str | None
    has_default: bool = False
    default: Any | None = None
    example_value: Any | None = None
    type_obj: Any | None = None  # Store the actual type object

    def __str__(self):
        descr = f"name: {self.name}, type: {adapt_type(str(self.arg_type))}, description: {self.description}"
        if self.has_default:
            descr += f", default: {self.default}"
        return descr


@dataclass
class AppTool:
    class_name: str
    app_name: str
    name: str
    function_description: str | None
    args: list[AppToolArg]
    return_type: Any | None = None
    return_description: str | None = None
    function: Callable | None = None
    class_instance: Any | None = None
    write_operation: bool | None = None
    # Public name and description for the tool given to the agent
    _public_name: str | None = None
    _public_description: str | None = None
    # Augmentation for the agent, not visible to the user, nor the environment:
    # We can augment tool call behavior to fail randomly with a given probability
    # This is to test how robust are Agents to these types of Random failures
    failure_probability: float | None = None
    failure_message_template: str = (
        "Calling {name} failed with error: Internal error - Retry again later"
    )
    seed: int | None = None
    rng: Random | None = None

    def __post_init__(self):
        assert (
            self.failure_probability is None or 0.0 <= self.failure_probability <= 1.0
        ), (
            f"failure_probability must be between 0.0 and 1.0, got {self.failure_probability}"
        )

        assert "{name}" in self.failure_message_template, (
            f"failure_message_template must contain placeholder {{name}}, it will be replaced by the actual call: {self.failure_message_template}"
        )

        if self.failure_probability is not None:
            self.rng = Random(self.seed)

        # Annotate the function with this tool instance if it exists
        if self.function is not None:
            # First check if the function has a set_apptool method (from event_registered)
            # This handles the case where @event_registered is applied before @app_tool
            if hasattr(self.function, "set_apptool") and callable(
                self.function.set_apptool  # type: ignore
            ):
                try:
                    # Use the set_apptool function to set the AppTool on both the wrapper and original function
                    self.function.set_apptool(self)  # type: ignore
                except (AttributeError, TypeError):
                    pass
            else:
                # Handle both functions and bound methods differently
                if hasattr(self.function, "__self__"):  # It's a bound method
                    # Set the attribute on the bound method itself
                    setattr(self.function.__func__, APPTOOL_ATTR_NAME, self)  # type: ignore
                else:  # It's a regular function
                    setattr(self.function, APPTOOL_ATTR_NAME, self)

        if self._public_name is None:
            self._public_name = self.name
        if self._public_description is None:
            self._public_description = self.function_description

    @property
    def arg_descriptions(self) -> str:
        return "\n\t- ".join([str(arg) for arg in self.args])

    @property
    def func_name(self):
        return self.function.__name__ if self.function else None

    @staticmethod
    def get_tool_for_function(func: Callable) -> "AppTool | None":
        """
        Get the AppTool instance associated with a function.
        """
        # First, check if the tool is directly attached to the function
        apptool = getattr(func, APPTOOL_ATTR_NAME, None)
        if apptool is not None:
            return apptool

        if hasattr(func, "__self__"):  # It's a bound method
            func_attr = getattr(func, "__func__", None)
            if func_attr is not None:
                apptool = getattr(func_attr, APPTOOL_ATTR_NAME, None)

        return None

    def __call__(self, *args, **kwargs):
        if self.function is not None:
            logger.debug(colored(f"Calling {self.name}"))

        if self.failure_probability is not None:
            if self.rng is None:
                self.rng = Random(self.seed)
            if self.rng.random() < self.failure_probability:
                raise Exception(self.failure_message_template.format(name=self.name))

        if self.function is not None:
            if self.class_instance is not None:
                result = self.function(self.class_instance, *args, **kwargs)
            else:
                result = self.function(*args, **kwargs)
        else:
            raise Exception("Cannot call AppTool without a function")

        if (
            hasattr(self.function, "llm_formatter")
            and self.function.llm_formatter is not None  # type: ignore
        ):
            result = self.function.llm_formatter(result)  # type: ignore

        result_str = str(result)
        if len(result_str) > 200:
            result_str = result_str[:200] + "..."

        logger.debug(colored(f"Calling {self.name} - Result:\n{result_str}", "green"))
        return result

    def to_metadata_dict(self):
        """
        Returns a dictionary representation of the tool's metadata.
        This is used for serialization and UI display.
        """
        return {
            "name": self.name,
            "description": self.function_description,
            "args": [
                {
                    **asdict(arg),
                    "type": arg.arg_type,  # Rename arg_type to type for frontend compatibility
                }
                for arg in self.args
            ],
            "return_type": self.return_type,
            "return_description": self.return_description,
            "write_operation": (
                self.write_operation if self.write_operation is not None else False
            ),
            "role": getattr(self, "role", ""),
        }

    def to_open_ai(self):
        """
        Convert the tool to OpenAI function calling format.

        Example::

            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"]
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        """
        d = {}
        d["type"] = "function"
        d["function"] = {
            "name": self._public_name,
            "description": self._public_description,
            "parameters": {
                "type": "object",
                "properties": {},
            },
        }
        for arg in self.args:
            d["function"]["parameters"]["properties"][arg.name] = {
                "type": adapt_type(arg.arg_type),
                "description": arg.description,
            }
        d["function"]["parameters"]["required"] = [arg.name for arg in self.args]
        return d


class OperationType(Enum):
    READ = "read"
    WRITE = "write"


class ToolAttributeName(Enum):
    """Enum for tool attribute names used by decorators and tool registration."""

    APP = "_is_app_tool"
    ENV = "_is_env_tool"
    DATA = "_is_data_tool"
    USER = "_is_user_tool"


def tool_decorator(
    llm_formatter: Callable | None = None,
    attribute_name: ToolAttributeName = ToolAttributeName.APP,
):
    """
    Decorator to register a function as an app tool.

    :param llm_formatter: a function to format the result of the tool before returning it to the LLM Agent,
                         THIS IS ONLY USED WHEN the function is called as a tool (i.e. from AppTool call), not when called as a normal function
    :param attribute_name: the attribute name to set on the function as a ToolAttributeName enum value
    """
    # Get the string value from the enum
    attr_name = attribute_name.value

    def app_tool_decorator(method):
        # Mark the method as an app tool
        setattr(method, attr_name, True)

        method.llm_formatter = llm_formatter  # type: ignore
        return method

    return app_tool_decorator


def app_tool(llm_formatter: Callable | None = None):
    """
    Decorator to register a function as an app tool.

    :param llm_formatter: a function to format the result of the tool before returning it to the LLM Agent
    """
    return tool_decorator(llm_formatter, ToolAttributeName.APP)


def env_tool(llm_formatter: Callable | None = None):
    """
    Decorator to register a function as an environment tool.

    :param llm_formatter: a function to format the result of the tool before returning it to the LLM Agent
    """
    return tool_decorator(llm_formatter, ToolAttributeName.ENV)


def data_tool(llm_formatter: Callable | None = None):
    """
    Decorator to register a function as a data tool.

    :param llm_formatter: a function to format the result of the tool before returning it to the LLM Agent
    """
    return tool_decorator(llm_formatter, ToolAttributeName.DATA)


def user_tool(llm_formatter: Callable | None = None):
    """
    Decorator to register a function as a user tool.

    :param llm_formatter: a function to format the result of the tool before returning it to the LLM Agent
    """
    return tool_decorator(llm_formatter, ToolAttributeName.USER)


def format_type_name(type_obj) -> str:
    """Helper function to format type names."""
    origin = get_origin(type_obj)
    if origin is None:
        if hasattr(type_obj, "__name__"):
            return type_obj.__name__
        else:
            return str(type_obj)
    else:
        args = get_args(type_obj)
        if origin in {Union, UnionType}:
            # Collect types and replace NoneType with None.
            union_args = [arg for arg in args if arg is not NoneType]
            if NoneType in args:
                # Make sure None is always the last element.
                union_args.append(None)
            # Combine all types together via the pipe syntax.
            return " | ".join(format_type_name(arg) for arg in union_args)

        base = origin.__name__ or type_obj._name
        if args:
            args = ", ".join(format_type_name(arg) for arg in type_obj.__args__)
            return f"{base}[{args}]"
        else:
            return base


def build_tool(app, func, failure_probability: float | None = None) -> AppTool:
    # Retrieve function name
    cls = app.__class__
    func_name = func.__name__

    # Retrieve signature and parameters
    sig = inspect.signature(func)
    params = sig.parameters

    docstring = func.__doc__
    parsed_docstring = docstring_parser.parse(docstring)
    if parsed_docstring.returns is not None:
        return_description = parsed_docstring.returns.description
    else:
        return_description = None

    arg_descriptions = {
        param.arg_name: param.description for param in parsed_docstring.params
    }
    type_hints = get_type_hints(func)
    return_type = type_hints.get("return", None)
    if return_type is not None:
        return_type = format_type_name(return_type)  # type: ignore

    example_from_doc = get_example_from_docstring(func)
    if example_from_doc is not None:
        example_values = parse_function_call_example(func, example_from_doc)
    else:
        example_values = {}

    write_operation = None
    if hasattr(func, "__operation_type__"):
        if func.__operation_type__ == OperationType.WRITE:
            write_operation = True
        else:
            write_operation = False

    args_details = []
    for name, param in params.items():
        if name == "self":
            continue
        type_obj = type_hints.get(name, "Any")
        arg_type = format_type_name(type_obj)
        description = arg_descriptions.get(name, None)
        has_default = param.default != param.empty
        default = param.default if param.default != param.empty else None
        args_details.append(
            AppToolArg(
                name=name,
                arg_type=arg_type,
                description=description,
                has_default=has_default,
                default=default,
                example_value=example_values.get(name, None),
                type_obj=type_obj,
            )
        )

    if (
        parsed_docstring.long_description is None
        and parsed_docstring.short_description is None
    ):
        raise Exception(f"Cannot register tool {func_name} without documenting it !")
    else:
        # We need to concatenate the short and long description
        # As otherwise we will not get the full description of the function
        function_description = ""
        if parsed_docstring.short_description is not None:
            function_description += parsed_docstring.short_description
        if parsed_docstring.long_description is not None:
            function_description += "\n" + parsed_docstring.long_description
    details = AppTool(
        class_name=cls.__name__,
        app_name=app.name,
        name=f"{app.name}__{func_name}",
        function_description=function_description,
        args=args_details,
        class_instance=app,
        function=func,
        return_type=return_type,
        return_description=return_description,
        write_operation=write_operation,
        failure_probability=failure_probability,
    )

    return details


inputs = {
    "offset": {
        "description": "The starting point to retrieve emails from, default is 0.",
        "type": "int",
    }
}
output_type = str


def validate_argument_types(func: Callable, args_mapping: dict[str, Any]) -> bool:
    """
    Validate the types of the provided arguments against the function's signature.
    """
    # Get the expected argument types from the function signature
    type_hints = get_type_hints(func)

    # Iterate through the provided arguments and their expected types
    for arg_name, arg_value in args_mapping.items():
        expected_type = type_hints.get(arg_name)
        if expected_type and not check_type(arg_value, expected_type):
            raise TypeError(
                f"Argument '{arg_name}' should be of type {expected_type}, but got {type(arg_value)}."
            )

    return True


def parse_function_call_example(func: Callable, example_str: str) -> dict[str, Any]:
    """
    Parse the function call example and check the argument types.
    """
    # Parse the example string using ast
    tree = ast.parse(example_str.strip(), mode="eval")

    # Ensure we are dealing with a function call
    if not isinstance(tree.body, ast.Call):
        raise ValueError("Input string is not a valid function call.")

    # Get the method name from the example
    func_name = tree.body.func.id  # type: ignore # Function name in the example

    # Ensure the function name matches the provided method
    if func_name != func.__name__:
        raise ValueError(
            f"Function name {func_name} does not match the provided function {func.__name__}."
        )

    # Get function signature to handle argument names
    sig = inspect.signature(func)

    # Create a dictionary to hold argument mappings
    args_mapping = {}

    parameters = list(sig.parameters.keys())
    if parameters[0] == "self":
        parameters = parameters[1:]  # Remove the first parameter (self)

    if len(tree.body.args) > len(parameters):
        raise ValueError(
            f"Too many arguments provided in the example. Expected {len(parameters)} but got {len(tree.body.args)}."
        )

    # Handle positional arguments
    for i, arg in enumerate(tree.body.args):
        param_name = parameters[i]
        args_mapping[param_name] = ast.literal_eval(arg)

    # Handle keyword arguments
    for kw in tree.body.keywords:
        args_mapping[kw.arg] = ast.literal_eval(kw.value)

    # Validate argument types
    validate_argument_types(func, args_mapping)

    return args_mapping


def get_example_from_docstring(func: Callable) -> str | None:
    """
    Extract examples from a docstring.
    """
    # Extract the function name
    func_name = func.__name__

    # Get the docstring from the function
    docstring = func.__doc__

    if docstring is None:
        return None

    # Define the regex pattern to match the function name followed by parentheses
    pattern = re.compile(rf"{func_name}\(.*?\)", re.DOTALL)

    # Search the docstring for the example
    match = pattern.search(docstring)

    if match:
        return match.group(0)  # Return the matched example string
    else:
        return None


python_to_hf_type = {
    "int": "integer",
    "float": "number",
    "str": "string",
    "bool": "boolean",
}


class AppToolAdapter(Tool):
    def __init__(self, app_tool: AppTool):
        self.name = app_tool._public_name  # type: ignore
        self.description = (
            app_tool._public_description if app_tool._public_description else ""
        )
        self.description = f"Acts on app {app_tool.app_name}: {self.description}"
        self.inputs = {}

        # Handle return type and extract actual type name
        self.actual_return_type = None
        if app_tool.return_type is not None:
            return_type_str = str(app_tool.return_type)
            if return_type_str in python_to_hf_type:
                self.output_type = python_to_hf_type[return_type_str]  # type: ignore
            else:
                self.output_type = "any"  # type: ignore
                # Extract the actual type name for custom types
                if hasattr(app_tool.return_type, "__name__"):
                    self.actual_return_type = app_tool.return_type.__name__
                elif hasattr(app_tool.return_type, "_name"):
                    self.actual_return_type = app_tool.return_type._name
                else:
                    self.actual_return_type = return_type_str
        else:
            self.output_type = "any"  # type: ignore
            self.actual_return_type = "None"

        for arg in app_tool.args:
            self.inputs[arg.name] = {  # type: ignore
                "description": arg.description,
                "type": python_to_hf_type.get(str(arg.arg_type), "any"),
            }
            if arg.has_default:
                self.inputs[arg.name]["default"] = arg.default  # type: ignore

        # Enhance description with actual return type info for custom types
        if self.actual_return_type:
            self.description += f" Returns: {self.actual_return_type}"
        self.app_tool = app_tool
        super().__init__()

    def forward(self, *args, **kwargs):
        return self.app_tool(*args, **kwargs)
