#!/usr/bin/env bash
# Deploy script (demo: local environment .deploy/<env> using release folders + a 'current' symlink)
#
#   scripts/deploy.sh staging                 # tests·lint → migration → swap → health check → smoke test
#   scripts/deploy.sh production              # only after staging verification + human approval (the hook enforces approval)
#   scripts/deploy.sh <env> --rollback        # go back to the previous release
#
# In a real environment, the same steps run on GitHub Actions (Environment approval) + Azure (Container Apps, etc.).
set -euo pipefail

ENV_NAME="${1:-}"; shift || true
ROLLBACK=0; CR="${DEMO_CR:-CR-2026-014}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rollback) ROLLBACK=1 ;;
    --cr) CR="$2"; shift ;;
    *) echo "Unknown option: $1"; exit 2 ;;
  esac
  shift
done
case "$ENV_NAME" in
  staging) PORT=8101 ;;
  production) PORT=8100 ;;
  *) echo "Usage: scripts/deploy.sh <staging|production> [--rollback] [--cr CR-ID]"; exit 2 ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
DEPLOY="$ROOT/.deploy/$ENV_NAME"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
BASE_URL="http://127.0.0.1:$PORT"
mkdir -p "$DEPLOY"/{releases,data,logs,backups}

step() { printf "\n\033[1;35m▶ %s\033[0m\n" "$*"; }
ok()   { printf "  \033[32m✔ %s\033[0m\n" "$*"; }
fail() { printf "  \033[31m✘ %s\033[0m\n" "$*"; }

listener_pids() { lsof -ti "tcp:$PORT" -sTCP:LISTEN 2>/dev/null || true; }

stop_service() {
  local pids; pids="$(listener_pids)"
  if [[ -n "$pids" ]]; then
    kill $pids 2>/dev/null || true
    for _ in $(seq 1 20); do [[ -z "$(listener_pids)" ]] && break; sleep 0.25; done
    pids="$(listener_pids)"
    [[ -n "$pids" ]] && kill -9 $pids 2>/dev/null || true
  fi
  rm -f "$DEPLOY/app.pid"
}

start_service() {
  local release="$1"
  (cd "$release" && APP_ENV="$ENV_NAME" DB_PATH="$DEPLOY/data/orders.db" LOG_PATH="$DEPLOY/logs/app.log" \
    PYTHONPATH="$release" nohup "$PY" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" \
    >> "$DEPLOY/logs/uvicorn.out" 2>&1 & echo $! > "$DEPLOY/app.pid")
}

wait_healthy() {
  local expected="$1"
  for _ in $(seq 1 30); do
    local body; body="$(curl -fsS "$BASE_URL/health" 2>/dev/null || true)"
    if [[ "$body" == *"\"version\":\"$expected\""* ]]; then listener_pids | head -1 > "$DEPLOY/app.pid"; ok "Health check passed: $body"; return 0; fi
    sleep 0.5
  done
  return 1
}

smoke() { "$PY" "$ROOT/scripts/smoke_test.py" "$BASE_URL"; }

if [[ $ROLLBACK -eq 1 ]]; then
  step "Rollback: $ENV_NAME"
  [[ -L "$DEPLOY/previous" ]] || { fail "There is no previous release to roll back to."; exit 1; }
  target="$(readlink "$DEPLOY/previous")"; current="$(readlink "$DEPLOY/current" || true)"
  stop_service; ln -sfn "$target" "$DEPLOY/current"; [[ -n "$current" ]] && ln -sfn "$current" "$DEPLOY/previous"
  start_service "$target"
  prev_version="$(tr -d '[:space:]' < "$target/VERSION")"
  wait_healthy "$prev_version" && ok "Rollback complete → v$prev_version" || { fail "Health check failed after rollback"; exit 1; }
  exit 0
fi

step "Pre-deployment checks ($ENV_NAME · v$VERSION)"
"$PY" "$ROOT/scripts/gate.py" verify code "$CR" || { fail "The code approval (②) record is missing or invalid. Stopping the deployment."; exit 1; }
if [[ "$ENV_NAME" == "production" ]]; then
  "$PY" "$ROOT/scripts/gate.py" verify staging "$CR" || { fail "No staging verification record found. Deploy to staging first."; exit 1; }
fi
(cd "$ROOT" && "$ROOT/.venv/bin/ruff" check . >/dev/null && ok "Lint passed") || { fail "Lint failed"; exit 1; }
(cd "$ROOT" && "$ROOT/.venv/bin/pytest" -q 2>&1 | tail -1) || { fail "Tests failed"; exit 1; }
ok "Tests passed"

step "Packaging the release"
RELEASE="$DEPLOY/releases/$(date +%Y%m%d-%H%M%S)-v$VERSION"
mkdir -p "$RELEASE/scripts"
cp -R "$ROOT/app" "$ROOT/db" "$ROOT/VERSION" "$ROOT/requirements.txt" "$RELEASE/"
cp "$ROOT/scripts/migrate.py" "$ROOT/scripts/seed.py" "$RELEASE/scripts/"
find "$RELEASE" -name '__pycache__' -type d -prune -exec rm -rf {} +
ok "Release folder: ${RELEASE#$ROOT/}"

step "DB backup + migration"
DB="$DEPLOY/data/orders.db"
FIRST=0; [[ -f "$DB" ]] || FIRST=1
[[ $FIRST -eq 0 ]] && cp "$DB" "$DEPLOY/backups/orders-$(date +%Y%m%d-%H%M%S).db" && ok "Backup complete (for data recovery on rollback)"
"$PY" "$RELEASE/scripts/migrate.py" "$DB"
[[ $FIRST -eq 1 ]] && "$PY" "$RELEASE/scripts/seed.py" "$DB" && ok "Demo seed data loaded"

step "Swapping the service"
OLD="$(readlink "$DEPLOY/current" || true)"
stop_service
[[ -n "$OLD" ]] && ln -sfn "$OLD" "$DEPLOY/previous"
ln -sfn "$RELEASE" "$DEPLOY/current"
start_service "$RELEASE"

if wait_healthy "$VERSION" && smoke; then
  "$PY" "$ROOT/scripts/gate.py" record-env "$ENV_NAME" "$VERSION" "$CR" >/dev/null
  printf "\n\033[1;32m✔ Deployment succeeded — %s · v%s · %s\033[0m\n" "$ENV_NAME" "$VERSION" "$BASE_URL"
else
  fail "Deployment verification failed → automatic rollback"
  stop_service
  if [[ -n "$OLD" ]]; then ln -sfn "$OLD" "$DEPLOY/current"; start_service "$OLD"; fi
  exit 1
fi
