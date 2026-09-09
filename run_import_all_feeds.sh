#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="python3"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

PYTHONPATH=src "$PYTHON_BIN" -m qwen_voice_engine.cli import-all-feeds "$@"
