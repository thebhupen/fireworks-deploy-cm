"""Turn a hand-written task.json into a runnable ARE scenario on top of a frozen universe version.

Usage, from the rlenv workspace root:

    omnilingual-gaia2-hindi/.venv/bin/python -m reference_environment.universes.assembly.tasks \\
        reference_environment/universes/blr_pranjal_01/tasks/T001_lehenga_size_swap

Writes scenario.json next to task.json, then grades the oracle and every listed wrong solution
with ARE's own judge in a fresh process (see task_check.py). The task is pinned to the frozen
universe by the scenario checksum in its manifest.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from are.simulation.data_handler.models import ExportedTrace

from .contacts import load_json
from .export import sha256

USER_EVENT_ID = "Event-USER-{task}"
ORACLE_EVENT_ID = "OracleEvent-AGENT-{task}-{step}"


def encode(value: Any) -> tuple[str | None, str]:
    """Encode an argument the way ARE's importer parses it back (value as text plus a type name)."""
    if value is None:
        return None, "Optional[str]"
    if isinstance(value, bool):
        return str(value), "bool"
    if isinstance(value, int):
        return str(value), "int"
    if isinstance(value, float):
        return str(value), "float"
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False), "list"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False), "dict"
    return str(value), "str"


def frozen_dir(task_dir: Path, task: dict[str, Any]) -> Path:
    universe_dir = task_dir.parents[1]
    target = universe_dir / "frozen" / task["universe"]["version"]
    manifest = load_json(target / "manifest.json")
    if sha256(target / "scenario.json") != manifest["scenario"]["sha256"]:
        raise SystemExit(f"{target} does not match its manifest")
    return target


def task_events(task: dict[str, Any], start_time: float) -> list[dict[str, Any]]:
    user_id = USER_EVENT_ID.format(task=task["task_id"])
    events: list[dict[str, Any]] = [
        {
            "class_name": "Event",
            "event_type": "USER",
            "event_time": start_time,
            "event_id": user_id,
            "dependencies": [],
            "event_relative_time": 0.0,
            "action": {
                "action_id": f"AgentUserInterface.send_message_to_agent-{task['task_id']}",
                "app": "AgentUserInterface",
                "function": "send_message_to_agent",
                "operation_type": "READ",
                "args": [{"name": "content", "value": task["prompt"], "value_type": "str"}],
            },
            "metadata": None,
        }
    ]
    steps = {step["id"] for step in task["oracle"]}
    for step in task["oracle"]:
        unknown = set(step["depends_on"]) - steps
        if unknown:
            raise SystemExit(f"Oracle step {step['id']} depends on unknown steps {sorted(unknown)}")
        args = []
        for name, value in step["args"].items():
            text, value_type = encode(value)
            args.append({"name": name, "value": text, "value_type": value_type})
        events.append(
            {
                "class_name": "OracleEvent",
                "event_type": "AGENT",
                "event_time": start_time + 1,
                "event_id": ORACLE_EVENT_ID.format(task=task["task_id"], step=step["id"]),
                "dependencies": [user_id]
                + [ORACLE_EVENT_ID.format(task=task["task_id"], step=parent) for parent in step["depends_on"]],
                "event_relative_time": 1.0,
                "action": {
                    "action_id": "",
                    "app": step["app"],
                    "function": step["function"],
                    "operation_type": None,
                    "args": args,
                },
                "metadata": None,
            }
        )
    return events


def build_task_scenario(task_dir: Path, prompt_variant: str | None = None) -> dict[str, Any]:
    """The task's ARE scenario; a prompt variant swaps only the user's words (same oracle, same judge)."""
    task = load_json(task_dir / "task.json")
    if prompt_variant is not None:
        task = {**task, "prompt": task["prompt_variants"][prompt_variant]}
    universe = load_json(frozen_dir(task_dir, task) / "scenario.json")
    definition = universe["metadata"]["definition"]
    document = {
        **universe,
        "metadata": {
            "definition": {
                **definition,
                "scenario_id": task["task_id"],
                "tags": task["capabilities"],
            }
        },
        "events": task_events(task, definition["start_time"]),
    }
    ExportedTrace.model_validate(document)
    return document


def check_task(task_dir: Path) -> dict[str, Any]:
    """Write the task's scenario.json and grade it (task_check.py, in a fresh process). Returns the report whether
    or not the task passed; raises SystemExit only when the check could not run at all."""
    document = build_task_scenario(task_dir)
    task = load_json(task_dir / "task.json")
    scenario_path = task_dir / "scenario.json"
    scenario_path.write_text(json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8")
    workspace = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "-m", "reference_environment.universes.assembly.task_check", str(task_dir)],
        cwd=workspace,
        env={**os.environ, "DEMO_FS_PATH": str(frozen_dir(task_dir, task) / "files")},
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(result.stdout)
    except ValueError:
        raise SystemExit(f"Task check could not run:\n{result.stdout[-2000:]}\n{result.stderr[-4000:]}") from None
    (task_dir / "check_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def export_task(task_dir: Path) -> dict[str, Any]:
    report = check_task(task_dir)
    if not report["ok"]:
        raise SystemExit(f"Task check failed:\n{json.dumps(report, ensure_ascii=False, indent=2)}")
    return report


def main() -> None:
    """tasks.py <task_dir> fails unless the task passes; with --report it prints the report either way (for the
    Universe Builder, which sends the problems back to the drafter); --scenario-only only writes scenario.json."""
    task_dir = Path(sys.argv[1]).resolve()
    if "--scenario-only" in sys.argv[2:]:  # write scenario.json for a run, without grading
        document = build_task_scenario(task_dir)
        (task_dir / "scenario.json").write_text(json.dumps(document, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({"written": str(task_dir / "scenario.json")}))
        return
    report = check_task(task_dir) if "--report" in sys.argv[2:] else export_task(task_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
