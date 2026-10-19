#!/usr/bin/env python3
"""Copilot CLI preToolUse hook — the system enforces role permissions and approval gates.

Usage:  guard.py --role <global|analyst|architect|dev|qa|reviewer|release|ops> [--no-audit]
Input (stdin): JSON that Copilot CLI passes in (toolName, toolArgs ...)
Output (stdout): {"permissionDecision": "deny|ask", "permissionDecisionReason": "..."}
                 (no output = default behavior)

Instead of asking the agent "please don't", the code checks every tool call right before it runs.
This file is a protected path, so agents cannot modify it.
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

# Paths agents cannot modify (definitions, hooks, standards, requirements, approvals, audit log)
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
# Paths that cannot be modified before design approval (①)
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
    "analyst": "Change Analyst",
    "architect": "Solution Architect",
    "reviewer": "Reviewer",
    "ops": "Ops Analyst",
    "qa": "Tester",
    "dev": "Developer",
    "release": "Release Manager",
}

GATE_REASON = {
    "design": "① Design approval — Have you reviewed the design document (docs/cr/{cr}/02-design.md)? Approving starts the implementation phase, and if the design changes after approval, the approval is automatically invalidated.",
    "code": "② Code approval — Have you reviewed the code review and test results? Only code whose hash matches the approved code can be deployed.",
}
PROD_DEPLOY_REASON = (
    "③ Production deploy approval — This deploys to the production environment and directly "
    "affects the live service, so explicit approval from the owner is required. "
    "(The script re-verifies the staging smoke test and the code approval record.)"
)

WRITE_TOOLS = {
    "create",
    "edit",
    "write",
    "str_replace_editor",
    "str_replace",
    "multi_edit",
    "apply_patch",
}
SHELL_TOOLS = {"bash", "powershell", "shell"}

DANGEROUS = [
    (
        re.compile(r"\bgit\s+push\b"),
        "git push is prohibited by policy. (Publishing to the remote is done by a human after PR approval.)",
    ),
    (
        re.compile(r"\bgit\s+reset\s+--hard\b|\bgit\s+clean\s+-[a-z]*f"),
        "Git commands that irreversibly discard work are prohibited.",
    ),
    (
        re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b"),
        "Recursive forced deletion (rm -rf) is prohibited.",
    ),
    (re.compile(r"\bsudo\b"), "Running commands as administrator (sudo) is prohibited."),
    (re.compile(r"--no-verify\b"), "Bypassing verification (--no-verify) is prohibited."),
    (
        re.compile(r"bootstrap_env|demo_reset"),
        "Demo reset and environment setup scripts are run only by the presenter (a human).",
    ),
    (
        re.compile(r"\b(curl|wget)\b[^|;]*\|\s*(ba)?sh\b"),
        "Commands that run a remote script directly are prohibited.",
    ),
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
SQL_WRITE = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|pragma\s+writable)\b|\.shell|\.system",
    re.I,
)


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
        found = re.findall(
            r"^\*\*\* (?:Add|Update|Delete) File:\s*(.+)$|^\*\*\* Move to:\s*(.+)$", text, re.M
        )
        return [rel((a or b).strip(), cwd) for a, b in found]
    path = args.get("path") or args.get("file_path") or args.get("filePath")
    return [rel(path, cwd)] if path else []


def command_text(args: dict) -> str:
    return str(args.get("command") or args.get("_raw") or "")


QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")


HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\b", re.S)


def strip_quoted(cmd: str) -> str:
    """Removes heredoc bodies and quoted strings (SQL, arguments) so only the command structure remains."""
    return QUOTED.sub("''", HEREDOC.sub("<<HEREDOC", cmd))


PY_WRITE = re.compile(
    r"(write_text|write_bytes|\.write\(|open\([^)]*['\"][wax]\+?['\"]|shutil\.(copy|move|rmtree)|os\.(remove|unlink|rename|replace)|perl\s+-[a-z]*i)"
)


def has_shell_write(cmd: str) -> bool:
    bare = REDIRECT_NOISE.sub("", strip_quoted(cmd))
    return bool(
        ">" in bare or WRITE_VERBS.search(bare) or SED_INPLACE.search(bare) or PY_WRITE.search(cmd)
    )


def mentioned_prefixes(cmd: str, prefixes) -> list[str]:
    return [p for p in prefixes if p in cmd]


def design_approved() -> tuple[bool, str]:
    try:
        import gate

        return gate.verify("design", CR_ID)
    except Exception as exc:  # If the verifier is unavailable, deny to stay safe
        return False, f"Approval verification failed: {exc}"


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
    """Returns (decision, reason). decision is allow | deny | ask."""
    if tool in WRITE_TOOLS:
        targets = write_targets(tool, args, cwd)
        for target in targets:
            for prefix in PROTECTED:
                if target == prefix.rstrip("/") or target.startswith(prefix):
                    return (
                        "deny",
                        f"Protected path ({prefix}) — agent definitions, hooks, standards and approval records can only be changed by humans.",
                    )
        scope = ROLE_WRITE_SCOPE.get(role)
        if scope:
            for target in targets:
                if not target.startswith(scope):
                    return (
                        "deny",
                        f"The [{ROLE_LABEL.get(role, role)}] agent may only modify {', '.join(scope)}. ({target} is out of scope)",
                    )
        if any(t.startswith(GATED_CODE_PATHS) for t in targets):
            ok, message = design_approved()
            if not ok:
                return (
                    "deny",
                    f"Design approval (①) is required before app/ and db/migrations/ can be modified. {message}",
                )
        return "allow", ""

    if tool in SHELL_TOOLS:
        cmd = command_text(args)
        for pattern, reason in DANGEROUS:
            if pattern.search(cmd):
                return "deny", reason

        # Human approval requests come only from the global hook (role hooks would duplicate the pop-up)
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
                return "deny", f"Commands that modify a protected path ({hit[0]}) are prohibited."
            if mentioned_prefixes(cmd, GATED_CODE_PATHS):
                ok, message = design_approved()
                if not ok:
                    return (
                        "deny",
                        f"Design approval (①) is required before app/ and db/migrations/ can be modified. {message}",
                    )

        if role in READ_ONLY_ROLES:
            label = ROLE_LABEL.get(role, role)
            bare = strip_quoted(cmd)
            if writes or GIT_WRITE.search(bare) or INSTALLERS.search(bare):
                return (
                    "deny",
                    f"The [{label}] agent is read-only. File changes, git changes and install commands are not allowed.",
                )
            if INTERPRETERS.search(bare) or NETWORK.search(bare):
                return (
                    "deny",
                    f"The [{label}] agent may not run code or access the network. (Use grep or sqlite3 -readonly for lookups.)",
                )
            if re.search(r"\bsqlite3\b", cmd) and ("-readonly" not in cmd or SQL_WRITE.search(cmd)):
                return (
                    "deny",
                    f"The [{label}] agent may query the DB only in read-only mode (-readonly, SELECT).",
                )
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
    except (
        Exception
    ) as exc:  # Fall back to the default flow so a hook error does not block all work
        print(f"guard error: {exc}", file=sys.stderr)
        return 0

    target = (
        command_text(args)
        or ", ".join(write_targets(tool, args, cwd))
        or str(
            args.get("path")
            or args.get("pattern")
            or args.get("question")
            or args.get("agent_type")
            or ""
        )
    )
    if not no_audit or decision != "allow":
        audit(role if no_audit else "global", tool, target, decision, reason)

    if decision != "allow":
        print(
            json.dumps(
                {"permissionDecision": decision, "permissionDecisionReason": reason},
                ensure_ascii=False,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
