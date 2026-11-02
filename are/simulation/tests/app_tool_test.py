# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import inspect
from dataclasses import is_dataclass
from types import NoneType, UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

import docstring_parser
import pytest

from are.simulation.apps import ALL_APPS
from are.simulation.apps.app import App, ToolType
from are.simulation.apps.cab import event_registered
from are.simulation.environment import Environment
from are.simulation.tool_utils import (
    AppToolArg,
    ToolAttributeName,
    app_tool,
    build_tool,
    get_example_from_docstring,
    parse_function_call_example,
)


def is_list_of_dataclass(type_hint):
    return get_origin(type_hint) is list and is_dataclass(get_args(type_hint)[0])


def is_dict_of_dataclass(type_hint):
    if get_origin(type_hint) is dict:
        args = get_args(type_hint)
        return (
            len(args) == 2
            and (args[0] is str or args[0] is Any)
            and is_dataclass(args[1])
        )
    return False


# typeddicts are really just dicts, so we are good with them
def is_typeddict(type_hint):
    """Check if a type is a TypedDict."""
    return hasattr(type_hint, "__mro__") and dict in type_hint.__mro__


def is_optional_of_any(some_type, types_list) -> bool:
    # Check if the type is a Union and if NoneType is part of it.
    if get_origin(some_type) in {Union, UnionType}:
        args = get_args(some_type)
        # Check if NoneType is in args
        # and if some of the types from types_list are also in args.
        return NoneType in args and any(t in args for t in types_list)
    return False


def is_union_of_any(some_type, type_list) -> bool:
    if get_origin(some_type) in {Union, UnionType}:
        args = get_args(some_type)
        return all(t in type_list for t in args)
    return False


def is_valid_app_tool_param_type(some_type):
    primitive_types = (int, str, float, bool)

    if some_type in primitive_types:
        return True

    origin = get_origin(some_type)

    if origin in {Union, UnionType}:
        args = get_args(some_type)
        return all(is_valid_app_tool_param_type(t) for t in args if t is not NoneType)

    # list and dict without args return None for get_origin and therefore require special handling.
    # See https://github.com/python/cpython/issues/95539 for more details.
    if origin is list or (some_type is list and origin is None):
        return all(
            is_valid_app_tool_param_type(item_type) for item_type in get_args(some_type)
        )

    if origin is dict or (some_type is dict and origin is None):
        if origin is None:
            return True

        key_type, value_type = get_args(some_type)

        # Specific case to allow dict[str, Any] for kwargs
        if key_type is str and value_type is Any:
            return True

        return is_valid_app_tool_param_type(key_type) and is_valid_app_tool_param_type(
            value_type
        )

    return False


ALLOWED_APP_TOOL_RETURN_TYPE = [
    type(None),
    dict,
    str,
    int,
    float,
    bool,
    bytes,
    list[Any],
    list[str],
    dict[Any, Any],
]


def get_app_tool_methods(app_instance, attribute_name="_is_app_tool"):
    methods = []
    for method_name, method in app_instance.__class__.__dict__.items():
        if callable(method) and getattr(method, attribute_name, False):
            methods.append(method)
    return methods


@pytest.mark.parametrize(
    "app_class",
    ALL_APPS,
)
@pytest.mark.parametrize(
    "attribute_name",
    ["_is_app_tool", "_is_env_tool", "_is_user_tool", "_is_data_tool"],
)
def test_app_tool_return_types(app_class, attribute_name):
    env = Environment()
    app_instance = app_class()
    env.register_apps([app_instance])
    app_tool_methods = get_app_tool_methods(app_instance, attribute_name)
    for method in app_tool_methods:
        return_type = get_type_hints(method).get("return")
        assert (
            return_type is None
            or return_type in ALLOWED_APP_TOOL_RETURN_TYPE
            or is_dataclass(return_type)
            or is_list_of_dataclass(return_type)
            or is_dict_of_dataclass(return_type)
            or get_origin(return_type) in [dict, list]
            or is_optional_of_any(return_type, ALLOWED_APP_TOOL_RETURN_TYPE)
            or is_union_of_any(return_type, ALLOWED_APP_TOOL_RETURN_TYPE)
            or is_typeddict(return_type)
        ), (
            f"Return type {return_type} is not allowed for {method.__name__} in {app_class.__name__}"
        )


@pytest.mark.parametrize(
    "app_class",
    ALL_APPS,
)
@pytest.mark.parametrize(
    "attribute_name",
    ["_is_app_tool", "_is_env_tool", "_is_user_tool", "_is_data_tool"],
)
def test_app_tool_methods(app_class, attribute_name):
    env = Environment()
    app_instance = app_class()
    env.register_apps([app_instance])
    app_tool_methods = get_app_tool_methods(app_instance, attribute_name)

    errors = []
    warnings = []

    for method in app_tool_methods:
        signature = inspect.signature(method)
        type_hints = get_type_hints(method)

        docstring = method.__doc__
        parsed_docstring = docstring_parser.parse(docstring)

        arg_descriptions = {
            param.arg_name: param.description for param in parsed_docstring.params
        }

        for param in signature.parameters.values():
            param_name = param.name
            if param_name == "self":
                continue

            param_type = type_hints.get(param_name, None)
            if param_type is None:
                errors.append(
                    f"parameter '{param_name}' in function '{method.__name__}' has no type"
                )
            elif not is_valid_app_tool_param_type(param_type):
                errors.append(
                    f"parameter '{param_name}' in function '{method.__name__}' has invalid type {param_type}, args: {get_args(param_type)}, origin: {get_origin(param_type)}"
                )

            description = arg_descriptions.get(param_name, None)
            if description is None:
                errors.append(
                    f"parameter '{param_name}' in function '{method.__name__}' has no description"
                )

        # Check for descriptions of non-existent parameters
        described_params = set(arg_descriptions.keys())
        non_existent_params = described_params - signature.parameters.keys()
        for param in non_existent_params:
            errors.append(
                f"docstring describes non-existent parameter '{param}' in function '{method.__name__}'"
            )

        # Check return description if return type is not None
        return_type = type_hints.get("return", None)
        if return_type is not None and return_type is not type(None):
            return_description = (
                parsed_docstring.returns.description
                if parsed_docstring.returns
                else None
            )
            if not return_description:
                errors.append(
                    f"function '{method.__name__}' in '{app_class.__name__}' has no return description"
                )

        # Check that examples if included are correct
        example_call = get_example_from_docstring(method)
        if example_call is not None:
            try:
                _ = parse_function_call_example(method, example_call)
            except Exception as e:
                errors.append(
                    f"Error parsing example call '{example_call}' for function '{method.__name__}': {e}"
                )
                continue
        else:
            warnings.append(
                f"function '{method.__name__}' in '{app_class.__name__}' has no example call"
            )

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    assert not errors, "Type errors found: " + ", ".join(errors)


def test_build_tool():
    class TestApp(App):
        def __init__(self):
            self.name = "SomeApp"

        @app_tool()
        @event_registered()
        def test_func_1(self, arg1: str, arg2: int, arg3: float | None = 33.3) -> str:
            """
            Test func description
            :param arg1: important parameter
            :param arg2: less important parameter
            :param arg3: non important parameter
            :returns: constant string "test_func_1"

            :example:
                test_func_1("test1", 123, 33.3)
            """
            return "test_func_1"

    app = TestApp()
    tool_details = build_tool(app, app.test_func_1)

    assert tool_details.class_name == "TestApp"
    assert tool_details.app_name == "SomeApp"
    assert tool_details.func_name == "test_func_1"
    assert tool_details.name == "SomeApp__test_func_1"
    assert tool_details.function_description == "Test func description"
    assert tool_details.return_type == "str"
    assert tool_details.return_description == 'constant string "test_func_1"'
    assert not tool_details.write_operation
    assert tool_details.args == [
        AppToolArg(
            name="arg1",
            arg_type="str",
            description="important parameter",
            has_default=False,
            default=None,
            example_value="test1",
            type_obj=str,
        ),
        AppToolArg(
            name="arg2",
            arg_type="int",
            description="less important parameter",
            has_default=False,
            default=None,
            example_value=123,
            type_obj=int,
        ),
        AppToolArg(
            name="arg3",
            arg_type="float | None",
            description="non important parameter",
            has_default=True,
            default=33.3,
            example_value=33.3,
            type_obj=float | None,
        ),
    ]


def test_get_example_from_docstring():
    class DummyApp:
        def __init__(self, name: str = "test"):
            self.name = name

        @app_tool()
        def get_current_weather(self, location: str, unit: str = "celsius"):
            """
            Get the current weather in a given location.

            :param location: The location to get the weather for.
            :param unit: The unit to return the temperature in. Defaults to "celsius".
            :return: The current weather in the given location.

            :example:
                get_current_weather("San Francisco, CA", "fahrenheit")
            """
            return f"The current weather in {location} is {unit}"

        @app_tool()
        def get_current_weather_wrong_type(self, location: str, unit: str = "celsius"):
            """
            Get the current weather in a given location.

            :param location: The location to get the weather for.
            :param unit: The unit to return the temperature in. Defaults to "celsius".
            :return: The current weather in the given location.

            :example:
                get_current_weather_wrong_type(123, "fahrenheit")
            """
            return f"The current weather in {location} is {unit}"

        @app_tool()
        def get_current_weather_wrong_nb_args(
            self, location: str, unit: str = "celsius"
        ):
            """
            Get the current weather in a given location.

            :param location: The location to get the weather for.
            :param unit: The unit to return the temperature in. Defaults to "celsius".
            :return: The current weather in the given location.

            :example:
                get_current_weather_wrong_nb_args("test1", "test2", "San Francisco, CA", "fahrenheit")
            """
            return f"The current weather in {location} is {unit}"

    call_example = get_example_from_docstring(DummyApp.get_current_weather)
    assert call_example == 'get_current_weather("San Francisco, CA", "fahrenheit")'

    example_values = parse_function_call_example(
        DummyApp.get_current_weather, call_example
    )
    assert example_values == {
        "location": "San Francisco, CA",
        "unit": "fahrenheit",
    }

    with pytest.raises(TypeError) as exc_info:
        call_example = get_example_from_docstring(
            DummyApp.get_current_weather_wrong_type
        )
        assert call_example == 'get_current_weather_wrong_type(123, "fahrenheit")'

        example_values = parse_function_call_example(
            DummyApp.get_current_weather_wrong_type, call_example
        )

    assert (
        str(exc_info.value)
        == "Argument 'location' should be of type <class 'str'>, but got <class 'int'>."
    )

    with pytest.raises(ValueError) as exc_info:
        call_example = get_example_from_docstring(
            DummyApp.get_current_weather_wrong_nb_args
        )
        assert (
            call_example
            == 'get_current_weather_wrong_nb_args("test1", "test2", "San Francisco, CA", "fahrenheit")'
        )

        example_values = parse_function_call_example(
            DummyApp.get_current_weather_wrong_nb_args, call_example
        )

    assert (
        str(exc_info.value)
        == "Too many arguments provided in the example. Expected 2 but got 4."
    )


def test_dynamic_tools_detection():
    class TestApp(App):
        def __init__(self):
            super().__init__()

        @app_tool()
        def static_method(self):
            """This is a statically defined method."""
            pass

    app = TestApp()

    @app_tool()
    def dynamic_method(self):
        """This is a dynamically added method."""
        pass

    app.dynamic_method = dynamic_method.__get__(app)  # type: ignore

    tools = app.get_tools_with_attribute(ToolAttributeName.APP, ToolType.APP)
    assert len(tools) == 2
    assert tools[0].name == "TestApp__static_method"
    assert tools[1].name == "TestApp__dynamic_method"


def test_app_tool_failure():
    class TestApp(App):
        def __init__(self):
            super().__init__()

        @app_tool()
        def multiply(self, a: int, b: int) -> int:
            """
            Multiply two numbers.

            :param a: The first number.
            :param b: The second number.
            :return: The product of the two numbers.
            """
            return a * b

    app = TestApp()
    app.failure_probability = 1.0

    @app_tool()
    def dynamic_method(self):
        """This is a dynamically added method."""
        pass

    app.dynamic_method = dynamic_method.__get__(app)  # type: ignore

    tools = app.get_tools_with_attribute(ToolAttributeName.APP, ToolType.APP)
    assert all(tool.failure_probability == 1.0 for tool in tools)

    with pytest.raises(Exception):
        tools[0](1, 2)


def test_app_tool_metadata_propagation():
    """
    Test that AppTool metadata is properly stored and accessible from different contexts:
    1. Directly from the AppTool
    2. When calling the tool
    3. From a registered event
    4. When the function is called and an event is registered by event_registered
    """
    from are.simulation.environment import Environment
    from are.simulation.tool_utils import APPTOOL_ATTR_NAME
    from are.simulation.types import Action, CompletedEvent

    # Create a test app with an AppTool
    class MetadataTestApp(App):
        def __init__(self):
            super().__init__(name="MetadataTestApp")
            self.time_manager = Environment().time_manager
            self.captured_event = None

        # Mock add_event method that captures the event
        def add_event(self, event: Any) -> None:
            self.captured_event = event

        @app_tool()
        @event_registered()
        def test_tool(self, param1: str, param2: int = 42) -> str:
            """
            A test tool with metadata.

            :param param1: First parameter description
            :param param2: Second parameter description
            :return: A test result string

            :example:
                test_tool("test", 123)
            """
            return f"Result: {param1}, {param2}"

    # Create app instance
    app = MetadataTestApp()

    # Get the AppTool
    tools = app.get_tools_with_attribute(ToolAttributeName.APP, ToolType.APP)
    assert len(tools) == 1

    # 2. Verify metadata is accessible from the function
    func = app.test_tool

    # Check if the function has the AppTool attribute directly
    if hasattr(func, "__self__"):  # It's a bound method
        apptool = getattr(func.__func__, APPTOOL_ATTR_NAME, None)  # type: ignore
    else:
        apptool = getattr(func, APPTOOL_ATTR_NAME, None)

    assert apptool is not None
    assert apptool.name == "MetadataTestApp__test_tool"

    # 3. Verify metadata is accessible from an Action
    action = Action(
        app=app,
        function=app.test_tool,
        args={"self": app, "param1": "test_value", "param2": 123},
    )

    assert action.tool_metadata is not None
    assert action.tool_metadata.name == "MetadataTestApp__test_tool"
    assert action.tool_metadata.function_description == "A test tool with metadata."
    assert len(action.tool_metadata.args) == 2
    assert action.tool_metadata.args[0].name == "param1"
    assert action.tool_metadata.args[0].arg_type == "str"
    assert action.tool_metadata.args[0].description == "First parameter description"

    # 4. Verify metadata is propagated when the function is called and an event is registered
    _result = app.test_tool("test_call", 456)

    # Verify the event was captured
    assert app.captured_event is not None
    assert isinstance(app.captured_event, CompletedEvent)
    event_action = app.captured_event.action
    assert isinstance(event_action, Action)

    # Verify the event has the correct metadata
    assert event_action.tool_metadata is not None
    assert event_action.tool_metadata != {}
    assert event_action.tool_metadata.name == "MetadataTestApp__test_tool"
    assert (
        event_action.tool_metadata.function_description == "A test tool with metadata."
    )
    assert len(event_action.tool_metadata.args) == 2
