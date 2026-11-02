# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from dataclasses import dataclass, field

from are.simulation.validation.base import BaseJudgeState


@dataclass
class GraphPerEventJudgeState(BaseJudgeState):
    # Matched events
    agent_idx_to_oracle_id: dict[int, str] = field(default_factory=dict)
    oracle_id_to_agent_idx: dict[str, int] = field(default_factory=dict)
    agent_id_to_oracle_id: dict[str, str] = field(default_factory=dict)

    def add_match(self, agent_idx: int, oracle_id: str):
        self.agent_idx_to_oracle_id[agent_idx] = oracle_id
        self.oracle_id_to_agent_idx[oracle_id] = agent_idx
        self.agent_id_to_oracle_id[self.agent_events[agent_idx].event_id] = oracle_id


@dataclass
class InContextJudgeState(BaseJudgeState):
    @property
    def agent_id_to_oracle_id(self) -> dict[str, str]:
        """
        There is no agent event to oracle event one to one matching in this judge
        """
        return {}

    @property
    def user_name(self) -> str:
        if self.user_details is None:
            return ""
        return f"{self.user_details.first_name} {self.user_details.last_name}"
