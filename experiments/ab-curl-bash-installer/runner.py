#!/usr/bin/env python3
"""End-task A/B runner: generate install.sh under each skill condition.

For every (case x condition x trial) it makes one `claude -p` call carrying
the condition's full skill text (SKILL.md + references/PATTERNS.md) inline
plus the case prompt, and saves the generated script under a
skill-creator-shaped workspace tree:

    workspace/iteration-1/eval-<n>-<id>/<condition>/run-<t>/outputs/install.sh

Python 3 stdlib only. Costs are read from the CLI's JSON envelope and summed.
The only thing that differs between conditions is the skill text — same
prompt shape, same model, same envelope — so the difference measures the
skill edit, nothing else.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAP = Path("/tmp/ab-cbi-2c80")

SKILL_FILES = {
    "old_skill": (SNAP / "old-SKILL.md", SNAP / "old-PATTERNS.md"),
    "new_skill": (SNAP / "new-SKILL.md", SNAP / "new-PATTERNS.md"),
}

FENCE_RE = re.compile(r"\A```(?:bash|sh)?\n(.*)\n```\s*\Z", re.DOTALL)


def build_prompt(skill_md: str, patterns_md: str, task: str) -> str:
    return (
        "You are writing a production install script and you have this skill "
        "loaded. Follow it.\n\n"
        "=== SKILL: curl-bash-installer ===\n"
        f"{skill_md}\n\n"
        "=== REFERENCE: references/PATTERNS.md ===\n"
        f"{patterns_md}\n"
        "=== END SKILL ===\n\n"
        f"Task: {task}\n\n"
        "Respond directly with plain text in this reply — do not use any "
        "tools. Output ONLY the complete contents of install.sh — no "
        "commentary, no markdown fences."
    )


def call_claude(prompt: str, model: str) -> tuple[str, float]:
    # A full production installer is a long single completion; give it room,
    # and retry once on timeout before giving up on the run.
    last_error: Exception | None = None
    for _ in range(2):
        try:
            # Single-completion envelope, enforced twice over: tools are
            # disallowed (otherwise the model spends turn 1 writing the file
            # via the Write tool) and --max-turns 1 caps the loop. Without
            # both, one generation ran 868s/$2.87 agentically, and with only
            # max-turns it died error_max_turns after a $0.51 tool attempt
            # (both measured 2026-08-08). All runs must share this envelope;
            # a run made without it is not comparable.
            result = subprocess.run(
                ["claude", "-p", prompt, "--output-format", "json",
                 "--model", model, "--max-turns", "1",
                 "--disallowedTools",
                 "Bash,Write,Edit,Read,Glob,Grep,Task,TodoWrite,WebFetch,WebSearch,NotebookEdit"],
                capture_output=True, text=True, timeout=1200,
            )
        except subprocess.TimeoutExpired as exc:
            last_error = exc
            continue
        if result.returncode != 0:
            # The real error type lives in the stdout JSON (subtype), not in
            # stderr, which carries only auth warnings.
            detail = result.stderr[:150]
            try:
                detail = json.loads(result.stdout).get("subtype", detail)
            except (json.JSONDecodeError, ValueError):
                pass
            last_error = RuntimeError(f"claude -p failed: {detail}")
            continue
        payload = json.loads(result.stdout)
        text = payload.get("result", "")
        match = FENCE_RE.match(text.strip())
        if match:
            text = match.group(1)
        return text, float(payload.get("total_cost_usd") or 0.0)
    raise RuntimeError(f"call failed after retry: {last_error}")


def run_one(job: dict) -> str:
    run_dir = job["run_dir"]
    run_dir.mkdir(parents=True, exist_ok=True)
    target = run_dir / "install.sh"
    if target.exists():
        return f"skip {job['label']} (exists)"
    started = time.time()
    try:
        script, cost = call_claude(job["prompt"], job["model"])
    except Exception as exc:  # keep the batch going; the grader skips holes
        return f"FAIL {job['label']}: {exc}"
    target.write_text(script)
    (run_dir.parent / "meta.json").write_text(json.dumps({
        "case": job["case"], "condition": job["condition"], "trial": job["trial"],
        "cost_usd": cost, "seconds": round(time.time() - started, 1),
        "model": job["model"], "chars": len(script),
    }, indent=2))
    return f"done {job['label']} ${cost:.4f} {len(script)}ch"


def main() -> None:
    from concurrent.futures import ThreadPoolExecutor

    config = json.loads((HERE / "cases.json").read_text())
    model = config["model"]
    workspace = HERE / "workspace" / "iteration-1"

    jobs = []
    for index, case in enumerate(config["cases"]):
        for condition in config["conditions"]:
            skill_md = SKILL_FILES[condition][0].read_text()
            patterns_md = SKILL_FILES[condition][1].read_text()
            prompt = build_prompt(skill_md, patterns_md, case["prompt"])
            for trial in range(1, config["trials"] + 1):
                jobs.append({
                    "case": case["id"], "condition": condition, "trial": trial,
                    "model": model, "prompt": prompt,
                    "label": f"{case['id']}/{condition}/run-{trial}",
                    "run_dir": (workspace / f"eval-{index}-{case['id']}"
                                / condition / f"run-{trial}" / "outputs"),
                })

    with ThreadPoolExecutor(max_workers=4) as pool:
        for line in pool.map(run_one, jobs):
            print(line, flush=True)

    costs = [json.loads(p.read_text())["cost_usd"]
             for p in workspace.glob("eval-*/*/run-*/meta.json")]
    print(f"TOTAL runs={len(costs)} cost=${sum(costs):.4f}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
