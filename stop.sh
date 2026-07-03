#!/usr/bin/env bash
set -euo pipefail
PORT="${1:-7865}"
if command -v lsof >/dev/null 2>&1; then
  PIDS=$(lsof -tiTCP:"$PORT" -sTCP:LISTEN || true)
elif command -v fuser >/dev/null 2>&1; then
  PIDS=$(fuser "$PORT/tcp" 2>/dev/null || true)
else
  echo "Install lsof or fuser to use this helper."
  exit 1
fi
if [ -z "${PIDS:-}" ]; then
  echo "No Data Curation Tool server is listening on port $PORT."
  exit 0
fi
echo "$PIDS" | xargs -r kill -TERM
sleep 1
for pid in $PIDS; do
  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL "$pid" 2>/dev/null || true
  fi
done
