"""Keep the N hardest training examples from build_sft.py's output, hardest = most expected actions in the task's
oracle, then most apps they span, then most facts the agent must find. Uses only the task definitions, never any
model's results, and only training phones' tasks (build_sft.py's input is the train split).

    python select_hard.py sft/train.jsonl sft/train25.jsonl --n 25
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def difficulty(task: dict) -> tuple[int, int, int]:
    facts = task.get("what_the_agent_must_find")
    return (
        len(task["oracle"]),
        len({action["app"] for action in task["oracle"]}),
        len(facts) if isinstance(facts, list) else 1,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--n", type=int, default=25)
    parser.add_argument("--pkg", type=Path, default=Path("pkg"))
    args = parser.parse_args()

    lines = args.source.read_text(encoding="utf-8").splitlines()
    meta = [json.loads(line) for line in args.source.with_suffix(".meta.jsonl").open(encoding="utf-8")]
    scored = []
    for line, info in zip(lines, meta, strict=True):
        task = json.loads((args.pkg / "tasks" / info["phone"] / info["task"] / "task.json").read_text("utf-8"))
        scored.append((difficulty(task), line, info))
    scored.sort(key=lambda item: item[0], reverse=True)
    with args.out.open("w", encoding="utf-8") as out, args.out.with_suffix(".meta.jsonl").open("w") as out_meta:
        for (actions, apps, facts), line, info in scored[: args.n]:
            out.write(line + "\n")
            out_meta.write(json.dumps({**info, "actions": actions, "apps": apps, "facts": facts}) + "\n")
    print(f"{min(args.n, len(scored))} of {len(scored)} examples -> {args.out}")


if __name__ == "__main__":
    main()
