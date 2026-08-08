#!/usr/bin/env python3
"""skill-tuner eval runner core.

The CLI skeleton, the guarded adapter, and the report/resume machinery every
skill-tuner eval shares. Python 3 standard library only (KTD1) -- no
third-party imports anywhere.

Subcommands: routing-parity, probe, report. Resume is a flag (--resume
RUN_ID) on the two eval subcommands, not a subcommand of its own. There is no
doctor subcommand here -- doctor is a separate shell script in a later unit.

Every eval path funnels through exactly one function, call_adapter(), which
builds and runs the headless `claude` CLI call (KTD2/R8). Callers that need
to test the surrounding machinery (budget gate, resume, retries, reporting)
inject a FAKE adapter with the same (prompt, model) -> AdapterResult
signature instead of touching call_adapter or subprocess at all.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
# Conservative placeholder; overridable per-run with --est-cost-per-call.
DEFAULT_EST_COST_PER_CALL = 0.05
DEFAULT_RETRIES = 2
DEFAULT_REPORTS_DIR = Path("reports")


# --------------------------------------------------------------------------
# Data shapes
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TrialSpec:
    """One (case, trial, condition) unit of work with its fully-built prompt."""

    case_id: str
    trial: int
    condition: str
    prompt: str


@dataclass(frozen=True)
class AdapterResult:
    """What every adapter call (real or fake) must hand back."""

    text: str
    cost_usd: float
    raw: dict[str, Any]
    # The model that actually answered, read back from the CLI envelope.
    # A pin like "claude-sonnet-5" is an alias; if it is ever repointed
    # upstream, a published receipt changes meaning without a byte of the
    # report changing. Recording what replied is the only way to notice.
    model_resolved: str | None = None


def extract_resolved_model(payload: Mapping[str, Any]) -> str | None:
    """Pull the canonical model id out of a `claude -p --output-format json`
    envelope. The envelope reports usage per model as
    ``modelUsage: {"<id>": {"canonicalModel": ..., ...}}``; when more than one
    answered, the busiest by output tokens is the one that produced the
    result."""
    usage = payload.get("modelUsage")
    if not isinstance(usage, Mapping) or not usage:
        return None

    def output_tokens(entry: Any) -> int:
        return int(entry.get("outputTokens", 0)) if isinstance(entry, Mapping) else 0

    best_key = max(usage, key=lambda key: output_tokens(usage[key]))
    entry = usage[best_key]
    if isinstance(entry, Mapping):
        canonical = entry.get("canonicalModel")
        if isinstance(canonical, str) and canonical:
            return canonical
    return str(best_key)


# --------------------------------------------------------------------------
# Auth mode (R8/AE3) -- detected from the environment, never from a live call
# --------------------------------------------------------------------------


def detect_auth_mode(env: Mapping[str, str] | None = None) -> str:
    """Classify the run's billing mode without making any subprocess call.

    "api-key" means the adapter will report real dollar cost (total_cost_usd
    is meaningful); "subscription" means total_cost_usd will always be 0.
    This must stay a pure function of the environment so the budget gate can
    refuse a run before the first subprocess call ever happens.
    """
    active_env = os.environ if env is None else env
    if active_env.get("ANTHROPIC_API_KEY"):
        return "api-key"
    return "subscription"


# --------------------------------------------------------------------------
# The single adapter chokepoint (KTD2/R8)
# --------------------------------------------------------------------------


def build_adapter_command(prompt: str, model: str) -> list[str]:
    return [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--setting-sources",
        "",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--tools",
        "",
        "--model",
        model,
    ]


def call_adapter(
    prompt: str,
    model: str,
    *,
    retries: int = DEFAULT_RETRIES,
    backoff: Callable[[float], None] = time.sleep,
    run: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> AdapterResult:
    """The one function that owns building + running the headless claude CLI
    call. Every eval path goes through this. Bounded retries with exponential
    backoff cover both subprocess failure (nonzero exit) and malformed JSON
    output.
    """
    command = build_adapter_command(prompt, model)
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            completed = run(command, capture_output=True, text=True, check=False)
        except OSError as exc:
            last_error = exc
        else:
            if completed.returncode == 0:
                try:
                    payload = json.loads(completed.stdout)
                except json.JSONDecodeError as exc:
                    last_error = exc
                else:
                    return AdapterResult(
                        text=str(payload.get("result", "")).strip(),
                        cost_usd=float(payload.get("total_cost_usd") or 0.0),
                        raw=payload,
                        model_resolved=extract_resolved_model(payload),
                    )
            else:
                stderr = (completed.stderr or "").strip()
                last_error = RuntimeError(f"adapter exited {completed.returncode}: {stderr}")

        if attempt < retries:
            backoff(2**attempt)

    raise RuntimeError(
        f"adapter failed after {retries + 1} attempt(s): {last_error}"
    ) from last_error


# --------------------------------------------------------------------------
# JSONL persistence
# --------------------------------------------------------------------------


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: line {number}: {exc.msg}") from exc
        rows.append(row)
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as destination:
        destination.write(json.dumps(row, ensure_ascii=False) + "\n")
        destination.flush()


def completed_keys(rows: Iterable[dict[str, Any]]) -> set[tuple[str, int, str]]:
    keys: set[tuple[str, int, str]] = set()
    for row in rows:
        case_id, trial, condition = row.get("case_id"), row.get("trial"), row.get("condition")
        if isinstance(case_id, str) and isinstance(trial, int) and isinstance(condition, str):
            keys.add((case_id, trial, condition))
    return keys


# --------------------------------------------------------------------------
# Durable run-id / run-dir resolution (R15/KTD3)
# --------------------------------------------------------------------------


def derive_run_id(prefix: str, content_parts: Iterable[str]) -> str:
    digest = hashlib.sha256("\x1f".join(content_parts).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}-{digest}"


def resolve_run_dir(
    reports_dir: Path,
    prefix: str,
    content_parts: Iterable[str],
    *,
    run_id: str | None,
    resume_id: str | None,
) -> tuple[Path, str]:
    """Resolve the run directory for a fresh or resumed run.

    --resume RUN_ID always reuses that exact directory. An explicit --run-id
    always wins too. Absent both, the run-id is a content-derived slug (never
    wall-clock randomness); if that slug's directory already exists from a
    prior *fresh* run, a numeric suffix is appended until a free directory is
    found, so a plain rerun never silently merges into an old run.
    """
    if resume_id:
        chosen = resume_id
    elif run_id:
        chosen = run_id
    else:
        base = derive_run_id(prefix, content_parts)
        chosen = base
        suffix = 1
        while (reports_dir / chosen).exists():
            suffix += 1
            chosen = f"{base}-{suffix}"

    run_dir = reports_dir / chosen
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir, chosen


# --------------------------------------------------------------------------
# Budget gate (R8/AE3)
# --------------------------------------------------------------------------


def enforce_budget_preflight(auth_mode: str, budget_usd: float | None, allow_unmetered: bool) -> None:
    """Refuse before any subprocess call when the run would report real
    dollar cost but has no budget cap. Subscription runs (total_cost_usd
    always 0) are exempt -- they're bounded by trial count, not dollars.
    """
    if auth_mode == "api-key" and budget_usd is None and not allow_unmetered:
        raise RuntimeError(
            "API-key auth reports dollar cost; refusing to run without --budget-usd. "
            "Pass --budget-usd, or override with --allow-unmetered."
        )


def confirm_or_abort(
    description: str,
    *,
    yes: bool,
    isatty: bool,
    print_fn: Callable[[str], None] = print,
    input_fn: Callable[[str], str] = input,
) -> None:
    """Shared pre-flight confirm-or-abort gate, same shape as
    ``execute_battery``'s own (print estimate, skip if --yes, prompt if a
    tty, else require --yes) -- for eval paths whose call count isn't fixed
    upfront and so don't run their trials through ``execute_battery``
    (currently: probe, whose verify-call count depends on findings
    discovered mid-run).
    """
    print_fn(description)
    if yes:
        return
    if isatty:
        response = input_fn("Proceed? [y/N] ")
        if response.strip().lower() not in {"y", "yes"}:
            raise RuntimeError("Pre-flight not confirmed; aborting before any adapter call.")
    else:
        raise RuntimeError(
            "Pre-flight confirmation required for a non-interactive run; pass --yes."
        )


# --------------------------------------------------------------------------
# Battery execution: pre-flight estimate, budget cap, resume, persistence
# --------------------------------------------------------------------------


def execute_battery(
    trials: Sequence[TrialSpec],
    *,
    run_dir: Path,
    adapter: Callable[[str, str], AdapterResult],
    model: str,
    budget_usd: float | None,
    allow_unmetered: bool,
    auth_mode: str,
    est_cost_per_call: float = DEFAULT_EST_COST_PER_CALL,
    yes: bool = False,
    isatty: bool = False,
    print_fn: Callable[[str], None] = print,
    input_fn: Callable[[str], str] = input,
) -> dict[str, Any]:
    """Run a battery of trials through `adapter`, honoring the budget gate,
    the pre-flight estimate/confirmation, and resume-by-completed-key. Every
    completed trial is appended to <run_dir>/trials.jsonl as it finishes, so
    a crash or a budget halt always leaves completed work durable.
    """
    # REFUSE before any subprocess call (AE3) -- this must be the first thing
    # that happens, ahead of even reading the resume state.
    enforce_budget_preflight(auth_mode, budget_usd, allow_unmetered)

    trials_path = run_dir / "trials.jsonl"
    existing_rows = read_jsonl(trials_path)
    done = completed_keys(existing_rows)
    pending = [spec for spec in trials if (spec.case_id, spec.trial, spec.condition) not in done]

    estimated_total = len(pending) * est_cost_per_call
    print_fn(
        f"Planned trials: {len(pending)} | estimated cost: ${estimated_total:.2f} "
        f"(${est_cost_per_call:.4f}/call, model={model})"
    )

    if pending and not yes:
        if isatty:
            response = input_fn("Proceed? [y/N] ")
            if response.strip().lower() not in {"y", "yes"}:
                raise RuntimeError("Pre-flight not confirmed; aborting before any adapter call.")
        else:
            raise RuntimeError(
                "Pre-flight confirmation required for a non-interactive run; pass --yes."
            )

    spent = sum(float(row.get("cost_usd") or 0.0) for row in existing_rows)
    completed_count = len(existing_rows)
    halted = False

    for spec in pending:
        if budget_usd is not None and spent >= budget_usd:
            halted = True
            print_fn(
                f"Budget cap ${budget_usd:.2f} reached; halting cleanly with "
                f"{completed_count} trial(s) persisted."
            )
            break

        result = adapter(spec.prompt, model)
        spent += result.cost_usd
        append_jsonl(
            trials_path,
            {
                "case_id": spec.case_id,
                "trial": spec.trial,
                "condition": spec.condition,
                "response": result.text,
                "cost_usd": result.cost_usd,
            },
        )
        completed_count += 1

    return {
        "run_dir": str(run_dir),
        "halted": halted,
        "spent_usd": spent,
        "completed_trials": completed_count,
        "planned_trials": len(trials),
    }


# --------------------------------------------------------------------------
# Report writer (R15)
# --------------------------------------------------------------------------


def build_report(trials: Sequence[dict[str, Any]], conditions: tuple[str, str]) -> dict[str, Any]:
    per_condition: dict[str, Any] = {}
    for condition in conditions:
        rows = [row for row in trials if row.get("condition") == condition]
        per_condition[condition] = {
            "trials": len(rows),
            "total_cost_usd": sum(float(row.get("cost_usd") or 0.0) for row in rows),
        }
    return {
        "conditions": per_condition,
        "total_trials": len(trials),
    }


def _render_manifest_lines(manifest: Mapping[str, Any]) -> list[str]:
    """The manifest in the human-readable report. A reader who never opens
    report.json should still be able to see what was measured and when."""
    lines = ["## Run manifest", ""]
    started, finished = manifest.get("started_at"), manifest.get("finished_at")
    lines.append(f"- run: `{manifest.get('run_id')}` ({started} → {finished})")
    lines.append(
        f"- claude CLI: `{manifest.get('cli_version') or 'unknown'}` "
        f"| skill-tuner: `{manifest.get('tool_version') or 'unknown'}`"
    )
    resolved = manifest.get("resolved_models") or []
    lines.append(
        f"- model pin: `{manifest.get('model_pin')}` "
        f"→ answered by: {', '.join(f'`{m}`' for m in resolved) or '`unrecorded`'}"
    )
    inputs = manifest.get("inputs") or []
    if inputs:
        lines.append("")
        lines.append("| Role | Input | sha256 | Source |")
        lines.append("| --- | --- | --- | --- |")
        for item in inputs:
            digest = str(item.get("sha256") or "")
            short = digest.split(":", 1)[-1][:12]
            flags = []
            if item.get("dirty"):
                flags.append("dirty")
            if item.get("differs_from_worktree"):
                flags.append("differs-from-worktree")
            source = str(item.get("source", ""))
            commit = (item.get("git_commit") or "")[:12]
            if commit:
                source = f"{source} @ {commit}"
            if flags:
                source = f"{source} ({', '.join(flags)})"
            lines.append(
                f"| {item.get('role')} | `{item.get('path')}` | `{short}` | {source} |"
            )
    lines.append("")
    return lines


def write_report(
    run_dir: Path,
    trials: Sequence[dict[str, Any]],
    conditions: tuple[str, str],
    manifest: Mapping[str, Any] | None = None,
) -> tuple[Path, Path]:
    """The shared report seam. Both evals funnel through here, so attaching
    the run manifest at this one point gives every eval provenance rather
    than each growing its own."""
    summary = build_report(trials, conditions)
    if manifest is not None:
        summary["manifest"] = dict(manifest)

    json_path = run_dir / "report.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# skill-tuner eval report",
        "",
        f"Conditions compared: **{conditions[0]}** vs **{conditions[1]}**.",
        "",
    ]
    for condition in conditions:
        stats = summary["conditions"][condition]
        lines.append(f"- {condition}: {stats['trials']} trial(s), ${stats['total_cost_usd']:.4f} spent")
    lines.append("")
    if manifest is not None:
        lines.extend(_render_manifest_lines(manifest))
    md_path = run_dir / "report.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return json_path, md_path


# --------------------------------------------------------------------------
# Case loading -- generic (case_id, {condition: prompt}) rows; battery-
# specific construction (routing-parity distractors, probe pairs, ...) is
# built on top of this in later units.
# --------------------------------------------------------------------------


def load_cases(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def conditions_from_cases(cases: Sequence[dict[str, Any]]) -> tuple[str, str]:
    if not cases:
        raise ValueError("cases file is empty")
    condition_sets = [tuple(sorted(case.get("prompts", {}))) for case in cases]
    first = condition_sets[0]
    if len(first) != 2:
        raise ValueError(f"each case must define exactly two conditions, got: {first}")
    mismatched = [other for other in condition_sets if other != first]
    if mismatched:
        raise ValueError("all cases must define the same pair of conditions")
    return first  # type: ignore[return-value]


def build_trial_specs(cases: Sequence[dict[str, Any]], trials_n: int) -> list[TrialSpec]:
    conditions = conditions_from_cases(cases)
    specs: list[TrialSpec] = []
    for trial in range(1, trials_n + 1):
        for case in cases:
            case_id = case["id"]
            for condition in conditions:
                specs.append(
                    TrialSpec(
                        case_id=case_id,
                        trial=trial,
                        condition=condition,
                        prompt=case["prompts"][condition],
                    )
                )
    return specs


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _add_eval_arguments(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--cases", type=Path, default=None, help="JSONL battery cases (generic path; superseded by --config)"
    )
    subparser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=(
            "JSON eval config for the real orchestrator: routing-parity's "
            "targets/distractors/battery_file, or probe's doctrine_file/target_file. "
            "Takes precedence over --cases."
        ),
    )
    subparser.add_argument("--trials", type=int, default=1, help="Trials per (case, condition)")
    subparser.add_argument("--model", default=DEFAULT_MODEL)
    subparser.add_argument("--run-id", default=None)
    subparser.add_argument("--resume", dest="resume", default=None, metavar="RUN_ID")
    subparser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    subparser.add_argument("--budget-usd", type=float, default=None)
    subparser.add_argument("--allow-unmetered", action="store_true")
    subparser.add_argument("--est-cost-per-call", type=float, default=DEFAULT_EST_COST_PER_CALL)
    subparser.add_argument("--yes", action="store_true")
    subparser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    subparser.add_argument(
        "--pin",
        default=None,
        metavar="GIT_REF",
        help=(
            "Read every input from this git ref (e.g. origin/main) instead of "
            "the working tree, so a run does not depend on uncommitted or "
            "behind-the-remote content. Overrides the config's 'pin'."
        ),
    )


def _run_eval(args: argparse.Namespace, prefix: str) -> int:
    if args.cases is None:
        raise RuntimeError(
            f"'{prefix}' needs either --config (the real eval) or --cases (the generic path)"
        )
    cases = load_cases(args.cases)
    conditions = conditions_from_cases(cases)
    trials = build_trial_specs(cases, args.trials)

    content_parts = [prefix, str(args.cases), str(args.trials), args.model, *conditions]
    run_dir, run_id = resolve_run_dir(
        args.reports_dir,
        prefix,
        content_parts,
        run_id=args.run_id,
        resume_id=args.resume,
    )

    def adapter(prompt: str, model: str) -> AdapterResult:
        return call_adapter(prompt, model, retries=args.retries)

    result = execute_battery(
        trials,
        run_dir=run_dir,
        adapter=adapter,
        model=args.model,
        budget_usd=args.budget_usd,
        allow_unmetered=args.allow_unmetered,
        auth_mode=detect_auth_mode(),
        est_cost_per_call=args.est_cost_per_call,
        yes=args.yes,
        isatty=sys.stdin.isatty(),
    )

    all_trials = read_jsonl(run_dir / "trials.jsonl")
    write_report(run_dir, all_trials, conditions)
    print(f"Run {run_id}: {result}")
    return 0


def _load_json_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_routing_parity_config(args: argparse.Namespace) -> int:
    """The real routing-parity path: --config names a JSON eval config
    (targets/distractors/battery_file/model), and every model call funnels
    through call_adapter -- the same guarded chokepoint every eval path
    uses. Budget/--yes/--resume are the same flags, passed straight through
    to routing_parity.run_routing_parity_eval, which honors them via
    tune.execute_battery internally.
    """
    import routing_parity  # local: routing_parity imports tune at module load time

    config = _load_json_config(args.config)
    if getattr(args, "pin", None):
        config = {**config, "pin": args.pin}
    base_dir = args.config.resolve().parent
    content_parts = ["routing-parity", str(args.config.resolve()), json.dumps(config, sort_keys=True)]
    run_dir, run_id = resolve_run_dir(
        args.reports_dir, "routing-parity", content_parts, run_id=args.run_id, resume_id=args.resume
    )

    def adapter(prompt: str, model: str) -> AdapterResult:
        return call_adapter(prompt, model, retries=args.retries)

    result = routing_parity.run_routing_parity_eval(
        config,
        adapter=adapter,
        run_dir=run_dir,
        base_dir=base_dir,
        budget_usd=args.budget_usd,
        allow_unmetered=args.allow_unmetered,
        auth_mode=detect_auth_mode(),
        yes=args.yes,
        run_id=run_id,
    )
    print(f"Run {run_id}: verdict={result['verdict']} failing_case_ids={result['failing_case_ids']}")
    return 0


def _run_probe_config(args: argparse.Namespace) -> int:
    """The real probe path: --config names a JSON eval config
    (doctrine_file/target_file/model/max_findings). probe.run_probe doesn't
    run its calls through execute_battery (its verify-call count depends on
    findings discovered mid-run), so the budget gate and the --yes/isatty
    confirm gate are applied here, ahead of the call, mirroring
    execute_battery's own pre-flight shape via confirm_or_abort.
    """
    import probe  # local: probe imports tune at module load time

    config = _load_json_config(args.config)
    if getattr(args, "pin", None):
        config = {**config, "pin": args.pin}
    base_dir = args.config.resolve().parent
    content_parts = ["probe", str(args.config.resolve()), json.dumps(config, sort_keys=True)]
    run_dir, run_id = resolve_run_dir(
        args.reports_dir, "probe", content_parts, run_id=args.run_id, resume_id=args.resume
    )

    auth_mode = detect_auth_mode()
    enforce_budget_preflight(auth_mode, args.budget_usd, args.allow_unmetered)

    # Parse through probe's own loader so the estimate counts exactly what the
    # run will spend: every target costs one probe call plus up to
    # max_findings * verify_trials verify calls.
    probe_config = probe.load_config(config, base_dir=base_dir)
    n_targets = len(probe_config.target_paths)
    max_findings = probe_config.max_findings
    verify_trials = probe_config.verify_trials
    per_target = 1 + max_findings * verify_trials
    planned = n_targets * per_target
    confirm_or_abort(
        f"Planned probe calls: up to {planned} "
        f"({n_targets} target(s) x [1 probe + up to {max_findings} findings x "
        f"{verify_trials} verify]) | "
        f"estimated cost: ${planned * args.est_cost_per_call:.2f} "
        f"(${args.est_cost_per_call:.4f}/call, model={config.get('model')})",
        yes=args.yes,
        isatty=sys.stdin.isatty(),
    )

    def adapter(prompt: str, model: str) -> AdapterResult:
        return call_adapter(prompt, model, retries=args.retries)

    result = probe.run_probe(
        config,
        adapter,
        run_dir,
        base_dir=base_dir,
        retries=args.retries,
        budget_usd=args.budget_usd,
        run_id=run_id,
    )
    print(
        f"Run {run_id}: findings_confirmed={result['findings_confirmed']} "
        f"refuted_count={result['refuted_count']} spent=${result['spent_usd']:.4f}"
    )
    if result["halted_on_budget"]:
        print(
            f"Budget cap ${args.budget_usd:.2f} reached; halted with a PARTIAL result "
            f"({len(result['per_target'])} of {len(result['target_files'])} target(s) probed)."
        )
    return 0


def _cmd_routing_parity(args: argparse.Namespace) -> int:
    if args.config is not None:
        return _run_routing_parity_config(args)
    return _run_eval(args, "routing-parity")


def _cmd_probe(args: argparse.Namespace) -> int:
    if args.config is not None:
        return _run_probe_config(args)
    return _run_eval(args, "probe")


def _cmd_report(args: argparse.Namespace) -> int:
    run_dir = args.reports_dir / args.run_id
    trials = read_jsonl(run_dir / "trials.jsonl")
    if args.conditions:
        conditions = tuple(args.conditions)
    else:
        conditions = tuple(sorted({row.get("condition") for row in trials if row.get("condition")}))
    if len(conditions) != 2:
        raise ValueError(f"report requires exactly two conditions, found: {conditions}")
    write_report(run_dir, trials, conditions)  # type: ignore[arg-type]
    print(f"Wrote report for {args.run_id}")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    """Re-read a finished run's manifest and report what has moved since.

    Makes no model call and costs nothing, which is the point: it is what
    keeps a published receipt falsifiable long after the run. The doctrine's
    own time-relative rule says a number measured on one CLI is not evidence
    about the next one; this is that rule as a command.

    Exit 0 when nothing drifted, 1 when something did, so it composes into a
    pre-publish check.
    """
    import provenance

    run_dir = args.run_dir if args.run_dir is not None else args.reports_dir / args.run_id
    report_path = run_dir / "report.json"
    if not report_path.is_file():
        raise FileNotFoundError(f"no report.json in {run_dir}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = report.get("manifest")
    if not manifest:
        print(
            f"{run_dir.name}: no manifest — this run predates provenance "
            "recording and cannot be verified."
        )
        return 1

    result = provenance.verify_manifest(manifest)

    if args.json:
        print(json.dumps(result, indent=2))
        return 1 if result["drifted"] else 0

    cli = result["cli_version"]
    print(f"run: {result['run_id']}")
    print(
        f"claude CLI: recorded {cli['recorded'] or 'unknown'} | "
        f"current {cli['current'] or 'unknown'}"
        + ("  <-- CHANGED" if cli["changed"] else "")
    )
    for item in result["inputs"]:
        marker = "ok " if item["status"] == "unchanged" else "!! "
        print(f"{marker}{item['status']:<12} {item['role']:<9} {item['path']}")
        if item["status"] == "changed":
            print(f"      recorded {item['recorded_sha256']}")
            print(f"      current  {item['current_sha256']}")
    print()
    print("DRIFTED — this receipt no longer describes current inputs." if result["drifted"]
          else "No drift: inputs and CLI match the recorded run.")
    return 1 if result["drifted"] else 0


def _cmd_compare(args: argparse.Namespace) -> int:
    """Judge one probe run against another, paired by document.

    Exit 0 when the candidate is `better` or `not_worse`; 1 otherwise, so a
    gate can be a shell condition instead of a human reading a table.
    """
    import compare as compare_mod

    if args.skill_creator is not None:
        import skillcreator

        if args.delta is None:
            print(
                "--delta is required with --skill-creator: the default of 1.0 is a "
                "margin in confirmed findings per document, which on a 0..1 pass "
                "rate would wave through every regression there is. Pick the "
                "smallest change that would matter to you (e.g. 0.05)."
            )
            return 2
        try:
            result = skillcreator.compare_benchmark(
                args.skill_creator,
                baseline=args.baseline,
                candidate=args.candidate,
                delta=args.delta,
                metric=args.metric,
                exclude=args.exclude or (),
            )
        except (skillcreator.BenchmarkError, compare_mod.ComparisonError) as exc:
            print(f"cannot compare: {exc}")
            return 2
    else:
        baseline = compare_mod.load_report(_resolve_run_path(args, args.baseline))
        candidate = compare_mod.load_report(_resolve_run_path(args, args.candidate))

        try:
            result = compare_mod.compare_probe_reports(
                baseline, candidate,
                delta=1.0 if args.delta is None else args.delta,
                exclude=args.exclude or (),
            )
        except compare_mod.ComparisonError as exc:
            print(f"cannot compare: {exc}")
            return 2

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(compare_mod.render(result))
    return 0 if result["verdict"] in ("better", "not_worse") else 1


def _resolve_run_path(args: argparse.Namespace, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.exists() else args.reports_dir / value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tune.py", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    routing_parity = subparsers.add_parser(
        "routing-parity", help="Run the routing-parity blind-battery eval"
    )
    _add_eval_arguments(routing_parity)
    routing_parity.set_defaults(handler=_cmd_routing_parity)

    probe = subparsers.add_parser("probe", help="Run the marginal-value probe eval")
    _add_eval_arguments(probe)
    probe.set_defaults(handler=_cmd_probe)

    report = subparsers.add_parser("report", help="Rebuild report.json/report.md for a run")
    report.add_argument("run_id")
    report.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    report.add_argument("--conditions", nargs=2, metavar=("A", "B"), default=None)
    report.set_defaults(handler=_cmd_report)

    verify = subparsers.add_parser(
        "verify",
        help="Check a finished run's inputs and CLI against now (no model calls, no cost)",
    )
    verify.add_argument("run_id", nargs="?", default=None)
    verify.add_argument("--run-dir", type=Path, default=None)
    verify.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    verify.add_argument("--json", action="store_true", help="Machine-readable output")
    verify.set_defaults(handler=_cmd_verify)

    compare_cmd = subparsers.add_parser(
        "compare",
        help="Pair two probe runs by document and judge the difference (no model calls)",
    )
    compare_cmd.add_argument("--baseline", required=True, metavar="RUN")
    compare_cmd.add_argument("--candidate", required=True, metavar="RUN")
    compare_cmd.add_argument(
        "--skill-creator",
        type=Path,
        default=None,
        metavar="BENCHMARK_DIR",
        help=(
            "Read a skill-creator benchmark tree instead of this repo's probe "
            "reports. --baseline/--candidate then name config directories "
            "(e.g. without_skill / with_skill)."
        ),
    )
    compare_cmd.add_argument(
        "--metric", default="pass_rate",
        help="Metric to pair on inside grading.json (skill-creator source only)",
    )
    compare_cmd.add_argument(
        "--delta",
        type=float,
        default=None,
        metavar="FINDINGS",
        help=(
            "Non-inferiority margin in confirmed findings per document: the "
            "largest regression you would still call acceptable (probe reports "
            "default to 1.0; required with --skill-creator)"
        ),
    )
    compare_cmd.add_argument(
        "--exclude",
        action="append",
        default=None,
        metavar="SUBSTRING",
        help=(
            "Drop documents matching this substring from BOTH sides. For a "
            "banked baseline whose input has since drifted: excluding the one "
            "document that moved keeps every other pair honest for the price "
            "of one document. Repeatable."
        ),
    )
    compare_cmd.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    compare_cmd.add_argument("--json", action="store_true")
    compare_cmd.set_defaults(handler=_cmd_compare)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
