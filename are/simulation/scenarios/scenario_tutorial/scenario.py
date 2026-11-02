# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import base64

from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.apps.calendar import CalendarApp
from are.simulation.apps.contacts import Contact, ContactsApp, Gender, Status
from are.simulation.apps.email_client import Email, EmailClientApp
from are.simulation.apps.messaging import MessagingApp
from are.simulation.apps.sandbox_file_system import SandboxLocalFileSystem
from are.simulation.apps.system import SystemApp
from are.simulation.data.population_scripts.sandbox_file_system_population import (
    default_fs_folders,
)
from are.simulation.scenarios.scenario import Scenario, ScenarioValidationResult
from are.simulation.scenarios.utils.registry import register_scenario
from are.simulation.types import Action, EventRegisterer, EventType


@register_scenario("scenario_tutorial")
class ScenarioTutorial(Scenario):
    # Define the start time and duration of the scenario
    start_time: float | None = 0
    duration: float | None = 20  # Scenario duration in seconds

    # Initialize and populate applications with data
    def init_and_populate_apps(self, *args, **kwargs) -> None:
        agui = AgentUserInterface()  # User interface for the agent
        calendar = CalendarApp()  # Calendar application
        email_client = EmailClientApp()  # Email client application
        contacts = ContactsApp()  # Contacts application
        fs = SandboxLocalFileSystem(
            sandbox_dir=kwargs.get("sandbox_dir", None)
        )  # File system application
        messaging = MessagingApp()  # Messaging application
        system = SystemApp()  # System application

        default_fs_folders(fs)  # Set up default folders in the file system

        # TODO: insert other population methods for additional applications if needed

        # Manually add specific contacts to the contacts application
        contacts.add_contact(
            Contact(
                first_name="John",
                last_name="Doe",
                phone="+33 345 678 9120",
                email="johndoe@example.com",
                gender=Gender.MALE,
                status=Status.EMPLOYED,
                age=20,
            )
        )

        contacts.add_contact(
            Contact(
                first_name="Greg",
                last_name="Barty",
                phone="+33 291 193 1892",
                email="gregb@example.com",
                gender=Gender.MALE,
                status=Status.EMPLOYED,
                age=27,
            )
        )

        # List of all initialized applications
        self.apps = [agui, calendar, email_client, contacts, fs, messaging, system]

    # Build the scenario by defining events and actions
    def build_events_flow(self) -> None:
        messaging = self.get_typed_app(MessagingApp)
        email_client = self.get_typed_app(EmailClientApp)
        aui = self.get_typed_app(AgentUserInterface)
        conv1_key = messaging.create_conversation(
            participants=["John Doe"],
            title="John Doe and I",
        )

        # Use capture_mode to create events using regular function calls from App api calls
        with EventRegisterer.capture_mode():
            # Define action1: Simulate receiving a message from John Doe
            # Event1 depends on the start of the simulation and is scheduled 5 seconds after the start
            event1 = messaging.add_message(
                conversation_id=conv1_key,
                sender="John Doe",
                content="Hey man how are you doing? Greg wanted to send me a pdf with the list of music we should listen to. He didn't manage to send it to me but will try to send it to you. Can you send it to me as soon as you get it?",
            ).depends_on(None, delay_seconds=5)

            # Define action2: Simulate receiving a message from Greg
            # Event2 depends on event1 and is scheduled 1 second after event1.
            event2 = aui.send_message_to_agent(
                content="Hey Assistant, can you take care of transferring the pdf Greg will send me to John? You can send it right away to John Doe.",
            ).depends_on(event1, delay_seconds=1)

            # Define action3: Simulate receiving a message from Greg
            # Event3 depends on event2 and is scheduled 10 seconds after event2.
            event3 = email_client.send_email_to_user(
                email=Email(
                    sender="gregb@example.com",
                    recipients=[email_client.user_email],
                    subject="List of music",
                    content="Hey man, here is attached the list of music you should listen to. I hope you like it.",
                    attachments={
                        "music.pdf": base64.b64encode(
                            b"This file contains a music list."
                        ),  # Encode the attachment in base64
                    },
                    email_id="greg_email",
                ),
            ).depends_on(event2, delay_seconds=10)

            # Define oracle1: Simulate the agent forwarding the email
            # Only scheduled in the oracle mode
            oracle1 = (
                email_client.forward_email(
                    email_id="greg_email",
                    recipients=["johndoe@example.com"],
                )
                .oracle()  # To indicate that this event is an oracle event
                .depends_on(event3, delay_seconds=1)
            )

        # Add all events to the scenario
        # Events will be executed in dependency order, not list order
        self.events = [event1, event2, event3, oracle1]

    def validate(self, env) -> ScenarioValidationResult:
        """
        Validate that the scenario was completed successfully.

        This method is called after the scenario execution to determine
        if the agent successfully completed the task. It should return
        a ScenarioValidationResult indicating success or failure.

        Args:
            env: The environment containing all apps and their final states

        Returns:
            ScenarioValidationResult with success status and optional exception
        """
        try:
            # Example validation: Check if the agent forwarded the PDF to John
            email_forwarded = any(
                event.event_type == EventType.AGENT
                and isinstance(event.action, Action)
                and event.action.function_name == "forward_email"
                and event.action.class_name == "EmailClientApp"
                and "johndoe@example.com" in event.action.args["recipients"]
                and event.action.args["email_id"] == "greg_email"
                for event in env.event_log.list_view()
            )
            return ScenarioValidationResult(success=email_forwarded)

        except Exception as e:
            # If validation fails due to an error, return failure with exception
            return ScenarioValidationResult(success=False, exception=e)


if __name__ == "__main__":
    from are.simulation.scenarios.utils.cli_utils import run_and_validate

    # Run the scenario in oracle mode and validate the agent actions
    run_and_validate(ScenarioTutorial())
