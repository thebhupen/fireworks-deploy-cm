# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from collections import Counter
from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Failure:
    def __str__(self) -> str:
        return "Failure occurred."


@dataclass
class ToolCallCountsFailure(Failure):
    agent_counter: Counter
    agent_aui_count: int
    oracle_counter: Counter
    oracle_aui_count: int
    extra_send_message_to_user_allowed: int = 0

    def __str__(self) -> str:
        message = []
        diff = self.agent_counter - self.oracle_counter
        diff.update(self.oracle_counter - self.agent_counter)
        if diff:
            discrepancies = "\n".join(
                f"- Tool '{tool}': Agent count {self.agent_counter.get(tool, 0)}, Oracle count {self.oracle_counter.get(tool, 0)}"
                for tool in diff
            )
            message.append(
                f"Agent and oracle counters do not match for the following tools:\n{discrepancies}"
            )
        if self.oracle_aui_count > self.agent_aui_count:
            message.append(
                f"Oracle sent {self.oracle_aui_count - self.agent_aui_count} more message(s) than agent."
            )
        if (
            self.agent_aui_count
            > self.oracle_aui_count + self.extra_send_message_to_user_allowed
        ):
            message.append(
                f"Agent message to user count exceeds oracle AUI count by more than {self.extra_send_message_to_user_allowed}."
            )
        return "Failure: \n" + "\n".join(message)


class EventComparisonFailureType(Enum):
    CAUSALITY = "causality"
    ALREADY_MATCHED = "already matched"
    TOOL_JUDGE_REJECT = "tool judge reject"


@dataclass
class EventComparisonFailure(Failure):
    agent_tool_name: str
    agent_event_id: str
    oracle_tool_name: str
    oracle_event_id: str
    failure_type: EventComparisonFailureType

    def __str__(self) -> str:
        reason = f"{self.failure_type.value}"
        return f"Failure matching agent event (ID: {self.agent_event_id}) with oracle event (ID: {self.oracle_event_id}), reason: {reason}"


@dataclass
class OracleEventMatchingFailure(Failure):
    oracle_tool_name: str
    oracle_tool_args: dict[str, str]
    comparison_failures: list[EventComparisonFailure]

    def __str__(self) -> str:
        tool_arg_str = [f"-{k}: {v}" for k, v in self.oracle_tool_args.items()]
        tool_arg_str = [
            (x[:200] + ("..." if len(x) > 200 else "")) for x in tool_arg_str
        ]
        tool_arg_str = "\n".join(tool_arg_str)
        message = "Failure: Agent did not perform the following oracle tool call:"
        message += f"\ntool name: {self.oracle_tool_name}\ntool args:\n{tool_arg_str}\n"
        message += "\nList of matching attempts:\n"
        message += "\n".join(["-" + str(c) for c in self.comparison_failures])
        return message


@dataclass
class EnvOracleMatchingFailure(Failure):
    oracle_event_id: str

    def __str__(self) -> str:
        return f"Failure: Oracle env/user event {self.oracle_event_id} could not be matched. This is likely a bug !"


@dataclass
class Judgment:
    success: bool | None = False
    failure: str | Failure | None = None
    agent_event_id_to_oracle_event_id: dict[str, str] = field(default_factory=dict)
