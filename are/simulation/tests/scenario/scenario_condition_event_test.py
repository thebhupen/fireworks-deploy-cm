# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from are.simulation.data_handler.models import ExportedExecutionMetadata
from are.simulation.tests.scenario.scenario_test import init_test_scenario
from are.simulation.types import ConditionCheckEvent, EventType


def test_add_event_condition():
    """Test adding a condition event to a scenario."""
    s = init_test_scenario()

    # Add dummy execution metadata
    s.execution_metadata = ExportedExecutionMetadata(  # type: ignore
        placeholders=[],
        has_placeholder_conflicts=False,
    )

    # Add a user event first
    user_event = s.add_event(
        app_name="AgentUserInterface",
        function_name="send_message_to_agent",
        parameters={"content": {"value": "Hello", "type": "str"}},
        predecessor_event_ids=[],
        event_type=EventType.USER,
        event_id="user_event",
    )

    # Add a condition event that checks for a specific turn
    condition_event = s.add_event(
        app_name="",  # Not needed for condition events
        function_name="wrapped_condition__turn_idx_1__scenario_id_scenario_universe_33",  # This format is expected by condition_from_name
        parameters={},  # No parameters needed for condition events
        predecessor_event_ids=["user_event"],
        event_type=EventType.CONDITION,
        event_id="condition_event",
    )

    # Verify the condition event was created correctly
    assert condition_event is not None
    assert condition_event.event_type == EventType.CONDITION
    assert condition_event.event_id == "condition_event"
    assert isinstance(condition_event, ConditionCheckEvent)
    assert len(condition_event.dependencies) == 1
    assert condition_event.dependencies[0].event_id == "user_event"

    # Verify the condition function was created correctly
    assert condition_event.action is not None
    assert (
        condition_event.action.function.__name__
        == "wrapped_condition__turn_idx_1__scenario_id_scenario_universe_33"
    )

    # Verify the user event has the condition event as a successor
    assert len(user_event.successors) == 1
    assert user_event.successors[0].event_id == "condition_event"
