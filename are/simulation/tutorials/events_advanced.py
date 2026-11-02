# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import random

from are.simulation.apps.email_client import Email, EmailClientApp
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.types import (
    AbstractEnvironment,
    AbstractEvent,
    AgentValidationEvent,
    ConditionCheckEvent,
    Event,
    EventRegisterer,
)


def example():
    email = EmailClientApp()
    start_time = 100

    env = Environment(EnvironmentConfig(start_time=start_time, duration=10))
    env.register_apps([email])

    # We use capture mode here to easily create events by just calling the app functions
    with EventRegisterer.capture_mode():
        # e1 is scheduled immediately at start_time, so it is equivalent to just populating the App
        e1 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=["receiver@example.com"],
                subject="Test Email 1 ",
                content="This is a test email. Number 1",
            )
        )

        # e2 is scheduled at start_time + 3 seconds
        e2 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=["receiver@example.com"],
                subject="Test Email 2 ",
                content="This is a test email. Number 2",
            )
        ).depends_on(None, delay_seconds=3)

        # e3 is scheduled at start_time as well for now, but we will see later that by making it depend on other events
        # it will be scheduled at a later time
        e3 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=["receiver@example.com"],
                subject="Test Email 3 ",
                content="This is a test email. Number 3",
            )
        )

        # e4 is also scheduled immediately at start_time, so it is equivalent to just populating the App
        e4 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=["receiver@example.com"],
                subject="Test Email 4 ",
                content="This is a test email. Number 4",
            )
        )

        # e5 is scheduled at start_time as well for now, but we will see later that by making it depend on other events
        # it will be scheduled at a later time
        e5 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=["receiver@example.com"],
                subject="Test Email 5 ",
                content="This is a test email. Number 5",
            )
        )

    # Here we create a condition check event, this event will be scheduled at start_time and rescheduled every tick
    # Until the condition is met and then
    random_condition_check = ConditionCheckEvent.from_condition(
        lambda env: random.random() > 0.5
    )

    # We can also schedule a verification event after e3 to check if a write action was performed in the 20 seconds
    # after e3 was executed
    # If the condition is not met in the given time, the event will fail and stop the simulation
    def val_func(env: AbstractEnvironment, event: AbstractEvent) -> bool:
        return (
            isinstance(event, Event)
            and event.function_name() == "send_message_to_user"
            and event.action.args["content"] == "I am a robot"
        )

    validation_event = (
        AgentValidationEvent(milestones=[val_func], timeout=10)
        .with_id("val1")
        .depends_on([e3])
    )

    # We can make events depend on other events, and specify a delay
    # delay means that the event will be scheduled at the time of the dependency + the delay
    e3.depends_on([e1, e2], delay_seconds=5)
    e5.depends_on([random_condition_check, e4], delay_seconds=2)

    # We schedule all the defined events
    env.schedule([e1, e2, e3, e4, e5, random_condition_check, validation_event])
    # We could have specified only e3 and e5 here, their dependencies would have been automatically added
    # env.schedule([e3, e5])

    # We start the environment
    env.start()
    env.join()

    # We can check the event log to see what happened
    print("Event log:")
    for event in env.event_log.list_view():
        print(event)
        print("\n")


if __name__ == "__main__":
    example()
