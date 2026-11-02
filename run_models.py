"""Run models on the packaged tasks (export_tasks.py) with ARE's default agent and judge, several at a time.
Runs inside the rluniverse container, where the API keys are. Safe to re-run: finished runs are skipped.

    python run_models.py <pkg> <out> --split test --models openrouter:nvidia/nemotron-3.5-lightning \
        anthropic:claude-sonnet-5-5 [--tries 1] [--variant en] [--workers 6]

Each model gets its own task folders under <out>/<model>/<phone>/tasks/<task>. One line per run in <out>/results.jsonl.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PY = os.environ["RLU_ASSEMBLY_PYTHON"]
ROOT = os.environ.get("RLU_APP_ROOT", "/app")  # the repo root the assembly modules import from
lock = threading.Lock()
MIN_CREDIT_USD = 8.0  # OpenRouter runs stop once the account's remaining credit falls below this
_credit = {"at": 0.0, "left": float("inf")}


def openrouter_credit_left() -> float:
    """Remaining OpenRouter credit, checked at most once a minute."""
    with lock:
        if time.time() - _credit["at"] > 60:
            request = urllib.request.Request(
                "https://openrouter.ai/api/v1/credits",
                headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]},
            )
            data = json.load(urllib.request.urlopen(request, timeout=30))["data"]
            _credit.update(at=time.time(), left=data["total_credits"] - data["total_usage"])
        return _credit["left"]


def run_one(pkg: Path, out: Path, provider: str, model: str, item: dict, attempt: int, variant: str | None) -> None:
    # The judge always runs on OpenRouter, so every run needs credit there.
    if openrouter_credit_left() < MIN_CREDIT_USD:
        print("skipped, OpenRouter credit low:", model, item["phone"], item["task"], flush=True)
        return
    phone = (pkg / "frozen" / item["phone"] / item["version"]).resolve()
    universe = out / model.replace("/", "__") / item["phone"]
    (universe / "frozen").mkdir(parents=True, exist_ok=True)
    link = universe / "frozen" / item["version"]
    with lock:
        if not link.exists():
            link.symlink_to(phone, target_is_directory=True)
    folder = universe / "tasks" / item["task"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "task.json").write_text(
        (pkg / "tasks" / item["phone"] / item["task"] / "task.json").read_text("utf-8"), "utf-8"
    )
    env = {**os.environ, "DEMO_FS_PATH": str(phone / "files")}
    base = {
        "provider": provider,
        "model": model,
        "phone": item["phone"],
        "task": item["task"],
        "try": attempt,
        "variant": variant or "owner",
    }
    command = [
        PY,
        "-m",
        "reference_environment.universes.assembly.run_agent",
        str(folder),
        "--model",
        model,
        "--provider",
        provider,
        "--runs",
        "1",
    ] + (["--prompt-variant", variant] if variant else [])
    with open(folder / "run.log", "a", encoding="utf-8") as log:
        try:
            if not (folder / "scenario.json").exists():
                subprocess.run(
                    [PY, "-m", "reference_environment.universes.assembly.tasks", str(folder), "--scenario-only"],
                    cwd=ROOT,
                    env=env,
                    stdout=log,
                    stderr=log,
                    check=True,
                    timeout=300,
                )
            before = set((folder / "runs").glob("*")) if (folder / "runs").exists() else set()
            # No check: the run's process can die after the judge has written summary.json; the summary is the result.
            subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=log, timeout=3600)
            run_dir = sorted(set((folder / "runs").glob("*")) - before)[-1]
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            outcome = next(iter(summary["scenarios"].values()), {})
            result = {
                **base,
                "success": bool(outcome.get("success")),
                "rationale": str(outcome.get("rationale") or outcome.get("exception") or ""),
                "run_dir": str(run_dir),
            }
        except Exception as error:  # one failed run must not stop the others
            result = {**base, "success": None, "error": repr(error)}
    with lock, open(out / "results.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")
    print(model, item["phone"], item["task"], attempt, result.get("success"), flush=True)


def salvage(out: Path) -> None:
    """Record runs that finished and were judged, but were logged as errors because their process died afterwards."""
    path = out / "results.jsonl"
    if not path.exists():
        return
    runs = [json.loads(line) for line in path.open(encoding="utf-8")]
    recorded = {r["run_dir"] for r in runs if r.get("run_dir")}
    for summary_path in sorted(out.glob("*/*/tasks/*/runs/*/summary.json")):
        run_dir = summary_path.parent
        if str(run_dir) in recorded:
            continue
        config = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
        outcome = next(iter(json.loads(summary_path.read_text(encoding="utf-8"))["scenarios"].values()), {})
        result = {
            "provider": config["provider"],
            "model": config["model"],
            "phone": config["universe"]["id"],
            "task": config["task_id"],
            "try": 1,
            "variant": config.get("prompt_variant") or "owner",
            "success": bool(outcome.get("success")),
            "rationale": str(outcome.get("rationale") or outcome.get("exception") or ""),
            "run_dir": str(run_dir),
            "salvaged": True,
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        print("salvaged", result["model"], result["phone"], result["task"], result["success"], flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pkg", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--split", choices=("train", "test"), required=True)
    parser.add_argument("--models", nargs="+", required=True, help="provider:model")
    parser.add_argument("--tries", type=int, default=1)
    parser.add_argument("--variant")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--split-file", default="split.json", help="a split file in <pkg>")
    parser.add_argument("--only-unsolved", action="store_true", help="skip tasks this model already solved")
    args = parser.parse_args()
    args.pkg, args.out = args.pkg.resolve(), args.out.resolve()  # the runs execute from /app

    salvage(args.out)
    items = json.loads((args.pkg / args.split_file).read_text("utf-8"))[args.split]
    args.out.mkdir(parents=True, exist_ok=True)
    done, solved = set(), set()
    if (args.out / "results.jsonl").exists():
        for line in (args.out / "results.jsonl").open(encoding="utf-8"):
            r = json.loads(line)
            if r.get("success") is not None:
                done.add((r["model"], r["phone"], r["task"], r["try"], r["variant"]))
            if r.get("success"):
                solved.add((r["model"], r["phone"], r["task"], r["variant"]))
    jobs = []
    for attempt in range(1, args.tries + 1):
        for item in items:
            for spec in args.models:
                provider, model = spec.split(":", 1)
                variant = args.variant or "owner"
                if (model, item["phone"], item["task"], attempt, variant) in done:
                    continue
                if args.only_unsolved and (model, item["phone"], item["task"], variant) in solved:
                    continue
                jobs.append((provider, model, item, attempt))
    print(f"{len(jobs)} runs", flush=True)
    with ThreadPoolExecutor(args.workers) as pool:
        for future in [pool.submit(run_one, args.pkg, args.out, p, m, i, a, args.variant) for p, m, i, a in jobs]:
            future.result()
    print("ALLDONE", flush=True)


if __name__ == "__main__":
    main()
