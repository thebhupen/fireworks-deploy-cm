#!/usr/bin/env bash
# One-time setup: a Python 3.12 virtualenv with the exact packages the evaluation was run with.
# Needs uv (https://docs.astral.sh/uv/): curl -LsSf https://astral.sh/uv/install.sh | sh
set -euo pipefail
cd "$(dirname "$0")"
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.lock.txt
PYTHONPATH=. .venv/bin/python -c "import are, reference_environment.universes.apps; print('setup ok')"
