-- 001: 초기 스키마 (고객, 주문, 환불, 감사 로그, 알림 대기열)
CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  tier TEXT,                       -- STANDARD | VIP (레거시 이관 데이터는 표기가 섞여 있을 수 있음)
  created_at TEXT NOT NULL
);

CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  total_amount INTEGER NOT NULL,   -- 원(KRW)
  status TEXT NOT NULL,            -- PAID | SHIPPED | DELIVERED | CANCELLED
  ordered_at TEXT NOT NULL         -- YYYY-MM-DD (UTC)
);

CREATE TABLE refunds (
  id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  amount INTEGER NOT NULL,
  status TEXT NOT NULL,            -- REQUESTED | APPROVED | REJECTED
  requested_at TEXT NOT NULL,
  decided_at TEXT
);

CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  detail TEXT
);

CREATE TABLE notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  channel TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_refunds_order ON refunds(order_id);
