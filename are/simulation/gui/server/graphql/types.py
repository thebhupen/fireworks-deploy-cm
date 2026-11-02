# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import json
from dataclasses import field
from enum import Enum
from typing import Any

import strawberry

from are.simulation.apps.app import App
from are.simulation.scenarios.scenario import Scenario
from are.simulation.tool_utils import AppTool
from are.simulation.types import CapabilityTag, Hint
from are.simulation.utils import strip_app_name_prefix


@strawberry.type
class AnnotationForGraphQL:
    scenario_id: str
    annotator: str
    validation_decision: str | None = None
    created_at: str
    validated_at: str | None = None
    last_updated_at: str
    version: int
    vendor: str
    batch_id: str | None = None
    comment: str | None = None


@strawberry.type
class ServerInfoForGraphQL:
    server_id: str
    server_version: str


@strawberry.type
class BugReportForGraphQL:
    bug_report_id: int
    reporter: str
    created_at: str
    blob_data: str


@strawberry.enum
class AgentLogTypeForGraphQL(Enum):
    SYSTEM_PROMPT = "system_prompt"
    TASK = "task"
    LLM_OUTPUT_THOUGHT_ACTION = "llm_output_thought_action"
    LLM_INPUT = "llm_input"
    LOG = "log"
    RATIONALE = "rationale"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"
    STEP = "step"
    SUBAGENT = "subagent"
    FINAL_ANSWER = "final_answer"
    ERROR = "error"
    THOUGHT = "thought"
    PLAN = "plan"
    FACTS = "facts"
    REPLAN = "replan"
    REFACTS = "refacts"
    AGENT_STOP = "agent_stop"
    CODE_EXECUTION_RESULT = "code_execution_result"
    CODE_STATE_UPDATE = "code_state_update"
    END_TASK = "end_task"
    LLM_OUTPUT_PLAN = "llm_output_plan"
    LLM_OUTPUT_FACTS = "llm_output_facts"


@strawberry.type
class AttachmentForGraphQL:
    length: int
    mime: str
    url: str


@strawberry.type
class AgentLogForGraphQL:
    type: AgentLogTypeForGraphQL
    id: str
    timestamp: float | None = None
    group_id: str | None = None
    content: str | None = None
    agent_name: str | None = None
    start_id: str | None = None
    input: str | None = None
    output: str | None = None
    action_name: str | None = None
    app_name: str | None = None
    exception: str | None = None
    exception_stack_trace: str | None = None
    attachments: list[AttachmentForGraphQL] | None = None
    is_subagent: bool = False


@strawberry.type
class AppToolParamsForGraphQL:
    name: str
    arg_type: str
    description: str | None = None
    has_default_value: bool = False
    default_value: str | None = None
    example_value: str | None = None


@strawberry.type
class AppToolForGraphQL:
    name: str
    role: str
    params: list[AppToolParamsForGraphQL]
    description: str | None = None
    return_description: str | None = None
    write_operation: bool | None = None


@strawberry.type
class AppForGraphQL:
    app_name: str
    app_tools: list[AppToolForGraphQL]

    @classmethod
    def app_tools_from_app(cls, app: App) -> list[AppToolForGraphQL]:
        """
        Retrieves a list of application tools categorized by their roles.

        :return: A list of AppToolForGraphQL objects representing the tools available in the application.
        :rtype: list[AppToolForGraphQL]
        """

        def format_value(value: Any) -> str | None:
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            elif value is not None:
                return str(value)
            return None

        def get_tools(tools: list[AppTool], role: str) -> list[AppToolForGraphQL]:
            """
            Converts a list of AppTool objects into a list of AppToolForGraphQL objects with a specified role.

            :param tools: The list of AppTool objects to be converted.
            :type tools: list[AppTool]
            :param role: The role associated with the tools (e.g., "AGENT", "USER", "ENV").
            :type role: str
            :return: A list of AppToolForGraphQL objects with the specified role.
            :rtype: list[AppToolForGraphQL]
            """
            return [
                # pyright: ignore
                AppToolForGraphQL(
                    name=strip_app_name_prefix(tool.name, app.name)
                    or tool.func_name
                    or "",
                    description=tool.function_description,
                    return_description=tool.return_description,
                    role=role,
                    params=[
                        # pyright: ignore
                        AppToolParamsForGraphQL(
                            name=arg.name,
                            description=arg.description,
                            arg_type=str(arg.arg_type),
                            has_default_value=arg.has_default,
                            default_value=format_value(arg.default),
                            example_value=format_value(arg.example_value),
                        )
                        for arg in tool.args
                    ],
                    write_operation=tool.write_operation,
                )
                for tool in tools
            ]

        agent_tools = get_tools(app.get_tools(), "AGENT")
        user_tools = get_tools(app.get_user_tools(), "USER")
        env_tools = get_tools(app.get_env_tools(), "ENV")
        data_tools = get_tools(app.get_data_tools(), "DATA")

        return agent_tools + user_tools + env_tools + data_tools

    @classmethod
    def from_app(cls, app: App) -> "AppForGraphQL":
        return AppForGraphQL(
            app_name=app.name,
            app_tools=AppForGraphQL.app_tools_from_app(app),
        )


@strawberry.type
class ScenarioGUIConfigForGraphQL:
    show_timestamps: bool


def _create_default_scenario_gui_config() -> ScenarioGUIConfigForGraphQL:
    return ScenarioGUIConfigForGraphQL(show_timestamps=False)


@strawberry.type
class ScenarioForGraphQL:
    scenario_id: str
    start_time: float | None
    duration: float | None
    time_increment_in_seconds: int | None
    apps: list[AppForGraphQL]
    status: str
    comment: str | None
    annotation_id: str | None
    hints: list[Hint] | None
    tags: list[CapabilityTag] | None
    gui_config: ScenarioGUIConfigForGraphQL = field(
        default_factory=_create_default_scenario_gui_config
    )

    @classmethod
    def from_scenario(cls, scenario: Scenario) -> "ScenarioForGraphQL":
        apps = scenario.apps if scenario.apps else []

        return cls(
            scenario_id=scenario.scenario_id,
            start_time=scenario.start_time,
            duration=scenario.duration,
            time_increment_in_seconds=scenario.time_increment_in_seconds,
            apps=[AppForGraphQL.from_app(app) for app in apps],
            status=scenario.status.value,
            comment=scenario.comment,
            annotation_id=scenario.annotation_id,
            hints=scenario.hints,
            tags=list(scenario.tags) if scenario.tags else None,
            gui_config=(
                ScenarioGUIConfigForGraphQL(
                    show_timestamps=scenario.gui_config.show_timestamps,
                )
                if scenario.gui_config
                else _create_default_scenario_gui_config()
            ),
        )


@strawberry.type
class ExecuteAppToolResultForGraphQL:
    """
    Result of executing an app tool, containing both the updated apps state and the tool's return value.
    The return_value is a json dump of the tool return value if it's json serializable, otherwise it's its repr.
    """

    apps_state_json: str
    return_value: str | None = None
