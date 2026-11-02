# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from os import getenv

DEFAULT_MODELS: list[str] = []

# All models names which are selectable in Meta Agents Research Environments settings. Can be configured
# using the `ALL_MODELS` environment variable, providing a list of
# comma-separated model names.
ALL_MODELS: list[str] = [
    model.strip() for model in getenv("ALL_MODELS", "").split(",") if model.strip()
] or DEFAULT_MODELS
