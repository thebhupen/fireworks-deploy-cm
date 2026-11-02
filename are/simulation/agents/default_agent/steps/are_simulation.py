# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from datetime import datetime, timezone

from are.simulation.agents.agent_log import (
    AgentUserInterfaceLog,
    EnvironmentNotificationLog,
)
from are.simulation.agents.default_agent.base_agent import ConditionalStep
from are.simulation.notification_system import Message, MessageType


def format_user_message(notif: Message):
    return f"{notif.message}"


def format_notification(notif: Message):
    return f"[{notif.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {notif.message}"


def pull_messages_from_notification_system(agent):
    """
    Pull messages from the notification system.
    """
    unhandled_notifications = agent.notification_system.message_queue.get_by_timestamp(
        timestamp=datetime.fromtimestamp(agent.make_timestamp(), tz=timezone.utc),
    )

    user_messages = []
    other_messages = []
    for notification in unhandled_notifications:
        if notification.message_type == MessageType.USER_MESSAGE:
            user_messages.append(notification)
        elif notification.message_type == MessageType.ENVIRONMENT_NOTIFICATION:
            other_messages.append(notification)

    if user_messages:
        agent.append_agent_log(
            AgentUserInterfaceLog(
                content="\n".join(
                    format_user_message(notif) for notif in user_messages
                ),
                timestamp=agent.make_timestamp(),
                agent_id=agent.agent_id,
            )
        )

    if other_messages:
        agent.append_agent_log(
            EnvironmentNotificationLog(
                content="\n".join(
                    format_notification(notif) for notif in other_messages
                ),
                timestamp=agent.make_timestamp(),
                agent_id=agent.agent_id,
            )
        )


def get_are_simulation_update_pre_step():
    return ConditionalStep(
        condition=None,
        function=pull_messages_from_notification_system,
        name="pull_messages_from_notification_system",
    )
