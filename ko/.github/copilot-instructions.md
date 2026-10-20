# ShopFlow 주문·환불 서비스 — Copilot 작업 지침

## 프로젝트
- Python 3.12 + FastAPI + SQLite. 구조: `app/`(routers, services, static), `db/migrations/`, `tests/`, `docs/`, `scripts/`
- 테스트: `.venv/bin/pytest -q` · 린트/포맷: `.venv/bin/ruff check . && .venv/bin/ruff format .`
- 사내 표준: `docs/standards/` (코딩 · 보안 점검표 · DB 마이그레이션 · 릴리스 정책)을 항상 따른다.

## 작업 방식 (모든 에이전트 공통)
1. 응답과 문서는 **한국어**로 쓴다. 현업이 읽는 요약을 먼저, 기술 상세는 뒤에 둔다. (코드 식별자는 영어)
2. 변경 요청(CR)의 단계별 산출물은 `docs/cr/<CR-ID>/` 에 번호 순서로 남긴다.
   `01-impact-analysis` → `02-design` → `03-implementation-notes` → `04-test-report` → `05-review-report` → `06-release-plan` → `07-ops-report` (모두 `.md`)
3. **사람 승인 3곳**: ① 설계 승인 ② 코드 승인 ③ 운영 배포 승인. 승인은 `scripts/gate.py request …` 또는 `scripts/deploy.sh production` 실행 시 사람에게 요청되며, 승인 없이 다음 단계로 넘어가지 않는다. `approvals/` 와 승인된 산출물은 직접 수정하지 않는다.
4. 사실만 쓴다. 확인하지 못한 것은 추측하지 말고 "확인 필요"로 표시하고 근거(파일·줄)를 함께 적는다.
5. 금지: 시크릿 출력, 운영 데이터 직접 수정, `git push`, 보호 경로(`.github/agents`, `.github/hooks`, `scripts/`, `docs/standards`, `docs/requirements`, `approvals/`) 수정.
6. 훅(Guardrail)이 도구 호출을 거부하면 우회하지 말고, 거부 사유를 사용자에게 한 줄로 설명한 뒤 다음 행동을 제안한다.
7. **범위 통제**: 변경 요청서(CR)에 없는 요구는 분석·설계·구현 범위에 넣지 않는다. 필요해 보이면 '후속 과제'로 한 줄만 적고, 항상 **요구사항을 충족하는 가장 단순한 방법**을 택한다. 외부 확인이 필요한 사항은 배포를 막는 조건이 아니라 '배포 전 체크리스트' 항목으로 적는다.
8. **분량 규칙**: 단계별 문서는 **A4 3쪽(약 90줄) 이내, 표 중심**으로 쓴다. 영향 범위 표는 핵심 10행 이내(같은 영역은 합친다), 결정 필요 사항은 중요도 순 **최대 5개**, 근거는 `파일:줄` 한 곳만. 마지막 채팅 응답은 **6줄 이내**로 요약한다.
