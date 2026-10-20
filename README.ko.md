# ShopFlow Orders × GitHub Copilot CLI · Custom Agent 데모 저장소

> - 이 문서는 **한국어판 안내**입니다.
> - 기본(영어) 문서는 [README.md](README.md) 입니다.
> - 한국어로 동작하는 데모(에이전트·문서·화면이 모두 한국어)는 **`ko` 브랜치**에 있으며 `git clone -b ko https://github.com/junwoojeong100/ghcp_cli_workflow_shopflow_orders.git shopflow-orders` 로 받습니다.

가상 쇼핑몰 **ShopFlow의 주문·환불 서비스**(Python · FastAPI · SQLite)에 현업의 변경 요청 **CR-2026-014**(VIP 환불 정책 개선)가 들어왔을 때,
**GitHub Copilot CLI + Custom Agent 7종**이 분석 → 설계 → 구현 → 테스트 → 리뷰 → 배포 → 운영 분석을 처리하고,
**사람은 3곳(설계 · 코드 · 운영 배포)에서만 승인**하는 워크플로우를 그대로 재현합니다.

> 이 저장소의 모든 데이터·고객·회사는 가상입니다. staging / production 은 로컬 포트(8101 / 8100)로 시뮬레이션합니다.
> `./scripts/demo_reset.sh` 는 저장소를 `baseline-ko` 태그 상태로 되돌립니다. **커밋하지 않은 변경은 모두 삭제**되니 시연용 복사본에서 실행하세요.

## ghcp_cli_workflow 시리즈 — 2개 저장소를 함께 씁니다

| 저장소 | 역할 |
|---|---|
| **[ghcp_cli_workflow_shopflow_orders](https://github.com/junwoojeong100/ghcp_cli_workflow_shopflow_orders)** (이 저장소) | **시연 대상** — 데모 앱 · Custom Agent 7종 · Hook · CI/Deploy 예시. 아래 스크립트로 같은 흐름을 직접 재현 |
| **[ghcp_cli_workflow_demo_kit](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit)** | **발표 키트** — 발표 가이드 · 영상/PPT 제작 소스 · 녹화 세션의 실제 산출물(`sample-output/`). **한국어판 자료는 [`ko/` 폴더](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit/tree/main/ko)**, 발표 자료(PPTX)·영상(MP4)은 [Releases](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit/releases) |

발표 키트의 도구는 이 저장소를 **`shopflow-orders`** 폴더 이름으로 찾습니다. 키트 안에서 함께 쓰려면 이름을 지정해 clone 하세요(아래 1장).

**다운로드 없이 브라우저에서 바로 보기:** 한국어판 [전체 영상](https://junwoojeong100.github.io/ghcp_cli_workflow_demo_kit/ko/video/GHCP_CLI_Workflow_Demo_KO.mp4) · [발표 자료](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fjunwoojeong100.github.io%2Fghcp_cli_workflow_demo_kit%2Fko%2FGHCP_CLI_Workflow_Demo_KO.pptx) — 영어판 [전체 영상](https://junwoojeong100.github.io/ghcp_cli_workflow_demo_kit/video/GHCP_CLI_Workflow_Demo_EN.mp4) · [발표 자료](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fjunwoojeong100.github.io%2Fghcp_cli_workflow_demo_kit%2FGHCP_CLI_Workflow_Demo_EN.pptx). 단계별 클립과 챕터 링크는 [발표 키트 README](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit/blob/main/README.ko.md#브라우저에서-바로-보기--다운로드-없이)에 있습니다.

태그: `baseline-ko` = 데모 시작 상태(`demo_reset.sh` 가 되돌아가는 기준), `baseline-recorded-ko` = 영상을 녹화할 때의 시작 상태입니다.
둘의 차이는 `scripts/` 코드 포맷(ruff, 동작 동일), `deploy.yml` 의 YAML 따옴표 수정(1줄), `.gitignore` · README 뿐이며, 발표 키트의 `sample-output/full-change.diff` 는 `baseline-recorded-ko` 기준입니다.

## 0. 이 데모로 확인한 것 (녹화 세션 실측)

| 항목 | 결과 |
|---|---|
| 요건 → 운영 분석까지 실제 소요 | 약 **38분** (분석 2.5 · 설계 3.8 · 구현 6.1 · 테스트 5.1 · 리뷰 4.1 · 배포 6.8 · 운영 9.2분, 사람의 응답 시간 포함) |
| 사람의 개입 | **6번** = 승인 3곳(설계 · 코드 · 운영 배포) + 설계 단계의 결정 3건 |
| 변경 규모 | 앱·DB 8개 파일 +142줄(구현 단계), 테스트 26 → 82(구현) → **117**(QA), 커버리지 99% |
| 리뷰 결과 | 치명 0 · 중대 0 · 경미 1 |
| AI 사용량 | 세션 전체 약 **454 AI Credits** (1 Credit = $0.01 → 약 $4.5) |
| 감사 기록 | 도구 호출 231건, 승인 요청 3건, 차단 0건(본 시연) / 안전장치 시연에서 3건 차단 |

검증 환경: macOS, GitHub Copilot CLI 1.0.98, 녹화 당시 기본 모델(GPT-6.1 Sol). 모델·요금제에 따라 소요 시간과 사용량은 달라집니다.
녹화 세션의 실제 산출물은 발표 키트 저장소([ghcp_cli_workflow_demo_kit](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit))의 한국어판 폴더 [`ko/`](https://github.com/junwoojeong100/ghcp_cli_workflow_demo_kit/tree/main/ko) 의 `sample-output/` 에 보관되어 있습니다.

## 1. 준비물

| 항목 | 설명 |
|---|---|
| GitHub Copilot | 개인 또는 조직(Business/Enterprise) 라이선스, 조직 정책에서 Copilot CLI 허용 |
| Copilot CLI | `npm install -g @github/copilot` · `brew install --cask copilot-cli` · `winget install GitHub.Copilot` → `copilot` 실행 후 `/login` |
| 도구 | Python 3.12, git, sqlite3, jq, curl, lsof (macOS / Linux) |

```bash
git clone -b ko https://github.com/junwoojeong100/ghcp_cli_workflow_shopflow_orders.git shopflow-orders   # 한국어판(ko 브랜치) · 폴더 이름을 shopflow-orders 로 (발표 키트 도구의 기본 경로)
cd shopflow-orders
python3.12 -m venv --copies .venv        # --copies: 가상환경 python 을 복사해 경로 권한 팝업을 줄입니다
./.venv/bin/pip install -r requirements.txt
./scripts/demo_reset.sh                  # 시작 상태로 초기화 + staging(8101)/production(8100)에 v1.0.0 가동
```

## 2. 실행 방법

```bash
export DEMO_APPROVER="홍길동 책임(운영 담당)"     # 승인 기록에 남는 이름(생략하면 OS 사용자)
copilot --allow-tool=write --allow-tool=shell --deny-tool='shell(git push)' \
        --allow-url=http://127.0.0.1:8100 --allow-url=http://127.0.0.1:8101
```

- **일상 작업은 자동 승인, 위험 작업은 시스템이 차단/승인 요청**이 이 데모의 원칙입니다. 그래서 파일 쓰기·셸 실행은 미리 허용하고,
  위험한 행동(승인 전 코드 수정, 표준 문서 수정, `git push`, 운영 배포 등)은 `.github/hooks/guardrails.json` 의 Hook 이 막습니다.
- 처음 열면 폴더 신뢰(trust) 확인이 나옵니다. **데모 폴더를 신뢰해야** `.github/agents` 와 `.github/hooks` 가 로드됩니다.
- 에이전트는 `/agent` 로 고르거나 `/agent change-analyst` 처럼 바로 지정합니다.
- 다른 모델을 쓰려면 `/model` 로 변경합니다. 영상과 같은 흐름이 나오지만 문구·소요 시간은 달라질 수 있습니다.

## 3. 시연 스크립트 (그대로 입력)

| 단계 | 에이전트 | 입력할 말 | 사람이 하는 일 |
|---|---|---|---|
| 1 분석 | `change-analyst` | `CR-2026-014 변경 요청서(docs/requirements/CR-2026-014.md)의 영향도를 분석해줘.` | 5줄 요약과 결정 필요 사항을 읽는다 |
| 2 설계 | `solution-architect` | `분석서를 바탕으로 설계해줘. 결정이 필요한 건 나에게 물어봐줘.` | 질문 3개에 답한다(추천안 선택, 또는 **Other** 로 직접 입력) → **① 설계 승인 팝업에서 Yes** |
| 3 구현 | `app-developer` | `승인된 설계대로 구현해줘.` | (자동) |
| 4 테스트 | `qa-engineer` | `구현된 변경을 검증하는 테스트를 작성하고 실행해줘.` | (자동) |
| 5 리뷰 | `code-reviewer` | `변경 사항을 리뷰해줘. 문제가 없으면 코드 승인을 요청해줘.` | **② 코드 승인 팝업에서 Yes** |
| 6 배포 | `release-manager` | `main에 병합하고 staging에 배포해서 검증한 뒤, 운영 배포까지 진행해줘.` | **③ 운영 배포 승인 팝업에서 Yes** |
| 7 운영 | `ops-analyst` | (먼저) `!.venv/bin/python scripts/simulate_traffic.py http://127.0.0.1:8100 --count 150` → `운영 환경 로그와 DB를 분석해서 운영 리포트를 작성해줘.` | 운영 리포트의 '현업 결정 필요 사항'을 읽는다 |

- 영상 속 설계 단계의 결정은 3건이었습니다. 구버전 앱 처리는 추천안 대신 **Other** 로 직접 입력했고
  (`구앱(3.1~3.3)은 2026-12-01까지 사유 누락을 허용하고 경고 로그를 남기며, 이후 필수로 전환한다`), 나머지 2건은 추천안(Enter)을 선택했습니다.
- 단계별 산출물은 `docs/cr/CR-2026-014/01~07-*.md`, 승인 기록은 `approvals/CR-2026-014/*.json`, 모든 도구 호출은 `.copilot-audit/audit.jsonl` 에 남습니다.
- 전체 소요: 실제 약 30~40분(대기 시간 포함), AI 사용량은 세션 하단의 `Session: N AIC used` 에서 확인합니다. (1 AI Credit = $0.01)
- 결과 화면: 고객 화면/관리자 콘솔은 `http://127.0.0.1:8100` (production), 사전 확인은 `http://127.0.0.1:8101` (staging).
  관리자 토큰은 화면에 입력된 `demo-admin-token` 입니다.

## 4. 안전장치 시연 (선택)

규칙을 모르는 에이전트가 위험한 일을 시도해도 시스템이 막는지 확인합니다.

```bash
./scripts/demo_reset.sh
# 시연용 에이전트를 임시로 추가한 뒤, 저장소 지침 없이 실행합니다
cp docs/demo/quick-fixer.agent.md.example .github/agents/quick-fixer.agent.md
copilot --no-custom-instructions --allow-tool=write --allow-tool=shell
```

`/agent quick-fixer` 를 고른 뒤 ① `app/services/refund_policy.py 의 30일 상수를 60으로 바꿔줘`
② `docs/standards/security-checklist.md 에 항목을 추가해줘` ③ `git push origin main 으로 올려줘` 를 차례로 입력하면
각각 **Denied by preToolUse hook** 으로 차단됩니다. (사용 후 `./scripts/demo_reset.sh` 로 되돌리면 `quick-fixer.agent.md` 도 함께 삭제됩니다)

> 평소의 에이전트(저장소 지침을 읽는 에이전트)는 이런 요청을 스스로 거절합니다.
> 이 시연은 **AI의 판단과 무관하게 Hook 이 막는다**는 점을 보이려고 일부러 규칙을 모르는 에이전트를 씁니다.

## 5. 구성

```
.github/
  copilot-instructions.md       # 저장소 공통 지침 (한국어 응답, 산출물 위치, 승인 규칙, 범위 통제)
  agents/*.agent.md             # Custom Agent 7종 (역할 · 도구 권한 · 작업 지침 · 역할별 Hook)
  hooks/guardrails.json         # 전역 Hook (preToolUse → scripts/hooks/guard.py)
  instructions/                 # 경로별 지침 (예: db/migrations)
  workflows/                    # 실제 환경용 CI / Deploy(Environment 승인) 예시
scripts/
  hooks/guard.py                # 역할별 쓰기 범위 · 위험 명령 차단 · 승인 팝업 강제 · 감사 로그
  gate.py                       # 승인(Gate) 기록 — 설계서/코드의 해시와 묶여 변경되면 무효
  deploy.sh                     # staging/production 배포(백업 → 마이그레이션 → 교체 → 헬스체크 → 스모크 → 롤백)
  demo_reset.sh, bootstrap_env.sh, simulate_traffic.py, smoke_test.py, migrate.py, seed.py
app/ db/ tests/ docs/           # 서비스 코드, 마이그레이션, 테스트, 요건·정책·표준·단계별 산출물, docs/demo(시연용 예시 파일)
```

역할별 쓰기 범위(Hook 이 강제)

| 에이전트 | 쓸 수 있는 곳 |
|---|---|
| change-analyst · solution-architect · code-reviewer · ops-analyst | `docs/cr/` 만 |
| app-developer | `app/` `db/migrations/` `tests/` `docs/policy/` `docs/cr/` (설계 승인 전에는 `app/` `db/migrations/` 수정 불가) |
| qa-engineer | `tests/` `docs/cr/` |
| release-manager | `docs/cr/` `VERSION` (운영 배포는 항상 승인 팝업) |

## 6. 실제 환경으로 옮길 때

| 이 데모 | 실제 조직 |
|---|---|
| `gate.py` 승인 기록 | GitHub **PR 승인 / 브랜치 보호**, 설계 승인은 이슈·문서 승인 워크플로우 |
| `deploy.sh production` + 승인 팝업 | GitHub **Environments(Required reviewers)** + Actions, Azure(Container Apps/AKS) 배포 |
| `guard.py` Hook | 저장소 Hook + 관리자 **managed settings**(`permissions.deny/ask/allow`, allow-all 금지, 샌드박스 강제, MCP 허용목록), 정책 Hook |
| 로컬 감사 로그 | Copilot **OpenTelemetry** 모니터링, 조직 감사 로그/사용량 지표 |

참고 문서: GitHub Docs — Copilot CLI, Custom agents, Hooks, Managed settings (docs.github.com/copilot)

## 7. 문제 해결

- `Address already in use`(8100/8101): `./scripts/demo_reset.sh` 가 이전 서비스를 정리합니다.
- 승인 팝업이 두 번 나오면 `scripts/hooks/guard.py` 의 `ask` 는 전역(`--role global`) 훅에서만 반환해야 합니다.
- 에이전트가 파일을 못 쓰면 Hook 거부 사유(`Denied by preToolUse hook: …`)를 확인하세요. 대부분 승인 전 단계이거나 쓰기 범위를 벗어난 경우입니다.
- 에이전트/Hook 이 로드되지 않으면 폴더 신뢰(trust) 여부와 `copilot` 실행 위치(저장소 루트)를 확인하세요.
- 승인 기록(`approvals/`)이 남은 상태에서 다시 시연하려면 먼저 `./scripts/demo_reset.sh` 를 실행하세요.
