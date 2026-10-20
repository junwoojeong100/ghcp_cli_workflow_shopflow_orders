import sqlite3

from scripts.seed import seed


def test_seed_creates_demo_data(db_path):
    seed(db_path)
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 12
    assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 20
    conn.close()


def test_seed_is_idempotent(db_path):
    seed(db_path)
    seed(db_path)
    conn = sqlite3.connect(db_path)
    assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 12
    conn.close()
