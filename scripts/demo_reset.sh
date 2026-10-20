#!/usr/bin/env bash
# Resets the demo to its initial state (baseline). A human runs this before the demo. (The hook blocks agents.)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

# 1) Make sure the running demo services (8100/8101) are stopped: SIGTERM → wait → SIGKILL
for port in 8100 8101; do
  pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
  [[ -n "$pids" ]] && kill $pids 2>/dev/null || true
  for _ in $(seq 1 20); do [[ -z "$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)" ]] && break; sleep 0.25; done
  pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
  [[ -n "$pids" ]] && kill -9 $pids 2>/dev/null || true
done

# 2) Reset the repository to baseline (removes in-progress changes, branches, tags and artifacts)
git reset -q --hard
git checkout -q -f -B main baseline
for b in $(git branch --list 'feature/*' --format='%(refname:short)'); do git branch -D "$b" >/dev/null 2>&1 || true; done
for t in $(git tag --list 'v*'); do git tag -d "$t" >/dev/null 2>&1 || true; done
git clean -qfdx -e .venv

# 3) Recreate the local dev DB + start baseline in staging/production
mkdir -p data logs
./.venv/bin/python scripts/migrate.py data/orders.db >/dev/null
./.venv/bin/python scripts/seed.py data/orders.db >/dev/null
./scripts/bootstrap_env.sh

# 4) Confirm the clean state
if [[ -n "$(git status --porcelain)" ]]; then echo "✘ The working tree is not clean:"; git status --short; exit 1; fi
if ls docs/cr/CR-* >/dev/null 2>&1 || [[ -d approvals ]]; then echo "✘ Artifacts from a previous run remain"; exit 1; fi
echo "✔ Demo reset complete — baseline (v$(cat VERSION)) state, local DB recreated, staging/production running"
