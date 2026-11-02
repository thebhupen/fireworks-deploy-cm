# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import ast
import os

import pytest

from are.simulation.config import ARE_SIMULATION_ROOT


class OracleMethodVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []
        self.current_file = None

    def set_current_file(self, filename):
        self.current_file = filename

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "oracle":
            current = node.func.value
            chain = []

            while isinstance(current, ast.Call) and isinstance(
                current.func, ast.Attribute
            ):
                chain.append(current.func.attr)
                current = current.func.value

            for method in chain:
                if method in ["depends_on", "followed_by"]:
                    line_number = getattr(node, "lineno", 0)
                    violation = {
                        "file": self.current_file,
                        "line": line_number,
                        "message": f"Line {line_number}: '.{method}()' called before '.oracle()' in chain",
                    }
                    self.violations.append(violation)
                    break

        self.generic_visit(node)


def find_python_files(directory):
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def analyze_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            content = file.read()
            tree = ast.parse(content)
            visitor = OracleMethodVisitor()
            visitor.set_current_file(file_path)
            visitor.visit(tree)
            return visitor.violations
        except SyntaxError:
            return []


def test_oracle_method_ordering():
    scenarios_dir = ARE_SIMULATION_ROOT / "simulation" / "scenarios"
    python_files = find_python_files(scenarios_dir)

    all_violations = []
    for file_path in python_files:
        violations = analyze_file(file_path)
        all_violations.extend(violations)

    if all_violations:
        violation_messages = [
            f"{v['file']}:{v['line']} - {v['message']}" for v in all_violations
        ]
        pytest.fail(
            "Found incorrect oracle method ordering:\n"
            + "\n".join(violation_messages)
            + "\n\nThe correct pattern is: .oracle().depends_on() or .oracle().followed_by()"
        )
