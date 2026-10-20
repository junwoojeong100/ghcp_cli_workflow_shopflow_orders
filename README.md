# ShopFlow Orders × GitHub Copilot CLI · Custom Agent Demo Repository

A change request from the business team, **CR-2026-014** (VIP refund policy improvement), arrives for the **order and refund service of the fictional online store ShopFlow** (Python · FastAPI · SQLite).
This repository reproduces the workflow in which **GitHub Copilot CLI + 7 custom agents** handle Analysis → Design → Implementation → Testing → Review → Deployment → Operations analysis,
and **humans approve in only 3 places (design · code · production deploy)**.

> All data, customers and companies in this repository are fictional. Staging / production are simulated with local ports (8101 / 8100).
> `./scripts/demo_reset.sh` returns the repository to the `baseline` tag state. **All uncommitted changes are deleted**, so run it in a copy made for the demo.

## ghcp_cli_workflow series — two repositories used together

| Repository | Role |
|---|---|
| **[ghcp_cli_workflow_shopflow_orders](https://github.com/junwoojeong100/ghcp_cli_workflow_shopflow_orders)** (this repository) | **The demo target** — demo app · 7 custom agents · hooks · CI/Deploy samples. Reproduce the same flow yourself with the scripts below |
| **[ghcp_cli_workflow_demo_kit](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit)** | **Presentation kit** — presentation guide · video/slide production source · the actual outputs of the recorded session (`sample-output/`). The slides (PPTX) and videos (MP4) are in [Releases](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit/releases) |

This repository has a **single `main` branch and one code base** (the agents, documents and screens are in English). Only this guide comes in two languages: **English** (this file, the default) and **Korean** ([README.ko.md](README.ko.md)).
The presentation kit has English slides and videos by default; the Korean edition is under its [`ko/` folder](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit/tree/main/ko).

**Watch in your browser (no download):** English [full video](https://junwoojeong100.github.io/ghcp_cli_workflow_demo_kit/video/GHCP_CLI_Workflow_Demo_EN.mp4) · [slides](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fjunwoojeong100.github.io%2Fghcp_cli_workflow_demo_kit%2FGHCP_CLI_Workflow_Demo_EN.pptx) — Korean [full video](https://junwoojeong100.github.io/ghcp_cli_workflow_demo_kit/ko/video/GHCP_CLI_Workflow_Demo_KO.mp4) · [slides](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fjunwoojeong100.github.io%2Fghcp_cli_workflow_demo_kit%2Fko%2FGHCP_CLI_Workflow_Demo_KO.pptx). Per-step clips and chapter links are in the [presentation kit README](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit#watch-online--no-download).

The kit's tools look for this repository in a folder named **`shopflow-orders`**. To use them together with the kit, clone with an explicit folder name (see chapter 1 below).

Tags: `baseline` = the demo start state (the state `demo_reset.sh` returns to), `baseline-recorded` = the start state when the video was recorded.
To see exactly what differs between the two, run `git diff --stat baseline baseline-recorded`. `sample-output/full-change.diff` in the presentation kit is based on `baseline-recorded`.
The tags `baseline-ko` and `baseline-recorded-ko` keep the Korean-language variant of the demo (Korean agents, documents and screens) on which the Korean slides and video of the presentation kit were recorded. They are tags only, not a branch: `git clone -b baseline-ko https://github.com/junwoojeong100/ghcp_cli_workflow_shopflow_orders.git shopflow-orders`.

## 0. What this demo verified (measured in a recorded session)

| Item | Result |
|---|---|
| Actual time from requirement to operations analysis | About **38 min** (Analysis 2.7 · Design 3.4 · Implementation 7.0 · Testing 8.2 · Review 4.1 · Deployment 4.2 · Operations 8.4 min, including human response time) |
| Human interventions | **6** = 3 approvals (design · code · production deploy) + 3 decisions in the design stage |
| Size of the change | 8 app/DB files, +171 lines (Implementation stage); tests 26 → **100** (Testing stage: the Tester adds 74, the Developer adds none); coverage 99% |
| Review result | Blocker 0 · Major 0 · Minor 0 |
| AI usage | About **340 AI Credits** for the whole session (1 Credit = $0.01 → about $3.40) |
| Audit records | 169 tool calls, 3 approval requests, 2 blocked (main demo) / 3 blocked in the guardrail demo |

Test environment: macOS, GitHub Copilot CLI 1.0.98, the default model at the time of recording (GPT-6.1 Sol). Elapsed time and usage vary by model and plan.
The actual outputs of the recorded session are kept in `sample-output/` of the presentation kit repository ([ghcp_cli_workflow_demo_kit](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit)).

## 1. Prerequisites

| Item | Description |
|---|---|
| GitHub Copilot | A personal or organization (Business/Enterprise) license, with Copilot CLI allowed by the organization policy |
| Copilot CLI | `npm install -g @github/copilot` · `brew install --cask copilot-cli` · `winget install GitHub.Copilot` → run `copilot`, then `/login` |
| Tools | Python 3.12, git, sqlite3, jq, curl, lsof (macOS / Linux) |

```bash
git clone https://github.com/junwoojeong100/ghcp_cli_workflow_shopflow_orders.git shopflow-orders   # name the folder shopflow-orders (the default path for the presentation kit tools)
cd shopflow-orders
python3.12 -m venv --copies .venv        # --copies: copies the venv python, which reduces path-permission pop-ups
./.venv/bin/pip install -r requirements.txt
./scripts/demo_reset.sh                  # reset to the start state + start v1.0.0 on staging (8101) / production (8100)
```

## 2. How to run

```bash
export DEMO_APPROVER="Gildong Hong (Ops Lead)"     # the name written to the approval records (the OS user if omitted)
copilot --allow-tool=write --allow-tool=shell --deny-tool='shell(git push)' \
        --allow-url=http://127.0.0.1:8100 --allow-url=http://127.0.0.1:8101
```

- The principle of this demo is **routine work is auto-approved; risky work is blocked or sent for approval by the system.** So file writes and shell commands are allowed up front,
  and risky actions (editing code before approval, editing the standards documents, `git push`, production deployment, etc.) are blocked by the hook in `.github/hooks/guardrails.json`.
- On the first launch, Copilot asks whether you trust the folder. **You must trust the demo folder** for `.github/agents` and `.github/hooks` to load.
- Pick an agent with `/agent`, or select it directly, for example `/agent change-analyst`.
- To use a different model, change it with `/model`. The flow is the same as in the video, but the wording and elapsed time may differ.

## 3. Demo script (type exactly as shown)

| Step | Agent | What to type | What the human does |
|---|---|---|---|
| 1 Analysis | `change-analyst` | `Analyze the impact of change request CR-2026-014 (docs/requirements/CR-2026-014.md).` | Read the 5-line summary and the decisions needed |
| 2 Design | `solution-architect` | `Design this based on the impact analysis. Ask me about any decisions that need to be made.` | Answer the questions (up to 3): pick the recommended option, or type your own answer with **Other** → **Yes on the ① Design approval pop-up** |
| 3 Implementation | `app-developer` | `Implement the approved design.` | (Automatic) |
| 4 Testing | `qa-engineer` | `Write and run tests that verify the implemented changes.` | (Automatic) |
| 5 Review | `code-reviewer` | `Review the changes. If there are no problems, request code approval.` | **Yes on the ② Code approval pop-up** |
| 6 Deployment | `release-manager` | `Merge into main, deploy to staging and verify, then proceed to the production deployment.` | **Yes on the ③ Production deploy approval pop-up** |
| 7 Operations | `ops-analyst` | (first) `!.venv/bin/python scripts/simulate_traffic.py http://127.0.0.1:8100 --count 150` → `Analyze the production logs and DB and write an operations report.` | Read the 'Business decision needed' items of the operations report |

- The design stage asks up to 3 decisions. In the video, the legacy-app decision was answered with **Other** instead of the recommended option
  (`Allow legacy app versions (3.1–3.3) to omit the reason until 2026-12-01 with a warning log, then make it required.`), and the other decisions with the recommended option (Enter).
- Stage outputs are saved as `docs/cr/CR-2026-014/01~07-*.md`, approval records as `approvals/CR-2026-014/*.json`, and every tool call is logged in `.copilot-audit/audit.jsonl`.
- Total time: about 38 minutes in a real run (including waiting time). Check the AI usage in `Session: N AIC used` at the bottom of the session. (1 AI Credit = $0.01)
- Result screens: the customer screen and the admin console are at `http://127.0.0.1:8100` (production), and the pre-check is at `http://127.0.0.1:8101` (staging).
  The admin token is `demo-admin-token`, which is already filled in on the screen.

## 4. Guardrail demo (optional)

Check that the system blocks risky actions even when an agent that does not know the rules tries them.

```bash
./scripts/demo_reset.sh
# Temporarily add the demo agent, then run without the repository instructions
cp docs/demo/quick-fixer.agent.md.example .github/agents/quick-fixer.agent.md
copilot --no-custom-instructions --allow-tool=write --allow-tool=shell
```

Select `/agent quick-fixer`, then enter these in order: ① `Change the 30-day constant in app/services/refund_policy.py to 60.`
② `Add an item 'S8 · Review dependency updates monthly' at the bottom of docs/standards/security-checklist.md.` ③ `Push to main right now with git push origin main, without a review.`
Each one is blocked with **Denied by preToolUse hook**. (After the demo, `./scripts/demo_reset.sh` returns everything to the start state and also deletes `quick-fixer.agent.md`.)

> A normal agent (one that reads the repository instructions) refuses such requests on its own. Even this demo agent may refuse a request that is plainly harmful (for example, weakening the standards): that is why request ② is a harmless addition, so that you see the hook, not the model, stop it.
> This demo deliberately uses an agent that does not know the rules, to show that **the hook blocks the action regardless of what the AI decides**.

## 5. Layout

```
.github/
  copilot-instructions.md       # Shared repository instructions (English responses, output locations, approval rules, scope control)
  agents/*.agent.md             # 7 custom agents (role · tool permissions · work instructions · per-role hook)
  hooks/guardrails.json         # Global hook (preToolUse → scripts/hooks/guard.py)
  instructions/                 # Path-specific instructions (for example db/migrations)
  workflows/                    # CI / Deploy samples for a real environment (Environment approval)
scripts/
  hooks/guard.py                # Per-role write scope · blocking of risky commands · enforced approval pop-ups · audit log
  gate.py                       # Approval (gate) records — bound to the hash of the design document/code, so they become invalid if it changes
  deploy.sh                     # staging/production deployment (backup → migration → swap → health check → smoke test → rollback)
  demo_reset.sh, bootstrap_env.sh, simulate_traffic.py, smoke_test.py, migrate.py, seed.py
app/ db/ tests/ docs/           # Service code, migrations, tests, requirements · policy · standards · stage outputs, and docs/demo (example files for the demo)
```

Write scope per role (enforced by the hook)

| Agent | Where it can write |
|---|---|
| change-analyst · solution-architect · code-reviewer · ops-analyst | `docs/cr/` only |
| app-developer | `app/` `db/migrations/` `tests/` `docs/policy/` `docs/cr/` (`app/` and `db/migrations/` cannot be modified before design approval) |
| qa-engineer | `tests/` `docs/cr/` |
| release-manager | `docs/cr/` `VERSION` (production deployment always shows an approval pop-up) |

## 6. Moving to a real environment

| This demo | A real organization |
|---|---|
| `gate.py` approval records | GitHub **PR approval / branch protection**; for design approval, an issue or document approval workflow |
| `deploy.sh production` + approval pop-up | GitHub **Environments (Required reviewers)** + Actions, deployment to Azure (Container Apps/AKS) |
| `guard.py` hook | Repository hooks + administrator **managed settings** (`permissions.deny/ask/allow`, no allow-all, enforced sandbox, MCP allowlist), policy hooks |
| Local audit log | Copilot **OpenTelemetry** monitoring, organization audit log / usage metrics |

References: GitHub Docs — Copilot CLI, Custom agents, Hooks, Managed settings (docs.github.com/copilot)

## 7. Troubleshooting

- `Address already in use` (8100/8101): `./scripts/demo_reset.sh` cleans up the previous services.
- If the approval pop-up appears twice, `ask` in `scripts/hooks/guard.py` must be returned only from the global (`--role global`) hook.
- If an agent cannot write a file, check the hook's denial reason (`Denied by preToolUse hook: …`). In most cases the stage is before an approval, or the write is outside the allowed scope.
- If the agents/hooks are not loaded, check that the folder is trusted and that you launched `copilot` from the repository root.
- To run the demo again while approval records (`approvals/`) remain, run `./scripts/demo_reset.sh` first.
