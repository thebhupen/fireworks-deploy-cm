# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import pytest

from are.simulation.tests.scenario.scenario_test import init_test_scenario
from are.simulation.types import EventType


def test_add_event_with_event_relative_time():
    """Test adding an event with event_relative_time specified."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=0.0,
    )
    assert event1.event_relative_time == 0.0
    assert event1.event_time is None

    event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Follow-up", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.USER,
        event_id="event2",
        event_relative_time=5.0,
    )
    assert event2.event_relative_time == 5.0
    assert event2.event_time is None


def test_add_event_with_event_time():
    """Test adding an event with event_time specified."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_time=(s.start_time or 0.0) + 100.0,
    )
    assert event1.event_time == (s.start_time or 0.0) + 100.0
    assert event1.event_relative_time is None

    event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Follow-up", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.USER,
        event_id="event2",
        event_time=(s.start_time or 0.0) + 200.0,
    )
    assert event2.event_time == (s.start_time or 0.0) + 200.0
    assert event2.event_relative_time is None


def test_add_event_with_default_time():
    """Test adding an event with no time parameters specified."""
    s = init_test_scenario()

    event = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
    )
    assert event.event_relative_time == 0.0
    assert event.event_time is None


def test_add_event_negative_event_relative_time():
    """Test adding an event with negative event_relative_time raises ValueError."""
    s = init_test_scenario()

    with pytest.raises(ValueError, match="event_relative_time must be non-negative"):
        s.add_event(
            app_name="AgentUserInterface",
            function_name="send_message_to_agent",
            parameters={"content": {"value": "Hello", "type": "str"}},
            predecessor_event_ids=[],
            event_type=EventType.USER,
            event_id="event1",
            event_relative_time=-1.0,
        )


def test_add_event_negative_event_time():
    """Test adding an event with negative event_time raises ValueError."""
    s = init_test_scenario()

    with pytest.raises(ValueError, match="event_time must be non-negative"):
        s.add_event(
            app_name="AgentUserInterface",
            function_name="send_message_to_agent",
            parameters={"content": {"value": "Hello", "type": "str"}},
            predecessor_event_ids=[],
            event_type=EventType.USER,
            event_id="event1",
            event_time=-1.0,
        )


def test_add_event_both_time_parameters():
    """Test adding an event with both event_relative_time and event_time raises ValueError."""
    s = init_test_scenario()

    with pytest.raises(
        ValueError, match="event_relative_time and event_time cannot both be specified"
    ):
        s.add_event(
            app_name="AgentUserInterface",
            function_name="send_message_to_agent",
            parameters={"content": {"value": "Hello", "type": "str"}},
            predecessor_event_ids=[],
            event_type=EventType.USER,
            event_id="event1",
            event_relative_time=1.0,
            event_time=100.0,
        )


def test_edit_event_with_event_relative_time():
    """Test editing an event with event_relative_time specified."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
    )
    assert event1.event_id == "event1"

    edited_event = s.edit_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Updated Hello", "type": "str"}},
        event_id="event1",
        event_type=EventType.USER,
        predecessor_event_ids=[],
        event_relative_time=3.5,
    )

    assert edited_event.event_relative_time == 3.5
    assert edited_event.event_time is None
    assert edited_event.event_id == "event1"


def test_edit_event_with_event_time():
    """Test editing an event with event_time specified."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
    )
    assert event1.event_id == "event1"

    edited_event = s.edit_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Updated Hello", "type": "str"}},
        event_id="event1",
        event_type=EventType.USER,
        predecessor_event_ids=[],
        event_time=150.0,
    )

    assert edited_event.event_time == 150.0
    assert edited_event.event_relative_time is None
    assert edited_event.event_id == "event1"


def test_edit_event_with_default_time():
    """Test editing an event with no time parameters specified."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=5.0,
    )
    assert event1.event_relative_time == 5.0

    edited_event = s.edit_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Updated Hello", "type": "str"}},
        event_id="event1",
        event_type=EventType.USER,
        predecessor_event_ids=[],
    )

    assert edited_event.event_relative_time == 0.0
    assert edited_event.event_time is None
    assert edited_event.event_id == "event1"


def test_edit_event_negative_event_relative_time():
    """Test editing an event with negative event_relative_time raises ValueError."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
    )
    assert event1.event_id == "event1"

    with pytest.raises(ValueError, match="event_relative_time must be non-negative"):
        s.edit_event(
            app_name="AgentUserInterface",
            function_name="send_message_to_agent",
            parameters={"content": {"value": "Updated Hello", "type": "str"}},
            event_id="event1",
            event_type=EventType.USER,
            predecessor_event_ids=[],
            event_relative_time=-1.0,
        )


def test_edit_event_negative_event_time():
    """Test editing an event with negative event_time raises ValueError."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
    )
    assert event1.event_id == "event1"

    with pytest.raises(ValueError, match="event_time must be non-negative"):
        s.edit_event(
            app_name="AgentUserInterface",
            function_name="send_message_to_agent",
            parameters={"content": {"value": "Updated Hello", "type": "str"}},
            event_id="event1",
            event_type=EventType.USER,
            predecessor_event_ids=[],
            event_time=-1.0,
        )


def test_edit_event_both_time_parameters():
    """Test editing an event with both event_relative_time and event_time raises ValueError."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
    )
    assert event1.event_id == "event1"

    with pytest.raises(
        ValueError, match="event_relative_time and event_time cannot both be specified"
    ):
        s.edit_event(
            app_name="AgentUserInterface",
            function_name="send_message_to_agent",
            parameters={"content": {"value": "Updated Hello", "type": "str"}},
            event_id="event1",
            event_type=EventType.USER,
            predecessor_event_ids=[],
            event_relative_time=1.0,
            event_time=100.0,
        )


def test_edit_event_change_from_relative_to_absolute_time():
    """Test editing an event to change from event_relative_time to event_time."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_relative_time=5.0,
    )

    assert event1.event_relative_time == 5.0
    assert event1.event_time is None

    edited_event = s.edit_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Updated Hello", "type": "str"}},
        event_id="event1",
        event_type=EventType.USER,
        predecessor_event_ids=[],
        event_time=200.0,
    )

    assert edited_event.event_time == 200.0
    assert edited_event.event_relative_time is None
    assert edited_event.event_id == "event1"


def test_edit_event_change_from_absolute_to_relative_time():
    """Test editing an event to change from event_time to event_relative_time."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
        event_time=100.0,
    )

    assert event1.event_time == 100.0
    assert event1.event_relative_time is None

    edited_event = s.edit_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Updated Hello", "type": "str"}},
        event_id="event1",
        event_type=EventType.USER,
        predecessor_event_ids=[],
        event_relative_time=7.5,
    )

    assert edited_event.event_relative_time == 7.5
    assert edited_event.event_time is None
    assert edited_event.event_id == "event1"


def test_edit_event_preserve_successors():
    """Test that successors are preserved when editing an event."""
    s = init_test_scenario()

    event1 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "First message", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="event1",
    )

    event2 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Second message", "type": "str"}},
        predecessor_event_ids=["event1"],
        event_type=EventType.USER,
        event_id="event2",
    )

    event3 = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Third message", "type": "str"}},
        predecessor_event_ids=["event2"],
        event_type=EventType.USER,
        event_id="event3",
    )

    assert len(event1.successors) == 1
    assert event1.successors[0].event_id == "event2"
    assert len(event2.dependencies) == 1
    assert event2.dependencies[0].event_id == "event1"
    assert len(event2.successors) == 1
    assert event2.successors[0].event_id == "event3"
    assert len(event3.dependencies) == 1
    assert event3.dependencies[0].event_id == "event2"
    assert len(event3.successors) == 0

    edited_event = s.edit_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Updated second message", "type": "str"}},
        event_id="event2",
        event_type=EventType.USER,
        predecessor_event_ids=["event1"],
    )

    # Check predecessor relationship: event1 -> edited_event
    assert len(event1.successors) == 1
    assert event1.successors[0].event_id == "event2"
    assert event1.successors[0] is edited_event
    assert len(edited_event.dependencies) == 1
    assert edited_event.dependencies[0].event_id == "event1"
    assert edited_event.dependencies[0] is event1

    # Check successor relationship: edited_event -> event3
    assert len(edited_event.successors) == 1
    assert edited_event.successors[0].event_id == "event3"
    assert edited_event.successors[0] is event3
    assert len(event3.dependencies) == 1
    assert event3.dependencies[0].event_id == "event2"
    assert event3.dependencies[0] is edited_event


def test_add_event_invalid_event_type():
    """Test adding an event with an invalid event type raises ValueError."""
    s = init_test_scenario()

    # Test VALIDATION event type
    with pytest.raises(
        ValueError, match="event_type must be one of AGENT, ENV, USER, CONDITION"
    ):
        s.add_event(
            app_name="AgentUserInterface",
            function_name="send_message_to_agent",
            parameters={"content": {"value": "Hello", "type": "str"}},
            predecessor_event_ids=[],
            event_type=EventType.VALIDATION,
            event_id="event1",
        )

    # Test STOP event type
    with pytest.raises(
        ValueError, match="event_type must be one of AGENT, ENV, USER, CONDITION"
    ):
        s.add_event(
            app_name="AgentUserInterface",
            function_name="send_message_to_agent",
            parameters={"content": {"value": "Hello", "type": "str"}},
            predecessor_event_ids=[],
            event_type=EventType.STOP,
            event_id="event1",
        )
