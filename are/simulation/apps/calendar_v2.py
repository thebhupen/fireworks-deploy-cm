# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from dataclasses import dataclass

from are.simulation.apps.calendar import CalendarApp, _parse_datetime
from are.simulation.tool_utils import app_tool, data_tool
from are.simulation.types import event_registered
from are.simulation.utils import type_check


@dataclass
class CalendarV2(CalendarApp):
    __doc__ = CalendarApp.__doc__

    @type_check
    @app_tool()
    @data_tool()
    @event_registered()
    def edit_calendar_event(
        self,
        event_id: str,
        title: str | None = None,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
        tag: str | None = None,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
    ) -> str:
        """
        Edit a calendar event details, update only not None parameters.
        :param event_id: Id
        :param title: Title of the event
        :param start_datetime: Start datetime of the event in the format of YYYY-MM-DD HH:MM:SS
        :param end_datetime: End datetime of the event in the format of YYYY-MM-DD HH:MM:SS
        :param tag: Tag of the event
        :param description: Description of the event
        :param location: Location of the event
        :param attendees: List of attendees names
        :returns: Message if successful, otherwise raise IndexError
        """
        if event_id not in self.events:
            raise IndexError(f"Calendar Event with id {event_id} does not exist.")

        event = self.events[event_id]
        if title:
            event.title = title
        if start_datetime:
            event.start_datetime = _parse_datetime(start_datetime)
        if end_datetime:
            event.end_datetime = _parse_datetime(end_datetime)
        if tag:
            event.tag = tag
        if description:
            event.description = description
        if location:
            event.location = location
        if attendees:
            event.attendees = attendees
        event.__post_init__()
        return f"Calendar event {event_id} successfully edited"
