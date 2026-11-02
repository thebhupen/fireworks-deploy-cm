# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from are.simulation.apps.app import App
from are.simulation.tool_utils import OperationType, app_tool
from are.simulation.types import event_registered
from are.simulation.utils import uuid_hex


@dataclass
class Reminder:
    reminder_id: str
    title: str
    due_datetime: datetime
    description: str
    repetition_unit: str | None = None
    repetition_value: int | None = 1
    time_notified: float | None = None

    @property
    def already_notified(self) -> bool:
        return self.time_notified is not None

    def __str__(self):
        return f"Reminder: {self.title}\nDescription: {self.description}\nDue Date: {self.due_datetime}"


@dataclass
class ReminderApp(App):
    name: str | None = None
    reminders: dict[str, Reminder] = field(default_factory=dict)
    max_future_datetime: datetime | None = None
    max_reminder_repetitions: int = 100  # maximum number of repetitions for a reminder

    def __post_init__(self):
        super().__init__(self.name)
        if self.max_future_datetime is None:
            # Initialize here to make sure it accounts for time changes
            self.max_future_datetime = datetime.fromtimestamp(
                self.time_manager.time(), tz=timezone.utc
            ) + timedelta(weeks=12)

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_reminder(
        self,
        title: str,
        due_datetime: str,
        description: str,
        repetition_unit: str | None = None,
        repetition_value: int | None = 1,
    ) -> str:
        """
        Add a new reminder, and add repetitions if the reminder is repeated.
        Args:
            title (str): title of the reminder.
            due_datetime (str): Date of the reminder in YYYY-MM-DD HH:MM:SS format.
            description (str): description to display for the reminder.
            repetition_unit (str, optional): repetition interval unit (second, minute, hour, day, week, month). Defaults to None.
            repetition_value (int, optional): value of the repetition interval. Defaults to 1.
        Returns:
            str: ID of the reminder
        """
        reminder_datetime = datetime.strptime(
            due_datetime, "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        if repetition_unit:
            assert repetition_unit in [
                "second",
                "minute",
                "hour",
                "day",
                "week",
                "month",
            ], "Invalid repetition interval"
        reminder_id = uuid_hex(self.rng)
        self.reminders[reminder_id] = Reminder(
            reminder_id=reminder_id,
            title=title,
            description=description,
            due_datetime=reminder_datetime,
            repetition_unit=repetition_unit,
            repetition_value=repetition_value,
        )
        # add reminder repetitions based on the repetition interval
        count_repeat = 0
        next_reminder_id = reminder_id
        while (
            repetition_unit
            and next_reminder_id is not None
            and count_repeat < self.max_reminder_repetitions
        ):
            next_reminder_id = self.add_reminder_repetition(next_reminder_id)
            if next_reminder_id is not None:
                count_repeat += 1
        return reminder_id

    def add_reminder_repetition(self, reminder_id: str) -> str | None:
        """
        Add a new reminder repetition.
        Args:
            reminder_id (str): ID of the reminder.
        Returns:
            str | None: ID of the new reminder or None if the reminder is not repeated
        """
        reminder = self.reminders[reminder_id]
        assert reminder.repetition_unit and reminder.repetition_value, (
            f"No repetition for this reminder: {str(reminder)}"
        )
        if reminder.repetition_unit == "second":
            new_datetime = reminder.due_datetime + timedelta(
                seconds=reminder.repetition_value
            )
        elif reminder.repetition_unit == "minute":
            new_datetime = reminder.due_datetime + timedelta(
                minutes=reminder.repetition_value
            )
        elif reminder.repetition_unit == "hour":
            new_datetime = reminder.due_datetime + timedelta(
                hours=reminder.repetition_value
            )
        elif reminder.repetition_unit == "day":
            new_datetime = reminder.due_datetime + timedelta(
                days=reminder.repetition_value
            )
        elif reminder.repetition_unit == "week":
            new_datetime = reminder.due_datetime + timedelta(
                weeks=reminder.repetition_value
            )
        elif reminder.repetition_unit == "month":
            year = reminder.due_datetime.year
            month = reminder.due_datetime.month + reminder.repetition_value
            while month > 12:
                year += 1
                month -= 12
            new_datetime = reminder.due_datetime.replace(year=year, month=month)
        else:
            raise ValueError("Invalid repetition interval")

        # increase the repetition count by 1 in the reminder_id if found
        if reminder_id.endswith("_rep_"):
            rep_count = int(reminder_id.split("_rep_")[-1])
            new_reminder_id = f"{reminder_id}_rep_{rep_count + 1}"
        else:
            new_reminder_id = f"{reminder_id}_rep_1"

        if self.max_future_datetime and new_datetime < self.max_future_datetime:
            # add the new reminder if new_datetime is within the max future datetime
            self.reminders[new_reminder_id] = Reminder(
                reminder_id=new_reminder_id,
                title=reminder.title,
                due_datetime=new_datetime,
                description=reminder.description,
                repetition_unit=reminder.repetition_unit,
                repetition_value=reminder.repetition_value,
            )
            return new_reminder_id
        else:
            return None

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def delete_reminder(self, reminder_id: str):
        """Delete a reminder, and its repetitions if there are any.

        Args:
            reminder_id (str): The ID of the reminder to delete.
        """
        if reminder_id not in self.reminders:
            raise ValueError(f"Reminder {reminder_id} not found.")
        reminder = self.reminders[reminder_id]
        del self.reminders[reminder_id]
        if reminder.repetition_unit and reminder.repetition_value:
            # delete all the repetitions of the reminder
            for rep_count in range(1, self.max_reminder_repetitions + 1):
                r_id = f"{reminder_id}_rep_{rep_count}"
                if r_id in self.reminders:
                    del self.reminders[r_id]

    @app_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def delete_all_reminders(self):
        """
        Delete all reminders from the system.
        """
        self.reminders.clear()

    @app_tool(llm_formatter=lambda x: "\n\n".join([str(reminder) for reminder in x]))
    @event_registered(operation_type=OperationType.READ)
    def get_due_reminders(self) -> list[Reminder]:
        """
        Get all the due reminders.
        :return: List of due Reminder
        """
        due_reminders = []
        current_time = self.time_manager.time()
        for reminder_id, reminder in self.reminders.items():
            if reminder.due_datetime.timestamp() <= current_time:
                due_reminders.append(reminder)
        return due_reminders

    @app_tool(llm_formatter=lambda x: "\n\n".join([str(reminder) for reminder in x]))
    @event_registered(operation_type=OperationType.READ)
    def get_all_reminders(self) -> list[Reminder]:
        """
        Get all the reminders from the reminder system.
        :return: List of Reminder
        """
        return list(self.reminders.values())

    # for debugging, to make sure that reminder app is on the same global time as the environment
    def get_current_time(self) -> dict:
        """
        Get the current time and date, return both in a dict, timestamp as int (epoch) and datetime as string (YYYY-MM-DD HH:MM:SS)
        :returns: a dictionary with the keys "timestamp" (current time as timestamp) and "datetime" (current time as datetime)
        """
        timestamp = self.time_manager.time()
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return {
            "current_timestamp": timestamp,
            "current_datetime": date.strftime("%Y-%m-%d %H:%M:%S"),
        }
