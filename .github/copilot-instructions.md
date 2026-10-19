# ShopFlow Orders & Refunds Service — Copilot Working Instructions

## Project
- Python 3.12 + FastAPI + SQLite. Structure: `app/` (routers, services, static), `db/migrations/`, `tests/`, `docs/`, `scripts/`
- Tests: `.venv/bin/pytest -q` · Lint/format: `.venv/bin/ruff check . && .venv/bin/ruff format .`
- Company standards: always follow `docs/standards/` (coding · security checklist · DB migration · release policy).

## How we work (all agents)
1. Write responses and documents in **English**. Put a business-readable summary first and technical detail after. (Code identifiers stay in English.)
2. Save the stage outputs of a change request (CR) in `docs/cr/<CR-ID>/`, in numbered order.
   `01-impact-analysis` → `02-design` → `03-implementation-notes` → `04-test-report` → `05-review-report` → `06-release-plan` → `07-ops-report` (all `.md`)
3. **Three human approvals**: ① Design approval ② Code approval ③ Production deploy approval. Approval is requested from a human when `scripts/gate.py request …` or `scripts/deploy.sh production` runs. Do not move to the next stage without approval. Do not edit `approvals/` or approved deliverables directly.
4. Write facts only. For anything you could not verify, do not guess: mark it "Needs confirmation" and give the evidence (file and line) with it.
5. Forbidden: printing secrets, modifying production data directly, `git push`, and modifying protected paths (`.github/agents`, `.github/hooks`, `scripts/`, `docs/standards`, `docs/requirements`, `approvals/`).
6. If a hook (guardrail) denies a tool call, do not work around it. Explain the reason for the denial to the user in one line, then suggest the next action.
7. **Scope control**: Do not put requirements that are not in the change request (CR) into the analysis, design or implementation scope. If something seems necessary, write it as a one-line 'follow-up item' only, and always choose **the simplest way that meets the requirements**. Items that need outside confirmation are not conditions that block deployment; write them as 'pre-deployment checklist' items.
8. **Length rules**: Keep each stage document to **3 A4 pages or fewer (about 90 lines), mostly tables**. The impact table has **10 key rows or fewer** (merge rows for the same area), decisions needed are **at most 5**, in order of importance, and evidence is **one `file:line` only**. Summarize the final chat reply in **6 lines or fewer**.
