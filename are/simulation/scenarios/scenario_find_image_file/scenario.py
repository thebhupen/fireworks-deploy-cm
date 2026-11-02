# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import uuid

from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.apps.sandbox_file_system import SandboxLocalFileSystem
from are.simulation.scenarios.scenario import Scenario, ScenarioValidationResult
from are.simulation.scenarios.utils import validation_utils
from are.simulation.scenarios.utils.registry import register_scenario
from are.simulation.types import AbstractEnvironment, CapabilityTag, EventRegisterer


@register_scenario("scenario_find_image_file")
class ScenarioFindImageFile(Scenario):
    """A scenario that tests an agent's ability to explore a file system and identify image files.

    This scenario creates a sandbox environment with multiple text files and one image file,
    then asks the agent to find the image file. It demonstrates basic file exploration capabilities.

    The scenario follows the standard Meta Agents Research Environments pattern:

    1. **Environment Setup**: Creates a sandboxed file system with controlled content
    2. **Oracle Events**: Defines the expected interaction sequence for validation
    3. **Custom Validation**: Implements additional checks beyond oracle event matching
    """

    start_time: float | None = 0
    tags: tuple[CapabilityTag, ...] = (CapabilityTag.Exploration,)

    def init_and_populate_apps(self, *args, **kwargs) -> None:
        """Initialize and populate the apps with test data.

        This method sets up the scenario environment by:

        1. Creating a sandbox file system with controlled content
        2. Adding multiple distractor text files to make the task non-trivial
        3. Adding one target image file that the agent needs to find
        4. Setting up the agent-user interface for communication

        The scenario follows the standard Meta Agents Research Environments pattern of creating apps and populating
        them with initial data before the agent interaction begins.

        :param args: Positional arguments (unused)
        :param kwargs: Keyword arguments, may contain 'sandbox_dir'
        :type kwargs: dict
        :rtype: None
        """
        # Create a sandboxed file system - isolated from the real file system
        fs = SandboxLocalFileSystem(sandbox_dir=kwargs.get("sandbox_dir", None))

        # Create the communication interface between agent and user
        agent_user_interface = AgentUserInterface()

        # Create 10 random text files as distractors
        # These make the task more realistic by requiring the agent to distinguish
        # between different file types rather than just finding the only file
        for _ in range(10):
            random_file_name = str(uuid.uuid4()) + ".txt"
            fs.write_text(f"{random_file_name}", f"I am {random_file_name} !")

        # Create the target image file that the agent needs to find
        # Using .jpg extension and binary content to simulate a real image file
        fs.write_bytes("llama.jpg", b"I am a binary image !")

        # Register both apps with the environment
        # The agent will have access to both the file system and user interface
        self.apps = [fs, agent_user_interface]

    def build_events_flow(self) -> None:
        """Define the sequence of events that should occur during the scenario.

        This method creates the **oracle events** - the ground truth sequence of actions
        that represents the correct solution to the scenario. The judge system will
        compare the agent's actual actions against these oracle events to determine
        if the scenario was completed successfully.

        Oracle events serve two purposes:

        1. They define the expected interaction flow for validation
        2. They provide the ground truth for the judge system to compare against

        As described in the :doc:`../api_reference/judge_system` documentation, oracle events
        are used by judges like ``GraphPerEventJudge`` to perform event-level validation,
        comparing individual agent actions against these expected oracle actions.

        :rtype: None
        """
        # Get the agent-user interface app for creating communication events
        aui: AgentUserInterface = self.get_typed_app(AgentUserInterface)

        # This captures all events created within this context as the expected flow
        with EventRegisterer.capture_mode():
            # Environment/User event: User sends the initial request to the agent
            # This represents the starting point of the interaction
            user_request = (
                aui.send_message_to_agent(
                    content="I need to find the image file in the current directory",
                )
                .depends_on(
                    None, delay_seconds=0
                )  # No dependencies, starts immediately
                .with_id("user_request")  # Unique identifier for this oracle event
            )

            # oracle event: Agent should respond with the correct answer
            # This is marked as .oracle() to indicate it's the expected agent response
            # The judge system will look for an agent action that matches this oracle event
            oracle_response = (
                aui.send_message_to_user(
                    content="The image file is `llama.jpg`",
                )
                .with_id("oracle_response")  # Unique identifier for validation
                .oracle()  # Marks this as an oracle event the agent should perform
                .depends_on(
                    user_request, delay_seconds=1
                )  # Should happen after user request
            )

        # Store the oracle events for the scenario execution and validation
        # The judge system will use these events to validate agent performance
        self.events = [user_request, oracle_response]

    def validate(self, env: AbstractEnvironment) -> ScenarioValidationResult:
        """Validate that the scenario was completed successfully by the agent.

        This method implements custom validation logic that runs after the scenario
        execution to determine if the agent successfully completed the task. It works
        alongside the judge system's oracle event validation.

        The validate method serves as a final check and can be used for:

        1. Custom validation logic that goes beyond oracle event matching
        2. Fallback validation when oracle events might not capture all success criteria
        3. Additional checks on the final state of the environment

        As described in the :doc:`../tutorials/scenario_development` documentation, the validate method
        should return a ``ScenarioValidationResult`` indicating success or failure.
        The judge system may use this in combination with oracle event validation
        to make the final determination of scenario success.

        :param env: The environment containing all apps and their final state
        :type env: AbstractEnvironment
        :returns: Contains success boolean and optional exception info
        :rtype: ScenarioValidationResult
        """
        try:
            # Get the last message sent by the agent to the user
            # This checks the final output to see if the agent provided the correct answer
            res = validation_utils.get_last_message_from_agent(env)
        except Exception:
            # If we can't get the agent's message, treat it as empty string
            res = ""

        # Check if the agent's response contains the correct image filename
        # This validates that the agent successfully identified "llama.jpg" as the image file
        result = res is not None and "llama.jpg" in res

        return ScenarioValidationResult(result)


if __name__ == "__main__":
    from are.simulation.scenarios.utils.cli_utils import run_and_validate

    run_and_validate(ScenarioFindImageFile())
