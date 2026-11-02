"""Check a universe's sources the way a freeze would, without freezing anything.

    python -m reference_environment.universes.assembly.check <universe_dir> [--load]

Builds every app's state, runs the cross-app validation and, with --load, exports a scenario to a
temporary folder and loads it with ARE in a fresh process. Prints a JSON report:
{"passed": bool, "problems": [{"stage": "build" | "validate" | "load", "message": str}], "counts": {...}}.
The Universe Builder runs this on every content draft, and with --scenario to show a universe in its explorer
before it is frozen.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from .build import build_states
from .files import files_root
from .validate import validate


def counts(states: dict[str, dict[str, Any]]) -> dict[str, int]:
    return {
        "chat_messages": sum(len(c["messages"]) for c in states["Chats"]["conversations"].values()),
        "sms_messages": sum(len(c["messages"]) for c in states["Messages"]["conversations"].values()),
        "emails": sum(len(f["emails"]) for f in states["Emails"]["folders"].values()),
        "calendar_events": len(states["Calendar"]["events"]),
        "payments": len(states["PaySetu"]["transactions"]),
        "food_orders": len(states["ThaliDash"]["orders"]),
        "shop_orders": len(states["KartBazaar"]["orders"]) + len(states["StyleGali"]["orders"]),
        "travel_bookings": len(states["SafarHub"]["bookings"]),
        "lab_and_doctor_appointments": len(states["SehatCare"]["appointments"]),
        "medicine_orders": len(states["DawaGhar"]["orders"]),
    }


def check(
    universe_dir: Path, load: bool = False, dump: Path | None = None, scenario: Path | None = None
) -> dict[str, Any]:
    """With dump, also write every app's built state there as JSON (bills and ids as assembly computed them). With
    scenario, also write the ARE scenario a freeze would (version "draft"), so it can be browsed unfrozen."""
    try:
        states = build_states(universe_dir)
    except (ValueError, KeyError, TypeError, StopIteration) as error:
        message = f"{type(error).__name__}: {error}" if not isinstance(error, ValueError) else str(error)
        return {"passed": False, "problems": [{"stage": "build", "message": message}], "counts": {}}
    if dump is not None:
        dump.write_text(json.dumps(states, ensure_ascii=False), encoding="utf-8")
    if scenario is not None:
        from .export import scenario_document

        document = scenario_document(universe_dir, states, "draft")
        scenario.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    problems = [{"stage": "validate", "message": message} for message in validate(universe_dir, states)]
    if load and not problems:
        problems += _load(universe_dir, states)
    return {"passed": not problems, "problems": problems, "counts": counts(states)}


def _load(universe_dir: Path, states: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    from .export import run_load_check, scenario_document

    with tempfile.TemporaryDirectory() as folder:
        export_dir = Path(folder)
        document = scenario_document(universe_dir, states, "check")
        (export_dir / "scenario.json").write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        if files_root(universe_dir).is_dir():
            shutil.copytree(files_root(universe_dir), export_dir / "files")
        else:
            (export_dir / "files").mkdir()
        try:
            report = run_load_check(export_dir)
        except SystemExit as failure:
            return [{"stage": "load", "message": str(failure)[-2000:]}]
    return [{"stage": "load", "message": failure} for failure in report["failures"]]


def serve() -> None:
    """Answer checks one per line, so a caller pays ARE's import once: each stdin line is
    {"universe_dir": ..., "load": bool, "dump": path or null, "scenario": path or null}, each stdout line its report."""
    replies, sys.stdout = sys.stdout, sys.stderr  # anything else printed must not land among the replies
    for line in sys.stdin:
        if not line.strip():
            continue
        request = json.loads(line)
        dump = Path(request["dump"]) if request.get("dump") else None
        scenario = Path(request["scenario"]) if request.get("scenario") else None
        try:
            report = check(
                Path(request["universe_dir"]).resolve(), load=request.get("load", False), dump=dump, scenario=scenario
            )
        except Exception as error:  # a crash in one check must not end the service; report it instead
            report = {"passed": False, "problems": [{"stage": "build", "message": repr(error)}], "counts": {}}
        replies.write(json.dumps(report, ensure_ascii=False) + "\n")
        replies.flush()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("universe_dir", type=Path, nargs="?")
    parser.add_argument("--load", action="store_true", help="also load the universe with ARE")
    parser.add_argument("--dump", type=Path, help="write the built app states to this JSON file")
    parser.add_argument("--scenario", type=Path, help="write the ARE scenario (version draft) to this JSON file")
    parser.add_argument("--serve", action="store_true", help="answer checks from stdin, one JSON line each")
    args = parser.parse_args(argv)
    if args.serve:
        serve()
        return
    if args.universe_dir is None:
        parser.error("give a universe folder, or --serve")
    report = check(args.universe_dir.resolve(), load=args.load, dump=args.dump, scenario=args.scenario)
    json.dump(report, sys.stdout, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
