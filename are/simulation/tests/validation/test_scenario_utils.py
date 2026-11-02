# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import unittest
from unittest.mock import MagicMock, patch

import pytest

from are.simulation.apps.contacts import Contact, ContactsApp
from are.simulation.environment import Environment
from are.simulation.scenarios import Scenario
from are.simulation.types import (
    AbstractEnvironment,
    CompletedEvent,
    CompletedOracleEvent,
    EventLog,
)
from are.simulation.validation.utils.event_utils import EventFilter
from are.simulation.validation.utils.scenario_utils import (
    extract_agent_events,
    extract_oracle_events,
    extract_oracle_graph,
    extract_tasks,
    extract_user_name,
    order_events_topologically,
    run_oracle_mode,
    topological_sort,
    validate_scenario_attribute,
)


class TestScenarioUtils(unittest.TestCase):
    def setUp(self):
        # Create mock scenario
        self.scenario = MagicMock(spec=Scenario)
        self.scenario.oracle_run_event_log = []
        self.scenario.event_id_to_turn_idx = {}
        self.scenario.events = []
        self.scenario.nb_turns = 3
        self.scenario._initialized = False
        self.scenario.start_time = 0
        self.scenario.duration = 100
        self.scenario.time_increment_in_seconds = 1

        # Create mock environment
        self.env = MagicMock(spec=AbstractEnvironment)
        self.env.event_log = MagicMock()
        self.env.event_log.list_view.return_value = []

        # Create mock event filter
        self.event_filter = MagicMock(spec=EventFilter)
        self.event_filter.return_value = True

    def test_validate_scenario_attribute_success(self):
        # Test when scenario has required attributes
        validate_scenario_attribute(self.scenario)

    def test_validate_scenario_attribute_missing_oracle_run_event_log(self):
        # Test when scenario is missing oracle_run_event_log
        self.scenario.oracle_run_event_log = None
        with pytest.raises(ValueError, match="Oracle run event log not found"):
            validate_scenario_attribute(self.scenario)

    def test_validate_scenario_attribute_missing_event_id_to_turn_idx(self):
        # Test when scenario is missing event_id_to_turn_idx
        self.scenario.event_id_to_turn_idx = None
        with pytest.raises(ValueError, match="Event id to turn not found"):
            validate_scenario_attribute(self.scenario)

    def test_extract_tasks(self):
        # Create mock events for tasks
        task_event1 = MagicMock()
        task_event1.action.class_name = "AgentUserInterface"
        task_event1.action.function_name = "send_message_to_agent"
        task_event1.action.args = {"content": "Task 1"}
        task_event1.event_id = "event1"

        task_event2 = MagicMock()
        task_event2.action.class_name = "AgentUserInterface"
        task_event2.action.function_name = "send_message_to_agent"
        task_event2.action.args = {"content": "Task 2"}
        task_event2.event_id = "event2"

        # Set up scenario with mock events
        self.scenario.oracle_run_event_log = [task_event1, task_event2]
        self.scenario.event_id_to_turn_idx = {"event1": 0, "event2": 1}

        # Test extract_tasks
        tasks = extract_tasks(self.scenario)
        self.assertEqual(len(tasks), 3)  # nb_turns = 3
        self.assertEqual(tasks[0], "Task 1\n")
        self.assertEqual(tasks[1], "Task 2\n")
        self.assertEqual(tasks[2], "")  # Empty task for turn 2

    def test_extract_user_name(self):
        # Create mock contacts app
        contacts_app = MagicMock(spec=ContactsApp)
        contacts_app.name = "contacts_app"
        user_contact = Contact(
            first_name="Test",
            last_name="User",
            is_user=True,
            phone="123456789",
        )
        contacts_app.contacts = {"user": user_contact}

        # Set up scenario with mock apps
        self.scenario.apps = [contacts_app]

        # Test extract_user_name
        user_name = extract_user_name(self.scenario)
        self.assertEqual(user_name, "test user")

    def test_extract_user_name_no_contacts_app(self):
        # Test when scenario has no contacts app
        self.scenario.apps = []

        # Test extract_user_name
        with patch("are.simulation.validation.utils.scenario_utils.logger"):
            user_name = extract_user_name(self.scenario)
            self.assertIsNone(user_name)

    def test_extract_agent_events(self):
        # Create mock events
        event1 = MagicMock(spec=CompletedEvent)
        event1.event_id = "event1"
        event1.event_time = 1

        event2 = MagicMock(spec=CompletedEvent)
        event2.event_id = "event2"
        event2.event_time = 2

        event_send_message = MagicMock(spec=CompletedEvent)
        event_send_message.event_id = "event_send_message"
        event_send_message.event_time = 3

        event3 = MagicMock(spec=CompletedEvent)
        event3.event_id = "event3"
        event3.event_time = 4

        # Set up environment with mock events
        self.env.event_log.list_view.return_value = [
            event1,
            event2,
            event_send_message,
            event3,
        ]

        # Mock is_send_message_to_user to return True for event2
        with patch(
            "are.simulation.validation.utils.scenario_utils.is_send_message_to_user",
            side_effect=[False, False, True, False],
        ):
            # Test extract_agent_events for turn_idx=0
            events = extract_agent_events(self.env, self.event_filter, turn_idx=0)
            self.assertEqual(len(events), 3)
            self.assertEqual(events[0], event1)

    def test_extract_oracle_graph(self):
        # Create mock events with dependencies
        event1 = MagicMock()
        event1.event_id = "event1"
        event1.dependencies = []

        event2 = MagicMock()
        event2.event_id = "event2"
        event2.dependencies = [event1]

        # Test extract_oracle_graph
        graph = extract_oracle_graph([event1, event2], ["event1", "event2"])
        self.assertEqual(graph["event1"], [])
        self.assertEqual(graph["event2"], ["event1"])

    def test_topological_sort(self):
        # Create a graph for topological sort
        graph = {
            "event1": [],
            "event2": ["event1"],
            "event3": ["event1", "event2"],
        }

        # Test topological_sort
        sorted_events = topological_sort(graph)
        self.assertEqual(sorted_events, ["event1", "event2", "event3"])

    def test_topological_sort_cycle(self):
        # Create a graph with a cycle
        graph = {
            "event1": ["event3"],
            "event2": ["event1"],
            "event3": ["event2"],
        }

        # Test topological_sort with cycle
        with pytest.raises(ValueError, match="Graph contains a cycle"):
            topological_sort(graph)

    def test_order_events_topologically(self):
        # Create mock events
        event1 = MagicMock(spec=CompletedEvent)
        event1.event_id = "event1"

        event2 = MagicMock(spec=CompletedEvent)
        event2.event_id = "event2"

        event3 = MagicMock(spec=CompletedEvent)
        event3.event_id = "event3"

        # Create a graph for topological ordering
        graph = {
            "event1": [],
            "event2": ["event1"],
            "event3": ["event1", "event2"],
        }

        # Test order_events_topologically
        ordered_events = order_events_topologically(graph, [event3, event1, event2])
        self.assertEqual(len(ordered_events), 3)
        self.assertEqual(ordered_events[0].event_id, "event1")
        self.assertEqual(ordered_events[1].event_id, "event2")
        self.assertEqual(ordered_events[2].event_id, "event3")

    def test_extract_oracle_events(self):
        # Create mock oracle events
        oracle_event1 = MagicMock(spec=CompletedEvent)
        oracle_event1.event_id = "event1"

        oracle_event2 = MagicMock(spec=CompletedEvent)
        oracle_event2.event_id = "event2"

        # Set up scenario with mock events
        self.scenario.oracle_run_event_log = [oracle_event1, oracle_event2]
        self.scenario.event_id_to_turn_idx = {"event1": 0, "event2": 0}
        self.scenario.events = [oracle_event1, oracle_event2]

        # Mock extract_oracle_graph
        with patch(
            "are.simulation.validation.utils.scenario_utils.extract_oracle_graph",
            return_value={"event1": [], "event2": ["event1"]},
        ):
            # Mock order_events_topologically
            with patch(
                "are.simulation.validation.utils.scenario_utils.order_events_topologically",
                return_value=[oracle_event1, oracle_event2],
            ):
                # Mock CompletedOracleEvent.from_completed_event_and_oracle_event
                with patch(
                    "are.simulation.validation.utils.scenario_utils.CompletedOracleEvent.from_completed_event_and_oracle_event",
                    side_effect=[
                        MagicMock(spec=CompletedOracleEvent),
                        MagicMock(spec=CompletedOracleEvent),
                    ],
                ):
                    # Test extract_oracle_events
                    events, graph = extract_oracle_events(
                        self.scenario, self.event_filter, 0
                    )
                    self.assertEqual(len(events), 2)
                    self.assertEqual(graph, {"event1": [], "event2": ["event1"]})

    def test_run_oracle_mode(self):
        # Mock Environment
        mock_env = MagicMock(spec=Environment)
        mock_env.event_log = MagicMock(spec=EventLog)
        mock_env.event_log.list_view.return_value = []

        # Mock Environment constructor
        with patch("are.simulation.environment.Environment", return_value=mock_env):
            # Mock build_event_id_to_turn_idx
            with patch(
                "are.simulation.validation.utils.scenario_utils.build_event_id_to_turn_idx"
            ):
                # Test run_oracle_mode
                run_oracle_mode(self.scenario)

                # Verify scenario was initialized if not already
                self.scenario.initialize.assert_called_once()

                # Verify environment was run with scenario
                mock_env.run.assert_called_once_with(self.scenario)

                # Verify environment was stopped
                mock_env.stop.assert_called_once()

                # Verify scenario was reset
                self.scenario.soft_reset.assert_called_once()

                # Verify oracle_run_event_log was set
                self.assertEqual(self.scenario.oracle_run_event_log, [])

    def test_run_oracle_mode_failure(self):
        # Create mock failed event
        failed_event = MagicMock()
        failed_event.failed.return_value = True
        failed_event.metadata.exception = "Test exception"

        # Mock Environment
        mock_env = MagicMock(spec=Environment)
        mock_env.event_log = MagicMock(spec=EventLog)
        mock_env.event_log.list_view.return_value = [failed_event]

        # Mock Environment constructor
        with patch("are.simulation.environment.Environment", return_value=mock_env):
            # Mock build_event_id_to_turn_idx
            with patch(
                "are.simulation.validation.utils.scenario_utils.build_event_id_to_turn_idx"
            ):
                # Test run_oracle_mode with failed event
                with pytest.raises(Exception, match="Oracle run failed:"):
                    run_oracle_mode(self.scenario)


if __name__ == "__main__":
    unittest.main()
