# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import base64
import logging
from io import BytesIO

from PIL import Image
from pydantic import BaseModel, field_serializer, field_validator

logger: logging.Logger = logging.getLogger(__name__)


class Attachment(BaseModel):
    base64_data: bytes
    mime: str
    name: str | None = None

    def __init__(self, **kwargs) -> None:
        # Validate mime
        if (
            "mime" not in kwargs
            or kwargs["mime"] is None
            or (isinstance(kwargs["mime"], str) and kwargs["mime"] == "")
        ):
            raise ValueError("mime cannot be null or empty")

        # Validate base64_data
        if (
            "base64_data" not in kwargs
            or kwargs["base64_data"] is None
            or (
                isinstance(kwargs["base64_data"], bytes)
                and len(kwargs["base64_data"]) == 0
            )
        ):
            raise ValueError("base64_data cannot be null or empty")

        super().__init__(**kwargs)

    def __hash__(self) -> int:
        """
        Generate a hash for the Attachment object based on its content.
        This allows Attachment objects to be used in sets and as dictionary keys.
        """
        return hash((self.base64_data, self.mime, self.name))

    @field_validator("base64_data", mode="before")
    @classmethod
    def encode_base64_data(cls, value):
        """
        Convert base64_data string to bytes for proper handling.
        Only accepts string input - raises ValueError for other types.
        """
        if isinstance(value, str):
            return value.encode("utf-8")
        elif isinstance(value, bytes):
            return value
        else:
            raise ValueError(
                f"base64_data must be a string or bytes, got {type(value).__name__}"
            )

    @field_serializer("base64_data")
    def serialize_base64_data(self, value: bytes) -> str:
        """
        Serialize base64_data bytes to string for JSON serialization.
        This ensures json.dumps() works properly on Attachment objects.
        """
        return value.decode("utf-8")

    def to_openai_json(self):
        if not self.mime.startswith("image/"):
            raise ValueError(f"Unsupported mime type: {self.mime}")

        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{self.mime};base64,{self.base64_data.decode('utf-8')}"
            },
        }


def attachments_to_pil(attachments: list[Attachment]) -> list[Image.Image]:
    images = []
    for attachment in attachments:
        base64_image = attachment.base64_data.decode("utf-8")
        image_bytes = base64.b64decode(base64_image)
        # Create a BytesIO object from the bytes
        image_buffer = BytesIO(image_bytes)
        # Open the image using PIL
        images.append(Image.open(image_buffer))
    return images


def pil_to_attachments(images: list[Image.Image]) -> list[Attachment]:
    attachments = []
    for image in images:
        if image is None:
            continue
        buffered = BytesIO()
        if image.mode == "RGBA":
            image.save(buffered, format="PNG")
            mime_type = "image/png"
        else:
            image.convert("RGB").save(buffered, format="JPEG", quality=97)
            mime_type = "image/jpeg"
        image_base64 = base64.b64encode(buffered.getvalue())
        attachments.append(
            Attachment(
                base64_data=image_base64,
                mime=mime_type,
            )
        )
    return attachments
