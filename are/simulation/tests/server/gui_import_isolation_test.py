# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.


import ast
import os
from pathlib import Path

import pytest

from are.simulation.config import ARE_SIMULATION_ROOT


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to collect import statements from Python files."""

    def __init__(self):
        self.imports: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        """Visit regular import statements (import module)."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statements (from module import name)."""
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)


def get_python_files_outside_gui(are_simulation_root: Path) -> list[Path]:
    """Get all Python files in are_simulation directory excluding those in are_simulation/gui and are_simulation/tests."""
    python_files = []
    gui_path = are_simulation_root / "gui"
    tests_path = are_simulation_root / "tests"

    for root, dirs, files in os.walk(are_simulation_root):
        root_path = Path(root)

        # Skip if we're inside the gui or tests directory
        if (
            gui_path in root_path.parents
            or root_path == gui_path
            or tests_path in root_path.parents
            or root_path == tests_path
        ):
            continue

        # Skip __pycache__ directories
        if "__pycache__" in root_path.parts:
            continue

        for file in files:
            if file.endswith(".py"):
                python_files.append(root_path / file)

    return python_files


def get_imports_from_file(file_path: Path) -> set[str]:
    """Extract all import statements from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        visitor = ImportVisitor()
        visitor.visit(tree)
        return visitor.imports
    except (SyntaxError, UnicodeDecodeError, OSError):
        # Skip files that can't be parsed or read
        return set()


def test_no_gui_imports_outside_gui():
    """Test that no Python file outside of are.simulation/gui imports modules from are.simulation.gui namespace."""
    # Get the are.simulation directory path
    are_simulation_dir = ARE_SIMULATION_ROOT / "simulation"

    # Get all Python files outside the gui and tests directories
    python_files = get_python_files_outside_gui(are_simulation_dir)

    # Track violations for better error reporting
    violations = []

    for file_path in python_files:
        imports = get_imports_from_file(file_path)

        # Check for any imports that start with 'are.simulation.gui'
        gui_imports = [imp for imp in imports if imp.startswith("are.simulation.gui")]

        if gui_imports:
            relative_path = file_path.relative_to(are_simulation_dir)
            violations.append({"file": str(relative_path), "imports": gui_imports})

    # Assert no violations found
    if violations:
        violation_details = []
        for violation in violations:
            imports_str = ", ".join(violation["imports"])
            violation_details.append(f"  {violation['file']}: {imports_str}")

        error_message = (
            f"Found {len(violations)} file(s) outside are_simulation/gui and are_simulation/tests importing from are.simulation.gui namespace:\n"
            + "\n".join(violation_details)
        )
        pytest.fail(error_message)
