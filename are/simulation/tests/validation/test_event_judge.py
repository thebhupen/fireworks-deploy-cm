# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import unittest
from unittest.mock import MagicMock, patch

from are.simulation.types import CompletedEvent, EventTimeComparator, EventType
from are.simulation.validation.configs import (
    AgentEventJudgeConfig,
    EnvUserEventJudgeConfig,
)
from are.simulation.validation.constants import CheckerType
from are.simulation.validation.event_judge import AgentEventJudge, EnvUserEventJudge
from are.simulation.validation.utils.scenario_utils import CompletedOracleEvent


class TestEnvUserEventJudge(unittest.TestCase):
    def setUp(self):
        # Create mock config
        self.config = MagicMock(spec=EnvUserEventJudgeConfig)
        self.config.tracer = None
        self.event_type = EventType.ENV

        # Create judge
        self.judge = EnvUserEventJudge(self.event_type, self.config)

        # Create mock events
        self.agent_event = MagicMock(spec=CompletedEvent)
        self.oracle_event = MagicMock(spec=CompletedOracleEvent)
        self.agent_event.event_id = "test_event_id"
        self.oracle_event.event_id = "test_event_id"

    def test_init(self):
        # Test initialization
        self.assertEqual(self.judge.event_type, self.event_type)
        self.assertEqual(self.judge.judge_type, "env-user")

    def test_eq_checker(self):
        # Test eq_checker
        self.assertTrue(self.judge.eq_checker("value", "value"))
        self.assertFalse(self.judge.eq_checker("value1", "value2"))
        self.assertTrue(self.judge.eq_checker(None, None))
        self.assertFalse(self.judge.eq_checker("value", None))

    def test_compare_success(self):
        # Test compare method with successful comparison
        result = self.judge.compare(self.agent_event, self.oracle_event)
        self.assertTrue(result)

    def test_compare_failure(self):
        # Test compare method with failed comparison
        self.agent_event.event_id = "different_event_id"
        result = self.judge.compare(self.agent_event, self.oracle_event)
        self.assertFalse(result)


class TestAgentEventJudge(unittest.TestCase):
    def setUp(self):
        # Create mock config
        self.config = MagicMock(spec=AgentEventJudgeConfig)
        self.config.per_tool_arg_to_checker_type = {
            "test_tool": {"arg1": CheckerType.llm_checker}
        }
        self.config.per_tool_soft_checker_types = {}
        self.config.event_id_to_checker_params = None
        self.config.engine = MagicMock()
        self.config.pre_event_tolerance_seconds = 5.0
        self.config.post_event_tolerance_seconds = 20.0
        self.config.check_time_threshold_seconds = 10.0
        self.config.tracer = None

        # Create judge
        self.judge = AgentEventJudge(self.config)

        # Create mock events
        self.agent_event = MagicMock(spec=CompletedEvent)
        self.oracle_event = MagicMock(spec=CompletedOracleEvent)
        self.agent_event.tool_name = "test_tool"
        self.oracle_event.tool_name = "test_tool"
        self.agent_event.event_time = 100.0
        self.oracle_event.event_time = 100.0
        self.oracle_event.event_time_comparator = None
        self.oracle_event.absolute_event_time = None

    def test_init(self):
        # Test initialization
        self.assertEqual(self.judge.config, self.config)
        self.assertEqual(self.judge.event_type, EventType.AGENT)
        self.assertEqual(self.judge.judge_type, "agent")
        self.assertIn("test_tool", self.judge.tool_judges)

    def test_event_time_checker_equal(self):
        # Test event_time_checker with EQUAL comparator
        result = self.judge.event_time_checker(
            agent_event_time=100.0,
            oracle_event_time=100.0,
            pre_event_tolerance_seconds=5.0,
            post_event_tolerance_seconds=20.0,
            event_time_comparator=None,
        )
        self.assertTrue(result)

        # Test within tolerance
        result = self.judge.event_time_checker(
            agent_event_time=105.0,
            oracle_event_time=100.0,
            pre_event_tolerance_seconds=5.0,
            post_event_tolerance_seconds=20.0,
            event_time_comparator=None,
        )
        self.assertTrue(result)

        # Test outside tolerance
        result = self.judge.event_time_checker(
            agent_event_time=125.0,
            oracle_event_time=100.0,
            pre_event_tolerance_seconds=5.0,
            post_event_tolerance_seconds=20.0,
            event_time_comparator=None,
        )
        self.assertFalse(result)

    def test_event_time_checker_less_than(self):
        # Test event_time_checker with LESS_THAN comparator
        result = self.judge.event_time_checker(
            agent_event_time=100.0,
            oracle_event_time=100.0,
            pre_event_tolerance_seconds=5.0,
            post_event_tolerance_seconds=20.0,
            event_time_comparator=EventTimeComparator.LESS_THAN.value,
        )
        self.assertTrue(result)

        # Test within tolerance
        result = self.judge.event_time_checker(
            agent_event_time=120.0,
            oracle_event_time=100.0,
            pre_event_tolerance_seconds=5.0,
            post_event_tolerance_seconds=20.0,
            event_time_comparator=EventTimeComparator.LESS_THAN.value,
        )
        self.assertTrue(result)

        # Test outside tolerance
        result = self.judge.event_time_checker(
            agent_event_time=121.0,
            oracle_event_time=100.0,
            pre_event_tolerance_seconds=5.0,
            post_event_tolerance_seconds=20.0,
            event_time_comparator=EventTimeComparator.LESS_THAN.value,
        )
        self.assertFalse(result)

    def test_event_time_checker_greater_than(self):
        # Test event_time_checker with GREATER_THAN comparator
        result = self.judge.event_time_checker(
            agent_event_time=100.0,
            oracle_event_time=100.0,
            pre_event_tolerance_seconds=5.0,
            post_event_tolerance_seconds=20.0,
            event_time_comparator=EventTimeComparator.GREATER_THAN.value,
        )
        self.assertTrue(result)

        # Test within tolerance
        result = self.judge.event_time_checker(
            agent_event_time=95.0,
            oracle_event_time=100.0,
            pre_event_tolerance_seconds=5.0,
            post_event_tolerance_seconds=20.0,
            event_time_comparator=EventTimeComparator.GREATER_THAN.value,
        )
        self.assertTrue(result)

        # Test outside tolerance
        result = self.judge.event_time_checker(
            agent_event_time=94.0,
            oracle_event_time=100.0,
            pre_event_tolerance_seconds=5.0,
            post_event_tolerance_seconds=20.0,
            event_time_comparator=EventTimeComparator.GREATER_THAN.value,
        )
        self.assertFalse(result)

    def test_event_time_checker_invalid_comparator(self):
        # Test event_time_checker with invalid comparator
        with self.assertRaises(ValueError):
            self.judge.event_time_checker(
                agent_event_time=100.0,
                oracle_event_time=100.0,
                pre_event_tolerance_seconds=5.0,
                post_event_tolerance_seconds=20.0,
                event_time_comparator="INVALID",
            )

    def test_check_time_absolute_time(self):
        # Test check_time with absolute event time
        self.oracle_event.absolute_event_time = 100.0
        result = self.judge.check_time(
            agent_event=self.agent_event,
            oracle_event=self.oracle_event,
            max_parent_oracle_event_time=0.0,
            max_parent_agent_event_time=0.0,
        )
        self.assertTrue(result)

        # Test outside tolerance
        self.agent_event.event_time = 130.0
        result = self.judge.check_time(
            agent_event=self.agent_event,
            oracle_event=self.oracle_event,
            max_parent_oracle_event_time=0.0,
            max_parent_agent_event_time=0.0,
        )
        self.assertFalse(result)

    def test_check_time_relative_time(self):
        # Test check_time with relative event time
        self.agent_event.event_time = 110.0
        self.oracle_event.event_time = 110.0
        result = self.judge.check_time(
            agent_event=self.agent_event,
            oracle_event=self.oracle_event,
            max_parent_oracle_event_time=100.0,
            max_parent_agent_event_time=100.0,
        )
        self.assertTrue(result)

        # Test with time difference above threshold
        self.oracle_event.event_time = 120.0
        result = self.judge.check_time(
            agent_event=self.agent_event,
            oracle_event=self.oracle_event,
            max_parent_oracle_event_time=100.0,
            max_parent_agent_event_time=100.0,
        )
        self.assertFalse(result)

    def test_check_time_with_comparator(self):
        # Test check_time with event time comparator
        self.oracle_event.event_time_comparator = EventTimeComparator.LESS_THAN
        result = self.judge.check_time(
            agent_event=self.agent_event,
            oracle_event=self.oracle_event,
            max_parent_oracle_event_time=0.0,
            max_parent_agent_event_time=0.0,
        )
        self.assertTrue(result)

    def test_compare(self):
        # Test compare method
        with patch.object(self.judge, "check_time", return_value=True):
            with patch(
                "are.simulation.validation.tool_judge.MildToolJudge.__call__",
                return_value=True,
            ):
                result = self.judge.compare(self.agent_event, self.oracle_event)
                self.assertTrue(result)

                # Test with failed time check
                with patch.object(self.judge, "check_time", return_value=False):
                    result = self.judge.compare(self.agent_event, self.oracle_event)
                    self.assertFalse(result)

                # Test with failed tool judge
                with patch.object(self.judge, "check_time", return_value=True):
                    with patch(
                        "are.simulation.validation.tool_judge.MildToolJudge.__call__",
                        return_value=False,
                    ):
                        result = self.judge.compare(self.agent_event, self.oracle_event)
                        self.assertFalse(result)

    def test_compare_tool_not_found(self):
        # Test compare with tool not found
        self.oracle_event.tool_name = "unknown_tool"
        with self.assertRaises(AssertionError):
            self.judge.compare(self.agent_event, self.oracle_event)


if __name__ == "__main__":
    unittest.main()
