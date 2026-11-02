# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import ast
import os

import pytest


def find_python_files(directory):
    """Recursively find all Python files in the given directory."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def check_datetime_fromtimestamp_with_utc(file_path):
    """Check if datetime.fromtimestamp calls in a file have tz=timezone.utc."""
    exclusion_list = [
        "apps/experimental/tree_app.py",
    ]

    relative_file_path = os.path.relpath(file_path, start=root_dir)
    if relative_file_path in exclusion_list:
        return True, None

    with open(file_path, "r") as file:
        try:
            tree = ast.parse(file.read(), filename=file_path)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in file {file_path}: {e}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "fromtimestamp"
            ):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "datetime"
                ):
                    tz_arg_present = any(
                        kw.arg == "tz"
                        and isinstance(kw.value, ast.Attribute)
                        and kw.value.attr == "utc"
                        for kw in node.keywords
                    )
                    if not tz_arg_present:
                        return False, node.lineno
    return True, None


test_file_path = os.path.abspath(__file__)
test_dir = os.path.dirname(test_file_path)
root_dir = os.path.join(test_dir, "..")


@pytest.mark.parametrize("file_path", find_python_files(root_dir))
def test_datetime_fromtimestamp_calls(file_path):
    """Test all Python files for datetime.fromtimestamp calls with tz=timezone.utc."""
    result, lineno = check_datetime_fromtimestamp_with_utc(file_path)
    assert result, f"Missing tz=timezone.utc in {file_path} at line {lineno}"
