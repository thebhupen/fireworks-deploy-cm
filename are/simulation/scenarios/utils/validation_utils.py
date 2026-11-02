# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging

from are.simulation.apps.agent_user_interface import AgentUserInterface
from are.simulation.types import AbstractEnvironment, disable_events

logger: logging.Logger = logging.getLogger(__name__)


def get_last_message_from_agent(env: AbstractEnvironment) -> str | None:
    aui: AgentUserInterface = env.get_app(AgentUserInterface.__name__)
    try:
        with disable_events():
            last_message = aui.get_last_message_from_agent()
            return last_message.content if last_message is not None else None
    except Exception as e:
        logger.error(f"Failed to get last message from agent: {e}")
        return None
