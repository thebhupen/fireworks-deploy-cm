# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import unittest
from unittest.mock import MagicMock, patch

from are.simulation.types import CompletedEvent
from are.simulation.validation.configs import (
    HardToolJudgeConfig,
    MildToolJudgeConfig,
    SoftToolJudgeConfig,
)
from are.simulation.validation.constants import CheckerType, SoftCheckerType
from are.simulation.validation.tool_judge import (
    HardToolJudge,
    MildToolJudge,
    SoftToolJudge,
)
from are.simulation.validation.utils.scenario_utils import CompletedOracleEvent


class TestHardToolJudge(unittest.TestCase):
    def setUp(self):
        # Create mock config
        self.config = MagicMock(spec=HardToolJudgeConfig)
        self.config.tool_name = "test_tool"
        self.config.arg_to_checker_type = {
            "arg1": CheckerType.eq_checker,
            "arg2": CheckerType.unordered_list_checker,
        }
        self.config.event_id_to_checker_params = None
        self.config.tracer = None

        # Create judge
        self.judge = HardToolJudge(self.config)

        # Create mock events
        self.agent_event = MagicMock(spec=CompletedEvent)
        self.oracle_event = MagicMock(spec=CompletedOracleEvent)
        self.agent_event.get_args.return_value = {"arg1": "value1", "arg2": [1, 2, 3]}
        self.oracle_event.get_args.return_value = {"arg1": "value1", "arg2": [3, 1, 2]}
        self.oracle_event.event_id = "test_event_id"

    def test_init(self):
        # Test initialization
        self.assertEqual(self.judge.config, self.config)
        self.assertEqual(len(self.judge.checkers), 10)  # 10 checker types
        self.assertIn(CheckerType.eq_checker.value, self.judge.checkers)
        self.assertIn(CheckerType.unordered_list_checker.value, self.judge.checkers)

    def test_eq_checker(self):
        # Test eq_checker
        self.assertTrue(self.judge.eq_checker("value", "value"))
        self.assertFalse(self.judge.eq_checker("value1", "value2"))
        self.assertTrue(self.judge.eq_checker(None, None))
        self.assertFalse(self.judge.eq_checker("value", None))

    def test_unordered_list_checker(self):
        # Test unordered_list_checker
        self.assertTrue(self.judge.unordered_list_checker([1, 2, 3], [3, 2, 1]))
        self.assertFalse(self.judge.unordered_list_checker([1, 2, 3], [1, 2, 4]))
        self.assertTrue(self.judge.unordered_list_checker(None, None))
        self.assertTrue(self.judge.unordered_list_checker(None, []))
        self.assertTrue(self.judge.unordered_list_checker([], None))

    def test_path_checker(self):
        # Test path_checker
        self.assertTrue(self.judge.path_checker("/path/to/file", "/path/to/file"))
        self.assertTrue(self.judge.path_checker("/path/to/file", "path/to/file"))
        self.assertTrue(self.judge.path_checker("path/to/file", "/path/to/file"))
        self.assertTrue(self.judge.path_checker("path/to/file/", "path/to/file"))
        self.assertFalse(self.judge.path_checker("/path/to/file1", "/path/to/file2"))
        self.assertTrue(self.judge.path_checker(None, None))
        self.assertFalse(self.judge.path_checker("/path/to/file", None))

    def test_unordered_path_list_checker(self):
        # Test unordered_path_list_checker
        self.assertTrue(
            self.judge.unordered_path_list_checker(
                ["/path/to/file1", "/path/to/file2"],
                ["path/to/file2", "path/to/file1"],
            )
        )
        self.assertFalse(
            self.judge.unordered_path_list_checker(
                ["/path/to/file1", "/path/to/file2"],
                ["/path/to/file1", "/path/to/file3"],
            )
        )
        self.assertTrue(self.judge.unordered_path_list_checker(None, None))
        self.assertTrue(self.judge.unordered_path_list_checker(None, []))
        self.assertTrue(self.judge.unordered_path_list_checker([], None))

    def test_unordered_str_list_with_tolerance_checker(self):
        # Test unordered_str_list_with_tolerance_checker
        self.assertTrue(
            self.judge.unordered_str_list_with_tolerance_checker(
                ["a", "b", "c"], ["c", "b", "a"]
            )
        )
        self.assertTrue(
            self.judge.unordered_str_list_with_tolerance_checker(
                ["a", "b", "c", "ignore"],
                ["c", "b", "a"],
                tolerance_list_str=["ignore"],
            )
        )
        self.assertFalse(
            self.judge.unordered_str_list_with_tolerance_checker(
                ["a", "b", "c"], ["a", "b", "d"]
            )
        )
        # Test case insensitivity
        self.assertTrue(
            self.judge.unordered_str_list_with_tolerance_checker(
                ["A", "B", "C"], ["c", "b", "a"]
            )
        )

    def test_datetime_checker(self):
        # Test datetime_checker
        self.assertTrue(
            self.judge.datetime_checker("2023-01-01 12:00:00", "2023-01-01 12:00:00")
        )
        self.assertFalse(
            self.judge.datetime_checker("2023-01-01 12:00:00", "2023-01-01 12:01:00")
        )
        self.assertTrue(self.judge.datetime_checker(None, None))
        self.assertFalse(self.judge.datetime_checker("2023-01-01 12:00:00", None))

    def test_eq_str_strip_checker(self):
        # Test eq_str_strip_checker
        self.assertTrue(self.judge.eq_str_strip_checker("value", "value"))
        self.assertTrue(self.judge.eq_str_strip_checker("  value  ", "value"))
        self.assertTrue(self.judge.eq_str_strip_checker("value", "  value  "))
        self.assertFalse(self.judge.eq_str_strip_checker("value1", "value2"))
        self.assertTrue(self.judge.eq_str_strip_checker("", None))
        self.assertTrue(self.judge.eq_str_strip_checker(None, ""))

    def test_phone_number_checker(self):
        # Test phone_number_checker
        self.assertTrue(self.judge.phone_number_checker("123-456-7890", "1234567890"))
        self.assertTrue(self.judge.phone_number_checker("(123) 456-7890", "1234567890"))
        self.assertFalse(self.judge.phone_number_checker("123-456-7890", "1234567891"))
        self.assertTrue(self.judge.phone_number_checker(None, None))
        self.assertFalse(self.judge.phone_number_checker("123-456-7890", None))

    def test_contain_any_checker(self):
        # Test contain_any_checker
        self.assertTrue(
            self.judge.contain_any_checker("This is a test", ["test", "example"])
        )
        self.assertFalse(
            self.judge.contain_any_checker("This is a test", ["example", "sample"])
        )
        # Test case insensitivity
        self.assertTrue(
            self.judge.contain_any_checker("This is a TEST", ["test", "example"])
        )

    def test_contain_all_checker(self):
        # Test contain_all_checker
        self.assertTrue(
            self.judge.contain_all_checker(
                "This is a test example", ["test", "example"]
            )
        )
        self.assertFalse(
            self.judge.contain_all_checker("This is a test", ["test", "example"])
        )
        # Test case insensitivity
        self.assertTrue(
            self.judge.contain_all_checker(
                "This is a TEST EXAMPLE", ["test", "example"]
            )
        )

    def test_compare_success(self):
        # Test compare method with successful comparison
        result = self.judge.compare(self.agent_event, self.oracle_event)
        self.assertTrue(result)

    def test_compare_failure(self):
        # Test compare method with failed comparison
        self.agent_event.get_args.return_value = {"arg1": "value1", "arg2": [1, 2, 4]}
        result = self.judge.compare(self.agent_event, self.oracle_event)
        self.assertFalse(result)

    def test_compare_with_event_id_checker_params(self):
        # Test compare with event_id_to_checker_params
        checker_params = MagicMock()
        checker_params.checker_type = CheckerType.eq_checker
        checker_params.arg_name = "arg3"
        checker_params.checker_args = {}

        self.config.event_id_to_checker_params = {"test_event_id": [checker_params]}

        self.agent_event.get_args.return_value = {
            "arg1": "value1",
            "arg2": [1, 2, 3],
            "arg3": "value3",
        }
        self.oracle_event.get_args.return_value = {
            "arg1": "value1",
            "arg2": [3, 1, 2],
            "arg3": "value3",
        }

        result = self.judge.compare(self.agent_event, self.oracle_event)
        self.assertTrue(result)

        # Test with failing checker
        self.agent_event.get_args.return_value["arg3"] = "different_value"
        result = self.judge.compare(self.agent_event, self.oracle_event)
        self.assertFalse(result)


class TestSoftToolJudge(unittest.TestCase):
    def setUp(self):
        # Create mock config
        self.config = MagicMock(spec=SoftToolJudgeConfig)
        self.config.tool_name = "test_tool"
        self.config.arg_to_checker_type = {
            "arg1": CheckerType.eq_checker,
            "arg2": CheckerType.llm_checker,
        }
        self.config.soft_checker_types = []
        self.config.tracer = None
        self.config.engine = MagicMock()

        # Create judge
        self.judge = SoftToolJudge(self.config)

        # Create mock events
        self.agent_event = MagicMock(spec=CompletedEvent)
        self.oracle_event = MagicMock(spec=CompletedOracleEvent)
        self.agent_event.get_args.return_value = {"arg1": "value1", "arg2": "content"}
        self.oracle_event.get_args.return_value = {"arg1": "value1", "arg2": "content"}
        self.oracle_event.event_id = "test_event_id"
        self.oracle_event.event_time = 1672531200  # 2023-01-01 00:00:00 UTC

    def test_init(self):
        # Test initialization
        self.assertEqual(self.judge.config, self.config)
        self.assertEqual(self.judge.engine, self.config.engine)
        self.assertEqual(
            len(self.judge.selected_action_args), 1
        )  # Only arg2 is llm_checker
        self.assertIn("arg2", self.judge.selected_action_args)
        self.assertFalse(self.judge.no_arg_to_check)
        self.assertEqual(len(self.judge.soft_checkers), 10)  # 10 soft checker types
        self.assertIsNotNone(self.judge.subtask_extractor)
        self.assertIsNotNone(self.judge.llm_checkers)

    def test_init_no_args_to_check(self):
        # Test initialization with no llm_checker args
        config_no_llm = MagicMock(spec=SoftToolJudgeConfig)
        config_no_llm.tool_name = "test_tool"
        config_no_llm.arg_to_checker_type = {"arg1": CheckerType.eq_checker}
        config_no_llm.soft_checker_types = []
        config_no_llm.tracer = None
        config_no_llm.engine = MagicMock()

        judge = SoftToolJudge(config_no_llm)
        self.assertTrue(judge.no_arg_to_check)
        self.assertEqual(len(judge.selected_action_args), 0)

    def test_describe_action_args(self):
        # Test describe_action_args method
        args = {"arg1": "value1", "arg2": "value2", "arg3": "value3"}
        result = self.judge.describe_action_args(args)
        expected_lines = ["arg1: value1", "arg2: value2", "arg3: value3"]
        for line in expected_lines:
            self.assertIn(line, result)

    def test_equality_checker(self):
        # Test equality_checker with matching args
        agent_args = {"arg1": "value1", "arg2": "value2"}
        oracle_args = {"arg1": "value1", "arg2": "value2"}
        result = self.judge.equality_checker(agent_args, oracle_args)
        self.assertTrue(result)

        # Test with non-matching args
        agent_args = {"arg1": "value1", "arg2": "different_value"}
        result = self.judge.equality_checker(agent_args, oracle_args)
        self.assertFalse(result)

    def test_placeholder_checker_success(self):
        # Test placeholder_checker with valid content
        agent_args = {"message": "Hello, this is a valid message without placeholders."}
        result = self.judge.placeholder_checker(agent_args)
        self.assertTrue(result)

    def test_placeholder_checker_failure(self):
        # Test placeholder_checker with placeholders
        test_cases = [
            {"message": "Hello [User's Name], how are you?"},
            {"message": "Best regards,\nYour Name"},
            {"message": "Dear [User], thank you for your inquiry."},
            {"message": "From: [Your Name]"},
        ]

        for agent_args in test_cases:
            with self.subTest(args=agent_args):
                result = self.judge.placeholder_checker(agent_args)
                self.assertFalse(result)

    def test_extract_subtask(self):
        # Test extract_subtask method
        with patch.object(self.judge, "subtask_extractor") as mock_extractor:
            mock_extractor.return_value = "<subtask>Send an email to John</subtask>"

            result = self.judge.extract_subtask(
                "send_email(to='john@example.com')", "Complete the task"
            )
            self.assertEqual(result, "Send an email to John")
            mock_extractor.assert_called_once()

        # Test with empty task
        result = self.judge.extract_subtask("action_call", "")
        self.assertEqual(result, "")

        # Test with None response from extractor
        with patch.object(self.judge, "subtask_extractor") as mock_extractor:
            mock_extractor.return_value = None
            result = self.judge.extract_subtask("action_call", "task")
            self.assertEqual(result, "")

    def test_get_checker_kwargs(self):
        # Test get_checker_kwargs method
        user_details = MagicMock()
        user_details.first_name = "John"
        user_details.last_name = "Doe"
        user_details.address = "123 Main St"

        kwargs = {
            "tasks": ["Previous task", "Current task"],
            "user_details": user_details,
        }
        oracle_args = {"arg1": "value1"}

        with patch.object(self.judge, "extract_subtask") as mock_extract:
            mock_extract.return_value = "Extracted subtask"
            self.judge.need_subtask = True

            result = self.judge.get_checker_kwargs(
                kwargs, self.oracle_event, oracle_args
            )

            expected_keys = [
                "task",
                "previous_task",
                "user_name",
                "user_address",
                "today_date",
                "oracle_args",
                "subtask",
            ]
            for key in expected_keys:
                self.assertIn(key, result)

            self.assertEqual(result["task"], "Current task")
            self.assertEqual(result["user_name"], "John Doe")
            self.assertEqual(result["user_address"], "123 Main St")
            self.assertEqual(result["oracle_args"], oracle_args)
            self.assertEqual(result["subtask"], "Extracted subtask")

    def test_compare_no_args_to_check(self):
        # Test compare when no_arg_to_check is True
        self.judge.no_arg_to_check = True
        result = self.judge.compare(self.agent_event, self.oracle_event)
        self.assertTrue(result)

    def test_compare_equality_checker_success(self):
        # Test compare when equality_checker passes
        with patch.object(self.judge, "equality_checker") as mock_equality:
            mock_equality.return_value = True
            result = self.judge.compare(self.agent_event, self.oracle_event)
            self.assertTrue(result)

    def test_compare_with_soft_checkers(self):
        # Test compare with soft checkers
        from are.simulation.validation.configs import SoftCheckerType

        # Mock soft checker that returns True
        mock_checker = MagicMock(return_value=True)
        self.judge.soft_checkers[SoftCheckerType.sanity_checker.value] = mock_checker
        self.config.soft_checker_types = [SoftCheckerType.sanity_checker]

        with patch.object(self.judge, "equality_checker") as mock_equality:
            mock_equality.return_value = False
            with patch.object(self.judge, "get_checker_kwargs") as mock_get_kwargs:
                mock_get_kwargs.return_value = {"task": "test task"}

                result = self.judge.compare(self.agent_event, self.oracle_event)
                self.assertTrue(result)
                mock_checker.assert_called_once()

    def test_compare_soft_checker_failure(self):
        # Test compare when soft checker fails
        from are.simulation.validation.configs import SoftCheckerType

        # Mock soft checker that returns False
        mock_checker = MagicMock(return_value=False)
        self.judge.soft_checkers[SoftCheckerType.sanity_checker.value] = mock_checker
        self.config.soft_checker_types = [SoftCheckerType.sanity_checker]

        with patch.object(self.judge, "equality_checker") as mock_equality:
            mock_equality.return_value = False
            with patch.object(self.judge, "get_checker_kwargs") as mock_get_kwargs:
                mock_get_kwargs.return_value = {"task": "test task"}

                result = self.judge.compare(self.agent_event, self.oracle_event)
                self.assertFalse(result)

    def test_llm_checker_methods(self):
        # Test that LLM checker methods call the appropriate llm_checkers
        test_cases = [
            (
                SoftCheckerType.content_checker.value,
                {
                    "agent_args": {"content": "test"},
                    "oracle_args": {"content": "oracle"},
                    "today_date": "2023-01-01",
                    "user_address": "123 Main St",
                    "subtask": "test subtask",
                },
            ),
            (
                SoftCheckerType.signature_checker.value,
                {"agent_args": {"content": "test"}, "user_name": "John Doe"},
            ),
            (
                SoftCheckerType.sanity_checker.value,
                {"agent_args": {"content": "test"}, "task": "test task"},
            ),
            (
                SoftCheckerType.cab_checker.value,
                {
                    "agent_args": {"content": "test"},
                    "oracle_args": {"content": "oracle"},
                    "user_address": "123 Main St",
                },
            ),
            (
                SoftCheckerType.email_checker.value,
                {
                    "agent_args": {"content": "test"},
                    "oracle_args": {"content": "oracle"},
                    "today_date": "2023-01-01",
                },
            ),
            (
                SoftCheckerType.message_checker.value,
                {
                    "agent_args": {"content": "test"},
                    "oracle_args": {"content": "oracle"},
                    "today_date": "2023-01-01",
                },
            ),
            (
                SoftCheckerType.event_checker.value,
                {
                    "agent_args": {"content": "test"},
                    "oracle_args": {"content": "oracle"},
                    "user_address": "123 Main St",
                    "subtask": "test subtask",
                },
            ),
            (
                SoftCheckerType.user_message_checker.value,
                {
                    "agent_args": {"content": "test"},
                    "oracle_args": {"content": "oracle"},
                    "subtask": "test subtask",
                },
            ),
            (SoftCheckerType.tone_checker.value, {"agent_args": {"content": "test"}}),
        ]

        for method_name, method_args in test_cases:
            with self.subTest(method=method_name):
                # Mock the llm_checkers to return True
                mock_llm_checker = MagicMock(return_value=True)
                with patch.dict(
                    self.judge.llm_checkers, {method_name: mock_llm_checker}
                ):
                    method = getattr(self.judge, method_name)
                    result = method(**method_args)

                    self.assertTrue(result)
                    mock_llm_checker.assert_called_once()

    def test_sanity_checker_numerical_values(self):
        # Test sanity_checker with valid numerical format
        agent_args = {"content": "42.5"}
        result = self.judge.sanity_checker(agent_args)
        self.assertTrue(result)

        # Test with integer
        agent_args = {"content": "123"}
        result = self.judge.sanity_checker(agent_args)
        self.assertTrue(result)

        # Test with invalid numerical format should use LLM checker
        agent_args = {"content": "not a number"}
        mock_llm_checker = MagicMock(return_value=True)
        with patch.dict(
            self.judge.llm_checkers,
            {SoftCheckerType.sanity_checker.value: mock_llm_checker},
        ):
            result = self.judge.sanity_checker(agent_args, task="test task")
            mock_llm_checker.assert_called_once()


class TestMildToolJudge(unittest.TestCase):
    def setUp(self):
        # Create mock config
        self.config = MagicMock(spec=MildToolJudgeConfig)
        self.config.tool_name = "test_tool"
        self.config.arg_to_checker_type = {
            "arg1": CheckerType.eq_checker,
            "arg2": CheckerType.llm_checker,
        }
        self.config.soft_checker_types = {}
        self.config.event_id_to_checker_params = None
        self.config.tracer = None
        self.config.engine = MagicMock()

        # Create judge
        self.judge = MildToolJudge(self.config)

        # Create mock events
        self.agent_event = MagicMock(spec=CompletedEvent)
        self.oracle_event = MagicMock(spec=CompletedOracleEvent)
        self.config.tool_name = "test_tool"
        self.agent_event.get_args.return_value = {"arg1": "value1", "arg2": "value2"}
        self.agent_event.tool_name = "test_tool"
        self.oracle_event.get_args.return_value = {"arg1": "value1", "arg2": "value2"}
        self.oracle_event.tool_name = "test_tool"

    def test_init(self):
        # Test initialization
        self.assertEqual(self.judge.config, self.config)
        self.assertIsInstance(self.judge.hard_judge, HardToolJudge)
        self.assertIsInstance(self.judge.soft_judge, SoftToolJudge)
        self.assertFalse(self.judge.soft_judge.no_arg_to_check)

    def test_init_with_scripted_checkers(self):
        # Test initialization with scripted checkers
        self.config.event_id_to_checker_params = {"event_id": []}
        judge = MildToolJudge(self.config)
        self.assertTrue(judge.soft_judge.no_arg_to_check)

    def test_compare_hard_judge_fails(self):
        # Test compare when hard judge fails
        with patch.object(self.judge, "hard_judge", return_value=False):
            result = self.judge.compare(self.agent_event, self.oracle_event)
            self.assertFalse(result)

    def test_compare_hard_judge_passes_soft_judge_skipped(self):
        # Test compare when hard judge passes and soft judge is skipped
        self.judge.soft_judge.no_arg_to_check = True
        with patch.object(self.judge, "hard_judge", return_value=True):
            result = self.judge.compare(self.agent_event, self.oracle_event)
            self.assertTrue(result)

    def test_compare_hard_judge_passes_soft_judge_passes(self):
        # Test compare when both judges pass
        with patch.object(self.judge, "hard_judge", return_value=True):
            with patch.object(
                self.judge, "soft_judge", return_value=True, no_arg_to_check=False
            ):
                result = self.judge.compare(self.agent_event, self.oracle_event)
                self.assertTrue(result)

    def test_compare_hard_judge_passes_soft_judge_fails(self):
        # Test compare when hard judge passes but soft judge fails
        with patch.object(self.judge, "hard_judge", return_value=True):
            with patch.object(
                self.judge, "soft_judge", return_value=False, no_arg_to_check=False
            ):
                result = self.judge.compare(self.agent_event, self.oracle_event)
                self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
