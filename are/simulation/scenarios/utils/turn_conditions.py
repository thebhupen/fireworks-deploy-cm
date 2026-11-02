# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from functools import partial
from typing import Callable

logger = logging.getLogger(__name__)
from are.simulation.types import (
    AbstractEnvironment,
    AbstractEvent,
    CompletedEvent,
    ConditionCheckEvent,
    EventType,
    ExecutionMetadata,
    OracleEvent,
    PlaceholderMetadata,
)


def is_send_message_to_user(event: AbstractEvent) -> bool:
    """
    Check if the event is a send message to user event
    """
    return (
        isinstance(event, OracleEvent)
        and event.action_desc
        and event.action_desc.app == "AgentUserInterface"
        and event.action_desc.function == "send_message_to_user"
    ) or (
        isinstance(event, CompletedEvent)
        and event.event_type == EventType.AGENT
        and event.action
        and event.action.function_name == "send_message_to_user"
        and event.action.class_name == "AgentUserInterface"
    )


def is_conditional_event(event: AbstractEvent) -> bool:
    """
    Check if the event is a conditional event
    """
    return isinstance(event, ConditionCheckEvent)


def turn_condition_wrapper(
    trigger_condition: Callable[
        [AbstractEnvironment, int], tuple[bool, dict[str, str]]
    ],
    turn_idx: int,
    scenario_id: str,
) -> Callable[[AbstractEnvironment], bool]:
    """
    Wrapper around a condition to check if the turn is reached.
    The trigger condition is evaluated only if the right turn is reached.
    If the condition failed, the environment is stopped.
    The environment is paused while the trigger condition is evaluated.
    """

    def wrapped_condition(env: AbstractEnvironment) -> bool:
        # Count the number of send message to user events
        nb_send_message_to_user = sum(
            1 for event in env.event_log.list_view() if is_send_message_to_user(event)
        )
        # Check if the right turn is reached
        if nb_send_message_to_user == turn_idx:
            # Pause the environment
            env.pause()
            # Check the trigger condition
            move_to_next_turn, event_id_to_oracle_event_id = trigger_condition(
                env, turn_idx
            )
            # Update matched event ids to oracle event ids for future place holder replacement.
            for event in env.event_log.list_view():
                if not event.failed() and event.event_id in event_id_to_oracle_event_id:
                    logger.warning(
                        f"Replacing event id {event.event_id} with id {event_id_to_oracle_event_id[event.event_id]} for future placeholder resolution."
                    )
                    event.event_id = event_id_to_oracle_event_id[event.event_id]
            # Resume the environment
            env.resume()
            if not move_to_next_turn:
                # Stop the environment
                env.stop()  # type: ignore
                # Return True to not create another check event
                return True
            # Move to the next turn
            return True
        # Wait for the agent to send a message to the user
        return False

    wrapped_condition.__name__ = (
        f"wrapped_condition__turn_idx_{turn_idx}__scenario_id_{scenario_id}"
    )
    return wrapped_condition


def basic_placeholder_mapper(
    placeholders: list[PlaceholderMetadata],
    events: list[CompletedEvent],
) -> dict[str, str]:
    """
    Maps event IDs to oracle event IDs based on placeholders and events.

    :placeholders PlaceholderMetadata: A list of PlaceholderMetadata.
    events CompletedEvent: A list of CompletedEvent objects to be processed.
    :returns: A dictionary mapping event IDs to oracle event IDs.
    """
    # Construct a mapping from (tool_name, turn_idx) to oracle_event_id
    placeholders_dict = {
        (
            placeholder.parent_tool_name,
            placeholder.parent_turn_idx,
        ): placeholder.parent_event_id
        for placeholder in placeholders
    }
    if len(placeholders_dict) == 0:
        return {}
    # Construct event_id to oracle_event_id mapping
    turn_idx = 0
    event_id_to_oracle_event_id = {}
    for event in sorted(events, key=lambda x: x.event_time):  # type: ignore
        if event.event_type == EventType.AGENT and event.action:
            tool_name = f"{event.action.app_name}__{event.action.function_name}"
            if (tool_name, turn_idx) in placeholders_dict:
                event_id_to_oracle_event_id[event.event_id] = placeholders_dict[
                    (tool_name, turn_idx)
                ]
        if is_send_message_to_user(event):
            turn_idx += 1
    return event_id_to_oracle_event_id


def dummy_trigger_condition(
    env: AbstractEnvironment,
    turn_idx: int,
    execution_metadata: ExecutionMetadata,
) -> tuple[bool, dict[str, str]]:
    """
    Dummy trigger condition that always returns True
    It uses the cached tool name to oracle event id mapping to replace the placeholders.
    """

    # Check if the env is running a scenario with placeholders that cannot be replaced
    if execution_metadata.has_placeholder_conflicts:
        logger.error(
            "Scenario has placeholder conflicts. It cannot be run in offline mode!"
        )
    # Replace the placeholders with the oracle event ids
    event_id_to_oracle_event_id = basic_placeholder_mapper(
        placeholders=execution_metadata.placeholders,
        events=env.event_log.list_view(),
    )

    return True, event_id_to_oracle_event_id


def condition_from_name(
    condition_fn_name: str, execution_metadata: ExecutionMetadata
) -> Callable[[AbstractEnvironment], bool]:
    """
    Get the wrapped condition from the name
    """
    if not condition_fn_name.startswith("wrapped_condition__turn_idx_"):
        raise NotImplementedError(
            f"Condition {condition_fn_name} is not supported yet."
        )
    if execution_metadata is None:
        raise ValueError("Execution metadata is None.")

    # Extract turn_idx and scenario_id from the function name
    # Format: wrapped_condition__turn_{turn_idx}__scenario_{scenario_id}
    parts = condition_fn_name.split("__")
    if (
        len(parts) != 3
        or not parts[1].startswith("turn_idx_")
        or not parts[2].startswith("scenario_id_")
    ):
        raise ValueError(f"Invalid condition function name format: {condition_fn_name}")

    turn_idx = int(parts[1].replace("turn_idx_", ""))
    scenario_id = parts[2].replace("scenario_id_", "")

    return turn_condition_wrapper(
        turn_idx=turn_idx,
        trigger_condition=partial(
            dummy_trigger_condition,
            execution_metadata=execution_metadata,
        ),
        scenario_id=scenario_id,
    )
