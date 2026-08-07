#!/usr/bin/env python3
"""skill-tuner routing-parity eval (R10, KTD6).

Measures whether a pruned/reworded skill description still routes as well
as the original, on a blind battery built from skill BODIES only -- never
from description text (KTD2: in-prompt presentation, nothing installed
anywhere). Python 3 standard library only.

Pipeline, in order:

1. ``load_config`` parses the eval config: target skills (with pruned
   descriptions), >=5 distractor skills, trials per condition, model pin.
2. ``build_battery`` builds the blind battery: per target skill, 2
   'obvious' + 1 'paraphrase' prompt derived from body capabilities (via
   ONE adapter call per target, or loaded from a pre-built battery file),
   plus a shared pool of near-miss / none-of-the-above prompts. Every
   prompt -- however it was produced -- passes through the structural
   blinding guard (``assert_no_blinding_violation``) before use.
3. ``build_router_trial_specs`` builds one router prompt per (battery
   case, condition, trial), presenting the full description set (targets
   in that condition's wording + distractors read from their real files)
   with deterministically-rotated presentation order (rotation offset =
   trial index).
4. The router battery runs through ``tune.execute_battery`` -- the same
   guarded adapter, budget gate, resume, and persistence machinery every
   skill-tuner eval shares. Every model call, real or fake, goes through
   the injected ``adapter`` (prompt, model) -> AdapterResult.
5. ``check_pairing`` requires identical (case_id, trial) coverage across
   both conditions before any scoring happens.
6. ``score_condition`` scores each condition; ``determine_verdict`` is the
   parity gate (AE1/AE2): 'land' only if pruned accuracy is >= original
   overall AND on near-miss rejection specifically, else 'refuse' naming
   the failing case ids.
7. ``write_routing_parity_report`` extends tune.py's report machinery
   (``tune.write_report``) with the verdict and both conditions' scores.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import tune

AdapterFn = Callable[[str, str], tune.AdapterResult]

CONDITIONS: tuple[str, str] = ("original", "pruned")


# --------------------------------------------------------------------------
# Structural blinding (KTD6): frontmatter-strip + substring guard
# --------------------------------------------------------------------------


class BlindingViolation(Exception):
    """Raised when a target skill's description text (original or pruned)
    reaches, or appears verbatim in, a generated battery prompt."""


_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n.*?\n---[ \t]*\n?", re.DOTALL)


def extract_body(skill_md_path: Path) -> str:
    """Strip YAML frontmatter entirely, so no description text can reach
    the battery builder. This is a structural parse of the file layout
    (the block between the first two '---' delimiter lines), not a
    text-based heuristic -- the frontmatter is removed outright."""
    text = skill_md_path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if match:
        return text[match.end():]
    return text


def extract_description(skill_md_path: Path) -> str:
    """Read the ``description:`` field out of a SKILL.md's YAML frontmatter."""
    text = skill_md_path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{skill_md_path}: no YAML frontmatter found")
    for line in match.group(0).splitlines():
        stripped = line.strip()
        if stripped.startswith("description:"):
            value = stripped[len("description:"):].strip()
            if value and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value
    raise ValueError(f"{skill_md_path}: no description field in frontmatter")


def assert_no_blinding_violation(prompt: str, forbidden: Sequence[str], *, case_id: str) -> None:
    for text in forbidden:
        if text and text in prompt:
            raise BlindingViolation(
                f"case {case_id!r}: battery prompt contains target description text: {text!r}"
            )


def _forbidden_strings(targets: Sequence["TargetSkill"]) -> list[str]:
    forbidden: list[str] = []
    for target in targets:
        if target.original_description:
            forbidden.append(target.original_description)
        if target.pruned_description:
            forbidden.append(target.pruned_description)
    return forbidden


# --------------------------------------------------------------------------
# Config loading
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TargetSkill:
    id: str
    path: Path
    original_description: str
    pruned_description: str


@dataclass(frozen=True)
class DistractorSkill:
    id: str
    path: Path
    description: str


def _skill_id_from_path(path: Path) -> str:
    return path.parent.name


def _resolve_path(raw: str, base_dir: Path) -> Path:
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else base_dir / candidate


def _resolve_pruned_description(entry: Mapping[str, Any], base_dir: Path) -> str:
    if "pruned_description" in entry and entry["pruned_description"] is not None:
        return str(entry["pruned_description"]).strip()
    if "pruned_description_file" in entry and entry["pruned_description_file"]:
        path = _resolve_path(entry["pruned_description_file"], base_dir)
        return path.read_text(encoding="utf-8").strip()
    raise ValueError(
        f"target {entry.get('id', entry.get('path'))!r} needs "
        "pruned_description or pruned_description_file"
    )


def load_config(
    config: Mapping[str, Any], *, base_dir: Path
) -> tuple[list[TargetSkill], list[DistractorSkill], int, str]:
    """Parse the eval config into (targets, distractors, trials_n, model)."""
    raw_targets = config.get("targets") or []
    if not raw_targets:
        raise ValueError("config must name at least one target skill")

    targets: list[TargetSkill] = []
    for entry in raw_targets:
        path = _resolve_path(entry["path"], base_dir)
        skill_id = entry.get("id") or _skill_id_from_path(path)
        targets.append(
            TargetSkill(
                id=skill_id,
                path=path,
                original_description=extract_description(path),
                pruned_description=_resolve_pruned_description(entry, base_dir),
            )
        )

    raw_distractors = config.get("distractors") or []
    if len(raw_distractors) < 5:
        raise ValueError(f"config must name at least 5 distractor skills, got {len(raw_distractors)}")

    distractors: list[DistractorSkill] = []
    for raw_entry in raw_distractors:
        entry = {"path": raw_entry} if isinstance(raw_entry, str) else raw_entry
        path = _resolve_path(entry["path"], base_dir)
        skill_id = entry.get("id") or _skill_id_from_path(path)
        distractors.append(DistractorSkill(id=skill_id, path=path, description=extract_description(path)))

    trials_n = int(config.get("trials", 2))
    if trials_n < 2:
        raise ValueError(f"trials per condition must be at least 2, got {trials_n}")

    model = config.get("model")
    if not model:
        raise ValueError("config must name a model pin")

    return targets, distractors, trials_n, str(model)


# --------------------------------------------------------------------------
# Blind battery builder (KTD6)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BatteryCase:
    case_id: str
    kind: str  # "obvious" | "paraphrase" | "near_miss" | "none_of_the_above"
    prompt: str
    target_id: str | None  # None for the shared near-miss / none-of-the-above pool


DEFAULT_SHARED_POOL: tuple[dict[str, str], ...] = (
    {
        "kind": "near_miss",
        "prompt": "Can you just read through this file and tell me what it does? No edits needed.",
    },
    {
        "kind": "near_miss",
        "prompt": "I need a quick status update on this project, nothing needs building or fixing right now.",
    },
    {"kind": "none_of_the_above", "prompt": "What's a good recipe for banana bread?"},
    {"kind": "none_of_the_above", "prompt": "Translate 'good morning' into French."},
)


def _build_authoring_prompt(body: str) -> str:
    return (
        "Below is the body of a skill document (its capabilities and "
        "instructions), with any name/description metadata already removed.\n\n"
        f"{body}\n\n"
        "Write test prompts a user might type that this skill's capabilities "
        "should handle. Return ONLY a JSON array of exactly 3 objects: two "
        'with "kind": "obvious" (a direct, clear request for this capability) '
        'and one with "kind": "paraphrase" (the same need worded very '
        'differently). Each object has keys "kind" and "prompt". No other text.'
    )


def _parse_authoring_response(text: str, target_id: str) -> list[dict[str, str]]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{target_id}: battery-authoring response was not valid JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise ValueError(f"{target_id}: battery-authoring response must be a JSON array")

    obvious = [item for item in payload if isinstance(item, dict) and item.get("kind") == "obvious"]
    paraphrase = [item for item in payload if isinstance(item, dict) and item.get("kind") == "paraphrase"]
    if len(obvious) != 2 or len(paraphrase) != 1:
        raise ValueError(
            f"{target_id}: expected 2 obvious + 1 paraphrase prompts, "
            f"got {len(obvious)} obvious + {len(paraphrase)} paraphrase"
        )
    return obvious + paraphrase


def _battery_cases_from_file(path: Path) -> list[BatteryCase]:
    raw_cases = json.loads(path.read_text(encoding="utf-8"))
    return [
        BatteryCase(
            case_id=entry["case_id"],
            kind=entry["kind"],
            prompt=entry["prompt"],
            target_id=entry.get("target_id"),
        )
        for entry in raw_cases
    ]


def build_battery(
    targets: Sequence[TargetSkill],
    config: Mapping[str, Any],
    *,
    adapter: AdapterFn,
    model: str,
    base_dir: Path,
) -> list[BatteryCase]:
    """Build the blind battery from skill bodies only. Every case -- whether
    adapter-authored or loaded from a pre-built battery file -- is checked
    against the blinding guard before being added."""
    forbidden = _forbidden_strings(targets)
    battery: list[BatteryCase] = []

    battery_file = config.get("battery_file")
    if battery_file:
        for case in _battery_cases_from_file(_resolve_path(battery_file, base_dir)):
            assert_no_blinding_violation(case.prompt, forbidden, case_id=case.case_id)
            battery.append(case)
        return battery

    for target in targets:
        body = extract_body(target.path)
        result = adapter(_build_authoring_prompt(body), model)
        authored = _parse_authoring_response(result.text, target.id)

        counts: dict[str, int] = {}
        for item in authored:
            kind = item["kind"]
            counts[kind] = counts.get(kind, 0) + 1
            case = BatteryCase(
                case_id=f"{target.id}__{kind}__{counts[kind]}",
                kind=kind,
                prompt=item["prompt"],
                target_id=target.id,
            )
            assert_no_blinding_violation(case.prompt, forbidden, case_id=case.case_id)
            battery.append(case)

    shared_pool = config.get("shared_pool") or DEFAULT_SHARED_POOL
    counts = {}
    for item in shared_pool:
        kind = item["kind"]
        counts[kind] = counts.get(kind, 0) + 1
        case = BatteryCase(
            case_id=item.get("case_id") or f"shared__{kind}__{counts[kind]}",
            kind=kind,
            prompt=item["prompt"],
            target_id=None,
        )
        assert_no_blinding_violation(case.prompt, forbidden, case_id=case.case_id)
        battery.append(case)

    return battery


# --------------------------------------------------------------------------
# Router condition: prompt construction + deterministic rotation
# --------------------------------------------------------------------------


def build_description_entries(
    condition: str, targets: Sequence[TargetSkill], distractors: Sequence[DistractorSkill]
) -> list[tuple[str, str]]:
    """The full description set for one condition: targets in that
    condition's wording, followed by distractors read from their real
    files (same in both conditions)."""
    entries: list[tuple[str, str]] = []
    for target in targets:
        description = target.original_description if condition == "original" else target.pruned_description
        entries.append((target.id, description))
    for distractor in distractors:
        entries.append((distractor.id, distractor.description))
    return entries


def rotate(entries: Sequence[tuple[str, str]], offset: int) -> list[tuple[str, str]]:
    if not entries:
        return []
    offset %= len(entries)
    return list(entries[offset:]) + list(entries[:offset])


def build_router_prompt(case: BatteryCase, description_entries: Sequence[tuple[str, str]]) -> str:
    listing = "\n".join(f"- {skill_id}: {description}" for skill_id, description in description_entries)
    return (
        "You are choosing which ONE skill, if any, should handle the request "
        "below.\n\nSkills available (id: description):\n"
        f"{listing}\n\n"
        f"Request:\n{case.prompt}\n\n"
        "Answer with exactly the skill id that should fire, or the word "
        "'none' if no skill applies. Respond with only that single token."
    )


def build_router_trial_specs(
    battery: Sequence[BatteryCase],
    targets: Sequence[TargetSkill],
    distractors: Sequence[DistractorSkill],
    trials_n: int,
) -> list[tune.TrialSpec]:
    """One router adapter call per (battery case, condition, trial).
    Presentation order rotates deterministically between trials: rotation
    offset equals the (zero-based) trial index."""
    specs: list[tune.TrialSpec] = []
    for trial in range(1, trials_n + 1):
        offset = trial - 1
        for condition in CONDITIONS:
            entries = rotate(build_description_entries(condition, targets, distractors), offset)
            for case in battery:
                specs.append(
                    tune.TrialSpec(
                        case_id=case.case_id,
                        trial=trial,
                        condition=condition,
                        prompt=build_router_prompt(case, entries),
                    )
                )
    return specs


# --------------------------------------------------------------------------
# Pairing check
# --------------------------------------------------------------------------


class PairingMismatch(ValueError):
    """Raised when the two conditions' router trials do not cover the same
    (case_id, trial) set."""


def check_pairing(rows: Sequence[Mapping[str, Any]], conditions: tuple[str, str]) -> None:
    first, second = conditions
    coverage = {
        condition: {(row["case_id"], row["trial"]) for row in rows if row.get("condition") == condition}
        for condition in conditions
    }
    if coverage[first] != coverage[second]:
        missing_in_first = sorted(coverage[second] - coverage[first])
        missing_in_second = sorted(coverage[first] - coverage[second])
        raise PairingMismatch(
            f"condition coverage mismatch between {first!r} and {second!r}: "
            f"missing in {first}: {missing_in_first}; missing in {second}: {missing_in_second}"
        )


# --------------------------------------------------------------------------
# Scoring + parity gate (AE1/AE2)
# --------------------------------------------------------------------------


def parse_router_answer(response_text: str, skill_ids: Iterable[str]) -> str:
    """Normalize a router response to a known skill id, or 'none'."""
    if not response_text or not response_text.strip():
        return "none"
    first_line = response_text.strip().splitlines()[0].strip()
    normalized = first_line.strip(" .,:;\"'").lower()
    lookup = {skill_id.lower(): skill_id for skill_id in skill_ids}
    return lookup.get(normalized, "none")


@dataclass(frozen=True)
class ScoreResult:
    condition: str
    total: int
    correct: int
    accuracy: float
    near_miss_total: int
    near_miss_correct: int
    near_miss_accuracy: float
    failing_case_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition": self.condition,
            "total": self.total,
            "correct": self.correct,
            "accuracy": self.accuracy,
            "near_miss_total": self.near_miss_total,
            "near_miss_correct": self.near_miss_correct,
            "near_miss_accuracy": self.near_miss_accuracy,
            "failing_case_ids": self.failing_case_ids,
        }


_REJECT_KINDS = {"near_miss", "none_of_the_above"}


def score_condition(
    rows: Sequence[Mapping[str, Any]],
    battery_by_id: Mapping[str, BatteryCase],
    all_skill_ids: Sequence[str],
    target_ids: Sequence[str],
) -> ScoreResult:
    condition = rows[0]["condition"] if rows else ""
    target_id_set = set(target_ids)
    total = correct = near_miss_total = near_miss_correct = 0
    failing: set[str] = set()

    for row in rows:
        case = battery_by_id[row["case_id"]]
        answer = parse_router_answer(row.get("response", ""), all_skill_ids)
        is_reject_case = case.kind in _REJECT_KINDS
        is_correct = (answer not in target_id_set) if is_reject_case else (answer == case.target_id)

        total += 1
        if is_correct:
            correct += 1
        else:
            failing.add(case.case_id)

        if is_reject_case:
            near_miss_total += 1
            if is_correct:
                near_miss_correct += 1

    return ScoreResult(
        condition=condition,
        total=total,
        correct=correct,
        accuracy=(correct / total) if total else 0.0,
        near_miss_total=near_miss_total,
        near_miss_correct=near_miss_correct,
        near_miss_accuracy=(near_miss_correct / near_miss_total) if near_miss_total else 1.0,
        failing_case_ids=sorted(failing),
    )


def determine_verdict(original: ScoreResult, pruned: ScoreResult) -> dict[str, Any]:
    """The parity gate (AE1/AE2): land only if pruned is >= original both
    overall and on near-miss rejection specifically."""
    overall_ok = pruned.accuracy >= original.accuracy
    near_miss_ok = pruned.near_miss_accuracy >= original.near_miss_accuracy
    if overall_ok and near_miss_ok:
        return {"verdict": "land", "failing_case_ids": []}
    return {"verdict": "refuse", "failing_case_ids": sorted(pruned.failing_case_ids)}


# --------------------------------------------------------------------------
# Report (extends tune.py's report machinery)
# --------------------------------------------------------------------------


def write_routing_parity_report(
    run_dir: Path,
    rows: Sequence[dict[str, Any]],
    conditions: tuple[str, str],
    scores: Mapping[str, ScoreResult],
    verdict_payload: Mapping[str, Any],
) -> tuple[Path, Path]:
    json_path, md_path = tune.write_report(run_dir, rows, conditions)

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    summary["routing_parity"] = {
        "verdict": verdict_payload["verdict"],
        "failing_case_ids": verdict_payload["failing_case_ids"],
        "scores": {condition: score.to_dict() for condition, score in scores.items()},
    }
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = ["", "## Routing-parity verdict", "", f"**Verdict: {verdict_payload['verdict']}**", ""]
    for condition in conditions:
        score = scores[condition]
        lines.append(
            f"- {condition}: accuracy {score.correct}/{score.total} ({score.accuracy:.1%}), "
            f"near-miss rejection {score.near_miss_correct}/{score.near_miss_total} "
            f"({score.near_miss_accuracy:.1%})"
        )
    if verdict_payload["failing_case_ids"]:
        lines.append("")
        lines.append("Failing case ids: " + ", ".join(verdict_payload["failing_case_ids"]))
    lines.append("")

    with md_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    return json_path, md_path


# --------------------------------------------------------------------------
# Orchestrator
# --------------------------------------------------------------------------


def run_routing_parity_eval(
    config: Mapping[str, Any],
    *,
    adapter: AdapterFn,
    run_dir: Path,
    base_dir: Path | None = None,
    budget_usd: float | None = None,
    allow_unmetered: bool = True,
    auth_mode: str = "subscription",
    yes: bool = True,
) -> dict[str, Any]:
    """Run the full routing-parity pipeline: build battery, run the router
    condition through tune.py's guarded battery executor, pair-check,
    score, gate, and report. Every model call goes through ``adapter``."""
    resolved_base_dir = base_dir if base_dir is not None else Path(".")
    targets, distractors, trials_n, model = load_config(config, base_dir=resolved_base_dir)
    battery = build_battery(targets, config, adapter=adapter, model=model, base_dir=resolved_base_dir)
    specs = build_router_trial_specs(battery, targets, distractors, trials_n)

    execute_result = tune.execute_battery(
        specs,
        run_dir=run_dir,
        adapter=adapter,
        model=model,
        budget_usd=budget_usd,
        allow_unmetered=allow_unmetered,
        auth_mode=auth_mode,
        yes=yes,
    )

    rows = tune.read_jsonl(run_dir / "trials.jsonl")
    check_pairing(rows, CONDITIONS)

    battery_by_id = {case.case_id: case for case in battery}
    all_skill_ids = [target.id for target in targets] + [distractor.id for distractor in distractors]
    target_ids = [target.id for target in targets]

    scores = {
        condition: score_condition(
            [row for row in rows if row.get("condition") == condition], battery_by_id, all_skill_ids, target_ids
        )
        for condition in CONDITIONS
    }

    verdict_payload = determine_verdict(scores["original"], scores["pruned"])
    json_path, md_path = write_routing_parity_report(run_dir, rows, CONDITIONS, scores, verdict_payload)

    return {
        "run_dir": str(run_dir),
        "verdict": verdict_payload["verdict"],
        "failing_case_ids": verdict_payload["failing_case_ids"],
        "scores": {condition: score.to_dict() for condition, score in scores.items()},
        "report_json": str(json_path),
        "report_md": str(md_path),
        "execute_result": execute_result,
    }
