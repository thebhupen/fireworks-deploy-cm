# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import time
from typing import cast

from are.simulation.agents.agent_log import (
    BaseAgentLog,
    SubagentLog,
    SystemPromptLog,
    TaskLog,
)


def test_subagent_log_serialization():
    system_prompt_log = SystemPromptLog(
        timestamp=time.time(),
        content="test system prompt",
        agent_id="test_agent_id",
    )
    task_log = TaskLog(
        timestamp=time.time(),
        content="test task",
        agent_id="test_agent_id",
    )

    original_log = SubagentLog(
        timestamp=time.time(),
        group_id="test_group",
        children=[system_prompt_log, task_log],
        name="test_agent",
        agent_id="test_agent_id",
    )

    log_dict = original_log.to_dict()

    assert original_log.name == "test_agent"
    assert "name" in log_dict
    assert log_dict["name"] == "test_agent"

    deserialized_log = BaseAgentLog.from_dict(log_dict)

    assert isinstance(deserialized_log, SubagentLog)
    deserialized_log = cast(SubagentLog, deserialized_log)

    assert deserialized_log.timestamp == original_log.timestamp
    assert deserialized_log.group_id == original_log.group_id
    assert deserialized_log.name == "test_agent"

    # Verify children
    assert len(deserialized_log.children) == 2

    assert isinstance(deserialized_log.children[0], SystemPromptLog)
    child1 = cast(SystemPromptLog, deserialized_log.children[0])
    assert child1.content == "test system prompt"

    assert isinstance(deserialized_log.children[1], TaskLog)
    child2 = cast(TaskLog, deserialized_log.children[1])
    assert child2.content == "test task"


def test_subagent_log_deserialization_without_name():
    system_prompt_log = SystemPromptLog(
        timestamp=time.time(),
        content="test system prompt",
        agent_id="test_agent_id",
    )
    task_log = TaskLog(
        timestamp=time.time(),
        content="test task",
        agent_id="test_agent_id",
    )

    original_log = SubagentLog(
        timestamp=time.time(),
        group_id="test_group",
        children=[system_prompt_log, task_log],
        agent_id="test_agent_id",
    )

    log_dict = original_log.to_dict()

    # Remove the 'name' key from the dictionary to simulate JSON without the name property
    if "name" in log_dict:
        del log_dict["name"]

    deserialized_log = BaseAgentLog.from_dict(log_dict)

    assert isinstance(deserialized_log, SubagentLog)
    deserialized_log = cast(SubagentLog, deserialized_log)

    assert deserialized_log.timestamp == original_log.timestamp
    assert deserialized_log.group_id == original_log.group_id
    assert deserialized_log.name is None  # Should default to None when key is missing

    # Verify children
    assert len(deserialized_log.children) == 2

    assert isinstance(deserialized_log.children[0], SystemPromptLog)
    child1 = cast(SystemPromptLog, deserialized_log.children[0])
    assert child1.content == "test system prompt"

    assert isinstance(deserialized_log.children[1], TaskLog)
    child2 = cast(TaskLog, deserialized_log.children[1])
    assert child2.content == "test task"
