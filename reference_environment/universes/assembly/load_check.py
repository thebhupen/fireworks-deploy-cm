"""Load an exported universe with ARE's own importer, the way a real run does, and check it.

Run as a separate process with DEMO_FS_PATH pointing at the export's files/ folder (ARE reads it
at import time):

    DEMO_FS_PATH=<export>/files python -m reference_environment.universes.assembly.load_check <export>

Prints a JSON report and exits non-zero if any check fails.
"""

from __future__ import annotations

import json
import sys
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

from are.simulation.data_handler.importer import JsonScenarioImporter
from are.simulation.environment import Environment, EnvironmentConfig

import reference_environment.universes.apps  # noqa: F401  (registers the apps with ARE)
from reference_environment.universes.apps import BHARAT_APP_CLASSES


def _plain(value: Any) -> Any:
    """Serialise the way ARE's exporter does: enums as their values."""
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"Cannot serialise {type(value).__name__}")


def check(export_dir: Path) -> dict[str, Any]:
    document = json.loads((export_dir / "scenario.json").read_text(encoding="utf-8"))
    expected = {app["name"]: app for app in document["apps"]}
    scenario, _, _ = JsonScenarioImporter().import_from_json((export_dir / "scenario.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as sandbox:
        scenario.init_and_populate_apps(sandbox_dir=sandbox)
        loaded = {app.name: app for app in scenario.apps}
        failures = []
        missing = sorted(set(expected) - set(loaded))
        if missing:
            failures.append(f"apps not loaded by ARE: {missing}")
        for name, app in loaded.items():
            if type(app).__name__ != expected[name]["class_name"]:
                failures.append(f"{name} loaded as {type(app).__name__}")
            if name in ("Files", "AgentUserInterface", "SystemApp"):
                continue
            if json.loads(json.dumps(app.get_state(), default=_plain)) != expected[name]["app_state"]:
                failures.append(f"{name} state differs after loading")
        environment = Environment(EnvironmentConfig(start_time=scenario.start_time))
        environment.register_apps(list(loaded.values()))
        paying = [app for app in loaded.values() if isinstance(app, BHARAT_APP_CLASSES) and app.name != "PaySetu"]
        unconnected = [app.name for app in paying if app.payment_app is not loaded.get("PaySetu")]
        if unconnected:
            failures.append(f"not connected to PaySetu: {unconnected}")
        # Every document the export ships must read back through the Files app, byte for byte.
        files = export_dir / "files"
        for path in sorted(p for p in files.rglob("*") if p.is_file()) if files.is_dir() else []:
            shown = "/" + str(path.relative_to(files))
            try:
                same = "Files" in loaded and loaded["Files"].cat(shown) == path.read_bytes()
            except Exception as error:  # ARE raises its own errors for missing paths
                same = False
                shown += f" ({type(error).__name__})"
            if not same:
                failures.append(f"could not read {shown} through the Files app")
        tool_count = sum(len(app.get_tools()) for app in loaded.values())
    return {
        "scenario_id": scenario.scenario_id,
        "start_time": scenario.start_time,
        "apps_loaded": sorted(loaded),
        "agent_tools": tool_count,
        "failures": failures,
        "passed": not failures,
    }


def main() -> None:
    report = check(Path(sys.argv[1]).resolve())
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
