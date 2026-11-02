"""Pass rate, steps and estimated cost per task for every model in one or more run_models.py results files.

    python report.py <results.jsonl> [<results.jsonl> ...] [--json out.json]

ARE's traces do not record tokens, so cost is estimated from the conversation itself: every step resends the whole
conversation so far (input) and adds one reply (output), at about 3 characters per token. Prices are list prices per
million tokens on the provider each model ran on. Treat the cost columns as estimates; the pass rates are exact.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

PRICES = {  # (input, output) USD per million tokens
    "nvidia/nemotron-3.5-lightning": (0.07, 0.20),
    "nvidia/nemotron-3.5-super-vl": (0.15, 0.50),
    "nvidia/nemotron-3-ultra-550b-a55b": (0.60, 2.40),
    "claude-sonnet-5-5": (2.00, 10.00),
    "anthropic/claude-sonnet-5.5": (2.00, 10.00),
    "google/gemini-4-argon": (2.00, 10.00),
}
CHARS_PER_TOKEN = 3


def usage(run_dir: Path) -> tuple[int, int, int]:
    """Steps, estimated input tokens and estimated output tokens for one run."""
    trace = next((run_dir / "traces" / "lite").glob("*.json"))
    history = next(iter(json.loads(trace.read_text(encoding="utf-8"))["per_agent_interaction_histories"].values()))
    sent, steps, input_chars, output_chars = 0, 0, 0, 0
    for message in history:
        if message["role"] == "assistant":
            steps += 1
            input_chars += sent
            output_chars += len(message["content"])
        sent += len(message["content"])
    return steps, input_chars // CHARS_PER_TOKEN, output_chars // CHARS_PER_TOKEN


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path, nargs="+")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    rows: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"runs": 0, "passed": 0, "errors": 0, "steps": 0, "cost": 0.0}
    )
    for path in args.results:
        for line in path.open(encoding="utf-8"):
            run = json.loads(line)
            row = rows[(run["model"], run["variant"])]
            if run.get("success") is None:
                row["errors"] += 1
                continue
            row["runs"] += 1
            row["passed"] += bool(run["success"])
            try:
                steps, tokens_in, tokens_out = usage(Path(run["run_dir"]))
            except (StopIteration, OSError, KeyError):
                continue
            price_in, price_out = PRICES.get(run["model"], (0.0, 0.0))
            row["steps"] += steps
            row["cost"] += (tokens_in * price_in + tokens_out * price_out) / 1e6

    print(f"{'model':45} {'prompt':7} {'passed':>9} {'rate':>6} {'steps':>6} {'$/run':>7} {'$/solved':>9}  errors")
    table = []
    for (model, variant), row in sorted(rows.items(), key=lambda kv: -kv[1]["passed"] / max(kv[1]["runs"], 1)):
        runs = max(row["runs"], 1)
        per_run = row["cost"] / runs
        per_solved = row["cost"] / row["passed"] if row["passed"] else float("nan")
        print(
            f"{model:45} {variant:7} {row['passed']:>4}/{row['runs']:<4} {row['passed'] / runs:>6.0%} "
            f"{row['steps'] / runs:>6.1f} {per_run:>7.3f} {per_solved:>9.3f}  {row['errors']}"
        )
        table.append(
            {"model": model, "variant": variant, **row, "cost_per_run": per_run, "cost_per_solved": per_solved}
        )
    if args.json:
        args.json.write_text(json.dumps(table, indent=2))


if __name__ == "__main__":
    main()
