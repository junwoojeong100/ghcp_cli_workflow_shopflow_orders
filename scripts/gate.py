#!/usr/bin/env python3
"""Approval (gate) record manager.

  gate.py request <design|code> [CR-ID]   Once a human approves, writes approvals/<CR>/<gate>.json
  gate.py verify  <design|code|staging> [CR-ID]   Checks the record is valid (artifact unchanged since approval)
  gate.py record-env <staging|production> <version> [CR-ID]   Records a deployment result (called by deploy.sh)
  gate.py status [CR-ID]   Shows the approval status

'request' is always forced by the hook (scripts/hooks/guard.py) to ask a human for confirmation.
So this record can only be created when a human clicks Yes in the approval prompt.
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
GATE_TITLES = {
    "design": "① Design approval",
    "code": "② Code approval",
    "production": "③ Production deploy approval",
}


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
        return False, f"No '{gate}' approval record found."
    if gate == "design":
        doc = design_doc(cr)
        if not doc.exists():
            return False, "The design document does not exist."
        if rec.get("sha256") != sha256_file(doc):
            return (
                False,
                "The design document changed after approval, so the approval is no longer valid. Please get it approved again.",
            )
        return True, f"Design approval valid (approver {rec['approver']}, {rec['at']})"
    if gate in ("code", "staging"):
        if rec.get("code_sha256") != code_hash():
            return (
                False,
                f"The code changed after approval/verification, so the '{gate}' record is no longer valid.",
            )
        return True, f"'{gate}' record valid ({rec.get('approver', 'system')}, {rec['at']})"
    return True, "Record exists"


def cmd_request(gate: str, cr: str) -> int:
    if gate == "design":
        doc = design_doc(cr)
        if not doc.exists():
            print(f"✗ The design document does not exist: {doc.relative_to(ROOT)}")
            return 1
        data = {"artifact": str(doc.relative_to(ROOT)), "sha256": sha256_file(doc)}
    elif gate == "code":
        missing = [
            n
            for n in ("04-test-report.md", "05-review-report.md")
            if not (ROOT / "docs" / "cr" / cr / n).exists()
        ]
        if missing:
            print(f"✗ Deliverables required before code approval are missing: {', '.join(missing)}")
            return 1
        data = {"artifact": "app/ + db/migrations/", "code_sha256": code_hash()}
    else:
        print(
            "✗ 'request' supports only design | code. (Production deploy approval is requested when deploy.sh production runs.)"
        )
        return 1
    data["approver"] = approver()
    path = write_record(cr, gate, data)
    print(f"✔ {GATE_TITLES[gate]} recorded — approver: {data['approver']}")
    print(f"  Record file: {path.relative_to(ROOT)}")
    print(
        f"  Integrity hash: {(data.get('sha256') or data.get('code_sha256'))[:16]}…  (invalid if changed after approval)"
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
    print(f"✔ {env} deployment record saved (v{version})")
    return 0


def cmd_status(cr: str) -> int:
    print(f"Approval status — {cr}")
    for gate in ("design", "code", "staging", "production"):
        rec = read_record(cr, gate)
        if rec is None:
            print(f"  {gate:<11} ✗ no record")
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
