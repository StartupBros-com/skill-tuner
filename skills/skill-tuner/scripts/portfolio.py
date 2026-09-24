"""Read-only inventory of Claude Code skills, listing tiers, and usage.

The portfolio describes the current project and user settings without making
model calls or recommending changes. Parsing, tier selection, character
accounting, and Markdown rendering are pure functions; ``run_portfolio`` reads
the local sources and assembles their report. Python 3 standard library only.
"""

from __future__ import annotations

import html
import json
import math
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from routing_parity import extract_description

FORMULA_SOURCE = "Claude Code 2.1.280"
TIERS = ("on", "name-only", "user-invocable-only", "off")
PLUGIN_OVERRIDE_NOTE = (
    "skillOverrides entry ignored: plugin skills are not affected "
    "(Claude Code docs; measured 2.1.280)"
)
BUDGET_NOTE = (
    "While over budget, the model sees at most rendered_max_chars, keeping "
    "every listed name. Descriptions are restored when they fit, in descending "
    "usage score; the rest render as bare names. Scores use only the exact "
    "runtime-name key: usageCount × max(0.5 ** (days_since_last_use / 7), 0.1), "
    "or 0 when absent. Ties follow an internal order this inventory cannot see. "
    "An entry's or a plugin's listing chars are what it demands, not what "
    "removing it saves."
)
BUDGET_ENV = "SLASH_COMMAND_TOOL_CHAR_BUDGET"
_JS_DECIMAL = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_JS_RADIX = re.compile(r"0(?:[xX][0-9a-fA-F]+|[oO][0-7]+|[bB][01]+)")
_THOUSANDS = re.compile(r"[+-]?\d{1,3}([_,   ])\d{3}(?:\1\d{3})*")
QUESTION = "Should the model start this skill on its own?"
DISPOSITIONS = (
    "keep",
    "fix the description so it fires",
    "name-only",
    "/-only (user-invocable-only)",
)


def parse_frontmatter(text: str) -> dict[str, str]:
    """Read inventory fields using the existing field-scoped scalar parser.

    Isolate top-level fields and present each as a description stanza to
    ``routing_parity.extract_description``. This reuses its handling of quoted,
    folded, and literal values without accidentally reading nested metadata.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = next(
        (index for index, line in enumerate(lines[1:], 1) if line.rstrip() == "---"),
        None,
    )
    if end is None:
        return {}
    fields = {"name", "description", "when_to_use", "disable-model-invocation"}
    values: dict[str, str] = {}
    for index in range(1, end):
        match = re.match(r"^([\w-]+):[ \t]*(.*)$", lines[index])
        if not match or match[1] not in fields:
            continue
        continuation: list[str] = []
        for line in lines[index + 1 : end]:
            if line.strip() and not line.startswith((" ", "\t")):
                break
            continuation.append(line)
        value = match[2]
        # Keep quoted hashes intact; comments belong to the field declaration,
        # not to its scalar value or indented block contents.
        quoted = re.match(
            r"""(?:"(?:\\.|[^"\\])*"|'(?:''|[^'])*')(?=\s*(?:#|$))""", value
        )
        value = quoted[0] if quoted else re.split(r"(?:^|\s+)#", value, maxsplit=1)[0]
        stanza = "\n".join(["---", "description: " + value, *continuation, "---", ""])
        values[match[1]] = extract_description(stanza)
    return values


def listing_chars(
    name: str, description: str, when_to_use: str, tier: str, max_desc_chars: int = 1536
) -> int:
    """Apply the listing formula measured in Claude Code 2.1.280."""
    if tier == "on":
        text = f"{description} - {when_to_use}" if when_to_use else description
        return len(name) + 4 + min(len(text), max_desc_chars)
    if tier == "name-only":
        return len(name) + 2
    return 0


def _finite_number(value: Any) -> bool:
    try:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
    except OverflowError:
        return False


def env_budget(raw: Any) -> float | None:
    """Read SLASH_COMMAND_TOOL_CHAR_BUDGET as Claude Code 2.1.280 does.

    JavaScript's `Number(raw)`, else a thousands-separated integer; any nonzero
    result replaces the budget formula. None means the formula applies.
    """
    text = str(raw).strip()
    if not text:
        number = 0.0
    elif _JS_DECIMAL.fullmatch(text):
        number = float(text)
    elif _JS_RADIX.fullmatch(text):
        number = float(int(text, 0))
    elif text in ("Infinity", "+Infinity", "-Infinity"):
        number = float(text.replace("Infinity", "inf"))
    elif len(text) <= 32 and _THOUSANDS.fullmatch(text):
        number = float(re.sub(r"[_,   ]", "", text))
    else:
        return None
    return number or None


def skill_tier(
    name: str,
    metadata: Mapping[str, str],
    plugin: str | None,
    overrides: Mapping[str, tuple[str, str]],
) -> tuple[str, str, list[str]]:
    """Resolve frontmatter before overrides; plugin overrides never apply."""
    notes = [PLUGIN_OVERRIDE_NOTE] if plugin and name in overrides else []
    if metadata.get("disable-model-invocation", "").lower() == "true":
        return "user-invocable-only", "frontmatter", notes
    if not plugin and name in overrides:
        tier, layer = overrides[name]
        return tier, f"override:{layer}", notes
    return "on", "default", notes


def _checkout_parts(parts: Sequence[str]) -> list[str]:
    """Drop every `.claude/worktrees/<task>` hop, mapping a worktree copy onto its checkout."""
    kept: list[str] = []
    index = 0
    while index < len(parts):
        if tuple(parts[index : index + 2]) == (
            ".claude",
            "worktrees",
        ) and index + 2 < len(parts):
            index += 3
            continue
        kept.append(parts[index])
        index += 1
    return kept


def _defines(directory: Path, name: str) -> bool:
    try:
        return (directory / ".claude" / "skills" / name / "SKILL.md").is_file() or (
            directory / ".claude" / "commands" / f"{name}.md"
        ).is_file()
    except OSError:
        return False


def _other_checkouts(
    name: str, prefix: str, checkout: Path, known_projects: set[Path]
) -> set[Path]:
    """Other checkouts a `<prefix>:<name>` key could have been recorded for.

    Evidence is a known session directory whose `<prefix>` is itself a known
    directory or defines the skill.
    """
    others: set[Path] = set()
    for known in known_projects:
        origin = known / prefix
        if origin in known_projects or _defines(origin, name):
            other = Path(*_checkout_parts(origin.parts))
            if other != checkout:
                others.add(other)
    return others


def _project_usage_attribution(
    name: str,
    project: Path,
    usage: Mapping[str, Any],
    known_projects: Sequence[Path],
) -> tuple[list[str], list[str], dict[str, int]]:
    """Keys a project skill's worktree copies and ancestor-directory sessions record.

    Claude Code names a skill found below the session's directory
    `<relative path>:<name>`, so one project skill fragments into keys such as
    `.claude/worktrees/<task>:name` and `SITES/<repo>:name`. Only prefixes that
    contain a `/` are read: a one-segment prefix cannot be told apart from a
    plugin's `plugin:name` key. An ancestor key is this project's only when the
    session directory that would have recorded it is a known project, and a
    worktree key only when its worktree is known or still on disk. Returns the
    counted keys, the untraceable keys, and, per counted key, how many other
    checkouts could have recorded it too.
    """
    project_parts = _checkout_parts(project.parts)
    checkout = Path(*project_parts)
    known = set(known_projects)
    keys: list[str] = []
    unattributed: list[str] = []
    shared: dict[str, int] = {}
    for key in usage:
        prefix, _, suffix = key.rpartition(":")
        if suffix != name or "/" not in prefix:
            continue
        relative = _checkout_parts(prefix.split("/"))
        if relative:
            if (
                len(relative) >= len(project_parts)
                or project_parts[-len(relative) :] != relative
            ):
                continue
            traced = Path(*project_parts[: -len(relative)]) in known
        else:
            candidate = checkout / prefix
            try:
                traced = candidate in known or candidate.exists()
            except OSError:
                traced = False
        others = _other_checkouts(name, prefix, checkout, known)
        if traced:
            keys.append(key)
            if others:
                shared[key] = len(others)
        elif not others:
            unattributed.append(key)
    return sorted(keys), sorted(unattributed), shared


def _project_usage_keys(
    name: str,
    project: Path,
    usage: Mapping[str, Any],
    known_projects: Sequence[Path] = (),
) -> list[str]:
    return _project_usage_attribution(name, project, usage, known_projects)[0]


def skill_usage_context(
    name: str,
    source: str,
    usage: Mapping[str, Any],
    project: Path | None,
    known_projects: Sequence[Path],
) -> tuple[int, list[str]]:
    """Describe usage that cannot be isolated to this project's runtime name."""
    if project is None:
        return 0, []
    notes: list[str] = []
    if source in ("project", "project-command"):
        _, unattributed, shared_keys = _project_usage_attribution(
            name, project, usage, known_projects
        )
        for key, others in sorted(shared_keys.items()):
            notes.append(
                f"usage key {key} may also hold uses from {others} other "
                "project(s) at the same relative path"
            )
        if unattributed:
            counts = [
                usage[key].get("usageCount")
                if isinstance(usage[key], Mapping)
                else None
                for key in unattributed
            ]
            uses = (
                sum(counts)
                if all(
                    isinstance(count, int) and not isinstance(count, bool)
                    for count in counts
                )
                else "unknown"
            )
            notes.append(
                f"{uses} uses under {len(unattributed)} worktree or "
                "ancestor-directory key(s) that cannot be traced to a project "
                "are not counted"
            )
    shared = 0
    if source in ("user", "project", "user-command", "project-command"):
        checkout = Path(*_checkout_parts(project.parts))
        # A repository's worktrees are one project, not one per worktree.
        sharing: set[Path] = set()
        for known in known_projects:
            known_checkout = Path(*_checkout_parts(known.parts))
            if (
                known == checkout
                or checkout in known.parents
                or known_checkout == checkout
                or known_checkout in sharing
            ):
                continue
            try:
                if (known / ".claude" / "skills" / name / "SKILL.md").is_file() or (
                    known / ".claude" / "commands" / f"{name}.md"
                ).is_file():
                    sharing.add(known_checkout)
            except OSError as exc:
                notes.append(
                    f"Cannot inspect shared usage key {name} in {known}: {exc}"
                )
        shared = len(sharing)
        if shared:
            notes.append(
                f"usage key {name} is shared with {shared} other project(s) "
                "that define it; uses may include theirs"
            )
    return shared, notes


def skill_usage(
    name: str,
    source: str,
    usage: Mapping[str, Any],
    project: Path | None = None,
    known_projects: Sequence[Path] = (),
) -> tuple[int | None, str | None, list[str]]:
    """Read exact usage names, with a bare-name fallback only for synced skills.

    Project skills and commands also sum the keys their worktree copies record.
    """
    keys = [name] if name in usage else []
    if not keys and source == "synced":
        bare_name = name.removeprefix("anthropic-skills:")
        if bare_name in usage:
            keys = [bare_name]
    if project is not None and source in ("project", "project-command"):
        keys.extend(_project_usage_keys(name, project, usage, known_projects))
    entries = [usage[key] for key in keys]
    if not entries:
        return None, None, []
    counts = [
        entry.get("usageCount")
        for entry in entries
        if isinstance(entry, Mapping)
        and isinstance(entry.get("usageCount"), int)
        and not isinstance(entry.get("usageCount"), bool)
        and entry["usageCount"] >= 0
    ]
    uses = sum(counts) if len(counts) == len(entries) else None
    last_used = None
    timestamps = [
        entry.get("lastUsedAt")
        for entry in entries
        if isinstance(entry, Mapping)
        and isinstance(entry.get("lastUsedAt"), (int, float))
        and not isinstance(entry.get("lastUsedAt"), bool)
    ]
    if timestamps:
        try:
            last_used = datetime.fromtimestamp(
                max(timestamps) / 1000, timezone.utc
            ).isoformat()
        except (OverflowError, OSError, ValueError):
            pass
    return uses, last_used, keys


def _source(name: str, path: Path) -> dict[str, Any]:
    return {"name": name, "path": str(path), "status": "ok", "count": 0, "notes": []}


def _unreadable(source: dict[str, Any], note: str) -> None:
    source["status"] = "unreadable"
    source["notes"].append(note)


def _read_json(path: Path, source: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        source["status"] = "missing"
        source["notes"].append("Source file is missing.")
        return {}
    except (OSError, UnicodeError, ValueError) as exc:
        source["status"] = "unreadable"
        source["notes"].append(f"Cannot read JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        source["status"] = "unreadable"
        source["notes"].append("Expected a JSON object.")
        return {}
    source["count"] = len(value)
    return value


def _directory_entries(
    path: Path, source: dict[str, Any], *, root: bool = False
) -> list[Path]:
    """List a directory once, retaining missing paths and read failures."""
    try:
        return sorted(path.iterdir())
    except FileNotFoundError:
        if root:
            source["status"] = "missing"
        source["notes"].append(f"Missing directory or broken symlink: {path}")
        return []
    except (OSError, ValueError) as exc:
        source["status"] = "unreadable"
        source["notes"].append(f"Cannot list {path}: {exc}")
        return []


def _directories(
    path: Path, source: dict[str, Any], *, root: bool = False
) -> list[Path]:
    """Enumerate one directory level, following links and retaining read failures."""
    directories: list[Path] = []
    for entry in _directory_entries(path, source, root=root):
        try:
            if stat.S_ISDIR(entry.stat().st_mode):
                directories.append(entry)
        except FileNotFoundError:
            source["notes"].append(f"Broken symlink or missing entry: {entry}")
        except OSError as exc:
            source["status"] = "unreadable"
            source["notes"].append(f"Cannot inspect {entry}: {exc}")
    return directories


def _command_files(path: Path, source: dict[str, Any]) -> list[tuple[Path, str, bool]]:
    """Top-level ``*.md`` commands, listed by file stem; subfolders are noted, not read.

    Claude Code puts commands in the same listing as skills, so a command costs
    listing characters exactly like a skill of the same description.
    """
    files: list[tuple[Path, str, bool]] = []
    for entry in _directory_entries(path, source, root=True):
        try:
            mode = entry.stat().st_mode
            if entry.suffix == ".md" and stat.S_ISREG(mode):
                files.append((entry, entry.stem, False))
            elif stat.S_ISDIR(mode):
                source["notes"].append(f"Subfolder not inventoried: {entry.name}")
        except FileNotFoundError:
            source["notes"].append(f"Broken symlink or missing entry: {entry}")
        except OSError as exc:
            _unreadable(source, f"Cannot inspect {entry}: {exc}")
    return files


def _skill_files(directories: Sequence[Path]) -> list[tuple[Path, str, bool]]:
    """Each skill directory's SKILL.md, named by the directory."""
    return [
        (directory / "SKILL.md", directory.name, False) for directory in directories
    ]


def _load_settings(
    claude_home: Path, project: Path, sources: list[dict[str, Any]]
) -> tuple[
    dict[str, tuple[str, str]],
    dict[str, tuple[bool, str]],
    float,
    int,
    tuple[Any, str] | None,
]:
    overrides: dict[str, tuple[str, str]] = {}
    enabled_plugins: dict[str, tuple[bool, str]] = {}
    fraction = 0.01
    max_desc_chars = 1536
    budget_env: tuple[Any, str] | None = None
    for layer, path in (
        ("user", claude_home / "settings.json"),
        ("project", project / ".claude" / "settings.json"),
        ("local", project / ".claude" / "settings.local.json"),
    ):
        source = _source(f"settings:{layer}", path)
        sources.append(source)
        settings = _read_json(path, source)
        for key, merged in (
            ("skillOverrides", overrides),
            ("enabledPlugins", enabled_plugins),
        ):
            values = settings.get(key, {})
            if not isinstance(values, dict):
                source["notes"].append(f"Ignored {key}: expected an object.")
                continue
            for name, value in values.items():
                valid = (
                    isinstance(value, str) and value in TIERS
                    if key == "skillOverrides"
                    else isinstance(value, bool)
                )
                if valid:
                    merged[name] = (value, layer)
                else:
                    source["notes"].append(f"Ignored invalid {key} value for {name}.")
        if "skillListingBudgetFraction" in settings:
            value = settings["skillListingBudgetFraction"]
            if _finite_number(value) and 0 < value <= 1:
                fraction = value
            else:
                source["notes"].append("Ignored invalid skillListingBudgetFraction.")
        if "skillListingMaxDescChars" in settings:
            value = settings["skillListingMaxDescChars"]
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                max_desc_chars = value
            else:
                source["notes"].append("Ignored invalid skillListingMaxDescChars.")
        env = settings.get("env", {})
        if not isinstance(env, dict):
            source["notes"].append("Ignored env: expected an object.")
        elif BUDGET_ENV in env:
            budget_env = (env[BUDGET_ENV], f"{layer} settings env")
    return overrides, enabled_plugins, fraction, max_desc_chars, budget_env


def _read_skills(
    files: Sequence[tuple[Path, str, bool]],
    source: dict[str, Any],
    source_name: str,
    overrides: Mapping[str, tuple[str, str]],
    usage: Mapping[str, Any],
    *,
    plugin: str | None = None,
    project: Path | None = None,
    known_projects: Sequence[Path] = (),
    max_desc_chars: int = 1536,
) -> list[dict[str, Any]]:
    """Inventory (file, directory or stem name, plugin single-skill root) entries."""
    skills: list[dict[str, Any]] = []
    for path, fallback, single_skill_root in files:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # Claude Code skips a dangling SKILL.md too, so nothing listed is missing.
            if path.is_symlink():
                source["notes"].append(f"Broken symlink: {path}")
            continue
        except (OSError, UnicodeError) as exc:
            source["status"] = "unreadable"
            source["notes"].append(f"Cannot read {path}: {exc}")
            continue
        metadata = parse_frontmatter(text)
        name = fallback
        if source_name == "synced":
            name = f"anthropic-skills:{name}"
        elif plugin:
            short_name = plugin.split("@", 1)[0]
            if single_skill_root:
                name = metadata.get("name", "").strip().removeprefix(f"{short_name}:")
                name = name or fallback
            if path.name == "SKILL.md":
                name = re.sub(r"[^A-Za-z0-9_-]", "-", name)
            name = f"{short_name}:{name}"
        description = metadata.get("description", "")
        when_to_use = metadata.get("when_to_use", "")
        tier, reason, notes = skill_tier(name, metadata, plugin, overrides)
        uses, last_used, usage_keys = skill_usage(
            name, source_name, usage, project, known_projects
        )
        shared_key_projects, usage_notes = skill_usage_context(
            name, source_name, usage, project, known_projects
        )
        notes.extend(usage_notes)
        if usage_keys and uses is None:
            notes.append(
                "Usage count is unknown for one or more attributed keys; uses are unknown."
            )
        elif len(usage_keys) > 1:
            notes.append(
                f"uses summed over {len(usage_keys)} usage keys "
                "(worktree copies or ancestor-directory sessions)"
            )
        skills.append(
            {
                "name": name,
                "display_name": metadata.get("name")
                if "name" in metadata and metadata["name"] != name
                else None,
                "source": source_name,
                "path": str(path),
                "plugin": plugin,
                "description": description,
                "when_to_use": when_to_use,
                "tier": tier,
                "tier_reason": reason,
                "listing_chars": listing_chars(
                    name, description, when_to_use, tier, max_desc_chars
                ),
                "uses": uses,
                "last_used": last_used,
                "usage_key": usage_keys[0] if usage_keys else None,
                "usage_keys": usage_keys,
                "shared_key_projects": shared_key_projects,
                "notes": notes,
            }
        )
    source["count"] += len(skills)
    return skills


def _choose_install(
    entries: Any, project: Path, notes: list[str]
) -> Mapping[str, Any] | None:
    if not isinstance(entries, list):
        notes.append("Invalid install entries: expected an array.")
        return None
    user_entry = None
    project_entry = None
    local_entry = None
    for entry in entries:
        if not isinstance(entry, dict):
            notes.append("Ignored an install entry that is not an object.")
            continue
        if entry.get("scope") == "user" and user_entry is None:
            user_entry = entry
        if entry.get("scope") in ("local", "project") and isinstance(
            entry.get("projectPath"), str
        ):
            try:
                if Path(entry["projectPath"]).expanduser().resolve() == project:
                    if entry["scope"] == "local":
                        local_entry = local_entry or entry
                    else:
                        project_entry = project_entry or entry
            except (OSError, RuntimeError, ValueError) as exc:
                notes.append(f"Cannot resolve plugin projectPath: {exc}")
    return local_entry or project_entry or user_entry


def _plugin_files(
    install: Path, kind: str, manifest: Mapping[str, Any], source: dict[str, Any]
) -> list[tuple[Path, str, bool]]:
    """Read default and declared paths, keeping the first copy of each file."""
    default = install / kind
    paths: list[Path] = []
    try:
        default.lstat()
        paths.append(default)
    except FileNotFoundError:
        if kind == "skills" and kind not in manifest:
            try:
                if (install / "SKILL.md").is_file():
                    paths.append(install)
            except OSError as exc:
                _unreadable(source, f"Cannot inspect {install / 'SKILL.md'}: {exc}")
    except OSError as exc:
        _unreadable(source, f"Cannot inspect {default}: {exc}")

    declared = manifest.get(kind, [])
    if isinstance(declared, str):
        declared = [declared]
    if not isinstance(declared, list):
        _unreadable(
            source,
            f"Manifest {kind} not inventoried: expected a string or list of strings.",
        )
        declared = []
    for value in declared:
        if not isinstance(value, str):
            _unreadable(
                source,
                f"Manifest {kind} entry not inventoried: expected a path string.",
            )
            continue
        try:
            path = (install / value).resolve()
            if not path.is_relative_to(install):
                _unreadable(
                    source,
                    f"Manifest {kind} path outside install directory, not inventoried: {value}",
                )
                continue
            if path != default.resolve() and not (kind == "skills" and path == install):
                paths.append(path)
        except (OSError, RuntimeError, ValueError) as exc:
            _unreadable(source, f"Manifest {kind} path not inventoried: {value}: {exc}")

    files: list[tuple[Path, str, bool]] = []
    seen: set[Path] = set()
    for path in paths:
        try:
            mode = path.stat().st_mode
            if stat.S_ISDIR(mode):
                if kind == "commands":
                    candidates = _command_files(path, source)
                elif (path / "SKILL.md").is_file():
                    candidates = [(path / "SKILL.md", path.name, True)]
                else:
                    previous_notes = len(source["notes"])
                    candidates = _skill_files(_directories(path, source))
                    if len(source["notes"]) > previous_notes:
                        source["status"] = "unreadable"
            elif kind == "commands" and path.suffix == ".md" and stat.S_ISREG(mode):
                candidates = [(path, path.stem, False)]
            else:
                _unreadable(source, f"Manifest {kind} path not inventoried: {path}")
                continue
            for candidate in candidates:
                resolved = candidate[0].resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    files.append(candidate)
        except FileNotFoundError:
            _unreadable(
                source, f"Missing directory or broken symlink, not inventoried: {path}"
            )
        except (OSError, RuntimeError, ValueError) as exc:
            _unreadable(source, f"Cannot inventory {path}: {exc}")
    return files


def _listing_totals(skills: Sequence[Mapping[str, Any]]) -> tuple[int, int, int]:
    listed = [skill for skill in skills if skill["tier"] in ("on", "name-only")]
    separators = max(0, len(listed) - 1)
    demand = sum(skill["listing_chars"] for skill in listed) + separators
    bare_floor = sum(len(skill["name"]) + 2 for skill in listed) + separators
    return demand, bare_floor, len(listed)


def _rendered_max(demand: int, bare_floor: int, budget: int) -> int:
    return min(demand, max(budget, bare_floor))


def run_portfolio(
    *,
    claude_home: Path | None = None,
    claude_json: Path | None = None,
    project: Path | None = None,
    context_tokens: int = 200000,
    bytes_per_token: float = 3,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Read the current portfolio; missing or unreadable sources remain in the report.

    No paths are created or modified. Callers own serialization and any report
    persistence, so the same inventory supports a completely read-only JSON CLI.
    `env` is the process environment (default `os.environ`).
    """
    if (
        not _finite_number(context_tokens)
        or not _finite_number(bytes_per_token)
        or context_tokens < 0
        or bytes_per_token < 0
    ):
        raise ValueError(
            "context_tokens and bytes_per_token must be nonnegative and finite"
        )
    claude_home = Path(claude_home or "~/.claude").expanduser().resolve()
    claude_json = Path(claude_json or "~/.claude.json").expanduser().resolve()
    project = Path(project or Path.cwd()).expanduser().resolve()
    sources: list[dict[str, Any]] = []
    overrides, enabled, fraction, max_desc_chars, budget_env = _load_settings(
        claude_home, project, sources
    )
    usage_source = _source("usage", claude_json)
    sources.append(usage_source)
    state = _read_json(claude_json, usage_source)
    # Claude Code applies ~/.claude.json's env, then each settings layer's,
    # over the process environment; the last layer that sets the key wins.
    global_env = state.get("env", {})
    if budget_env is None and isinstance(global_env, dict) and BUDGET_ENV in global_env:
        budget_env = (global_env[BUDGET_ENV], "~/.claude.json env")
    environ = os.environ if env is None else env
    if budget_env is None and BUDGET_ENV in environ:
        budget_env = (environ[BUDGET_ENV], "environment")
    usage = state.get("skillUsage", {})
    if not isinstance(usage, dict):
        usage_source["notes"].append("Ignored skillUsage: expected an object.")
        usage = {}
    usage_source["count"] = len(usage)
    projects = state.get("projects", {})
    known_projects: list[Path] = []
    if not isinstance(projects, dict):
        usage_source["notes"].append("Ignored projects: expected an object.")
    else:
        for name in projects:
            try:
                path = Path(name)
                if not path.is_absolute():
                    usage_source["notes"].append(
                        f"Ignored non-absolute project path: {name}"
                    )
                else:
                    known_projects.append(path.resolve())
            except (OSError, RuntimeError, ValueError) as exc:
                usage_source["notes"].append(
                    f"Cannot resolve project path {name}: {exc}"
                )
    known_projects = sorted(set(known_projects))

    skills: list[dict[str, Any]] = []
    for name, path in (
        ("user", claude_home / "skills"),
        ("synced", claude_home / "skills" / "synced"),
        ("project", project / ".claude" / "skills"),
    ):
        source = _source(name, path)
        sources.append(source)
        directories = _directories(path, source, root=True)
        if name == "user":
            directories = [
                directory for directory in directories if directory.name != "synced"
            ]
        elif name == "synced":
            directories = [
                skill for group in directories for skill in _directories(group, source)
            ]
        skills.extend(
            _read_skills(
                _skill_files(directories),
                source,
                name,
                overrides,
                usage,
                project=project,
                known_projects=known_projects,
                max_desc_chars=max_desc_chars,
            )
        )

    for name, path in (
        ("user-command", claude_home / "commands"),
        ("project-command", project / ".claude" / "commands"),
    ):
        source = _source(name, path)
        sources.append(source)
        skills.extend(
            _read_skills(
                _command_files(path, source),
                source,
                name,
                overrides,
                usage,
                project=project,
                known_projects=known_projects,
                max_desc_chars=max_desc_chars,
            )
        )

    registry_path = claude_home / "plugins" / "installed_plugins.json"
    registry_source = _source("plugins", registry_path)
    sources.append(registry_source)
    installed = _read_json(registry_path, registry_source).get("plugins", {})
    if not isinstance(installed, dict):
        registry_source["notes"].append("Ignored plugins: expected an object.")
        installed = {}
    registry_source["count"] = len(installed)
    plugins: list[dict[str, Any]] = []
    for key, entries in sorted(installed.items()):
        notes: list[str] = []
        entry = _choose_install(entries, project, notes)
        enabled_value, enabled_by = enabled.get(key, (None, None))
        row = {
            "plugin": key,
            "enabled": enabled_value,
            "enabled_by": enabled_by,
            "visible_skills": 0,
            "listing_chars": 0,
            "complete": True,
            "notes": notes,
        }
        plugins.append(row)
        if entry is None:
            row["complete"] = False
            notes.append(
                "Incomplete: no matching local or project installation, or user installation."
            )
            continue
        install_path = entry.get("installPath")
        if not isinstance(install_path, str) or not install_path:
            row["complete"] = False
            notes.append("Incomplete: install entry has no valid installPath.")
            continue
        try:
            install = Path(install_path).expanduser().resolve()
            if not stat.S_ISDIR(install.stat().st_mode):
                raise ValueError("installPath is not a directory")
        except (OSError, RuntimeError, ValueError) as exc:
            row["complete"] = False
            notes.append(f"Incomplete: cannot read installPath: {exc}")
            continue
        manifest_path = install / ".claude-plugin" / "plugin.json"
        manifest_source = _source(f"plugin-manifest:{key}", manifest_path)
        manifest = _read_json(manifest_path, manifest_source)
        if manifest_source["status"] == "unreadable" or (
            manifest_source["status"] == "missing" and manifest_path.is_symlink()
        ):
            row["complete"] = False
            notes.extend(
                f"Incomplete plugin manifest: {note}"
                for note in manifest_source["notes"]
            )
            # Root fallback requires knowing the manifest has no skills field.
            manifest = {"skills": []}
        source = _source(f"plugin:{key}", install / "skills")
        sources.append(source)
        if enabled_value is not True:
            note = (
                "Skills not listed: plugin is disabled."
                if enabled_value is False
                else "Skills not listed: plugin enabled state is unknown."
            )
            notes.append(note)
            source["notes"].append(note)
            # Source existence is useful even when its skills do not participate.
            _directories(install / "skills", source, root=True)
            continue
        commands_source = _source(f"plugin-commands:{key}", install / "commands")
        sources.append(commands_source)
        plugin_skills = []
        for kind, plugin_source in (("skills", source), ("commands", commands_source)):
            plugin_skills += _read_skills(
                _plugin_files(install, kind, manifest, plugin_source),
                plugin_source,
                "plugin",
                overrides,
                usage,
                plugin=key,
                max_desc_chars=max_desc_chars,
            )
            if plugin_source["status"] != "ok":
                row["complete"] = False
            notes.extend(plugin_source["notes"])
        if not row["complete"]:
            notes.append("Incomplete plugin inventory.")
        row["visible_skills"] = sum(
            skill["tier"] in ("on", "name-only") for skill in plugin_skills
        )
        row["listing_chars"] = sum(skill["listing_chars"] for skill in plugin_skills)
        skills.extend(plugin_skills)

    total_chars, bare_floor_chars, listed = _listing_totals(skills)
    budget_source = "formula"
    budget_notes: list[str] = []
    override = env_budget(budget_env[0]) if budget_env is not None else None
    if override is not None and math.isfinite(override):
        # Listing lengths are integers, so the floor compares identically.
        budget_chars = math.floor(override)
        budget_source = f"{BUDGET_ENV} ({budget_env[1]})"
    else:
        if override is not None:
            budget_notes.append(
                f"{BUDGET_ENV}={budget_env[0]!r} ({budget_env[1]}) is not finite; "
                "Claude Code uses it as the budget, which this report does not "
                "model, so the formula is shown instead."
            )
        try:
            budget_chars = context_tokens * bytes_per_token * fraction
        except OverflowError as exc:
            raise ValueError("The computed listing budget must be finite") from exc
        if not _finite_number(budget_chars):
            raise ValueError("The computed listing budget must be finite")
        budget_chars = max(1, math.floor(budget_chars))
    rendered_max_chars = _rendered_max(total_chars, bare_floor_chars, budget_chars)
    for row in plugins:
        remaining_demand, remaining_floor, _ = _listing_totals(
            [skill for skill in skills if skill["plugin"] != row["plugin"]]
        )
        row["saving_chars"] = rendered_max_chars - _rendered_max(
            remaining_demand, remaining_floor, budget_chars
        )
    return {
        "formula_source": FORMULA_SOURCE,
        "project": str(project),
        "sources": sources,
        "skills": sorted(
            skills, key=lambda skill: (-skill["listing_chars"], skill["name"])
        ),
        "plugins": plugins,
        "totals": {
            "skills": len(skills),
            "listing_chars": total_chars,
            "listed": listed,
            "tiers": {
                tier: sum(skill["tier"] == tier for skill in skills) for tier in TIERS
            },
        },
        "budget": {
            "context_tokens": context_tokens,
            "bytes_per_token": bytes_per_token,
            "fraction": fraction,
            "source": budget_source,
            "notes": budget_notes,
            "chars": budget_chars,
            "demand_chars": total_chars,
            "bare_floor_chars": bare_floor_chars,
            "rendered_max_chars": rendered_max_chars,
            "over_budget": total_chars > budget_chars,
            "note": BUDGET_NOTE,
        },
        "question": QUESTION,
        "dispositions": list(DISPOSITIONS),
    }


def _cell(value: Any) -> str:
    return (
        html.escape(str(value), quote=False)
        .replace("|", "\\|")
        .replace("\r\n", "\n")
        .replace("\n", "<br>")
    )


def render_report(report: Mapping[str, Any]) -> str:
    """Render facts without recommendations, preserving run_portfolio's skill order."""
    totals = report["totals"]
    budget = report["budget"]
    tier_counts = ", ".join(f"{tier}: {totals['tiers'][tier]}" for tier in TIERS)
    if budget["source"] == "formula":
        origin = (
            f"= max(1, floor({budget['context_tokens']} context tokens "
            f"× {budget['bytes_per_token']:g} bytes/token × {budget['fraction']:g}))"
        )
    else:
        origin = f"from {budget['source']}"
    lines = [
        "# Skill portfolio",
        "",
        f"Skills: {totals['skills']} | Listed: {totals['listed']} | "
        f"Demand: {totals['listing_chars']} chars | {tier_counts}",
        "",
        f"Budget: {budget['chars']} chars {_cell(origin)}; "
        f"over budget: {'yes' if budget['over_budget'] else 'no'}.",
        *(_cell(note) for note in budget["notes"]),
        f"Rendered max: {budget['rendered_max_chars']} chars; "
        f"bare floor: {budget['bare_floor_chars']} chars.",
        "",
        f"Formula source: {report['formula_source']}.",
        "",
        budget["note"],
        "",
        "## Sources",
        "",
    ]
    for source in report["sources"]:
        note = f" — {'; '.join(source['notes'])}" if source["notes"] else ""
        lines.append(
            f"- {_cell(source['name'])}: **{source['status']}**, {source['count']} entries "
            f"({_cell(source['path'])}){_cell(note)}"
        )
    lines.extend(
        [
            "",
            "## Plugins",
            "",
            "| plugin | enabled | enabled by | visible skills | chars | saves | notes |",
            "| --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for plugin in report["plugins"]:
        enabled = (
            "unknown" if plugin["enabled"] is None else str(plugin["enabled"]).lower()
        )
        cells = (
            plugin["plugin"],
            enabled,
            plugin["enabled_by"] or "unknown",
            plugin["visible_skills"],
            plugin["listing_chars"],
            plugin["saving_chars"],
            "; ".join(plugin["notes"]),
        )
        lines.append("| " + " | ".join(_cell(value) for value in cells) + " |")
    lines.extend(
        [
            "",
            "## Skills",
            "",
            "| skill | source | tier | chars | uses | last used | notes |",
            "| --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for skill in report["skills"]:
        cells = (
            skill["name"],
            skill["source"],
            skill["tier"],
            skill["listing_chars"],
            "unknown" if skill["uses"] is None else skill["uses"],
            skill["last_used"] or "unknown",
            "; ".join(skill["notes"]),
        )
        lines.append("| " + " | ".join(_cell(value) for value in cells) + " |")
    lines.extend(["", f"## {report['question']}", ""])
    lines.extend(f"- {disposition}" for disposition in report["dispositions"])
    return "\n".join(lines) + "\n"
