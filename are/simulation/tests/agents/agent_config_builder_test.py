# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import pytest

from are.simulation.agents.agent_config_builder import AgentConfigBuilder
from are.simulation.agents.are_simulation_agent_config import (
    ARESimulationReactAgentConfig,
    RunnableARESimulationAgentConfig,
)


@pytest.fixture
def agent_config_builder() -> AgentConfigBuilder:
    return AgentConfigBuilder()


def test_build_default(
    agent_config_builder: AgentConfigBuilder,
):
    agent_config = agent_config_builder.build("default")
    assert isinstance(agent_config, RunnableARESimulationAgentConfig)
    assert isinstance(agent_config, ARESimulationReactAgentConfig)


def test_build_invalid_agent(agent_config_builder: AgentConfigBuilder):
    with pytest.raises(ValueError, match="Agent invalid_agent not found"):
        agent_config_builder.build("invalid_agent")
