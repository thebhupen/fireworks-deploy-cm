"""Files app state: a tree of the universe's real documents under <universe>/files.

ARE's SandboxLocalFileSystem restores each file node from `real_path`, resolved against the
state directory the app is created with, so the universe's files folder is that directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _node(path: Path, root: Path) -> dict[str, Any]:
    if path.is_dir():
        children = [_node(child, root) for child in sorted(path.iterdir()) if not child.name.startswith(".")]
        return {"name": path.name if path != root else "", "type": "directory", "real_path": None, "children": children}
    return {"name": path.name, "type": "file", "real_path": str(path.relative_to(root)), "children": []}


def files_root(universe_dir: Path) -> Path:
    return universe_dir / "files"


def build_files(universe_dir: Path) -> dict[str, Any]:
    root = files_root(universe_dir)
    if not root.is_dir():
        return {"files": {"name": "", "type": "directory", "real_path": None, "children": []}}
    return {"files": _node(root, root)}


def file_paths(universe_dir: Path) -> set[str]:
    """Paths as the agent sees them, e.g. /Documents/Health/report.txt."""
    root = files_root(universe_dir)
    return {"/" + str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}
