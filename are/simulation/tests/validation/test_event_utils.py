# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from unittest.mock import MagicMock, patch

from are.simulation.scenarios.utils.scenario_expander import ENV_EVENT_EXPANSION_TAG
from are.simulation.tool_utils import OperationType
from are.simulation.types import Action, CompletedEvent, EventType
from are.simulation.validation.utils.event_utils import (
    AgentEventFilter,
    BulletActionDescription,
    BulletEventDescription,
    EnvAgentEventFilter,
    parameter_descr,
    resolve_arg_placeholders,
)


class TestResolveArgPlaceholders:
    def test_returns_event_when_action_is_none(self):
        """Test that resolve_arg_placeholders returns the event unchanged when action is None."""
        # Setup
        event = MagicMock(spec=CompletedEvent)
        event.action = None
        target_events = []
        event_id_to_target_event_idx = {}

        # Execute
        result = resolve_arg_placeholders(
            event, target_events, event_id_to_target_event_idx
        )

        # Assert
        assert result == event

    def test_returns_event_when_args_is_none(self):
        """Test that resolve_arg_placeholders returns the event unchanged when args is None."""
        # Setup
        event = MagicMock(spec=CompletedEvent)
        event.action = MagicMock()
        event.action.args = None
        target_events = []
        event_id_to_target_event_idx = {}

        # Execute
        result = resolve_arg_placeholders(
            event, target_events, event_id_to_target_event_idx
        )

        # Assert
        assert result == event

    def test_resolves_placeholder_args(self):
        """Test that resolve_arg_placeholders resolves placeholder arguments correctly."""
        # Setup
        event = MagicMock(spec=CompletedEvent)
        event.action = MagicMock()
        event.action.args = {"arg1": "{{past_event_id}}", "arg2": "normal_value"}
        event.action.resolved_args = {}

        past_event = MagicMock(spec=CompletedEvent)
        past_event.metadata.return_value = "past_event_return_value"
        target_events = [past_event]

        event_id_to_target_event_idx = {"past_event_id": 0}

        # Execute
        result = resolve_arg_placeholders(
            event,
            target_events,  # type: ignore
            event_id_to_target_event_idx,  # type: ignore
        )

        # Assert
        assert result == event
        assert result.action.resolved_args["arg1"] == past_event.metadata.return_value  # type: ignore


class TestEventFilter:
    def test_preprocess_event_file_system_operations(self):
        """Test that preprocess_event correctly processes file system operations."""
        # Setup
        event_filter = AgentEventFilter()

        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.AGENT
        event.action = MagicMock()
        event.action.function_name = "makedirs"
        event.action.class_name = "SandboxLocalFileSystem"
        event._tool_name = None

        # Execute
        result = event_filter.preprocess_event(event)

        # Assert - verify that the action attributes were modified correctly
        assert result._tool_name == "SandboxLocalFileSystem__mkdir"

    def test_call_method(self):
        """Test that __call__ method calls preprocess_event and filter methods."""
        # Setup
        event_filter = AgentEventFilter()
        event = MagicMock(spec=CompletedEvent)

        # Mock the preprocess_event and filter methods
        event_filter.preprocess_event = MagicMock(return_value=event)
        event_filter.filter = MagicMock(return_value=True)

        # Execute
        result = event_filter(event)

        # Assert
        event_filter.preprocess_event.assert_called_once_with(event)
        event_filter.filter.assert_called_once_with(event)
        assert result is True


class TestAgentEventFilter:
    def test_filter_returns_true_for_valid_agent_events(self):
        """Test that filter returns True for valid agent events."""
        # Setup
        agent_filter = AgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.AGENT
        event.action = MagicMock()
        event.action.operation_type = OperationType.WRITE
        event.failed.return_value = False

        # Execute
        result = agent_filter.filter(event)

        # Assert
        assert result is True

    def test_filter_returns_false_for_non_agent_events(self):
        """Test that filter returns False for non-agent events."""
        # Setup
        agent_filter = AgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.ENV
        event.action = MagicMock()
        event.action.operation_type = OperationType.WRITE
        event.failed.return_value = False

        # Execute
        result = agent_filter.filter(event)

        # Assert
        assert result is False

    def test_filter_returns_false_for_non_write_operations(self):
        """Test that filter returns False for non-write operations."""
        # Setup
        agent_filter = AgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.AGENT
        event.action = MagicMock()
        event.action.operation_type = OperationType.READ
        event.failed.return_value = False

        # Execute
        result = agent_filter.filter(event)

        # Assert
        assert result is False

    def test_filter_returns_false_for_failed_events(self):
        """Test that filter returns False for failed events."""
        # Setup
        agent_filter = AgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.AGENT
        event.action = MagicMock()
        event.action.operation_type = OperationType.WRITE
        event.failed.return_value = True

        # Execute
        result = agent_filter.filter(event)

        # Assert
        assert result is False

    def test_filter_returns_false_when_action_is_none(self):
        """Test that filter returns False when action is None."""
        # Setup
        agent_filter = AgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.AGENT
        event.action = None
        event.failed.return_value = False

        # Execute
        result = agent_filter.filter(event)

        # Assert
        assert result is False


class TestEnvAgentEventFilter:
    def test_filter_returns_true_for_env_events(self):
        """Test that filter returns True for ENV events that are not failed."""
        # Setup
        env_agent_filter = EnvAgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.ENV
        event.event_id = "env_event_id"  # Not containing expansion tag
        event.failed.return_value = False

        # Execute
        result = env_agent_filter.filter(event)

        # Assert
        assert result is True

    def test_filter_returns_true_for_user_events(self):
        """Test that filter returns True for USER events that are not failed."""
        # Setup
        env_agent_filter = EnvAgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.USER
        event.event_id = "user_event_id"  # Not containing expansion tag
        event.failed.return_value = False

        # Execute
        result = env_agent_filter.filter(event)

        # Assert
        assert result is True

    def test_filter_returns_false_for_env_events_with_expansion_tag(self):
        """Test that filter returns False for ENV events with expansion tag."""
        # Setup
        env_agent_filter = EnvAgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.ENV
        event.event_id = f"env_event_id_{ENV_EVENT_EXPANSION_TAG}"
        event.failed.return_value = False

        # Execute
        result = env_agent_filter.filter(event)

        # Assert
        assert result is False

    def test_filter_returns_false_for_failed_env_events(self):
        """Test that filter returns False for failed ENV events."""
        # Setup
        env_agent_filter = EnvAgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.ENV
        event.event_id = "env_event_id"
        event.failed.return_value = True

        # Execute
        result = env_agent_filter.filter(event)

        # Assert
        assert result is False

    def test_filter_delegates_to_agent_event_filter_for_agent_events(self):
        """Test that filter delegates to agent_event_filter for AGENT events."""
        # Setup
        env_agent_filter = EnvAgentEventFilter()
        event = MagicMock(spec=CompletedEvent)
        event.event_type = EventType.AGENT

        # Mock the agent_event_filer to return a specific value
        env_agent_filter.agent_event_filer = MagicMock(return_value=True)

        # Execute
        result = env_agent_filter.filter(event)

        # Assert
        env_agent_filter.agent_event_filer.assert_called_once_with(event)
        assert result is True


class TestParameterDescr:
    def test_formats_parameters_with_all_args(self):
        """Test that parameter_descr formats parameters correctly with all args."""
        # Setup
        action = MagicMock(spec=Action)
        action.args = {"arg1": "value1", "arg2": "value2", "self": "self_value"}
        action.resolved_args = None

        # Execute
        result = parameter_descr(action)

        # Assert
        assert "arg1: value1" in result
        assert "arg2: value2" in result
        assert "self: self_value" not in result  # 'self' should be excluded

    def test_formats_parameters_with_selected_args(self):
        """Test that parameter_descr formats parameters correctly with selected args."""
        # Setup
        action = MagicMock(spec=Action)
        action.args = {"arg1": "value1", "arg2": "value2", "arg3": "value3"}
        action.resolved_args = None
        selected_args = ["arg1", "arg3"]

        # Execute
        result = parameter_descr(action, selected_args)

        # Assert
        assert "arg1: value1" in result
        assert "arg2: value2" not in result
        assert "arg3: value3" in result

    def test_uses_resolved_args_when_available(self):
        """Test that parameter_descr uses resolved_args when available."""
        # Setup
        action = MagicMock(spec=Action)
        action.args = {"arg1": "original1", "arg2": "original2"}
        action.resolved_args = {"arg1": "resolved1", "arg2": "resolved2"}

        # Execute
        result = parameter_descr(action)

        # Assert
        assert "arg1: resolved1" in result
        assert "arg2: resolved2" in result
        assert "original1" not in result
        assert "original2" not in result


class TestBulletEventDescription:
    def test_describe_event_formats_correctly(self):
        """Test that describe_event formats the event description correctly."""
        # Setup
        tool_name = "TestTool"
        bullet_desc = BulletEventDescription(tool_name)

        event = MagicMock(spec=CompletedEvent)
        event.event_time = "2023-01-01T12:00:00"
        event.action = MagicMock(spec=Action)
        event.action.args = {"arg1": "value1", "arg2": "value2"}
        event.action.resolved_args = None

        # Execute
        result = bullet_desc.describe_event(event)

        # Assert
        assert f"Tool name: {tool_name}" in result
        assert f"Tool call time: {event.event_time}" in result
        assert "Arguments:" in result
        assert "arg1: value1" in result
        assert "arg2: value2" in result

    def test_call_method_delegates_to_describe_event(self):
        """Test that __call__ method delegates to describe_event."""
        # Setup
        tool_name = "TestTool"
        bullet_desc = BulletEventDescription(tool_name)

        event = MagicMock(spec=CompletedEvent)

        # Mock the describe_event method
        bullet_desc.describe_event = MagicMock(return_value="test description")

        # Execute
        result = bullet_desc(event, extra_kwarg="test")

        # Assert
        bullet_desc.describe_event.assert_called_once_with(event, extra_kwarg="test")
        assert result == "test description"


class TestBulletActionDescription:
    def test_describe_event_uses_default_selected_args(self):
        """Test that describe_event uses the default selected_args when not provided in kwargs."""
        # Setup
        default_selected_args = ["arg1", "arg3"]
        bullet_action_desc = BulletActionDescription(default_selected_args)

        event = MagicMock(spec=CompletedEvent)
        event.action = MagicMock(spec=Action)

        # Mock parameter_descr to verify the args passed
        with patch(
            "are.simulation.validation.utils.event_utils.parameter_descr"
        ) as mock_param_descr:
            mock_param_descr.return_value = "formatted parameters"

            # Execute
            result = bullet_action_desc.describe_event(event)

            # Assert
            mock_param_descr.assert_called_once_with(
                event.action, default_selected_args
            )
            assert result == "formatted parameters"

    def test_describe_event_uses_kwargs_selected_args(self):
        """Test that describe_event uses the selected_args provided in kwargs."""
        # Setup
        default_selected_args = ["arg1", "arg3"]
        kwargs_selected_args = ["arg2", "arg4"]
        bullet_action_desc = BulletActionDescription(default_selected_args)

        event = MagicMock(spec=CompletedEvent)
        event.action = MagicMock(spec=Action)

        # Mock parameter_descr to verify the args passed
        with patch(
            "are.simulation.validation.utils.event_utils.parameter_descr"
        ) as mock_param_descr:
            mock_param_descr.return_value = "formatted parameters"

            # Execute
            result = bullet_action_desc.describe_event(
                event, action_selected_args=kwargs_selected_args
            )

            # Assert
            mock_param_descr.assert_called_once_with(event.action, kwargs_selected_args)
            assert result == "formatted parameters"
