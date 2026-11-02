# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
import random
import tempfile
from dataclasses import dataclass

import pytest

from are.simulation.apps.app import App
from are.simulation.apps.sandbox_file_system import SandboxLocalFileSystem
from are.simulation.apps.shopping import Item, Product, ShoppingApp
from are.simulation.apps.system import SystemApp
from are.simulation.data.population_scripts.sandbox_file_system_population import (
    default_fs_folders,
    random_fs_population,
    set_available_files,
)
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.tests.utils import IN_GITHUB_ACTIONS
from are.simulation.tool_utils import (
    AppTool,
    AppToolAdapter,
    AppToolArg,
    app_tool,
    user_tool,
)
from are.simulation.types import (
    AbstractEnvironment,
    Action,
    ConditionCheckEvent,
    Event,
    EventRegisterer,
    EventType,
    OperationType,
    event_registered,
)
from are.simulation.utils import deserialize_dynamic

logger = logging.getLogger(__name__)


class DummyApp(App):
    def __init__(self, name: str | None = None, a: str = "test", b: int = 0):
        # We pass all the args to the super init, so they get memorised when we want to reset
        super().__init__(name, a, b)
        self.logs = []
        self.a = a
        self.b = b

    @app_tool()
    @event_registered()
    def add_numbers(self, a: int, b: int) -> int:
        """
        Adds two numbers
        :param a: first number
        :param b: second number
        :returns: sum of the two numbers
        """
        return a + b

    @app_tool(llm_formatter=lambda x: f"Calling calculator returned {x}")
    @event_registered(operation_type=OperationType.WRITE)
    def add_numbers_formatted(self, a: int, b: int) -> int:
        """
        Adds two numbers
        :param a: first number
        :param b: second number
        :returns: sum of the two numbers
        """
        return a + b

    @user_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def multiply_numbers(self, a: int, b: int) -> int:
        """
        Multiplies two numbers
        :param a: first number
        :param b: second number
        :returns: product of the two numbers
        """
        return a * b

    def log_input(self, log: str):
        self.logs.append(log)


def test_adds_event_history():
    app = DummyApp()
    environment = Environment()
    environment.register_apps([app])

    app.add_numbers(3, 5)

    assert len(environment.event_log) == 1


def test_register_tools():
    app = DummyApp()
    environment = Environment()
    environment.register_apps([app])
    expected_tools = [
        AppTool(
            class_name="DummyApp",
            app_name="DummyApp",
            name="DummyApp__add_numbers",
            function_description="Adds two numbers",
            args=[
                AppToolArg(
                    name="a", arg_type="int", description="first number", type_obj=int
                ),
                AppToolArg(
                    name="b", arg_type="int", description="second number", type_obj=int
                ),
            ],
            class_instance=app,
            function=DummyApp.add_numbers,
            return_type="int",
            return_description="sum of the two numbers",
            write_operation=False,
        ),
        AppTool(
            class_name="DummyApp",
            app_name="DummyApp",
            name="DummyApp__add_numbers_formatted",
            function_description="Adds two numbers",
            args=[
                AppToolArg(
                    name="a", arg_type="int", description="first number", type_obj=int
                ),
                AppToolArg(
                    name="b", arg_type="int", description="second number", type_obj=int
                ),
            ],
            class_instance=app,
            function=DummyApp.add_numbers_formatted,
            return_type="int",
            return_description="sum of the two numbers",
            write_operation=True,
        ),
    ]

    expected_user_tools = [
        AppTool(
            class_name="DummyApp",
            app_name="DummyApp",
            name="DummyApp__multiply_numbers",
            function_description="Multiplies two numbers",
            args=[
                AppToolArg(
                    name="a", arg_type="int", description="first number", type_obj=int
                ),
                AppToolArg(
                    name="b", arg_type="int", description="second number", type_obj=int
                ),
            ],
            class_instance=app,
            function=DummyApp.multiply_numbers,
            return_type="int",
            return_description="product of the two numbers",
            write_operation=True,
        )
    ]

    assert app.get_user_tools() == expected_user_tools
    assert app.get_tools() == expected_tools


def test_app_tool_adapter():
    app = DummyApp()
    environment = Environment()
    environment.register_apps([app])
    app_tool = app.get_tools()[0]
    tool = AppToolAdapter(app_tool)
    a = random.randint(0, 1000)
    b = random.randint(0, 1000)
    assert app_tool(a, b) == tool.forward(a, b)


def test_llm_formatted_tool_calls():
    app = DummyApp()
    environment = Environment()
    environment.register_apps([app])
    app_tool = app.get_tools()[1]
    tool = AppToolAdapter(app_tool)
    a = random.randint(0, 1000)
    b = random.randint(0, 1000)
    c = a + b
    assert app_tool(a, b) == tool.forward(a, b)
    assert app_tool(a, b) == f"Calling calculator returned {c}"
    assert tool.forward(a, b) == f"Calling calculator returned {c}"
    assert app.add_numbers_formatted(a, b) == c


def test_open_ai_tools():
    app = DummyApp()
    environment = Environment()
    environment.register_apps([app])
    app_tool = app.get_tools()[0]
    expected_tool_desc = {
        "type": "function",
        "function": {
            "name": "DummyApp__add_numbers",
            "description": "Adds two numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer", "description": "first number"},
                    "b": {"type": "integer", "description": "second number"},
                },
                "required": ["a", "b"],
            },
        },
    }
    assert app_tool.to_open_ai() == expected_tool_desc


def test_generate_tools():
    app = DummyApp()
    environment = Environment()
    environment.register_apps([app])

    app_tools = environment.get_tools_by_app()
    print(app_tools)
    tools = app_tools["DummyApp"]

    assert len(tools) == 2
    assert tools[0].name == "DummyApp__add_numbers"
    assert tools[1].name == "DummyApp__add_numbers_formatted"


def test_from_function():
    logger.setLevel(logging.DEBUG)
    app = DummyApp()

    event = Event.from_function(app.log_input, log="Event from function")

    assert event.action.app == app
    assert event.app_class_name() == "DummyApp"
    assert event.function_name() == "log_input"
    assert event.action.args == {"log": "Event from function"}


def test_simple_event():
    logger.setLevel(logging.DEBUG)
    app = DummyApp()

    # Setup trigger
    def condition(env: AbstractEnvironment) -> bool:
        last_event = environment.get_latest_event()
        if last_event and type(last_event.action) is Action:
            return last_event.app_class_name() == "DummyApp"
        return False

    event = Event.from_function(app.log_input, log="oh hai")
    condition_check = ConditionCheckEvent.from_condition(condition)
    event.depends_on(condition_check)

    # Initialize app
    environment = Environment()
    environment.register_apps([app])
    environment.schedule([event, condition_check])
    app.add_numbers(3, 5)

    environment.prepare_events_for_start()
    environment.tick()

    assert len(app.logs) == 1


def test_sandbox_file_system():
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = SandboxLocalFileSystem(sandbox_dir=tmpdir)

        fs.touch("test.txt")
        assert fs.exists("test.txt")

        fs.rm("test.txt")
        assert not fs.exists("test.txt")

        fs.mkdir("test_dir")
        assert fs.exists("test_dir")

        fs.rmdir("test_dir")
        assert not fs.exists("test_dir")

        with fs.open("test_write.txt", "w") as file:
            file.write("test")

        assert fs.exists("test_write.txt")

        with fs.open("test_write.txt", "r") as file:
            assert file.read() == "test"

        fs.rm("test_write.txt")
        assert not fs.exists("test.txt")


def test_sandbox_file_system_base_population():
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = SandboxLocalFileSystem(sandbox_dir=tmpdir)

        default_fs_folders(fs)
        assert fs.exists("Applications")
        assert fs.exists("Desktop")
        assert fs.exists("Documents")
        assert fs.exists("Downloads")
        assert fs.exists("Music")
        assert fs.exists("Pictures")
        assert fs.exists("Public")
        assert fs.exists("Templates")
        assert fs.exists("Videos")


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="does not work in github actions")
def test_sandbox_file_system_random_population():
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = SandboxLocalFileSystem(sandbox_dir=tmpdir)

        d = set_available_files()
        random_fs_population(fs, d)
        assert fs.ls("") != []


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="does not work in github actions")
def test_sandbox_file_system_base_random_population():
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = SandboxLocalFileSystem(sandbox_dir=tmpdir)

        default_fs_folders(fs)
        d = set_available_files()
        random_fs_population(fs=fs, available_files=d, path="Documents")
        assert fs.exists("Documents")
        assert fs.ls("Documents") != []


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="does not work in github actions")
def test_sandbox_file_system_sample_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = SandboxLocalFileSystem(sandbox_dir=tmpdir)

        default_fs_folders(fs)
        d = set_available_files()
        random_fs_population(fs=fs, available_files=d, path="Documents")
        assert fs.exists("Documents")
        assert fs.ls("Documents") != []

        sample_files = fs.get_sample_files(k=3)
        print(sample_files)
        assert type(sample_files[0]) is str
        assert len(sample_files) == 3


def test_inherit_doc():
    class Foo:
        def __init__(self):
            pass

        def my_method(self) -> None:
            """
            This is an awesome method
            """

    class Bar(App, Foo):
        def __init__(self):
            super().__init__()

        @app_tool()
        def my_method(self):
            pass

    bar = Bar()

    expected_tool = AppTool(
        class_name="Bar",
        app_name="Bar",
        name="Bar__my_method",
        function_description="This is an awesome method",
        args=[],
        class_instance=bar,
        function=Bar.my_method,
    )

    assert bar.get_tools()[0] == expected_tool


def test_event_capture_mode():
    app = DummyApp()
    environment = Environment()
    environment.register_apps([app])
    with EventRegisterer.capture_mode():
        e = app.add_numbers(3, 5)

    assert e.event_type == EventType.ENV
    assert e.action.class_name == "DummyApp"
    assert e.action.function_name == "add_numbers"
    assert e.action.args == {
        "self": app,
        "a": 3,
        "b": 5,
    }


def test_app_reset():
    app = DummyApp(a="blabla", b=42)

    app.log_input("test")
    app.log_input("test2")
    app.log_input("test3")

    assert len(app.logs) == 3
    assert app.a == "blabla"
    assert app.b == 42

    app.a = "another blabla"
    app.b = 1337
    app.reset()

    assert len(app.logs) == 0
    assert app.a == "blabla"
    assert app.b == 42


def test_system_get_time():
    pass

    for i in range(100):
        print(f"ITERATION={i}")
        start_time = random.randint(0, 10000)
        sys = SystemApp()
        env = Environment(EnvironmentConfig(start_time=start_time, duration=200))
        env.register_apps([sys])

        ### Test start time
        env.start()
        assert sys.get_current_time()["current_timestamp"] == pytest.approx(
            env.start_time, abs=1
        )

        ### test wait method
        wait_time = random.randint(0, 100)
        sys.wait(wait_time)

        assert env.start_time is not None
        assert sys.get_current_time()["current_timestamp"] == pytest.approx(
            env.start_time + wait_time, abs=1
        )
        env.stop()


def test_type_check():
    from are.simulation.utils import type_check

    @type_check
    def test_func(a: int, b: str) -> str:
        return f"{a} and {b}"

    test_func(1, "test")

    with pytest.raises(TypeError):
        test_func(1, 2)  # type: ignore

    with pytest.raises(TypeError):
        test_func("test", "test")  # type: ignore

    with pytest.raises(Exception):
        test_func(1, "test", "test")  # type: ignore

    class MyClass:
        @type_check
        def my_method(self, arg1: int, arg2: str) -> str:
            return f"{arg1} and {arg2}"

    my_class = MyClass()
    my_class.my_method(1, "test")

    with pytest.raises(TypeError):
        my_class.my_method(1, 2)  # type: ignore

    with pytest.raises(TypeError):
        my_class.my_method("test", "test")  # type: ignore


def test_deserialize_dynamic():
    @dataclass
    class InnerClass:
        f: float

    @dataclass
    class MyClass:
        a: int
        b: str
        c: list[str]
        d: InnerClass

    ser = {"a": 11, "b": "test", "c": ["test1", "test2"], "d": {"f": 0.1}}
    deser = MyClass(a=11, b="test", c=["test1", "test2"], d=InnerClass(0.1))

    assert deserialize_dynamic(ser, MyClass) == deser
    assert deserialize_dynamic([ser, ser, ser], list[MyClass]) == [deser, deser, deser]
    assert deserialize_dynamic({"stuff": [ser, ser]}, dict[str, list[MyClass]]) == {
        "stuff": [deser, deser]
    }
    assert deserialize_dynamic(
        {"stuff": {1: [ser]}}, dict[str, dict[int, list[MyClass]]]
    ) == {"stuff": {1: [deser]}}


def test_app_fields():
    shopping = ShoppingApp()
    shopping.products = {}
    shopping.products["item1"] = Product(
        name="item1",
        variants={
            "variant1": Item(
                price=10,
                item_id="variant1",
            )
        },
    )
    shopping.products["item2"] = Product(
        name="item2",
        variants={
            "variant2": Item(
                price=10,
                item_id="variant2",
            )
        },
    )

    serialized = shopping.get_state()
    shopping2 = ShoppingApp()

    shopping2.load_state(serialized or {})
    assert shopping == shopping2
