#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p data
if [[ ! -f .env ]]; then
  cp .env.example .env
fi
export PYTHONPATH="$ROOT/backend"
export DATABASE_URL="${DATABASE_URL:-sqlite:////workspace/data/monitor.db}"
cd "$ROOT/backend"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
