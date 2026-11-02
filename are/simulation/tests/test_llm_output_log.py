# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import time
import unittest

from are.simulation.agents.agent_log import BaseAgentLog, LLMOutputThoughtActionLog


class TestLLMOutputThoughtActionLog(unittest.TestCase):
    def test_llm_output_log_with_token_usage_and_completion_duration(self):
        """Test that LLMOutputThoughtActionLog correctly stores token usage and inference time."""
        # Create a log with token usage and inference time
        timestamp = time.time()
        content = "This is a test response from the LLM"
        prompt_tokens = 100
        completion_tokens = 50
        total_tokens = 150
        completion_duration = 1.25
        agent_id = "test_agent_id"

        log = LLMOutputThoughtActionLog(
            timestamp=timestamp,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            completion_duration=completion_duration,
            agent_id=agent_id,
        )

        # Verify that the values are correctly stored
        self.assertEqual(log.content, content)
        self.assertEqual(log.prompt_tokens, prompt_tokens)
        self.assertEqual(log.completion_tokens, completion_tokens)
        self.assertEqual(log.total_tokens, total_tokens)
        self.assertEqual(log.completion_duration, completion_duration)
        self.assertEqual(log.get_type(), "llm_output")

    def test_llm_output_log_serialization(self):
        """Test that LLMOutputThoughtActionLog correctly serializes and deserializes."""
        # Create a log with token usage and inference time
        timestamp = time.time()
        content = "This is a test response from the LLM"
        prompt_tokens = 100
        completion_tokens = 50
        total_tokens = 150
        completion_duration = 1.25
        agent_id = "test_agent_id"

        log = LLMOutputThoughtActionLog(
            timestamp=timestamp,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            completion_duration=completion_duration,
            agent_id=agent_id,
        )

        # Serialize the log
        serialized = log.serialize()

        # Deserialize the log
        deserialized_dict = json.loads(serialized)

        # Verify that the serialized data contains all fields
        self.assertEqual(deserialized_dict["content"], content)
        self.assertEqual(deserialized_dict["prompt_tokens"], prompt_tokens)
        self.assertEqual(deserialized_dict["completion_tokens"], completion_tokens)
        self.assertEqual(deserialized_dict["total_tokens"], total_tokens)
        self.assertEqual(deserialized_dict["completion_duration"], completion_duration)
        self.assertEqual(deserialized_dict["log_type"], "llm_output")

    def test_llm_output_log_from_dict(self):
        """Test that LLMOutputThoughtActionLog correctly reconstructs from a dict."""
        # Create a dict representing a serialized log
        timestamp = time.time()
        content = "This is a test response from the LLM"
        prompt_tokens = 100
        completion_tokens = 50
        total_tokens = 150
        completion_duration = 1.25
        log_id = "test_id_123"
        agent_id = "test_agent_id"

        log_dict = {
            "timestamp": timestamp,
            "content": content,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "completion_duration": completion_duration,
            "log_type": "llm_output",
            "id": log_id,
            "agent_id": agent_id,
        }

        # Reconstruct the log from the dict
        log = BaseAgentLog.from_dict(log_dict)

        # Verify that the reconstructed log has all fields
        self.assertIsInstance(log, LLMOutputThoughtActionLog)
        # Typing ignore because we first check the log is an instance of LLMOutputThoughtActionLog
        self.assertEqual(log.content, content)  # type: ignore
        self.assertEqual(log.prompt_tokens, prompt_tokens)  # type: ignore
        self.assertEqual(log.completion_tokens, completion_tokens)  # type: ignore
        self.assertEqual(log.total_tokens, total_tokens)  # type: ignore
        self.assertEqual(log.completion_duration, completion_duration)  # type: ignore
        self.assertEqual(log.id, log_id)
        self.assertEqual(log.get_type(), "llm_output")

    def test_llm_output_log_default_values(self):
        """Test that LLMOutputThoughtActionLog uses default values correctly."""
        # Create a log with only required fields
        timestamp = time.time()
        content = "This is a test response from the LLM"
        agent_id = "test_agent_id"

        log = LLMOutputThoughtActionLog(
            timestamp=timestamp,
            content=content,
            agent_id=agent_id,
        )

        # Verify that default values are used
        self.assertEqual(log.content, content)
        self.assertEqual(log.prompt_tokens, 0)
        self.assertEqual(log.completion_tokens, 0)
        self.assertEqual(log.total_tokens, 0)
        self.assertEqual(log.completion_duration, 0.0)


if __name__ == "__main__":
    unittest.main()
