# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from abc import ABC

from are.simulation.agents.agent_execution_result import AgentExecutionResult
from are.simulation.agents.agent_log import BaseAgentLog
from are.simulation.notification_system import BaseNotificationSystem
from are.simulation.scenarios.scenario import Scenario

logger = logging.getLogger(__name__)


class AgentStoppedException(Exception):
    pass


class RunnableARESimulationAgent(ABC):
    def run_scenario(
        self,
        scenario: Scenario,
        notification_system: BaseNotificationSystem | None,
        initial_agent_logs: list[BaseAgentLog] | None = None,
    ) -> AgentExecutionResult:
        """
        Run the agent on a given scenario.
        :param scenario: Scenario with task to solve and available tools.
        :param notification_system: Notification system to use for sending notifications.
        :returns: The result of the agent (type depends on the implementation).
        """
        raise NotImplementedError("run_scenario is not implemented")

    def stop(self) -> None:
        """
        Stop the agent.
        """
        pass
