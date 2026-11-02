# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from abc import ABC, abstractmethod
from functools import partial
from typing import Any

from are.simulation.scenarios.utils.scenario_expander import ENV_EVENT_EXPANSION_TAG
from are.simulation.tool_utils import OperationType
from are.simulation.types import Action, CompletedEvent, EventType


def resolve_arg_placeholders(
    event: CompletedEvent,
    target_events: list[CompletedEvent],
    event_id_to_target_event_idx: dict[str, int],
) -> CompletedEvent:
    """
    Resolve arg placeholders in the event.
    If an event has an arg that is a placeholder for a past event, we replace it with the return value of that event.
    """
    if event.action is None or event.action.args is None:  # type: ignore
        return event

    for arg_name, arg_value in event.action.args.items():  # type: ignore
        for past_event_id in event_id_to_target_event_idx:
            if arg_value == f"{{{{{past_event_id}}}}}":
                event.action.resolved_args[arg_name] = target_events[  # type: ignore
                    event_id_to_target_event_idx[past_event_id]
                ].metadata.return_value
                break
    return event


class EventFilter(ABC):
    @abstractmethod
    def filter(self, event: CompletedEvent) -> bool:
        pass

    def preprocess_event(self, event: CompletedEvent) -> CompletedEvent:
        # Remove get cotations
        if (
            event.event_type == EventType.AGENT
            and event.action
            and event.action.function_name == "get_quotation"
            and event.action.class_name == "CabApp"
        ):
            event.action.operation_type = OperationType.READ  # type: ignore
        # Remove add email
        if (
            event.event_type == EventType.AGENT
            and event.action
            and event.action.function_name == "add_email"
            and event.action.class_name in ["EmailClientApp", "EmailClientV2"]
        ):
            event.event_type = EventType.ENV  # type: ignore
        # Replace makedirs with mkdir
        if (
            event.event_type == EventType.AGENT
            and event.action
            and event.action.function_name == "makedirs"
            and event.action.class_name == "SandboxLocalFileSystem"
        ):
            # Modify the function name to achieve the desired tool name "SandboxLocalFileSystem__mkdir"
            event._tool_name = "SandboxLocalFileSystem__mkdir"

        return event

    def __call__(self, event: CompletedEvent) -> bool:
        # Preprocess some events
        event = self.preprocess_event(event)
        # Main filter events
        return self.filter(event)


class AgentEventFilter(EventFilter):
    """
    Filter that keep all agent events that are not failed and are write action.
    """

    def __init__(self) -> None:
        super().__init__()

    def filter(self, event: CompletedEvent) -> bool:
        return (
            event.event_type == EventType.AGENT
            and event.action is not None
            and event.action.operation_type == OperationType.WRITE  # type: ignore
            and not event.failed()
        )


class EnvAgentEventFilter(EventFilter):
    """
    Filter that keeps all env or user events that are not failed,
    and all agent events that are not failed and are write action.
    """

    def __init__(self) -> None:
        super().__init__()
        self.agent_event_filer = AgentEventFilter()

    def filter(self, event: CompletedEvent) -> bool:
        if (
            event.event_type in [EventType.ENV, EventType.USER]
            and ENV_EVENT_EXPANSION_TAG not in event.event_id
        ):
            return not event.failed()
        return self.agent_event_filer(event)


class EventDescription(ABC):
    @abstractmethod
    def describe_event(self, event: CompletedEvent) -> Any:
        pass

    def __call__(self, event: CompletedEvent, **kwargs) -> Any:
        return self.describe_event(event, **kwargs)


def parameter_descr(action: Action, selected_args: list[str] | None = None) -> str:
    if selected_args is None:
        selected_args = list(action.args.keys())
    param_dict = {}
    action_args = action.resolved_args if action.resolved_args else action.args
    for k, v in action_args.items():
        if k != "self" and k in selected_args:  # type: ignore
            param_dict[k] = str(v)
    return_string = "\n"
    for k, v in param_dict.items():
        return_string += f"{k}: {v} \n"
    return return_string.strip()


class BulletEventDescription(EventDescription):
    def __init__(
        self,
        tool_name: str,
        action_selected_args: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.tool_name = tool_name
        self.parameter_descr = partial(
            parameter_descr, selected_args=action_selected_args
        )

    def describe_event(self, event: CompletedEvent, **kwargs) -> str:
        desc = f"Tool name: {self.tool_name}"
        desc += f"\nTool call time: {event.event_time}"
        desc += "\nArguments:\n"
        desc += self.parameter_descr(action=event.action)  # type: ignore
        return desc


class BulletActionDescription(EventDescription):
    def __init__(
        self,
        action_selected_args: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.action_selected_args = action_selected_args

    def describe_event(self, event: CompletedEvent, **kwargs) -> str:
        action_selected_args = kwargs.get(
            "action_selected_args", self.action_selected_args
        )
        return parameter_descr(event.action, action_selected_args)  # type: ignore
