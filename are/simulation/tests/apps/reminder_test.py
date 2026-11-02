# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import datetime

from are.simulation.apps.reminder import ReminderApp


def test_add_reminder():
    due_datetime = (datetime.datetime.now() + datetime.timedelta(seconds=10)).replace(
        tzinfo=datetime.timezone.utc
    )
    reminder_app = ReminderApp()
    reminder_app.add_reminder(
        title="test reminder",
        due_datetime=due_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        description="test description",
    )
    assert any(
        [
            reminder.due_datetime.replace(second=0, microsecond=0)
            == due_datetime.replace(second=0, microsecond=0)
            and reminder.title == "test reminder"
            for reminder in reminder_app.reminders.values()
        ]
    ), "Reminder not added correctly"


def test_add_reminder_with_repetition():
    current_date = datetime.datetime(2024, 3, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
    reminder_app = ReminderApp(reminders={})
    time_manager = reminder_app.time_manager
    time_manager.reset(current_date.timestamp())
    reminder_app.add_reminder(
        title="Test Reminder",
        due_datetime="2024-03-01 10:00:00",
        description="This is a test reminder.",
        repetition_unit="day",
    )
    assert len(reminder_app.reminders) > 1
    reminder_ids = list(reminder_app.reminders.keys())
    for i in range(len(reminder_ids) - 1):
        current_reminder = reminder_app.reminders[reminder_ids[i]]
        next_reminder = reminder_app.reminders[reminder_ids[i + 1]]
        assert (
            next_reminder.due_datetime - current_reminder.due_datetime
            == datetime.timedelta(days=1)
        )


def test_get_due_reminders():
    reminder_app = ReminderApp(reminders={})
    time_manager = reminder_app.time_manager
    time_manager.reset(
        datetime.datetime(
            2024, 3, 1, 10, 0, 0, tzinfo=datetime.timezone.utc
        ).timestamp()
    )
    reminder_app.add_reminder(
        title="Test Reminder",
        due_datetime="2024-03-01 10:00:00",
        description="This is a test reminder.",
        repetition_unit="day",
    )

    due_reminders = reminder_app.get_due_reminders()
    assert len(due_reminders) == 1


def test_get_due_reminders_with_repetition():
    reminder_app = ReminderApp(reminders={})
    time_manager = reminder_app.time_manager
    time_manager.reset(
        datetime.datetime(
            2024, 3, 6, 10, 0, 0, tzinfo=datetime.timezone.utc
        ).timestamp()
    )
    reminder_app.add_reminder(
        title="Test Reminder",
        due_datetime="2024-03-01 10:00:00",
        description="This is a test reminder.",
        repetition_unit="day",
        repetition_value=2,
    )

    due_reminders = reminder_app.get_due_reminders()
    assert len(due_reminders) == 3


def test_get_all_reminders():
    current_date = datetime.datetime(2024, 3, 3, 10, 0, 0, tzinfo=datetime.timezone.utc)
    due_date = datetime.datetime(2024, 3, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
    max_future_datetime = current_date + datetime.timedelta(weeks=12)
    reminder_app = ReminderApp(
        reminders={},
        max_future_datetime=max_future_datetime,
    )
    time_manager = reminder_app.time_manager
    time_manager.reset(current_date.timestamp())
    reminder_app.add_reminder(
        title="Test Reminder",
        due_datetime=due_date.strftime("%Y-%m-%d %H:%M:%S"),
        description="This is a test reminder.",
        repetition_unit="day",
    )
    all_reminders = reminder_app.get_all_reminders()
    # Number of days between 2024-03-01 and 2024-05-26 excluded (reminder.max_future_datetime)
    total_days = (max_future_datetime - due_date).days

    assert len(all_reminders) == total_days, f"{len(all_reminders)} != {total_days}"
