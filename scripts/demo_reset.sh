#!/usr/bin/env bash
# 데모를 처음 상태(baseline)로 되돌린다. 사람이 시연 전에 실행한다. (에이전트는 훅이 차단)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# 1) 실행 중인 데모 서비스(8100/8101)를 확실히 종료: SIGTERM → 대기 → SIGKILL
for port in 8100 8101; do
  pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
  [[ -n "$pids" ]] && kill $pids 2>/dev/null || true
  for _ in $(seq 1 20); do [[ -z "$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)" ]] && break; sleep 0.25; done
  pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
  [[ -n "$pids" ]] && kill -9 $pids 2>/dev/null || true
done

# 2) 저장소를 baseline 으로 되돌림 (작업 중이던 변경·브랜치·태그·산출물 모두 제거)
git reset -q --hard
git checkout -q -f -B main baseline
for b in $(git branch --list 'feature/*' --format='%(refname:short)'); do git branch -D "$b" >/dev/null 2>&1 || true; done
for t in $(git tag --list 'v*'); do git tag -d "$t" >/dev/null 2>&1 || true; done
git clean -qfdx -e .venv

# 3) 로컬 개발 DB 재생성 + staging/production 에 baseline 가동
mkdir -p data logs
./.venv/bin/python scripts/migrate.py data/orders.db >/dev/null
./.venv/bin/python scripts/seed.py data/orders.db >/dev/null
./scripts/bootstrap_env.sh

# 4) 깨끗한 상태 확인
if [[ -n "$(git status --porcelain)" ]]; then echo "✘ 작업 트리가 깨끗하지 않습니다:"; git status --short; exit 1; fi
if ls docs/cr/CR-* >/dev/null 2>&1 || [[ -d approvals ]]; then echo "✘ 이전 산출물이 남아 있습니다"; exit 1; fi
echo "✔ 데모 초기화 완료 — baseline(v$(cat VERSION)) 상태, 로컬 DB 재생성, staging/production 가동 중"
