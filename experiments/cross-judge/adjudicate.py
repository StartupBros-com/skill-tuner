#!/usr/bin/env python3
"""Blind cross-model adjudication of claude-confirmed probe findings.

Every scoring run in this repo to date used a claude-family judge on
claude-authored documents. This experiment sends each confirmed finding from
two banked legs to a non-Claude frontier model (codex CLI, profile `auto`)
for adversarial re-adjudication, blind:

- the judge sees the banked-time document content INLINE (reconstructed and
  hash-verified by reconstruct.py) and never a file path — the current files
  on disk have since been fixed, so a path would unblind and contaminate;
- the judge sees the claim as quote + issue only — no rule name (rule names
  carry doctrine vocabulary that identifies the leg), no leg, no mention
  that another model confirmed it;
- the judge is instructed to refute, mirroring the probe's own skeptics.

Output: adjudications.jsonl (one line per finding, leg recorded here but
never shown to the judge). Stdlib only. Cost: codex subscription; no API
dollars.
"""
import argparse
import concurrent.futures
import json
import pathlib
import subprocess
import sys
import tempfile
import threading

SCHEMA = {
    "type": "object",
    "properties": {
        "quote_present": {
            "type": "boolean",
            "description": "Does the quoted text appear in the document (allowing whitespace differences)?",
        },
        "genuine": {
            "type": "boolean",
            "description": "Does the claimed defect survive your attempt to refute it?",
        },
        "reason": {"type": "string", "description": "<=60 words"},
    },
    "required": ["quote_present", "genuine", "reason"],
    "additionalProperties": False,
}

PROMPT = """You are auditing one claimed defect in a skill document written for AI agents \
(instructions an agent loads before acting). Your job is adversarial: try to REFUTE \
the claim. Report genuine=true only if the claim survives your refutation attempt — \
the quoted text exists, the stated issue is factually accurate about this document, \
and it describes a real defect (wasted context, contradiction, unverifiable rule, \
drift risk), not a stylistic preference.

Do not run any commands or tools. Judge only from the text provided here.

THE CLAIM
Quoted text: {quote}

Claimed issue: {issue}

THE DOCUMENT
<document>
{document}
</document>"""

print_lock = threading.Lock()


def run_one(item: dict, docs_dir: pathlib.Path, schema_path: str,
            retries: int = 2) -> dict:
    doc = (docs_dir / item["doc_file"]).read_text()
    prompt = PROMPT.format(quote=item["target_quote"], issue=item["issue"],
                           document=doc)
    for attempt in range(retries + 1):
        with tempfile.NamedTemporaryFile("r", suffix=".json") as out:
            r = subprocess.run(
                ["codex", "exec", "--profile", "auto", "-s", "read-only",
                 "--skip-git-repo-check", "--ephemeral",
                 "--output-schema", schema_path, "-o", out.name, "-"],
                input=prompt, text=True, capture_output=True, timeout=600)
            model = next((ln.split("model:")[-1].strip()
                          for ln in r.stderr.splitlines() if "model:" in ln), "")
            try:
                verdict = json.loads(out.file.read() or "null")
            except json.JSONDecodeError:
                verdict = None
        if r.returncode == 0 and isinstance(verdict, dict):
            with print_lock:
                print(f"  {item['id']}: genuine={verdict['genuine']} "
                      f"quote_present={verdict['quote_present']}")
            return {**item, **verdict, "judge_model": model,
                    "attempts": attempt + 1}
    return {**item, "error": f"failed after {retries + 1} attempts",
            "judge_model": model, "attempts": retries + 1}


def load_findings(report_path: str, leg: str, index_path: pathlib.Path) -> list:
    report = json.load(open(report_path))
    index = json.loads(index_path.read_text())
    items = []
    for i, f in enumerate(report["probe"]["confirmed_findings"]):
        items.append({
            "id": f"{leg}-{i:02d}",
            "leg": leg,
            "skill": pathlib.Path(f["target_file"]).parent.name,
            "rule": f["rule"],
            "doc_file": index[f["target_file"]],
            "target_quote": f["target_quote"],
            "issue": f["issue"],
        })
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs-dir", required=True,
                    help="reconstruct.py output dir (index.json + docs)")
    ap.add_argument("--leg", action="append", nargs=2, required=True,
                    metavar=("NAME", "REPORT_JSON"),
                    help="leg name and its report.json; repeatable")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0,
                    help="pilot: only the first N findings overall")
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()

    docs_dir = pathlib.Path(args.docs_dir)
    items = []
    for name, report in args.leg:
        items.extend(load_findings(report, name, docs_dir / "index.json"))
    if args.limit:
        items = items[:args.limit]
    print(f"adjudicating {len(items)} findings with {args.workers} workers")

    schema_file = tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False)
    json.dump(SCHEMA, schema_file)
    schema_file.close()

    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(
            lambda it: run_one(it, docs_dir, schema_file.name), items))

    with open(args.out, "w") as fh:
        for row in results:
            fh.write(json.dumps(row) + "\n")
    errors = [r for r in results if "error" in r]
    print(f"wrote {len(results)} rows -> {args.out} ({len(errors)} errors)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
