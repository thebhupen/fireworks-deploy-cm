# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import logging
from collections import defaultdict, deque
from typing import Any

from are.simulation.apps.contacts import Contact, ContactsApp
from are.simulation.scenarios import Scenario
from are.simulation.scenarios.scenario_imported_from_json.benchmark_scenario import (
    build_event_id_to_turn_idx,
    is_send_message_to_user,
)
from are.simulation.types import (
    AbstractEnvironment,
    CompletedEvent,
    CompletedOracleEvent,
)
from are.simulation.validation.utils.event_utils import EventFilter

logger: logging.Logger = logging.getLogger(__name__)


def validate_scenario_attribute(scenario: Scenario):
    """
    Check if the scenario has a oracle run event log
    and event id to turn idx dictionary
    """
    if (
        not hasattr(scenario, "oracle_run_event_log")
        or scenario.oracle_run_event_log is None  # type: ignore
    ):
        raise ValueError("Oracle run event log not found")
    if (
        not hasattr(scenario, "event_id_to_turn_idx")
        or scenario.event_id_to_turn_idx is None  # type: ignore
    ):
        raise ValueError("Event id to turn not found")


def extract_tasks(scenario: Scenario) -> list[str]:
    """
    Extract the tasks from the scenario.
    """
    validate_scenario_attribute(scenario)
    # Filter tasks
    task_events = [
        event
        for event in scenario.oracle_run_event_log  # type: ignore
        if event.action.class_name == "AgentUserInterface"
        and event.action.function_name == "send_message_to_agent"
    ]
    # Merge tasks by turn idx
    turn_idx_to_task = defaultdict(lambda: "")
    for task_events in task_events:
        turn_idx = scenario.event_id_to_turn_idx[task_events.event_id]  # type: ignore
        turn_idx_to_task[turn_idx] += task_events.action.args["content"] + "\n"
    tasks = [turn_idx_to_task.get(i, "") for i in range(scenario.nb_turns)]  # type: ignore
    if len(tasks) == 0:
        raise Exception("TASK NOT FOUND")
    return tasks


def extract_user_details(scenario: Scenario) -> Contact:
    if scenario.apps is None:
        raise Exception("No apps found in scenario")
    contacts_app_names = [
        app.name for app in scenario.apps if app.name in ["Contacts", "ContactsApp"]
    ]
    if len(contacts_app_names) == 0:
        raise Exception("No contacts app found in scenario")
    contacts_app: ContactsApp = scenario.get_app(contacts_app_names[0])  # type: ignore
    user_contact = [
        contact for contact in contacts_app.contacts.values() if contact.is_user
    ]
    if len(user_contact) > 1:
        raise Exception("More than one user contact found in scenario")
    return user_contact[0]


def extract_user_name(scenario: Scenario) -> str | None:
    try:
        if scenario.apps is None:
            return None
        contacts_app_names = [
            app for app in scenario.apps if isinstance(app, ContactsApp)
        ]
        if len(contacts_app_names) == 0:
            return None
        contacts_app: ContactsApp = contacts_app_names[0]
        user_contact = [
            contact for contact in contacts_app.contacts.values() if contact.is_user
        ]
        if len(user_contact) == 1:
            return f"{user_contact[0].first_name} {user_contact[0].last_name}".lower()
        return None
    except Exception as e:
        logger.error(f"Error extracting user name: {e}")
        return None


def extract_agent_events(
    env: AbstractEnvironment, event_filter: EventFilter, turn_idx: int = -1
) -> list[CompletedEvent]:
    """
    Extract the agent events from the environment.
    """
    agent_events = [event for event in env.event_log.list_view() if event_filter(event)]
    # Sort events by time
    agent_events = sorted(agent_events, key=lambda x: x.event_time)  # type: ignore
    # Compute the turn index
    event_id_to_turn_idx = {}
    turn = 0
    for event in agent_events:
        event_id_to_turn_idx[event.event_id] = turn
        if is_send_message_to_user(event):
            turn += 1
    # Select the turn
    if turn_idx == -1:
        turn_idx = turn
    assert turn_idx <= turn, f"Invalid turn index {turn_idx} (max {turn})"
    return [
        event
        for event in agent_events
        if event_id_to_turn_idx[event.event_id] == turn_idx
    ]


GraphEventId = dict[str, list[str]]


def extract_oracle_graph(
    events: list[Any], target_oracle_event_id: list[str]
) -> GraphEventId:
    """
    This function extracts the causal graph for the oracle events.
    Note that it only considers dependencies between oracle events.
    """
    graph = {event_id: [] for event_id in target_oracle_event_id}
    for event in events:
        if event.event_id in target_oracle_event_id:
            graph[event.event_id] = list(
                {
                    e.event_id
                    for e in event.dependencies
                    if e.event_id in target_oracle_event_id
                }
            )
    return graph


def topological_sort(graph: GraphEventId) -> list[str]:
    """
    Performs a topological sort on the given graph.
    :param graph: A dictionary representing the graph, where each key is an event ID and its corresponding value is a list of parent event IDs.
    :return: A list of event IDs in topological order.
    """
    # Initialize the in-degree dictionary
    in_degree = defaultdict(int)

    # Initialize the adjacency list
    adj_list = defaultdict(list)

    # Populate the in-degree dictionary and adjacency list
    for event_id, parent_ids in graph.items():
        for parent_id in parent_ids:
            adj_list[parent_id].append(event_id)
            in_degree[event_id] += 1

    # Initialize the queue with nodes having in-degree 0
    queue = deque([event_id for event_id in graph if in_degree[event_id] == 0])

    # Perform the topological sort
    sorted_events = []
    while queue:
        event_id = queue.popleft()
        sorted_events.append(event_id)

        # Decrease the in-degree of neighboring nodes
        for neighbor_id in adj_list[event_id]:
            in_degree[neighbor_id] -= 1
            if in_degree[neighbor_id] == 0:
                queue.append(neighbor_id)

    # Check for cycles
    if len(sorted_events) != len(graph):
        raise ValueError("Graph contains a cycle")

    return sorted_events


def order_events_topologically(
    event_id_graph: GraphEventId, events: list[CompletedEvent]
):
    """
    Orders a list of events in topological order based on the given graph.
    :param graph: A dictionary representing the graph, where each key is an event ID and its corresponding value is the parent event ID.
    :param events: A list of events with unique event IDs.
    :return: The list of events in topological order.
    """
    # Create a dictionary to store the events by their IDs
    events_by_id = {event.event_id: event for event in events}
    # Perform the topological sort on the graph
    topological_order = topological_sort(event_id_graph)
    # Order the events based on the topological order
    ordered_events = [events_by_id[event_id] for event_id in topological_order]
    return ordered_events


def extract_oracle_events(
    scenario: Scenario,
    event_filter: EventFilter,
    turn_idx: int,
) -> tuple[list[CompletedOracleEvent], GraphEventId]:
    """
    Extract the oracle events and causal graph from the scenario.
    """
    validate_scenario_attribute(scenario)
    oracle_events = [
        event
        for event in scenario.oracle_run_event_log  # type: ignore
        if event_filter(event)
    ]
    oracle_events = [
        e
        for e in oracle_events
        if scenario.event_id_to_turn_idx[e.event_id] == turn_idx  # type: ignore
    ]
    # Extract the oracle graph
    oracle_graph = extract_oracle_graph(
        events=scenario.events,
        target_oracle_event_id=[e.event_id for e in oracle_events],
    )
    # Sort oracle events in topological order
    oracle_events = order_events_topologically(
        events=oracle_events, event_id_graph=oracle_graph
    )
    # Create enriched oracle events with timing information
    oracle_events_dict = {e.event_id: e for e in scenario.events}
    completed_oracle_events = []
    for completed_event in oracle_events:
        event = oracle_events_dict[completed_event.event_id]
        completed_oracle_event = (
            CompletedOracleEvent.from_completed_event_and_oracle_event(
                completed_event=completed_event,
                oracle_event=event,
            )
        )
        completed_oracle_events.append(completed_oracle_event)
    return completed_oracle_events, oracle_graph


def run_oracle_mode(scenario: Scenario):
    from are.simulation.environment import Environment, EnvironmentConfig

    # build event id to turn idx
    build_event_id_to_turn_idx(scenario)
    # Run the scenario in oracle mode
    if not scenario._initialized:
        scenario.initialize()
    env = Environment(
        EnvironmentConfig(
            oracle_mode=True,
            queue_based_loop=True,
            start_time=scenario.start_time,
            duration=scenario.duration,
            time_increment_in_seconds=scenario.time_increment_in_seconds,
        )
    )
    env.run(scenario)
    env.stop()
    scenario.soft_reset()
    oracle_run_event_log = env.event_log.list_view()
    # Check clean run
    if any(e.failed() for e in oracle_run_event_log):
        raise Exception(
            f"Oracle run failed: {[e.metadata.exception for e in oracle_run_event_log if e.failed()]}"
        )
    # Attach the oracle run events to the scenario for the judge
    scenario.oracle_run_event_log = env.event_log.list_view()  # type: ignore
