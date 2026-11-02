# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from enum import Enum
from typing import Union

from pydantic import BaseModel

from are.simulation.agents.multimodal import Attachment


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALL = "tool-call"
    TOOL_RESPONSE = "tool-response"

    @classmethod
    def roles(cls):
        return [r.value for r in cls]


# Copied from `are/core/base_agent/types.py``
class MMObservation(BaseModel):
    content: str
    attachments: list[Attachment]

    def verbose(self) -> str:
        attachment_info = "\n".join(
            [
                f"Attachment - MIME: {attachment.mime}, SIZE: {len(attachment.base64_data)}"
                for attachment in self.attachments
            ]
        )
        return f"Content: {self.content}\nAttachments:\n{attachment_info}"


Observation = Union[str, MMObservation]
