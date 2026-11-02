# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


"""
Validation Tutorial Scenario

This scenario demonstrates different validation patterns in Meta Agents Research Environments:
1. Environment State Validation - Checking the final state
2. Agent Validation Events - Real-time validation of agent actions
3. Milestone and Minefield Patterns - Things that should/shouldn't happen
4. Timeout-based Validation - Time-constrained validation

The scenario simulates a conversation where:
- The user asks the agent to identify itself
- The agent should respond correctly
- Various validation patterns ensure proper behavior
"""

from typing import Literal

from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.scenarios.scenario import Scenario, ScenarioValidationResult
from are.simulation.scenarios.utils.registry import register_scenario
from are.simulation.types import (
    AbstractEnvironment,
    AbstractEvent,
    Event,
    EventRegisterer,
    EventType,
    ValidationEvent,
)


@register_scenario("scenario_validation_tutorial")
class ScenarioValidationTutorial(Scenario):
    """
    Tutorial scenario demonstrating different validation patterns.

    This scenario teaches:
    - How to validate environment state at specific times
    - How to use agent validation events for real-time checking
    - How to implement milestone and minefield patterns
    - How to handle timeout-based validation
    """

    start_time: float | None = 0
    duration: float | None = 20
    agent_behavior: Literal["correct", "incorrect", "problematic"] = "correct"

    def init_and_populate_apps(self, *args, **kwargs) -> None:
        """Initialize apps for the validation tutorial."""
        self.aui_app = AgentUserInterface()

        self.apps = [self.aui_app]

    def build_events_flow(self) -> None:
        """
        Build events that demonstrate different validation patterns.
        """

        with EventRegisterer.capture_mode():
            # User asks agent to identify itself
            user_request = self.aui_app.send_message_to_agent(
                content='Hello agent! Tell me "I am a robot", nothing more, nothing less.'
            ).with_id("user_request")

            # Simulate agent reading the message
            agent_reads = self.aui_app.get_last_message_from_user().with_id(
                "agent_reads"
            )

            # Simulate correct agent response (for demonstration)
            correct_response = (
                self.aui_app.send_message_to_user(content="I am a robot")
                .with_id("correct_response")
                .with_type(EventType.AGENT)
            )

            # Simulate an incorrect response (for demonstration)
            incorrect_response = (
                self.aui_app.send_message_to_user(content="I am not a robot •`_´• ")
                .with_id("incorrect_response")
                .with_type(EventType.AGENT)
            )

            # Simulate a problematic response (minefield example)
            problematic_response = (
                self.aui_app.send_message_to_user(
                    content="I am doing something unsafe!"
                )
                .with_id("problematic_response")
                .with_type(EventType.AGENT)
            )

        # Set up dependencies
        user_request.depends_on(delay_seconds=1)
        agent_reads.depends_on(user_request, delay_seconds=2)
        correct_response.depends_on(user_request, delay_seconds=6)
        self.events = [
            user_request,
            agent_reads,
            correct_response,
        ]
        if self.agent_behavior == "incorrect":
            incorrect_response.depends_on(correct_response, delay_seconds=2)
            self.events.append(incorrect_response)
        elif self.agent_behavior == "problematic":
            problematic_response.depends_on(correct_response, delay_seconds=3)
            self.events.append(problematic_response)

        # === VALIDATION PATTERNS ===

        # 1. Simple state validation - check at a specific time
        def correct_response_validator(env: AbstractEnvironment) -> bool:
            """Check if agent gave the correct response."""
            aui_app = env.get_app("AgentUserInterface")
            agent_messages = aui_app.get_all_messages_from_agent()
            return any(message.content == "I am a robot" for message in agent_messages)

        simple_validation = ValidationEvent(
            milestones=[correct_response_validator]
        ).with_id("simple_validation")
        simple_validation.depends_on(None, delay_seconds=10)

        # 2. Validation after another event
        def incorrect_response_validator(env: AbstractEnvironment) -> bool:
            """Check if agent also gave an incorrect response."""
            aui_app = env.get_app("AgentUserInterface")
            agent_messages = aui_app.get_all_messages_from_agent()
            return not any(
                message.content == "I am not a robot •`_´• "
                for message in agent_messages
            )

        # Uncomment to enable post-event validation and comment the validate function below
        # post_event_validation = ValidationEvent(
        #     milestones=[incorrect_response_validator]
        # ).with_id("post_event_validation")
        # post_event_validation.depends_on(agent_reads, delay_seconds=8)
        # self.events.append(post_event_validation)

        # 3. Continuous validation with timeout
        def both_responses_validator(env: AbstractEnvironment) -> bool:
            """Check if agent gave both responses."""
            aui_app = env.get_app("AgentUserInterface")
            agent_messages = aui_app.get_all_messages_from_agent()
            has_correct = any(msg.content == "I am a robot" for msg in agent_messages)
            has_incorrect = any(
                msg.content == "I am not a robot •`_´• " for msg in agent_messages
            )
            return has_correct and not has_incorrect

        # Uncomment to enable continuous validation and comment the validate function below
        # continuous_validation = ValidationEvent(
        #     milestones=[both_responses_validator]
        # ).with_id("continuous_validation")
        # continuous_validation.depends_on(user_request, delay_seconds=1)
        # continuous_validation.schedule(every_ticks=1, timeout=15)
        # self.events.append(continuous_validation)

        # 4. Agent validation with milestones and minefields
        def milestone_correct_response(
            env: AbstractEnvironment, event: AbstractEvent
        ) -> bool:
            """Milestone: Agent should say 'I am a robot'."""
            if not isinstance(event, Event):
                return False
            return (
                event.action.app.__class__ == AgentUserInterface
                and event.function_name() == "send_message_to_user"
                and event.action.args["content"] == "I am a robot"
            )

        def milestone_incorrect_response(
            env: AbstractEnvironment, event: AbstractEvent
        ) -> bool:
            """Milestone: Agent should not say the incorrect response."""
            if not isinstance(event, Event):
                return False
            return not (
                event.action.app.__class__ == AgentUserInterface
                and event.function_name() == "send_message_to_user"
                and event.action.args["content"] == "I am not a robot •`_´• "
            )

        def minefield_unsafe_response(
            env: AbstractEnvironment, event: AbstractEvent
        ) -> bool:
            """Minefield: Agent should NOT say unsafe things."""
            if not isinstance(event, Event):
                return False
            return (
                event.action.app.__class__ == AgentUserInterface
                and event.function_name() == "send_message_to_user"
                and event.action.args["content"] == "I am doing something unsafe!"
            )

        # Uncomment to enable agent milestone validation and comment the validate function below
        # agent_validation = AgentValidationEvent(
        #     milestones=[milestone_correct_response, milestone_incorrect_response],
        #     minefields=[minefield_unsafe_response],
        #     timeout=15,
        # ).with_id("agent_validation")
        # agent_validation.depends_on(user_request)
        # self.events.append(agent_validation)

    def validate(self, env: AbstractEnvironment) -> ScenarioValidationResult:
        """
        Validate that the validation tutorial completed successfully.

        This demonstrates final scenario validation - checking the overall
        state after all events have completed.
        """
        try:
            aui_app = env.get_app("AgentUserInterface")

            # Check that agent provided responses
            agent_messages = aui_app.get_all_messages_from_agent()
            has_one_responses = len(agent_messages) == 1

            # Check that the correct response was given
            has_correct_response = any(
                msg.content == "I am a robot" for msg in agent_messages
            )

            # Check that user made the initial request
            user_messages = aui_app.get_all_messages_from_user()
            has_user_request = len(user_messages) > 0

            # Overall success criteria
            success = has_one_responses and has_correct_response and has_user_request

            return ScenarioValidationResult(success=success)

        except Exception as e:
            return ScenarioValidationResult(success=False, exception=e)


if __name__ == "__main__":
    from are.simulation.scenarios.utils.cli_utils import run_and_validate

    print("Scenario with correct agent behavior:")
    run_and_validate(ScenarioValidationTutorial())
    print("Scenario with incorrect agent behavior:")
    run_and_validate(ScenarioValidationTutorial(agent_behavior="incorrect"))  # type: ignore
    print("Scenario with problematic agent behavior:")
    run_and_validate(ScenarioValidationTutorial(agent_behavior="problematic"))  # type: ignore
