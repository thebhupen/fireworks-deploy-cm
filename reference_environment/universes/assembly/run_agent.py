"""Run an LLM agent on a task with ARE's own benchmark runner and keep everything it produces.

Usage, from the rlenv workspace root, with the provider's key in the environment
(for OpenRouter: OPENROUTER_API_KEY):

    omnilingual-gaia2-hindi/.venv/bin/python -m reference_environment.universes.assembly.run_agent \\
        reference_environment/universes/blr_pranjal_01/tasks/T001_lehenga_size_swap \\
        --model openai/gpt-oss-120b --provider openrouter --runs 1 [--reasoning-effort high] [--prompt-variant en]

The task's scenario.json (or, with --prompt-variant, the same scenario with one of the task's
prompt_variants as the user's message) is run by ARE's default agent, graded by ARE's judge, and the traces,
logs and a summary land in <task_dir>/runs/<timestamp>_<model>/. The Files app is served from the
frozen universe the task is pinned to, so the run re-executes itself with DEMO_FS_PATH set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .contacts import load_json
from .tasks import build_task_scenario, frozen_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("--model", default="openai/gpt-oss-120b")
    parser.add_argument("--provider", default="openrouter")
    parser.add_argument("--judge-model", default="meta-llama/llama-3.3-70b-instruct")  # GAIA2's default judge
    parser.add_argument("--judge-provider", default="openrouter")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument(
        "--reasoning-effort",
        choices=["minimal", "low", "medium", "high"],
        help="Thinking effort for the agent's model (OpenRouter's reasoning.effort); the judge is unaffected",
    )
    parser.add_argument("--prompt-variant", help="A key of the task's prompt_variants, e.g. en")
    parser.add_argument("--output-dir", type=Path, help="Set by the launcher; do not pass")
    return parser.parse_args()


def run_dir_name(model: str, prompt_variant: str | None) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{stamp}_{re.sub(r'[^A-Za-z0-9.-]+', '-', model)}"
    return f"{name}_prompt-{prompt_variant}" if prompt_variant else name


def launch(args: argparse.Namespace) -> Path:
    """Prepare the run folder and re-run this module in a child process with DEMO_FS_PATH set."""
    task_dir = args.task_dir.resolve()
    task = load_json(task_dir / "task.json")
    output_dir = task_dir / "runs" / run_dir_name(args.model, args.prompt_variant)
    dataset_dir = output_dir / "dataset"
    dataset_dir.mkdir(parents=True)
    if args.prompt_variant:
        scenario = json.dumps(build_task_scenario(task_dir, args.prompt_variant), ensure_ascii=False, indent=1)
    else:
        scenario = (task_dir / "scenario.json").read_text(encoding="utf-8")
    (dataset_dir / f"{task['task_id']}.json").write_text(scenario, encoding="utf-8")
    config = {
        "task_id": task["task_id"],
        "universe": task["universe"],
        "model": args.model,
        "provider": args.provider,
        "judge_model": args.judge_model,
        "judge_provider": args.judge_provider,
        "runs": args.runs,
        "reasoning_effort": args.reasoning_effort,
        "prompt_variant": args.prompt_variant,
        "prompt": json.loads(scenario)["events"][0]["action"]["args"][0]["value"],
        "agent": "default",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_dir / "run_config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    workspace = Path(__file__).resolve().parents[3]
    command = [
        sys.executable, "-m", "reference_environment.universes.assembly.run_agent", str(task_dir),
        "--model", args.model, "--provider", args.provider,
        "--judge-model", args.judge_model, "--judge-provider", args.judge_provider,
        "--runs", str(args.runs), "--output-dir", str(output_dir),
    ]  # fmt: skip
    if args.reasoning_effort:
        command += ["--reasoning-effort", args.reasoning_effort]
    env = {**os.environ, "DEMO_FS_PATH": str(frozen_dir(task_dir, task) / "files")}
    with open(output_dir / "run.log", "w", encoding="utf-8") as log:
        result = subprocess.run(command, cwd=workspace, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        raise SystemExit(f"Agent run failed, see {output_dir / 'run.log'}")
    return output_dir


def set_agent_reasoning(model: str, effort: str) -> dict[str, int]:
    """Make every LLM call for `model` ask for the given thinking effort, and count what it used.

    ARE's LiteLLM engine has no option for this, so the engine module's `completion` is wrapped.
    Calls for other models (the judge, unless it is the same model) pass through unchanged.
    """
    from are.simulation.agents.llm.litellm import litellm_engine

    usage = {"calls": 0, "reasoning_tokens": 0, "completion_tokens": 0}
    completion = litellm_engine.completion

    def completion_with_reasoning(*call_args, **kwargs):
        if kwargs.get("model") != model:
            return completion(*call_args, **kwargs)
        response = completion(*call_args, **kwargs, extra_body={"reasoning": {"effort": effort}})
        details = response.usage.completion_tokens_details
        usage["calls"] += 1
        usage["reasoning_tokens"] += (details.reasoning_tokens or 0) if details else 0
        usage["completion_tokens"] += response.usage.completion_tokens
        return response

    litellm_engine.completion = completion_with_reasoning
    return usage


def execute(args: argparse.Namespace) -> None:
    """The child process: ARE is imported only here, after DEMO_FS_PATH is set."""
    from are.simulation.benchmark.scenario_executor import run_dataset

    import reference_environment.universes.apps  # noqa: F401  (registers the apps with ARE)

    output_dir = args.output_dir
    agent_usage = set_agent_reasoning(args.model, args.reasoning_effort) if args.reasoning_effort else None
    result = run_dataset(
        model=args.model,
        model_provider=args.provider,
        dataset_path=str(output_dir / "dataset"),
        agent="default",
        output_dir=str(output_dir / "traces"),
        trace_dump_format="both",
        max_concurrent_scenarios=1,
        num_runs=args.runs,
        judge_model=args.judge_model,
        judge_provider=args.judge_provider,
    )
    summary = {
        "success_rate": result.success_rate(),
        "scenarios": {
            scenario_id if run is None else f"{scenario_id}#run{run}": {
                "success": scenario_result.success,
                "exception": str(scenario_result.exception) if scenario_result.exception else None,
                "rationale": scenario_result.rationale,
                "export_path": scenario_result.export_path,
            }
            for (scenario_id, run), scenario_result in result.scenario_results.items()
        },
    }
    if agent_usage is not None:
        summary["agent_usage"] = agent_usage
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.output_dir is None:
        output_dir = launch(args)
        print((output_dir / "summary.json").read_text(encoding="utf-8"))
    else:
        execute(args)


if __name__ == "__main__":
    main()
