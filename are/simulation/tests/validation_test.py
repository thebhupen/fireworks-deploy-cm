# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import threading
from unittest.mock import patch

from are.simulation.apps import AgentUserInterface
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.tests.core_test import DummyApp
from are.simulation.types import (
    AbstractEnvironment,
    AbstractEvent,
    AgentValidationEvent,
    EnvironmentState,
    Event,
    EventRegisterer,
    EventType,
    ValidationEvent,
)


def patched_thread_init(self, *args, **kwargs):
    original_thread_init = kwargs.pop("original_thread_init", [])
    original_target = kwargs.get("target")
    exception_container = kwargs.pop("exception_container", [])
    if original_target:

        def wrapped_target(*args, **kwargs):
            try:
                original_target(*args, **kwargs)
            except Exception as e:
                exception_container.append(e)

        kwargs["target"] = wrapped_target
    # Call the original __init__ method to avoid recursion
    original_thread_init(self, *args, **kwargs)


# Wrapper function that returns the correct `patched_thread_init`
def create_patched_thread_init_with_container(
    exception_container, original_thread_init
):
    def wrapper(self, *args, **kwargs):
        # Call patched_thread_init with the `self` and pass the exception_container
        return patched_thread_init(
            self,
            *args,
            exception_container=exception_container,
            original_thread_init=original_thread_init,
            **kwargs,
        )

    return wrapper


def val_fn1(env: AbstractEnvironment) -> bool:
    app: AgentUserInterface = env.get_app(AgentUserInterface.__name__)
    agent_messages = app.get_all_messages_from_agent()
    return any(message.content == "I am a robot" for message in agent_messages)


def val_fn2(env: AbstractEnvironment) -> bool:
    app: AgentUserInterface = env.get_app(AgentUserInterface.__name__)
    agent_messages = app.get_all_messages_from_agent()
    return any(
        message.content == "I am not a robot •`_´• " for message in agent_messages
    )


def test_validation_events():
    app = DummyApp()
    aui = AgentUserInterface()
    env = Environment(EnvironmentConfig(start_time=0, duration=15))
    env.register_apps([app, aui])

    with EventRegisterer.capture_mode():
        aui1 = (
            aui.send_message_to_agent(
                content='Hello agent! Tell me "I am a robot", nothing more, nothing less.'
            )
            .with_id("aui1")
            .depends_on(None, delay_seconds=1)
        )

        aui2 = (
            aui.get_last_message_from_user()
            .with_id("aui2")
            .depends_on(aui1, delay_seconds=2)
        )

        val1 = (
            ValidationEvent(
                milestones=[val_fn1, val_fn2], schedule_every_ticks=1, timeout=10
            )
            .with_id("val1")
            .depends_on(aui1)
        )

        aui3 = (
            aui.send_message_to_user(content="I am a robot")
            .with_id("aui3")
            .with_type(EventType.AGENT)
        ).depends_on(aui1, delay_seconds=6)

        aui4 = (
            aui.send_message_to_user(content="I am not a robot •`_´• ")
            .with_id("aui4")
            .with_type(EventType.AGENT)
        ).depends_on(aui3, delay_seconds=2)

        aui5 = (
            aui.send_message_to_user(content="I know this is gonna raise an error!")
            .with_id("aui5")
            .depends_on(aui3, delay_seconds=3)
            .with_type(EventType.AGENT)
        )

    # env.schedule([aui1, aui2, aui3])
    env.schedule([aui1, aui2, aui3, aui4, aui5, val1])

    # Capture exceptions
    exception_container = []
    # Store the original __init__ to avoid recursion
    original_thread_init = threading.Thread.__init__
    partial_patched_thread_init = create_patched_thread_init_with_container(
        exception_container=exception_container,
        original_thread_init=original_thread_init,
    )

    with patch.object(
        threading.Thread,
        "__init__",
        new=partial_patched_thread_init,
    ):
        env.start()
        env.join()

    log = env.event_log.list_view()
    log = [e for e in log if not e.event_type == EventType.VALIDATION]

    assert log[0].event_id == "aui1" and log[0].event_time == 1
    assert log[1].event_id == "aui2" and log[1].event_time == 3
    assert log[2].event_id == "aui3" and log[2].event_time == 7
    assert log[3].event_id == "aui4" and log[3].event_time == 9

    log = [e for e in env.event_log.list_view() if e.event_type == EventType.VALIDATION]
    for e in log:
        # 7 here because it's the time when aui3 happens thus achieving the first milestone
        if e.event_time == 7:
            if e.metadata.return_value is not None:
                milestones = e.metadata.return_value.achieved_milestones
            else:
                milestones = []
            assert len(milestones) == 1 and milestones[0].__name__ == "val_fn1"
        # 7 here because it's the time when aui4 happens thus achieving the first milestone
        elif e.event_time == 9:
            print(e)
            if e.metadata.return_value is not None:
                milestones = e.metadata.return_value.achieved_milestones
            else:
                milestones = []
            assert len(milestones) == 2 and milestones[1].__name__ == "val_fn2"

    # Now let's alter the timeout for the validation event to something shorter
    app = DummyApp()
    aui.messages = []
    env = Environment(EnvironmentConfig(start_time=0, duration=15))
    env.register_apps([app, aui])

    # To make sure only 1 of the validation functions is triggered before timeout
    val1.timeout = 7
    # print(val1)

    env.schedule([aui1, aui2, aui3, aui4, aui5, val1])
    with patch.object(threading.Thread, "__init__", new=partial_patched_thread_init):
        env.start()
        env.join()

    log = [e for e in env.event_log.list_view() if e.event_type == EventType.VALIDATION]
    for e in log:
        # 7 here because it's the time when aui3 happens thus achieving the first milestone
        if e.event_time == 7:
            if e.metadata.return_value is not None:
                milestones = e.metadata.return_value.achieved_milestones
            else:
                milestones = []
            assert len(milestones) == 1 and milestones[0].__name__ == "val_fn1"

    assert env.state == EnvironmentState.FAILED


def agent_val_fn1(env: AbstractEnvironment, event: AbstractEvent) -> bool:
    if type(event) is not Event:
        return False
    return (
        event.action.app.__class__ == AgentUserInterface
        and event.function_name() == "send_message_to_user"
        and event.action.args["content"] == "I am a robot"
    )


def agent_val_fn2(env: AbstractEnvironment, event: AbstractEvent) -> bool:
    if type(event) is not Event:
        return False
    return (
        event.action.app.__class__ == AgentUserInterface
        and event.function_name() == "send_message_to_user"
        and event.action.args["content"] == "I am not a robot •`_´• "
    )


def test_agent_validation_events():
    app = DummyApp()
    aui = AgentUserInterface()
    env = Environment(EnvironmentConfig(start_time=0, duration=15))
    env.register_apps([app, aui])

    with EventRegisterer.capture_mode():
        aui1 = (
            aui.send_message_to_agent(
                content='Hello agent! Tell me "I am a robot", nothing more, nothing less.'
            )
            .with_id("aui1")
            .depends_on(None, delay_seconds=1)
        )

        aui2 = (
            aui.get_last_message_from_user()
            .with_id("aui2")
            .depends_on(aui1, delay_seconds=2)
        )

        val1 = (
            AgentValidationEvent(milestones=[agent_val_fn1, agent_val_fn2], timeout=10)
            .with_id("val1")
            .depends_on(aui1)
        )

        aui3 = (
            aui.send_message_to_user(content="I am a robot")
            .with_id("aui3")
            .with_type(EventType.AGENT)
        ).depends_on(aui1, delay_seconds=6)

        aui4 = (
            aui.send_message_to_user(content="I am not a robot •`_´• ")
            .with_id("aui4")
            .with_type(EventType.AGENT)
        ).depends_on(aui3, delay_seconds=2)

        aui5 = (
            aui.send_message_to_user(content="I know this is gonna raise an error!")
            .with_id("aui5")
            .depends_on(aui3, delay_seconds=3)
            .with_type(EventType.AGENT)
        )

    # env.schedule([aui1, aui2, aui3])
    env.schedule([aui1, aui2, aui3, aui4, aui5, val1])

    # Capture exceptions
    exception_container = []
    # Store the original __init__ to avoid recursion
    original_thread_init = threading.Thread.__init__
    partial_patched_thread_init = create_patched_thread_init_with_container(
        exception_container=exception_container,
        original_thread_init=original_thread_init,
    )

    with patch.object(
        threading.Thread,
        "__init__",
        new=partial_patched_thread_init,
    ):
        env.start()
        env.join()

    log = env.event_log.list_view()
    log = [e for e in log if not e.event_type == EventType.VALIDATION]

    assert log[0].event_id == "aui1" and log[0].event_time == 1
    assert log[1].event_id == "aui2" and log[1].event_time == 3
    assert log[2].event_id == "aui3" and log[2].event_time == 7
    assert log[3].event_id == "aui4" and log[3].event_time == 9

    log = [e for e in env.event_log.list_view() if e.event_type == EventType.VALIDATION]
    for e in log:
        # 7 here because it's the time when aui3 happens thus achieving the first milestone
        if e.event_time == 7:
            if e.metadata.return_value is not None:
                milestones = e.metadata.return_value.achieved_milestones
            else:
                milestones = []
            assert len(milestones) == 1 and milestones[0].__name__ == "val_fn1"
        # 7 here because it's the time when aui4 happens thus achieving the first milestone
        elif e.event_time == 9:
            print(e)
            if e.metadata.return_value is not None:
                milestones = e.metadata.return_value.achieved_milestones
            else:
                milestones = []
            assert len(milestones) == 2 and milestones[1].__name__ == "val_fn2"

    # Now let's alter the timeout for the validation event to something shorter
    app = DummyApp()
    aui.messages = []
    env = Environment(EnvironmentConfig(start_time=0, duration=15))
    # env = Environment(EnvironmentConfig(start_time=0, duration=15, oracle_mode=False, queue_based_loop=False))
    env.register_apps([app, aui])

    # To make sure only 1 of the milestones is triggered before timeout
    val1.timeout = 6
    # print(val1)

    env.schedule([aui1, aui2, aui3, aui4, aui5, val1])
    # with patch.object(threading.Thread, "__init__", new=partial_patched_thread_init):
    env.start()
    env.join()

    log = [e for e in env.event_log.list_view() if e.event_type == EventType.VALIDATION]
    for e in log:
        # 7 here because it's the time when aui3 happens thus achieving the first milestone
        if e.event_time == 7:
            if e.metadata.return_value is not None:
                milestones = e.metadata.return_value.achieved_milestones
            else:
                milestones = []
            assert len(milestones) == 1 and milestones[0].__name__ == "val_fn1"

    assert env.state == EnvironmentState.FAILED


if __name__ == "__main__":
    test_validation_events()
