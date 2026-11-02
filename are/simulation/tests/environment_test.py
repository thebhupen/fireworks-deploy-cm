# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import functools
import random
from unittest.mock import MagicMock

import pytest

from are.simulation.apps import AgentUserInterface
from are.simulation.apps.app import App
from are.simulation.apps.email_client import Email, EmailClientApp, EmailFolderName
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.tool_utils import app_tool
from are.simulation.types import (
    AbstractEnvironment,
    Action,
    CompletedEvent,
    ConditionCheckEvent,
    Event,
    event_registered,
)
from are.simulation.utils import get_state_dict


class DummyApp(App):
    def __init__(self):
        super().__init__()
        self.logs = []

    def get_state(self):
        return get_state_dict(self, ["logs"])

    def reset(self):
        self.logs = []

    @app_tool()
    @event_registered()
    def log_stuff(self, message: str):
        self.logs.append(message)

    @event_registered()
    def print_action_triggered(self):
        print("[TRIGGERED EVENT] Hello World at time")

    @event_registered()
    def print_action_event(self):
        print("[SCHEDULED EVENT] Hello World at time")


def random_email_action(email_app: EmailClientApp, max_index: int = 5) -> Action:
    method_to_call = random.choice(["list_emails", "read_email", "add_email"])
    random_index = random.randint(0, max_index)

    if method_to_call == "list_emails":
        a = Action(function=email_app.list_emails)
    elif (
        method_to_call == "read_email"
        and len(email_app.folders[EmailFolderName.INBOX].emails) > 0
    ):
        email_id = random.choice(
            [m.email_id for m in email_app.folders[EmailFolderName.INBOX].emails]
        )
        a = Action(
            email_app.get_email_by_id,
            {"email_id": email_id},
        )
    else:
        a = Action(
            function=email_app.add_email,
            args={
                "email": Email(
                    sender=f"user_{random_index}@example.com",
                    subject=f"Subject {random_index}",
                    content=f"Content {random_index}",
                    timestamp=email_app.time_manager.time(),
                    recipients=["recipient@example.com"],
                    cc=[],
                )
            },
        )

    return a


def random_time_condition(r: float):
    def condition(env: AbstractEnvironment) -> bool:
        return (
            r - env.time_increment_in_seconds <= env.current_time - env.start_time <= r
        )

    return condition


def test_env():
    start_time = random.randint(0, 1000)
    app = DummyApp()

    env = Environment(EnvironmentConfig(start_time=start_time, duration=10))

    expected_event_times = []
    for i in range(10):
        event = Event.from_function(app.print_action_event)
        event.event_time = start_time + i
        expected_event_times.append(start_time + i)
        env.schedule(event)
    trigger_times = [3, 6, 9]

    def check_env_time(env, r):
        return (
            r - env.time_increment_in_seconds <= env.current_time - env.start_time <= r
        )

    for r in trigger_times:
        event = Event.from_function(app.print_action_triggered)
        condition_check = ConditionCheckEvent.from_condition(
            functools.partial(check_env_time, r=r)
        )
        event.depends_on(condition_check)
        env.schedule([event, condition_check])
        # every condition check also generates a completed event
        for i in range(0, r, env.time_increment_in_seconds):
            expected_event_times.append(start_time + i)

        expected_event_times.append(start_time + r - env.time_increment_in_seconds)

    expected_event_times = sorted(expected_event_times)

    env.start()
    env.join()
    event_list = env.event_log.list_view()

    assert len(event_list) == len(expected_event_times)

    for expected_time, event in zip(expected_event_times, event_list):
        assert isinstance(event, CompletedEvent)
        assert (
            pytest.approx(expected_time, abs=env.time_increment_in_seconds)
            == event.event_time
        )


def test_queue_based_loop():
    start_time = random.randint(0, 1000)
    app = DummyApp()
    event_relative_times = [3, 5, 9]
    conditional_event_relative_times = [2, 8]

    def run_env(queue_based_loop: bool = False):
        env = Environment(
            EnvironmentConfig(
                start_time=start_time,
                duration=10,
                queue_based_loop=queue_based_loop,
                oracle_mode=queue_based_loop,
            )
        )

        expected_event_times = []
        for i in event_relative_times:
            event = Event.from_function(app.print_action_event).with_id(
                f"scheduled_{i}"
            )
            event.event_time = start_time + i
            expected_event_times.append(start_time + i)
            env.schedule(event)

        def check_env_time(env, r):
            return (
                r - env.time_increment_in_seconds
                <= env.current_time - env.start_time
                <= r
            )

        for r in conditional_event_relative_times:
            event = Event.from_function(app.print_action_triggered).with_id(
                f"triggered_{r}"
            )
            condition_check = ConditionCheckEvent.from_condition(
                functools.partial(check_env_time, r=r), every_tick=2
            ).with_id(f"condition_{r}")
            event.depends_on(condition_check)
            env.schedule([event, condition_check])
            # every condition check also generates a completed event
            for i in range(0, r, env.time_increment_in_seconds):
                expected_event_times.append(start_time + i)

            expected_event_times.append(start_time + r - env.time_increment_in_seconds)

        expected_event_times = sorted(expected_event_times)

        env.start()
        env.join()
        event_list = env.event_log.list_view()
        return event_list

    event_list_time_based = run_env()
    event_list_queue_based = run_env(queue_based_loop=True)

    time_event_ids = [e.event_id for e in event_list_time_based]
    queue_event_ids = [e.event_id for e in event_list_queue_based]

    print(f"DIFF {(set(time_event_ids) - set(queue_event_ids))}")

    print(f"DIFF {set(queue_event_ids) - set(time_event_ids)}")

    # print([(e.event_id, e.event_time) for e in event_list_queue_based])
    # print([(e.event_id, e.event_time) for e in event_list_time_based])
    for event in event_list_queue_based:
        if event.event_id not in time_event_ids:
            print("\nNEW EVENT")
            print(event)

    assert len(event_list_queue_based) == len(event_list_time_based)


def test_get_user_tools():
    env = Environment()
    aui = AgentUserInterface()
    env.register_apps([aui])
    user_tools_by_app = env.get_user_tools_by_app()
    assert len(user_tools_by_app["AgentUserInterface"]) == 1
    assert (
        user_tools_by_app["AgentUserInterface"][0].name
        == "AgentUserInterface__send_message_to_agent"
    )

    user_tools = env.get_user_tools()
    assert len(user_tools) == 1
    assert user_tools[0].name == "AgentUserInterface__send_message_to_agent"


@pytest.fixture
def setup_event_and_past_events():
    event = MagicMock()
    event.action = MagicMock()
    event.action.args = {
        "arg1": "{{event1.key1}}",
        "arg2": "value2",
        "arg3": "{{event2.key2.key3}}",
    }
    event.action.resolved_args = {}

    past_event1 = MagicMock()
    past_event1.event_id = "event1"
    past_event1.metadata.return_value = {"key1": "resolved_value1"}

    past_event2 = MagicMock()
    past_event2.event_id = "event2"
    past_event2.metadata.return_value = {"key2": {"key3": "resolved_value2"}}

    past_events = [past_event1, past_event2]

    return event, past_events


def test_resolve_arg_placeholders(setup_event_and_past_events):
    event, past_events = setup_event_and_past_events
    resolved_event = Environment().resolve_arg_placeholders(event, past_events)
    assert resolved_event.action.resolved_args["arg1"] == "resolved_value1"
    assert resolved_event.action.resolved_args["arg2"] == "value2"
    assert resolved_event.action.resolved_args["arg3"] == "resolved_value2"


def test_resolve_arg_no_placeholder(setup_event_and_past_events):
    event, past_events = setup_event_and_past_events
    event.action.args = {"arg1": "value1"}
    resolved_event = Environment().resolve_arg_placeholders(event, past_events)
    assert resolved_event.action.resolved_args["arg1"] == "value1"


def test_resolve_arg_placeholder_not_found(setup_event_and_past_events):
    event, past_events = setup_event_and_past_events
    event.action.args = {"arg1": "{{event3.key1}}"}
    resolved_event = Environment().resolve_arg_placeholders(event, past_events)
    assert resolved_event.action.resolved_args["arg1"] == "{{event3.key1}}"


def test_resolve_arg_placeholders_with_whitespace(setup_event_and_past_events):
    event, past_events = setup_event_and_past_events
    event.action.args = {"arg1": " {{event1.key1}} "}
    resolved_event = Environment().resolve_arg_placeholders(event, past_events)
    assert resolved_event.action.resolved_args["arg1"] == "resolved_value1"
