# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import tempfile
from unittest.mock import Mock

import pytest

from are.simulation.agents.agent_log import (
    ActionLog,
    AgentUserInterfaceLog,
    EndTaskLog,
    EnvironmentNotificationLog,
    ErrorLog,
    FactsLog,
    FinalAnswerLog,
    LLMInputLog,
    LLMOutputFactsLog,
    LLMOutputPlanLog,
    LLMOutputThoughtActionLog,
    ObservationLog,
    PlanLog,
    RationaleLog,
    RefactsLog,
    ReplanLog,
    StepLog,
    StopLog,
    SubagentLog,
    SystemPromptLog,
    TaskLog,
    ThoughtLog,
    ToolCallLog,
)
from are.simulation.agents.multimodal import Attachment
from are.simulation.gui.server.graphql.subscription import (
    get_world_logs_for_graphql,
    graphql_cache,
    update_graphql_cache,
)
from are.simulation.gui.server.graphql.types import AgentLogTypeForGraphQL


@pytest.fixture
def setup_environment():
    session_id = "test_session"
    graphql_cache.clear()
    return session_id


def test_update_with_string(setup_environment):
    session_id = setup_environment
    update_graphql_cache(session_id, "test_string", "env_state")
    assert graphql_cache[session_id]["env_state"] == "test_string"


def test_update_with_list(setup_environment):
    session_id = setup_environment
    step_logs = [1, 2, 3]
    update_graphql_cache(session_id, step_logs, "step_logs")
    assert "step_logs_hash" in graphql_cache[session_id]


def test_update_with_object(setup_environment):
    session_id = setup_environment
    test_obj = {"key": "value"}
    update_graphql_cache(session_id, test_obj, "apps_state")
    assert "apps_state_hash" in graphql_cache[session_id]


def test_update_with_no_change(setup_environment):
    session_id = setup_environment
    graphql_cache[session_id] = {}
    graphql_cache[session_id]["env_state"] = "test_string"
    update_graphql_cache(session_id, "test_string", "env_state")
    assert graphql_cache[session_id]["env_state"] == "test_string"


class TestGetWorldLogsForGraphQL:
    """Test suite for the refactored get_world_logs_for_graphql function."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = f"{self.temp_dir}/cache"
        self.hosting_root = "http://test.com/files"

    def create_log_instance(self, log_class, **kwargs):
        """Helper to create actual log instances with required attributes."""
        # Common required fields for all logs
        base_kwargs = {
            "timestamp": kwargs.get("timestamp", 1234567890.0),
            "agent_id": kwargs.get("agent_id", "test_agent"),
        }

        # Add specific fields based on log type
        if log_class == SystemPromptLog:
            base_kwargs["content"] = kwargs.get("content", "test content")
        elif log_class == TaskLog:
            base_kwargs["content"] = kwargs.get("content", "test content")
            base_kwargs["attachments"] = kwargs.get("attachments", [])
        elif log_class == LLMInputLog:
            base_kwargs["content"] = kwargs.get(
                "content", [{"role": "user", "content": "test"}]
            )
        elif log_class == LLMOutputThoughtActionLog:
            base_kwargs["content"] = kwargs.get("content", "test content")
        elif log_class == RationaleLog:
            base_kwargs["content"] = kwargs.get("content", "test content")
        elif log_class == ToolCallLog:
            base_kwargs["tool_name"] = kwargs.get("tool_name", "test_tool")
            base_kwargs["tool_arguments"] = kwargs.get(
                "tool_arguments", {"arg": "value"}
            )
        elif log_class == ObservationLog:
            base_kwargs["content"] = kwargs.get("content", "test content")
            base_kwargs["attachments"] = kwargs.get("attachments", [])
        elif log_class == StepLog:
            base_kwargs["iteration"] = kwargs.get("iteration", 1)
        elif log_class == SubagentLog:
            base_kwargs["group_id"] = kwargs.get("group_id", "test_group")
            base_kwargs["children"] = kwargs.get("children", [])
            base_kwargs["name"] = kwargs.get("name", "test_subagent")
        elif log_class == FinalAnswerLog:
            base_kwargs["content"] = kwargs.get("content", "test content")
            base_kwargs["attachments"] = kwargs.get("attachments", [])
        elif log_class == ErrorLog:
            base_kwargs["error"] = kwargs.get("error", "test error")
            base_kwargs["exception"] = kwargs.get("exception", "test exception")
            base_kwargs["category"] = kwargs.get("category", "test_category")
            base_kwargs["agent"] = kwargs.get("agent", "test_agent")
        elif log_class == EndTaskLog:
            pass  # No additional fields needed
        elif log_class in [ThoughtLog, PlanLog, FactsLog, ReplanLog, RefactsLog]:
            base_kwargs["content"] = kwargs.get("content", "test content")
        elif log_class in [LLMOutputPlanLog, LLMOutputFactsLog]:
            base_kwargs["content"] = kwargs.get("content", "test content")
        elif log_class in [StopLog, ActionLog]:
            base_kwargs["content"] = kwargs.get("content", "test content")
            if log_class == ActionLog:
                base_kwargs["input"] = kwargs.get("input", {})
                base_kwargs["event_type"] = kwargs.get("event_type", "test_event")
                base_kwargs["output"] = kwargs.get("output", "test_output")
                base_kwargs["action_name"] = kwargs.get("action_name", "test_action")
                base_kwargs["app_name"] = kwargs.get("app_name", "test_app")
                base_kwargs["exception"] = kwargs.get("exception", None)
                base_kwargs["exception_stack_trace"] = kwargs.get(
                    "exception_stack_trace", None
                )
        elif log_class in [AgentUserInterfaceLog, EnvironmentNotificationLog]:
            base_kwargs["content"] = kwargs.get("content", "test content")

        # Create the actual instance
        log = log_class(**base_kwargs)

        # Override the ID if provided
        if "id" in kwargs:
            log.id = kwargs["id"]

        return log

    def test_step_log_processing(self):
        """Test that StepLog is processed correctly."""
        step_log = self.create_log_instance(StepLog, iteration=5)

        result = get_world_logs_for_graphql(
            [step_log], self.cache_dir, self.hosting_root
        )

        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.STEP
        assert result[0].content == "STEP 5"
        assert result[0].group_id is None

    def test_system_prompt_log_processing(self):
        """Test that SystemPromptLog is processed correctly."""
        system_log = self.create_log_instance(SystemPromptLog, content="System prompt")

        result = get_world_logs_for_graphql(
            [system_log], self.cache_dir, self.hosting_root
        )

        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.SYSTEM_PROMPT
        assert result[0].content == "System prompt"

    def test_task_log_with_attachments(self):
        """Test that TaskLog with attachments is processed correctly."""
        attachment = Mock(spec=Attachment)
        attachment.mime = "text/plain"
        attachment.base64_data = "dGVzdCBkYXRh"  # "test data" in base64

        task_log = self.create_log_instance(
            TaskLog, content="Task content", attachments=[attachment]
        )

        result = get_world_logs_for_graphql(
            [task_log], self.cache_dir, self.hosting_root
        )

        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.TASK
        assert result[0].content == "Task content"
        assert result[0].group_id is None
        assert result[0].attachments is not None
        assert len(result[0].attachments) == 1

    def test_observation_log_with_attachments(self):
        """Test that ObservationLog with attachments is processed correctly."""
        attachment = Mock(spec=Attachment)
        attachment.mime = "image/png"
        attachment.base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

        obs_log = self.create_log_instance(
            ObservationLog, content="Observation", attachments=[attachment]
        )

        result = get_world_logs_for_graphql(
            [obs_log], self.cache_dir, self.hosting_root
        )

        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.OBSERVATION
        assert result[0].content == "Observation"
        assert result[0].attachments is not None

    def test_llm_input_log_json_serialization(self):
        """Test that LLMInputLog content is JSON serialized."""
        llm_input = self.create_log_instance(
            LLMInputLog, content=[{"messages": ["test"]}]
        )

        result = get_world_logs_for_graphql(
            [llm_input], self.cache_dir, self.hosting_root
        )

        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.LLM_INPUT
        # Content should be JSON serialized
        assert result[0].content is not None
        parsed_content = json.loads(result[0].content)
        assert parsed_content == [{"messages": ["test"]}]

    def test_error_log_with_exception(self):
        """Test that ErrorLog includes exception field."""
        error_log = self.create_log_instance(
            ErrorLog, error="Test error", exception="Test exception"
        )

        result = get_world_logs_for_graphql(
            [error_log], self.cache_dir, self.hosting_root
        )

        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.ERROR
        assert result[0].content == "Test error"
        assert result[0].exception == "Test exception"

    def test_end_task_log_no_content(self):
        """Test that EndTaskLog has no content."""
        end_task = self.create_log_instance(EndTaskLog)

        result = get_world_logs_for_graphql(
            [end_task], self.cache_dir, self.hosting_root
        )

        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.END_TASK
        assert result[0].content is None

    def test_subagent_log_recursive_processing(self):
        """Test that SubagentLog processes children recursively."""
        child_log = self.create_log_instance(SystemPromptLog, content="Child content")
        subagent = self.create_log_instance(
            SubagentLog, name="test_agent", children=[child_log]
        )

        result = get_world_logs_for_graphql(
            [subagent], self.cache_dir, self.hosting_root
        )

        assert len(result) == 2
        # First log should be the subagent
        assert result[0].type == AgentLogTypeForGraphQL.SUBAGENT
        assert result[0].content == "SUBAGENT (test_agent)"
        # Second log should be the child with is_subagent=True
        assert result[1].type == AgentLogTypeForGraphQL.SYSTEM_PROMPT
        assert result[1].is_subagent is True

    def test_skip_logs_are_ignored(self):
        """Test that logs marked for skipping are ignored."""
        stop_log = self.create_log_instance(StopLog)
        action_log = self.create_log_instance(ActionLog)
        system_log = self.create_log_instance(SystemPromptLog, content="Should appear")

        result = get_world_logs_for_graphql(
            [stop_log, action_log, system_log], self.cache_dir, self.hosting_root
        )

        # Only the system log should appear
        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.SYSTEM_PROMPT

    def test_simple_log_mappings(self):
        """Test that simple logs are mapped correctly."""
        logs = [
            (RationaleLog, AgentLogTypeForGraphQL.RATIONALE),
            (FinalAnswerLog, AgentLogTypeForGraphQL.FINAL_ANSWER),
            (PlanLog, AgentLogTypeForGraphQL.PLAN),
            (FactsLog, AgentLogTypeForGraphQL.FACTS),
            (ReplanLog, AgentLogTypeForGraphQL.REPLAN),
            (RefactsLog, AgentLogTypeForGraphQL.REFACTS),
            (ThoughtLog, AgentLogTypeForGraphQL.THOUGHT),
            (LLMOutputPlanLog, AgentLogTypeForGraphQL.LLM_OUTPUT_PLAN),
            (LLMOutputFactsLog, AgentLogTypeForGraphQL.LLM_OUTPUT_FACTS),
            (
                LLMOutputThoughtActionLog,
                AgentLogTypeForGraphQL.LLM_OUTPUT_THOUGHT_ACTION,
            ),
        ]

        for log_class, expected_type in logs:
            log = self.create_log_instance(log_class, content="Test content")
            result = get_world_logs_for_graphql(
                [log], self.cache_dir, self.hosting_root
            )

            assert len(result) == 1
            assert result[0].type == expected_type
            assert result[0].content == "Test content"

    def test_tool_call_log_uses_get_content_for_llm(self):
        """Test that ToolCallLog uses get_content_for_llm method."""
        tool_log = self.create_log_instance(
            ToolCallLog, tool_name="test_tool", tool_arguments={"arg": "value"}
        )

        result = get_world_logs_for_graphql(
            [tool_log], self.cache_dir, self.hosting_root
        )

        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.TOOL_CALL
        # ToolCallLog.get_content_for_llm() returns JSON with tool_name and tool_arguments
        assert result[0].content is not None
        parsed_content = json.loads(result[0].content)
        assert parsed_content["tool_name"] == "test_tool"
        assert parsed_content["tool_arguments"] == {"arg": "value"}

    def test_group_id_assignment(self):
        """Test that group_id is assigned correctly based on StepLog."""
        step_log = self.create_log_instance(StepLog, iteration=1)
        system_log = self.create_log_instance(SystemPromptLog, content="System")

        result = get_world_logs_for_graphql(
            [step_log, system_log], self.cache_dir, self.hosting_root
        )

        assert len(result) == 2
        assert result[0].group_id is None  # StepLog has no group_id
        assert (
            result[1].group_id == step_log.id
        )  # SystemPromptLog gets StepLog's id as group_id

    def test_logs_are_sorted_by_timestamp(self):
        """Test that logs are sorted by timestamp."""
        log1 = self.create_log_instance(
            SystemPromptLog, content="Second", timestamp=2.0
        )
        log2 = self.create_log_instance(SystemPromptLog, content="First", timestamp=1.0)
        log3 = self.create_log_instance(SystemPromptLog, content="Third", timestamp=3.0)

        result = get_world_logs_for_graphql(
            [log1, log2, log3], self.cache_dir, self.hosting_root
        )

        assert len(result) == 3
        assert result[0].content == "First"
        assert result[1].content == "Second"
        assert result[2].content == "Third"

    def test_unknown_log_type_handling(self):
        """Test that unknown log types are handled gracefully."""
        # Create a mock log that doesn't match any known type
        unknown_log = Mock()
        unknown_log.id = "unknown_id"
        unknown_log.timestamp = 1234567890.0

        result = get_world_logs_for_graphql(
            [unknown_log], self.cache_dir, self.hosting_root
        )

        # Unknown log should be skipped
        assert len(result) == 0

    def test_warn_log_types_are_skipped(self):
        """Test that logs that generate warnings are skipped."""
        ui_log = self.create_log_instance(AgentUserInterfaceLog)
        env_log = self.create_log_instance(EnvironmentNotificationLog)
        system_log = self.create_log_instance(SystemPromptLog, content="Should appear")

        result = get_world_logs_for_graphql(
            [ui_log, env_log, system_log], self.cache_dir, self.hosting_root
        )

        # Only the system log should appear
        assert len(result) == 1
        assert result[0].type == AgentLogTypeForGraphQL.SYSTEM_PROMPT
