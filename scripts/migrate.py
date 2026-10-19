"""DB migration runner: applies db/migrations/*.sql in numeric order, once each."""

import sqlite3
import sys
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parent.parent / "db" / "migrations"


def apply_migrations(db_path: str) -> list[str]:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations"
        " (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
    )
    done = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    applied = []
    for sql_file in sorted(MIGRATIONS.glob("*.sql")):
        if sql_file.stem in done:
            continue
        conn.executescript(sql_file.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'))",
            (sql_file.stem,),
        )
        conn.commit()
        applied.append(sql_file.stem)
    conn.close()
    return applied


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/orders.db"
    applied = apply_migrations(target)
    print(f"migrations applied: {', '.join(applied) if applied else '(none, already up to date)'}")
