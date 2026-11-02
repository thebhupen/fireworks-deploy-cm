"""Freeze a universe version: an ARE scenario file, its documents, and a manifest of checksums.

Usage, from the rlenv workspace root:

    omnilingual-gaia2-hindi/.venv/bin/python -m reference_environment.universes.assembly.export \\
        reference_environment/universes/blr_pranjal_01 v1

A frozen version is immutable. Re-running with unchanged sources is a no-op; changed sources
need a new version name.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from are.simulation.data_handler.models import ExportedTrace

import reference_environment.universes.apps  # noqa: F401  (registers the apps with ARE)
from reference_environment.universes.apps.common import parse_datetime

from .build import build_states
from .contacts import load_json
from .files import files_root
from .validate import validate

APP_CLASSES = {
    "Contacts": "ContactsApp",
    "Chats": "MessagingAppV2",
    "Messages": "MessagingAppV2",
    "Emails": "EmailClientV2",
    "Calendar": "CalendarApp",
    "Files": "SandboxLocalFileSystem",
    "PaySetu": "PaySetuApp",
    "ThaliDash": "ThaliDashApp",
    "SehatCare": "SehatCareApp",
    "DawaGhar": "DawaGharApp",
    "KartBazaar": "KartBazaarApp",
    "StyleGali": "StyleGaliApp",
    "SafarHub": "SafarHubApp",
    "RailMitra": "RailMitraApp",
}
SCENARIO_DURATION_SECONDS = 1800


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(universe_dir: Path) -> list[Path]:
    """Every hand-written source that defines the universe."""
    fixed = [universe_dir / name for name in ("universe_spec.md", "app_schemas.md", "cast.json", "household.json")]
    content = sorted((universe_dir / "content").rglob("*.*"))
    documents = sorted(path for path in files_root(universe_dir).rglob("*") if path.is_file())
    return fixed + content + documents


def scenario_document(universe_dir: Path, states: dict[str, dict[str, Any]], version: str) -> dict[str, Any]:
    household = load_json(universe_dir / "household.json")
    apps = [{"name": "AgentUserInterface", "class_name": "AgentUserInterface", "app_state": {"messages": []}}]
    apps += [{"name": name, "class_name": APP_CLASSES[name], "app_state": states[name]} for name in APP_CLASSES]
    apps.append({"name": "SystemApp", "class_name": "SystemApp", "app_state": {}})
    document = {
        "metadata": {
            "definition": {
                "scenario_id": f"universe_{household['universe_id']}_{version}",
                "start_time": parse_datetime(household["now"]).timestamp(),
                "duration": SCENARIO_DURATION_SECONDS,
                "time_increment_in_seconds": 1,
                "hints": [],
            }
        },
        "apps": apps,
        "events": [],
        "version": "are_simulation_v1",
    }
    ExportedTrace.model_validate(document)
    return document


def assamese_review(universe_dir: Path) -> dict[str, Any]:
    glossed = 0
    for path in sorted((universe_dir / "content").rglob("review_glosses.md")):
        rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("| 20")]
        glossed += len(rows)
    return {
        "status": "reviewed",
        "reviewer": "Owner (native Assamese speaker); owner decided this counts as the native review",
        "date": "2026-10-06",
        "where": "Design review doc, one tab per storyline; corrections applied to content/*",
        "lines_glossed": glossed,
    }


def freeze(universe_dir: Path, version: str) -> dict[str, Any]:
    states = build_states(universe_dir)
    problems = validate(universe_dir, states)
    if problems:
        raise SystemExit("Validation failed, not freezing:\n" + "\n".join(problems))
    sources = {str(path.relative_to(universe_dir)): sha256(path) for path in source_files(universe_dir)}
    target = universe_dir / "frozen" / version
    manifest_path = target / "manifest.json"
    if manifest_path.exists():
        existing = load_json(manifest_path)
        if existing["sources"] == sources:
            return existing
        raise SystemExit(f"{version} is already frozen with different sources; freeze as a new version")
    staging = universe_dir / "frozen" / f".staging-{version}"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    scenario_path = staging / "scenario.json"
    scenario_path.write_text(
        json.dumps(scenario_document(universe_dir, states, version), ensure_ascii=False, indent=1), encoding="utf-8"
    )
    shutil.copytree(files_root(universe_dir), staging / "files")
    load_report = run_load_check(staging)
    manifest = {
        "universe_id": load_json(universe_dir / "household.json")["universe_id"],
        "version": version,
        "frozen_on": "2026-10-06",
        "scenario": {"path": "scenario.json", "sha256": sha256(scenario_path)},
        "apps": {name: APP_CLASSES[name] for name in APP_CLASSES},
        "record_counts": {
            "contacts": len(states["Contacts"]["contacts"]),
            "chat_conversations": len(states["Chats"]["conversations"]),
            "chat_messages": sum(len(c["messages"]) for c in states["Chats"]["conversations"].values()),
            "sms_messages": sum(len(c["messages"]) for c in states["Messages"]["conversations"].values()),
            "emails": sum(len(f["emails"]) for f in states["Emails"]["folders"].values()),
            "calendar_events": len(states["Calendar"]["events"]),
            "paysetu_transactions": len(states["PaySetu"]["transactions"]),
            "food_orders": len(states["ThaliDash"]["orders"]),
            "shop_products": len(states["KartBazaar"]["products"]) + len(states["StyleGali"]["products"]),
            "shop_orders": len(states["KartBazaar"]["orders"]) + len(states["StyleGali"]["orders"]),
            "lab_and_doctor_slots": len(states["SehatCare"]["slots"]),
            "medicine_orders": len(states["DawaGhar"]["orders"]),
            "travel_bookings": len(states["SafarHub"]["bookings"]),
            "train_availability_records": len(states["RailMitra"]["availability"]),
        },
        "validation": {"passed": True, "problems": []},
        "are_load_check": load_report,
        "assamese_review": assamese_review(universe_dir),
        "how_to_load": (
            "Set DEMO_FS_PATH to this folder's files/ directory, import reference_environment.universes.apps "
            "(registers the apps with ARE), then load scenario.json with "
            "are.simulation.data_handler.importer.JsonScenarioImporter."
        ),
        "sources": sources,
    }
    (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    staging.rename(target)
    return manifest


def run_load_check(export_dir: Path) -> dict[str, Any]:
    """Load the export with ARE's importer in a fresh process, as a real run would."""
    workspace = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [sys.executable, "-m", "reference_environment.universes.assembly.load_check", str(export_dir)],
        cwd=workspace,
        env={**os.environ, "DEMO_FS_PATH": str(export_dir / "files")},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"ARE could not load the export:\n{result.stdout}\n{result.stderr[-3000:]}")
    return json.loads(result.stdout)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("universe_dir", type=Path)
    parser.add_argument("version")
    args = parser.parse_args(argv)
    manifest = freeze(args.universe_dir.resolve(), args.version)
    json.dump({k: manifest[k] for k in ("universe_id", "version", "scenario", "record_counts")}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
