#!/usr/bin/env python3
"""The mirror of adjudicate.py: claude blind-adjudicates the NOVEL findings
a non-claude probe produced (recall_probe.py output findings that matched
nothing in claude's own raw set).

Same blindness contract as the GPT direction: document content inline, the
claim as quote + issue only — no rule names (the GPT probe was primed with
the v3 doctrine, so its rule labels carry leg vocabulary), no origin story.
Runs through tune.call_adapter, the guarded claude envelope (no tools, no
session, single turn) — an ad-hoc `claude -p` here would run agentically at
~10x. Prints total spend at the end; sonnet judge, ~$0.02–0.06/call.
"""
import argparse
import concurrent.futures
import json
import pathlib
import re
import sys
import threading

SCRIPTS = pathlib.Path(__file__).resolve().parents[2] / "skills/skill-tuner/scripts"
sys.path.insert(0, str(SCRIPTS))
import tune  # noqa: E402

PROMPT = """You are auditing one claimed defect in a skill document written for AI agents \
(instructions an agent loads before acting). Your job is adversarial: try to REFUTE \
the claim. Report genuine=true only if the claim survives your refutation attempt — \
the quoted text exists, the stated issue is factually accurate about this document, \
and it describes a real defect (wasted context, contradiction, unverifiable rule, \
drift risk), not a stylistic preference.

THE CLAIM
Quoted text: {quote}

Claimed issue: {issue}

THE DOCUMENT
<document>
{document}
</document>

Return ONLY a JSON object with keys "quote_present" (boolean: does the quoted \
text appear in the document, allowing whitespace differences), "genuine" \
(boolean), and "reason" (string, <=60 words). No other text."""

_OBJ_RE = re.compile(r"\{.*\}", re.DOTALL)
print_lock = threading.Lock()


def parse_obj(text: str):
    for candidate in (text, *( [m.group(0)] if (m := _OBJ_RE.search(text)) else [] )):
        try:
            obj = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and {"quote_present", "genuine", "reason"} <= set(obj):
            return obj
    return None


def run_one(item: dict, docs_dir: pathlib.Path, model: str) -> dict:
    doc = (docs_dir / f"{item['doc']}.md").read_text()
    prompt = PROMPT.format(quote=item["target_quote"], issue=item["issue"],
                           document=doc)
    result = tune.call_adapter(prompt, model)
    verdict = parse_obj(result.text)
    if verdict is None:
        return {**item, "error": "unparseable", "cost_usd": result.cost_usd,
                "judge_model": result.model_resolved}
    with print_lock:
        print(f"  {item['id']}: genuine={verdict['genuine']} "
              f"quote_present={verdict['quote_present']}")
    return {**item, **verdict, "cost_usd": result.cost_usd,
            "judge_model": result.model_resolved}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--novel", required=True, help="novel findings JSON list")
    ap.add_argument("--docs-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()

    items = json.load(open(args.novel))
    docs_dir = pathlib.Path(args.docs_dir)
    print(f"claude-adjudicating {len(items)} novel findings")

    with concurrent.futures.ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(
            lambda it: run_one(it, docs_dir, args.model), items))

    with open(args.out, "w") as fh:
        for row in results:
            fh.write(json.dumps(row) + "\n")
    spent = sum(r.get("cost_usd") or 0 for r in results)
    errors = [r for r in results if "error" in r]
    genuine = sum(1 for r in results if r.get("genuine"))
    print(f"wrote {len(results)} rows -> {args.out} "
          f"({len(errors)} errors) | genuine {genuine}/{len(results)} "
          f"| spent ${spent:.4f}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
