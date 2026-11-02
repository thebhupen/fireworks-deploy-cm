# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from typing import Any

from pydantic import BaseModel

from are.simulation.scenarios.config import ScenarioRunnerConfig
from are.simulation.types import ExecutionMetadata, PlaceholderMetadata

TRACE_V1_VERSION: str = "are_simulation_v1"


class ExportedEventMetadata(BaseModel):
    return_value: str | None = None
    return_value_type: str | None = None
    exception: str | None = None
    exception_stack_trace: str | None = None


class ExportedActionArg(BaseModel):
    name: str
    value: str | None = None
    value_type: str | None = None


class ExportedAction(BaseModel):
    action_id: str
    app: str | None = None
    function: str | None = None
    operation_type: str | None = None
    args: list[ExportedActionArg] | None = None


class ExportedEvent(BaseModel):
    class_name: str
    event_type: str
    event_time: float | None
    event_id: str
    dependencies: list[str]
    event_relative_time: float | None
    action: ExportedAction | None = None


class ExportedOracleEvent(ExportedEvent):
    event_time_comparator: str | None = None


class ExportedCompletedEvent(BaseModel):
    class_name: str
    event_type: str
    event_time: float
    event_id: str
    dependencies: list[str]
    event_relative_time: float | None
    action: ExportedAction | None = None
    metadata: ExportedEventMetadata | None = None


class ExportedHint(BaseModel):
    hint_type: str
    content: str
    associated_event_id: str


class ExportedHuggingFaceMetadata(BaseModel):
    dataset: str
    split: str
    revision: str | None = None


class ExportedTraceDefinitionMetadata(BaseModel):
    scenario_id: str
    seed: int | None = None
    duration: float | None = None
    time_increment_in_seconds: int | None = None
    start_time: float | None = None
    run_number: int | None = None  # Run number for multiple runs of the same scenario
    hints: list[ExportedHint] = []
    config: str | None = None
    has_a2a_augmentation: bool = False
    has_tool_augmentation: bool = False
    has_env_events_augmentation: bool = False
    has_exception: bool = False
    exception_type: str | None = None
    exception_message: str | None = None
    tags: list[str] | None = None
    hf_metadata: ExportedHuggingFaceMetadata | None = None


class ExportedTraceSimulationMetadata(BaseModel):
    agent_id: str | None = None
    model_id: str | None = None


class ExportedTraceAnnotationMetadata(BaseModel):
    annotation_id: str | None = None
    annotator: str | None = None
    validation_decision: str | None = None
    comment: str | None = None
    date: float = 0.0


class ExportedTraceLLMSafetyRedTeamingMetadata(BaseModel):
    """
    Metadata specific to LLM Safety Red Teaming.
    """

    group_id: str | None = None
    category: str = ""
    is_violating: bool = False
    has_ars_violation: bool = False
    has_crs_violation: bool = False
    is_false_refusal: bool = False


class ExportedTraceAgentSecurityRedTeamingMetadata(BaseModel):
    """
    Metadata specific to Agent Security Red Teaming.
    """

    group_id: str | None = None
    attack_category: str | None = None
    references: str | None = None
    additional_notes: str | None = None


class ExportedPlaceholderMetadata(BaseModel):
    """
    Metadata for a placeholder.
    `parent_tool_name`: Name of the tool parent event.
    `parent_turn_idx`: Index of the turn the parent event belongs to.
    `parent_event_id`: ID of the parent event.
    `placeholder_turn_idx`: Index of the turn the placeholder belongs to.
    `placeholder_event_id`: ID of the placeholder event (where the placeholder is).
    """

    parent_tool_name: str
    parent_turn_idx: int
    parent_event_id: str
    placeholder_turn_idx: int
    placeholder_event_id: str

    @classmethod
    def from_metadata(
        cls, metadata: PlaceholderMetadata
    ) -> "ExportedPlaceholderMetadata":
        """
        Convert a PlaceholderMetadata instance to an ExportedPlaceholderMetadata instance.

        :params metadata: The PlaceholderMetadata instance to convert
        :returns: An ExportedPlaceholderMetadata instance
        """
        return cls(
            parent_tool_name=metadata.parent_tool_name,
            parent_turn_idx=metadata.parent_turn_idx,
            parent_event_id=metadata.parent_event_id,
            placeholder_turn_idx=metadata.placeholder_turn_idx,
            placeholder_event_id=metadata.placeholder_event_id,
        )

    def to_metadata(self) -> PlaceholderMetadata:
        """
        Convert this ExportedPlaceholderMetadata instance to a PlaceholderMetadata instance.

        :returns: A PlaceholderMetadata instance
        """
        return PlaceholderMetadata(
            parent_tool_name=self.parent_tool_name,
            parent_turn_idx=self.parent_turn_idx,
            parent_event_id=self.parent_event_id,
            placeholder_turn_idx=self.placeholder_turn_idx,
            placeholder_event_id=self.placeholder_event_id,
        )


class ExportedExecutionMetadata(BaseModel):
    """
    Data structure for exporting execution data.
    """

    has_placeholder_conflicts: bool
    placeholders: list[ExportedPlaceholderMetadata]

    @classmethod
    def from_metadata(cls, metadata: ExecutionMetadata) -> "ExportedExecutionMetadata":
        """
        Convert an ExecutionMetadata instance to an ExportedExecutionMetadata instance.

        :params metadata: The ExecutionMetadata instance to convert
        :returns: An ExportedExecutionMetadata instance
        """
        return cls(
            has_placeholder_conflicts=metadata.has_placeholder_conflicts,
            placeholders=[
                ExportedPlaceholderMetadata.from_metadata(placeholder)
                for placeholder in metadata.placeholders
            ],
        )

    def to_metadata(self) -> ExecutionMetadata:
        """
        Convert this ExportedExecutionMetadata instance to an ExecutionMetadata instance.

        :returns: An ExecutionMetadata instance
        """
        return ExecutionMetadata(
            has_placeholder_conflicts=self.has_placeholder_conflicts,
            placeholders=[
                placeholder.to_metadata() for placeholder in self.placeholders
            ],
        )


class ExportedTraceMetadata(BaseModel):
    definition: ExportedTraceDefinitionMetadata
    simulation: ExportedTraceSimulationMetadata | None = None
    annotation: ExportedTraceAnnotationMetadata | None = None
    execution: ExportedExecutionMetadata | None = None
    runner_config: ScenarioRunnerConfig | None = None


class ExportedApp(BaseModel):
    name: str
    class_name: str | None = None
    app_state: dict[str, Any] | None = None


class ExportedTraceBase(BaseModel):
    world_logs: list[str] = []
    apps: list[ExportedApp] = []
    events: list[ExportedEvent | ExportedOracleEvent] = []
    completed_events: list[ExportedCompletedEvent] = []
    version: str
    context: str | None = None
    augmentation: dict | None = None


class ExportedTrace(ExportedTraceBase):
    metadata: ExportedTraceMetadata
