#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
open "http://127.0.0.1:5173"
./run_new_local_studio.sh
