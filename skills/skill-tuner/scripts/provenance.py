#!/usr/bin/env python3
"""Run provenance for skill-tuner evals (Unit 9.1). Python 3 stdlib only.

This module is the single input chokepoint. ``tune.call_adapter`` is the one
function that talks to the model; ``resolve_input`` is the one function that
reads a byte an eval will feed it. Both return their result *and* the record
of it, so no eval path can reach content without that content's provenance
being written down.

The problem it exists to solve: a report that cannot say what produced it is
an assertion wearing a table. Before this module, ``report.json`` carried
counts and costs and nothing else -- no model, no CLI version, no timestamp,
no content hash -- so a receipt could not be checked, dated, or reproduced.
That gap is not academic. skill-tuner's own doctrine carries a `[measured]`
rule saying no-op verdicts are time-relative and the test must be re-run
after every model or CLI upgrade; with no version recorded anywhere, the
runner could not tell whether a given receipt predated an upgrade, and the
CLI moved from 2.1.221 to 2.1.224 while the numbers sat unlabelled.

Three pieces:

- ``resolve_input`` reads one file, optionally pinned to a git ref, and
  returns a ``ResolvedInput``: the text, its sha256, and where it came from.
  A pin resolves through ``git show <ref>:<path>``, so a run measures
  committed content instead of whatever happened to be in a working tree.
  An unresolvable pin raises rather than falling back to the worktree --
  silently substituting different bytes is the exact failure a pin prevents.
- ``build_manifest`` assembles those records, the model pin and the models
  that actually answered, the CLI version, and the run's timestamps into one
  JSON-serializable block that rides along in every report.
- ``verify_manifest`` re-reads the recorded inputs and reports what drifted.
  It makes no model calls and costs nothing, which is what lets a receipt
  stay falsifiable long after the run that produced it.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

WORKTREE_SOURCE = "worktree"


class ProvenanceError(RuntimeError):
    """Raised when an input cannot be resolved as asked -- a missing file, a
    pin outside any repository, an unknown ref, or a path absent from the
    ref. Always a hard failure: the alternative is measuring bytes nobody
    asked for."""


# --------------------------------------------------------------------------
# Hashing and timestamps
# --------------------------------------------------------------------------


def sha256_text(text: str) -> str:
    """Content hash of a document, prefixed with its algorithm so a stored
    hash stays readable if the algorithm ever changes."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_now() -> str:
    """UTC timestamp, second resolution, ISO-8601 with a trailing Z."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


# --------------------------------------------------------------------------
# git interrogation
# --------------------------------------------------------------------------


def _git(args: Sequence[str], *, cwd: Path) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False
        )
    except OSError as exc:  # git absent from PATH
        return 127, "", str(exc)
    return completed.returncode, completed.stdout, completed.stderr.strip()


def _repo_root(path: Path) -> Path | None:
    start = path.parent if path.parent.exists() else Path.cwd()
    code, out, _ = _git(["rev-parse", "--show-toplevel"], cwd=start)
    return Path(out.strip()) if code == 0 and out.strip() else None


_MODULE_DIR = Path(__file__).resolve().parent


def tool_version() -> str | None:
    """skill-tuner's own version from the repo VERSION file. A receipt should
    say which build of the tool produced it, not only which model answered."""
    try:
        return (_MODULE_DIR.parents[2] / "VERSION").read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def cli_version() -> str | None:
    """The `claude` build this machine would run right now, or None if the
    CLI is absent. Captured once per run, not per call."""
    try:
        completed = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True, check=False
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    # "2.1.224 (Claude Code)" -> "2.1.224"
    first = (completed.stdout or "").strip().splitlines()
    return first[0].split()[0] if first and first[0].split() else None


# --------------------------------------------------------------------------
# Resolved inputs
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedInput:
    role: str  # "doctrine" | "target" | "config" | "battery"
    path: Path  # as configured, for report identity
    text: str  # the bytes actually fed to the model
    sha256: str
    source: str  # "worktree" | f"git:{ref}"
    git_commit: str | None
    git_path: str | None  # repo-relative
    # Two different questions, kept as two fields on purpose. `dirty` always
    # means "git reports uncommitted modifications for this path", whatever
    # the source. `differs_from_worktree` is pin-only and means "the bytes I
    # measured are not the bytes on disk" -- which happens with a perfectly
    # clean tree whose branch is simply behind the pinned ref. Collapsing
    # them into one flag makes a provenance record ambiguous exactly where it
    # exists to remove doubt.
    dirty: bool | None
    differs_from_worktree: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """The record without the content. Manifests name and hash an input;
        they never inline it, or every report would carry a copy of every
        document it measured."""
        return {
            "role": self.role,
            "path": str(self.path),
            "sha256": self.sha256,
            "source": self.source,
            "git_commit": self.git_commit,
            "git_path": self.git_path,
            "dirty": self.dirty,
            "differs_from_worktree": self.differs_from_worktree,
        }


def resolve_input(
    path: Path | str, *, role: str, pin: str | None = None
) -> ResolvedInput:
    """Read one input and record where it came from.

    With ``pin`` set (e.g. ``origin/main``), the content comes from that ref
    via ``git show``, so the run does not depend on a working tree that may
    be dirty or behind. Without it, the working tree is read and the record
    still carries the repo's commit and whether the file is modified.
    """
    resolved_path = Path(path)

    if pin is None:
        if not resolved_path.is_file():
            raise ProvenanceError(f"input not found: {resolved_path}")
        text = resolved_path.read_text(encoding="utf-8")
        root = _repo_root(resolved_path)
        if root is None:
            return ResolvedInput(
                role=role,
                path=resolved_path,
                text=text,
                sha256=sha256_text(text),
                source=WORKTREE_SOURCE,
                git_commit=None,
                git_path=None,
                dirty=None,
            )
        rel = _relative_to_root(resolved_path, root)
        code, out, _ = _git(["rev-parse", "HEAD"], cwd=root)
        commit = out.strip() if code == 0 else None
        return ResolvedInput(
            role=role,
            path=resolved_path,
            text=text,
            sha256=sha256_text(text),
            source=WORKTREE_SOURCE,
            git_commit=commit,
            git_path=rel,
            dirty=_is_dirty(root, rel),
        )

    root = _repo_root(resolved_path)
    if root is None:
        raise ProvenanceError(
            f"cannot pin {resolved_path} to {pin!r}: not inside a git repository"
        )
    rel = _relative_to_root(resolved_path, root)

    code, out, err = _git(["rev-parse", "--verify", f"{pin}^{{commit}}"], cwd=root)
    if code != 0:
        raise ProvenanceError(f"cannot resolve ref {pin!r} in {root}: {err}")
    commit = out.strip()

    code, out, err = _git(["show", f"{pin}:{rel}"], cwd=root)
    if code != 0:
        raise ProvenanceError(f"{rel} is not present in {pin!r} ({root}): {err}")
    text = out

    return ResolvedInput(
        role=role,
        path=resolved_path,
        text=text,
        sha256=sha256_text(text),
        source=f"git:{pin}",
        git_commit=commit,
        git_path=rel,
        dirty=_is_dirty(root, rel),
        differs_from_worktree=_worktree_differs(resolved_path, text),
    )


def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:  # pragma: no cover - path outside its own repo root
        return path.name


def _is_dirty(root: Path, rel: str) -> bool | None:
    code, out, _ = _git(["status", "--porcelain", "--", rel], cwd=root)
    if code != 0:
        return None
    return bool(out.strip())


def _worktree_differs(path: Path, pinned_text: str) -> bool | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8") != pinned_text


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------


# How the prompt reaches the model. Every run to date sends doctrine and
# target inline in a `claude -p` user message; an optimization that moves the
# doctrine into a system prompt, or a batch-API adapter, is a different
# envelope, and the model reads the same document differently across
# envelopes (measured in docs/COSTS.md). Recording the shape lets `compare`
# refuse cross-envelope pairings instead of silently measuring the envelope.
ADAPTER_SHAPE_USER_MESSAGE = "claude-p-user-message"
# The doctrine rides --append-system-prompt (cached prefix); target and
# instructions stay in the user message. Adopted at the v0.6.0 re-baseline
# boundary per docs/COSTS.md's rule.
ADAPTER_SHAPE_DOCTRINE_SYSTEM = "claude-p-doctrine-system-prompt"


def build_manifest(
    *,
    run_id: str,
    inputs: Iterable[ResolvedInput],
    model_pin: str,
    started_at: str,
    finished_at: str,
    cli_version: str | None,
    resolved_models: Sequence[str] = (),
    tool_version: str | None = None,
    adapter_shape: str = ADAPTER_SHAPE_USER_MESSAGE,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the block that makes a report self-describing.

    ``resolved_models`` is what actually answered, which is not the same as
    ``model_pin``: pins like ``claude-sonnet-5`` are aliases, and an alias
    repointed upstream would otherwise change what a published receipt means
    without changing a byte of the report.
    """
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "cli_version": cli_version,
        "tool_version": tool_version,
        "model_pin": model_pin,
        "resolved_models": list(resolved_models),
        "adapter_shape": adapter_shape,
        "inputs": [item.to_dict() for item in inputs],
    }
    if extra:
        manifest.update(dict(extra))
    return manifest


def verify_manifest(
    manifest: Mapping[str, Any], *, cli_version: str | None = None
) -> dict[str, Any]:
    """Re-read a manifest's inputs and report what moved since the run.

    Costs nothing -- no model call, no network. Each input comes back
    ``unchanged``, ``changed``, ``missing``, or ``unresolvable`` (its pinned
    ref no longer resolves). A CLI or resolved-model change counts as drift
    on its own, with every input byte-identical: the doctrine's time-relative
    rule says a receipt measured on one binary is not evidence about the next.
    """
    current_cli = cli_version if cli_version is not None else globals()["cli_version"]()
    recorded_cli = manifest.get("cli_version")

    results: list[dict[str, Any]] = []
    for record in manifest.get("inputs", []):
        results.append(_verify_one(record))

    cli_changed = recorded_cli != current_cli
    drifted = cli_changed or any(item["status"] != "unchanged" for item in results)

    return {
        "run_id": manifest.get("run_id"),
        "drifted": drifted,
        "inputs": results,
        "cli_version": {
            "recorded": recorded_cli,
            "current": current_cli,
            "changed": cli_changed,
        },
    }


def _verify_one(record: Mapping[str, Any]) -> dict[str, Any]:
    path = Path(record["path"])
    source = record.get("source", WORKTREE_SOURCE)
    pin = source.split("git:", 1)[1] if source.startswith("git:") else None

    entry: dict[str, Any] = {
        "role": record.get("role"),
        "path": str(path),
        "source": source,
        "recorded_sha256": record.get("sha256"),
        "recorded_commit": record.get("git_commit"),
    }

    try:
        current = resolve_input(path, role=record.get("role", "target"), pin=pin)
    except ProvenanceError as exc:
        entry["status"] = "missing" if pin is None else "unresolvable"
        entry["detail"] = str(exc)
        entry["current_sha256"] = None
        return entry

    entry["current_sha256"] = current.sha256
    entry["current_commit"] = current.git_commit
    entry["status"] = (
        "unchanged" if current.sha256 == record.get("sha256") else "changed"
    )
    return entry
