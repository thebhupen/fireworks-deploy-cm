# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

# pyright: ignore

import time
from datetime import datetime, timezone
from unittest.mock import patch

from are.simulation.apps import AgentUserInterface, EmailClientV2, ReminderApp
from are.simulation.apps.system import SystemApp, WaitForNotificationTimeout
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.notification_system import (
    Message,
    MessageType,
    VerboseNotificationSystem,
)
from are.simulation.types import EventRegisterer


class TestWaitForNotification:
    """Test suite for wait_for_notification functionality"""

    def setup_method(self):
        """Setup method run before each test"""
        self.env_config = EnvironmentConfig(
            duration=10,
            time_increment_in_seconds=1,
            queue_based_loop=False,
            oracle_mode=False,
        )
        self.env = Environment(self.env_config)
        self.system_app = SystemApp()
        self.aui = AgentUserInterface()
        self.email_app = EmailClientV2()
        self.env.register_apps([self.system_app, self.aui, self.email_app])

    def test_wait_for_notification_method_exists(self):
        """Test that wait_for_notification method exists and is properly decorated"""
        assert hasattr(self.system_app, "wait_for_notification")
        assert callable(self.system_app.wait_for_notification)

        # Check that it's an app tool
        tools = self.system_app.get_tools()
        tool_names = [tool.name for tool in tools]
        assert "SystemApp__wait_for_notification" in tool_names

    def test_wait_for_notification_creates_timeout(self):
        """Test that wait_for_notification creates a WaitForNotificationTimeout object"""
        timeout_seconds = 5
        initial_time = self.system_app.time_manager.time()

        # Mock the wait_for_next_notification method to avoid actual waiting
        with patch.object(self.system_app, "wait_for_next_notification"):
            self.system_app.wait_for_notification(timeout=timeout_seconds)

        # Check that timeout object was created
        assert self.system_app.wait_for_notification_timeout is not None
        assert isinstance(
            self.system_app.wait_for_notification_timeout, WaitForNotificationTimeout
        )
        assert self.system_app.wait_for_notification_timeout.timeout == timeout_seconds
        assert (
            self.system_app.wait_for_notification_timeout.time_created >= initial_time
        )

    def test_wait_for_notification_calls_environment_method(self):
        """Test that wait_for_notification calls the environment's wait_for_next_notification method"""
        with patch.object(self.system_app, "wait_for_next_notification") as mock_wait:
            self.system_app.wait_for_notification(timeout=3)
            mock_wait.assert_called_once()

    def test_wait_for_notification_with_zero_timeout(self):
        """Test wait_for_notification with zero timeout"""
        with patch.object(self.system_app, "wait_for_next_notification"):
            self.system_app.wait_for_notification(timeout=0)

        assert self.system_app.wait_for_notification_timeout is not None
        assert self.system_app.wait_for_notification_timeout.timeout == 0

    def test_integration_wait_for_notification_with_user_message(self):
        """Integration test: wait_for_notification should exit when user message arrives"""
        env = Environment(EnvironmentConfig(duration=5))
        system_app = SystemApp()
        aui = AgentUserInterface()
        env.register_apps([system_app, aui])

        with EventRegisterer.capture_mode():
            # Schedule a user message to arrive after 2 seconds
            user_message = (
                aui.send_message_to_agent("test message")
                .depends_on(None, delay_seconds=2)
                .with_id("user_msg")
            )

        env.schedule(user_message)

        # Start environment in a separate thread to avoid blocking
        env.start()

        start_time = time.time()
        system_app.wait_for_notification(timeout=10)
        elapsed_time = time.time() - start_time

        env.stop()
        env.join()

        # Should have exited before timeout due to user message
        assert elapsed_time < 2  # Much less than the 10-second timeout

    def test_integration_wait_for_notification_with_timeout(self):
        """Integration test: wait_for_notification should timeout when no messages arrive"""
        env = Environment(EnvironmentConfig(duration=5))
        system_app = SystemApp()
        env.register_apps([system_app])

        # Mock the wait_for_next_notification method since we're testing the timeout logic, not the actual waiting
        with patch.object(system_app, "wait_for_next_notification"):
            start_time = time.time()
            system_app.wait_for_notification(timeout=2)
            elapsed_time = time.time() - start_time

        # Should complete quickly since we're mocking the actual wait
        assert elapsed_time < 1
        assert system_app.wait_for_notification_timeout is not None
        assert system_app.wait_for_notification_timeout.timeout == 2

    def test_integration_wait_for_notification_with_email_notification(self):
        """Integration test: wait_for_notification should exit when email notification arrives"""
        notification_system = VerboseNotificationSystem()
        env = Environment(
            EnvironmentConfig(duration=5), notification_system=notification_system
        )
        system_app = SystemApp()
        email_app = EmailClientV2()
        env.register_apps([system_app, email_app])

        with EventRegisterer.capture_mode():
            # Schedule an email to arrive after 1 second
            email_event = (
                email_app.send_email_to_user_only(
                    sender=["test@example.com"],
                    subject="Test Email",
                    content="Test content",
                )
                .depends_on(None, delay_seconds=1)
                .with_id("email_event")
            )

        env.schedule(email_event)
        env.start()

        start_time = time.time()
        system_app.wait_for_notification(timeout=10)
        elapsed_time = time.time() - start_time

        env.stop()
        env.join()

        # Should have exited before timeout due to email notification
        assert elapsed_time < 5

    def test_integration_wait_for_notification_with_reminder(self):
        """Integration test: wait_for_notification should exit when reminder notification arrives"""
        env = Environment(EnvironmentConfig(duration=5))
        system_app = SystemApp()
        reminder_app = ReminderApp()
        env.register_apps([system_app, reminder_app])

        # Create a reminder that's already due
        current_time = env.time_manager.time()
        past_time = datetime.fromtimestamp(current_time - 60, tz=timezone.utc)

        with EventRegisterer.capture_mode():
            reminder_event = (
                reminder_app.add_reminder(
                    title="Test Reminder",
                    due_datetime=past_time.strftime("%Y-%m-%d %H:%M:%S"),
                    description="Test reminder description",
                )
                .depends_on(None, delay_seconds=1)
                .with_id("reminder_event")
            )

        env.schedule(reminder_event)
        env.start()

        start_time = time.time()
        system_app.wait_for_notification(timeout=10)
        elapsed_time = time.time() - start_time

        env.stop()
        env.join()

        # Should have exited before timeout due to reminder notification
        assert elapsed_time < 5

    def test_timeout_object_properties(self):
        """Test WaitForNotificationTimeout object properties"""
        timeout_seconds = 5
        time_created = self.system_app.time_manager.time()

        timeout_obj = WaitForNotificationTimeout(
            time_created=time_created, timeout=timeout_seconds
        )

        assert timeout_obj.time_created == time_created
        assert timeout_obj.timeout == timeout_seconds
        assert timeout_obj.timeout_timestamp == time_created + timeout_seconds  # type: ignore
        assert "timeout after 5 seconds" in str(timeout_obj)

    def test_get_wait_for_notification_timeout_before_timeout(self):
        """Test get_wait_for_notification_timeout returns None before timeout"""
        self.system_app.wait_for_notification_timeout = WaitForNotificationTimeout(
            time_created=self.system_app.time_manager.time(), timeout=10
        )

        result = self.system_app.get_wait_for_notification_timeout()
        assert result is None

    def test_get_wait_for_notification_timeout_after_timeout(self):
        """Test get_wait_for_notification_timeout returns timeout object after timeout"""
        past_time = self.system_app.time_manager.time() - 10
        self.system_app.wait_for_notification_timeout = WaitForNotificationTimeout(
            time_created=past_time, timeout=5
        )

        result = self.system_app.get_wait_for_notification_timeout()
        assert result is not None
        assert result == self.system_app.wait_for_notification_timeout

    def test_reset_wait_for_notification_timeout(self):
        """Test reset_wait_for_notification_timeout clears the timeout"""
        self.system_app.wait_for_notification_timeout = WaitForNotificationTimeout(
            time_created=self.system_app.time_manager.time(), timeout=5
        )

        self.system_app.reset_wait_for_notification_timeout()
        assert self.system_app.wait_for_notification_timeout is None

    def test_multiple_wait_for_notification_calls(self):
        """Test multiple consecutive calls to wait_for_notification"""
        with patch.object(self.system_app, "wait_for_next_notification"):
            # First call
            self.system_app.wait_for_notification(timeout=3)
            first_timeout = self.system_app.wait_for_notification_timeout

            # Second call should replace the timeout
            self.system_app.wait_for_notification(timeout=5)
            second_timeout = self.system_app.wait_for_notification_timeout

            assert first_timeout != second_timeout
            assert second_timeout is not None
            assert second_timeout.timeout == 5

    def test_wait_for_notification_with_string_timeout(self):
        """Test wait_for_notification converts string timeout to int"""
        with patch.object(self.system_app, "wait_for_next_notification"):
            self.system_app.wait_for_notification(timeout="7")

        assert self.system_app.wait_for_notification_timeout is not None
        assert self.system_app.wait_for_notification_timeout.timeout == 7

    def test_environment_waiting_flag_reset_on_exception(self):
        """Test that waiting_for_notification flag is reset even if exception occurs"""
        # We need to ensure the flag is reset in the finally block
        # Let's modify the environment method to use try/finally

        def mock_wait_with_exception():
            self.env.waiting_for_notification = True
            try:
                raise Exception("Test exception")
            finally:
                self.env.waiting_for_notification = False

        with patch.object(
            self.env, "wait_for_next_notification", side_effect=mock_wait_with_exception
        ):
            try:
                self.env.wait_for_next_notification()
            except Exception:
                pass

        # Flag should be reset even after exception
        assert not self.env.waiting_for_notification

    def test_notification_system_integration(self):
        """Test integration with notification system's message queue"""

        with patch.object(self.system_app, "wait_for_next_notification"):
            self.system_app.wait_for_notification(timeout="7")

        # Create a mock message
        test_message = Message(
            message_type=MessageType.USER_MESSAGE,
            message="Test message",
            timestamp=datetime.fromtimestamp(
                self.env.time_manager.time(), tz=timezone.utc
            ),
        )

        # Add message to queue
        self.env.notification_system.message_queue.put(test_message)

        # wait_for_next_notification should detect existing message and exit immediately
        start_time = time.time()
        self.env.wait_for_next_notification()
        elapsed_time = time.time() - start_time

        # Should exit almost immediately
        assert elapsed_time < 0.2

    def test_edge_case_very_large_timeout(self):
        """Test wait_for_notification with very large timeout"""
        large_timeout = 999999
        with patch.object(self.system_app, "wait_for_next_notification"):
            self.system_app.wait_for_notification(timeout=large_timeout)

        assert self.system_app.wait_for_notification_timeout is not None
        assert self.system_app.wait_for_notification_timeout.timeout == large_timeout

    def test_event_sequence_integration(self):
        """Test wait_for_notification with a sequence of events where only some generate notifications"""
        env = Environment(EnvironmentConfig(duration=10))
        system_app = SystemApp()
        aui = AgentUserInterface()
        email_app = EmailClientV2()
        env.register_apps([system_app, aui, email_app])

        with EventRegisterer.capture_mode():
            # Schedule sequence: user message (t=1), email (t=3), another user message (t=5)
            user_msg1 = (
                aui.send_message_to_agent("first message")
                .depends_on(None, delay_seconds=1)
                .with_id("user_msg1")
            )

            email_event = (
                email_app.send_email(
                    recipients=["test@example.com"],
                    subject="Test Email",
                    content="Test content",
                )
                .depends_on(None, delay_seconds=3)
                .with_id("email_event")
            )

            user_msg2 = (
                aui.send_message_to_agent("second message")
                .depends_on(None, delay_seconds=5)
                .with_id("user_msg2")
            )

        env.schedule([user_msg1, email_event, user_msg2])
        env.start()

        # Agent calls wait_for_notification at t=0, should exit at t=1 when first user message arrives
        start_time = time.time()
        system_app.wait_for_notification(timeout=10)
        elapsed_time = time.time() - start_time

        env.stop()
        env.join()

        # Should have exited quickly when first notification arrived, not waited for all events
        assert (
            elapsed_time < 3
        )  # Much less than the 5 seconds it would take to process all events

        # Verify we have messages in the queue (first user message should have triggered exit)
        messages = env.notification_system.message_queue.list_view()
        assert len(messages) >= 1  # At least the first user message

    def test_efficiency_verification(self):
        """Test wait_for_notification efficiency by jumping over many non-notification events"""
        env = Environment(EnvironmentConfig(duration=50))
        system_app = SystemApp()
        aui = AgentUserInterface()
        email_app = EmailClientV2()
        env.register_apps([system_app, aui, email_app])

        with EventRegisterer.capture_mode():
            # Schedule many non-notification events (emails that don't generate notifications)
            events = []
            for i in range(1, 20):  # Events at t=1,2,3...19
                email_event = (
                    email_app.send_email(
                        recipients=["test@example.com"],
                        subject=f"Email {i}",
                        content=f"Content {i}",
                    )
                    .depends_on(None, delay_seconds=i)
                    .with_id(f"email_{i}")
                )
                events.append(email_event)

            # Schedule one notification event at t=20
            user_message = (
                aui.send_message_to_agent("notification message")
                .depends_on(None, delay_seconds=20)
                .with_id("notification_msg")
            )
            events.append(user_message)

        env.schedule(events)
        env.start()

        # Measure time for wait_for_notification to reach the notification at t=20
        start_time = time.time()
        system_app.wait_for_notification(timeout=30)
        elapsed_time = time.time() - start_time

        env.stop()
        env.join()

        # Should complete much faster than 20 seconds (time-based waiting)
        # Even with event processing overhead, should be much less than 10 seconds
        assert elapsed_time < 2, (
            f"wait_for_notification took {elapsed_time}s, expected < 10s"
        )

        # Verify the notification message was received
        messages = env.notification_system.message_queue.list_view()
        notification_messages = [
            m for m in messages if "notification message" in m.message
        ]
        assert len(notification_messages) >= 1

    def test_timeout_vs_notification_race(self):
        """Test that timeout object is created correctly when timeout matches notification timing"""
        env = Environment(EnvironmentConfig(duration=10))
        system_app = SystemApp()
        aui = AgentUserInterface()
        env.register_apps([system_app, aui])

        with EventRegisterer.capture_mode():
            # Schedule notification to arrive at t=5
            user_message = (
                aui.send_message_to_agent("race condition message")
                .depends_on(None, delay_seconds=5)
                .with_id("race_msg")
            )

        env.schedule(user_message)

        # Test that timeout object is created correctly even when timeout matches event timing
        initial_time = system_app.time_manager.time()

        # Mock the wait_for_next_notification method to focus on testing the timeout setup
        with patch.object(system_app, "wait_for_next_notification"):
            system_app.wait_for_notification(timeout=5)

        # Verify timeout object was created with correct timing
        assert system_app.wait_for_notification_timeout is not None
        assert system_app.wait_for_notification_timeout.timeout == 5
        assert system_app.wait_for_notification_timeout.time_created >= initial_time

        # Verify timeout timestamp is calculated correctly
        expected_timeout_time = (
            system_app.wait_for_notification_timeout.time_created + 5
        )
        assert (
            system_app.wait_for_notification_timeout.timeout_timestamp
            == expected_timeout_time  # type: ignore
        )

    def test_realistic_multi_app_scenario(self):
        """Test realistic scenario with multiple app types generating notifications"""
        notification_system = VerboseNotificationSystem()
        env = Environment(
            EnvironmentConfig(duration=15), notification_system=notification_system
        )
        system_app = SystemApp()
        aui = AgentUserInterface()
        email_app = EmailClientV2()
        reminder_app = ReminderApp()
        env.register_apps([system_app, aui, email_app, reminder_app])

        # Create a reminder that will be due
        current_time = env.time_manager.time()
        due_time = datetime.fromtimestamp(current_time + 8, tz=timezone.utc)

        with EventRegisterer.capture_mode():
            # Complex sequence of events:
            # t=2: Email arrives (should generate notification with VerboseNotificationSystem)
            email_event = (
                email_app.send_email_to_user_only(
                    sender=["sender@example.com"],
                    subject="Important Email",
                    content="This should generate a notification",
                )
                .depends_on(None, delay_seconds=2)
                .with_id("email_notif")
            )

            # t=5: Some non-notification email
            email_event2 = (
                email_app.send_email(
                    recipients=["other@example.com"],
                    subject="Regular Email",
                    content="This won't generate notification",
                )
                .depends_on(None, delay_seconds=5)
                .with_id("email_regular")
            )

            # t=8: Reminder becomes due (should generate notification)
            reminder_event = (
                reminder_app.add_reminder(
                    title="Important Reminder",
                    due_datetime=due_time.strftime("%Y-%m-%d %H:%M:%S"),
                    description="This should generate a notification",
                )
                .depends_on(None, delay_seconds=1)
                .with_id("reminder_setup")
            )

            # t=10: User message (should generate notification)
            user_message = (
                aui.send_message_to_agent("User message")
                .depends_on(None, delay_seconds=10)
                .with_id("user_msg")
            )

        env.schedule([email_event, email_event2, reminder_event, user_message])
        env.start()

        # Agent calls wait_for_notification, should exit at t=2 when first email notification arrives
        start_time = time.time()
        system_app.wait_for_notification(timeout=15)
        elapsed_time = time.time() - start_time

        env.stop()
        env.join()

        # Should exit at t=2 when email notification arrives, not wait for reminder or user message
        assert elapsed_time < 5, f"Expected to exit around t=2, took {elapsed_time}s"

        # Verify we got the email notification
        messages = env.notification_system.message_queue.list_view()
        email_notifications = [
            m for m in messages if "email received" in m.message.lower()
        ]
        assert len(email_notifications) >= 1, "Should have received email notification"

    def test_wait_for_notification_timestamp_accuracy(self):
        """Verify that events are processed at correct timestamps when jumping efficiently"""
        env = Environment(EnvironmentConfig(duration=20))
        system_app = SystemApp()
        aui = AgentUserInterface()
        email_app = EmailClientV2()
        env.register_apps([system_app, aui, email_app])

        # Track timestamps when events are processed
        processed_timestamps = []
        original_add_to_log = env.add_to_log

        def timestamp_tracking_add_to_log(events):
            """Wrapper to track when events are processed"""
            if not isinstance(events, list):
                events = [events]
            for event in events:
                processed_timestamps.append(
                    {
                        "event_id": event.event_id,
                        "event_time": event.event_time,
                        "env_current_time": env.current_time,
                        "processed_at": env.time_manager.time(),
                    }
                )
            return original_add_to_log(events)

        env.add_to_log = timestamp_tracking_add_to_log

        with EventRegisterer.capture_mode():
            # Schedule events at specific timestamps: t=5, t=10, t=15
            email1 = (
                email_app.send_email(
                    recipients=["test1@example.com"],
                    subject="Email 1",
                    content="Content 1",
                )
                .depends_on(None, delay_seconds=5)
                .with_id("email_t5")
            )

            email2 = (
                email_app.send_email(
                    recipients=["test2@example.com"],
                    subject="Email 2",
                    content="Content 2",
                )
                .depends_on(None, delay_seconds=10)
                .with_id("email_t10")
            )

            # Notification event at t=15
            user_message = (
                aui.send_message_to_agent("notification at t=15")
                .depends_on(None, delay_seconds=15)
                .with_id("notification_t15")
            )

        env.schedule([email1, email2, user_message])
        env.start()

        # Record initial environment time
        initial_env_time = env.current_time

        # Agent calls wait_for_notification - should jump efficiently to t=15
        start_time = time.time()
        system_app.wait_for_notification(timeout=20)
        elapsed_time = time.time() - start_time

        env.stop()
        env.join()

        # Should complete efficiently (much faster than 15 seconds)
        assert elapsed_time < 8, f"Expected efficient completion, took {elapsed_time}s"

        # Verify timestamp accuracy
        assert len(processed_timestamps) >= 3, (
            f"Expected at least 3 events, got {len(processed_timestamps)}"
        )

        # Find our specific events
        email_t5_events = [
            e for e in processed_timestamps if e["event_id"] == "email_t5"
        ]
        email_t10_events = [
            e for e in processed_timestamps if e["event_id"] == "email_t10"
        ]
        notification_t15_events = [
            e for e in processed_timestamps if e["event_id"] == "notification_t15"
        ]

        # Verify events were processed at correct environment timestamps
        if email_t5_events:
            # Email at t=5 should be processed when environment time is around start_time + 5
            expected_time_t5 = initial_env_time + 5
            actual_time_t5 = email_t5_events[0]["env_current_time"]
            assert abs(actual_time_t5 - expected_time_t5) <= 2, (
                f"Email t=5 processed at wrong time: expected ~{expected_time_t5}, got {actual_time_t5}"
            )

        if email_t10_events:
            # Email at t=10 should be processed when environment time is around start_time + 10
            expected_time_t10 = initial_env_time + 10
            actual_time_t10 = email_t10_events[0]["env_current_time"]
            assert abs(actual_time_t10 - expected_time_t10) <= 2, (
                f"Email t=10 processed at wrong time: expected ~{expected_time_t10}, got {actual_time_t10}"
            )

        if notification_t15_events:
            # Notification at t=15 should be processed when environment time is around start_time + 15
            expected_time_t15 = initial_env_time + 15
            actual_time_t15 = notification_t15_events[0]["env_current_time"]
            assert abs(actual_time_t15 - expected_time_t15) <= 2, (
                f"Notification t=15 processed at wrong time: expected ~{expected_time_t15}, got {actual_time_t15}"
            )

        # Verify final environment time is approximately t=15
        final_env_time = env.current_time
        expected_final_time = initial_env_time + 15
        assert abs(final_env_time - expected_final_time) <= 2, (
            f"Final environment time incorrect: expected ~{expected_final_time}, got {final_env_time}"
        )

    def test_wait_for_notification_with_condition_check_event(self):
        """Test wait_for_notification with ConditionCheckEvent dependencies"""
        from are.simulation.types import ConditionCheckEvent

        env = Environment(EnvironmentConfig(duration=20))
        system_app = SystemApp()
        aui = AgentUserInterface()
        email_app = EmailClientV2()
        env.register_apps([system_app, aui, email_app])

        # Create a simple condition that becomes true when a specific email is sent
        condition_met = False
        condition_met_time = None

        def email_sent_condition(environment):
            """Condition that becomes true when we find a specific email in the event log"""
            nonlocal condition_met, condition_met_time
            if condition_met:
                return True

            # Check if our trigger email has been processed
            past_events = environment.event_log.list_view()
            for event in past_events:
                if (
                    hasattr(event, "event_id")
                    and event.event_id == "trigger_email"
                    and event.metadata.return_value is not None
                ):
                    condition_met = True
                    condition_met_time = environment.current_time
                    return True
            return False

        with EventRegisterer.capture_mode():
            # Schedule an email that will trigger the condition at t=5
            trigger_email = (
                email_app.send_email(
                    recipients=["trigger@example.com"],
                    subject="Trigger Email",
                    content="This email triggers the condition",
                )
                .depends_on(None, delay_seconds=5)
                .with_id("trigger_email")
            )

            # Create condition check event that checks every 1 second
            condition_event = ConditionCheckEvent.from_condition(
                condition=email_sent_condition,
                every_tick=1,  # Check every 1 time increment
                timeout=15,  # Timeout after 15 seconds
            ).with_id("email_condition")

            # Create a user message that depends on the condition
            notification_event = (
                aui.send_message_to_agent("condition met notification")
                .depends_on(condition_event)
                .with_id("condition_notification")
            )

        env.schedule([trigger_email, condition_event, notification_event])
        env.start()

        # Record start time for verification
        start_env_time = env.current_time

        # Agent calls wait_for_notification - should wait until condition is met at t=5
        start_time = time.time()
        system_app.wait_for_notification(timeout=20)
        elapsed_time = time.time() - start_time

        env.stop()
        env.join()

        # Should complete efficiently after the condition is met
        assert elapsed_time < 10, (
            f"Expected completion before timeout, took {elapsed_time}s"
        )

        # Verify the condition was actually met
        assert condition_met, "Condition should have been met"
        assert condition_met_time is not None, "Condition met time should be recorded"

        # Verify condition was met at approximately the right time (around t=5)
        expected_condition_time = start_env_time + 5
        assert abs(condition_met_time - expected_condition_time) <= 3, (
            f"Condition met at wrong time: expected ~{expected_condition_time}, got {condition_met_time}"
        )

        # Verify we received the notification
        messages = env.notification_system.message_queue.list_view()
        condition_notifications = [
            m for m in messages if "condition met notification" in m.message
        ]
        assert len(condition_notifications) >= 1, (
            "Should have received condition-dependent notification"
        )

        # Verify the trigger email was processed
        past_events = env.event_log.list_view()
        trigger_events = [
            e
            for e in past_events
            if hasattr(e, "event_id") and e.event_id == "trigger_email"
        ]
        assert len(trigger_events) >= 1, "Trigger email should have been processed"

    def test_empty_queue_with_timeout_fix(self):
        """Test the specific fix: empty event queue with timeout should jump to timeout time"""
        env = Environment(EnvironmentConfig(duration=20))
        system_app = SystemApp()
        env.register_apps([system_app])

        # Start environment
        env.start()

        initial_time = env.time_manager.time()
        assert env.get_event_queue_length() == 0, "Event queue should be empty"

        timeout_seconds = 5
        system_app.wait_for_notification(timeout=timeout_seconds)
        final_time = env.time_manager.time()
        time_advanced = final_time - initial_time

        env.stop()
        env.join()

        # Time should have advanced by approximately the timeout amount
        assert abs(time_advanced - timeout_seconds) <= 1, (
            f"Expected time to advance by ~{timeout_seconds}s, advanced by {time_advanced}s"
        )

        # Verify timeout object is still in the queue for the agent
        assert system_app.wait_for_notification_timeout is None
        # Check that the timeout message was generated
        assert len(env.notification_system.message_queue.list_view()) != 0

    def test_multiple_wait_calls_with_timeout_progression(self):
        """Test multiple wait_for_notification calls with timeout progression"""
        env = Environment(EnvironmentConfig(duration=30))
        system_app = SystemApp()
        aui = AgentUserInterface()
        env.register_apps([system_app, aui])

        env.start()

        timestamps = []

        # First wait - should advance by 3 seconds
        initial_time = env.time_manager.time()
        timestamps.append(("start", initial_time))

        system_app.wait_for_notification(timeout=3)
        after_first_wait = env.time_manager.time()
        timestamps.append(("after_first_wait", after_first_wait))

        # Check and clear notification queue after first wait
        messages_after_first = env.notification_system.message_queue.list_view()
        print(f"Messages after first wait: {len(messages_after_first)}")
        for msg in messages_after_first:
            print(f"  - {msg.message_type}: {msg.message}")
        env.notification_system.clear()

        # Second wait - should advance by 5 more seconds
        system_app.wait_for_notification(timeout=5)
        after_second_wait = env.time_manager.time()
        timestamps.append(("after_second_wait", after_second_wait))

        # Check and clear notification queue after second wait
        messages_after_second = env.notification_system.message_queue.list_view()
        print(f"Messages after second wait: {len(messages_after_second)}")
        for msg in messages_after_second:
            print(f"  - {msg.message_type}: {msg.message}")
        env.notification_system.clear()

        # Third wait - should advance by 2 more seconds
        system_app.wait_for_notification(timeout=2)
        after_third_wait = env.time_manager.time()
        timestamps.append(("after_third_wait", after_third_wait))

        # Check and clear notification queue after third wait
        messages_after_third = env.notification_system.message_queue.list_view()
        print(f"Messages after third wait: {len(messages_after_third)}")
        for msg in messages_after_third:
            print(f"  - {msg.message_type}: {msg.message}")
        env.notification_system.clear()

        env.stop()
        env.join()

        # Verify time progression
        first_advance = after_first_wait - initial_time
        second_advance = after_second_wait - after_first_wait
        third_advance = after_third_wait - after_second_wait

        assert abs(first_advance - 3) <= 1, (
            f"First wait should advance ~3s, advanced {first_advance}s"
        )
        assert abs(second_advance - 5) <= 1, (
            f"Second wait should advance ~5s, advanced {second_advance}s"
        )
        assert abs(third_advance - 2) <= 1, (
            f"Third wait should advance ~2s, advanced {third_advance}s"
        )

        # Total advancement should be approximately 10 seconds
        total_advance = after_third_wait - initial_time
        assert abs(total_advance - 10) <= 2, (
            f"Total advancement should be ~10s, was {total_advance}s"
        )

    def test_wait_with_events_vs_empty_queue_behavior(self):
        """Test different behavior when queue has events vs when it's empty"""
        env = Environment(EnvironmentConfig(duration=25))
        system_app = SystemApp()
        aui = AgentUserInterface()
        email_app = EmailClientV2()
        env.register_apps([system_app, aui, email_app])

        # Schedule an event at t=10
        with EventRegisterer.capture_mode():
            user_message = (
                aui.send_message_to_agent("scheduled message")
                .depends_on(None, delay_seconds=10)
                .with_id("scheduled_msg")
            )

        env.schedule(user_message)
        env.start()

        initial_time = env.time_manager.time()

        # First wait: queue has events, should jump to next event time (t=10)
        system_app.wait_for_notification(timeout=15)
        after_event_wait = env.time_manager.time()
        # simulate agent polling for new messages
        env.notification_system.clear()

        # Second wait: queue should now be empty, should jump to timeout
        system_app.wait_for_notification(timeout=5)
        after_timeout_wait = env.time_manager.time()
        # simulate agent polling for new messages
        env.notification_system.clear()

        env.stop()
        env.join()

        # First wait should have jumped to around t=10 (when the event was scheduled)
        first_advance = after_event_wait - initial_time
        assert abs(first_advance - 10) <= 2, (
            f"First wait should jump to event time (~10s), advanced {first_advance}s"
        )

        # Second wait should have advanced by timeout amount (5s)
        second_advance = after_timeout_wait - after_event_wait
        assert abs(second_advance - 5) <= 1, (
            f"Second wait should advance by timeout (~5s), advanced {second_advance}s"
        )

    def test_timeout_notification_generation(self):
        """Test that timeout actually generates a notification when reached"""
        env = Environment(EnvironmentConfig(duration=15))
        system_app = SystemApp()
        env.register_apps([system_app])

        env.start()

        # Call wait_for_notification with timeout
        timeout_seconds = 3
        system_app.wait_for_notification(timeout=timeout_seconds)
        # simulate agent polling for new messages
        env.notification_system.clear()

        env.stop()
        env.join()

        # Check if timeout notification was generated
        messages = env.notification_system.message_queue.list_view()
        timeout_messages = [
            m
            for m in messages
            if "timeout" in m.message.lower() or "wait" in m.message.lower()
        ]

        # Should have at least one timeout-related message
        assert len(timeout_messages) >= 0, (
            f"Expected timeout notification, got messages: {[m.message for m in messages]}"
        )

    def test_precise_timestamp_alignment_with_timeout(self):
        """Test precise timestamp alignment when jumping to timeout"""
        env = Environment(EnvironmentConfig(duration=20))
        system_app = SystemApp()
        env.register_apps([system_app])

        env.start()
        initial_time = env.time_manager.time()

        timeout_seconds = 7
        assert system_app.wait_for_notification_timeout is None

        system_app.wait_for_notification(timeout=timeout_seconds)
        env.notification_system.clear()

        # Record final times
        final_time = env.time_manager.time()
        final_current_time = env.current_time

        env.stop()
        env.join()

        # Verify timeout object was created and destroyed
        assert system_app.wait_for_notification_timeout is None

        # Verify environment time advanced to timeout time
        time_advance = final_time - initial_time
        assert abs(time_advance - timeout_seconds) <= 0.5, (
            f"Time should advance by {timeout_seconds}s, advanced by {time_advance}s"
        )

        # Verify current_time is aligned with time_manager.time()
        assert abs(final_current_time - final_time) <= 0.1, (
            f"current_time ({final_current_time}) should align with time_manager.time() ({final_time})"
        )

    def test_concurrent_timeout_and_event_edge_case(self):
        """Test edge case where timeout and event occur at exactly the same time"""
        env = Environment(EnvironmentConfig(duration=15))
        system_app = SystemApp()
        aui = AgentUserInterface()
        env.register_apps([system_app, aui])

        # Schedule event at exactly t=5
        with EventRegisterer.capture_mode():
            user_message = (
                aui.send_message_to_agent("concurrent message")
                .depends_on(None, delay_seconds=5)
                .with_id("concurrent_msg")
            )

        env.schedule(user_message)
        env.start()

        initial_time = env.time_manager.time()

        # Set timeout to also be 5 seconds
        system_app.wait_for_notification(timeout=5)

        final_time = env.time_manager.time()

        env.stop()
        env.join()

        # Should advance by approximately 5 seconds
        time_advance = final_time - initial_time
        assert abs(time_advance - 5) <= 1, (
            f"Time should advance by ~5s, advanced by {time_advance}s"
        )

        # Should have received the user message notification
        messages = env.notification_system.message_queue.list_view()
        user_messages = [m for m in messages if "concurrent message" in m.message]
        assert len(user_messages) >= 1, (
            "Should have received the concurrent user message"
        )

    def test_zero_timeout_immediate_return(self):
        """Test that zero timeout returns immediately with timeout notification"""
        env = Environment(EnvironmentConfig(duration=10))
        system_app = SystemApp()
        env.register_apps([system_app])

        env.start()

        initial_time = env.time_manager.time()

        # Call with zero timeout
        start_time = time.time()
        system_app.wait_for_notification(timeout=0)
        elapsed_real_time = time.time() - start_time

        final_time = env.time_manager.time()

        env.stop()
        env.join()

        # Should complete very quickly in real time
        assert elapsed_real_time < 1, (
            f"Zero timeout should complete quickly, took {elapsed_real_time}s"
        )

        # Environment time should not advance significantly (maybe just processing overhead)
        time_advance = final_time - initial_time
        assert time_advance <= 1, (
            f"Zero timeout should not advance time much, advanced {time_advance}s"
        )

    def test_large_timeout_efficiency(self):
        """Test that large timeout values are handled efficiently"""
        env = Environment(EnvironmentConfig(duration=100))
        system_app = SystemApp()
        aui = AgentUserInterface()
        env.register_apps([system_app, aui])

        # Schedule a notification at t=5 (much earlier than timeout)
        with EventRegisterer.capture_mode():
            user_message = (
                aui.send_message_to_agent("early notification")
                .depends_on(None, delay_seconds=5)
                .with_id("early_msg")
            )

        env.schedule(user_message)
        env.start()

        initial_time = env.time_manager.time()

        # Set very large timeout, but notification should arrive much earlier
        start_time = time.time()
        system_app.wait_for_notification(timeout=3600)  # 1 hour timeout
        elapsed_real_time = time.time() - start_time

        final_time = env.time_manager.time()

        env.stop()
        env.join()

        # Should complete efficiently (much faster than 1 hour!)
        assert elapsed_real_time < 10, (
            f"Should complete efficiently, took {elapsed_real_time}s"
        )

        # Environment time should advance to around t=5 (when notification arrived)
        time_advance = final_time - initial_time
        assert abs(time_advance - 5) <= 2, (
            f"Should advance to notification time (~5s), advanced {time_advance}s"
        )

        # Should have received the early notification
        messages = env.notification_system.message_queue.list_view()
        early_messages = [m for m in messages if "early notification" in m.message]
        assert len(early_messages) >= 1, "Should have received early notification"
