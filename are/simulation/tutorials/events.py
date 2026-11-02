# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import time
from datetime import datetime

from are.simulation.apps.email_client import Email, EmailClientApp
from are.simulation.environment import (
    AbstractEnvironment,
    Environment,
    EnvironmentConfig,
)
from are.simulation.types import (
    Action,
    ConditionCheckEvent,
    Event,
    EventRegisterer,
    EventType,
)


def events_example():
    main()


def main():
    email = EmailClientApp()
    start_time = 100

    env = Environment(EnvironmentConfig(start_time=100))
    env.register_apps([email])

    """
    SCHEDULED EVENT
    """

    # We create an action, that specified which function should be called with which arguments
    # We can either explicitly specify the `app` argument of Action, or let it
    # be inferred from the function if it's a method call
    action = Action(
        function=email.add_email,
        args={
            "email": Email(
                sender="test@example.com",
                recipients=[email.user_email],
                cc=[],
                subject="Hello World !",
                content="Hello World !",
            )
        },
    )
    # Here we create the actual event, that will happen 2 seconds after the start_time
    event_scheduled = Event(event_time=start_time + 2, action=action)

    # We can also use an alternative syntax
    event_scheduled = Event.from_function(
        email.add_email,
        email=Email(
            sender="test@example.com",
            recipients=["test@example.com"],
            subject="Hello World !",
            content="Hello World !",
        ),
    ).depends_on(None, delay_seconds=2)

    # We can also use the delayed syntax
    event_scheduled = Event.from_function(
        email.add_email,
        email=Email(
            sender="test@example.com",
            recipients=["test@example.com"],
            subject="Hello World !",
            content="Hello World !",
        ),
    ).delayed(2)

    # NOTE: we can also have events that are scheduled at some absolute time of our choosing
    # start_time and duration of the simulation need to be coherent for that event to actually happen
    # Example:
    _event_scheduled_at_christmas = Event.from_function(
        email.add_email,
        email=Email(
            sender="test@example.com",
            recipients=["test@example.com"],
            subject="Hello World !",
            content="Hello World !",
        ),
    ).at_absolute_time(
        datetime(year=2024, month=12, day=25, hour=0, minute=0, second=0).timestamp()
    )

    # IMPORTANT: You can also use capture_mode to create events using regular function calls from App api calls
    # These function calls will not be executed, and will simply return a corresponding event instance
    # By default captured events are of type AGENT, but you can specify it with the `with_type` method
    with EventRegisterer.capture_mode():
        _event_captured = (
            email.add_email(
                Email(
                    sender="test@example.com",
                    recipients=["test@example.com"],
                    subject="Hello World !",
                    content="Hello World !",
                )
            )
            .at_absolute_time(start_time + 2)
            .with_type(EventType.ENV)
        )

    # Adding it to the environment
    env.schedule(event_scheduled)

    """
    CONDITIONAL EVENTS
    """

    # Here we define our condition, which is when there as at least one event that already happened in the environment
    def condition(env: AbstractEnvironment) -> bool:
        return len(env.event_log) > 1

    # Here we write a condition check event
    condition_check = ConditionCheckEvent.from_condition(condition)

    # define the event that is going to happen, no need to specify time as the
    # condition triggering defines when it is going to happen
    event_triggered = Event.from_function(
        email.add_email,
        email=Email(
            sender="test@example.com",
            recipients=["test@example.com"],
            subject="Hello World, again !",
            content="Hello World, some event happened in the past ! WoW !",
        ),
    )

    # We make the event depend on the condition check event
    event_triggered.depends_on(condition_check)

    # we can also delay triggering where the event does not execute immediately
    # when condition is met, but after a delay
    event_triggered.depends_on(condition_check, delay_seconds=1)

    # Adding the condition check and the event to the environment
    env.schedule([event_triggered, condition_check])

    """
    AGENT EVENT
    """

    # Agent events happen while the environment is running, when App api calls are used
    # Let's start the environment

    env.start()

    # And now let's simulate an Agent doing stuff with the available App(s)

    for i in range(5):
        # Agent is idle, doing nothing
        time.sleep(1)

        # Agent doing stuff, obsessively reading the same email over and over again
        try:
            _ = email.get_email_by_index(idx=0)
        except Exception:
            print("No email to read")

    # Pausing the env
    env.pause()

    # checking the event queue
    for e in env.event_log.list_view():
        print(e)
        print("\n")


if __name__ == "__main__":
    main()
