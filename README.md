# One small model, ready for a billion

Small open models as phone assistants for Indian users, fine-tuned and served on Fireworks.
Fireworks Deploy Buildathon with Microsoft and NVIDIA, San Francisco, 2 November 2026.

**Task.** An assistant that does real errands on a person's phone, from a request in their own words and language,
for example *"Ghar ka bijli bill bhar do, mera usual account se, aur bhaiya ko bata do done hai"* (Romanised Hindi;
an illustrative example, not from our data). It has to read chats, email and calendars to find the facts, act through
apps (payments, shopping, travel, pharmacy, doctors), and message the right people in the right register.

**User.** People in India who mix languages and scripts on their phones and expect an assistant to understand them
without switching to formal English.

**Approach.**
1. Fine-tune **NVIDIA Nemotron 3.5 Lightning** (30B total, 3B active) and **Nemotron 3 Super** (120B, 12B active) as
   base models, with supervised fine-tuning (LoRA) on the **Fireworks Training API**.
2. The dataset is synthetic: full agent runs of larger open models (Nemotron 3 Ultra, Kimi K3) on training phones,
   kept only when the task's checks pass.
3. Serve the output models on Fireworks on-demand deployments and compare them with a frontier model (**Kimi K3**) on
   phones never used in training. The tradeoff we measure is pass rate against cost per task.
4. A routing harness combines the two fine-tuned models and escalates to Kimi K3 only when they disagree.

## Evaluation

- Simulated phones built with Meta's [ARE](https://github.com/facebookresearch/meta-agents-research-environments)
  (Agents Research Environments), each with a person's contacts, chats, email, calendar and Indian apps.
- 184 tasks on 11 phones, each with the exact tool calls a correct assistant makes (the oracle). Split by phone: **50
  test tasks on 3 held-out phones** (Tamil, Assamese and Gujarati owners) and 134 training tasks on the other 8. No
  test phone is used for training, and no test request appears in any training example (checked).
- Every model runs with ARE's default agent, one try per task, judged the same way: exact checks on tool arguments
  (IDs, amounts, dates, recipients) plus an LLM check of message wording by **Qwen3.8-Max on Fireworks**, a different
  model family from every model being evaluated.
- Pass rates come with 95% Wilson intervals (`report.py`). Runs that never terminate are stopped and counted as
  failures.

## Results (50 held-out tasks, judge Qwen3.8-Max)

| Model (all on Fireworks) | Training examples | Passed | 95% CI | $/task | $/solved |
|---|---|---|---|---|---|
| Kimi K3 (frontier baseline) | | 30/50 (60%) | 46-72% | 0.85 | 1.42 |
| Nemotron 3.5 Lightning, untrained | 0 | 2/50 (4%) | 1-14% | 0.02 | 0.60 |
| Nemotron 3.5 Lightning, LoRA v1 | 25 | 7/50 (14%) | 7-26% | 0.03 | 0.21 |
| Nemotron 3.5 Lightning, LoRA v2 | 55 | 9/50 (18%) | 10-31% | 0.07 | 0.40 |
| Nemotron 3 Super, untrained | 0 | 9/50 (18%) | 10-31% | | |
| Nemotron 3 Super, LoRA v1 | 55 | 15/50 (30%) | 19-44% | 0.48 | 1.58 |
| Nemotron 3 Super, LoRA v2 | 90 | 22/50 (44%) | 31-58% | 0.14 | 0.31 |
| Router: Lightning v2 + Super v1, else Kimi K3 | | 27/50 (54%) | 40-67% | near Kimi's | |

- **Fine-tuning works and is data-limited.** Lightning went from 4% to 14% with 25 examples and 18% with 55; Super
  from 18% to 30% with 55 and 44% with 90. Fine-tuned Lightning (3B active) matches untrained Super (12B active).
- **Cost.** Kimi K3 and untrained Lightning: serverless, estimated from tokens at list prices. Tuned models: the
  deployment's GPU time for the 50 runs (one B200 at $13/h for Lightning, 7 and 17 minutes; four B200s at $52/h for
  Super, 27 and 8 minutes). A dedicated deployment is billed by the hour, so cost per task depends on how busy it
  is: tuned Lightning is about 12x cheaper per task than Kimi K3, Super LoRA v2 about 6x (4.6x per solved task).
- **What fine-tuning changed.** Untrained Lightning mostly fails on format: 8-27 replies per run carry no `Action:`
  the agent can execute. After LoRA v1 it was about 3 per run; the remaining failures are wrong decisions.

**Judge prompt changes, disclosed.** Two of ARE's judge prompts were edited so that the judge reads its input
correctly: the tone check accepts the user's own language and script instead of requiring English (the expected
messages themselves are in Romanised Indian languages), and the reward-hacking filter no longer treats the reply's
`content:` prefix or tool-sourced IDs as fabrication. Neither loosens what the oracle requires; both apply to every
model. Details: [JUDGE_CHANGES.md](JUDGE_CHANGES.md); original prompts in `are/simulation/validation/prompts.py.orig`.

**Pilot before the event** (same 50 tasks, older judge Llama 3.3 70B, via OpenRouter; not comparable with the table):
Claude Sonnet 5.5 35/50, Nemotron 3 Ultra 23/50, Nemotron 3.5 Super VL 21/50, Nemotron 3.5 Lightning 6/49. In a hand
review of 8 runs that judge rejected although the agent called the right tool, 4 were real mistakes and 4 were correct
messages worded differently from the expected one, which is why the judge changed.

## Routing harness: agree or escalate

`reference_environment/universes/assembly/router.py`, enabled in `run_agent.py` by the `RLU_ROUTER` variable. At every
agent step the two fine-tuned models (Lightning LoRA v2, Super LoRA v1) propose the next action in parallel. If they
choose the same tool with the same arguments (free text such as a message's wording is not compared), Lightning's reply
is used; otherwise Kimi K3 answers that step. Nothing is paid, ordered or sent unless two models agree or the frontier
model decides. Every decision is logged with token usage (`router.jsonl` beside each run).

Result: 27/50 (54%, 95% CI 40-67%), close to Kimi K3 alone (60%). The two models agreed on 19% of steps; 81% went to
Kimi K3, so cost stays near Kimi's. 57 escalations were two different read-only searches, so the next step is to require
agreement only on actions that change something (pay, order, message).

```bash
./run_router.sh test fireworks_ai:accounts/<ACCOUNT_ID>/deployments/<LIGHTNING> \
  fireworks_ai:accounts/<ACCOUNT_ID>/deployments/<SUPER> fireworks_ai:accounts/fireworks/models/kimi-k3
```

## Dataset (synthetic, supervised fine-tuning)

1. `./run.sh train <provider:model>` runs a model on the 134 training tasks. Nemotron 3 Ultra solved 55 (two tries on
   the ones it failed). Kimi K3 was then run on the 79 tasks Ultra failed and solved 36 of them.
2. `python3 build_sft.py runs/train/results.jsonl sft/train.jsonl --model <model>` turns passing runs into chat-format
   JSONL: one example per task (the shortest passing run), the agent's whole conversation (system prompt with tools,
   the request, every reasoning step, tool call and tool result). Runs over the length limit are dropped.
3. `python3 select_hard.py sft/train.jsonl sft/train25.jsonl --n 25` keeps the 25 hardest: most expected actions, then
   most apps, then most facts to find, judged from the task definitions only, never from model results.

| Dataset | Examples | Used for |
|---|---|---|
| 25 hardest Ultra runs | 25 | Lightning LoRA v1 |
| all Ultra runs | 55 | Lightning LoRA v2, Super LoRA v1 |
| Ultra + Kimi K3 runs | 90 | Super LoRA v2 |

Only open-licensed models produced training data: Claude's and Gemini's terms restrict training other models on their
outputs, so they appear only as pilot baselines. Kimi K3's licence allows it.

## Fine-tune and deploy on Fireworks

Training uses the Training API cookbook ([fw-ai/cookbook](https://github.com/fw-ai/cookbook), `training/`): the dataset
stays local, the recipe tokenizes it and trains a LoRA on a dedicated Fireworks trainer, then promotes the adapter as a
model on the account.

```bash
git clone https://github.com/fw-ai/cookbook.git && (cd cookbook/training && uv venv --python 3.12 && uv pip install -e .)
export FIREWORKS_API_KEY=...
cookbook/training/.venv/bin/python train_fireworks.py --dataset sft/train.jsonl --output-model nemotron-lightning-rlu-v2
cookbook/training/.venv/bin/python train_fireworks.py --dataset sft/train.jsonl --output-model nemotron-super-rlu-v1 \
  --base-model accounts/fireworks/models/nemotron-3-super-120b-a12b-bf16 --tokenizer nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16
```

Hyperparameters (defaults in `train_fireworks.py`): LoRA rank 16, 3 epochs, batch size 8, learning rate 1e-4, max
context 64k. Training loss fell from about 0.36 to 0.10-0.15 in every run. These are standard starting values; we did
not tune them (that needs a validation split of training phones, never the test set).

LoRA models are served on an on-demand deployment with live merge (`POST /v1/accounts/<ACCOUNT_ID>/deployments` with
`baseModel` = the output model and `deploymentShape: "default"`): one B200 for Lightning, four for Super, ready in 1-10
minutes. Query the deployment, not the model name:

```bash
./run.sh test fireworks_ai:accounts/<ACCOUNT_ID>/deployments/<DEPLOYMENT_ID>
```

## Run the evaluation

The phone data is private (real people's phones) and is not in this repository; get `pkg/` from the team and put it at
the repository root.

```bash
./setup.sh                                   # Python 3.12 venv via uv, exact package versions
export FIREWORKS_AI_API_KEY=...              # models and the judge (Qwen3.8-Max) run on Fireworks
WORKERS=12 ./run.sh test fireworks_ai:accounts/fireworks/models/kimi-k3 \
  fireworks_ai:accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b
python3 report.py runs/test/results.jsonl    # pass rate, 95% CI, steps, cost per run and per solved task
```

## What existed before the event, and what we built at it

Disclosed per the rules.

- **Before 2 November:** the phone apps and phone data (`reference_environment/`, from our RL Universe project); the
  184 tasks (drafted by Claude Opus, checked automatically against each phone, not reviewed by the phone owners); the
  pilot runs with the Llama judge; the Nemotron 3 Ultra runs on the training phones; `run_models.py`, `build_sft.py`
  and `report.py`.
- **At the event:** all Fireworks work (Training API fine-tunes of Lightning and Super, deployments, serverless
  evaluation); the switch to the Qwen3.8-Max judge and its two prompt edits; every result in the table above; the Kimi
  K3 synthetic data; the 25-hardest selection; the routing harness; this repository.
- **AI assistance:** Claude Code was used to write and run much of the code and analysis; every number above comes
  from the scripts in this repository.

## Layout

| Path | What |
|---|---|
| `run_models.py`, `run.sh` | run models on tasks, in parallel, resumable; judge configurable |
| `report.py` | pass rate, 95% CI, steps and estimated cost per model |
| `build_sft.py` | passing runs to a chat-format SFT dataset |
| `select_hard.py` | keep the N hardest training examples, by task definition |
| `train_fireworks.py` | LoRA SFT on Fireworks with the Training API cookbook |
| `fireworks_api.py` | small Fireworks REST helper (account, models, jobs) |
| `run_router.sh`, `reference_environment/universes/assembly/router.py` | agree-or-escalate routing harness |
| `reference_environment/universes/apps/` | the simulated Indian apps (payments, shopping, travel, health, ...) |
| `reference_environment/universes/assembly/` | builds a task's scenario and runs the agent and judge |
| `are/` | ARE 1.2.0 by Meta, MIT licence (`ARE_LICENSE`); judge prompts edited as disclosed |
| `JUDGE_CHANGES.md`, `PRESENTATION.md` | judge edits; presentation notes |
