# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


class PromptTooLongException(Exception):
    """
    Custom exception for specific application errors.
    """

    pass


class EmptyResponseException(Exception):
    """
    Custom exception for specific application errors.
    """

    pass
