#!/usr/bin/env python3
"""Copilot CLI preToolUse 훅 — 역할별 권한과 승인 게이트를 '시스템'이 강제한다.

사용법:  guard.py --role <global|analyst|architect|dev|qa|reviewer|release|ops> [--no-audit]
입력(stdin): Copilot CLI 가 넘겨주는 JSON (toolName, toolArgs ...)
출력(stdout): {"permissionDecision": "deny|ask", "permissionDecisionReason": "..."}  (없으면 기본 동작)

에이전트에게 "하지 마세요"라고 부탁하는 것이 아니라, 도구 호출 직전에 코드가 검사한다.
이 파일은 보호 경로이므로 에이전트가 수정할 수 없다.
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(os.environ.get("DEMO_REPO_ROOT") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(ROOT / "scripts"))
CR_ID = os.environ.get("DEMO_CR", "CR-2026-014")

# 에이전트가 수정할 수 없는 경로 (정의·훅·표준·원본 요건·승인 기록·감사 로그)
PROTECTED = (
    ".github/agents/",
    ".github/hooks/",
    ".github/instructions/",
    ".github/copilot-instructions.md",
    ".github/workflows/",
    "scripts/",
    "docs/standards/",
    "docs/requirements/",
    "approvals/",
    ".copilot-audit/",
)
# 설계 승인(①) 전에는 수정할 수 없는 경로
GATED_CODE_PATHS = ("app/", "db/migrations/")

ROLE_WRITE_SCOPE = {
    "analyst": ("docs/cr/",),
    "architect": ("docs/cr/",),
    "reviewer": ("docs/cr/",),
    "ops": ("docs/cr/",),
    "qa": ("tests/", "docs/cr/"),
    "dev": ("app/", "db/migrations/", "tests/", "docs/policy/", "docs/cr/"),
    "release": ("docs/cr/", "VERSION"),
}
READ_ONLY_ROLES = {"analyst", "architect", "reviewer", "ops"}
ROLE_LABEL = {
    "analyst": "변경 분석가",
    "architect": "설계자",
    "reviewer": "리뷰어",
    "ops": "운영 분석가",
    "qa": "테스터",
    "dev": "개발자",
    "release": "배포 관리자",
}

GATE_REASON = {
    "design": "① 설계 승인 — 설계서(docs/cr/{cr}/02-design.md)를 검토하셨습니까? 승인하면 구현 단계가 시작되며, 승인 후 설계서가 바뀌면 승인은 자동으로 무효가 됩니다.",
    "code": "② 코드 승인 — 코드 리뷰·테스트 결과를 확인하셨습니까? 승인한 코드와 해시가 일치하는 코드만 배포할 수 있습니다.",
}
PROD_DEPLOY_REASON = (
    "③ 운영 배포 승인 — 운영(production) 환경에 배포합니다. 실서비스에 직접 영향을 주므로 "
    "담당자의 명시적 승인이 필요합니다. (staging 스모크 테스트 통과·코드 승인 기록은 스크립트가 다시 검증합니다)"
)

WRITE_TOOLS = {"create", "edit", "write", "str_replace_editor", "str_replace", "multi_edit", "apply_patch"}
SHELL_TOOLS = {"bash", "powershell", "shell"}

DANGEROUS = [
    (re.compile(r"\bgit\s+push\b"), "git push 는 정책상 금지입니다. (원격 반영은 사람이 PR 승인 후 수행)"),
    (re.compile(r"\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-[a-z]*f"), "작업 내용을 되돌릴 수 없는 git 명령은 금지입니다."),
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b"), "재귀 강제 삭제(rm -rf)는 금지입니다."),
    (re.compile(r"\bsudo\b"), "관리자 권한 실행(sudo)은 금지입니다."),
    (re.compile(r"--no-verify\b"), "검증 우회(--no-verify)는 금지입니다."),
    (re.compile(r"bootstrap_env|demo_reset"), "데모 초기화·환경 구성 스크립트는 진행자(사람)만 실행합니다."),
    (re.compile(r"\b(curl|wget)\b[^|;]*\|\s*(ba)?sh\b"), "원격 스크립트를 바로 실행하는 명령은 금지입니다."),
]
REDIRECT_NOISE = re.compile(r"\d*>&\d+|\d*>>?\s*/dev/null|&>\s*/dev/null")
WRITE_VERBS = re.compile(
    r"(^|[\s;&|(])(tee|mv|cp|rm|touch|mkdir|rmdir|chmod|chown|ln|truncate|dd|install|patch)\s"
)
SED_INPLACE = re.compile(r"\bsed\s+(-[a-zA-Z]*i|--in-place)")
GIT_WRITE = re.compile(
    r"\bgit\s+(add|commit|checkout|switch|merge|rebase|reset|stash|apply|cherry-pick|restore|mv|rm|pull|fetch|clean|tag|branch\s+-[dDmM])\b"
)
INSTALLERS = re.compile(r"\b(pip3?|npm|yarn|brew|apt|apt-get)\s+(install|add|remove|uninstall)\b")
INTERPRETERS = re.compile(r"(^|[\s;&|(])(python3?|node|perl|ruby|php)\s|\b(ba)?sh\s+-c\b")
NETWORK = re.compile(r"\b(curl|wget|nc|ssh|scp)\b")
SQL_WRITE = re.compile(r"\b(insert|update|delete|drop|alter|create|replace|attach|pragma\s+writable)\b|\.shell|\.system", re.I)


def load_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def parse_args(raw):
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {"_raw": raw}
        except json.JSONDecodeError:
            return {"_raw": raw}
    return raw if isinstance(raw, dict) else {}


def rel(path: str, cwd: str) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path(cwd) / candidate
    normalized = Path(os.path.normpath(candidate))
    try:
        return normalized.relative_to(ROOT).as_posix()
    except ValueError:
        return normalized.as_posix()


def write_targets(tool: str, args: dict, cwd: str) -> list[str]:
    if tool == "apply_patch":
        text = args.get("_raw") or args.get("patch") or args.get("input") or ""
        found = re.findall(r"^\*\*\* (?:Add|Update|Delete) File:\s*(.+)$|^\*\*\* Move to:\s*(.+)$", text, re.M)
        return [rel((a or b).strip(), cwd) for a, b in found]
    path = args.get("path") or args.get("file_path") or args.get("filePath")
    return [rel(path, cwd)] if path else []


def command_text(args: dict) -> str:
    return str(args.get("command") or args.get("_raw") or "")


QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")


HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\b", re.S)


def strip_quoted(cmd: str) -> str:
    """히어독 본문과 따옴표 안의 문자열(SQL·인자 등)을 지워 실제 명령 구조만 남긴다."""
    return QUOTED.sub("''", HEREDOC.sub("<<HEREDOC", cmd))


PY_WRITE = re.compile(
    r"(write_text|write_bytes|\.write\(|open\([^)]*['\"][wax]\+?['\"]|shutil\.(copy|move|rmtree)|os\.(remove|unlink|rename|replace)|perl\s+-[a-z]*i)"
)


def has_shell_write(cmd: str) -> bool:
    bare = REDIRECT_NOISE.sub("", strip_quoted(cmd))
    return bool(">" in bare or WRITE_VERBS.search(bare) or SED_INPLACE.search(bare) or PY_WRITE.search(cmd))


def mentioned_prefixes(cmd: str, prefixes) -> list[str]:
    return [p for p in prefixes if p in cmd]


def design_approved() -> tuple[bool, str]:
    try:
        import gate

        return gate.verify("design", CR_ID)
    except Exception as exc:  # 검증기를 못 쓰면 안전하게 거부
        return False, f"승인 검증 실패: {exc}"


def audit(role: str, tool: str, target: str, decision: str, reason: str = "") -> None:
    try:
        log_dir = ROOT / ".copilot-audit"
        log_dir.mkdir(exist_ok=True)
        entry = {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "role": role,
            "tool": tool,
            "target": target[:200],
            "decision": decision,
        }
        if reason:
            entry["reason"] = reason
        with open(log_dir / "audit.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def decide(role: str, tool: str, args: dict, cwd: str) -> tuple[str, str]:
    """(decision, reason) 반환. decision 은 allow | deny | ask."""
    if tool in WRITE_TOOLS:
        targets = write_targets(tool, args, cwd)
        for target in targets:
            for prefix in PROTECTED:
                if target == prefix.rstrip("/") or target.startswith(prefix):
                    return "deny", f"보호된 경로입니다 ({prefix}) — 에이전트 정의·훅·표준·승인 기록은 사람만 변경할 수 있습니다."
        scope = ROLE_WRITE_SCOPE.get(role)
        if scope:
            for target in targets:
                if not target.startswith(scope):
                    return "deny", f"[{ROLE_LABEL.get(role, role)}] 에이전트의 수정 가능 범위는 {', '.join(scope)} 입니다. ({target} 는 범위 밖)"
        if any(t.startswith(GATED_CODE_PATHS) for t in targets):
            ok, message = design_approved()
            if not ok:
                return "deny", f"설계 승인(①) 전에는 app/·db/migrations/ 를 수정할 수 없습니다. {message}"
        return "allow", ""

    if tool in SHELL_TOOLS:
        cmd = command_text(args)
        for pattern, reason in DANGEROUS:
            if pattern.search(cmd):
                return "deny", reason

        # 사람 승인 요청은 전역 훅(global)에서만 한 번 띄운다 (역할 훅까지 띄우면 승인 팝업이 중복된다)
        if role == "global":
            gate_match = re.search(r"scripts/gate\.py\s+request\s+(design|code)\b", cmd)
            if gate_match:
                return "ask", GATE_REASON[gate_match.group(1)].format(cr=CR_ID)
            if re.search(r"deploy\.sh\s+(production|prod)\b", cmd):
                return "ask", PROD_DEPLOY_REASON

        writes = has_shell_write(cmd)
        if writes:
            hit = mentioned_prefixes(cmd, PROTECTED)
            if hit:
                return "deny", f"보호된 경로({hit[0]})를 수정하는 명령은 금지입니다."
            if mentioned_prefixes(cmd, GATED_CODE_PATHS):
                ok, message = design_approved()
                if not ok:
                    return "deny", f"설계 승인(①) 전에는 app/·db/migrations/ 를 수정할 수 없습니다. {message}"

        if role in READ_ONLY_ROLES:
            label = ROLE_LABEL.get(role, role)
            bare = strip_quoted(cmd)
            if writes or GIT_WRITE.search(bare) or INSTALLERS.search(bare):
                return "deny", f"[{label}] 에이전트는 읽기 전용입니다. 파일 변경·git 변경·설치 명령은 허용되지 않습니다."
            if INTERPRETERS.search(bare) or NETWORK.search(bare):
                return "deny", f"[{label}] 에이전트는 코드 실행·네트워크 접근이 허용되지 않습니다. (조회는 grep/sqlite3 -readonly 사용)"
            if re.search(r"\bsqlite3\b", cmd) and ("-readonly" not in cmd or SQL_WRITE.search(cmd)):
                return "deny", f"[{label}] 에이전트는 DB를 읽기 전용(-readonly, SELECT)으로만 조회할 수 있습니다."
        return "allow", ""

    return "allow", ""


def main() -> int:
    argv = sys.argv[1:]
    role = argv[argv.index("--role") + 1] if "--role" in argv else "global"
    no_audit = "--no-audit" in argv
    payload = load_payload()
    tool = (payload.get("toolName") or payload.get("tool_name") or "").lower()
    args = parse_args(payload.get("toolArgs", payload.get("tool_input", {})))
    cwd = payload.get("cwd") or str(ROOT)

    try:
        decision, reason = decide(role, tool, args, cwd)
    except Exception as exc:  # 훅 오류가 작업 전체를 막지 않도록 기본 흐름으로 위임
        print(f"guard error: {exc}", file=sys.stderr)
        return 0

    target = (
        command_text(args)
        or ", ".join(write_targets(tool, args, cwd))
        or str(args.get("path") or args.get("pattern") or args.get("question") or args.get("agent_type") or "")
    )
    if not no_audit or decision != "allow":
        audit(role if no_audit else "global", tool, target, decision, reason)

    if decision != "allow":
        print(json.dumps({"permissionDecision": decision, "permissionDecisionReason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
