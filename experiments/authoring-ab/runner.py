#!/usr/bin/env python3
"""Authoring A/B runner: write a SKILL.md under each doctrine.

For every (brief x condition x trial), one single-completion call through
``tune.call_adapter`` -- the exact envelope every banked receipt used
(tools disabled, no session persistence), so nothing here can go agentic
the way the first end-task A/B's ad-hoc runner did. The only difference
between conditions is which doctrine text rides in the prompt.

Outputs land under workspace/<brief>/<condition>/run-<t>/SKILL.md with a
meta.json beside each. Python 3 stdlib only; resumable (existing outputs
are skipped).
"""

from __future__ import annotations

import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skills" / "skill-tuner" / "scripts"))

import tune  # noqa: E402

DOCTRINES = {
    "ancestor": Path("/tmp/authoring-ab-2c80/ancestor.md"),
    "ours": Path("/tmp/authoring-ab-2c80/ours.md"),
}

FENCE_RE = re.compile(r"\A```(?:markdown|md)?\n(.*)\n```\s*\Z", re.DOTALL)


def build_prompt(doctrine: str, brief: str) -> str:
    return (
        "You write documents for AI agents, and you follow this authoring "
        "doctrine:\n\n"
        "=== AUTHORING DOCTRINE ===\n"
        f"{doctrine}\n"
        "=== END DOCTRINE ===\n\n"
        f"Task: {brief}\n\n"
        "Respond directly with plain text — do not use any tools. Output "
        "ONLY the complete contents of the SKILL.md file (YAML frontmatter "
        "with name and description, then the body) — no commentary, no "
        "outer markdown fences."
    )


def run_one(job: dict) -> str:
    out_dir = job["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "SKILL.md"
    if target.exists():
        return f"skip {job['label']}"
    started = time.time()
    try:
        result = tune.call_adapter(job["prompt"], job["model"])
    except Exception as exc:
        return f"FAIL {job['label']}: {exc}"
    text = result.text
    match = FENCE_RE.match(text.strip())
    if match:
        text = match.group(1)
    target.write_text(text)
    (out_dir / "meta.json").write_text(json.dumps({
        "brief": job["brief"], "condition": job["condition"], "trial": job["trial"],
        "cost_usd": result.cost_usd, "seconds": round(time.time() - started, 1),
        "model": job["model"], "model_resolved": result.model_resolved,
        "chars": len(text),
    }, indent=2))
    return f"done {job['label']} ${result.cost_usd:.4f} {len(text)}ch"


def main() -> None:
    config = json.loads((HERE / "briefs.json").read_text())
    jobs = []
    for brief in config["briefs"]:
        for condition in config["conditions"]:
            doctrine = DOCTRINES[condition].read_text()
            prompt = build_prompt(doctrine, brief["prompt"])
            for trial in range(1, config["trials"] + 1):
                jobs.append({
                    "brief": brief["id"], "condition": condition, "trial": trial,
                    "model": config["model"], "prompt": prompt,
                    "label": f"{brief['id']}/{condition}/run-{trial}",
                    "out_dir": HERE / "workspace" / brief["id"] / condition / f"run-{trial}",
                })
    with ThreadPoolExecutor(max_workers=4) as pool:
        for line in pool.map(run_one, jobs):
            print(line, flush=True)
    costs = [json.loads(p.read_text())["cost_usd"]
             for p in (HERE / "workspace").rglob("meta.json")]
    print(f"TOTAL runs={len(costs)} cost=${sum(costs):.4f}", flush=True)


if __name__ == "__main__":
    main()
