# ShopFlow Orders & Refunds Service — System Overview

## Components
| Component | Description |
|---|---|
| API server (`app/`) | FastAPI. Provides the customer, order, refund and admin APIs and the static web screen (`app/static`) |
| DB (`data/orders.db`) | SQLite. The schema is managed with `db/migrations/*.sql` and applied with `scripts/migrate.py` |
| Notifications | `notifications` table (send queue). The actual e-mail sending is done by a separate worker (outside this repository) |
| Audit log | `audit_log` table. History of refund requests, approvals and rejections |
| Access log | JSON Lines (`logs/app.log`, or `.deploy/<env>/logs/app.log` for each environment) |

## Clients
| Client | Notes |
|---|---|
| Web screen | `app/static/index.html` in this repository — deployed together with the server, so it is always the latest |
| **Mobile apps 3.1–3.3** | Distributed through the app stores. Users take weeks to update, and the app **sends only `amount` when requesting a refund** |
| Admin console | The 'Admin console' tab of the web screen (authenticated with the `X-Admin-Token` header) |

## Main APIs
| Method/path | Description |
|---|---|
| `GET /customers`, `GET /customers/{id}`, `GET /customers/{id}/orders` | Look up customers and orders |
| `POST /orders`, `GET /orders/{id}` | Create and look up orders |
| `POST /orders/{id}/refund` | Refund request — `APPROVED` immediately if the rules pass; `REQUESTED` (manual admin approval) if the order is in delivery (`SHIPPED`) |
| `GET /admin/refunds?status=`, `POST /admin/refunds/{id}/approve\|reject` | Admin refund handling |
| `GET /health` | Health check (used by the smoke test after deployment) |

## Environments
| Environment | Port | Purpose |
|---|---|---|
| local | 8000 | Development |
| staging | 8101 | Verification before release (automatic deployment allowed) |
| production | 8100 | Live service (owner approval required) |

## Data notes
- Customer tier (`customers.tier`) may be written inconsistently because of legacy migration history.
- Amounts are integers in KRW (won), and dates are `YYYY-MM-DD` in UTC.
