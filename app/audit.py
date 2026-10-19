"""Audit log: records who did what and when in the audit_log table."""

import json

from . import clock


def log(db, actor: str, action: str, detail: dict | None = None) -> None:
    db.execute(
        "INSERT INTO audit_log (at, actor, action, detail) VALUES (?, ?, ?, ?)",
        (clock.now().isoformat(), actor, action, json.dumps(detail or {}, ensure_ascii=False)),
    )
