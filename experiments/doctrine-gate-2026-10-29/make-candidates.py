#!/usr/bin/env python3
"""Generate the candidate doctrine files for the swapgate8 round.

Usage: make-candidates.py [--description original|candidate]

Reads skills/skill-tuner/SKILL.md and writes candidates/{desc-only,c68,c69a,
combined}.SKILL.md. Every edit is anchored on text that must occur exactly
once, so a drifted base file fails loudly instead of producing a silently
different candidate. Prints each output's sha256 so the summary can show
that landed bytes equal gated bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
BASE = REPO / "skills" / "skill-tuner" / "SKILL.md"
OUT = HERE / "candidates"

ORIGINAL_DESCRIPTION = (
    "description: Evidence-tagged rules for writing documents agents consume. "
    "Use when creating or editing skills, AGENTS.md, or CLAUDE.md.\n"
)
CANDIDATE_DESCRIPTION = (
    "description: Evidence-tagged rules for writing documents agents consume. "
    "Use when creating, editing, or shortening skills, AGENTS.md, or CLAUDE.md.\n"
)

# c69a: these sentences leave the Single-source-of-truth paragraph and become
# their own bullet, placed first among the section's bullets.
ENV_SENTENCES = (
    " The environment is a source of truth too: `package.json`, config, "
    "`--help` output. A document restating a one-command lookup is a cache, "
    "and caching earns its load only when the lookup is expensive — cache "
    "what the agent cannot find by looking, the unwritten convention, the "
    "reason behind a choice, the gotcha no config confesses, and leave the "
    "one-command lookups to the environment, where they cannot go stale."
)
ENV_BULLET = (
    "- **The environment is a source of truth too** [craft] — `package.json`, "
    "config, `--help` output: a document restating a one-command lookup is a "
    "cache, and caching earns its load only when the lookup is expensive — "
    "cache what the agent cannot find by looking, the unwritten convention, "
    "the reason behind a choice, the gotcha no config confesses, and leave "
    "the one-command lookups to the environment, where they cannot go stale.\n"
)
RELEVANCE_BULLET_START = "- **Relevance and sediment** [craft]"

# c68: one new bullet between Relevance-and-sediment and the [measured] no-op
# bullet, so the measured rule keeps the section's terminal position.
NOOP_BULLET_START = "- **No-op verdicts are time-relative** [measured]"
RULE_BULLET = (
    "- **Rule, not incident** [craft] — when a lesson earns a line, write the "
    "behaviour it asks for as one positive rule and leave the incident that "
    "taught it to the commit message: a one-clause reason rides along, a "
    "dated account of what went wrong does not, because the agent reads a "
    "story as the one case to avoid rather than the rule to follow.\n"
)


def once(text: str, needle: str) -> None:
    count = text.count(needle)
    if count != 1:
        sys.exit(f"anchor occurs {count} times, expected 1: {needle[:60]!r}")


def apply_description(text: str, which: str) -> str:
    once(text, ORIGINAL_DESCRIPTION)
    if which == "original":
        return text
    return text.replace(ORIGINAL_DESCRIPTION, CANDIDATE_DESCRIPTION)


def apply_c69a(text: str) -> str:
    once(text, ENV_SENTENCES)
    once(text, RELEVANCE_BULLET_START)
    text = text.replace(ENV_SENTENCES, "")
    return text.replace(RELEVANCE_BULLET_START, ENV_BULLET + RELEVANCE_BULLET_START)


def apply_c68(text: str) -> str:
    once(text, NOOP_BULLET_START)
    return text.replace(NOOP_BULLET_START, RULE_BULLET + NOOP_BULLET_START)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--description", choices=("original", "candidate"), default="original")
    args = parser.parse_args()

    base = apply_description(BASE.read_text(encoding="utf-8"), args.description)
    variants = {
        "desc-only": base,
        "c68": apply_c68(base),
        "c69a": apply_c69a(base),
        "combined": apply_c68(apply_c69a(base)),
    }
    OUT.mkdir(exist_ok=True)
    for name, text in variants.items():
        path = OUT / f"{name}.SKILL.md"
        path.write_text(text, encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        print(f"{digest[:12]}  {path.relative_to(REPO)}  ({len(text)} bytes)")
    print(f"description: {args.description}")


if __name__ == "__main__":
    main()
