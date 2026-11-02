# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging

from are.simulation.agents.agent_log import ActionLog, BaseAgentLog, StepLog
from are.simulation.apps import AgentUserInterface
from are.simulation.environment import Environment
from are.simulation.utils import truncate_string

logger = logging.getLogger(__name__)


def replay_logs(world_logs: list[BaseAgentLog], env: Environment) -> None:
    if env is None:
        logger.error("Cannot replay logs, Environment is None.")
        return

    logger.info(f"Replaying {len(world_logs)} agent logs.")

    aui = env.apps.get(AgentUserInterface.__name__, None)

    if aui is None:
        logger.error("Cannot replay, AgentUserInterface not found.")
        return

    # During replay, we don't want to wait for user input.
    env.set_is_replaying(True)
    aui.set_wait_for_user_response(False)

    for log in world_logs:
        env.time_manager.reset(start_time=log.timestamp)

        if not isinstance(log, ActionLog):
            logger.debug(
                f"Nothing to replay in log {truncate_string(log)} because it is not an ActionLog, it is of type {type(log)}."
            )
            continue

        action_name = log.action_name
        action_args = log.input
        app_name = log.app_name
        app = env.apps.get(log.app_name, None)

        if app is None:
            logger.error(
                f"Could not replay {action_name} because app {app_name} was not found."
            )
            continue

        action = getattr(app, action_name, None)

        if action is None:
            logger.error(
                f"Could not replay {action_name} because the method was not found in app {app_name}."
            )
            continue

        try:
            logger.info(f"Replaying {action_name} with input {action_args}.")
            action(**action_args)
        except Exception as e:
            logger.error(
                f"Failed to replay {action_name} with input {log.input} because an exception was raised: {e}."
            )
            continue

    # After we have replayed events, re-enable waiting for user input
    aui.set_wait_for_user_response(True)
    env.set_is_replaying(False)

    # Now that we have replayed all the events, we can set the environment world logs
    env.set_world_logs(world_logs)

    # Clear all notifications from the existing notification system
    env.notification_system.clear()


def find_log_position(
    world_logs: list[BaseAgentLog], log_id: str, log_types=None
) -> int:
    return next(
        (
            i
            for i, log in enumerate(world_logs)
            if log.id == log_id and (log_types is None or isinstance(log, log_types))
        ),
        -1,
    )


def find_previous_step_position(
    world_logs: list[BaseAgentLog], start_position: int
) -> int:
    return next(
        (
            i
            for i in range(start_position - 1, -1, -1)
            if isinstance(world_logs[i], StepLog)
        ),
        -1,
    )
