# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from are.simulation.apps import AgentUserInterface
from are.simulation.apps.email_client import Email, EmailClientApp, EmailFolderName
from are.simulation.environment import (
    AbstractEnvironment,
    Environment,
    EnvironmentConfig,
)
from are.simulation.types import (
    AbstractEvent,
    AgentValidationEvent,
    ConditionCheckEvent,
    Event,
    EventRegisterer,
    EventType,
)
from are.simulation.utils import helper_delay_range


def val1_func(env: AbstractEnvironment, event: AbstractEvent) -> bool:
    email = env.get_app(EmailClientApp.__name__)
    aui = env.get_app(AgentUserInterface.__name__)
    val = isinstance(event, Event) and all(
        [
            event.action.app == aui,
            event.function_name() == "send_message_to_user",
            event.action.args["content"] == "You received 3 emails",
            len(email.folders[EmailFolderName.INBOX].emails) >= 3,
        ]
    )
    if val:
        print(f"Validation passed because of agent event with id {event.event_id}")
    return val


def example():
    email = EmailClientApp()
    aui = AgentUserInterface()
    start_time = 0

    # The environment will start at start_time = 0 seconds and will last for 60 seconds.
    # After 60 seconds, the environment will stop and the simulation will end.

    # Add example where we set start date!
    # If we want to start on the 1st of January 2023 at 00:00:00, we can do the following:
    # start_time = datetime.datetime(2023, 1, 1, 0, 0, 0).timestamp()

    # Turn the oracle mode on to simulate an agent that takes all the right decisions
    env = Environment(
        EnvironmentConfig(start_time=start_time, duration=60, oracle_mode=True)
    )
    env.register_apps([email, aui])

    # We use capture mode here to easily create events by just calling the app functions
    with EventRegisterer.capture_mode():
        aui1 = aui.send_message_to_agent(
            content="Hello ARE_SIMULATION, send me a message when I receive more than 3 emails"
        ).with_id("aui1")

        e1 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=[email.user_email],
                subject="Test Email 1 ",
                content="This is a test email. Number 1",
            )
        ).with_id("e1")

        e2 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=[email.user_email],
                subject="Test Email 2 ",
                content="This is a test email. Number 2",
            )
        ).with_id("e2")

        e3 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=[email.user_email],
                subject="Test Email 3 ",
                content="This is a test email. Number 3",
            )
        ).with_id("e3")

        e4 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=[email.user_email],
                subject="Test Email 4 ",
                content="This is a test email. Number 4",
            )
        ).with_id("e4")

        e5 = email.add_email(
            email=Email(
                sender="sender@example.com",
                recipients=[email.user_email],
                subject="Test Email 5 ",
                content="This is a test email. Number 5",
            )
        ).with_id("e5")

        validation = AgentValidationEvent(
            milestones=[val1_func],
        ).with_id("validation")

        aui2 = (
            aui.send_message_to_user(content="You received 3 emails")
            .with_id("aui2")
            .with_type(EventType.AGENT)
        )

    def condition_3_emails(env: AbstractEnvironment) -> bool:
        # We check that 3 emails were received after the aui1 event
        log = env.event_log.list_view()
        # get all the events after the aui1 event
        msg_agent_events = [
            e for e in log if e.action.function.__name__ == "send_message_to_agent"
        ]
        if len(msg_agent_events) == 0:
            return False
        aui1_event_time = msg_agent_events[0].event_time
        emails = [
            e
            for e in log
            if e.action.function.__name__ == "add_email"
            and e.event_time is not None
            and aui1_event_time is not None
            and e.event_time >= aui1_event_time
        ]
        return len(emails) >= 3

    # Here e1 depends on the start and is scheduled after a random delay between 10 and 15 seconds
    e1.depends_on(None, delay_seconds=helper_delay_range(10, 15, unit="sec"))
    # Here e2 depends on e1 and is scheduled after a random delay between 1 and 5 seconds after e1
    e2.depends_on(e1, delay_seconds=helper_delay_range(1, 5, unit="sec"))
    # Here e3 and e4 depend on e2 and are scheduled after a random delay between 1 and 10 seconds after e2
    e3.depends_on(e2, delay_seconds=helper_delay_range(1, 10, unit="sec"))
    e4.depends_on(e2, delay_seconds=helper_delay_range(1, 10, unit="sec"))

    # Here e5 depends on e3 and e4 and is scheduled after a random delay between 1 and 15 seconds
    # It is important to note that e5 will be scheduled after e3 and e4 are both executed
    e5.depends_on(
        [e3, e4],
        delay_seconds=helper_delay_range(1, 15, unit="sec"),
    )

    # Here aui1 depends on nothing (so the start of the sim) and is scheduled after a delay of 6 seconds
    aui1.depends_on(delay_seconds=6)

    # Here we create a condition check event, this event will be scheduled at start_time and rescheduled every tick
    # until the condition is met or the end of the simulation
    condition_check = ConditionCheckEvent.from_condition(condition_3_emails).with_id(
        "condition"
    )
    # We only start checking the number of emails after the agent has been notified by the user
    condition_check.depends_on([aui1])

    # We create a validation event that will be scheduled after the condition check event is met
    # it will check every tick (every second) that the user was notified and will fail if the user was not notified
    # after a delay of 20 seconds

    validation.depends_on(condition_check, schedule_every_ticks=1, timeout=10)
    aui2.depends_on(condition_check, delay_seconds=helper_delay_range(1, 5))

    # We schedule the events
    env.schedule([e1, e2, e3, e4, e5, aui1, condition_check, validation, aui2])

    # We start the environment
    env.start()
    env.join()


if __name__ == "__main__":
    example()
