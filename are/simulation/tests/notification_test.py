# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from datetime import datetime, timezone

from are.simulation.agents.multimodal import Attachment
from are.simulation.apps import (
    AgentUserInterface,
    CabApp,
    Calendar,
    EmailClientV2,
    Mail,
    MessagingAppV2,
    ReminderApp,
)
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.notification_system import (
    Message,
    MessageType,
    NotificationSystem,
    VerboseNotificationSystem,
)
from are.simulation.time_manager import TimeManager
from are.simulation.types import Event, EventRegisterer, EventType


def get_content_from_aui_message(message: str) -> str:
    return message.split("\nMessage: ")[1].split("\nAlready read: ")[0]


def test_notification_system():
    time_manager = TimeManager()
    notification_system = NotificationSystem()
    notification_system.initialize(time_manager)
    expected_message = Message(
        message_type=MessageType.USER_MESSAGE,
        message="Received at: timestamp_recv_str\nSender: self.sender.value\nMessage: test\nAlready read: already_read",
        timestamp=datetime.fromtimestamp(time_manager.time(), tz=timezone.utc),
    )

    aui = AgentUserInterface()
    expected_attachment: Attachment = Attachment(
        base64_data="data".encode(),
        mime="image/mime",
        name="name",
    )
    event = Event.from_function(
        function=aui.send_message_to_agent,
        event_type=EventType.USER,
        content="test",
        base64_utf8_encoded_attachment_contents=[expected_attachment],
    )

    # cast to completed event
    completed_event = event.execute()
    message = notification_system.convert_to_message(completed_event)

    assert message is not None
    assert message.message_type == expected_message.message_type
    assert get_content_from_aui_message(
        message.message
    ) == get_content_from_aui_message(expected_message.message)
    assert len(message.attachments) == 1
    actual_attachment: Attachment = message.attachments[0]
    assert expected_attachment.model_dump() == actual_attachment.model_dump()

    event2 = Event.from_function(
        function=aui.get_last_message_from_user,
        event_type=EventType.AGENT,
    )
    completed_event2 = event2.execute()
    message2 = notification_system.convert_to_message(completed_event2)
    assert message2 is None


def test_notification_from_environment():
    env = Environment(
        EnvironmentConfig(
            duration=5,
        )
    )
    aui = AgentUserInterface()
    email_client = EmailClientV2()
    env.register_apps([aui])

    with EventRegisterer.capture_mode():
        user_request1 = (
            aui.send_message_to_agent("testing stuff")
            .depends_on(None, delay_seconds=1)
            .with_id("user_request1")
        )

        user_request2 = (
            aui.send_message_to_agent("testing stuff 2")
            .depends_on(user_request1, delay_seconds=3)
            .with_id("user_request2")
        )

        some_other_event = email_client.send_email(
            recipients=["test@test.com"],
            subject="test",
            content="test",
        )

    env.schedule([user_request1, user_request2, some_other_event])

    env.start()
    env.join()

    messages = (
        env.notification_system.message_queue.list_view()
        if env.notification_system is not None
        and env.notification_system.message_queue is not None
        else []
    )

    assert (
        len(messages) == 3
    )  # 2 user messages + 1 notification that the environment stop
    assert get_content_from_aui_message(messages[0].message) == "testing stuff"
    assert get_content_from_aui_message(messages[1].message) == "testing stuff 2"
    assert messages[2].message == f"Environment stopped with state {env.state}"


def test_verbose_notification_env_events():
    notification_system = VerboseNotificationSystem()
    env = Environment(
        EnvironmentConfig(
            duration=6,
        ),
        notification_system=notification_system,
    )
    aui = AgentUserInterface()
    email_client = Mail()
    cab_app = CabApp()
    messaging = MessagingAppV2(
        current_user_id="0123456789",
        current_user_name="test_user",
        id_to_name={"0123456789": "test_user", "4567890123": "other_user"},
        name_to_id={"test_user": "0123456789", "other_user": "4567890123"},
    )
    calendar = Calendar()
    env.register_apps([aui, email_client, cab_app, calendar, messaging])

    with EventRegisterer.capture_mode():
        user_request1 = (
            aui.send_message_to_agent("testing stuff")
            .depends_on(None, delay_seconds=1)
            .with_id("user_request1")
        )

        user_request2 = (
            aui.send_message_to_agent("testing stuff 2")
            .depends_on(user_request1, delay_seconds=4)
            .with_id("user_request2")
        )

        e1 = email_client.send_email_to_user_only(
            sender=["test@test.com"],
            subject="test",
            content="test",
        ).depends_on(user_request1, delay_seconds=1)

        e2 = messaging.create_group_conversation(user_ids=["4567890123"]).depends_on(
            user_request1, delay_seconds=1
        )
        e3 = messaging.create_and_add_message(
            conversation_id="{{e1}}", sender_id="4567890123", content="test"
        ).depends_on(e2)

        e4 = calendar.add_calendar_event_by_attendee(
            who_add="other_user",
            title="test",
            start_datetime="2023-01-01 00:00:00",
            end_datetime="2023-01-01 01:00:00",
        ).depends_on(user_request2)

    env.schedule([user_request1, user_request2, e1, e2, e3, e4])

    env.start()
    env.join()

    messages = (
        env.notification_system.message_queue.list_view()
        if env.notification_system is not None
        and env.notification_system.message_queue is not None
        else []
    )

    assert (
        len(messages) == 6
    )  # 2 user messages + 3 notified ENV events + 1 notification that the environment stop
    assert get_content_from_aui_message(messages[0].message) == "testing stuff"
    assert messages[1].message == "Mail: New email received from ['test@test.com']"
    assert "New message received" in messages[2].message
    assert get_content_from_aui_message(messages[3].message) == "testing stuff 2"
    assert "New calendar event added" in messages[4].message
    assert messages[-1].message == f"Environment stopped with state {env.state}"


def test_environment_with_time_based_notifications():
    # Setup the environment
    env_config = EnvironmentConfig(duration=5)
    test_configs = [
        {
            "notification_system": NotificationSystem(),
            "expected_messages": 3,  # 1 user message + 1 reminder notification + 1 environment stop notification
            "check_notification": False,
        },
        {
            "notification_system": VerboseNotificationSystem(),
            "expected_messages": 3,  # 1 user message + 1 reminder notification + 1 environment stop notification
            "check_notification": True,
        },
    ]
    for cfg in test_configs:
        notification_system = cfg["notification_system"]
        env = Environment(env_config, notification_system=notification_system)

        # Register apps
        aui = AgentUserInterface()
        email_client = EmailClientV2()
        reminder_app = ReminderApp(name="TestReminderApp")
        env.register_apps([aui, email_client, reminder_app])
        time_manager = env.time_manager
        current_time = time_manager.time()
        # Schedule events
        with EventRegisterer.capture_mode():
            user_request = aui.send_message_to_agent("testing stuff").with_id(
                "user_request"
            )
            new_reminder = (
                reminder_app.add_reminder(
                    title="Test Reminder",
                    due_datetime=datetime.fromtimestamp(
                        current_time - 60, tz=timezone.utc
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    description="This is a test reminder.",
                )
                .depends_on(user_request, delay_seconds=1)
                .with_id("new_reminder")
            )
        env.schedule([user_request, new_reminder])
        # Start the environment
        env.start()
        env.join()
        # Check the messages in the notification system
        messages = (
            env.notification_system.message_queue.list_view()
            if env.notification_system is not None
            and env.notification_system.message_queue is not None
            else []
        )
        # Assert that the reminder notification is present
        assert len(messages) == cfg["expected_messages"]
        if cfg["check_notification"]:
            assert "TestReminderApp: New due reminders" in messages[1].message
            assert "Test Reminder" in messages[1].message
