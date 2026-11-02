# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from datetime import datetime, timezone

import pytest

from are.simulation.apps.calendar import CalendarApp
from are.simulation.environment import Environment


def test_init_calendar_app():
    app = CalendarApp()
    environment = Environment()
    environment.register_apps([app])
    assert len(app.events) == 0


def test_add_calendar_event():
    app = CalendarApp()
    environment = Environment()
    environment.register_apps([app])
    title = "Test Event"
    start_datetime = "2022-01-01 10:00:00"
    end_datetime = "2022-01-01 11:00:00"
    description = "This is a test event."
    location = "Test Location"
    attendees = ["John", "Jane"]
    key = app.add_calendar_event(
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        description=description,
        location=location,
        attendees=attendees,
    )

    assert len(app.events) == 1
    assert app.events[key].title == title
    assert (
        app.events[key].start_datetime
        == datetime.strptime(start_datetime, "%Y-%m-%d %H:%M:%S")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )
    assert (
        app.events[key].end_datetime
        == datetime.strptime(end_datetime, "%Y-%m-%d %H:%M:%S")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )
    assert app.events[key].description == description
    assert app.events[key].location == location
    assert app.events[key].attendees == attendees


def test_get_calendar_event():
    app = CalendarApp()
    environment = Environment()
    environment.register_apps([app])
    title = "Test Event"
    start_datetime = "2022-01-01 10:00:00"
    end_datetime = "2022-01-01 11:00:00"
    tag = "WORK"
    description = "This is a test event."
    location = "Test Location"
    attendees = ["John", "Jane"]
    key = app.add_calendar_event(
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        tag=tag,
        description=description,
        location=location,
        attendees=attendees,
    )

    assert app.get_calendar_event(event_id=key) is not None


def test_delete_calendar_event():
    app = CalendarApp()
    environment = Environment()
    environment.register_apps([app])
    title = "Test Event"
    start_datetime = "2022-01-01 10:00:00"
    end_datetime = "2022-01-01 11:00:00"
    description = "This is a test event."
    location = "Test Location"
    attendees = ["John", "Jane"]
    key = app.add_calendar_event(
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        description=description,
        location=location,
        attendees=attendees,
    )
    app.delete_calendar_event(event_id=key)
    assert len(app.events) == 0


def test_get_calendar_events_from_to():
    app = CalendarApp()
    environment = Environment()
    environment.register_apps([app])
    title = "Test Event"
    start_datetime = "2022-01-01 10:00:00"
    end_datetime = "2022-01-01 11:00:00"
    description = "This is a test event."
    location = "Test Location"
    attendees = ["John", "Jane"]
    key = app.add_calendar_event(
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        description=description,
        location=location,
        attendees=attendees,
    )
    results = app.get_calendar_events_from_to(start_datetime, end_datetime)
    events = results["events"]
    assert len(events) == 1
    assert events[0] == app.events[key]


def test_read_today_calendar_events():
    app = CalendarApp()
    environment = Environment()
    environment.register_apps([app])

    fixed_time = (
        datetime.now(timezone.utc)
        .replace(hour=12, minute=0, second=0, microsecond=0)
        .timestamp()
    )

    time_manager = environment.time_manager
    time_manager.reset(start_time=fixed_time)

    current_time = time_manager.time()

    title = "Test Event"
    start_datetime = datetime.fromtimestamp(current_time, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    end_datetime = datetime.fromtimestamp(
        current_time + 3600, tz=timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S")
    description = "This is a test event."
    location = "Test Location"
    attendees = ["John", "Jane"]

    key = app.add_calendar_event(
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        description=description,
        location=location,
        attendees=attendees,
    )
    results = app.read_today_calendar_events()
    events = results["events"]
    assert len(events) == 1
    assert events[0] == app.events[key]


def test_read_calendar_events_by_tag():
    app = CalendarApp()
    environment = Environment()
    environment.register_apps([app])
    title = "Test Event"
    start_datetime = "2022-01-01 10:00:00"
    end_datetime = "2022-01-01 11:00:00"
    tag = "WORK"
    description = "This is a test event."
    location = "Test Location"
    attendees = ["John", "Jane"]
    key = app.add_calendar_event(
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        tag=tag,
        description=description,
        location=location,
        attendees=attendees,
    )
    events = app.get_calendar_events_by_tag(tag=tag)
    assert len(events) == 1
    assert events[0] == app.events[key]
    events = app.get_calendar_events_by_tag("PERSONAL")
    assert len(events) == 0


def test_adversarial_calendar_event():
    app = CalendarApp()
    environment = Environment()
    environment.register_apps([app])
    # try to add events with a start date after end date
    with pytest.raises(ValueError):
        app.add_calendar_event(
            title="Test Event",
            start_datetime="2022-01-01 10:00:00",
            end_datetime="2022-01-01 09:00:00",
        )
