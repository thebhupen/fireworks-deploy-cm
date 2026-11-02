"""Turn the teacher's passing runs into a supervised fine-tuning set: each run's whole conversation, exactly as ARE's
default agent sent it to the model (its prompt, the owner's request, every Thought/Action and every tool result).

    python build_sft.py <runs results.jsonl> <out.jsonl> [--model nvidia/nemotron-3-ultra-550b-a55b]

Only runs the judge passed are kept, at most one per task (the shortest), so no task is weighted twice. Roles follow
ARE's LiteLLM engine: tool results go to the model as user messages. Output is Fireworks' chat format, one
{"messages": [...]} per line; a <out>.meta.jsonl beside it says which run each line came from.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROLES = {
    "system": "system",
    "user": "user",
    "assistant": "assistant",
    "tool-response": "user",
    "tool-call": "assistant",
}


def conversation(run_dir: Path) -> list[dict[str, str]]:
    trace = next((run_dir / "traces" / "lite").glob("*.json"))
    histories = json.loads(trace.read_text(encoding="utf-8"))["per_agent_interaction_histories"]
    if len(histories) != 1:
        raise ValueError(f"{run_dir}: {len(histories)} agents")
    messages = [{"role": ROLES[m["role"]], "content": m["content"]} for m in next(iter(histories.values()))]
    if messages[0]["role"] != "system" or messages[-1]["role"] not in ("assistant", "user"):
        raise ValueError(f"{run_dir}: unexpected shape")
    while messages[-1]["role"] != "assistant":  # the last tool result teaches nothing
        messages.pop()
    return messages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--model", default="nvidia/nemotron-3-ultra-550b-a55b")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=60000,
        help="drop runs longer than this; estimated as characters / 3, which overestimates for English and "
        "roughly matches Indian scripts. Fireworks truncates past the job's --max-context-length.",
    )
    args = parser.parse_args()

    best: dict[tuple[str, str], tuple[int, list[dict[str, str]], dict]] = {}
    for line in args.results.open(encoding="utf-8"):
        run = json.loads(line)
        if run.get("model") != args.model or not run.get("success") or run.get("variant") != "owner":
            continue
        try:
            messages = conversation(Path(run["run_dir"]))
        except (StopIteration, ValueError, KeyError) as error:
            print("skipped", run["run_dir"], error)
            continue
        size = sum(len(m["content"]) for m in messages)
        if size / 3 > args.max_tokens:
            print("too long", run["run_dir"], size)
            continue
        key = (run["phone"], run["task"])
        if key not in best or size < best[key][0]:
            best[key] = (size, messages, run)
    with args.out.open("w", encoding="utf-8") as out, args.out.with_suffix(".meta.jsonl").open("w") as meta:
        for (phone, task), (size, messages, run) in sorted(best.items()):
            out.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
            steps = sum(m["role"] == "assistant" for m in messages)
            meta.write(
                json.dumps({"phone": phone, "task": task, "steps": steps, "chars": size, "run_dir": run["run_dir"]})
                + "\n"
            )
    print(f"{len(best)} examples -> {args.out}")


if __name__ == "__main__":
    main()
