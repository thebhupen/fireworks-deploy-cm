# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import os

import strawberry
from strawberry.scalars import JSON

from are.simulation.gui.server.graphql.common import make_async
from are.simulation.gui.server.graphql.types import (
    AnnotationForGraphQL,
    BugReportForGraphQL,
    ScenarioForGraphQL,
    ServerInfoForGraphQL,
)
from are.simulation.gui.server.scenarios import GUI_SCENARIOS
from are.simulation.types import CapabilityTag


@strawberry.type
class Query:
    server = None  # : ARESimulationServer | None - Can't type this because of circular dependency

    @strawberry.field
    @make_async
    def all_scenarios(self) -> list[str]:
        return [str(k) for k in GUI_SCENARIOS.keys()]

    @strawberry.field
    @make_async
    def active_scenario(self, session_id: str) -> ScenarioForGraphQL | None:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return ScenarioForGraphQL.from_scenario(are_simulation_instance.scenario)

    @strawberry.field
    @make_async
    def all_agents(self) -> list[str]:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        return Query.server.get_all_agents()

    @strawberry.field
    @make_async
    def agent_name(self, session_id: str) -> str | None:  # type: ignore
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.agent_name

    @strawberry.field
    @make_async
    def agent_config(self, session_id: str) -> JSON | None:  # type: ignore
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.get_agent_config_with_schema()

    @strawberry.field
    @make_async
    def report_bug(
        self,
        session_id: str,
        scenario_id: str | None,
        reporter: str,
        context: str | None,
    ) -> str | None:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.report_bug(scenario_id, reporter, context)

    @strawberry.field
    @make_async
    def export_trace_data(
        self,
        session_id: str,
        scenario_id: str,
        validation_decision: str | None,
        annotation_id: str | None,
        annotator_name: str | None,
        comment: str | None = None,
        tags: list[CapabilityTag] | None = None,
    ) -> str | None:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.export_trace(
            scenario_id,
            validation_decision,
            annotation_id,
            annotator_name,
            comment,
            tags,
        )

    @strawberry.field
    @make_async
    def export_annotated_trace_data(
        self,
        session_id: str,
        scenario_id: str,
        category: str | None = None,
        is_violating: bool | None = None,
        has_ars_violation: bool | None = None,
        has_crs_violation: bool | None = None,
        is_false_refusal: bool | None = None,
        annotation_id: str | None = None,
        annotator_name: str | None = None,
        group_id: str | None = None,
        attack_category: str | None = None,
        references: str | None = None,
        additional_notes: str | None = None,
    ) -> str | None:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.export_annotated_trace(
            scenario_id,
            category,
            is_violating,
            has_ars_violation,
            has_crs_violation,
            is_false_refusal,
            annotation_id,
            annotator_name,
            group_id,
            attack_category,
            references,
            additional_notes,
        )

    @strawberry.field
    @make_async
    def get_file_content(
        self, session_id: str, filesystem_app_name: str, file_path: str
    ) -> str | None:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.get_file_content(filesystem_app_name, file_path)

    @strawberry.field
    @make_async
    def download_file(
        self, session_id: str, filesystem_app_name: str, file_path: str
    ) -> str | None:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.download_file(filesystem_app_name, file_path)

    @strawberry.field
    @make_async
    def default_ui_view(self) -> str | None:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        return Query.server.get_default_ui_view()

    @strawberry.field
    @make_async
    def get_annotations_from_db(self, session_id: str) -> list[AnnotationForGraphQL]:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.get_annotations_from_db()

    @strawberry.field
    @make_async
    def get_bug_reports_from_db(
        self,
        session_id: str,
        with_blob: bool = False,
        where_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[BugReportForGraphQL]:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        all = are_simulation_instance.get_bug_reports_from_db(
            with_blob=with_blob, where_id=where_id, limit=limit, offset=offset
        )
        return all

    @strawberry.field
    @make_async
    def server_info(self) -> ServerInfoForGraphQL:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        return ServerInfoForGraphQL(
            server_id=Query.server.server_id,
            server_version=Query.server.server_version,
        )

    @strawberry.field
    @make_async
    def get_huggingface_dataset_configs(self, dataset_name: str) -> list[str] | None:
        """
        Get the available configs for a Huggingface dataset.

        Args:
            dataset_name: The name of the Huggingface dataset

        Returns:
            A list of available configs
        """
        from are.simulation.utils.huggingface import get_huggingface_dataset_configs

        return get_huggingface_dataset_configs(dataset_name)

    @strawberry.field
    @make_async
    def get_huggingface_dataset_splits(
        self, dataset_name: str, dataset_config: str
    ) -> list[str] | None:
        """
        Get the available splits for a Huggingface dataset.

        Args:
            dataset_name: The name of the Huggingface dataset
            dataset_config: The config name of the Huggingface dataset

        Returns:
            A list of available splits
        """
        from are.simulation.utils.huggingface import get_huggingface_dataset_splits

        return get_huggingface_dataset_splits(dataset_name, dataset_config)

    @strawberry.field
    @make_async
    def get_huggingface_scenarios(
        self, dataset_name: str, dataset_config: str, dataset_split: str
    ) -> list[str] | None:
        """
        List available scenarios in a Huggingface dataset.

        Args:
            dataset_name: The name of the Huggingface dataset
            dataset_config: The config name of the Huggingface dataset
            dataset_split: The split of the Huggingface dataset

        Returns:
            A list of scenario IDs
        """
        from are.simulation.utils.huggingface import list_huggingface_scenarios

        return list_huggingface_scenarios(dataset_name, dataset_config, dataset_split)

    @strawberry.field
    @make_async
    def save_annotated_trace_to_db(
        self,
        session_id: str,
        scenario_id: str,
        category: str | None = None,
        is_violating: bool | None = None,
        has_ars_violation: bool | None = None,
        has_crs_violation: bool | None = None,
        is_false_refusal: bool | None = None,
        annotation_id: str | None = None,
        annotator_name: str | None = None,
        group_id: str | None = None,
        attack_category: str | None = None,
        references: str | None = None,
        additional_notes: str | None = None,
    ) -> str | None:
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.save_annotated_trace_to_db(
            scenario_id,
            category,
            is_violating,
            has_ars_violation,
            has_crs_violation,
            is_false_refusal,
            annotation_id,
            annotator_name,
            group_id,
            attack_category,
            references,
            additional_notes,
        )

    @strawberry.field
    @make_async
    def get_interactive_scenarios_tree(self) -> JSON | None:  # type: ignore
        """
        Get the interactive scenarios tree from a JSON file if INTERACTIVE_SCENARIOS_TREE environment variable is set.

        Returns:
            The interactive scenarios tree as JSON, or None if not configured
        """
        import json
        import os

        tree_file_path = os.environ.get("INTERACTIVE_SCENARIOS_TREE")
        if not tree_file_path:
            return None

        try:
            with open(tree_file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
            # Log the error but don't raise it - just return None to fall back to hardcoded scenarios
            print(
                f"Warning: Could not load interactive scenarios tree from {tree_file_path}: {e}"
            )
            return None

    @strawberry.field
    @make_async
    def get_local_json_dataset_capabilities(self, session_id: str) -> list[str]:
        """
        Get the list of capabilities (subfolders) in the local JSON dataset directory.

        Args:
            session_id: The unique identifier of the simulation session

        Returns:
            A list of capability names (subfolder names)
        """
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.get_local_json_dataset_capabilities()

    @strawberry.field
    @make_async
    def get_local_json_dataset_files(
        self, session_id: str, capability: str
    ) -> list[str]:
        """
        Get the list of JSON files in a specific capability folder.

        Args:
            session_id: The unique identifier of the simulation session
            capability: The capability (subfolder) name

        Returns:
            A list of JSON filenames in the capability folder
        """
        if Query.server is None:
            raise ValueError("Query.server is not initialized.")
        are_simulation_instance = Query.server.get_or_create_are_simulation(session_id)
        return are_simulation_instance.get_local_json_dataset_files(capability)

    @strawberry.field
    @make_async
    def get_default_scenario_id(self) -> str | None:
        """
        Get the default scenario ID from environment variable or return default.

        Returns:
            The default scenario ID from DEFAULT_SCENARIO_ID environment variable,
            or a constant variable if not set
        """
        return os.environ.get("DEFAULT_SCENARIO_ID")
