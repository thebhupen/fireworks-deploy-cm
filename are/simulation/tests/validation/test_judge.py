# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import unittest
from collections import Counter
from unittest.mock import MagicMock, patch

from are.simulation.apps.contacts import Contact
from are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario import (
    BenchmarkScenarioImportedFromJson,
)
from are.simulation.types import AbstractEnvironment, CompletedEvent, EventType
from are.simulation.validation.configs import (
    GraphPerEventJudgeConfig,
    InContextJudgeConfig,
)
from are.simulation.validation.judge import GraphPerEventJudge, InContextJudge
from are.simulation.validation.judge_states import (
    GraphPerEventJudgeState,
    InContextJudgeState,
)
from are.simulation.validation.judgment import Judgment, ToolCallCountsFailure
from are.simulation.validation.utils.scenario_utils import CompletedOracleEvent


class TestInContextJudge(unittest.TestCase):
    def setUp(self):
        # Create mock config
        self.config = MagicMock(spec=InContextJudgeConfig)
        self.config.engine = MagicMock()
        self.config.engine.return_value = ("[[success]]", None)
        self.config.system_prompt_template = "System prompt: {{ evaluation_criteria }}"
        self.config.time_system_prompt_template = (
            "Time evaluation: {{ check_time_threshold_seconds }}"
        )
        self.config.check_time_threshold_seconds = 10.0
        self.config.pre_event_tolerance_seconds = 5.0
        self.config.post_event_tolerance_seconds = 20.0
        self.config.per_tool_evaluation_criteria = {"test_tool": "Test criteria"}
        self.config.tool_to_selected_args = {"test_tool": {"arg1": "value1"}}
        self.config.tracer = None

        # Create judge
        self.judge = InContextJudge(self.config)

        # Create mock user details
        self.user_details = MagicMock(spec=Contact)
        self.user_details.first_name = "John"
        self.user_details.last_name = "Doe"

        # Create mock environment
        self.env = MagicMock(spec=AbstractEnvironment)

        # Create mock scenario
        self.scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        self.scenario.nb_turns = 1
        self.scenario.start_time = 100.0

    def test_init(self):
        # Test initialization
        self.assertEqual(self.judge.config, self.config)
        self.assertIsInstance(self.judge.state, InContextJudgeState)
        self.assertFalse(self.judge.state.initialized)

    def test_initialize_state(self):
        # Mock extract functions
        with patch(
            "are.simulation.validation.judge.extract_oracle_events"
        ) as mock_extract_oracle:
            with patch(
                "are.simulation.validation.judge.extract_tasks"
            ) as mock_extract_tasks:
                with patch(
                    "are.simulation.validation.judge.extract_user_details"
                ) as mock_extract_user:
                    # Set up mock returns
                    mock_extract_oracle.return_value = ([], {})
                    mock_extract_tasks.return_value = ["task1"]
                    mock_extract_user.return_value = self.user_details

                    # Call initialize_state
                    self.judge.initialize_state(self.scenario)

                    # Check state is initialized
                    self.assertTrue(self.judge.state.initialized)
                    self.assertEqual(self.judge.state.nb_turns, 1)
                    self.assertEqual(self.judge.state.turn_idx, -1)
                    self.assertEqual(self.judge.state.scenario_start_time, 100.0)
                    self.assertEqual(self.judge.state.scenario_tasks, ["task1"])
                    self.assertEqual(self.judge.state.user_name, "John Doe")

    def test_update_state(self):
        # Initialize state first
        with patch(
            "are.simulation.validation.judge.extract_oracle_events"
        ) as mock_extract_oracle:
            with patch(
                "are.simulation.validation.judge.extract_tasks"
            ) as mock_extract_tasks:
                with patch(
                    "are.simulation.validation.judge.extract_user_details"
                ) as mock_extract_user:
                    mock_extract_oracle.return_value = ([], {})
                    mock_extract_tasks.return_value = ["task1"]
                    mock_extract_user.return_value = self.user_details
                    self.judge.initialize_state(self.scenario)

        # Mock extract_agent_events
        with patch(
            "are.simulation.validation.judge.extract_agent_events"
        ) as mock_extract_agent:
            mock_extract_agent.return_value = ["agent_event1"]

            # Call update_state
            self.judge.update_state(self.env)

            # Check state is updated
            self.assertEqual(self.judge.state.turn_idx, 0)
            self.assertEqual(self.judge.state.turn_to_agent_events, [["agent_event1"]])

    def test_list_events_str(self):
        # Create mock events
        event = MagicMock(spec=CompletedEvent)
        event.tool_name = "test_tool"

        # Mock event description
        with patch.object(
            type(self.judge.tool_to_event_description["test_tool"]), "__call__"
        ) as mock_desc:
            mock_desc.return_value = "Event description"

            # Call list_events_str
            result = self.judge.list_events_str([event])

            # Check result
            self.assertEqual(result, "Event description")

    def test_build_user_prompt(self):
        # Mock list_events_str
        with patch.object(self.judge, "list_events_str") as mock_list:
            mock_list.side_effect = ["Agent events", "Oracle events"]

            # Call build_user_prompt
            result = self.judge.build_user_prompt(["agent_event"], ["oracle_event"])

            # Check result
            self.assertIn("Agent actions:", result)
            self.assertIn("Agent events", result)
            self.assertIn("Oracle actions:", result)
            self.assertIn("Oracle events", result)

    def test_inner_call(self):
        # Initialize state
        with patch(
            "are.simulation.validation.judge.extract_oracle_events"
        ) as mock_extract_oracle:
            with patch(
                "are.simulation.validation.judge.extract_tasks"
            ) as mock_extract_tasks:
                with patch(
                    "are.simulation.validation.judge.extract_user_details"
                ) as mock_extract_user:
                    mock_extract_oracle.return_value = ([], {})
                    mock_extract_tasks.return_value = ["task1"]
                    mock_extract_user.return_value = self.user_details
                    self.judge.initialize_state(self.scenario)

        # Mock update_state and build_user_prompt
        with patch.object(self.judge, "update_state"):
            with patch.object(
                self.judge, "build_user_prompt", return_value="User prompt"
            ):
                # Mock current_turn properties
                with patch.object(
                    type(self.judge.state),
                    "current_turn_agent_events",
                    new=[],
                ):
                    with patch.object(
                        type(self.judge.state),
                        "current_turn_oracle_events",
                        new=[],
                    ):
                        # Call inner_call
                        result = self.judge.inner_call(self.env)

                        # Check result
                        self.assertTrue(result)
                        self.config.engine.assert_called_once()

    def test_call(self):
        # Mock inner_call
        with patch.object(self.judge, "inner_call") as mock_inner:
            mock_inner.return_value = True

            # Call __call__
            result = self.judge(self.env)

            # Check result
            self.assertIsInstance(result, Judgment)
            self.assertTrue(result.success)


class TestGraphPerEventJudge(unittest.TestCase):
    def setUp(self):
        # Create mock config
        self.config = MagicMock(spec=GraphPerEventJudgeConfig)
        self.config.extra_send_message_to_user_allowed = 1
        self.config.check_time_threshold_seconds = 10.0
        self.config.pre_event_tolerance_seconds = 5.0
        self.config.post_event_tolerance_seconds = 20.0
        self.config.per_tool_arg_to_checker_type = {}
        self.config.per_tool_soft_checker_types = {}
        self.config.engine = MagicMock()
        self.config.event_id_to_checker_params = None
        self.config.tracer = None

        # Create judge
        self.judge = GraphPerEventJudge(self.config)

        # Create mock environment
        self.env = MagicMock(spec=AbstractEnvironment)

        # Create mock user details
        self.user_details = MagicMock(spec=Contact)
        self.user_details.first_name = "John"
        self.user_details.last_name = "Doe"

        # Create mock scenario
        self.scenario = MagicMock(spec=BenchmarkScenarioImportedFromJson)
        self.scenario.nb_turns = 1
        self.scenario.start_time = 100.0
        self.scenario.event_id_to_turn_idx = {"event1": 0}
        event1 = MagicMock()
        event1.action.class_name = "AgentUserInterface"
        event1.action.function_name = "send_message_to_agent"
        event1.action.args = {"content": "Task 1"}
        event1.event_id = "event1"
        self.scenario.events = [event1]

    def test_init(self):
        # Test initialization
        self.assertEqual(self.judge.config, self.config)
        self.assertIsInstance(self.judge.state, GraphPerEventJudgeState)
        self.assertFalse(self.judge.state.initialized)
        self.assertIn(EventType.ENV, self.judge.event_judges)
        self.assertIn(EventType.USER, self.judge.event_judges)
        self.assertIn(EventType.AGENT, self.judge.event_judges)

    def test_initialize_state(self):
        # Mock extract functions
        with patch(
            "are.simulation.validation.judge.extract_oracle_events"
        ) as mock_extract_oracle:
            with patch(
                "are.simulation.validation.judge.extract_tasks"
            ) as mock_extract_tasks:
                with patch(
                    "are.simulation.validation.judge.extract_user_details"
                ) as mock_extract_user_details:
                    # Set up mock returns
                    mock_extract_oracle.return_value = ([], {})
                    mock_extract_tasks.return_value = ["task1"]
                    mock_extract_user_details.return_value = self.user_details

                    # Call initialize_state
                    self.judge.initialize_state(self.scenario)

                    # Check state is initialized
                    self.assertTrue(self.judge.state.initialized)
                    self.assertEqual(self.judge.state.nb_turns, 1)
                    self.assertEqual(self.judge.state.turn_idx, -1)
                    self.assertEqual(self.judge.state.scenario_start_time, 100.0)
                    self.assertEqual(self.judge.state.scenario_tasks, ["task1"])
                    self.assertEqual(self.judge.state.user_details, self.user_details)
                    self.assertEqual(
                        self.judge.state.oracle_event_id_to_turn_idx, {"event1": 0}
                    )

    def test_update_state(self):
        # Initialize state first
        with patch(
            "are.simulation.validation.judge.extract_oracle_events"
        ) as mock_extract_oracle:
            with patch(
                "are.simulation.validation.judge.extract_tasks"
            ) as mock_extract_tasks:
                with patch(
                    "are.simulation.validation.judge.extract_user_details"
                ) as mock_extract_user:
                    mock_extract_oracle.return_value = ([], {})
                    mock_extract_tasks.return_value = ["task1"]
                    mock_extract_user.return_value = self.user_details
                    self.judge.initialize_state(self.scenario)

        # Mock extract_agent_events
        with patch(
            "are.simulation.validation.judge.extract_agent_events"
        ) as mock_extract_agent:
            mock_extract_agent.return_value = ["agent_event1"]

            # Call update_state
            self.judge.update_state(self.env)

            # Check state is updated
            self.assertEqual(self.judge.state.turn_idx, 0)
            self.assertEqual(self.judge.state.turn_to_agent_events, [["agent_event1"]])

    def test_check_tool_call_counts_success(self):
        # Test check_tool_call_counts with matching counts
        agent_counter = Counter({"tool1": 1, "tool2": 2})
        oracle_counter = Counter({"tool1": 1, "tool2": 2})

        result = self.judge.check_tool_call_counts(
            agent_counter, 1, oracle_counter, 1, 1
        )

        self.assertTrue(result.success)

    def test_check_tool_call_counts_failure(self):
        # Test check_tool_call_counts with mismatched counts
        agent_counter = Counter({"tool1": 1, "tool2": 2})
        oracle_counter = Counter({"tool1": 1, "tool2": 3})

        result = self.judge.check_tool_call_counts(
            agent_counter, 1, oracle_counter, 1, 1
        )

        self.assertFalse(result.success)
        self.assertIsInstance(result.failure, ToolCallCountsFailure)

    def test_preliminary_checks(self):
        # Mock get_count functionality
        agent_event = MagicMock(spec=CompletedEvent)
        agent_event.tool_name = "tool1"

        oracle_event = MagicMock(spec=CompletedOracleEvent)
        oracle_event.tool_name = "tool1"

        # Mock check_tool_call_counts
        with patch.object(self.judge, "check_tool_call_counts") as mock_check:
            mock_check.return_value = Judgment(success=True)

            # Call preliminary_checks
            result = self.judge.preliminary_checks([agent_event], [oracle_event])

            # Check result
            self.assertTrue(result.success)

    def test_match_env_oracle_event_success(self):
        # Initialize state
        self.judge.state = MagicMock(spec=GraphPerEventJudgeState)
        self.judge.state.current_turn_agent_events = [MagicMock(spec=CompletedEvent)]
        self.judge.state.agent_events = self.judge.state.current_turn_agent_events

        # Mock oracle event
        oracle_event = MagicMock(spec=CompletedOracleEvent)
        oracle_event.event_type = EventType.ENV
        oracle_event.event_id = "event1"

        # Mock event judge
        self.judge.event_judges[EventType.ENV] = MagicMock(return_value=True)

        # Call _match_env_oracle_event
        result = self.judge._match_env_oracle_event(oracle_event)

        # Check result
        self.assertTrue(result.success)
        self.judge.state.add_match.assert_called_once()

    def test_match_agent_oracle_event_success(self):
        # Initialize state
        self.judge.state = MagicMock(spec=GraphPerEventJudgeState)
        self.judge.state.current_turn_agent_events = [MagicMock(spec=CompletedEvent)]
        self.judge.state.agent_events = self.judge.state.current_turn_agent_events
        self.judge.state.agent_idx_to_oracle_id = {}
        self.judge.state.current_turn_oracle_graph = {"event1": []}

        # Mock oracle event
        oracle_event = MagicMock(spec=CompletedOracleEvent)
        oracle_event.event_type = EventType.AGENT
        oracle_event.event_id = "event1"
        oracle_event.tool_name = "test_tool"

        # Mock agent event judge
        self.judge.event_judges[EventType.AGENT] = MagicMock()
        self.judge.event_judges[EventType.AGENT].tool_judges = {
            "test_tool": MagicMock()
        }
        self.judge.event_judges[EventType.AGENT].__call__ = MagicMock(return_value=True)

        # Mock get_judge_kwargs
        with patch.object(self.judge, "get_judge_kwargs") as mock_get_kwargs:
            mock_get_kwargs.return_value = {}

            # Call _match_agent_oracle_event
            result = self.judge._match_agent_oracle_event(oracle_event)

            # Check result
            self.assertTrue(result.success)
            self.judge.state.add_match.assert_called_once()

    def test_inner_call_success(self):
        # Initialize state
        with patch(
            "are.simulation.validation.judge.extract_oracle_events"
        ) as mock_extract_oracle:
            with patch(
                "are.simulation.validation.judge.extract_tasks"
            ) as mock_extract_tasks:
                with patch(
                    "are.simulation.validation.judge.extract_user_details"
                ) as mock_extract_user:
                    mock_extract_oracle.return_value = ([], {})
                    mock_extract_tasks.return_value = ["task1"]
                    mock_extract_user.return_value = self.user_details
                    self.judge.initialize_state(self.scenario)

        # Mock update_state
        with patch.object(self.judge, "update_state"):
            # Mock preliminary_checks
            with patch.object(self.judge, "preliminary_checks") as mock_prelim:
                mock_prelim.return_value = Judgment(success=True)

                # Mock current_turn properties
                with patch.object(
                    type(self.judge.state),
                    "current_turn_agent_events",
                    new=[],
                ):
                    with patch.object(
                        type(self.judge.state),
                        "current_turn_oracle_events",
                        new=[],
                    ):
                        # Call inner_call
                        result = self.judge.inner_call(self.env)

                        # Check result
                        self.assertTrue(result.success)

    def test_call(self):
        # Mock inner_call
        with patch.object(self.judge, "inner_call") as mock_inner:
            mock_inner.return_value = Judgment(success=True)

            # Call __call__
            result = self.judge(self.env)

            # Check result
            self.assertIsInstance(result, Judgment)
            self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
