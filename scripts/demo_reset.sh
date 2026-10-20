#!/usr/bin/env bash
# 데모를 처음 상태로 되돌린다. 사람이 시연 전에 실행한다. (에이전트는 훅이 차단)
#   ./scripts/demo_reset.sh                 이 판의 시작 상태로 초기화 (한국어판: 태그 baseline-ko)
#   DEMO_LANG=en ./scripts/demo_reset.sh    영어판(태그 baseline)으로 전환, DEMO_LANG=ko 는 한국어판
# 두 판이 한 저장소에 들어 있다: 영어판은 루트, 한국어판은 main 브랜치의 ko/ 폴더. 작업 트리에는 한쪽 판만 펼쳐진다
# (초기화가 선택한 태그의 트리를 저장소 루트에 놓는다). 그래서 시연 중에는 ko/ 폴더가 보이지 않는다.
set -euo pipefail

reset_demo() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  local lang="${DEMO_LANG:-ko}" baseline port pids b t
  case "$lang" in
    ko) baseline=baseline-ko ;;
    en) baseline=baseline ;;
    *) echo "✘ DEMO_LANG 은 en 또는 ko 여야 합니다 (현재: $lang)"; return 1 ;;
  esac
  git rev-parse -q --verify "refs/tags/$baseline" >/dev/null \
    || { echo "✘ 태그 '$baseline' 가 없습니다. 먼저 태그를 받으세요: git fetch --tags --force"; return 1; }

  # 1) 실행 중인 데모 서비스(8100/8101)를 확실히 종료: SIGTERM → 대기 → SIGKILL
  for port in 8100 8101; do
    pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
    [[ -n "$pids" ]] && kill $pids 2>/dev/null || true
    for _ in $(seq 1 20); do [[ -z "$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)" ]] && break; sleep 0.25; done
    pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
    [[ -n "$pids" ]] && kill -9 $pids 2>/dev/null || true
  done

  # 2) 저장소를 선택한 baseline 으로 되돌림 (작업 중이던 변경·브랜치·태그·산출물 모두 제거)
  git reset -q --hard
  git checkout -q -f -B main "$baseline"
  for b in $(git branch --list 'feature/*' --format='%(refname:short)'); do git branch -D "$b" >/dev/null 2>&1 || true; done
  for t in $(git tag --list 'v*'); do git tag -d "$t" >/dev/null 2>&1 || true; done
  git clean -qfdx -e .venv

  # 3) 로컬 개발 DB 재생성 + staging/production 에 baseline 가동
  mkdir -p data logs
  ./.venv/bin/python scripts/migrate.py data/orders.db >/dev/null
  ./.venv/bin/python scripts/seed.py data/orders.db >/dev/null
  ./scripts/bootstrap_env.sh

  # 4) 깨끗한 상태 확인
  if [[ -n "$(git status --porcelain)" ]]; then echo "✘ 작업 트리가 깨끗하지 않습니다:"; git status --short; return 1; fi
  if ls docs/cr/CR-* >/dev/null 2>&1 || [[ -d approvals ]]; then echo "✘ 이전 산출물이 남아 있습니다"; return 1; fi
  echo "✔ 데모 초기화 완료 — $baseline(v$(cat VERSION)) 상태, 로컬 DB 재생성, staging/production 가동 중"
}

# 일부러 한 줄: bash 는 이 줄을 통째로 읽은 뒤 실행하므로, 초기화 도중 이 파일이 다른 판의 사본으로 바뀌어도(체크아웃이 가져온다) 다음 실행에 영향이 없다.
reset_demo "$@"; exit $?
