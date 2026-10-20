"""SQLite 연결 관리."""

import sqlite3

from . import config


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """FastAPI 의존성: 요청 단위로 연결을 열고, 성공하면 커밋, 실패하면 롤백한다."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
