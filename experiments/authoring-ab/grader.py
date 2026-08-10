#!/usr/bin/env python3
"""Deterministic grader for the authoring A/B — doctrine-neutral on purpose.

Every assertion derives from Anthropic's published skill guidance (the
skill-creator plugin's authoring guide and the Agent Skills spec) or from
task fidelity to the brief — never from either competing doctrine's own
rules, because grading with one contestant's rulebook is how a Goodhart
loop closes. Writes grading.json beside each generated SKILL.md and a
paired-scores JSON per condition for `tune.py compare --paired-json`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE / "workspace"

# Task-fidelity tokens per brief: concrete facts the brief says the skill
# must carry. Missing one means the authored skill dropped load-bearing
# content, whichever doctrine wrote it.
FIDELITY = {
    "pdf-invoice-extractor": ["extract.py", "OCR", "--currency"],
    "staging-deploy": ["rollback-staging", "healthz", "db:migrate:staging"],
    "sql-migration-review": ["CONCURRENTLY", "backfill", "two-phase"],
    "weekly-metrics-digest": ["10%", "an4", "Flags"],
    "incident-triage": ["pd ack", "30", "CODEOWNERS"],
    "brand-image-alt-text": ["125", 'alt=""', "verbatim"],
}

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
TRIGGER_RE = re.compile(r"use (when|this|it)|when (the user|a user|you)|whenever",
                        re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\bTODO\b|\bFIXME\b|lorem ipsum|<placeholder>", re.IGNORECASE)


def grade(text: str, brief_id: str) -> list[dict]:
    checks = []

    def add(name, passed, evidence=""):
        checks.append({"text": name, "passed": bool(passed), "evidence": evidence})

    fm = FRONTMATTER_RE.match(text)
    name_m = desc = None
    if fm:
        name_m = re.search(r"^name:\s*(\S+)", fm.group(1), re.MULTILINE)
        dm = re.search(r"description:\s*(>-?\s*)?(.*?)(?=\n[a-zA-Z_-]+:|\Z)",
                       fm.group(1), re.DOTALL)
        desc = " ".join(dm.group(2).split()) if dm else None
    add("A1 frontmatter with name and description", bool(fm and name_m and desc))
    add("A2 kebab-case name <=64 chars",
        bool(name_m and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name_m.group(1))
             and len(name_m.group(1)) <= 64),
        name_m.group(1) if name_m else "no name")
    add("A3 description states when to trigger",
        bool(desc and TRIGGER_RE.search(desc)), (desc or "")[:80])
    add("A4 description within spec length", bool(desc and len(desc) <= 1024),
        f"{len(desc or '')} chars")
    body = text[fm.end():] if fm else text
    add("A5 body under 500 lines", len(body.splitlines()) < 500,
        f"{len(body.splitlines())} lines")
    add("A6 contains a concrete example or command block",
        "```" in body or bool(re.search(r"^\s{4,}\S", body, re.MULTILINE)))
    add("A7 no placeholder debris", not PLACEHOLDER_RE.search(text))
    tokens = FIDELITY[brief_id]
    missing = [t for t in tokens if t not in text]
    add("A8 brief fidelity (load-bearing facts carried)", not missing,
        f"missing: {missing}" if missing else "all present")
    return checks


def main() -> None:
    per_condition: dict[str, dict[str, list[float]]] = {}
    for skill_path in sorted(WORKSPACE.glob("*/*/run-*/SKILL.md")):
        run_dir = skill_path.parent
        brief_id = run_dir.parents[1].name
        condition = run_dir.parents[0].name
        checks = grade(skill_path.read_text(), brief_id)
        passed = sum(1 for c in checks if c["passed"])
        rate = passed / len(checks)
        (run_dir / "grading.json").write_text(json.dumps(
            {"pass_rate": rate, "expectations": checks}, indent=2) + "\n")
        per_condition.setdefault(condition, {}).setdefault(brief_id, []).append(rate)
        print(f"{brief_id}/{condition}/{run_dir.name}: {passed}/{len(checks)}")

    for condition, briefs in per_condition.items():
        scores = {b: sum(v) / len(v) for b, v in sorted(briefs.items())}
        out = HERE / f"scores-{condition}.json"
        out.write_text(json.dumps(scores, indent=2) + "\n")
        print(f"wrote {out.name}: {scores}")


if __name__ == "__main__":
    main()
