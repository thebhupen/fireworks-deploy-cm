# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from functools import partial

from are.simulation.agents.agent_log import ToolCallLog
from are.simulation.agents.default_agent.base_agent import RunningState, TerminationStep
from are.simulation.agents.default_agent.tools.json_action_executor import (
    JsonActionExecutor,
)
from are.simulation.exceptions import MaxIterationsAgentError

logger: logging.Logger = logging.getLogger(__name__)


def termination_state_update(agent, tool_name: str | None = None):
    """
    Updates the running state of the agent based on the provided tool name.

    By default, sets the agent's running state to TERMINATED. If the tool name
    is "SystemApp__wait_for_notification", the running state is set to PAUSED, indicating
    that the agent is waiting for an event.

    Args:
        agent: The agent whose state is being updated.
        tool_name (Optional[str]): The name of the tool that may affect the agent's state.
    """
    # By default, we assume the agent is terminated
    agent.custom_state["running_state"] = RunningState.TERMINATED
    if tool_name and tool_name.strip() == "SystemApp__wait_for_notification":
        # If the agent is waiting for an event we pause it
        agent.custom_state["running_state"] = RunningState.PAUSED


def get_end_of_turn_termination_step():
    return TerminationStep(
        name="end_scenario",
        condition=termination_condition_are_simulation_send_message_to_user,
    )


def extract_final_answer(agent) -> str:
    tool_call = agent.get_last_log_of_type(ToolCallLog)
    tool_name = tool_call.tool_name if tool_call else ""
    if isinstance(agent.action_executor, JsonActionExecutor):
        if tool_name == "final_answer":
            return tool_call.tool_arguments.get("answer", "")

    return ""


def termination_condition_are_simulation_final_answer(agent):
    if agent.iterations >= agent.total_iterations:
        return True
    tool_call = agent.get_last_log_of_type(ToolCallLog)
    tool_name = tool_call.tool_name if tool_call else ""
    if isinstance(agent.action_executor, JsonActionExecutor):
        if tool_name == "final_answer":
            return True
    return False


def termination_step_are_simulation_final_answer():
    return TerminationStep(
        name="final_answer",
        condition=termination_condition_are_simulation_final_answer,
        function=extract_final_answer,  # type: ignore
    )


def termination_condition_are_simulation(agent, termination_tool_names: list[str]):
    """
    Determines if the agent should be terminated based on the last tool call and other conditions.

    This function checks the last tool call made by the agent and compares it against a list of
    termination tool names. If a match is found, or if certain conditions such as reaching the
    maximum number of iterations or receiving an environment stop message are met, the agent's
    state is updated to terminated.

    Args:
        agent: The agent whose termination condition is being evaluated.
        termination_tool_names (list[str]): A list of tool names that, if matched with the last
                                            tool call, will trigger the agent's termination.

    Returns:
        bool: True if the agent should be terminated, False otherwise.
    """
    tool_call = agent.get_last_log_of_type(ToolCallLog)
    tool_name = tool_call.tool_name if tool_call else ""
    if isinstance(agent.action_executor, JsonActionExecutor):
        if any(
            tool_name.strip() == agent.get_original_tool_name(target_tool_name).strip()
            for target_tool_name in termination_tool_names
        ):
            logger.info(f"TERMINATING AGENT DUE TO {tool_name}")
            termination_state_update(agent, tool_name=tool_name)
            logger.info(f"Agent state {agent.custom_state}")
            return True

    if agent.notification_system.message_queue.has_environment_stop_message():
        termination_state_update(agent)
        return True
    if agent.iterations >= agent.max_iterations:
        agent.send_message_to_user(
            content=f"Max iterations ({agent.max_iterations}) reached. Stopping."
        )
        print(
            "TERMINATING AGENT DUE TO AUTOMATED send_message_to_user (MAX ITERATIONS REACHED)"
        )
        agent.log_error(MaxIterationsAgentError())
        termination_state_update(agent)
        return True
    return False


termination_condition_are_simulation_send_message_to_user = partial(
    termination_condition_are_simulation,
    termination_tool_names=["AgentUserInterface__send_message_to_user"],
)

termination_condition_are_simulation_send_message_to_user_or_wait_for_notification = partial(
    termination_condition_are_simulation,
    termination_tool_names=[
        "AgentUserInterface__send_message_to_user",  # First check if the agent is sending a message to the user
        "SystemApp__wait_for_notification",
    ],
)


def get_gaia2_termination_step() -> TerminationStep:
    return TerminationStep(
        name="end_scenario",
        condition=termination_condition_are_simulation_send_message_to_user_or_wait_for_notification,
    )
