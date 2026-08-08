#!/usr/bin/env python3
"""Deterministic grader for the curl-bash-installer A/B. No LLM judge.

Walks workspace/iteration-1, grades every run's install.sh against assertions
derived from the skill's own 14 non-negotiables plus two behavioral checks,
and writes a skill-creator-shaped grading.json beside each run so
`tune.py compare --skill-creator` can pair the conditions.

Assertions (identical for both conditions; none reference either version's
specific wording):
  static  A1  bash -n parses
          A2  set -euo pipefail
          A3  trap ... EXIT
          A4  proxy honored (HTTPS_PROXY/HTTP_PROXY wired into curl)
          A5  sha256 verification present
          A6  umask set
          A7  uninstall path present
          A8  final summary box/section printed
          A9  documented curl one-liner with cache-buster
          A10 atomic lock (flock or mkdir)
          A11 no unguarded call to an in-script-undefined *_service/uninstall_*
              helper (the class of bug that half-copies a snippet pair)
          A12 shellcheck: no error-severity findings (n/a when not installed)
  exec    E1  fails loudly and atomically: run sandboxed (fresh HOME, no
              tarball available, stdin closed, 45s timeout) -> must exit
              nonzero, not hang (124 = fail), say something, and leave no
              binary under the sandbox HOME.

Python 3 stdlib only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE / "workspace" / "iteration-1"

HAVE_SHELLCHECK = shutil.which("shellcheck") is not None

DEFINED_FN_RE = re.compile(r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{",
                           re.MULTILINE)
RISKY_CALL_RE = re.compile(r"^\s*((?:[a-z0-9]+_)*(?:uninstall|install)_[a-z0-9_]+|"
                           r"[a-z0-9_]+_service)\b\s*(?:#.*)?$", re.MULTILINE)
GUARD_TOKENS = ("declare -F", "declare -f", "type ", "command -v", "if ", "&&", "||")


def grade_static(text: str) -> list[dict]:
    checks: list[dict] = []

    def add(name: str, passed: bool, evidence: str) -> None:
        checks.append({"text": name, "passed": bool(passed), "evidence": evidence})

    syntax = subprocess.run(["bash", "-n"], input=text, capture_output=True, text=True)
    add("A1 bash -n parses", syntax.returncode == 0,
        syntax.stderr.strip()[:160] or "parsed")

    add("A2 set -euo pipefail", bool(re.search(r"set\s+-[a-z]*e[a-z]*uo?\s+pipefail|"
        r"set\s+-euo\s+pipefail", text)),
        "found" if "pipefail" in text else "missing")
    add("A3 trap cleanup on EXIT", bool(re.search(r"trap\s+.*\bEXIT\b", text)), "regex")
    add("A4 proxy honored", bool(re.search(r"HTTPS?_PROXY", text))
        and bool(re.search(r"PROXY_ARGS|--proxy|proxy_args", text)), "regex")
    add("A5 sha256 verification", bool(re.search(r"sha256sum|shasum", text)), "regex")
    add("A6 umask set", bool(re.search(r"^\s*umask\s+\d+", text, re.MULTILINE)), "regex")
    add("A7 uninstall path present", bool(re.search(r"uninstall", text, re.IGNORECASE)),
        "regex")
    add("A8 final summary box", bool(re.search(r"draw_box|╔|═══", text)), "regex")
    add("A9 documented one-liner with cache-buster",
        bool(re.search(r"curl .*install\.sh.*\|\s*bash", text))
        and bool(re.search(r"date \+%s|\?\$\(date", text)), "regex")
    add("A10 atomic lock", bool(re.search(r"\bflock\b|mkdir\s+\"?\$\{?[A-Za-z_]*[Ll]ock",
        text)), "regex")

    defined = set(DEFINED_FN_RE.findall(text))
    unguarded = []
    for line in text.splitlines():
        match = RISKY_CALL_RE.match(line)
        if not match:
            continue
        name = match.group(1)
        if name in defined:
            continue
        if any(tok in line for tok in GUARD_TOKENS):
            continue
        unguarded.append(name)
    add("A11 no unguarded undefined helper call", not unguarded,
        f"unguarded: {sorted(set(unguarded))}" if unguarded else "clean")

    if HAVE_SHELLCHECK:
        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as handle:
            handle.write(text)
            tmp = handle.name
        try:
            sc = subprocess.run(
                ["shellcheck", "--severity=error", "--format=json", tmp],
                capture_output=True, text=True,
            )
            try:
                errors = json.loads(sc.stdout or "[]")
            except json.JSONDecodeError:
                errors = []
            add("A12 shellcheck no errors", len(errors) == 0,
                f"{len(errors)} error(s)")
        finally:
            os.unlink(tmp)

    return checks


def grade_exec(text: str) -> dict:
    sandbox = Path(tempfile.mkdtemp(prefix="cbi-e1-"))
    try:
        script = sandbox / "install.sh"
        script.write_text(text)
        env = {
            "HOME": str(sandbox), "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8", "TERM": "dumb",
        }
        proc = subprocess.run(
            ["timeout", "45", "bash", str(script)],
            cwd=sandbox, env=env, capture_output=True, text=True,
            stdin=subprocess.DEVNULL,
        )
        binaries = [p for p in sandbox.rglob("*")
                    if p.is_file() and os.access(p, os.X_OK)
                    and p.name != "install.sh" and "/tmp" not in str(p.relative_to(sandbox))]
        said_something = bool(proc.stderr.strip() or proc.stdout.strip())
        passed = (proc.returncode not in (0, 124)) and said_something and not binaries
        evidence = (f"exit={proc.returncode} output={'yes' if said_something else 'no'} "
                    f"leftover_binaries={[str(b) for b in binaries][:3]}")
        return {"text": "E1 fails loudly and atomically (sandboxed run)",
                "passed": passed, "evidence": evidence}
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def main() -> None:
    if not HAVE_SHELLCHECK:
        print("note: shellcheck not installed — A12 skipped for every run")
    graded = 0
    for run_dir in sorted(WORKSPACE.glob("eval-*/*/run-*")):
        script_path = run_dir / "outputs" / "install.sh"
        if not script_path.exists():
            continue
        text = script_path.read_text()
        expectations = grade_static(text)
        expectations.append(grade_exec(text))
        passed = sum(1 for e in expectations if e["passed"])
        static = [e for e in expectations if not e["text"].startswith("E1")]
        static_passed = sum(1 for e in static if e["passed"])
        (run_dir / "grading.json").write_text(json.dumps({
            # pass_rate feeds tune.py compare --skill-creator directly;
            # pass_rate_static excludes E1, whose sandbox collides with the
            # skill's own build-from-source mandate (both conditions obey it
            # and install a real toolchain, which E1 counts as non-atomic).
            "pass_rate": passed / len(expectations),
            "pass_rate_static": static_passed / len(static),
            "expectations": expectations,
        }, indent=2) + "\n")
        rel = run_dir.relative_to(WORKSPACE)
        print(f"{rel}: {passed}/{len(expectations)}")
        graded += 1
    print(f"graded {graded} runs")


if __name__ == "__main__":
    main()
