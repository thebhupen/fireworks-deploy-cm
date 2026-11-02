# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from dataclasses import dataclass
from typing import Any

from are.simulation.agents.llm.types import MMObservation


@dataclass
class AgentExecutionResult:
    output: str | MMObservation | None = None
    metadata: dict[str, Any] | None = None
