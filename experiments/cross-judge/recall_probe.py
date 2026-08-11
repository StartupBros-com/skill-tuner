#!/usr/bin/env python3
"""Recall pilot: a non-Claude judge probes banked-time docs under the banked
v3 doctrine — does it surface genuine defect classes the claude probe never
flagged?

The precision half (adjudicate.py) can only validate findings claude made;
a family-shared blind spot would live in what claude MISSED. This sends the
probe's own inline-doctrine prompt (probe.build_probe_prompt, verbatim,
user-message shape) through the codex CLI for a sample of docs, then the
caller compares finding sets against the banked claude leg.

Envelope note, recorded honestly: the banked claude leg ran
claude-p-doctrine-system-prompt; codex has no equivalent seam, so this uses
the inline shape. Fine for recall (no paired scoring against the claude
leg) — the doctrine and document bytes are identical, hash-verified.

Stdlib only. Cost: codex subscription; no API dollars.
"""
import argparse
import concurrent.futures
import json
import pathlib
import subprocess
import sys
import tempfile

SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "skills/skill-tuner/scripts"
sys.path.insert(0, str(SCRIPTS))
import probe  # noqa: E402  (build_probe_prompt — the real one, not a copy)

SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rule": {"type": "string"},
                    "target_quote": {"type": "string"},
                    "issue": {"type": "string"},
                    "proposed_fix": {"type": "string"},
                },
                "required": ["rule", "target_quote", "issue", "proposed_fix"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["findings"],
    "additionalProperties": False,
}

NO_TOOLS = ("Do not run any commands or tools; audit only the text below.\n\n")


def probe_one(doc_name: str, doctrine: str, docs_dir: pathlib.Path,
              schema_path: str, retries: int = 2) -> dict:
    target = (docs_dir / f"{doc_name}.md").read_text()
    prompt = NO_TOOLS + probe.build_probe_prompt(doctrine, target)
    for attempt in range(retries + 1):
        with tempfile.NamedTemporaryFile("r", suffix=".json") as out:
            r = subprocess.run(
                ["codex", "exec", "--profile", "auto", "-s", "read-only",
                 "--skip-git-repo-check", "--ephemeral",
                 "--output-schema", schema_path, "-o", out.name, "-"],
                input=prompt, text=True, capture_output=True, timeout=900)
            model = next((ln.split("model:")[-1].strip()
                          for ln in r.stderr.splitlines() if "model:" in ln), "")
            try:
                payload = json.loads(out.file.read() or "null")
            except json.JSONDecodeError:
                payload = None
        if r.returncode == 0 and isinstance(payload, dict):
            findings = payload["findings"]
            print(f"  {doc_name}: {len(findings)} findings")
            return {"doc": doc_name, "judge_model": model,
                    "attempts": attempt + 1, "findings": findings}
    return {"doc": doc_name, "judge_model": model, "error": "failed",
            "attempts": retries + 1, "findings": []}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--doctrine", required=True, help="banked doctrine file")
    ap.add_argument("--docs-dir", required=True)
    ap.add_argument("--docs", required=True, help="comma-separated doc stems")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()

    doctrine = pathlib.Path(args.doctrine).read_text()
    docs_dir = pathlib.Path(args.docs_dir)
    names = args.docs.split(",")
    print(f"recall probe over {len(names)} docs")

    schema_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(SCHEMA, schema_file)
    schema_file.close()

    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(
            lambda n: probe_one(n, doctrine, docs_dir, schema_file.name),
            names))

    with open(args.out, "w") as fh:
        for row in results:
            fh.write(json.dumps(row) + "\n")
    errors = [r for r in results if "error" in r]
    print(f"wrote {len(results)} rows -> {args.out} ({len(errors)} errors)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
