# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from abc import ABC, abstractmethod

from are.simulation.agents.llm.llm_engine import LLMEngine

logger = logging.getLogger(__name__)


class UserProxy(ABC):
    @abstractmethod
    def reply(self, message: str) -> str:
        """
        Sends a message to the User and returns the response.
        :param message: the message to send to the User
        :returns: the response from the User
        """
        pass

    @abstractmethod
    def init_conversation(self) -> str:
        """
        Initiate the conversation with the Agent.
        :return: conversation starter from the User
        """
        pass


class UserProxyLLM(UserProxy):
    def __init__(
        self,
        llm: LLMEngine,
        system_message: str = "You are a Human user interacting with an AI agent that is trying to solve a task you gave them.",
    ):
        self.llm = llm
        self.system_message = system_message
        self.history: list[dict[str, str]] = []
        self.history.append({"role": "system", "content": self.system_message})

    def reply(self, message: str) -> str:
        """
        Sends a message to the User and returns the response.
        :param message: the message to send to the User
        :returns: the response from the User
        """
        logger.info(f"User Proxy Received message from Agent: {message}")
        self.history.append({"role": "user", "content": "AI agent : " + message})
        response, _ = self.llm(self.history)
        logger.info(f"User Proxy Sent response to Agent: {response}")
        self.history.append({"role": "assistant", "content": response})
        return response

    def init_conversation(self) -> str:
        """
        Initiate the conversation with the Agent.
        :return: conversation starter from the User
        """
        response, _ = self.llm(self.history)
        logger.info(f"User Proxy Conversation Starter: {response}")
        self.history.append({"role": "assistant", "content": response})
        return response
