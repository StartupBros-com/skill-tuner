#!/usr/bin/env python3
"""skill-tuner marginal-value probe (R11, KTD2).

Applies the skill-tuner doctrine (or any doctrine document) to a target
document and adversarially verifies every finding it raises, so the report
only ever surfaces defects that survived a fresh, skeptical, second look --
the check behind the doctrine's "the probe finds what audits miss" rule.
Python 3 standard library only.

Pipeline, in order:

1. ``load_config`` parses the eval config: ``doctrine_file`` (defaults to
   the bundled ``skills/skill-tuner/SKILL.md``), the targets -- ``target_file``
   for one document or ``target_files`` for several -- ``model``,
   ``max_findings`` (default 8), and ``verify_trials`` (default 1).
2. For each target, ``run_probe_call`` makes ONE adapter call with the
   doctrine text and the full target document inline (KTD2: nothing installed
   anywhere, no out-of-band state), asking for genuine defects as a JSON
   array; an empty array is an explicitly legitimate answer. Malformed JSON
   retries through the same adapter path -- no subprocess, no shared state,
   just another call -- up to ``retries`` bounded attempts.
3. ``cap_findings`` truncates the parsed findings to ``max_findings``,
   recording the overflow count rather than silently dropping it.
4. ``verify_finding`` judges each capped finding with ``verify_trials``
   independent skeptics -- each a fresh self-contained prompt carrying that
   finding alone plus the full target document, never another finding's
   text, never a shared conversation -- under a default-refute instruction:
   confirm only if the quoted text is verbatim in the target and the cited
   rule genuinely applies. A finding is confirmed on a strict majority; a
   tie refutes. ``quote_present`` is the code-level backstop that outranks
   every vote: a CONFIRMED verdict for a quote absent from the target is
   downgraded to refuted no matter how the panel voted. That check compares
   prose, not layout -- markdown repeats blockquote and list markers on
   every wrapped line and a correct quote drops them, so a raw substring
   test rejects real findings on exactly the documents this probe targets.
   Every call's row lands in ``trials.jsonl`` as it completes, not after the
   run, so an interrupted battery keeps the spend it already made.
5. ``write_probe_report`` extends tune.py's report machinery
   (``tune.write_report``) with the probe verdict: confirmed findings with
   their evidence quotes, refuted findings with the mode that killed each
   (``verifier`` or ``quote_not_found``), the overflow count, probe/verify
   call counts, a per-target breakdown, and the target/doctrine identifiers.
   Verdict field: ``findings_confirmed: N``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import provenance
import tune

AdapterFn = Callable[[str, str], tune.AdapterResult]

# The bundled doctrine this probe defaults to when a config doesn't name its
# own: skills/skill-tuner/SKILL.md, resolved from this file's own location
# so the default never depends on the run's base_dir or cwd.
_MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_DOCTRINE_PATH = _MODULE_DIR.parent / "SKILL.md"

DEFAULT_MAX_FINDINGS = 8
DEFAULT_RETRIES = 2
DEFAULT_VERIFY_TRIALS = 1


class ProbeParseError(ValueError):
    """Raised when the probe response never yields a valid JSON array after
    exhausting the bounded retry budget."""


class _BudgetExhausted(Exception):
    """Signal: the run has spent its cap. Raised by the budget wrapper
    before a call is made; run_probe and the sequential gate catch it, stop
    cleanly, and report the partial result as halted. Public alias:
    ``BudgetExhausted``."""


BudgetExhausted = _BudgetExhausted


# Public seam for callers outside this module (the sequential gate): the
# budget wrapper and its stop signal are part of the probe's contract now,
# not internals.
def budget_guarded(adapter, budget_usd, state):
    return _budget_guarded(adapter, budget_usd, state)


def _record(
    rows: list[dict[str, Any]], row: dict[str, Any], trials_path: Path | None
) -> None:
    """Append a trial row to the in-memory list and, when a path is given,
    to the durable log in the same breath. Persisting at the call site rather
    than after the run is what makes an interrupted run resumable instead of
    a total loss -- a six-target battery has a lot of spend to lose."""
    rows.append(row)
    if trials_path is not None:
        tune.append_jsonl(trials_path, row)


def _budget_guarded(
    adapter: AdapterFn, budget_usd: float | None, state: dict[str, float]
) -> AdapterFn:
    """Wrap ``adapter`` so the run stops before exceeding ``budget_usd``.

    tune.execute_battery owns this for fixed-size batteries, but the probe's
    call count is discovered mid-run (findings are only known after the probe
    call), so it runs outside that battery and needs its own cap. The check
    is before the call, so the cap is never breached by the call that trips
    it."""

    def wrapped(prompt: str, model: str) -> tune.AdapterResult:
        if budget_usd is not None and state["spent"] >= budget_usd:
            raise _BudgetExhausted()
        result = adapter(prompt, model)
        state["spent"] += result.cost_usd or 0.0
        return result

    return wrapped


# --------------------------------------------------------------------------
# Config loading
# --------------------------------------------------------------------------


def _resolve_path(raw: str, base_dir: Path) -> Path:
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else base_dir / candidate


@dataclass(frozen=True)
class ProbeConfig:
    doctrine_path: Path
    target_paths: tuple[Path, ...]
    model: str
    max_findings: int
    verify_trials: int = DEFAULT_VERIFY_TRIALS
    # git ref every input is read from, e.g. "origin/main". None reads the
    # working tree, which is convenient while iterating and wrong for a
    # published receipt.
    pin: str | None = None

    @property
    def target_path(self) -> Path:
        """The first target. Single-target configs are the common case and
        every pre-multi-target caller reads this name."""
        return self.target_paths[0]


def load_config(config: Mapping[str, Any], *, base_dir: Path) -> ProbeConfig:
    """Parse the eval config into a ``ProbeConfig``. ``doctrine_file``
    defaults to the bundled SKILL.md (resolved independent of base_dir).

    Targets come from ``target_file`` (one document) or ``target_files`` (a
    list); both may be given and are concatenated in order, de-duplicated.
    At least one is required, and each resolves relative to base_dir like
    every other skill-tuner eval config path. ``verify_trials`` sets how many
    independent skeptics judge each finding (default 1); a count-based gate
    wants an odd panel so one stray verdict cannot decide it."""
    doctrine_file = config.get("doctrine_file")
    doctrine_path = _resolve_path(doctrine_file, base_dir) if doctrine_file else DEFAULT_DOCTRINE_PATH

    raw_targets: list[str] = []
    single = config.get("target_file")
    if single:
        raw_targets.append(str(single))
    listed = config.get("target_files") or []
    if isinstance(listed, (str, bytes)):
        raise ValueError("target_files must be a list of paths, not a string")
    raw_targets.extend(str(item) for item in listed if item)
    if not raw_targets:
        raise ValueError("config must name a target_file or a non-empty target_files list")

    target_paths: list[Path] = []
    for raw in raw_targets:
        resolved = _resolve_path(raw, base_dir)
        if resolved not in target_paths:
            target_paths.append(resolved)

    model = config.get("model")
    if not model:
        raise ValueError("config must name a model pin")

    max_findings = int(config.get("max_findings", DEFAULT_MAX_FINDINGS))
    if max_findings < 1:
        raise ValueError(f"max_findings must be >= 1, got {max_findings}")

    verify_trials = int(config.get("verify_trials", DEFAULT_VERIFY_TRIALS))
    if verify_trials < 1:
        raise ValueError(f"verify_trials must be >= 1, got {verify_trials}")

    pin = config.get("pin")

    return ProbeConfig(
        doctrine_path=doctrine_path,
        target_paths=tuple(target_paths),
        model=str(model),
        max_findings=max_findings,
        verify_trials=verify_trials,
        pin=str(pin) if pin else None,
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
# Quote existence: the code-level backstop against fabricated evidence
# --------------------------------------------------------------------------

# Per-line markdown decoration: blockquote markers and list bullets. These
# carry no prose, so a quote that spans a line break legitimately drops them.
_LINE_DECORATION_RE = re.compile(r"^\s*(?:>\s?)*(?:[-*+]\s+|\d+[.)]\s+)?")


def normalize_for_quote_match(text: str) -> str:
    """Reduce markdown to the prose a quote can be checked against: strip
    per-line blockquote and list decoration, then collapse all whitespace.

    A model quoting across a line break reproduces the words, not the ``> ``
    that markdown repeats on every wrapped line of a blockquote. Comparing
    raw strings therefore fails on correctly-quoted blockquotes, list items,
    and any hard-wrapped passage -- and since every document this probe
    targets is markdown, that false negative is systematic rather than rare.
    Normalizing both sides identically keeps the check a genuine substring
    test on the document's words while ignoring only its layout."""
    lines = [_LINE_DECORATION_RE.sub("", line) for line in text.splitlines()]
    return " ".join(" ".join(lines).split())


def quote_present(quote: str, target_text: str) -> bool:
    """True when ``quote`` appears in ``target_text`` as prose. Tries the
    strict raw substring first and falls back to the normalized comparison,
    so an exact quote is never rejected and a fabricated one is never
    accepted -- normalization drops layout, never words."""
    if not quote.strip():
        return False
    if quote in target_text:
        return True
    normalized_quote = normalize_for_quote_match(quote)
    if not normalized_quote:
        return False
    return normalized_quote in normalize_for_quote_match(target_text)


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
    case_id: str = "probe",
    trials_path: Path | None = None,
) -> list[dict[str, Any]]:
    """One adapter call carrying the doctrine + target document inline.
    Malformed JSON is retried through the same adapter path -- never
    subprocess -- up to ``retries`` additional bounded attempts. Every
    attempt is recorded in ``rows`` regardless of outcome."""
    prompt = build_probe_prompt(doctrine_text, target_text)
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        result = adapter(prompt, model)
        _record(
            rows,
            {
                "case_id": case_id,
                "trial": attempt + 1,
                "condition": "probe",
                "response": result.text,
                "cost_usd": result.cost_usd,
                "model_resolved": result.model_resolved,
            },
            trials_path,
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
    # Why a refuted finding was refuted: "verifier" (the skeptic panel voted
    # it down) or "quote_not_found" (the code-level guard downgraded it, so
    # the probe fabricated its evidence). None when confirmed. The two are
    # different failures -- a weak rule application versus a hallucinated
    # quote -- and a bare refuted count cannot tell them apart.
    refutation_mode: str | None = None
    target_file: str | None = None


def verify_finding(
    finding: Finding,
    *,
    target_text: str,
    adapter: AdapterFn,
    model: str,
    case_id: str,
    rows: list[dict[str, Any]],
    verify_trials: int = DEFAULT_VERIFY_TRIALS,
    trials_path: Path | None = None,
) -> VerifiedFinding:
    """Judge one finding with ``verify_trials`` independent skeptics, each a
    fresh self-contained adapter call carrying this finding alone. A finding
    is confirmed only on a strict majority of confirm votes; a tie refutes,
    matching the verifier prompt's own default-refute stance.

    The quote-existence check is a code-level guard that outranks every vote:
    the panel cannot confirm a quote that isn't in the target document, no
    matter how it votes."""
    prompt = build_verify_prompt(finding, target_text)
    votes: list[str] = []
    reasons: list[str] = []

    for trial in range(1, verify_trials + 1):
        result = adapter(prompt, model)
        _record(
            rows,
            {
                "case_id": case_id,
                "trial": trial,
                "condition": "verify",
                "response": result.text,
                "cost_usd": result.cost_usd,
                "model_resolved": result.model_resolved,
            },
            trials_path,
        )
        votes.append(parse_verify_answer(result.text))
        reasons.append(result.text.strip())

    confirmed_votes = sum(1 for vote in votes if vote == "confirmed")
    verdict = "confirmed" if confirmed_votes * 2 > len(votes) else "refuted"
    reason = reasons[0] if len(reasons) == 1 else (
        f"panel {confirmed_votes}/{len(votes)} confirmed | " + " || ".join(reasons)
    )

    if verdict == "confirmed" and not quote_present(finding.target_quote, target_text):
        return VerifiedFinding(
            finding=finding,
            verdict="refuted",
            reason="downgraded: quoted text not found verbatim in target document",
            refutation_mode="quote_not_found",
        )

    return VerifiedFinding(
        finding=finding,
        verdict=verdict,
        reason=reason,
        refutation_mode=None if verdict == "confirmed" else "verifier",
    )


# --------------------------------------------------------------------------
# Report (extends tune.py's report machinery)
# --------------------------------------------------------------------------


def _finding_entry(entry: VerifiedFinding) -> dict[str, Any]:
    payload: dict[str, Any] = {**entry.finding.to_dict(), "reason": entry.reason}
    if entry.target_file is not None:
        payload["target_file"] = entry.target_file
    if entry.refutation_mode is not None:
        payload["refutation_mode"] = entry.refutation_mode
    return payload


def write_probe_report(
    run_dir: Path,
    rows: Sequence[dict[str, Any]],
    *,
    confirmed: Sequence[VerifiedFinding],
    refuted: Sequence[VerifiedFinding] = (),
    refuted_count: int,
    overflow: int,
    probe_calls: int,
    verify_calls: int,
    doctrine_path: Path,
    target_path: Path,
    target_paths: Sequence[Path] | None = None,
    per_target: Sequence[Mapping[str, Any]] = (),
    verify_trials: int = DEFAULT_VERIFY_TRIALS,
    halted_on_budget: bool = False,
    manifest: Mapping[str, Any] | None = None,
) -> tuple[Path, Path]:
    json_path, md_path = tune.write_report(run_dir, rows, ("probe", "verify"), manifest)

    confirmed_findings = [_finding_entry(entry) for entry in confirmed]
    refuted_findings = [_finding_entry(entry) for entry in refuted]
    resolved_targets = list(target_paths) if target_paths else [target_path]

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    summary["probe"] = {
        "findings_confirmed": len(confirmed),
        "refuted_count": refuted_count,
        "overflow": overflow,
        "probe_calls": probe_calls,
        "verify_calls": verify_calls,
        "verify_trials": verify_trials,
        "doctrine_file": str(doctrine_path),
        "target_file": str(target_path),
        "target_files": [str(path) for path in resolved_targets],
        "confirmed_findings": confirmed_findings,
        "refuted_findings": refuted_findings,
        "per_target": [dict(entry) for entry in per_target],
        "halted_on_budget": halted_on_budget,
    }
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "",
        "## Marginal-value probe verdict",
        "",
        f"**findings_confirmed: {len(confirmed)}**",
        "",
        f"- doctrine: {doctrine_path}",
    ]
    if len(resolved_targets) == 1:
        lines.append(f"- target: {resolved_targets[0]}")
    else:
        lines.append(f"- targets: {len(resolved_targets)}")
    lines.extend(
        [
            f"- probe calls: {probe_calls}",
            f"- verify calls: {verify_calls} ({verify_trials} skeptic(s) per finding)",
            f"- refuted: {refuted_count}",
        ]
    )
    if overflow:
        lines.append(f"- overflow (beyond max_findings cap, not verified): {overflow}")
    if halted_on_budget:
        lines.append(
            "- **PARTIAL RUN: budget cap reached; not every target was probed. "
            "These counts are not a verdict on the full target set.**"
        )
    lines.append("")

    if len(resolved_targets) > 1 and per_target:
        lines.append("### Per target")
        lines.append("")
        lines.append("| Target | confirmed | refuted |")
        lines.append("| --- | --- | --- |")
        for entry in per_target:
            lines.append(
                f"| `{entry['target_file']}` | {entry['findings_confirmed']} | {entry['refuted_count']} |"
            )
        lines.append("")

    if confirmed_findings:
        lines.append("### Confirmed findings")
        lines.append("")
        for entry in confirmed_findings:
            lines.append(f"- **{entry['rule']}**: {entry['issue']}")
            lines.append(f"  - quote: \"{entry['target_quote']}\"")
            lines.append(f"  - proposed fix: {entry['proposed_fix']}")
            if entry.get("target_file"):
                lines.append(f"  - target: {entry['target_file']}")
        lines.append("")

    if refuted_findings:
        # Refuted findings are reported, not just counted: a run that raised
        # findings and lost them all to fabricated quotes is a different
        # result from one whose findings were judged inapplicable, and the
        # count alone reads identically for both.
        lines.append("### Refuted findings")
        lines.append("")
        for entry in refuted_findings:
            lines.append(
                f"- **{entry['rule']}** — {entry.get('refutation_mode', 'verifier')}: {entry['issue']}"
            )
            lines.append(f"  - quote: \"{entry['target_quote']}\"")
        lines.append("")

    with md_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    return json_path, md_path


# --------------------------------------------------------------------------
# Orchestrator
# --------------------------------------------------------------------------


def probe_one_target(
    target_text: str,
    doctrine_text: str,
    *,
    adapter: AdapterFn,
    probe_config: ProbeConfig,
    rows: list[dict[str, Any]],
    trials_path: Path | None,
    retries: int = DEFAULT_RETRIES,
    prefix: str = "",
) -> tuple[list[VerifiedFinding], int]:
    """Probe one target and verify every capped finding: the per-target unit
    both the fixed-n probe and the sequential gate run. Returns (verified
    findings, overflow). Budget exhaustion propagates as _BudgetExhausted for
    the caller's policy -- the fixed-n probe flags a partial run, the gate
    treats it as an undecided stop."""
    raw_findings = run_probe_call(
        doctrine_text,
        target_text,
        adapter=adapter,
        model=probe_config.model,
        retries=retries,
        rows=rows,
        case_id=f"{prefix}probe",
        trials_path=trials_path,
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
                case_id=f"{prefix}finding-{index}",
                rows=rows,
                verify_trials=probe_config.verify_trials,
                trials_path=trials_path,
            )
        )
    return verified, overflow


def run_probe(
    config: Mapping[str, Any],
    adapter: AdapterFn,
    run_dir: Path,
    base_dir: Path | None = None,
    *,
    retries: int = DEFAULT_RETRIES,
    budget_usd: float | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run the full marginal-value probe pipeline: one probe call (doctrine
    + target inline), cap findings, one fresh self-contained verify call per
    capped finding, then report. Every model call goes through ``adapter``."""
    resolved_base_dir = base_dir if base_dir is not None else Path(".")
    probe_config = load_config(config, base_dir=resolved_base_dir)
    pin = probe_config.pin
    started_at = provenance.utc_now()

    # Every input is read through the one chokepoint, before any spend: an
    # unresolvable pin should cost nothing, not fail halfway through a
    # battery.
    doctrine_input = provenance.resolve_input(
        probe_config.doctrine_path, role="doctrine", pin=pin
    )
    target_inputs = [
        provenance.resolve_input(path, role="target", pin=pin)
        for path in probe_config.target_paths
    ]

    doctrine_text = doctrine_input.text
    multi_target = len(probe_config.target_paths) > 1

    rows: list[dict[str, Any]] = []
    verified: list[VerifiedFinding] = []
    per_target: list[dict[str, Any]] = []
    overflow = 0
    halted_on_budget = False
    spend_state = {"spent": 0.0}
    guarded_adapter = _budget_guarded(adapter, budget_usd, spend_state)

    # Created up front so every trial row is durable the moment it completes.
    run_dir.mkdir(parents=True, exist_ok=True)
    trials_path = run_dir / "trials.jsonl"

    for target_index, target_input in enumerate(target_inputs, start=1):
        if halted_on_budget:
            break
        target_path = target_input.path
        target_text = target_input.text
        # Single-target runs keep the original flat case ids so their trial
        # logs stay byte-comparable with pre-multi-target runs.
        prefix = f"t{target_index}-" if multi_target else ""
        before = len(rows)
        target_overflow = 0
        target_verified: list[VerifiedFinding] = []
        target_halted = False

        try:
            probed, target_overflow = probe_one_target(
                target_text,
                doctrine_text,
                adapter=guarded_adapter,
                probe_config=probe_config,
                rows=rows,
                trials_path=trials_path,
                retries=retries,
                prefix=prefix,
            )
            for entry in probed:
                if multi_target:
                    entry = replace(entry, target_file=str(target_path))
                target_verified.append(entry)
        except _BudgetExhausted:
            # Stop cleanly: whatever completed stays durable and the report
            # is flagged partial, so a truncated run can never be read as a
            # verdict on the full target set.
            halted_on_budget = True
            target_halted = True

        overflow += target_overflow
        verified.extend(target_verified)
        target_rows = rows[before:]
        if target_rows:
            per_target.append(
                {
                    "target_file": str(target_path),
                    "findings_confirmed": sum(
                        1 for item in target_verified if item.verdict == "confirmed"
                    ),
                    "refuted_count": sum(
                        1 for item in target_verified if item.verdict == "refuted"
                    ),
                    "overflow": target_overflow,
                    "probe_calls": sum(1 for row in target_rows if row["condition"] == "probe"),
                    "verify_calls": sum(1 for row in target_rows if row["condition"] == "verify"),
                    "complete": not target_halted,
                }
            )

    confirmed = [entry for entry in verified if entry.verdict == "confirmed"]
    refuted = [entry for entry in verified if entry.verdict == "refuted"]
    refuted_count = len(refuted)

    probe_calls = sum(1 for row in rows if row["condition"] == "probe")
    verify_calls = sum(1 for row in rows if row["condition"] == "verify")

    manifest = provenance.build_manifest(
        run_id=run_id or run_dir.name,
        inputs=[doctrine_input, *target_inputs],
        model_pin=probe_config.model,
        resolved_models=sorted(
            {row["model_resolved"] for row in rows if row.get("model_resolved")}
        ),
        started_at=started_at,
        finished_at=provenance.utc_now(),
        cli_version=provenance.cli_version(),
        tool_version=provenance.tool_version(),
        extra={"eval": "probe", "pin": pin},
    )

    json_path, md_path = write_probe_report(
        run_dir,
        rows,
        manifest=manifest,
        confirmed=confirmed,
        refuted=refuted,
        refuted_count=refuted_count,
        overflow=overflow,
        probe_calls=probe_calls,
        verify_calls=verify_calls,
        doctrine_path=probe_config.doctrine_path,
        target_path=probe_config.target_path,
        target_paths=probe_config.target_paths,
        per_target=per_target,
        verify_trials=probe_config.verify_trials,
        halted_on_budget=halted_on_budget,
    )

    return {
        "run_dir": str(run_dir),
        # Which doctrine text actually ran, so two probe yields are never
        # informally compared across silently different doctrine versions
        # (the dogfood3 batch was, and the caveat cost a re-run's worth of
        # comparability).
        "doctrine_sha256": doctrine_input.sha256,
        "halted_on_budget": halted_on_budget,
        "spent_usd": round(spend_state["spent"], 6),
        "findings_confirmed": len(confirmed),
        "refuted_count": refuted_count,
        "overflow": overflow,
        "probe_calls": probe_calls,
        "verify_calls": verify_calls,
        "verify_trials": probe_config.verify_trials,
        "confirmed_findings": [_finding_entry(entry) for entry in confirmed],
        "refuted_findings": [_finding_entry(entry) for entry in refuted],
        "per_target": per_target,
        "doctrine_file": str(probe_config.doctrine_path),
        "target_file": str(probe_config.target_path),
        "target_files": [str(path) for path in probe_config.target_paths],
        "report_json": str(json_path),
        "report_md": str(md_path),
    }
