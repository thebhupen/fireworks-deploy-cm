"""Grade a task's oracle and its listed wrong solutions with ARE's own judge.

Run as a separate process with DEMO_FS_PATH pointing at the frozen universe's files/ folder:

    DEMO_FS_PATH=<frozen>/files python -m reference_environment.universes.assembly.task_check <task_dir>

For each solution this imports the task scenario, runs ARE's offline-validation preprocessing
(the oracle run plus judge set-up, exactly as the benchmark's `judge` command does), plays the
solution's tool calls in a live environment, and asks the judge for a verdict. The report also says what the correct
solution changed on the phone, so a person can check it did the right thing. Free-text arguments
are replayed verbatim, so the LLM part of the judge is never needed. Prints a JSON report and exits
non-zero unless the oracle passes and every wrong solution fails.

    DEMO_FS_PATH=<frozen>/files python -m reference_environment.universes.assembly.task_check catalog <frozen>

prints every tool the phone's apps offer, for whoever writes the oracle.
"""

from __future__ import annotations

import ast
import copy
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

from are.simulation.data_handler.importer import JsonScenarioImporter
from are.simulation.environment import Environment, EnvironmentConfig
from are.simulation.scenarios.scenario_imported_from_json.utils import preprocess_scenario
from are.simulation.types import EventType
from are.simulation.validation.configs import GraphPerEventJudgeConfig
from are.simulation.validation.constants import TOOL_ARG_CHECKER_TYPE_REGISTRY, CheckerType

import reference_environment.universes.apps  # noqa: F401  (registers the apps with ARE)

logging.disable(logging.WARNING)

ORACLE_RUN_FAILED = "Oracle run failed: "


class OracleRefused(Exception):
    """ARE's own oracle run, while loading the task, hit tool errors; `errors` are the apps' messages."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def load(scenario_text: str):
    scenario, _, _ = JsonScenarioImporter().import_from_json_to_benchmark(scenario_text, load_completed_events=False)
    try:
        preprocess_scenario(scenario, judge_config=GraphPerEventJudgeConfig(), offline_validation=True)
    except Exception as error:
        # ARE raises a bare Exception whose message ends with the list of the failed events' exceptions.
        message = str(error)
        if not message.startswith(ORACLE_RUN_FAILED):
            raise
        try:
            errors = [str(e) for e in ast.literal_eval(message[len(ORACLE_RUN_FAILED) :])]
        except (ValueError, SyntaxError):
            errors = [message[len(ORACLE_RUN_FAILED) :]]
        raise OracleRefused(errors) from error
    return scenario


def snapshot(env: Environment) -> dict[str, dict[str, Any]]:
    """Every app's state, as plain JSON, so before and after compare like for like."""
    return {
        app.name: json.loads(json.dumps(app.get_state(), default=str))
        for app in env.apps.values()
        if app.name not in SKIP_APPS
    }


def play(scenario, steps: list[dict[str, Any]]) -> tuple[Any, Environment, list[str], dict[str, Any]]:
    env = Environment(EnvironmentConfig(start_time=scenario.start_time, oracle_mode=False, time_increment_in_seconds=1))
    env.run(scenario, wait_for_end=False)
    aui = env.get_app("AgentUserInterface")
    aui.wait_for_user_response = False
    deadline = time.time() + 10
    while not any(e.event_type == EventType.USER for e in env.event_log.list_view()):
        if time.time() > deadline:
            raise RuntimeError("The user's message was never delivered")
        time.sleep(0.05)
    before = snapshot(env)
    errors = []
    for step in steps:
        app = env.get_app(step["app"])
        try:
            getattr(app, step["function"])(**step["args"])
        except Exception as error:  # a wrong solution may also fail at the tool
            errors.append(f"{step['app']}.{step['function']}: {error}")
    env.stop()
    return scenario.judge.validate_current_turn(env), env, errors, before


def variant(oracle: list[dict[str, Any]], wrong: dict[str, Any]) -> list[dict[str, Any]]:
    """The oracle with a wrong solution's mistakes: steps left out, arguments changed, and actions it adds, played
    before the reply."""
    steps = [step for step in copy.deepcopy(oracle) if step["id"] not in wrong.get("drop", [])]
    for step in steps:
        step["args"].update(wrong.get("replace", {}).get(step["id"], {}))
    added = copy.deepcopy(wrong.get("add", []))
    if steps and steps[-1]["app"] == "AgentUserInterface":
        return [*steps[:-1], *added, steps[-1]]
    return [*steps, *added]


SKIP_APPS = {"AgentUserInterface", "SystemApp"}
SKIP_FIELDS = {"id_counters", "view_limit", "messages_view_limit", "conversation_view_limit"}


def _trim(value: Any) -> Any:
    """A record as it is, with long texts cut and long lists shortened, for a person to read."""
    if isinstance(value, dict):
        return {k: _trim(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_trim(v) for v in value[:8]] + (["…"] if len(value) > 8 else [])
    if isinstance(value, str) and len(value) > 240:
        return value[:240] + "…"
    return value


def _diff(old: Any, new: Any) -> Any:
    """What changed between two values of one record, field by field; lists show what was appended, or which items
    changed."""
    if isinstance(old, dict) and isinstance(new, dict):
        return {k: _diff(old.get(k), v) for k, v in new.items() if old.get(k) != v}
    if isinstance(old, list) and isinstance(new, list):
        if new[: len(old)] == old:
            return {"appended": _trim(new[len(old) :])}
        if len(old) == len(new):
            return {f"item {i + 1}": _diff(o, n) for i, (o, n) in enumerate(zip(old, new, strict=True)) if o != n}
    return {"was": _trim(old), "now": _trim(new)}


def effects(before: dict[str, dict[str, Any]], env: Environment) -> dict[str, Any]:
    """Everything a solution changed on the phone, app by app: records added, and fields of records changed."""
    result: dict[str, Any] = {}
    after = snapshot(env)
    for name, old_state in before.items():
        new_state = after[name]
        app_changes: dict[str, Any] = {}
        for field, new in new_state.items():
            old = old_state.get(field)
            if field in SKIP_FIELDS or old == new:
                continue
            if isinstance(old, dict) and isinstance(new, dict):
                added = {k: _trim(v) for k, v in new.items() if k not in old}
                changed = {k: _diff(old[k], v) for k, v in new.items() if k in old and old[k] != v}
                removed = [k for k in old if k not in new]
                app_changes[field] = {
                    k: v for k, v in (("added", added), ("changed", changed), ("removed", removed)) if v
                }
            else:
                app_changes[field] = _diff(old, new)
        if app_changes:
            result[name] = app_changes
    return result


def catalog(scenario_text: str) -> list[dict[str, Any]]:
    """Every tool the phone's apps give an agent: app, name, what it does, its arguments, and whether it writes. An
    argument is free text when ARE's judge compares it with the oracle's through a language model, not exactly."""
    scenario, _, _ = JsonScenarioImporter().import_from_json_to_benchmark(scenario_text, load_completed_events=False)
    scenario.initialize()
    tools = []
    for app in scenario.apps:
        if app.name == "SystemApp":
            continue
        for tool in app.get_tools():
            function = tool.name.split("__")[-1]
            checkers = TOOL_ARG_CHECKER_TYPE_REGISTRY.get(f"{type(app).__name__}__{function}", {})
            tools.append(
                {
                    "app": app.name,
                    "function": function,
                    "description": (tool.function_description or "").strip(),
                    "writes": bool(tool.write_operation),
                    "args": [
                        {
                            "name": arg.name,
                            "type": arg.arg_type,
                            "required": not arg.has_default,
                            "description": (arg.description or "").strip(),
                            "free_text": checkers.get(arg.name) == CheckerType.llm_checker,
                        }
                        for arg in tool.args
                    ],
                }
            )
    return tools


def check(task_dir: Path) -> dict[str, Any]:
    task = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    scenario_text = (task_dir / "scenario.json").read_text(encoding="utf-8")
    results = []
    try:
        scenario = load(scenario_text)
    except OracleRefused as refused:
        # The correct steps fail on this phone, so nothing can be graded: report why, for whoever fixes the task.
        oracle = {
            "solution": "oracle",
            "expected": "pass",
            "passed": False,
            "tool_errors": refused.errors,
            "effects": {},
        }
        return {"task_id": task["task_id"], "ok": False, "results": [oracle]}
    verdict, env, errors, before = play(scenario, task["oracle"])
    results.append(
        {
            "solution": "oracle",
            "expected": "pass",
            "passed": verdict.success,
            "tool_errors": errors,
            "effects": effects(before, env),
        }
    )
    for wrong in task["wrong_solutions"]:
        verdict, _, errors, _ = play(load(scenario_text), variant(task["oracle"], wrong))
        results.append(
            {
                "solution": wrong["name"],
                "expected": "fail",
                "passed": verdict.success,
                "tool_errors": errors,
                "judge_rationale": str(verdict.rationale)[:300],
            }
        )
    ok = results[0]["passed"] and not results[0]["tool_errors"] and not any(r["passed"] for r in results[1:])
    return {"task_id": task["task_id"], "ok": ok, "results": results}


def main() -> None:
    # Only the report goes to stdout: ARE and LiteLLM print their own notices, which go to stderr instead.
    out, sys.stdout = sys.stdout, sys.stderr
    if sys.argv[1] == "catalog":  # catalog <frozen universe folder>
        text = (Path(sys.argv[2]) / "scenario.json").read_text(encoding="utf-8")
        out.write(json.dumps(catalog(text), ensure_ascii=False) + "\n")
        return
    report = check(Path(sys.argv[1]).resolve())
    out.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    out.flush()
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
