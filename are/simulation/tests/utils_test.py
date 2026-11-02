# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


from are.simulation.utils import strip_app_name_prefix


def test_strip_app_name_prefix():
    # Case 1: Tool name with a prefix matching the app name
    assert strip_app_name_prefix("app1__tool1", "app1") == "tool1"

    # Case 2: Tool name with a prefix that doesn't match the app name
    assert strip_app_name_prefix("app2__tool1", "app1") == "app2__tool1"

    # Case 3: Tool name without a prefix (no double underscore)
    assert strip_app_name_prefix("tool1", "app1") == "tool1"

    # Case 4: Tool name without a prefix (no double underscore)
    assert strip_app_name_prefix("app3__tool__1", "app3") == "tool__1"

    # Additional case: Empty strings
    assert strip_app_name_prefix("", "app1") == ""
    assert strip_app_name_prefix("app1__", "app1") == ""
