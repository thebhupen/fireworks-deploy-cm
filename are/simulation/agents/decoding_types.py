# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from typing import Any, Literal

from pydantic import BaseModel


class DecodingSchema(BaseModel):
    type: Literal["json"] | Literal["regex"]
    decoding_schema: Any
