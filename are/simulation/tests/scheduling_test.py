# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from are.simulation.apps.app import App
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.types import (
    ConditionCheckEvent,
    Event,
    EventRegisterer,
    event_registered,
)


class DummyApp(App):
    def __init__(self):
        super().__init__()
        self.logs = []

    @event_registered()
    def log_input(self, log: str):
        self.logs.append(log)


def test_depends_on_start_with_delay():
    app = DummyApp()
    config = EnvironmentConfig(start_time=0, duration=10)
    env = Environment(config)
    env.register_apps([app])
    with EventRegisterer.capture_mode():
        e1: Event = app.log_input("hello 1").with_id("e1")
        e2: Event = app.log_input("hello 2").with_id("e2")

    e1.depends_on(None, delay_seconds=5)
    e2.depends_on([e1], delay_seconds=2)

    env.schedule([e1, e2])

    env.start()
    env.join()

    expected_event_ids_time = [
        ("e1", 5),
        ("e2", 7),
    ]

    actual_event_ids_time = [
        (e.event_id, e.event_time) for e in env.event_log.list_view()
    ]

    assert actual_event_ids_time == expected_event_ids_time


def test_temporal_dependency():
    app = DummyApp()
    config = EnvironmentConfig(start_time=0, duration=10)
    env = Environment(config)
    env.register_apps([app])
    with EventRegisterer.capture_mode():
        e1: Event = app.log_input("hello 1").with_id("e1")
        e2: Event = app.log_input("hello 2").with_id("e2")
        e3: Event = app.log_input("hello 3").with_id("e3")
        e4: Event = app.log_input("hello 4").with_id("e4")

    e1.depends_on(None, delay_seconds=1)
    e2.depends_on(None, delay_seconds=2)
    e3.depends_on([e1, e2], delay_seconds=5)
    e4.depends_on([e3], delay_seconds=2)

    env.schedule([e1, e2, e3, e4])
    env.start()
    env.join()

    expected_event_ids_time = [
        ("e1", 1),
        ("e2", 2),
        ("e3", 7),
        ("e4", 9),
    ]

    actual_event_ids_time = [
        (e.event_id, e.event_time) for e in env.event_log.list_view()
    ]

    print(expected_event_ids_time)
    print(actual_event_ids_time)

    assert actual_event_ids_time == expected_event_ids_time


def test_multiple_dependencies():
    app = DummyApp()
    config = EnvironmentConfig(start_time=0, duration=10)
    env = Environment(config)
    env.register_apps([app])
    with EventRegisterer.capture_mode():
        e1: Event = app.log_input("hello 1").with_id("e1")
        e2: Event = app.log_input("hello 2").with_id("e2")
        e3: Event = app.log_input("hello 3").with_id("e3")
        e4: Event = app.log_input("hello 4").with_id("e4")

    e2.depends_on([e1], delay_seconds=1)
    e3.depends_on([e1], delay_seconds=1)
    e4.depends_on([e2, e3], delay_seconds=1)

    env.schedule([e1, e2, e3, e4])
    env.start()
    env.join()

    expected_event_ids_time = [
        ("e1", 0),
        ("e2", 1),
        ("e3", 1),
        ("e4", 2),
    ]

    actual_event_ids_time = [
        (e.event_id, e.event_time) for e in env.event_log.list_view()
    ]

    assert len(env.event_log) == 4
    assert actual_event_ids_time == expected_event_ids_time


def test_conditional_events():
    app = DummyApp()
    config = EnvironmentConfig(
        start_time=0, duration=10, queue_based_loop=True, oracle_mode=True
    )
    env = Environment(config)
    env.register_apps([app])
    with EventRegisterer.capture_mode():
        c1 = ConditionCheckEvent.from_condition(
            lambda env: env.current_time >= 5
        ).with_id("c1")
        ec1: Event = app.log_input("Triggered after condition c1 !").with_id("ec1")

    c1.depends_on(None)
    ec1.depends_on([c1], delay_seconds=3)
    env.schedule([c1, ec1])
    env.start()
    env.join()

    for e in env.event_log.list_view():
        print(f"{e.event_id} at {e.event_time}")

    expected_event_ids_time = [
        ("c1-CHECK_0", 0),
        ("c1-CHECK_1", 1),
        ("c1-CHECK_2", 2),
        ("c1-CHECK_3", 3),
        ("c1-CHECK_4", 4),
        ("c1-CHECK_5", 5),
        ("ec1", 5 + 3),
    ]

    actual_event_ids_time = [
        (e.event_id, e.event_time) for e in env.event_log.list_view()
    ]

    print(expected_event_ids_time)
    print(actual_event_ids_time)

    assert actual_event_ids_time == expected_event_ids_time
