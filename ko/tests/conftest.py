import sqlite3
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import clock
from app.main import app
from scripts.migrate import apply_migrations

TODAY = date(2026, 10, 16)
NOW = datetime(2026, 10, 16, 3, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch):
    monkeypatch.setattr(clock, "today", lambda: TODAY)
    monkeypatch.setattr(clock, "now", lambda: NOW)


@pytest.fixture()
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", path)
    apply_migrations(path)
    return path


@pytest.fixture()
def client(db_path):
    return TestClient(app)


@pytest.fixture()
def query(db_path):
    def _query(sql, params=()):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
        conn.close()
        return rows

    return _query


@pytest.fixture()
def make_customer(db_path):
    def _make(name="테스트고객", tier="STANDARD", email="test@example.com"):
        conn = sqlite3.connect(db_path)
        cur = conn.execute(
            "INSERT INTO customers (name, email, tier, created_at) VALUES (?, ?, ?, ?)",
            (name, email, tier, NOW.isoformat()),
        )
        conn.commit()
        conn.close()
        return cur.lastrowid

    return _make


@pytest.fixture()
def make_order(db_path):
    def _make(customer_id, amount=100_000, days_ago=1, status="DELIVERED"):
        ordered_at = (TODAY - timedelta(days=days_ago)).isoformat()
        conn = sqlite3.connect(db_path)
        cur = conn.execute(
            "INSERT INTO orders (customer_id, total_amount, status, ordered_at)"
            " VALUES (?, ?, ?, ?)",
            (customer_id, amount, status, ordered_at),
        )
        conn.commit()
        conn.close()
        return cur.lastrowid

    return _make


@pytest.fixture()
def admin_headers():
    return {"X-Admin-Token": "demo-admin-token"}
