# Small open models as phone assistants for Indian users

Fireworks Deploy Buildathon with Microsoft and NVIDIA, San Francisco, 2 November 2026.

**Task.** An assistant that does real errands on a person's phone, from a request in their own words and language:
"book the homestay for the Coorg dates from my default account and tell Jaan", written in Romanised Assamese, Tamil,
Gujarati, Marathi and more. The assistant has to read chats, email and calendars to find the facts, then act through
apps (payments, shopping, travel, pharmacy, doctors) and message the right people in the right register.

**User.** People in India who mix languages and scripts on their phones and expect an assistant to understand them
without switching to formal English.

**Approach.** Fine-tune NVIDIA Nemotron 3.5 Lightning (30B total, 3B active) with LoRA on Fireworks, using the passing
runs of a larger open teacher (Nemotron 3 Ultra) on training phones, and compare it with a frontier model on held-out
phones. Cost per solved task is the tradeoff we measure.

## Evaluation

- Simulated phones built with Meta's [ARE](https://github.com/facebookresearch/meta-agents-research-environments)
  (Agents Research Environments), each with a person's contacts, chats, email, calendar and apps.
- 184 tasks on 11 phones, each with the expected tool calls (oracle). Split by phone: 50 test tasks on 3 held-out
  phones (Tamil, Assamese, Gujarati owners), 134 training tasks on the other 8. No test phone is used for training.
- Every model runs with ARE's default agent, one try per task, and the same judge (ARE's judge: exact checks on
  tool arguments such as IDs, amounts and dates, plus an LLM check on message wording, Llama 3.3 70B).

## Results so far (held-out test phones)

| Model | Passed | Est. $/run |
|---|---|---|
| Claude Sonnet 5.5 (frontier baseline) | 35/50 (70%) | 0.50 |
| Nemotron 3 Ultra | 23/50 (46%) | 0.12 |
| Nemotron 3.5 Super | 21/50 (42%) | 0.04 |
| Nemotron 3.5 Lightning, untrained (OpenRouter) | 6/49 (12%) | 0.08 |
| Nemotron 3.5 Lightning, untrained (Fireworks serverless) | running | |
| Nemotron 3.5 Lightning, fine-tuned on Fireworks (25 hardest training tasks) | training | |

Costs are estimated from conversation length at list prices; pass rates are exact.

Known limitation: the judge's wording check is strict. In a hand review of 8 rejected runs where the agent called the
right tool, 4 rejections were for real mistakes (wrong dates, patient or amount) and 4 were correct messages worded
differently from the expected one. It applies equally to every model.

## Run it

The phone data is private (real people's phones) and is not in this repository; get `pkg/` from the team and put it at
the repository root.

```bash
./setup.sh                                   # Python 3.12 venv via uv, exact package versions
export OPENROUTER_API_KEY=...                # the judge runs on OpenRouter
export FIREWORKS_AI_API_KEY=...              # for fireworks_ai: models
./run.sh test openrouter:nvidia/nemotron-3.5-lightning
./run.sh test fireworks_ai:accounts/<ACCOUNT_ID>/models/<MODEL_ID>
python3 report.py runs/test/results.jsonl    # pass rate, steps, cost per run and per solved task
```

## Training data

1. `./run.sh train openrouter:nvidia/nemotron-3-ultra-550b-a55b` runs the teacher on the 134 training tasks (we ran
   it twice on the ones it failed). It solved 55.
2. `python3 build_sft.py runs/train/results.jsonl sft/train.jsonl` turns the passing runs into chat examples: one
   per task (the shortest passing run), the agent's whole conversation (system prompt with tools, the request, every
   reasoning step, tool call and tool result).
3. `python3 select_hard.py sft/train.jsonl sft/train25.jsonl --n 25` keeps the 25 hardest: most expected actions,
   then most apps, then most facts to find, judged from the task definitions only (never from model results). They
   need 3-5 actions across 2-3 apps and cover all 8 training phones.

## Fine-tune and deploy on Fireworks

Training uses Fireworks' Training API cookbook ([fw-ai/cookbook](https://github.com/fw-ai/cookbook), `training/`):
the dataset stays local, the recipe tokenizes it and trains a LoRA on a dedicated Fireworks trainer, then promotes
the adapter as a model on the account.

```bash
git clone https://github.com/fw-ai/cookbook.git && (cd cookbook/training && uv venv --python 3.12 && uv pip install -e .)
export FIREWORKS_API_KEY=...
cookbook/training/.venv/bin/python train_fireworks.py --dataset sft/train25.jsonl --output-model nemotron-lightning-rlu-v1
```

Settings: base `accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b`, LoRA rank 16, 3 epochs, batch 8,
learning rate 1e-4, 64k context. `python3 fireworks_api.py get models/nemotron-lightning-rlu-v1` shows the result.
The untrained base is served serverless on Fireworks; the tuned LoRA needs an on-demand deployment, then:

```bash
./run.sh test fireworks_ai:accounts/<ACCOUNT_ID>/models/nemotron-lightning-rlu-v1
```

## What existed before the event

Disclosed per the rules. Built before 2 November: the phone apps and phone data (`reference_environment/`, from our
RL Universe project), the 184 tasks (drafted by Claude Opus, checked automatically against each phone), the baseline
and teacher runs above, and the scripts in this repository. Built at the event: the fine-tuning, deployment and
evaluation of the tuned model on Fireworks, and the results added to this README.

## Layout

| Path | What |
|---|---|
| `run_models.py`, `run.sh` | run models on tasks, in parallel, resumable |
| `report.py` | pass rate, steps and estimated cost per model |
| `build_sft.py` | teacher runs to a chat SFT dataset |
| `select_hard.py` | keep the N hardest training examples, by task definition |
| `train_fireworks.py` | LoRA SFT on Fireworks with the Training API cookbook |
| `fireworks_api.py` | small Fireworks REST helper (account, models, jobs) |
| `reference_environment/universes/apps/` | the simulated Indian apps (payments, shopping, travel, health, ...) |
| `reference_environment/universes/assembly/` | builds a task's scenario and runs the agent and judge |
| `are/` | ARE 1.2.0 by Meta, MIT licence (`ARE_LICENSE`) |
