# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import pytest

from are.simulation.types import (
    EventType,
    HintType,
    OracleEvent,
    ToolAugmentationConfig,
)


def test_initialize_scenario():
    s = init_test_scenario()
    assert s.apps is not None


def init_test_scenario():
    from are.simulation.scenarios.utils.load_utils import load_hf_demo_universes

    scenarios = load_hf_demo_universes()

    assert len(scenarios) > 0
    scenario = list(scenarios.values())[0]
    s = scenario()
    s.init_and_populate_apps()
    return s


def add_user_aui_event(scenario, predecessors, event_id):
    scenario.add_event(
        "AgentUserInterface",
        "send_message_to_agent",
        {"content": {"value": "Hello", "type": "str"}},
        predecessors,
        EventType.USER,
        event_id,
    )


def add_agent_aui_event(scenario, predecessors, event_id):
    scenario.add_event(
        "AgentUserInterface",
        "send_message_to_user",
        {"content": {"value": "How can I help", "type": "str"}},
        predecessors,
        EventType.AGENT,
        event_id,
    )


def add_env_aui_get_all_message_event(scenario, predecessors, event_id):
    scenario.add_event(
        "AgentUserInterface",
        "get_all_messages",
        {},
        predecessors,
        EventType.ENV,
        event_id,
    )


def add_calendar_event(scenario, predecessors, event_id):
    scenario.add_event(
        "CalendarApp",
        "add_calendar_event",
        {
            "title": {"value": "Event", "type": "str"},
            "start_datetime": {"value": "2024-12-11 23:06:38", "type": "str"},
            "end_datetime": {"value": "2024-12-12 00:06:38", "type": "str"},
            "tag": {"value": "", "type": "str | None"},
            "description": {"value": "", "type": "str | None"},
            "location": {"value": "", "type": "str | None"},
            "attendees": {"value": "[]", "type": "list[str]"},
        },
        predecessors,
        EventType.AGENT,
        event_id,
    )


def edit_to_cal_event(scenario, event_id, predecessors):
    scenario.edit_event(
        "CalendarApp",
        "add_calendar_event",
        {
            "title": {"value": "Event", "type": "str"},
            "start_datetime": {"value": "2024-12-11 23:06:38", "type": "str"},
            "end_datetime": {"value": "2024-12-12 00:06:38", "type": "str"},
            "tag": {"value": "", "type": "str | None"},
            "description": {"value": "", "type": "str | None"},
            "location": {"value": "", "type": "str | None"},
            "attendees": {"value": "[]", "type": "list[str]"},
        },
        event_id,
        EventType.AGENT,
        predecessors,
    )


def edit_to_user_event(scenario, event_id, predecessors):
    scenario.edit_event(
        "AgentUserInterface",
        "send_message_to_agent",
        {"content": {"value": "Hello", "type": "str"}},
        event_id,
        EventType.USER,
        predecessors,
    )


def edit_to_agent_event(scenario, event_id, predecessors):
    scenario.edit_event(
        "AgentUserInterface",
        "send_message_to_agent",
        {"content": {"value": "How can I help", "type": "str"}},
        event_id,
        EventType.AGENT,
        predecessors,
    )


def edit_env_aui_get_all_message_event(scenario, predecessors, event_id):
    scenario.edit_event(
        "AgentUserInterface",
        "get_all_messages",
        {},
        event_id,
        EventType.ENV,
        predecessors,
    )


def test_add_event_success():
    s = init_test_scenario()
    assert len(s.events) == 0
    add_user_aui_event(s, [], "to_agent_event")
    assert len(s.events) == 1
    add_agent_aui_event(s, ["to_agent_event"], "to_user_event")
    add_calendar_event(s, ["to_agent_event"], "cal_1")
    assert len(s.events) == 3


def test_add_event_predecessor_not_found():
    s = init_test_scenario()
    with pytest.raises(
        ValueError, match="Predecessor event with id 'non_exist' not found"
    ):
        add_user_aui_event(s, ["non_exist"], "to_agent_event")


def test_add_event_special_rule_violation():
    s = init_test_scenario()
    with pytest.raises(
        ValueError, match="Agent events must have at least one predecessor event"
    ):
        add_agent_aui_event(s, [], "to_user_event")
    with pytest.raises(
        ValueError,
        match="The add_calendar_event event is not allowed to link after send_message_to_user",
    ):
        add_user_aui_event(s, [], "to_agent_event")
        add_agent_aui_event(s, ["to_agent_event"], "to_user_event")
        add_env_aui_get_all_message_event(s, ["to_agent_event"], "get_all_message")
        add_calendar_event(s, ["to_user_event"], "cal_1")


def test_add_aui_event_special_rule_violation():
    s = init_test_scenario()
    with pytest.raises(
        ValueError,
        match="Only one branch of the events graph should contain send_message_to_agent or send_message_to_user events. Found multiple branches with send_message_to_agent or send_message_to_user events.",
    ):
        add_user_aui_event(s, [], "to_agent_event")
        add_agent_aui_event(s, ["to_agent_event"], "to_user_event")
        add_user_aui_event(s, [], "to_agent_event_2")


def test_add_env_event_special_rule_violation():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event")
    add_agent_aui_event(s, ["to_agent_event"], "to_user_event")
    add_calendar_event(s, ["to_agent_event"], "cal_1")
    # Test: Adding an env event with no predecessor
    with pytest.raises(
        ValueError,
        match="Env events must have only one predecessor event",
    ):
        add_env_aui_get_all_message_event(s, [], "get_all_message_1")
    # Test: Adding an env event with more than one predecessor
    with pytest.raises(
        ValueError,
        match="Env events must have only one predecessor event",
    ):
        add_env_aui_get_all_message_event(
            s, ["to_user_event", "cal_1"], "get_all_message_2"
        )
    # Test: Adding an env event with an invalid predecessor type
    with pytest.raises(
        ValueError,
        match="Env events can only have a send_message_to_agent or user/env event as a predecessor event.",
    ):
        add_env_aui_get_all_message_event(s, ["cal_1"], "get_all_message_2")
    # Test: Adding an env event with a non-existent predecessor
    with pytest.raises(
        ValueError,
        match="Predecessor event with id 'to_agent_event_2' not found.",
    ):
        add_env_aui_get_all_message_event(s, ["to_agent_event_2"], "get_all_message_2")
    add_env_aui_get_all_message_event(s, ["to_agent_event"], "get_all_message_2")
    add_env_aui_get_all_message_event(s, ["get_all_message_2"], "get_all_message_3")


def test_edit_event_success():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event")
    add_calendar_event(s, ["to_agent_event"], "cal_1")
    new_event = s.edit_event(
        "AgentUserInterface",
        "send_message_to_user",
        {"content": {"value": "How can I help", "type": "str"}},
        "cal_1",
        EventType.AGENT,
        ["to_agent_event"],
    )
    assert type(new_event) is OracleEvent
    if new_event.action_desc is not None:
        assert new_event.action_desc.function == "send_message_to_user"


def test_edit_event_not_found():
    s = init_test_scenario()
    with pytest.raises(ValueError, match="Current event with id 'non_exist' not found"):
        s.edit_event(
            "AgentUserInterface",
            "send_message_to_user",
            {"content": {"value": "How can I help", "type": "str"}},
            "non_exist",
            EventType.AGENT,
            [],
        )


def test_edit_event_predecessor_not_found():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event")
    with pytest.raises(
        ValueError, match="Predecessor event with id 'non_exist' not found"
    ):
        s.edit_event(
            "AgentUserInterface",
            "send_message_to_user",
            {"content": {"value": "How can I help", "type": "str"}},
            "to_agent_event",
            EventType.AGENT,
            ["non_exist"],
        )


def test_edit_event_special_rule_violation():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event")
    with pytest.raises(
        ValueError,
        match="Agent events must have at least one predecessor event",
    ):
        edit_to_cal_event(s, "to_agent_event", [])
    add_agent_aui_event(s, ["to_agent_event"], "to_user_event")
    add_user_aui_event(s, ["to_user_event"], "to_agent_event_2")
    with pytest.raises(
        ValueError,
        match="The add_calendar_event event is not allowed to link after send_message_to_user",
    ):
        edit_to_cal_event(s, "to_agent_event_2", ["to_user_event"])
    edit_env_aui_get_all_message_event(s, ["to_user_event"], "to_agent_event_2")


def test_edit_aui_event_special_rule_violation():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event")
    with pytest.raises(
        ValueError,
        match="Only one branch of the events graph should contain send_message_to_agent or send_message_to_user events. Found multiple branches with send_message_to_agent or send_message_to_user events.",
    ):
        add_user_aui_event(s, [], "to_agent_event")
        add_agent_aui_event(s, ["to_agent_event"], "to_user_event")
        add_env_aui_get_all_message_event(s, [], "get_all_message")
        edit_to_user_event(s, "get_all_message", [])


def test_edit_env_event_special_rule_violation():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event")
    add_agent_aui_event(s, ["to_agent_event"], "to_user_event_1")
    add_agent_aui_event(s, ["to_agent_event"], "to_user_event_2")
    # Test: Editing an env event with more than one predecessor
    with pytest.raises(
        ValueError,
        match="Env events must have only one predecessor event",
    ):
        edit_env_aui_get_all_message_event(
            s,
            ["to_user_event_1", "to_agent_event"],
            "to_user_event_2",
        )
    # Test: Editing an env event with an invalid predecessor type
    add_calendar_event(s, ["to_agent_event"], "cal_1")
    with pytest.raises(
        ValueError,
        match="Env events can only have a send_message_to_agent or user/env event as a predecessor event.",
    ):
        edit_env_aui_get_all_message_event(
            s,
            ["cal_1"],
            "cal_1",
        )
    # Test: Editing an env event with a non-existent predecessor
    with pytest.raises(
        ValueError,
        match="Predecessor event with id 'non_existent_event' not found.",
    ):
        edit_env_aui_get_all_message_event(
            s,
            ["non_existent_event"],
            "cal_1",
        )
    # Test: Editing an env event with a valid predecessor
    edit_env_aui_get_all_message_event(
        s,
        ["to_user_event_1"],
        "cal_1",
    )


def test_add_event_creates_hint():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event")
    assert len(s.hints or []) == 1
    assert s.hints is not None and s.hints[0].associated_event_id == "to_agent_event"
    assert s.hints is not None and s.hints[0].hint_type == HintType.TASK_HINT
    add_env_aui_get_all_message_event(s, ["to_agent_event"], "get_all_message_1")
    assert len(s.hints or []) == 2
    assert s.hints is not None and s.hints[1].associated_event_id == "get_all_message_1"
    assert s.hints is not None and s.hints[1].hint_type == HintType.ENVIRONMENT_HINT
    add_env_aui_get_all_message_event(s, ["to_agent_event"], "get_all_message_2")
    assert len(s.hints or []) == 3
    assert s.hints is not None and s.hints[2].associated_event_id == "get_all_message_2"
    assert s.hints is not None and s.hints[2].hint_type == HintType.ENVIRONMENT_HINT


def test_edit_event_removes_hint():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event_1")
    add_agent_aui_event(s, ["to_agent_event_1"], "to_user_event")
    add_user_aui_event(s, ["to_user_event"], "to_agent_event_2")
    assert len(s.hints or []) == 2
    edit_to_cal_event(s, "to_agent_event_2", ["to_agent_event_1"])
    assert len(s.hints or []) == 1
    add_env_aui_get_all_message_event(s, ["to_agent_event_1"], "get_all_message")
    assert len(s.hints or []) == 2
    edit_to_cal_event(s, "get_all_message", ["to_agent_event_1"])
    assert len(s.hints or []) == 1


def test_edit_event_adds_hint():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event_1")
    add_calendar_event(s, ["to_agent_event_1"], "cal_1")
    assert len(s.hints or []) == 1
    edit_to_user_event(s, "cal_1", ["to_agent_event_1"])
    assert len(s.hints or []) == 2
    add_calendar_event(s, ["to_agent_event_1"], "cal_2")
    assert len(s.hints or []) == 2
    edit_env_aui_get_all_message_event(s, ["to_agent_event_1"], "cal_2")
    assert len(s.hints or []) == 3


def test_delete_event_removes_hint():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event")
    assert len(s.hints or []) == 1
    s.delete_event("to_agent_event")
    assert len(s.hints or []) == 0
    add_user_aui_event(s, [], "to_agent_event")
    add_env_aui_get_all_message_event(s, ["to_agent_event"], "get_all_message")
    assert len(s.hints or []) == 2
    s.delete_event("get_all_message")
    assert len(s.hints or []) == 1


def test_edit_hint_content():
    s = init_test_scenario()
    add_user_aui_event(s, [], "to_agent_event")
    s.edit_hint_content("to_agent_event", "New hint content")
    assert s.hints is not None and s.hints[0].content == "New hint content"


def test_failure_probability():
    s = init_test_scenario()
    s.tool_augmentation_config = ToolAugmentationConfig(tool_failure_probability=0.5)
    s.initialize()

    assert all(tool.failure_probability == 0.5 for tool in s.get_tools())


def test_failure_probability_preserved_after_soft_reset():
    """
    Test that failure probability is preserved after calling soft_reset().
    """
    s = init_test_scenario()
    failure_prob = 0.75
    s.tool_augmentation_config = ToolAugmentationConfig(
        tool_failure_probability=failure_prob
    )
    s.initialize()

    for app in s.apps or []:
        assert app.failure_probability == failure_prob

    s.soft_reset()

    for app in s.apps or []:
        assert app.failure_probability == failure_prob

    for tool in s.get_tools():
        assert tool.failure_probability == failure_prob


def test_modify_event_times_no_errors():
    """Test that modifying event times in a 3-event scenario does not raise errors."""
    s = init_test_scenario()

    s.add_event(
        "AgentUserInterface",
        "send_message_to_agent",
        {"content": {"value": "Hello", "type": "str"}},
        [],
        EventType.USER,
        "event1",
        event_relative_time=0.0,
    )

    s.add_event(
        "CalendarApp",
        "read_today_calendar_events",
        {},
        ["event1"],
        EventType.AGENT,
        "event2",
        event_relative_time=5.0,
    )

    s.add_event(
        "CalendarApp",
        "get_calendar_events",
        {},
        ["event2"],
        EventType.AGENT,
        "event3",
        event_relative_time=10.0,
    )

    s.add_event(
        "CalendarApp",
        "get_calendar_events",
        {},
        ["event3"],
        EventType.AGENT,
        "event4",
        event_relative_time=3.0,
    )

    s.add_event(
        "AgentUserInterface",
        "send_message_to_user",
        {"content": {"value": "How can I help", "type": "str"}},
        ["event4"],
        EventType.AGENT,
        "event5",
        event_relative_time=1.0,
    )

    s.edit_event(
        "CalendarApp",
        "read_today_calendar_events",
        {},
        "event3",
        EventType.AGENT,
        ["event2"],
        event_relative_time=10.0,
    )

    s.edit_event(
        "CalendarApp",
        "read_today_calendar_events",
        {},
        "event3",
        EventType.AGENT,
        ["event2"],
        event_relative_time=20.0,
    )
