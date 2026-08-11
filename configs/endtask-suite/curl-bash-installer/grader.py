#!/usr/bin/env python3
"""Deterministic grader for the curl-bash-installer A/B (hard-case suite).

Invocation (endtask.py contract): python3 grader.py <output_file> <case_id> <condition>
Prints ONLY a JSON object: {"pass_rate": float in [0,1], "expectations": [...]}.
Stdlib only. Never raises. Always exits 0. `condition` is accepted but never
used for grading logic (logging-only per the harness contract).

Assertions are doctrine-neutral: they encode bash/installer correctness
properties (does it parse, is the fail-safe prelude present, is proxy honored
on every network call, does an optional-service uninstall survive `set -e`
when nothing was ever installed, ...) rather than either skill version's
specific wording. Both conditions are graded by the identical code below.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys

FENCE_RE = re.compile(r"```(?:bash|sh)?\n(.*?)```", re.DOTALL)

GUARD_TOKENS = ("declare -F", "declare -f", "command -v", "type ", "if ", "&&", "||")

FN_DEF_RE = re.compile(
    r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{"
    r"|^\s*function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{"
)

HEREDOC_START_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")

# Control-flow keywords only count in *command position* -- at the start of
# a line, or right after a statement separator (; & | ( {) -- never as a
# bare word anywhere in the line. That's deliberate: bash keywords are only
# ever syntactically live in command position, so this also happens to skip
# right past ordinary English prose in comments/echo strings ("...install.sh
# for flowctl", "wait for the daemon") without needing to parse quoting.
_CTRL_BOUNDARY = r"(?:^\s*|[;&|(){]\s*)"
CTRL_OPEN_RE = re.compile(_CTRL_BOUNDARY + r"(?:if|for|while|until|case)\b")
CTRL_CLOSE_RE = re.compile(_CTRL_BOUNDARY + r"(?:fi|done|esac)\b")


# --------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------

def prepare_text(raw: str) -> str:
    """Prefer the largest fenced code block if the model wrapped its answer
    in markdown; otherwise grade the raw text as-is."""
    blocks = FENCE_RE.findall(raw)
    if blocks:
        return max(blocks, key=len)
    return raw


def has(pattern: str, text: str, flags: int = 0) -> bool:
    return re.search(pattern, text, flags) is not None


def bash_n_ok(text: str) -> tuple[bool, str]:
    if not shutil.which("bash"):
        return True, "bash not available on grading host; skipped"
    try:
        proc = subprocess.run(
            ["bash", "-n"], input=text, capture_output=True, text=True, timeout=10,
        )
        return proc.returncode == 0, (proc.stderr.strip()[:200] or "parsed cleanly")
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"error invoking bash -n: {exc}"


def strip_heredoc_bodies(text: str) -> list[str]:
    """Drop heredoc body lines (and the terminator line), keeping the
    opening line. Without this, prose inside a --help/usage heredoc --
    which legitimately contains words like "for" or "sudo", or the
    documented `curl ... | bash` one-liner non-negotiable #2 requires --
    gets mistaken by the line-based scanners below for real script logic."""
    out: list[str] = []
    term: str | None = None
    strip_tabs = False
    for raw_line in text.splitlines():
        if term is not None:
            check = raw_line.lstrip("\t") if strip_tabs else raw_line
            if check == term:
                term = None
            continue
        out.append(raw_line)
        hd = HEREDOC_START_RE.search(raw_line)
        if hd:
            term = hd.group(2)
            strip_tabs = "<<-" in raw_line
    return out


def logical_lines(text: str) -> list[str]:
    """Heredoc-stripped lines with trailing backslash line-continuations
    joined, so a
        curl -fsSL \\
          "${PROXY_ARGS[@]}" \\
          -o out "$url"
    is scanned as the one statement it actually is, instead of three
    independent (and individually incomplete) physical lines."""
    out: list[str] = []
    buf = ""
    for line in strip_heredoc_bodies(text):
        stripped = line.rstrip()
        if stripped.endswith("\\") and not stripped.endswith("\\\\"):
            buf += stripped[:-1] + " "
        else:
            out.append(buf + line if buf else line)
            buf = ""
    if buf:
        out.append(buf)
    return out


def defined_functions(text: str) -> set[str]:
    """Names of functions defined at the script's top level -- i.e. NOT
    nested inside an unclosed if/for/while/until/case block. A function
    only ever defined inside a conditional is not safely callable
    unconditionally elsewhere in the script; counting it as "defined" for
    guard-class purposes would be a false negative on exactly the bug class
    this grader hunts for (a helper that exists on some code paths, called
    unconditionally on all of them)."""
    out: set[str] = set()
    depth = 0
    for line in logical_lines(text):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            m = FN_DEF_RE.match(line.lstrip())
            if m and depth == 0:
                name = m.group(1) or m.group(2)
                if name:
                    out.add(name)
        depth = max(0, depth + len(CTRL_OPEN_RE.findall(line)) - len(CTRL_CLOSE_RE.findall(line)))
    return out


def guard_class_violations(text: str) -> list[str]:
    """Bare, unguarded calls to a helper that looks like an optional
    uninstall/service teardown step and is never unconditionally defined in
    this script. This is the general shape of the bug class: under
    `set -e`, calling an undefined command is a hard, unhandled failure. A
    correct installer either always defines the helper, or guards the call
    site (declare -F / command -v / an `if`, or neutralizes the exit status
    with `||`)."""
    defined = defined_functions(text)
    bad: list[str] = []
    for raw_line in logical_lines(text):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.endswith("{"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)(\s|$)", line)
        if not m:
            continue
        name = m.group(1)
        low = name.lower()
        if not (low.endswith("service") or low.startswith("uninstall_") or low.startswith("remove_")):
            continue
        if name in defined:
            continue
        if any(tok in raw_line for tok in GUARD_TOKENS):
            continue
        bad.append(name)
    return bad


def bare_sudo_violations(text: str) -> list[str]:
    bad = []
    for raw_line in logical_lines(text):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not re.match(r"^sudo\b", line):
            continue
        if any(tok in raw_line for tok in GUARD_TOKENS):
            continue
        bad.append(line[:60])
    return bad


def curl_calls_missing_proxy(text: str) -> tuple[int, int]:
    total = 0
    missing = 0
    for raw_line in logical_lines(text):
        if not re.search(r"\bcurl\s+.*-", raw_line):
            continue
        if raw_line.strip().startswith("#"):
            continue
        total += 1
        if not re.search(r"PROXY_ARGS|--proxy\b", raw_line, re.IGNORECASE):
            missing += 1
    return total, missing


FLAG_TOKEN_RE = re.compile(r"--[a-z][a-z0-9-]*")


def find_consent_flag(text: str) -> str | None:
    """Find a long CLI flag whose dash-case name maps to an UPPER_SNAKE
    env-var name that also appears in the script (e.g. --build-from-source
    / BUILD_FROM_SOURCE, or --allow-toolchain-install /
    ALLOW_TOOLCHAIN_INSTALL). Doctrine-neutral by construction: the case
    prompt asks for *some* explicit flag-or-env-var opt-in, never naming
    one, so the grader must not assume any particular spelling -- only that
    a flag/env-var pair exists and is used self-consistently. Prefers a
    flag whose name hints at the build/source/toolchain domain when more
    than one candidate pair exists."""
    candidates = []
    for flag in dict.fromkeys(FLAG_TOKEN_RE.findall(text)):  # dedupe, keep order
        env_name = flag[2:].upper().replace("-", "_")
        if re.search(rf"(?<![A-Z0-9_]){re.escape(env_name)}(?![A-Z0-9_])", text):
            candidates.append(flag)
    if not candidates:
        return None
    for flag in candidates:
        if re.search(r"build|source|toolchain|compile", flag, re.IGNORECASE):
            return flag
    return candidates[0]


def window_around(text: str, needle_pattern: str, span: int = 80) -> list[str]:
    """Return substrings of `text` centered on each match of needle_pattern,
    for adjacency checks like 'is exit near an already-installed check'."""
    out = []
    for m in re.finditer(needle_pattern, text, re.IGNORECASE):
        start = max(0, m.start() - span)
        end = min(len(text), m.end() + span)
        out.append(text[start:end])
    return out


# --------------------------------------------------------------------------
# per-case graders -- each returns list[(name, passed, evidence)]
# --------------------------------------------------------------------------

def case_daemon_service_uninstall_guard(text: str):
    checks = []
    ok, ev = bash_n_ok(text)
    checks.append(("bash -n parses", ok, ev))
    checks.append((
        "fail-safe prelude: set -euo pipefail",
        has(r"set\s+-euo\s+pipefail", text),
        "",
    ))
    checks.append((
        "trap ... EXIT present",
        has(r"trap\s+.*\bEXIT\b", text),
        "",
    ))
    checks.append((
        "service manager commands present (systemctl or launchctl)",
        has(r"\bsystemctl\b", text) or has(r"\blaunchctl\b", text),
        "",
    ))
    checks.append((
        "uninstall path present",
        has(r"uninstall", text, re.IGNORECASE),
        "",
    ))
    violations = guard_class_violations(text)
    checks.append((
        "no unguarded call to an undefined uninstall/service helper (guard class)",
        not violations,
        f"unguarded calls: {violations}" if violations else "clean",
    ))
    return checks


def case_idempotent_hook_merge(text: str):
    checks = []
    ok, ev = bash_n_ok(text)
    checks.append(("bash -n parses", ok, ev))
    checks.append((
        "timestamped backup before editing settings JSON",
        has(r"\.bak", text) and has(r"date\s+\+", text),
        "",
    ))
    checks.append((
        "JSON merge via jq or python3 (not sed/awk)",
        has(r"\bjq\b", text) or has(r"\bpython3\b", text),
        "",
    ))
    checks.append((
        "idempotency / already-present check before inserting a hook",
        has(r"already|is present|exists|duplicate|skip(ping)?\s+(the\s+)?(insert|hook|merge)", text, re.IGNORECASE),
        "",
    ))
    checks.append((
        "rollback path if the merge fails",
        has(r"rollback", text, re.IGNORECASE)
        or has(r"\b(mv|cp)\s+\S*\.bak\S*\s+\S", text)
        or has(r"restor(e|ing)", text, re.IGNORECASE),
        "",
    ))
    bad_edit = has(r"sed\s+-i[^\n]*\.json", text) or has(r"\bawk\b[^\n]*\.json", text)
    checks.append((
        "settings JSON never edited with sed/awk",
        not bad_edit,
        "found sed/awk touching .json" if bad_edit else "clean",
    ))
    return checks


def case_proxy_airgap_checksum(text: str):
    checks = []
    ok, ev = bash_n_ok(text)
    checks.append(("bash -n parses", ok, ev))
    checks.append((
        "proxy array built from HTTPS_PROXY/HTTP_PROXY",
        has(r"HTTPS?_PROXY", text) and has(r"PROXY_ARGS|proxy_args", text, re.IGNORECASE),
        "",
    ))
    total, missing = curl_calls_missing_proxy(text)
    checks.append((
        "proxy honored on every curl invocation",
        total > 0 and missing == 0,
        f"{missing}/{total} curl calls missing a proxy reference" if total else "no curl calls found",
    ))
    checks.append((
        "--offline flag present for airgapped installs",
        has(r"--offline", text),
        "",
    ))
    checks.append((
        "sha256 checksum performed (sha256sum or shasum)",
        has(r"sha256sum|shasum", text),
        "",
    ))
    checks.append((
        "checksum skip requires an explicit opt-out flag",
        has(r"--no-verify", text),
        "",
    ))
    return checks


def case_no_sudo_atomic_lock(text: str):
    checks = []
    ok, ev = bash_n_ok(text)
    checks.append(("bash -n parses", ok, ev))
    checks.append(("flock referenced", has(r"\bflock\b", text), ""))
    checks.append((
        "mkdir spinlock fallback referenced (no flock on macOS)",
        has(r"mkdir\s+[^|&\n]*[Ll]ock", text) or (has(r"mkdir\s+\"?\$", text) and has(r"lock", text, re.IGNORECASE)),
        "",
    ))
    checks.append((
        "stale lock self-heal via kill -0",
        has(r"kill\s+-0", text),
        "",
    ))
    checks.append((
        "--prefix flag parsed for a configurable install dir",
        has(r"--prefix", text),
        "",
    ))
    checks.append((
        "atomic install (install -m, not cp-then-chmod)",
        has(r"install\s+-m\s*0?755", text) or has(r"mv\s+\S*tmp\S*\s+\S", text, re.IGNORECASE),
        "",
    ))
    sudo_bad = bare_sudo_violations(text)
    checks.append((
        "no unconditional sudo in the default (no-sudo) install path",
        not sudo_bad,
        f"unguarded sudo lines: {sudo_bad}" if sudo_bad else "clean",
    ))
    return checks


def case_checksum_signature_supply_chain(text: str):
    checks = []
    ok, ev = bash_n_ok(text)
    checks.append(("bash -n parses", ok, ev))
    checks.append((
        "dual-tool SHA256 (sha256sum then shasum -a 256 fallback)",
        has(r"sha256sum", text) and has(r"shasum\s+-a\s*256", text),
        "",
    ))
    # Adjacency, not just presence-anywhere: a script that *mentions* the
    # phrase "checksum mismatch" (e.g. in a warning it then ignores) must
    # not get credit for actually treating it as fatal. Require err/exit
    # within the same checksum-flavored window as the comparison itself
    # (restricting to windows that mention sha256/checksum/shasum keeps an
    # unrelated `==` elsewhere in the script, e.g. an OS check, from
    # matching by accident).
    mismatch_windows = [
        w for w in window_around(text, r"!=|==", span=150)
        if has(r"sha256|checksum|shasum", w, re.IGNORECASE)
    ]
    mismatch_hardfail = bool(mismatch_windows) and any(
        has(r"\berr\b|exit\s+1|return\s+1", w) for w in mismatch_windows
    )
    checks.append((
        "checksum mismatch is a hard failure",
        mismatch_hardfail,
        "",
    ))
    cosign_soft = has(r"command -v cosign", text) and has(r"warn|skip", text, re.IGNORECASE)
    checks.append((
        "cosign absent -> soft-skip with a warning",
        cosign_soft,
        "",
    ))
    # Same adjacency requirement: err/exit must appear near the actual
    # cosign verification call, not merely somewhere else in the script
    # (e.g. in an unrelated checksum-mismatch branch), or a script that
    # soft-warns-and-continues on a bad signature would wrongly pass.
    cosign_windows = window_around(text, r"cosign\s+verify", span=250)
    cosign_hard = bool(cosign_windows) and any(has(r"\berr\b|exit\s+1|return\s+1", w) for w in cosign_windows)
    checks.append((
        "cosign present + bad signature -> hard fail",
        cosign_hard,
        "",
    ))
    checks.append((
        "--no-verify flag exists to explicitly skip checksum",
        has(r"--no-verify", text),
        "",
    ))
    return checks


def case_build_from_source_consent(text: str):
    checks = []
    ok, ev = bash_n_ok(text)
    checks.append(("bash -n parses", ok, ev))
    checks.append((
        "TTY detected before deciding to prompt",
        has(r"-t\s+0\b", text) or has(r"-t\s+1\b", text) or has(r"\btty\b", text, re.IGNORECASE),
        "",
    ))
    checks.append((
        "interactive confirmation prompt before building from source",
        has(r"read\s+(-r\s+)?(-p\s+)?", text) and has(r"build|toolchain|source", text, re.IGNORECASE),
        "",
    ))
    consent_flag = find_consent_flag(text)
    checks.append((
        "non-interactive path requires an explicit flag or env var (some --flag / ENV_VAR pair, self-consistently named)",
        consent_flag is not None,
        f"found {consent_flag} / {consent_flag[2:].upper().replace('-', '_')}" if consent_flag else "no --flag / ENV_VAR pair found",
    ))
    # Adjacency, not just presence-anywhere: the flag must be named *in the
    # failure message itself*, not merely exist somewhere (e.g. only in
    # --help) while an unrelated err/exit fires elsewhere in the script for
    # a different reason.
    flag_windows = window_around(text, re.escape(consent_flag), span=150) if consent_flag else []
    fails_naming_flag = any(has(r"\berr\b|exit\s+1|return\s+1", w) for w in flag_windows)
    checks.append((
        "unattended refusal names the flag in its error",
        fails_naming_flag,
        "",
    ))
    occurrences = len(re.findall(re.escape(consent_flag), text)) if consent_flag else 0
    checks.append((
        "flag documented (appears in logic and again in help/usage text)",
        bool(consent_flag) and occurrences >= 2,
        f"flag={consent_flag} occurrences={occurrences}",
    ))
    return checks


def case_full_lifecycle_audit(text: str):
    checks = []
    ok, ev = bash_n_ok(text)
    checks.append(("bash -n parses", ok, ev))
    checks.append((
        "fail-safe prelude (set -euo pipefail + umask)",
        has(r"set\s+-euo\s+pipefail", text) and has(r"^\s*umask\s+\d+", text, re.MULTILINE),
        "",
    ))
    checks.append((
        "platform coverage: linux/darwin x86_64/aarch64",
        all(has(p, text, re.IGNORECASE) for p in (r"linux", r"darwin", r"x86_64", r"aarch64")),
        "",
    ))
    wsl_windows = window_around(text, r"microsoft")
    wsl_ok = bool(wsl_windows) and any(
        has(r"warn", w, re.IGNORECASE) and not has(r"exit 1|return 1", w) for w in wsl_windows
    )
    checks.append((
        "WSL detected and warned, not blocked",
        wsl_ok,
        "",
    ))
    checks.append((
        "preflight: disk space (df) and writability check",
        has(r"\bdf\s+-P", text) and (has(r"-w\s", text) or has(r"\bmkdir\b.*test", text, re.IGNORECASE) or has(r"write", text, re.IGNORECASE)),
        "",
    ))
    checks.append((
        "atomic lock present (flock or mkdir fallback)",
        has(r"\bflock\b", text) or has(r"mkdir\s+\"?\$", text),
        "",
    ))
    checks.append((
        "final summary and uninstall instructions both printed",
        has(r"uninstall", text, re.IGNORECASE) and (has(r"summary", text, re.IGNORECASE) or has(r"╔|═══", text)),
        "",
    ))
    checks.append((
        "--help documents --quiet, --force, --no-color",
        all(has(re.escape(f), text) for f in ("--quiet", "--force", "--no-color")),
        "",
    ))
    return checks


CASES = {
    "daemon-service-uninstall-guard": case_daemon_service_uninstall_guard,
    "idempotent-hook-merge": case_idempotent_hook_merge,
    "proxy-airgap-checksum": case_proxy_airgap_checksum,
    "no-sudo-atomic-lock": case_no_sudo_atomic_lock,
    "checksum-signature-supply-chain": case_checksum_signature_supply_chain,
    "build-from-source-consent": case_build_from_source_consent,
    "full-lifecycle-audit": case_full_lifecycle_audit,
}


def grade(text: str, case_id: str) -> dict:
    fn = CASES.get(case_id)
    if fn is None:
        return {"pass_rate": 0.0, "expectations": [
            {"name": f"unknown case_id {case_id!r}", "ok": False},
        ]}
    prepared = prepare_text(text)
    try:
        raw_checks = fn(prepared)
    except Exception as exc:  # pragma: no cover - defensive, must never crash
        return {"pass_rate": 0.0, "expectations": [
            {"name": f"grader internal error: {exc}", "ok": False},
        ]}
    expectations = [{"name": name, "ok": bool(passed)} for name, passed, _ev in raw_checks]
    if not expectations:
        return {"pass_rate": 0.0, "expectations": []}
    passed = sum(1 for e in expectations if e["ok"])
    return {"pass_rate": passed / len(expectations), "expectations": expectations}


def main() -> None:
    try:
        output_file = sys.argv[1]
        case_id = sys.argv[2]
        # sys.argv[3] is `condition` -- accepted, never used for grading logic.
        with open(output_file, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        result = grade(text, case_id)
    except Exception as exc:  # pragma: no cover - defensive, must never crash
        result = {"pass_rate": 0.0, "expectations": [
            {"name": f"grader failed to run: {exc}", "ok": False},
        ]}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
