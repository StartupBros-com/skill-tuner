#!/usr/bin/env python3
"""Blind pairwise judging for the authoring A/B.

For each (brief, trial) the two conditions' outputs are shown as Document A
and Document B — condition names never appear — judged against a rubric
derived from Anthropic's published skill-authoring guidance (neutral ground:
neither competing doctrine wrote it). Every pair is judged in BOTH
presentation orders; an inconsistent judge (prefers the first slot both
times) scores the pair a tie. Calls go through tune.call_adapter, the same
guarded envelope as everything banked. Resumable via judgments.jsonl.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skills" / "skill-tuner" / "scripts"))

import tune  # noqa: E402

WORKSPACE = HERE / "workspace"
OUT = HERE / "judgments.jsonl"
MODEL = "claude-sonnet-5"

RUBRIC = (
    "You are judging which of two SKILL.md documents would serve an AI agent "
    "better, using these criteria (from Anthropic's published skill-authoring "
    "guidance, in order of weight):\n"
    "1. Would the agent know WHEN to use the skill (clear, specific "
    "triggering description)?\n"
    "2. Could the agent follow it to a correct result (actionable steps, "
    "concrete commands, the task's real constraints and gotchas carried)?\n"
    "3. Is it appropriately concise for an agent's context window (no "
    "padding, no restated boilerplate), while keeping everything "
    "load-bearing?\n"
    "4. Does it explain the why where a rote instruction would mislead?\n"
    "Judge the documents as written; do not reward style for its own sake."
)


def judge_pair(brief_prompt: str, first: str, second: str) -> str:
    prompt = (
        f"{RUBRIC}\n\n"
        f"The task both documents were written for:\n{brief_prompt}\n\n"
        f"=== DOCUMENT A ===\n{first}\n\n=== DOCUMENT B ===\n{second}\n\n"
        "Respond directly with plain text and no tools. First line: exactly "
        "'A' or 'B' (the better document). Second line: one sentence why."
    )
    result = tune.call_adapter(prompt, MODEL)
    verdict = result.text.strip().splitlines()[0].strip().upper()[:1]
    return verdict if verdict in ("A", "B") else "?"


def main() -> None:
    briefs = {b["id"]: b["prompt"]
              for b in json.loads((HERE / "briefs.json").read_text())["briefs"]}
    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            entry = json.loads(line)
            done.add((entry["brief"], entry["trial"]))

    for brief_id, brief_prompt in briefs.items():
        for trial in (1, 2):
            if (brief_id, trial) in done:
                print(f"skip {brief_id}/run-{trial}")
                continue
            try:
                ancestor = (WORKSPACE / brief_id / "ancestor" / f"run-{trial}"
                            / "SKILL.md").read_text()
                ours = (WORKSPACE / brief_id / "ours" / f"run-{trial}"
                        / "SKILL.md").read_text()
            except FileNotFoundError:
                print(f"hole {brief_id}/run-{trial} — skipping")
                continue
            # Order 1: ancestor is A. Order 2: ours is A.
            v1 = judge_pair(brief_prompt, ancestor, ours)
            v2 = judge_pair(brief_prompt, ours, ancestor)
            pick1 = {"A": "ancestor", "B": "ours"}.get(v1, "?")
            pick2 = {"A": "ours", "B": "ancestor"}.get(v2, "?")
            winner = pick1 if pick1 == pick2 and pick1 != "?" else "tie"
            entry = {"brief": brief_id, "trial": trial,
                     "order1_pick": pick1, "order2_pick": pick2, "winner": winner}
            tune.append_jsonl(OUT, entry)
            print(json.dumps(entry))

    wins = {"ours": 0, "ancestor": 0, "tie": 0}
    for line in OUT.read_text().splitlines():
        wins[json.loads(line)["winner"]] += 1
    print(f"\nblind pairwise (order-consistent only): {wins}")


if __name__ == "__main__":
    main()
