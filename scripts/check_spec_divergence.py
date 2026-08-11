#!/usr/bin/env python3
"""Known-divergence tripwire against the agentskills.io reference validator.

skills/tune ships two frontmatter keys the spec's exhaustive field list
rejects: `argument-hint` and `disable-model-invocation`. They are kept
deliberately — both are functional on Claude Code and Cursor, tolerated by
Codex and VS Code, and no portable invocation-policy field exists to replace
them (decision record: PR #32 review thread and PR #38).

The check fails in two directions:

  - skills/tune is rejected for anything beyond exactly those two fields
    (we drifted further from the spec), or
  - skills/tune PASSES the validator (the spec or validator moved — e.g.
    agentskills/agentskills#350 `--allow-field` landed, or the frontmatter
    schema opened per discussion #211). That firing is good news: it means
    the divergence can likely be retired. Revisit the decision.

Requires the reference validator on PATH: `pip install skills-ref==0.1.1`.
Note the installed console command is named `agentskills`, not `skills-ref`
(the 0.1.1 wheel's entry point diverges from the project README).
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXPECTED_DIVERGENCE = {"argument-hint", "disable-model-invocation"}


def validate(skill_dir):
    proc = subprocess.run(
        ["agentskills", "validate", str(skill_dir)],
        capture_output=True, text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def main():
    rc, out = validate(REPO / "skills" / "skill-tuner")
    if rc != 0:
        print(f"FAIL: doctrine skill no longer validates as spec-clean:\n{out}")
        return 1

    rc, out = validate(REPO / "skills" / "tune")
    if rc == 0:
        print(
            "FAIL (good news): skills/tune now PASSES the reference validator - "
            "the spec or validator moved. Revisit the single-file dual-format "
            "decision (PR #38); the divergence can likely be retired.\n" + out
        )
        return 1

    match = re.search(r"Unexpected fields in frontmatter: ([^.]+)\.", out)
    if not match:
        print(f"FAIL: skills/tune was rejected for an unexpected reason:\n{out}")
        return 1

    fields = {f.strip() for f in match.group(1).split(",")}
    if fields != EXPECTED_DIVERGENCE:
        print(
            f"FAIL: divergence set changed: {sorted(fields)} != "
            f"{sorted(EXPECTED_DIVERGENCE)}\n{out}"
        )
        return 1

    print(f"known divergence confirmed: {sorted(EXPECTED_DIVERGENCE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
