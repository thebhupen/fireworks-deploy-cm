# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import textwrap

NOTIFICATION_SYSTEM_PROMPTS = {
    "NotificationSystem": textwrap.dedent(
        """
      Notification policy:
      - All new messages from the User will be notified to you.
      - The environment state may also change over time, but environment events will not be notified to you.
      - You can also proactively check for any other update in an App by using the tools given to you.
      - If a call to SystemApp__wait_for_notification times out, you will receive a notification.
      """
    ),
    "VerboseNotificationSystem": textwrap.dedent(
        """
    Notification policy:
    - All new messages from the User will be notified to you.
    - Whenever the environment is updated with any of the following tools, you will receive a notification: {notified_tools_list}.
    - You can also proactively check for any other update in an App by using the tools given to you.
    - If a call to SystemApp__wait_for_notification times out, you will receive a notification.
    """
    ),
}


def get_notification_system_prompt(notification_system, apps):
    if len(notification_system.config.notified_tools) == 0:
        prompt_template = NOTIFICATION_SYSTEM_PROMPTS["NotificationSystem"]
    else:
        prompt_template = NOTIFICATION_SYSTEM_PROMPTS["VerboseNotificationSystem"]

    notified_tools_list = []
    if apps:
        for app in apps:
            if app.name in notification_system.config.notified_tools:
                tools_to_add = notification_system.config.notified_tools[app.name]
                tools_to_add = [f"{app.name}__{tool}" for tool in tools_to_add]
                notified_tools_list.extend(tools_to_add)
    prompt = prompt_template.format(notified_tools_list=", ".join(notified_tools_list))
    return prompt
