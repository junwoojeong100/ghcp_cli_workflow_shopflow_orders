#!/usr/bin/env bash
# 배포 스크립트 (데모: 로컬 환경 .deploy/<env> 에 릴리스 폴더 + current 심볼릭 링크 방식)
#
#   scripts/deploy.sh staging                 # 테스트·린트 → 마이그레이션 → 교체 → 헬스체크 → 스모크 테스트
#   scripts/deploy.sh production              # staging 검증 + 사람 승인 후에만 (훅이 승인을 강제)
#   scripts/deploy.sh <env> --rollback        # 직전 릴리스로 되돌리기
#
# 실제 환경에서는 같은 단계를 GitHub Actions(Environment 승인) + Azure(Container Apps 등)로 수행한다.
set -euo pipefail

ENV_NAME="${1:-}"; shift || true
ROLLBACK=0; CR="${DEMO_CR:-CR-2026-014}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rollback) ROLLBACK=1 ;;
    --cr) CR="$2"; shift ;;
    *) echo "알 수 없는 옵션: $1"; exit 2 ;;
  esac
  shift
done
case "$ENV_NAME" in
  staging) PORT=8101 ;;
  production) PORT=8100 ;;
  *) echo "사용법: scripts/deploy.sh <staging|production> [--rollback] [--cr CR-ID]"; exit 2 ;;
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
    if [[ "$body" == *"\"version\":\"$expected\""* ]]; then listener_pids | head -1 > "$DEPLOY/app.pid"; ok "헬스체크 통과: $body"; return 0; fi
    sleep 0.5
  done
  return 1
}

smoke() { "$PY" "$ROOT/scripts/smoke_test.py" "$BASE_URL"; }

if [[ $ROLLBACK -eq 1 ]]; then
  step "롤백: $ENV_NAME"
  [[ -L "$DEPLOY/previous" ]] || { fail "되돌릴 직전 릴리스가 없습니다."; exit 1; }
  target="$(readlink "$DEPLOY/previous")"; current="$(readlink "$DEPLOY/current" || true)"
  stop_service; ln -sfn "$target" "$DEPLOY/current"; [[ -n "$current" ]] && ln -sfn "$current" "$DEPLOY/previous"
  start_service "$target"
  prev_version="$(tr -d '[:space:]' < "$target/VERSION")"
  wait_healthy "$prev_version" && ok "롤백 완료 → v$prev_version" || { fail "롤백 후 헬스체크 실패"; exit 1; }
  exit 0
fi

step "배포 전 점검 ($ENV_NAME · v$VERSION)"
"$PY" "$ROOT/scripts/gate.py" verify code "$CR" || { fail "코드 승인(②) 기록이 없거나 무효입니다. 배포를 중단합니다."; exit 1; }
if [[ "$ENV_NAME" == "production" ]]; then
  "$PY" "$ROOT/scripts/gate.py" verify staging "$CR" || { fail "staging 검증 기록이 없습니다. 먼저 staging 에 배포하세요."; exit 1; }
fi
(cd "$ROOT" && "$ROOT/.venv/bin/ruff" check . >/dev/null && ok "린트 통과") || { fail "린트 실패"; exit 1; }
(cd "$ROOT" && "$ROOT/.venv/bin/pytest" -q 2>&1 | tail -1) || { fail "테스트 실패"; exit 1; }
ok "테스트 통과"

step "릴리스 패키징"
RELEASE="$DEPLOY/releases/$(date +%Y%m%d-%H%M%S)-v$VERSION"
mkdir -p "$RELEASE/scripts"
cp -R "$ROOT/app" "$ROOT/db" "$ROOT/VERSION" "$ROOT/requirements.txt" "$RELEASE/"
cp "$ROOT/scripts/migrate.py" "$ROOT/scripts/seed.py" "$RELEASE/scripts/"
find "$RELEASE" -name '__pycache__' -type d -prune -exec rm -rf {} +
ok "릴리스 폴더: ${RELEASE#$ROOT/}"

step "DB 백업 + 마이그레이션"
DB="$DEPLOY/data/orders.db"
FIRST=0; [[ -f "$DB" ]] || FIRST=1
[[ $FIRST -eq 0 ]] && cp "$DB" "$DEPLOY/backups/orders-$(date +%Y%m%d-%H%M%S).db" && ok "백업 완료 (롤백 시 데이터 복구용)"
"$PY" "$RELEASE/scripts/migrate.py" "$DB"
[[ $FIRST -eq 1 ]] && "$PY" "$RELEASE/scripts/seed.py" "$DB" && ok "시연용 초기 데이터 적재"

step "서비스 교체"
OLD="$(readlink "$DEPLOY/current" || true)"
stop_service
[[ -n "$OLD" ]] && ln -sfn "$OLD" "$DEPLOY/previous"
ln -sfn "$RELEASE" "$DEPLOY/current"
start_service "$RELEASE"

if wait_healthy "$VERSION" && smoke; then
  "$PY" "$ROOT/scripts/gate.py" record-env "$ENV_NAME" "$VERSION" "$CR" >/dev/null
  printf "\n\033[1;32m✔ 배포 성공 — %s · v%s · %s\033[0m\n" "$ENV_NAME" "$VERSION" "$BASE_URL"
else
  fail "배포 검증 실패 → 자동 롤백"
  stop_service
  if [[ -n "$OLD" ]]; then ln -sfn "$OLD" "$DEPLOY/current"; start_service "$OLD"; fi
  exit 1
fi
