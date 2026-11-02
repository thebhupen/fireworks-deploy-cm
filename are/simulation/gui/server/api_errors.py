# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


class APIScenarioNotFoundError(Exception):
    code = 400
    description = "scenario_not_found"
