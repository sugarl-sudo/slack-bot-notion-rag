#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

uv venv "$VENV_PATH"
uv pip install --python "$VENV_PATH/bin/python" -e ".[dev]"

cat <<'MSG'
Environment ready.
Activate it with:
  source .venv/bin/activate
MSG
