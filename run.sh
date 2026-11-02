#!/usr/bin/env bash
# Run models on the held-out test phones (or the train phones) with ARE's default agent and judge.
#   ./run.sh test openrouter:nvidia/nemotron-3.5-lightning [more provider:model ...]
# Results: runs/<split>/results.jsonl. Safe to re-run: finished runs are skipped.
# Needs FIREWORKS_AI_API_KEY. Judge: Qwen3.8-Max on Fireworks (JUDGE=provider:model to change it; keep one judge
# per results folder). OPENROUTER_API_KEY only for openrouter: models.
set -euo pipefail
cd "$(dirname "$0")"
split=$1
shift
export RLU_ASSEMBLY_PYTHON=$PWD/.venv/bin/python RLU_APP_ROOT=$PWD
python3 run_models.py pkg "runs/$split" --split "$split" --workers "${WORKERS:-8}" \
  --judge "${JUDGE:-fireworks_ai:accounts/fireworks/models/qwen3p8-max}" --models "$@"
python3 report.py "runs/$split/results.jsonl"
