# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json

import strawberry
from strawberry.scalars import JSON

from are.simulation.gui.server.graphql.common import make_async
from are.simulation.gui.server.graphql.subscription import clear_graphql_cache
from are.simulation.gui.server.graphql.types import (
    ExecuteAppToolResultForGraphQL,
    ScenarioForGraphQL,
)
from are.simulation.types import EventTimeComparator, EventType
from are.simulation.utils import make_serializable


@strawberry.type
class Mutation:
    """GraphQL mutation class for Meta Agents Research Environments operations.

    This class provides GraphQL mutations for managing simulation scenarios,
    agents, playback controls, and various simulation operations.
    """

    server = None  # : ARESimulationServer | None - Can't type this because of circular dependency

    @strawberry.mutation
    @make_async
    def set_scenario(
        self, scenario_id: str, session_id: str
    ) -> ScenarioForGraphQL | None:
        """Set the active scenario for a simulation session.

        :param scenario_id: The unique identifier of the scenario to set
        :param session_id: The unique identifier of the simulation session
        :return: The scenario object for GraphQL, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.set_scenario(scenario_id)
        clear_graphql_cache(session_id)
        return ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)

    @strawberry.mutation
    @make_async
    def set_agent_name(
        self,
        agent_id: str | None,
        session_id: str,  # type: ignore
    ) -> JSON | None:  # type: ignore
        """Set the agent name for a simulation session.

        :param agent_id: The unique identifier of the agent to set, or None to clear
        :param session_id: The unique identifier of the simulation session
        :return: The agent configuration with schema, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.set_agent_name(agent_id)
        return are_simulation_instance.get_agent_config_with_schema()

    @strawberry.mutation
    @make_async
    def set_agent_config(
        self,
        agent_config: JSON | None,  # type: ignore
        session_id: str,  # type: ignore
    ) -> JSON | None:  # type: ignore
        """Set the agent configuration for a simulation session.

        :param agent_config: The agent configuration as JSON, or None to clear
        :param session_id: The unique identifier of the simulation session
        :return: The agent configuration with schema, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.set_agent_config(agent_config)
        return are_simulation_instance.get_agent_config_with_schema()

    @strawberry.mutation
    @make_async
    def play(self, session_id: str) -> ScenarioForGraphQL | None:
        """Start playback of the simulation scenario.

        :param session_id: The unique identifier of the simulation session
        :return: The scenario object for GraphQL, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.play()
        return ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)

    @strawberry.mutation
    @make_async
    def pause(self, session_id: str) -> ScenarioForGraphQL | None:
        """Pause the simulation scenario playback.

        :param session_id: The unique identifier of the simulation session
        :return: The scenario object for GraphQL, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.pause()
        return ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)

    @strawberry.mutation
    @make_async
    def stop(self, session_id: str) -> ScenarioForGraphQL | None:
        """Stop the simulation scenario playback.

        :param session_id: The unique identifier of the simulation session
        :return: The scenario object for GraphQL, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.stop()
        return ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)

    @strawberry.mutation
    @make_async
    def load(self, session_id: str) -> ScenarioForGraphQL | None:
        """Load the simulation scenario.

        :param session_id: The unique identifier of the simulation session
        :return: The scenario object for GraphQL, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.load()
        return ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)

    @strawberry.mutation
    @make_async
    def delete_logs_after(
        self, id: str, session_id: str, edit: str | None
    ) -> ScenarioForGraphQL | None:
        """Delete logs after a specific point and replay from that turn.

        :param id: The identifier of the log entry to replay from
        :param session_id: The unique identifier of the simulation session
        :param edit: Optional edit content to apply during replay
        :return: The scenario object for GraphQL, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.replay_turn(id, edit)
        clear_graphql_cache(session_id)
        return are_simulation_instance.scenario

    @strawberry.mutation
    @make_async
    def amend_and_replay(
        self, session_id: str, log_id: str, content: str
    ) -> ScenarioForGraphQL | None:
        """Amend a log entry and replay the scenario from that point.

        :param session_id: The unique identifier of the simulation session
        :param log_id: The identifier of the log entry to amend
        :param content: The new content to replace the original log entry
        :return: The scenario object for GraphQL, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.replay_modified_output(log_id, content)
        clear_graphql_cache(session_id)
        return are_simulation_instance.scenario

    @strawberry.mutation
    @make_async
    def send_user_message_to_agent(
        self, message: str, attachments: list[tuple[str, str]] | None, session_id: str
    ) -> str:
        """Send a user message to the agent in the simulation.

        :param message: The message content to send to the agent
        :param attachments: Optional list of attachments as tuples of (filename, content)
        :param session_id: The unique identifier of the simulation session
        :return: The response from the agent
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        return are_simulation_instance.send_user_message_to_agent(message, attachments)

    @strawberry.mutation
    @make_async
    def send_conversation_message(
        self,
        session_id: str,
        messaging_app_name: str,
        conversation_id: str,
        sender: str,
        message: str,
    ) -> bool:
        """Send a message to a conversation in a messaging app.

        :param session_id: The unique identifier of the simulation session
        :param messaging_app_name: The name of the messaging app
        :param conversation_id: The unique identifier of the conversation
        :param sender: The sender of the message
        :param message: The message content to send
        :return: True if the message was sent successfully, False otherwise
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        return are_simulation_instance.send_conversation_message(
            messaging_app_name, conversation_id, sender, message
        )

    @strawberry.mutation
    @make_async
    def add_scenario_event(
        self,
        session_id: str,
        app: str,
        function: str,
        parameters: str,
        predecessor_event_ids: list[str],
        event_type: EventType,
        event_relative_time: float | None = None,
        event_time: float | None = None,
        event_time_comparator: EventTimeComparator | None = None,
    ) -> str:
        """Add a new event to the scenario.

        :param session_id: The unique identifier of the simulation session
        :param app: The name of the app for the event
        :param function: The function name to execute
        :param parameters: The parameters for the function as a string
        :param predecessor_event_ids: List of event IDs that must complete before this event
        :param event_type: The type of event to add
        :param event_relative_time: Optional relative time for the event
        :param event_time: Optional absolute time for the event
        :param event_time_comparator: Optional time comparator for the event
        :return: The ID of the newly created event
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        return are_simulation_instance.add_scenario_event(
            app,
            function,
            parameters,
            predecessor_event_ids,
            event_type,
            event_relative_time,
            event_time,
            event_time_comparator,
        )

    @strawberry.mutation
    @make_async
    def edit_scenario_event(
        self,
        session_id: str,
        app: str,
        function: str,
        parameters: str,
        event_id: str,
        event_type: EventType,
        predecessor_event_ids: list[str],
        event_relative_time: float | None = None,
        event_time: float | None = None,
        event_time_comparator: EventTimeComparator | None = None,
    ) -> str:
        """Edit an existing event in the scenario.

        :param session_id: The unique identifier of the simulation session
        :param app: The name of the app for the event
        :param function: The function name to execute
        :param parameters: The parameters for the function as a string
        :param event_id: The ID of the event to edit
        :param event_type: The type of event
        :param predecessor_event_ids: List of event IDs that must complete before this event
        :param event_relative_time: Optional relative time for the event
        :param event_time: Optional absolute time for the event
        :param event_time_comparator: Optional time comparator for the event
        :return: The ID of the edited event
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        return are_simulation_instance.edit_scenario_event(
            app,
            function,
            parameters,
            event_id,
            event_type,
            predecessor_event_ids,
            event_relative_time,
            event_time,
            event_time_comparator,
        )

    @strawberry.mutation
    @make_async
    def edit_scenario_duration(
        self,
        session_id: str,
        duration: float | None,
    ) -> float | None:
        """Edit the duration of the scenario.

        :param session_id: The unique identifier of the simulation session
        :param duration: The new duration for the scenario in seconds, or None to clear
        :return: The updated duration value
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.edit_scenario_duration(duration)
        return duration

    @strawberry.mutation
    @make_async
    def edit_time_increment(
        self,
        session_id: str,
        time_increment_in_seconds: int,
    ) -> int:
        """Edit the time increment for the scenario.

        :param session_id: The unique identifier of the simulation session
        :param time_increment_in_seconds: The new time increment value in seconds
        :return: The updated time increment value
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.edit_scenario_time_increment(time_increment_in_seconds)
        return time_increment_in_seconds

    @strawberry.mutation
    @make_async
    def delete_scenario_event(
        self,
        session_id: str,
        event_id: str,
    ) -> None:
        """Delete a specific event from the scenario.

        :param session_id: The unique identifier of the simulation session
        :param event_id: The ID of the event to delete
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.delete_scenario_event(event_id)

    @strawberry.mutation
    @make_async
    def delete_all_scenario_events(
        self,
        session_id: str,
    ) -> None:
        """Delete all events from the scenario.

        :param session_id: The unique identifier of the simulation session
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.delete_all_scenario_events()

    @strawberry.mutation
    @make_async
    def set_annotator_name(
        self,
        session_id: str,
        name: str | None,
    ) -> str | None:
        """Set the annotator name for a simulation session.

        :param session_id: The unique identifier of the simulation session
        :param name: The name of the annotator, or None to clear
        :return: The annotator name that was set
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.set_annotator_name(name)
        return name

    @strawberry.mutation
    @make_async
    def set_override_phone_number(
        self,
        session_id: str,
        override_phone_number: str | None,
    ) -> str | None:
        """Set an override phone number for the simulation session.

        :param session_id: The unique identifier of the simulation session
        :param override_phone_number: The phone number to override with, or None to clear
        :return: The override phone number that was set
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        are_simulation_instance.set_override_phone_number(override_phone_number)
        return override_phone_number

    @strawberry.mutation
    @make_async
    def init_connect_with_session_id(self, session_id: str) -> str:
        """Initialize a connection with a specific session ID.

        :param session_id: The unique identifier of the simulation session
        :return: A confirmation message indicating the Meta Agents Research Environments instance was created
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        Mutation.server.get_or_create_are_simulation(session_id)
        return "create new are_simulation instance"

    @strawberry.mutation
    @make_async
    def import_trace(
        self, trace_json: str, session_id: str, replay_logs: bool
    ) -> ScenarioForGraphQL | None:
        """Import a scenario from a trace JSON.

        :param trace_json: The JSON string containing the trace data
        :param session_id: The unique identifier of the simulation session
        :param replay_logs: Whether to replay the logs after importing
        :return: The imported scenario object for GraphQL, or None if import failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        success = are_simulation_instance.import_trace(trace_json, replay_logs)
        clear_graphql_cache(session_id)
        return (
            ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)
            if success
            else None
        )

    @strawberry.mutation
    @make_async
    def import_from_db(
        self, scenario_id: str, session_id: str
    ) -> ScenarioForGraphQL | None:
        """Import a scenario from the database.

        :param scenario_id: The unique identifier of the scenario to import
        :param session_id: The unique identifier of the simulation session
        :return: The imported scenario object for GraphQL, or None if import failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        success = are_simulation_instance.import_from_db(scenario_id)
        clear_graphql_cache(session_id)
        return (
            ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)
            if success
            else None
        )

    @strawberry.mutation
    @make_async
    def execute_app_tool(
        self, session_id: str, app_name: str, tool_name: str, kwargs: str
    ) -> ExecuteAppToolResultForGraphQL:
        """Execute a tool within an app.

        :param session_id: The unique identifier of the session
        :param app_name: The name of the app containing the tool
        :param tool_name: The name of the tool to execute
        :param kwargs: JSON string containing the parameters to pass to the tool
        :return: ExecuteAppToolResultForGraphQL containing the updated apps state and the tool's return value
        :raises ValueError: If the mutation server is not initialized, app is not found, or tool is not found
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")

        # Get the Meta Agents Research Environments instance from the session_id
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )

        # Parse the kwargs from JSON string
        tool_params = json.loads(kwargs)

        # Find the app in the Meta Agents Research Environments instance
        if are_simulation_instance.env is None:
            raise ValueError("Environment is not initialized.")

        app = are_simulation_instance.env.apps.get(app_name)
        if app is None:
            raise ValueError(
                f"App '{app_name}' not found, available apps: {are_simulation_instance.env.apps.keys()}."
            )

        found_tool = app.get_tool(tool_name)

        if found_tool is None:
            raise ValueError(f"Tool '{tool_name}' not found in app '{app_name}'.")

        # Execute the tool with the provided kwargs using the AppTool.__call__ method
        # and capture the return value
        return_value = found_tool(**tool_params)

        # Clear the GraphQL cache to ensure the client gets the updated state
        clear_graphql_cache(session_id)

        # Convert the return value to JSON string if it's not None
        return_value_str = None
        if return_value is not None:
            try:
                # Try to convert to JSON
                return_value_str = json.dumps(return_value)
            except (TypeError, ValueError):
                # If it's not JSON serializable, convert to string
                return_value_str = str(return_value)

        # Get the apps state
        apps_state = are_simulation_instance.env.get_apps_state()

        # Convert the apps state to JSON string
        apps_state_json = json.dumps(make_serializable(apps_state))

        # Return the updated apps state and the tool's return value
        return ExecuteAppToolResultForGraphQL(
            apps_state_json=apps_state_json, return_value=return_value_str
        )

    @strawberry.mutation
    @make_async
    def save_annotation(
        self,
        session_id: str,
        scenario_id: str,
        validation_decision: str | None,
        annotation_id: str | None,
        annotator_name: str | None,
        comment: str | None = None,
    ) -> bool:
        """Save an annotation for a scenario.

        :param session_id: The unique identifier of the simulation session
        :param scenario_id: The unique identifier of the scenario to annotate
        :param validation_decision: The validation decision for the annotation
        :param annotation_id: The unique identifier of the annotation, or None for new annotation
        :param annotator_name: The name of the annotator, or None if not specified
        :param comment: Optional comment for the annotation
        :return: True if the annotation was saved successfully, False otherwise
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        return are_simulation_instance.save_annotation(
            scenario_id, validation_decision, annotation_id, annotator_name, comment
        )

    @strawberry.mutation
    @make_async
    def import_from_huggingface(
        self,
        dataset_name: str,
        dataset_config: str,
        dataset_split: str,
        scenario_id: str,
        session_id: str,
    ) -> ScenarioForGraphQL | None:
        """Import a scenario from a Huggingface dataset.

        :param dataset_name: The name of the Huggingface dataset
        :param dataset_config: The config name of the Huggingface dataset
        :param dataset_split: The split name of the Huggingface dataset
        :param scenario_id: The unique identifier of the scenario to import
        :param session_id: The unique identifier of the simulation session
        :return: The imported scenario object for GraphQL, or None if import failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        success = are_simulation_instance.import_from_huggingface(
            dataset_name, dataset_config, dataset_split, scenario_id
        )
        if success:
            clear_graphql_cache(session_id)

        return (
            ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)
            if success
            else None
        )

    @strawberry.mutation
    @make_async
    def import_from_local_json_dataset(
        self, capability: str, filename: str, session_id: str, replay_logs: bool
    ) -> ScenarioForGraphQL | None:
        """Import a scenario from a local JSON dataset file.

        :param capability: The capability (subfolder) name
        :param filename: The JSON filename to import
        :param session_id: The unique identifier of the simulation session
        :param replay_logs: Whether to replay the logs after importing
        :return: The imported scenario object for GraphQL, or None if import failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        success = are_simulation_instance.import_from_local_json_dataset(
            capability, filename, replay_logs
        )
        clear_graphql_cache(session_id)
        return (
            ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)
            if success
            else None
        )

    @strawberry.mutation
    @make_async
    def edit_hint_content(
        self, event_id: str, hint_content: str, session_id: str
    ) -> ScenarioForGraphQL | None:
        """Edit the hint content for a specific scenario event.

        :param event_id: The unique identifier of the event to edit
        :param hint_content: The new hint content for the event
        :param session_id: The unique identifier of the simulation session
        :return: The updated scenario object for GraphQL, or None if operation failed
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        if are_simulation_instance.edit_scenario_event_hint_content(
            event_id, hint_content
        ):
            return ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)
        else:
            return None

    @strawberry.mutation
    @make_async
    def upload_file(
        self,
        session_id: str,
        filesystem_app_name: str,
        file_name: str,
        file_content: str,
        destination_path: str,
    ) -> bool:
        """Upload a file to the filesystem.

        :param session_id: The unique identifier of the session
        :param filesystem_app_name: The name of the filesystem app
        :param file_name: The name of the file to upload
        :param file_content: The base64-encoded content of the file
        :param destination_path: The destination path where the file should be saved
        :return: True if the upload was successful, False otherwise
        :raises ValueError: If the mutation server is not initialized
        """
        if Mutation.server is None:
            raise ValueError("Mutation.server is not initialized.")
        are_simulation_instance = Mutation.server.get_or_create_are_simulation(
            session_id
        )
        return are_simulation_instance.upload_file(
            filesystem_app_name, file_name, file_content, destination_path
        )
