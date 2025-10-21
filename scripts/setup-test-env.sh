#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv-test"

echo "Creating test venv at: $VENV_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$ROOT_DIR/requirements-dev.txt"
echo "Installed dev requirements into $VENV_DIR"
echo "To run tests:"
echo "  source $VENV_DIR/bin/activate"
echo "  pytest -q"
