# ShopFlow 주문·환불 서비스 — 시스템 개요

## 구성
| 구성요소 | 설명 |
|---|---|
| API 서버 (`app/`) | FastAPI. 고객·주문·환불·관리자 API, 정적 웹 화면(`app/static`) 제공 |
| DB (`data/orders.db`) | SQLite. 스키마는 `db/migrations/*.sql` 로 관리, `scripts/migrate.py` 로 적용 |
| 알림 | `notifications` 테이블(발송 대기열). 실제 이메일 발송은 별도 워커(본 저장소 범위 밖) |
| 감사 로그 | `audit_log` 테이블. 환불 접수·승인·반려 이력 |
| 접근 로그 | JSON Lines (`logs/app.log` 또는 환경별 `.deploy/<env>/logs/app.log`) |

## 클라이언트
| 클라이언트 | 비고 |
|---|---|
| 웹 화면 | 이 저장소의 `app/static/index.html` — 서버와 함께 배포되어 항상 최신 |
| **모바일 앱 3.1 ~ 3.3** | 앱스토어 배포. 사용자 업데이트에 수 주가 걸리며 **환불 요청 시 `amount`만 전송**한다 |
| 관리자 콘솔 | 웹 화면의 '관리자 콘솔' 탭 (`X-Admin-Token` 헤더 인증) |

## 주요 API
| 메서드/경로 | 설명 |
|---|---|
| `GET /customers`, `GET /customers/{id}`, `GET /customers/{id}/orders` | 고객·주문 조회 |
| `POST /orders`, `GET /orders/{id}` | 주문 생성·조회 |
| `POST /orders/{id}/refund` | 환불 요청 — 규칙 통과 시 즉시 `APPROVED`, 배송 중(`SHIPPED`)이면 `REQUESTED`(관리자 수동 승인) |
| `GET /admin/refunds?status=`, `POST /admin/refunds/{id}/approve\|reject` | 관리자 환불 처리 |
| `GET /health` | 상태 확인 (배포 후 스모크 테스트에서 사용) |

## 환경
| 환경 | 포트 | 용도 |
|---|---|---|
| local | 8000 | 개발 |
| staging | 8101 | 배포 전 검증 (자동 배포 가능) |
| production | 8100 | 실서비스 (담당자 승인 필요) |

## 데이터 메모
- 고객 등급(`customers.tier`)은 레거시 이관 이력 때문에 표기가 일정하지 않을 수 있다.
- 금액 단위는 원(KRW) 정수, 날짜는 UTC 기준 `YYYY-MM-DD` 이다.
