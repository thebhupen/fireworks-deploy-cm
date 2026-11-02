# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import unittest.mock as mock

import pytest

from are.simulation.tests.scenario.scenario_test import init_test_scenario
from are.simulation.types import EventType


def test_validate_events_dag_base_on_time_no_predecessors():
    """Test that the function returns early when there are no predecessor event IDs."""
    s = init_test_scenario()

    # This should not raise any error since there are no predecessors
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=[],
        function_name="send_message_to_agent",
        new_event_relative_time=5.0,
    )


def test_validate_events_dag_base_on_time_no_delays():
    """Test that the function returns early when no event has a delay (event_relative_time > 1)."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "How can I help", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=1.0,
    )

    # This should not raise any error since there are no delays
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event2"],
        function_name="send_message_to_agent",
        new_event_relative_time=1.0,
    )


def test_validate_events_dag_base_on_time_with_delays():
    """Test that the function correctly validates events with delays."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "How can I help", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=5.0,
    )

    # This should not raise any error since the new event's time is after send_message_to_user
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event2"],
        function_name="send_message_to_agent",
        new_event_relative_time=1.0,
    )


def test_validate_events_dag_base_on_time_send_message_to_user_exceeds_max():
    """Test that the function raises an error when send_message_to_user event's time exceeds allowed maximum."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="CalendarApp",
        function_name="read_today_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=10.0,
    )

    # This should raise an error since the new send_message_to_user event's time would be less than the max time
    with pytest.raises(
        ValueError,
        match=r"send_message_to_user event's time \(\d+\.\d+\) should be the maximum of the turn \(\d+\.\d+\)\.",
    ):
        s.validate_events_dag_message_to_user_time(
            predecessor_event_ids=["event1"],
            function_name="send_message_to_user",
            new_event_relative_time=1.0,  # Total time would be 1.0, which is less than event2's accumulated time
        )


def test_validate_events_dag_base_on_time_event_exceeds_send_message_to_user():
    """Test that the function raises an error when a new event's time exceeds send_message_to_user time."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "How can I help", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=5.0,
    )

    # This should raise an error since the new event's time would exceed send_message_to_user time
    with pytest.raises(
        ValueError,
        match=r"New event's time \(\d+\.\d+\) exceeds send_message_to_user event's time \(\d+\.\d+\)\.",
    ):
        s.validate_events_dag_message_to_user_time(
            predecessor_event_ids=["event1"],
            function_name="read_today_calendar_events",
            new_event_relative_time=6.0,  # Greater than event2's time
        )


def test_validate_events_dag_base_on_time_different_turns():
    """Test that the function raises an error when predecessor events belong to different turns."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "How can I help", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=1.0,
    )

    _event3 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={
            "content": {"value": "I need help with my calendar", "type": "str"}
        },
        predecessor_event_ids=["event2"],
        event_type=EventType.USER,
        event_id="event3",
        event_relative_time=0.0,
    )

    # This should raise an error since event1 and event3 belong to different turns
    with pytest.raises(
        ValueError, match="Predecessor events do not belong to the same turn"
    ):
        s.validate_events_dag_message_to_user_time(
            predecessor_event_ids=["event1", "event3"],
            function_name="read_today_calendar_events",
            new_event_relative_time=1.0,
        )


def test_validate_events_dag_base_on_time_new_turn():
    """Test that the function correctly handles events in a new turn."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "How can I help", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=5.0,
    )

    _event3 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={
            "content": {"value": "I need help with my calendar", "type": "str"}
        },
        predecessor_event_ids=["event2"],
        event_type=EventType.USER,
        event_id="event3",
        event_relative_time=0.0,
    )

    # This should not raise any error since we're adding an event in a new turn
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event3"],
        function_name="read_today_calendar_events",
        new_event_relative_time=10.0,  # Even though this is large, it's in a new turn
    )


def test_validate_events_dag_base_on_time_send_message_to_user_in_new_turn():
    """Test that the function correctly handles send_message_to_user events in a new turn."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "How can I help", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=5.0,
    )

    _event3 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={
            "content": {"value": "I need help with my calendar", "type": "str"}
        },
        predecessor_event_ids=["event2"],
        event_type=EventType.USER,
        event_id="event3",
        event_relative_time=0.0,
    )

    # This should not raise any error since we're adding a send_message_to_user event in a new turn
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event3"],
        function_name="send_message_to_user",
        new_event_relative_time=15.0,  # Even though this is large, it's in a new turn
    )


def test_validate_events_dag_base_on_time_validation_not_required():
    """Test that the function returns early when EVENT_TIME_VALIDATION_REQUIRED is False."""
    s = init_test_scenario()

    with mock.patch(
        "are.simulation.scenarios.scenario.EVENT_TIME_VALIDATION_REQUIRED", False
    ):
        # This should not raise any error even with invalid inputs
        s.validate_events_dag_message_to_user_time(
            predecessor_event_ids=["non_existent_event"],
            function_name="send_message_to_agent",
            new_event_relative_time=5.0,
        )


def test_validate_events_dag_base_on_time_empty_events():
    """Test that the function handles an empty events list correctly."""
    s = init_test_scenario()

    # This should not raise any error with an empty events list
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=[],
        function_name="send_message_to_agent",
        new_event_relative_time=5.0,
    )


def test_validate_events_dag_base_on_time_invalid_predecessor():
    """Test that the function raises KeyError for invalid predecessor event IDs."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    # This should raise a KeyError since the predecessor event ID doesn't exist
    with pytest.raises(KeyError, match="'non_existent_event'"):
        s.validate_events_dag_message_to_user_time(
            predecessor_event_ids=["non_existent_event"],
            function_name="send_message_to_agent",
            new_event_relative_time=5.0,
        )


def test_validate_events_dag_base_on_time_multiple_predecessors_same_turn():
    """Test that the function correctly handles multiple predecessors in the same turn."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="CalendarApp",
        function_name="read_today_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=2.0,
    )

    _event3 = s.add_event(
        app_name="CalendarApp",
        function_name="get_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event3",
        event_relative_time=3.0,
    )

    # This should not raise any error since both predecessors are in the same turn
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event2", "event3"],
        function_name="send_message_to_user",
        new_event_relative_time=1.0,
    )


def test_validate_events_dag_base_on_time_max_predecessor_time():
    """Test that the function correctly calculates the maximum predecessor time."""
    s = init_test_scenario()

    # Add events with different relative times
    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="CalendarApp",
        function_name="read_today_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=2.0,
    )

    _event3 = s.add_event(
        app_name="CalendarApp",
        function_name="get_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event3",
        event_relative_time=5.0,
    )

    # This should not raise any error since the new event's time is after the maximum predecessor time
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event2", "event3"],
        function_name="send_message_to_user",
        new_event_relative_time=1.0,  # Total time would be 5.0 + 1.0 = 6.0, which is greater than any other event
    )


def test_validate_events_dag_base_on_time_send_message_to_user_equal_max():
    """Test that the function correctly handles send_message_to_user events with time equal to the maximum."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="CalendarApp",
        function_name="read_today_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=10.0,
    )

    # This should not raise any error since the new send_message_to_user event's time equals the max time
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event1"],
        function_name="send_message_to_user",
        new_event_relative_time=10.0,  # Total time would be 10.0, which equals event2's accumulated time
    )


def test_validate_events_dag_base_on_time_complex_dag():
    """Test that the function correctly handles a complex DAG with multiple events and dependencies."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="CalendarApp",
        function_name="read_today_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=2.0,
    )

    _event3 = s.add_event(
        app_name="CalendarApp",
        function_name="get_calendar_events",
        parameters={},
        predecessor_event_ids=["event2"],
        event_type=EventType.AGENT,
        event_id="event3",
        event_relative_time=3.0,
    )

    _event4 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={
            "content": {"value": "Here are your calendar events", "type": "str"}
        },
        predecessor_event_ids=["event3"],
        event_type=EventType.AGENT,
        event_id="event4",
        event_relative_time=4.0,
    )

    # This should not raise any error since we're adding an event after the send_message_to_user in a new turn
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event4"],
        function_name="send_message_to_agent",
        new_event_relative_time=1.0,
    )


def test_validate_events_dag_base_on_time_zero_relative_time():
    """Test that the function correctly handles events with zero relative time."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "How can I help", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=0.0,
    )

    # This should not raise any error since there are no delays (all event_relative_time values are 0)
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event2"],
        function_name="send_message_to_agent",
        new_event_relative_time=0.0,
    )


def test_validate_events_dag_base_on_time_with_new_event_time():
    """Test that the function correctly validates events with new_event_time instead of new_event_relative_time."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "How can I help", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=5.0,
    )

    # This should not raise any error since the new event's time is after send_message_to_user
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event2"],
        function_name="send_message_to_agent",
        new_event_time=10.0,  # Absolute time instead of relative time
    )


def test_validate_events_dag_base_on_time_send_message_to_user_with_new_event_time():
    """Test that the function correctly validates send_message_to_user events with new_event_time."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="CalendarApp",
        function_name="read_today_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=10.0,
    )

    # This should not raise any error since the new send_message_to_user event's time equals the max time
    # Absolute time equals event2's accumulated time
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event1"],
        function_name="send_message_to_user",
        new_event_time=(s.start_time or 0.0) + 10.0,
    )


def test_validate_events_dag_base_on_time_send_message_to_user_with_new_event_time_exceeds_max():
    """Test that the function raises an error when send_message_to_user event's time with new_event_time exceeds allowed maximum."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="CalendarApp",
        function_name="read_today_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=10.0,
    )

    # This should raise an error since the new send_message_to_user event's time would be less than the max time
    with pytest.raises(
        ValueError,
        match=r"send_message_to_user event's time \(\d+\.\d+\) should be the maximum of the turn \(\d+\.\d+\)\.",
    ):
        s.validate_events_dag_message_to_user_time(
            predecessor_event_ids=["event1"],
            function_name="send_message_to_user",
            new_event_time=5.0,  # Less than event2's accumulated time
        )


def test_validate_events_dag_base_on_time_event_exceeds_send_message_to_user_with_new_event_time():
    """Test that the function raises an error when a new event's time with new_event_time exceeds send_message_to_user time."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "How can I help", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=5.0,
    )

    # This should raise an error since the new event's time would exceed send_message_to_user time
    with pytest.raises(
        ValueError,
        match=r"New event's time \(\d+\.\d+\) exceeds send_message_to_user event's time \(\d+\.\d+\)\.",
    ):
        s.validate_events_dag_message_to_user_time(
            predecessor_event_ids=["event1"],
            function_name="read_today_calendar_events",
            new_event_relative_time=6.0,  # Greater than event2's time
        )


def test_validate_events_dag_base_on_time_with_event_time_instead_of_relative_time():
    """Test that the function correctly validates events that have event_time instead of event_relative_time."""
    s = init_test_scenario()

    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_time=(s.start_time or 0.0) + 5.0,
    )

    # This should not raise any error
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event1"],
        function_name="send_message_to_user",
        new_event_relative_time=1.0,
    )


def test_validate_events_dag_base_on_time_skip_validation_when_all_events_have_time_0_or_1():
    """Test that validation is skipped when all events in turn have relative time of 0 or 1."""
    s = init_test_scenario()

    # Create events with relative time of 0 and 1 only
    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="CalendarApp",
        function_name="read_today_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=1.0,
    )

    _event3 = s.add_event(
        app_name="CalendarApp",
        function_name="get_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event3",
        event_relative_time=0.0,
    )

    # This should not raise any error because all events have relative time of 0 or 1
    # The validation should be skipped entirely
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event2", "event3"],
        function_name="send_message_to_user",
        new_event_relative_time=10.0,  # Even with a large time, validation should be skipped
    )


def test_validate_events_dag_dependency_chain_modification():
    """Test that modifying an event's relative time in a dependency chain does not raise an error."""
    s = init_test_scenario()

    # Create event chain: _event1 -> _event2 -> _event3 -> _event4
    _event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )

    _event2 = s.add_event(
        app_name="CalendarApp",
        function_name="read_today_calendar_events",
        parameters={},
        predecessor_event_ids=["event1"],
        event_type=EventType.AGENT,
        event_id="event2",
        event_relative_time=95.0,
    )

    _event3 = s.add_event(
        app_name="CalendarApp",
        function_name="get_calendar_events",
        parameters={},
        predecessor_event_ids=["event2"],
        event_type=EventType.AGENT,
        event_id="event3",
        event_relative_time=5.0,
    )

    _event4 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_user",
        parameters={"content": {"value": "Here are your events", "type": "str"}},
        predecessor_event_ids=["event3"],
        event_type=EventType.AGENT,
        event_id="event4",
        event_relative_time=1.0,
    )

    # This validation should pass without raising an error
    s.validate_events_dag_message_to_user_time(
        predecessor_event_ids=["event1"],
        function_name="read_today_calendar_events",
        new_event_relative_time=96.0,
        event_id="event2",
    )
