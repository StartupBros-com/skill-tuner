#!/usr/bin/env python3
"""skill-tuner marginal-value probe (R11, KTD2).

Applies the skill-tuner doctrine (or any doctrine document) to a target
document and adversarially verifies every finding it raises, so the report
only ever surfaces defects that survived a fresh, skeptical, second look --
the check behind the doctrine's "the probe finds what audits miss" rule.
Python 3 standard library only.

Pipeline, in order:

1. ``load_config`` parses the eval config: ``doctrine_file`` (defaults to
   the bundled ``skills/skill-tuner/SKILL.md``), ``target_file`` (required),
   ``model``, and ``max_findings`` (default 8).
2. ``run_probe_call`` makes ONE adapter call with the doctrine text and the
   full target document inline (KTD2: nothing installed anywhere, no
   out-of-band state), asking for genuine defects as a JSON array; an empty
   array is an explicitly legitimate answer. Malformed JSON retries through
   the same adapter path -- no subprocess, no shared state, just another
   call -- up to ``retries`` bounded attempts.
3. ``cap_findings`` truncates the parsed findings to ``max_findings``,
   recording the overflow count rather than silently dropping it.
4. ``verify_finding`` runs ONE fresh adapter call per capped finding --  a
   self-contained prompt carrying that finding alone plus the full target
   document, never another finding's text, never a shared conversation --
   with a default-refute skeptic instruction: confirm only if the quoted
   text is verbatim in the target and the cited rule genuinely applies. A
   local existence check is the code-level backstop: a CONFIRMED verdict
   for a quote that doesn't literally appear in the target document is
   downgraded to refuted regardless of what the verifier said.
5. ``write_probe_report`` extends tune.py's report machinery
   (``tune.write_report``) with the probe verdict: confirmed findings with
   their evidence quotes, the refuted count, the overflow count, probe/verify
   call counts, and the target/doctrine identifiers. Verdict field:
   ``findings_confirmed: N``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import tune

AdapterFn = Callable[[str, str], tune.AdapterResult]

# The bundled doctrine this probe defaults to when a config doesn't name its
# own: skills/skill-tuner/SKILL.md, resolved from this file's own location
# so the default never depends on the run's base_dir or cwd.
_MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_DOCTRINE_PATH = _MODULE_DIR.parent / "SKILL.md"

DEFAULT_MAX_FINDINGS = 8
DEFAULT_RETRIES = 2


class ProbeParseError(ValueError):
    """Raised when the probe response never yields a valid JSON array after
    exhausting the bounded retry budget."""


# --------------------------------------------------------------------------
# Config loading
# --------------------------------------------------------------------------


def _resolve_path(raw: str, base_dir: Path) -> Path:
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else base_dir / candidate


@dataclass(frozen=True)
class ProbeConfig:
    doctrine_path: Path
    target_path: Path
    model: str
    max_findings: int


def load_config(config: Mapping[str, Any], *, base_dir: Path) -> ProbeConfig:
    """Parse the eval config into a ``ProbeConfig``. ``doctrine_file``
    defaults to the bundled SKILL.md (resolved independent of base_dir);
    ``target_file`` is required and resolved relative to base_dir like every
    other skill-tuner eval config path."""
    doctrine_file = config.get("doctrine_file")
    doctrine_path = _resolve_path(doctrine_file, base_dir) if doctrine_file else DEFAULT_DOCTRINE_PATH

    target_file = config.get("target_file")
    if not target_file:
        raise ValueError("config must name a target_file")

    model = config.get("model")
    if not model:
        raise ValueError("config must name a model pin")

    max_findings = int(config.get("max_findings", DEFAULT_MAX_FINDINGS))
    if max_findings < 1:
        raise ValueError(f"max_findings must be >= 1, got {max_findings}")

    return ProbeConfig(
        doctrine_path=doctrine_path,
        target_path=_resolve_path(target_file, base_dir),
        model=str(model),
        max_findings=max_findings,
    )


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    rule: str
    target_quote: str
    issue: str
    proposed_fix: str

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Finding":
        return cls(
            rule=str(raw.get("rule", "")).strip(),
            target_quote=str(raw.get("target_quote", "")).strip(),
            issue=str(raw.get("issue", "")).strip(),
            proposed_fix=str(raw.get("proposed_fix", "")).strip(),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "rule": self.rule,
            "target_quote": self.target_quote,
            "issue": self.issue,
            "proposed_fix": self.proposed_fix,
        }


# --------------------------------------------------------------------------
# Probe call: doctrine + target document inline, tolerant JSON parse, retry
# --------------------------------------------------------------------------


def build_probe_prompt(doctrine_text: str, target_text: str) -> str:
    return (
        "You are auditing a target document against a doctrine's checks. "
        "Read the doctrine below, then the target document, and report only "
        "genuine defects -- places where the target document violates a "
        "specific rule from the doctrine.\n\n"
        "=== DOCTRINE ===\n"
        f"{doctrine_text}\n\n"
        "=== TARGET DOCUMENT ===\n"
        f"{target_text}\n\n"
        "Return ONLY a JSON array. Each element is an object with keys "
        '"rule" (the doctrine rule violated), "target_quote" (the exact, '
        "verbatim text from the target document that shows the defect), "
        '"issue" (why it violates the rule), and "proposed_fix" (a concrete '
        "fix). An empty array `[]` is a legitimate, expected answer when the "
        "target document has no genuine defects under the doctrine -- do "
        "not manufacture findings just to fill the list. No other text."
    )


_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


def extract_json_array(text: str) -> list[Any] | None:
    """Tolerant JSON-array extraction: try the whole response first, then
    fall back to the widest ``[...]`` slice found inside it (handles
    responses wrapped in prose or a markdown code fence). Returns None if
    nothing in the text parses as a JSON array."""
    stripped = text.strip()
    candidates = [stripped]
    match = _ARRAY_RE.search(stripped)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            return payload
    return None


def run_probe_call(
    doctrine_text: str,
    target_text: str,
    *,
    adapter: AdapterFn,
    model: str,
    retries: int,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """One adapter call carrying the doctrine + target document inline.
    Malformed JSON is retried through the same adapter path -- never
    subprocess -- up to ``retries`` additional bounded attempts. Every
    attempt is recorded in ``rows`` regardless of outcome."""
    prompt = build_probe_prompt(doctrine_text, target_text)
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        result = adapter(prompt, model)
        rows.append(
            {
                "case_id": "probe",
                "trial": attempt + 1,
                "condition": "probe",
                "response": result.text,
                "cost_usd": result.cost_usd,
            }
        )
        payload = extract_json_array(result.text)
        if payload is not None:
            return [item for item in payload if isinstance(item, dict)]
        last_error = ProbeParseError(
            f"probe response was not a JSON array (attempt {attempt + 1}): {result.text!r}"
        )

    raise ProbeParseError(
        f"probe call failed to yield valid JSON after {retries + 1} attempt(s): {last_error}"
    ) from last_error


def cap_findings(
    raw_findings: Sequence[Mapping[str, Any]], max_findings: int
) -> tuple[list[Finding], int]:
    """Truncate parsed findings to ``max_findings``, returning (capped,
    overflow_count) so the overflow is recorded rather than silently lost."""
    findings = [Finding.from_dict(item) for item in raw_findings]
    capped = findings[:max_findings]
    overflow = max(0, len(findings) - max_findings)
    return capped, overflow


# --------------------------------------------------------------------------
# Verify: one fresh, self-contained adapter call per finding
# --------------------------------------------------------------------------


def build_verify_prompt(finding: Finding, target_text: str) -> str:
    return (
        "You are a skeptical verifier. Default to REFUTED unless the "
        "evidence clearly holds. You are shown ONE candidate finding and "
        "the target document it claims to be about -- nothing else. "
        "Confirm it ONLY if (a) the quoted text appears verbatim in the "
        "target document, and (b) the cited rule genuinely applies to that "
        "text as described. Otherwise, refute it.\n\n"
        "=== TARGET DOCUMENT ===\n"
        f"{target_text}\n\n"
        "=== CANDIDATE FINDING ===\n"
        f"Rule: {finding.rule}\n"
        f"Quoted text: {finding.target_quote}\n"
        f"Issue: {finding.issue}\n"
        f"Proposed fix: {finding.proposed_fix}\n\n"
        "Answer on the first line with exactly one word, CONFIRMED or "
        "REFUTED, followed by a one-line reason."
    )


def parse_verify_answer(text: str) -> str:
    """Normalize a verifier response to 'confirmed' or 'refuted'. Ambiguous
    or unparseable text defaults to refuted (skeptic default)."""
    upper = text.strip().upper()
    if upper.startswith("CONFIRMED"):
        return "confirmed"
    if upper.startswith("REFUTED"):
        return "refuted"
    has_confirmed = re.search(r"\bCONFIRMED\b", upper) is not None
    has_refuted = re.search(r"\bREFUTED\b", upper) is not None
    if has_confirmed and not has_refuted:
        return "confirmed"
    return "refuted"


@dataclass(frozen=True)
class VerifiedFinding:
    finding: Finding
    verdict: str  # "confirmed" | "refuted"
    reason: str


def verify_finding(
    finding: Finding,
    *,
    target_text: str,
    adapter: AdapterFn,
    model: str,
    case_id: str,
    rows: list[dict[str, Any]],
) -> VerifiedFinding:
    """ONE fresh adapter call for this finding alone. The quote-existence
    check is a code-level guard: the verifier cannot confirm a quote that
    isn't actually in the target document, no matter what it answers."""
    prompt = build_verify_prompt(finding, target_text)
    result = adapter(prompt, model)
    rows.append(
        {
            "case_id": case_id,
            "trial": 1,
            "condition": "verify",
            "response": result.text,
            "cost_usd": result.cost_usd,
        }
    )

    verdict = parse_verify_answer(result.text)
    quote_present = bool(finding.target_quote) and finding.target_quote in target_text

    if verdict == "confirmed" and not quote_present:
        return VerifiedFinding(
            finding=finding,
            verdict="refuted",
            reason="downgraded: quoted text not found verbatim in target document",
        )

    return VerifiedFinding(finding=finding, verdict=verdict, reason=result.text.strip())


# --------------------------------------------------------------------------
# Report (extends tune.py's report machinery)
# --------------------------------------------------------------------------


def write_probe_report(
    run_dir: Path,
    rows: Sequence[dict[str, Any]],
    *,
    confirmed: Sequence[VerifiedFinding],
    refuted_count: int,
    overflow: int,
    probe_calls: int,
    verify_calls: int,
    doctrine_path: Path,
    target_path: Path,
) -> tuple[Path, Path]:
    json_path, md_path = tune.write_report(run_dir, rows, ("probe", "verify"))

    confirmed_findings = [
        {**entry.finding.to_dict(), "reason": entry.reason} for entry in confirmed
    ]

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    summary["probe"] = {
        "findings_confirmed": len(confirmed),
        "refuted_count": refuted_count,
        "overflow": overflow,
        "probe_calls": probe_calls,
        "verify_calls": verify_calls,
        "doctrine_file": str(doctrine_path),
        "target_file": str(target_path),
        "confirmed_findings": confirmed_findings,
    }
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "",
        "## Marginal-value probe verdict",
        "",
        f"**findings_confirmed: {len(confirmed)}**",
        "",
        f"- doctrine: {doctrine_path}",
        f"- target: {target_path}",
        f"- probe calls: {probe_calls}",
        f"- verify calls: {verify_calls}",
        f"- refuted: {refuted_count}",
    ]
    if overflow:
        lines.append(f"- overflow (beyond max_findings cap, not verified): {overflow}")
    lines.append("")

    if confirmed_findings:
        lines.append("### Confirmed findings")
        lines.append("")
        for entry in confirmed_findings:
            lines.append(f"- **{entry['rule']}**: {entry['issue']}")
            lines.append(f"  - quote: \"{entry['target_quote']}\"")
            lines.append(f"  - proposed fix: {entry['proposed_fix']}")
        lines.append("")

    with md_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    return json_path, md_path


# --------------------------------------------------------------------------
# Orchestrator
# --------------------------------------------------------------------------


def run_probe(
    config: Mapping[str, Any],
    adapter: AdapterFn,
    run_dir: Path,
    base_dir: Path | None = None,
    *,
    retries: int = DEFAULT_RETRIES,
) -> dict[str, Any]:
    """Run the full marginal-value probe pipeline: one probe call (doctrine
    + target inline), cap findings, one fresh self-contained verify call per
    capped finding, then report. Every model call goes through ``adapter``."""
    resolved_base_dir = base_dir if base_dir is not None else Path(".")
    probe_config = load_config(config, base_dir=resolved_base_dir)

    doctrine_text = probe_config.doctrine_path.read_text(encoding="utf-8")
    target_text = probe_config.target_path.read_text(encoding="utf-8")

    rows: list[dict[str, Any]] = []

    raw_findings = run_probe_call(
        doctrine_text,
        target_text,
        adapter=adapter,
        model=probe_config.model,
        retries=retries,
        rows=rows,
    )

    capped, overflow = cap_findings(raw_findings, probe_config.max_findings)

    verified: list[VerifiedFinding] = []
    for index, finding in enumerate(capped, start=1):
        verified.append(
            verify_finding(
                finding,
                target_text=target_text,
                adapter=adapter,
                model=probe_config.model,
                case_id=f"finding-{index}",
                rows=rows,
            )
        )

    confirmed = [entry for entry in verified if entry.verdict == "confirmed"]
    refuted_count = sum(1 for entry in verified if entry.verdict == "refuted")

    run_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        tune.append_jsonl(run_dir / "trials.jsonl", row)

    probe_calls = sum(1 for row in rows if row["condition"] == "probe")
    verify_calls = sum(1 for row in rows if row["condition"] == "verify")

    json_path, md_path = write_probe_report(
        run_dir,
        rows,
        confirmed=confirmed,
        refuted_count=refuted_count,
        overflow=overflow,
        probe_calls=probe_calls,
        verify_calls=verify_calls,
        doctrine_path=probe_config.doctrine_path,
        target_path=probe_config.target_path,
    )

    return {
        "run_dir": str(run_dir),
        "findings_confirmed": len(confirmed),
        "refuted_count": refuted_count,
        "overflow": overflow,
        "probe_calls": probe_calls,
        "verify_calls": verify_calls,
        "confirmed_findings": [
            {**entry.finding.to_dict(), "reason": entry.reason} for entry in confirmed
        ],
        "doctrine_file": str(probe_config.doctrine_path),
        "target_file": str(probe_config.target_path),
        "report_json": str(json_path),
        "report_md": str(md_path),
    }
