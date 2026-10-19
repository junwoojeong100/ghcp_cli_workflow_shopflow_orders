#!/usr/bin/env bash
# Before the demo, starts the current release (VERSION) in staging / production to create an 'already running service'.
# Initial setup for the presenter (a human) only. (The hook blocks agents from running it.)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"

for ENV_NAME in staging production; do
  case "$ENV_NAME" in staging) PORT=8101 ;; production) PORT=8100 ;; esac
  DEPLOY="$ROOT/.deploy/$ENV_NAME"
  mkdir -p "$DEPLOY"/{releases,data,logs,backups}
  RELEASE="$DEPLOY/releases/$(date +%Y%m%d-%H%M%S)-v$VERSION"
  mkdir -p "$RELEASE/scripts"
  cp -R "$ROOT/app" "$ROOT/db" "$ROOT/VERSION" "$ROOT/requirements.txt" "$RELEASE/"
  cp "$ROOT/scripts/migrate.py" "$ROOT/scripts/seed.py" "$RELEASE/scripts/"
  find "$RELEASE" -name '__pycache__' -type d -prune -exec rm -rf {} +
  DB="$DEPLOY/data/orders.db"
  "$PY" "$RELEASE/scripts/migrate.py" "$DB" >/dev/null
  "$PY" "$RELEASE/scripts/seed.py" "$DB" >/dev/null
  ln -sfn "$RELEASE" "$DEPLOY/current"
  (cd "$RELEASE" && APP_ENV="$ENV_NAME" DB_PATH="$DB" LOG_PATH="$DEPLOY/logs/app.log" PYTHONPATH="$RELEASE" \
    nohup "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" >> "$DEPLOY/logs/uvicorn.out" 2>&1 &)
  for _ in $(seq 1 30); do curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && break; sleep 0.5; done
  lsof -ti "tcp:$PORT" -sTCP:LISTEN 2>/dev/null | head -1 > "$DEPLOY/app.pid" || true
  echo "  ✔ $ENV_NAME v$VERSION started → http://127.0.0.1:$PORT"
done
