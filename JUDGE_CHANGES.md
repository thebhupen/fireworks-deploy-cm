# Judge changes (2 Nov 2026, buildathon)

Judge model: `accounts/fireworks/models/qwen3p8-max` on Fireworks (replacing Llama 3.3 70B on OpenRouter). Applied
identically to every model evaluated: frontier baseline, untrained Nemotron 3.5 Lightning and the fine-tuned model.
Results from the original Llama judge (`results_so_far/`, README table) are not comparable with the new judge.

Two edits to ARE's judge prompts in `are/simulation/validation/prompts.py` (original kept as `prompts.py.orig`).
Both fix the judge misreading its input; neither loosens what the oracle requires.

1. **Tone checker**: criterion 1 required "plain English". The tasks and the oracle's own expected messages are in
   the phone owner's language (Romanised Gujarati, Tamil, Assamese, ...). Qwen applied the rule literally and failed
   every correct non-English message (verified on bom_jay_01/T003: tool calls all matched, group message rejected
   solely for "primarily in Gujarati written in Latin script"). Now accepts the user's own language and script.
2. **Sanity (reward-hacking) filter**: the agent's reply is rendered as tool-call arguments, i.e. prefixed with
   `content:`. Qwen flagged that prefix as a "technical artifact" and, unable to see tool results, called real
   transaction IDs and amounts "fabricated" (verified on the same task). Now told that the prefix is input format,
   that concrete details come from tools, and that the user's language and emoji are allowed.

Runs under the unpatched English-only judge are archived in the team's local `runs/*_englishjudge/` folders (not in the repo) for reference.

## Baseline results under this judge (test split, 50 tasks, owner's own words, 1 try)

| Model | Passed | Est. $/run | Est. $/solved |
|---|---|---|---|
| Kimi K3 (`accounts/fireworks/models/kimi-k3`, frontier baseline) | 30/50 (60%) | 0.85 | 1.42 |
| Nemotron 3.5 Lightning, untrained (`accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b`) | 2/50 (4%) | 0.02 | 0.60 |

Per-task outcomes: `results/baseline_per_task.jsonl` (phone IDs anonymised, no rationale text); table with 95% Wilson intervals: `results/baseline_report.json`. Full traces stay local under `runs/`.

Loop rule: 5 Lightning runs never terminated (the agent repeated actions for 22 to 624 model calls, 27 to 52 minutes,
stopped_loop=true in the per-task file). They were stopped and counted as failures, not excluded as errors.
Apply the same rule to the fine-tuned model.

Failure breakdown (from the judge's rationale): Kimi 9 final-reply rejections, 4 contact-message rejections, 7
missing or wrong tool calls. Lightning 33 missing or wrong tool calls, 9 final-reply rejections, 1 contact-message
rejection, 5 loops.
