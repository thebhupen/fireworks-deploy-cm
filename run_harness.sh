#!/usr/bin/env bash
# Agree-or-escalate harness on the test (or train) phones: at every agent step two fine-tuned models propose
# the next action; if they agree (same tool and arguments, message wording aside) the first one's reply is used,
# otherwise the fallback model answers that step. Decisions and token usage: runs/harness_<split>/.../router.jsonl.
#   ./run_harness.sh test fireworks_ai:<model A> fireworks_ai:<model B> fireworks_ai:<fallback>
set -euo pipefail
cd "$(dirname "$0")"
split=$1 first=$2 second=$3 fallback=$4
export RLU_ASSEMBLY_PYTHON=$PWD/.venv/bin/python RLU_APP_ROOT=$PWD
export RLU_ROUTER="{\"models\": [\"$first\", \"$second\"], \"fallback\": \"$fallback\"}"
python3 run_models.py pkg "runs/harness_$split" --split "$split" --workers "${WORKERS:-8}" \
  --judge "${JUDGE:-fireworks_ai:accounts/fireworks/models/qwen3p8-max}" --models router:router
python3 report.py "runs/harness_$split/results.jsonl"
