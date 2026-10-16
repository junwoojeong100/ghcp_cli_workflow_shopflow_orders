"""감사 로그: 누가 언제 무엇을 했는지 audit_log 테이블에 남긴다."""

import json

from . import clock


def log(db, actor: str, action: str, detail: dict | None = None) -> None:
    db.execute(
        "INSERT INTO audit_log (at, actor, action, detail) VALUES (?, ?, ?, ?)",
        (clock.now().isoformat(), actor, action, json.dumps(detail or {}, ensure_ascii=False)),
    )
