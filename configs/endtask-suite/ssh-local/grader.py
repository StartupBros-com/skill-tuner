#!/usr/bin/env python3
"""Deterministic grader for the ssh-local A/B suite (batch-3 sshpass-dedup edit).

Invocation (endtask contract): python3 grader.py <output_file> <case_id> <condition>
Prints ONLY a JSON object {"pass_rate": float, "expectations": [...]} to
stdout. Never raises and always exits 0 -- an ungradeable / off-topic
output scores pass_rate 0.0, not a traceback. `condition` is accepted for
signature compatibility but never inspected (logging only, per contract).
Python 3 stdlib only.
"""

from __future__ import annotations

import json
import re
import sys


def _search(pattern: str, text: str, flags: int = re.IGNORECASE) -> bool:
    return re.search(pattern, text, flags) is not None


def _c(name: str, ok: object) -> dict:
    return {"name": name, "ok": bool(ok)}


def _same_line_both(pattern_a: str, pattern_b: str, text: str) -> bool:
    """True if patterns a and b both appear on the same line, in either order."""
    for line in text.splitlines():
        if re.search(pattern_a, line, re.IGNORECASE) and re.search(pattern_b, line, re.IGNORECASE):
            return True
    return False


# --------------------------------------------------------------------------
# Case 1: generic password-auth non-interactive construction
# --------------------------------------------------------------------------
def grade_password_env_basic(text: str) -> list[dict]:
    return [
        _c("uses sshpass", _search(r"\bsshpass\b", text)),
        _c("sshpass in env mode (-e), not -p on the command line",
           _search(r"sshpass\s+-e\b", text)),
        _c("SSHPASS wired from DEPLOY_PASS",
           _search(r"SSHPASS=[\"']?\$\{?DEPLOY_PASS\}?", text)),
        _c("ConnectTimeout set (bounded wait)",
           _search(r"ConnectTimeout[=\s]+\d+", text)),
        _c("StrictHostKeyChecking=accept-new",
           _search(r"StrictHostKeyChecking[=\s]+accept-new", text)),
        _c("password-auth options present "
           "(PreferredAuthentications=password + PubkeyAuthentication=no)",
           _search(r"PreferredAuthentications[=\s]+password", text)
           and _search(r"PubkeyAuthentication[=\s]+no", text)),
        _c("no BatchMode=yes (it disables password prompting entirely, "
           "breaking sshpass)",
           not _search(r"BatchMode[=\s]+yes", text)),
        _c("no ssh -p <password> anti-pattern (-p is the PORT flag, not a "
           "password flag)",
           not _search(r"ssh\b[^\n]*-p\s+[\"']?\$?\{?DEPLOY_PASS", text)),
    ]


# --------------------------------------------------------------------------
# Case 2: mac-mini specifically -- the host whose worked example was
# collapsed into a cross-reference to the generic recipe (batch-3 edit).
# --------------------------------------------------------------------------
def grade_mac_mini_reachability(text: str) -> list[dict]:
    host_ok = _search(r"\bmac-mini\b", text) or _search(r"100\.94\.108\.13", text)
    return [
        _c("targets the mac-mini host (alias or its Tailscale IP)", host_ok),
        _c("sshpass in env mode (-e)", _search(r"sshpass\s+-e\b", text)),
        _c("SSHPASS wired from MACMINI_PW",
           _search(r"SSHPASS=[\"']?\$\{?MACMINI_PW\}?", text)),
        _c("StrictHostKeyChecking=accept-new",
           _search(r"StrictHostKeyChecking[=\s]+accept-new", text)),
        _c("ConnectTimeout set", _search(r"ConnectTimeout[=\s]+\d+", text)),
        _c("password-auth options present "
           "(PreferredAuthentications=password + PubkeyAuthentication=no)",
           _search(r"PreferredAuthentications[=\s]+password", text)
           and _search(r"PubkeyAuthentication[=\s]+no", text)),
        _c("trailing command is a lightweight reachability probe "
           "(hostname/whoami/true/echo), not left off or heavyweight",
           _search(r"['\"]?\bhostname\b['\"]?", text)
           or _search(r"['\"]?\bwhoami\b['\"]?", text)
           or _search(r"['\"]?\btrue\b['\"]?", text)
           or _search(r"\becho\b", text)),
        _c("no BatchMode=yes (breaks password auth)",
           not _search(r"BatchMode[=\s]+yes", text)),
    ]


# --------------------------------------------------------------------------
# Case 3: file copy over password auth
# --------------------------------------------------------------------------
def grade_scp_password_copy(text: str) -> list[dict]:
    return [
        _c("sshpass in env mode (-e)", _search(r"sshpass\s+-e\b", text)),
        _c("SSHPASS wired from OPS_PW",
           _search(r"SSHPASS=[\"']?\$\{?OPS_PW\}?", text)),
        _c("a real copy tool is invoked (scp or rsync)",
           _search(r"\b(scp|rsync)\b", text)),
        _c("password-auth options present "
           "(PreferredAuthentications=password + PubkeyAuthentication=no)",
           _search(r"PreferredAuthentications[=\s]+password", text)
           and _search(r"PubkeyAuthentication[=\s]+no", text)),
        _c("StrictHostKeyChecking=accept-new",
           _search(r"StrictHostKeyChecking[=\s]+accept-new", text)),
        _c("no inline user:password@host URI (not valid scp/ssh syntax, "
           "leaks the password into the command line)",
           not _search(r"ops\s*:\s*\$?\{?OPS_PW\}?\s*@\s*198\.51\.100\.9", text)),
        _c("ConnectTimeout set", _search(r"ConnectTimeout[=\s]+\d+", text)),
        _c("correct local and remote paths (report.csv -> "
           "/home/ops/incoming/)",
           _search(r"report\.csv", text)
           and _search(r"/home/ops/incoming", text)),
    ]


# --------------------------------------------------------------------------
# Case 4: alias resolution when config is split across Include'd config.d
# files -- general SSH competence, not covered verbatim by the skill text.
# --------------------------------------------------------------------------
def grade_config_include_alias(text: str) -> list[dict]:
    uses_ssh_g = _search(r"ssh\s+-G\s+stagingbox\b", text)
    return [
        _c("uses `ssh -G stagingbox` -- the one-command way to see the "
           "fully-resolved effective config, Include'd files and all",
           uses_ssh_g),
        _c("actually engages with the task (mentions both ssh and the "
           "stagingbox alias, not an off-topic non-answer)",
           _search(r"\bssh\b", text) and _search(r"\bstagingbox\b", text)),
        _c("does not fall back to a live connection attempt as the "
           "inspection method (bare `ssh stagingbox` without -G)",
           not _search(r"\bssh\s+stagingbox\b", text)),
        _c("does not tell the user to open the config in an editor "
           "(misses that definitions live in config.d/*.conf)",
           not _same_line_both(
               r"\b(vim|nano|emacs|code|gedit)\b",
               r"(\.ssh|config\.d|ssh[_ ]?config)",
               text)),
        _c("no leftover quoted remote-command argument tacked onto the "
           "-G invocation (ssh -G doesn't run anything remote)",
           not _search(r"ssh\s+-G\s+stagingbox\s+[\"']", text)),
    ]


# --------------------------------------------------------------------------
# Case 5: StrictHostKeyChecking / known-hosts handling on first connect
# --------------------------------------------------------------------------
def grade_first_connect_key_auth(text: str) -> list[dict]:
    return [
        _c("StrictHostKeyChecking=accept-new (trust-on-first-use, not "
           "disabled forever)",
           _search(r"StrictHostKeyChecking[=\s]+accept-new", text)),
        _c("does not blanket-disable host-key checking "
           "(StrictHostKeyChecking=no)",
           not _search(r"StrictHostKeyChecking[=\s]+no\b", text)),
        _c("BatchMode=yes (fine and expected for key auth)",
           _search(r"BatchMode[=\s]+yes", text)),
        _c("IdentitiesOnly=yes", _search(r"IdentitiesOnly[=\s]+yes", text)),
        _c("ConnectTimeout set", _search(r"ConnectTimeout[=\s]+\d+", text)),
        _c("correct key path (-i ~/.ssh/deploy_key)",
           _search(r"-i\s+\S*deploy_key\b", text)),
        _c("correct user@host (deployer@198.51.100.20)",
           _search(r"deployer@198\.51\.100\.20", text)),
        _c("runs the requested remote command (cat /etc/os-release)",
           _search(r"cat\s+/etc/os-release", text)),
    ]


# --------------------------------------------------------------------------
# Case 6: password auth from cron (no controlling tty)
# --------------------------------------------------------------------------
def grade_cron_password_no_tty(text: str) -> list[dict]:
    return [
        _c("sshpass in env mode (-e)", _search(r"sshpass\s+-e\b", text)),
        _c("SSHPASS wired from BATCH_PW",
           _search(r"SSHPASS=[\"']?\$\{?BATCH_PW\}?", text)),
        _c("StrictHostKeyChecking=accept-new",
           _search(r"StrictHostKeyChecking[=\s]+accept-new", text)),
        _c("password-auth options present "
           "(PreferredAuthentications=password + PubkeyAuthentication=no)",
           _search(r"PreferredAuthentications[=\s]+password", text)
           and _search(r"PubkeyAuthentication[=\s]+no", text)),
        _c("ConnectTimeout set", _search(r"ConnectTimeout[=\s]+\d+", text)),
        _c("stdin explicitly closed/redirected (</dev/null) so it can "
           "never block under cron",
           _search(r"<\s*/dev/null", text)),
        _c("no BatchMode=yes (breaks password auth)",
           not _search(r"BatchMode[=\s]+yes", text)),
        _c("runs the requested remote command "
           "(/opt/scripts/nightly.sh)",
           _search(r"/opt/scripts/nightly\.sh", text)),
    ]


# --------------------------------------------------------------------------
# Case 7: restricted automation key -- key generation + authorized_keys
# command= restriction + non-interactive verification, chained together.
# --------------------------------------------------------------------------
def grade_restricted_deploy_key_setup(text: str) -> list[dict]:
    keygen_line_has_no_passphrase = bool(
        re.search(r"ssh-keygen[^\n]*-N\s+[\"']{2}", text)
        or re.search(r"ssh-keygen[^\n]*-N\s+\"\"", text)
        or re.search(r"ssh-keygen[^\n]*-N\s+''", text)
    )
    verify_flags = (
        _search(r"BatchMode[=\s]+yes", text)
        and _search(r"IdentitiesOnly[=\s]+yes", text)
        and _search(r"ConnectTimeout[=\s]+\d+", text)
        and _search(r"StrictHostKeyChecking[=\s]+accept-new", text)
    )
    return [
        _c("generates an Ed25519 key (ssh-keygen -t ed25519)",
           _search(r"ssh-keygen[^\n]*-t\s+ed25519", text)),
        _c("key is generated passphrase-free for unattended use (-N '' )",
           keygen_line_has_no_passphrase),
        _c("uses a dedicated key path, not the default id_ed25519 "
           "(-f <custom path>)",
           _search(r"ssh-keygen[^\n]*-f\s+\S+", text)),
        _c("restricts the authorized_keys entry to the one allowed "
           "command (command=\"...backup.sh...\")",
           _search(r'command\s*=\s*[\"\'][^\"\']*backup\.sh', text)),
        _c("final verification uses all four non-interactive safety "
           "flags together (BatchMode=yes, IdentitiesOnly=yes, "
           "ConnectTimeout, StrictHostKeyChecking=accept-new)",
           verify_flags),
        _c("verification targets runner@203.0.113.99 with -i pointing "
           "at a key",
           _search(r"-i\s+\S+", text)
           and _search(r"runner@203\.0\.113\.99", text)),
    ]


CASE_GRADERS = {
    "password-env-basic": grade_password_env_basic,
    "mac-mini-reachability": grade_mac_mini_reachability,
    "scp-password-copy": grade_scp_password_copy,
    "config-include-alias-resolution": grade_config_include_alias,
    "first-connect-key-auth": grade_first_connect_key_auth,
    "cron-password-no-tty": grade_cron_password_no_tty,
    "restricted-deploy-key-setup": grade_restricted_deploy_key_setup,
}


def main() -> None:
    try:
        output_path, case_id = sys.argv[1], sys.argv[2]
        # sys.argv[3] (condition) is accepted for signature compatibility
        # with the endtask contract but is intentionally never inspected.
        try:
            text = open(output_path, "r", errors="replace").read()
        except OSError:
            text = ""
        grader = CASE_GRADERS.get(case_id)
        if grader is None:
            print(json.dumps({"pass_rate": 0.0, "expectations": [],
                               "error": f"unknown case_id {case_id!r}"}))
            return
        expectations = grader(text)
        total = len(expectations)
        passed = sum(1 for e in expectations if e["ok"])
        pass_rate = (passed / total) if total else 0.0
        print(json.dumps({"pass_rate": pass_rate, "expectations": expectations}))
    except Exception as exc:  # noqa: BLE001 - grader must never crash the harness
        print(json.dumps({"pass_rate": 0.0, "expectations": [],
                           "error": f"{type(exc).__name__}: {exc}"}))


if __name__ == "__main__":
    main()
