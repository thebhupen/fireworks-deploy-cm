#!/usr/bin/env bash
# Run models on the held-out test phones (or the train phones) with ARE's default agent and judge.
#   ./run.sh test openrouter:nvidia/nemotron-3.5-lightning [more provider:model ...]
# Results: runs/<split>/results.jsonl. Safe to re-run: finished runs are skipped.
# Needs OPENROUTER_API_KEY (the judge always runs there); FIREWORKS_AI_API_KEY for fireworks_ai: models.
set -euo pipefail
cd "$(dirname "$0")"
split=$1
shift
export RLU_ASSEMBLY_PYTHON=$PWD/.venv/bin/python RLU_APP_ROOT=$PWD
python3 run_models.py pkg "runs/$split" --split "$split" --workers "${WORKERS:-8}" --models "$@"
python3 report.py "runs/$split/results.jsonl"
