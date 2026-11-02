# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from are.simulation.apps import App
from are.simulation.apps.agent_user_interface import AUIMessage, Sender
from are.simulation.tool_utils import OperationType, app_tool
from are.simulation.types import event_registered


class AppAgent(App):
    # an app with a single tool: expert_agent that itself has all the tools of the app
    def __init__(
        self,
        app_agent,
        tools,
        name,
    ) -> None:
        super().__init__()
        self.name = name
        self.app_agent = app_agent
        self.app_agent.tools = tools

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def expert_agent(self, task: str) -> str:
        """
        This will send a message to an expert Agent for the app.
        Ask them to complete any specific tasks that you know require the app.
        If you need a specific output, please specify it and do not forget to mention the format. Otherwise, just ask them to call the final_answer tool with the text 'task completed'.
        Note that:
            - The expert Agent may make mistakes, so you may want to check if they have accomplished the required task.
            - Once a task is send to the expert Agent you will not be able to communicate with them.
        """
        timestamp = self.time_manager.time()
        task = str(
            AUIMessage(
                sender=Sender.USER,
                content=task,
                timestamp=timestamp,
                time_read=timestamp,
            )
        )
        answer = self.app_agent.run(task=task)
        return str(answer)
