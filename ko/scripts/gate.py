#!/usr/bin/env python3
"""승인(Gate) 기록 관리자.

  gate.py request <design|code> [CR-ID]   사람이 승인하면 approvals/<CR>/<gate>.json 기록
  gate.py verify  <design|code|staging> [CR-ID]   기록이 유효한지(승인 후 산출물 변경 없음) 검증
  gate.py record-env <staging|production> <version> [CR-ID]   배포 결과 기록 (deploy.sh 가 호출)
  gate.py status [CR-ID]   승인 현황 표시

'request' 는 훅(scripts/hooks/guard.py)이 항상 사람에게 확인을 요청하도록 강제한다.
즉 이 기록은 사람이 승인 프롬프트에서 Yes 를 눌러야만 생성된다.
"""

import getpass
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("DEMO_REPO_ROOT") or Path(__file__).resolve().parent.parent)
DEFAULT_CR = os.environ.get("DEMO_CR", "CR-2026-014")
CODE_GLOBS = ["app/**/*.py", "app/static/*", "db/migrations/*.sql"]
GATE_TITLES = {"design": "① 설계 승인", "code": "② 코드 승인", "production": "③ 운영 배포 승인"}


def approver() -> str:
    return os.environ.get("DEMO_APPROVER") or getpass.getuser()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_hash() -> str:
    digest = hashlib.sha256()
    files = sorted({p for pattern in CODE_GLOBS for p in ROOT.glob(pattern) if p.is_file()})
    for path in files:
        if "__pycache__" in path.parts:
            continue
        digest.update(str(path.relative_to(ROOT)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def design_doc(cr: str) -> Path:
    return ROOT / "docs" / "cr" / cr / "02-design.md"


def record_path(cr: str, gate: str) -> Path:
    return ROOT / "approvals" / cr / f"{gate}.json"


def write_record(cr: str, gate: str, data: dict) -> Path:
    path = record_path(cr, gate)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cr": cr,
        "gate": gate,
        "at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    payload.update(data)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def read_record(cr: str, gate: str):
    path = record_path(cr, gate)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def verify(gate: str, cr: str) -> tuple[bool, str]:
    rec = read_record(cr, gate)
    if rec is None:
        return False, f"'{gate}' 승인 기록이 없습니다."
    if gate == "design":
        doc = design_doc(cr)
        if not doc.exists():
            return False, "설계서가 없습니다."
        if rec.get("sha256") != sha256_file(doc):
            return False, "승인 이후 설계서가 변경되어 승인이 무효입니다. 다시 승인받으세요."
        return True, f"설계 승인 유효 (승인자 {rec['approver']}, {rec['at']})"
    if gate in ("code", "staging"):
        if rec.get("code_sha256") != code_hash():
            return False, f"승인/검증 이후 코드가 변경되어 '{gate}' 기록이 무효입니다."
        return True, f"'{gate}' 기록 유효 ({rec.get('approver', 'system')}, {rec['at']})"
    return True, "기록 존재"


def cmd_request(gate: str, cr: str) -> int:
    if gate == "design":
        doc = design_doc(cr)
        if not doc.exists():
            print(f"✗ 설계서가 없습니다: {doc.relative_to(ROOT)}")
            return 1
        data = {"artifact": str(doc.relative_to(ROOT)), "sha256": sha256_file(doc)}
    elif gate == "code":
        missing = [
            n
            for n in ("04-test-report.md", "05-review-report.md")
            if not (ROOT / "docs" / "cr" / cr / n).exists()
        ]
        if missing:
            print(f"✗ 코드 승인 전에 필요한 산출물이 없습니다: {', '.join(missing)}")
            return 1
        data = {"artifact": "app/ + db/migrations/", "code_sha256": code_hash()}
    else:
        print(
            "✗ request 는 design | code 만 지원합니다. (운영 배포 승인은 deploy.sh production 실행 시점에 받습니다)"
        )
        return 1
    data["approver"] = approver()
    path = write_record(cr, gate, data)
    print(f"✔ {GATE_TITLES[gate]} 기록 완료 — 승인자: {data['approver']}")
    print(f"  기록 파일: {path.relative_to(ROOT)}")
    print(
        f"  무결성 해시: {(data.get('sha256') or data.get('code_sha256'))[:16]}…  (승인 후 변경되면 무효)"
    )
    return 0


def cmd_verify(gate: str, cr: str) -> int:
    ok, message = verify(gate, cr)
    print(("✔ " if ok else "✗ ") + message)
    return 0 if ok else 1


def cmd_record_env(env: str, version: str, cr: str) -> int:
    data = {
        "version": version,
        "code_sha256": code_hash(),
        "approver": approver() if env == "production" else "system",
    }
    write_record(cr, env, data)
    print(f"✔ {env} 배포 기록 저장 (v{version})")
    return 0


def cmd_status(cr: str) -> int:
    print(f"승인 현황 — {cr}")
    for gate in ("design", "code", "staging", "production"):
        rec = read_record(cr, gate)
        if rec is None:
            print(f"  {gate:<11} ✗ 기록 없음")
            continue
        ok, message = verify(gate, cr) if gate != "production" else (True, "")
        mark = "✔" if ok else "⚠"
        print(
            f"  {gate:<11} {mark} {rec.get('approver', 'system')} · {rec['at']}  {message if not ok else ''}"
        )
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "request" and len(argv) >= 3:
        return cmd_request(argv[2], argv[3] if len(argv) > 3 else DEFAULT_CR)
    if cmd == "verify" and len(argv) >= 3:
        return cmd_verify(argv[2], argv[3] if len(argv) > 3 else DEFAULT_CR)
    if cmd == "record-env" and len(argv) >= 4:
        return cmd_record_env(argv[2], argv[3], argv[4] if len(argv) > 4 else DEFAULT_CR)
    if cmd == "status":
        return cmd_status(argv[2] if len(argv) > 2 else DEFAULT_CR)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
