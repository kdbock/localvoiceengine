#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: ./run_brief.sh path/to/article.txt"
  exit 1
fi

PYTHON_BIN="python3"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

PYTHONPATH=src "$PYTHON_BIN" -m qwen_voice_engine.cli brief "$1"
