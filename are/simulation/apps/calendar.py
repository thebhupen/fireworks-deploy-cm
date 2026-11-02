# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

from are.simulation.apps.app import App
from are.simulation.tool_utils import OperationType, app_tool, data_tool, env_tool
from are.simulation.types import EventType, event_registered
from are.simulation.utils import get_state_dict, type_check, uuid_hex

logger = logging.getLogger(__name__)

# Calendar constants
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"  # For API input/output and parsing
DISPLAY_FORMAT = "%A, %Y-%m-%d %H:%M:%S"  # For human-readable display
DEFAULT_DURATION_HOURS = 1  # Default event duration


@dataclass
class CalendarEvent:
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    title: str = "Event"
    start_datetime: float = field(default_factory=lambda: time.time())
    end_datetime: float = field(default_factory=lambda: time.time() + 3600)
    tag: str | None = None
    description: str | None = None
    location: str | None = None
    attendees: list[str] = field(default_factory=list)
    start_strftime: str | None = None
    end_strftime: str | None = None

    def __post_init__(self):
        assert isinstance(self.start_datetime, float) or isinstance(
            self.start_datetime, int
        )
        assert isinstance(self.end_datetime, float) or isinstance(
            self.end_datetime, int
        )
        if self.start_datetime > self.end_datetime:
            raise ValueError("Start time cannot be after end time.")
        if self.event_id is None or len(self.event_id) == 0:
            self.event_id = uuid.uuid4().hex

        self.start_strftime = datetime.fromtimestamp(
            self.start_datetime, tz=timezone.utc
        ).strftime(DISPLAY_FORMAT)
        self.end_strftime = datetime.fromtimestamp(
            self.end_datetime, tz=timezone.utc
        ).strftime(DISPLAY_FORMAT)

    def __str__(self):
        return f"EventID: {self.event_id}\nTitle: {self.title}\nStart: {datetime.fromtimestamp(self.start_datetime, tz=timezone.utc)}\nEnd: {datetime.fromtimestamp(self.end_datetime, tz=timezone.utc)}\nTag: {self.tag}\nDescription: {self.description}\nLocation: {self.location}\nAttendees: {', '.join(self.attendees)}"

    @property
    def summary(self):
        return f"EventID: {self.event_id}\nTitle: {self.title} - {datetime.fromtimestamp(self.start_datetime, tz=timezone.utc)} to {datetime.fromtimestamp(self.end_datetime, tz=timezone.utc)}"


# Define TypedDict for calendar events result
class CalendarEventsResult(TypedDict):
    events: list[CalendarEvent]
    range: tuple[int, int]
    total: int


def _parse_datetime(dt_str: str) -> float:
    """Parse a datetime string in the format "YYYY-MM-DD HH:MM:SS" and return the timestamp in UTC timezone."""
    try:
        dt = datetime.strptime(dt_str, DATETIME_FORMAT)
        return dt.replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        raise ValueError("Invalid datetime format. Please use YYYY-MM-DD HH:MM:SS")


@dataclass
class CalendarApp(App):
    """
    A calendar application that manages and manipulates calendar events. This class provides functionality
    for creating, reading, updating, and deleting calendar events, as well as various utility methods
    for searching and filtering events.

    The CalendarApp maintains events in a dictionary where each event is identified by a unique event_id.
    All datetime inputs should be in the format "YYYY-MM-DD HH:MM:SS" and are handled in UTC timezone.

    Key Features:
        - Event Management: Add, update, delete, and retrieve calendar events
        - Time-based Queries: Get events within specific time ranges
        - Tag Support: Organize and filter events using tags
        - Search Functionality: Search events across multiple fields
        - State Management: Save and load calendar state

    Notes:
        - All datetime operations are performed in UTC timezone
        - Event IDs are automatically generated when creating new events
        - The class supports state persistence through save/load operations
        - Search operations are case-insensitive
        - Empty tags are not allowed when filtering by tag
    """

    name: str | None = None
    events: dict[str, CalendarEvent] = field(default_factory=dict)

    def __post_init__(self):
        super().__init__(self.name)

    def get_state(self) -> dict[str, Any]:
        return get_state_dict(self, ["events"])

    def load_state(self, state_dict: dict[str, Any]):
        self.load_calendar_events_from_dict(state_dict["events"])

    def reset(self):
        super().reset()
        self.events = {}

    def load_calendar_events_from_file(self, path):
        try:
            with open(path) as f:
                temp_dic = json.load(f)
            self.load_calendar_events_from_dict(temp_dic)
        except Exception as e:
            logger.exception(e)

    def load_calendar_events_from_dict(self, events):
        try:
            self.events = {}
            for e in events:
                self.events[e] = CalendarEvent(**events[e])
        except Exception as e:
            logger.exception(e)

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def add_calendar_event(
        self,
        title: str = "Event",
        start_datetime: str | None = None,
        end_datetime: str | None = None,
        tag: str | None = None,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
    ) -> str:
        """
        Add a calendar event to the calendar. Unless specified otherwise in the task, the default week starts on Monday and ends on Sunday.
        :param title: Title of the event.
        :param start_datetime: Start datetime of the event in the format of YYYY-MM-DD HH:MM:SS.
        :param end_datetime: End datetime of the event in the format of YYYY-MM-DD HH:MM:SS.
        :param tag: Tag of the event. Defaults to None.
        :param description: Description of the event. Defaults to None.
        :param location: Location of the event. Defaults to None.
        :param attendees: List of attendees full names. Defaults to empty list.
        :returns: event_id: Id of the created event if successful.
        """
        if attendees is None:
            attendees = []
        # Handle default times using time_manager
        if start_datetime is None:
            start_datetime = datetime.fromtimestamp(
                self.time_manager.time(), tz=timezone.utc
            ).strftime(DATETIME_FORMAT)

        if end_datetime is None:
            end_datetime = (
                datetime.fromtimestamp(self.time_manager.time(), tz=timezone.utc)
                + timedelta(hours=DEFAULT_DURATION_HOURS)
            ).strftime(DATETIME_FORMAT)

        event = CalendarEvent(
            event_id=uuid_hex(self.rng),
            title=title,
            start_datetime=_parse_datetime(start_datetime),
            end_datetime=_parse_datetime(end_datetime),
            tag=tag,
            description=description,
            location=location,
            attendees=attendees,
        )
        self.events[event.event_id] = event

        return event.event_id

    @type_check
    @env_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def add_calendar_event_by_attendee(
        self,
        who_add: str,
        title: str = "Event",
        start_datetime: str | None = None,
        end_datetime: str | None = None,
        tag: str | None = None,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
    ) -> str:
        """
        Add a calendar event to the calendar. Unless specified otherwise in the task, the default week starts on Monday and ends on Sunday.
        :param who_add: Name of the attendee who is adding the event.
        :param title: Title of the event.
        :param start_datetime: Start datetime of the event in the format of YYYY-MM-DD HH:MM:SS.
        :param end_datetime: End datetime of the event in the format of YYYY-MM-DD HH:MM:SS.
        :param tag: Tag of the event. Defaults to None.
        :param description: Description of the event. Defaults to None.
        :param location: Location of the event. Defaults to None.
        :param attendees: List of attendees full names. who_add is automatically added to the list if not already present.
        :returns: event_id: Id of the created event if successful.
        """
        if attendees is None:
            attendees = []
        # Handle default times using time_manager
        if start_datetime is None:
            start_datetime = datetime.fromtimestamp(
                self.time_manager.time(), tz=timezone.utc
            ).strftime(DATETIME_FORMAT)

        if end_datetime is None:
            end_datetime = (
                datetime.fromtimestamp(self.time_manager.time(), tz=timezone.utc)
                + timedelta(hours=DEFAULT_DURATION_HOURS)
            ).strftime(DATETIME_FORMAT)

        if who_add not in attendees:
            attendees.append(who_add)
        title = f"Event created by {who_add}: {title}"
        description = (
            f"Event created by {who_add}: {description}"
            if description
            else f"Event created by {who_add}"
        )
        event = CalendarEvent(
            event_id=uuid_hex(self.rng),
            title=title,
            start_datetime=_parse_datetime(start_datetime),
            end_datetime=_parse_datetime(end_datetime),
            tag=tag,
            description=description,
            location=location,
            attendees=attendees,
        )
        self.events[event.event_id] = event

        return event.event_id

    @event_registered(operation_type=OperationType.WRITE)
    def set_calendar_event(self, event: CalendarEvent | dict[str, Any]) -> None:
        """
        Set a calendar event to the calendar.
        :param event: (CalendarEvent | dict[str, Any]): Event to set.
        :returns: None
        """
        if isinstance(event, dict):
            event = CalendarEvent(**event)
        self.events[event.event_id] = event

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_calendar_event(self, event_id: str) -> CalendarEvent:
        """
        Read a calendar event from the calendar.
        :param event_id: Id of the event to read.
        :returns: Calendar event details if successful, of type CalendarEvent, otherwise raise ValueError.
        """
        if event_id not in self.events:
            raise ValueError(f"Calendar Event with id {event_id} does not exist.")
        return self.events[event_id]

    @env_tool()
    @type_check
    @event_registered(operation_type=OperationType.WRITE, event_type=EventType.ENV)
    def delete_calendar_event_by_attendee(self, event_id: str, who_delete: str) -> str:
        """
        Delete a calendar event from the calendar.
        :param event_id: Id of the event to delete.
        :param who_delete: Name of the attendee who is deleting the event.
        :returns: Message if successful, otherwise raise ValueError.
        """
        if event_id not in self.events:
            raise ValueError(f"Calendar Event with id {event_id} does not exist.")
        if who_delete not in self.events[event_id].attendees:
            raise ValueError(f"{who_delete} is not an attendee of the event.")
        del self.events[event_id]
        return f"Event {event_id} successfully deleted by {who_delete}."

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.WRITE)
    def delete_calendar_event(self, event_id: str) -> str:
        """
        Delete a calendar event from the calendar.
        :param event_id: Id of the event to delete.
        :returns: Message if successful, otherwise raise ValueError.
        """
        if event_id not in self.events:
            raise ValueError(f"Calendar Event with id {event_id} does not exist.")
        del self.events[event_id]
        return f"Event {event_id} successfully deleted."

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_calendar_events_from_to(
        self, start_datetime: str, end_datetime: str, offset: int = 0, limit: int = 10
    ) -> CalendarEventsResult:
        """
        Get calendar events that have any time overlap with the specified date range (excludes events that only touch at boundaries).
        Unless specified otherwise in the task, the default week starts on Monday and ends on Sunday.
        :param start_datetime: Start datetime of the query range in the format of YYYY-MM-DD HH:MM:SS.
        :param end_datetime: End datetime of the query range in the format of YYYY-MM-DD HH:MM:SS.
        :param offset: offset to start listing from, default is 0.
        :param limit: number of events to list, default is 10.
        :returns: List of calendar events details that overlap with the specified time range, limited to the specified offset and limit, with additional metadata about the range of events retrieved and total number of events.
        """
        start_datetime_ts = _parse_datetime(start_datetime)
        end_datetime_ts = _parse_datetime(end_datetime)

        if start_datetime_ts > end_datetime_ts:
            raise ValueError("Start time cannot be after end time.")

        events_to_return = [
            event
            for event in self.events.values()
            if event.start_datetime < end_datetime_ts
            and event.end_datetime > start_datetime_ts
        ]
        start_index = offset
        end_index = offset + limit

        return {
            "events": events_to_return[start_index:end_index],
            "range": (start_index, min(end_index, len(events_to_return))),
            "total": len(events_to_return),
        }

    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def read_today_calendar_events(self) -> list[CalendarEvent]:
        """
        Read today's calendar events from the calendar.
        :returns: List of calendar events details.
        """
        today = datetime.fromtimestamp(self.time_manager.time(), tz=timezone.utc)
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.get_calendar_events_from_to(
            today.strftime(DATETIME_FORMAT),
            (today + timedelta(days=1)).strftime(DATETIME_FORMAT),
        )

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_all_tags(self) -> list[str]:
        """
        Get all tags from the calendar.
        :returns: List of tags.
        """
        return list({event.tag for event in self.events.values() if event.tag})

    @type_check
    @app_tool()
    @event_registered(operation_type=OperationType.READ)
    def get_calendar_events_by_tag(self, tag: str) -> list[CalendarEvent]:
        """
        Get calendar events from the calendar by tag.
        :param tag: Tag for which to get the events.
        :returns: List of calendar events details.
        """
        if not tag:
            raise ValueError("Tag cannot be empty.")
        return [event for event in self.events.values() if event.tag == tag]

    @type_check
    @app_tool()
    @data_tool()
    @event_registered(operation_type=OperationType.READ)
    def search_events(self, query: str) -> list[CalendarEvent]:
        """
        Searches for calendar events based on a query string.
        The search looks for partial matches in title, description, location, and attendees.
        :param query: The search query string
        :returns: A list of matching calendar details
        """
        query = query.lower()
        results = []

        for event in self.events.values():
            if (
                query in event.title.lower()
                or (event.description and query in event.description.lower())
                or (event.location and query in event.location.lower())
                or any(query in attendee.lower() for attendee in event.attendees)
            ):
                results.append(event)

        return results


@dataclass
class Calendar(CalendarApp):
    __doc__ = CalendarApp.__doc__
    name: str | None = "Calendar"
