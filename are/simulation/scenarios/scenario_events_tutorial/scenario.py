# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Events Tutorial Scenario

This scenario demonstrates the fundamental concepts of events in Meta Agents Research Environments:
1. Scheduled Events - Events that happen at specific times
2. Conditional Events - Events triggered by conditions
3. Event Dependencies - How events can depend on other events
4. Different event creation patterns

The scenario simulates an email workflow where:
- Initial emails are sent at scheduled times
- A conditional event triggers when enough emails are received
- The agent should respond appropriately to the email flow
"""

from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.apps.email_client import Email, EmailClientApp, EmailFolderName
from are.simulation.scenarios.scenario import Scenario, ScenarioValidationResult
from are.simulation.scenarios.utils.registry import register_scenario
from are.simulation.types import AbstractEnvironment, ConditionCheckEvent, Event


@register_scenario("scenario_events_tutorial")
class ScenarioEventsTutorial(Scenario):
    """
    Tutorial scenario demonstrating different types of events and their usage patterns.

    This scenario teaches:
    - How to create scheduled events with specific timing
    - How to create conditional events that trigger based on environment state
    - How to chain events with dependencies
    - Different syntactic patterns for event creation
    """

    start_time: float | None = 0
    duration: float | None = 30

    def init_and_populate_apps(self, *args, **kwargs) -> None:
        """Initialize apps for the events tutorial."""
        # Create the apps we'll use
        self.email_app = EmailClientApp()
        self.aui_app = AgentUserInterface()

        # Register apps with the scenario
        self.apps = [self.email_app, self.aui_app]

    def build_events_flow(self) -> None:
        """
        Build a flow of events demonstrating different event patterns.
        """

        # === SCHEDULED EVENTS ===
        # These events happen at specific times

        # Pattern 1: Using Event.from_function with depends_on
        scheduled_email_1 = Event.from_function(
            self.email_app.add_email,
            email=Email(
                sender="tutorial@example.com",
                recipients=[self.email_app.user_email],
                subject="Welcome to Events Tutorial",
                content="This email demonstrates a scheduled event that happens 2 seconds after start.",
            ),
        ).depends_on(None, delay_seconds=2)

        # Pattern 2: Using the delayed syntax (alternative)
        scheduled_email_2 = Event.from_function(
            self.email_app.add_email,
            email=Email(
                sender="tutorial@example.com",
                recipients=[self.email_app.user_email],
                subject="Second Scheduled Email",
                content="This email demonstrates the delayed() syntax, arriving 5 seconds after start.",
            ),
        ).delayed(5)

        # Pattern 3: Absolute time scheduling (for demonstration)
        # Note: This would only work if the simulation runs long enough
        future_time = (self.start_time or 0) + 15
        scheduled_email_3 = Event.from_function(
            self.email_app.add_email,
            email=Email(
                sender="tutorial@example.com",
                recipients=[self.email_app.user_email],
                subject="Absolutely Timed Email",
                content="This email was scheduled for an absolute time (15 seconds after start).",
            ),
        ).at_absolute_time(future_time)

        # === CONDITIONAL EVENTS ===
        # These events trigger when certain conditions are met

        def enough_emails_condition(env: AbstractEnvironment) -> bool:
            """Condition: trigger when we have at least 2 emails"""
            email_app = env.get_app("EmailClientApp")
            return len(email_app.folders[EmailFolderName.INBOX].emails) >= 2

        # Create a condition check event
        condition_check = ConditionCheckEvent.from_condition(enough_emails_condition)

        # Event that triggers when condition is met
        conditional_email = Event.from_function(
            self.email_app.add_email,
            email=Email(
                sender="system@example.com",
                recipients=[self.email_app.user_email],
                subject="Conditional Event Triggered!",
                content="This email was sent because the condition (2+ emails) was met!",
            ),
        ).depends_on(condition_check, delay_seconds=1)

        # === USER INTERACTION EVENT ===
        # Simulate user asking agent to summarize emails
        user_request = Event.from_function(
            self.aui_app.send_message_to_agent,
            content="Please count how many emails I have received and tell me about them.",
        ).depends_on(conditional_email, delay_seconds=2)

        # Simulate the agent responding to the user's request
        agent_response = (
            Event.from_function(
                self.aui_app.send_message_to_user,
                content="You have received 4 emails.",
            )
            .oracle()
            .depends_on(user_request, delay_seconds=2)
        )

        # Add all events to the scenario
        self.events = [
            scheduled_email_1,
            scheduled_email_2,
            scheduled_email_3,
            condition_check,
            conditional_email,
            user_request,
            agent_response,
        ]

    def validate(self, env: AbstractEnvironment) -> ScenarioValidationResult:
        """
        Validate that the events tutorial completed successfully.

        We check that:
        1. All scheduled emails were delivered
        2. The conditional email was triggered
        3. The agent responded to the user's request
        """
        try:
            email_app = env.get_app("EmailClientApp")
            aui_app = env.get_app("AgentUserInterface")

            # Check that we have the expected emails
            all_emails = email_app.folders[EmailFolderName.INBOX].emails
            expected_subjects = [
                "Welcome to Events Tutorial",
                "Second Scheduled Email",
                "Absolutely Timed Email",
                "Conditional Event Triggered!",
            ]

            # Check that all expected subjects are present
            received_subjects = [email.subject for email in all_emails]
            emails_received = all(
                subject in received_subjects for subject in expected_subjects
            )
            conditional_triggered = any(
                "Conditional Event Triggered" in email.subject for email in all_emails
            )

            # Check if agent responded to user request
            agent_messages = aui_app.get_all_messages_from_agent()
            agent_responded = len(agent_messages) > 0

            success = emails_received and conditional_triggered and agent_responded
            return ScenarioValidationResult(success=success)

        except Exception as e:
            return ScenarioValidationResult(success=False, exception=e)


if __name__ == "__main__":
    from are.simulation.scenarios.utils.cli_utils import run_and_validate

    # Run the scenario in oracle mode and validate the agent actions
    run_and_validate(ScenarioEventsTutorial())
