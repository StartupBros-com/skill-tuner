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
    "Over budget, Claude Code keeps full descriptions for the highest-usage "
    "skills and renders the rest as bare names."
)
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


def listing_chars(name: str, description: str, when_to_use: str, tier: str) -> int:
    """Apply the listing formula measured in Claude Code 2.1.280."""
    if tier == "on":
        return len(name) + 4 + min(len(description) + len(when_to_use), 1536)
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


def skill_tier(
    name: str,
    metadata: Mapping[str, str],
    plugin: str | None,
    overrides: Mapping[str, str],
    override_layers: Mapping[str, str],
) -> tuple[str, str, list[str]]:
    """Resolve frontmatter before overrides; plugin overrides never apply."""
    notes = [PLUGIN_OVERRIDE_NOTE] if plugin and name in overrides else []
    if metadata.get("disable-model-invocation", "").lower() == "true":
        return "user-invocable-only", "frontmatter", notes
    if not plugin and name in overrides:
        return overrides[name], f"override:{override_layers[name]}", notes
    return "on", "default", notes


def _checkout_parts(parts: Sequence[str]) -> list[str]:
    """Drop every `.claude/worktrees/<task>` hop, mapping a worktree copy onto its checkout."""
    kept: list[str] = []
    index = 0
    while index < len(parts):
        if tuple(parts[index : index + 2]) == (".claude", "worktrees") and index + 2 < len(
            parts
        ):
            index += 3
            continue
        kept.append(parts[index])
        index += 1
    return kept


def _project_usage_keys(name: str, project: Path, usage: Mapping[str, Any]) -> list[str]:
    """Keys a project skill's worktree copies and ancestor-directory sessions record.

    Claude Code names a skill found below the session's directory
    `<relative path>:<name>`, so one project skill fragments into keys such as
    `.claude/worktrees/<task>:name` and `SITES/<repo>:name`. Only prefixes that
    contain a `/` are read: a one-segment prefix cannot be told apart from a
    plugin's `plugin:name` key.
    """
    project_parts = _checkout_parts(project.parts)
    keys = []
    for key in usage:
        prefix, _, suffix = key.rpartition(":")
        if suffix != name or "/" not in prefix:
            continue
        relative = _checkout_parts(prefix.split("/"))
        if not relative or project_parts[-len(relative) :] == relative:
            keys.append(key)
    return sorted(keys)


def skill_usage(
    name: str,
    source: str,
    usage: Mapping[str, Any],
    project: Path | None = None,
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
        keys.extend(_project_usage_keys(name, project, usage))
    keys = [key for key in keys if isinstance(usage[key], Mapping)]
    entries = [usage[key] for key in keys]
    if not entries:
        return None, None, []
    counts = [
        entry.get("usageCount")
        for entry in entries
        if isinstance(entry.get("usageCount"), int)
        and not isinstance(entry.get("usageCount"), bool)
    ]
    uses = sum(counts) if counts else None
    last_used = None
    timestamps = [
        entry.get("lastUsedAt")
        for entry in entries
        if isinstance(entry.get("lastUsedAt"), (int, float))
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


def _directories(
    path: Path, source: dict[str, Any], *, root: bool = False
) -> list[Path]:
    """Enumerate one directory level, following links and retaining read failures."""
    try:
        entries = sorted(path.iterdir())
    except FileNotFoundError:
        if root:
            source["status"] = "missing"
        source["notes"].append(f"Missing directory or broken symlink: {path}")
        return []
    except (OSError, ValueError) as exc:
        source["status"] = "unreadable"
        source["notes"].append(f"Cannot list {path}: {exc}")
        return []
    directories: list[Path] = []
    for entry in entries:
        try:
            if stat.S_ISDIR(entry.stat().st_mode):
                directories.append(entry)
        except FileNotFoundError:
            source["notes"].append(f"Broken symlink or missing entry: {entry}")
        except OSError as exc:
            source["status"] = "unreadable"
            source["notes"].append(f"Cannot inspect {entry}: {exc}")
    return directories


def _command_files(
    path: Path, source: dict[str, Any], *, root: bool = True
) -> list[tuple[Path, str, bool]]:
    """Top-level ``*.md`` commands, listed by file stem; subfolders are noted, not read.

    Claude Code puts commands in the same listing as skills, so a command costs
    listing characters exactly like a skill of the same description.
    """
    try:
        entries = sorted(path.iterdir())
    except FileNotFoundError:
        if root:
            source["status"] = "missing"
        source["notes"].append(f"Missing directory: {path}")
        return []
    except (OSError, ValueError) as exc:
        source["status"] = "unreadable"
        source["notes"].append(f"Cannot list {path}: {exc}")
        return []
    files: list[tuple[Path, str, bool]] = []
    for entry in entries:
        try:
            if entry.suffix == ".md" and entry.is_file():
                files.append((entry, entry.stem, False))
            elif entry.is_dir():
                source["notes"].append(f"Subfolder not inventoried: {entry.name}")
        except OSError as exc:
            source["notes"].append(f"Cannot inspect {entry}: {exc}")
    return files


def _skill_files(directories: Sequence[Path]) -> list[tuple[Path, str, bool]]:
    """Each skill directory's SKILL.md, named by frontmatter first, then the directory."""
    return [(directory / "SKILL.md", directory.name, True) for directory in directories]


def _load_settings(
    claude_home: Path, project: Path, sources: list[dict[str, Any]]
) -> tuple[dict[str, str], dict[str, str], dict[str, bool], dict[str, str], float]:
    overrides: dict[str, str] = {}
    override_layers: dict[str, str] = {}
    enabled_plugins: dict[str, bool] = {}
    enabled_layers: dict[str, str] = {}
    fraction = 0.01
    for layer, path in (
        ("user", claude_home / "settings.json"),
        ("project", project / ".claude" / "settings.json"),
        ("local", project / ".claude" / "settings.local.json"),
    ):
        source = _source(f"settings:{layer}", path)
        sources.append(source)
        settings = _read_json(path, source)
        for key, merged, provenance in (
            ("skillOverrides", overrides, override_layers),
            ("enabledPlugins", enabled_plugins, enabled_layers),
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
                    merged[name] = value
                    provenance[name] = layer
                else:
                    source["notes"].append(f"Ignored invalid {key} value for {name}.")
        if "skillListingBudgetFraction" in settings:
            value = settings["skillListingBudgetFraction"]
            if _finite_number(value):
                fraction = value
            else:
                source["notes"].append("Ignored invalid skillListingBudgetFraction.")
    return overrides, override_layers, enabled_plugins, enabled_layers, fraction


def _read_skills(
    files: Sequence[tuple[Path, str, bool]],
    source: dict[str, Any],
    source_name: str,
    overrides: Mapping[str, str],
    override_layers: Mapping[str, str],
    usage: Mapping[str, Any],
    *,
    plugin: str | None = None,
    project: Path | None = None,
) -> list[dict[str, Any]]:
    """Inventory (file, fallback name, frontmatter-name-wins) entries from one source."""
    skills: list[dict[str, Any]] = []
    for path, fallback, frontmatter_name in files:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            if path.is_symlink():
                source["notes"].append(f"Broken symlink: {path}")
            continue
        except (OSError, UnicodeError) as exc:
            source["status"] = "unreadable"
            source["notes"].append(f"Cannot read {path}: {exc}")
            continue
        metadata = parse_frontmatter(text)
        name = (metadata.get("name") if frontmatter_name else None) or fallback
        if source_name == "synced":
            name = f"anthropic-skills:{name}"
        elif plugin:
            name = f"{plugin.split('@', 1)[0]}:{name}"
        description = metadata.get("description", "")
        when_to_use = metadata.get("when_to_use", "")
        tier, reason, notes = skill_tier(
            name, metadata, plugin, overrides, override_layers
        )
        uses, last_used, usage_keys = skill_usage(name, source_name, usage, project)
        if len(usage_keys) > 1:
            notes.append(
                f"uses summed over {len(usage_keys)} usage keys "
                "(worktree copies or ancestor-directory sessions)"
            )
        skills.append(
            {
                "name": name,
                "source": source_name,
                "path": str(path),
                "plugin": plugin,
                "description": description,
                "when_to_use": when_to_use,
                "tier": tier,
                "tier_reason": reason,
                "listing_chars": listing_chars(name, description, when_to_use, tier),
                "uses": uses,
                "last_used": last_used,
                "usage_key": usage_keys[0] if usage_keys else None,
                "usage_keys": usage_keys,
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
    for entry in entries:
        if not isinstance(entry, dict):
            notes.append("Ignored an install entry that is not an object.")
            continue
        if entry.get("scope") == "user" and user_entry is None:
            user_entry = entry
        if entry.get("scope") == "project" and isinstance(
            entry.get("projectPath"), str
        ):
            try:
                if Path(entry["projectPath"]).expanduser().resolve() == project:
                    project_entry = project_entry or entry
            except (OSError, RuntimeError, ValueError) as exc:
                notes.append(f"Cannot resolve plugin projectPath: {exc}")
    return project_entry or user_entry


def run_portfolio(
    *,
    claude_home: Path | None = None,
    claude_json: Path | None = None,
    project: Path | None = None,
    context_tokens: int = 200000,
    bytes_per_token: float = 3,
) -> dict[str, Any]:
    """Read the current portfolio; missing or unreadable sources remain in the report.

    No paths are created or modified. Callers own serialization and any report
    persistence, so the same inventory supports a completely read-only JSON CLI.
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
    overrides, override_layers, enabled, enabled_layers, fraction = _load_settings(
        claude_home, project, sources
    )
    usage_source = _source("usage", claude_json)
    sources.append(usage_source)
    usage = _read_json(claude_json, usage_source).get("skillUsage", {})
    if not isinstance(usage, dict):
        usage_source["notes"].append("Ignored skillUsage: expected an object.")
        usage = {}
    usage_source["count"] = len(usage)

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
                override_layers,
                usage,
                project=project,
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
                override_layers,
                usage,
                project=project,
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
        row = {
            "plugin": key,
            "enabled": enabled.get(key),
            "enabled_by": enabled_layers.get(key),
            "visible_skills": 0,
            "listing_chars": 0,
            "notes": notes,
        }
        plugins.append(row)
        if entry is None:
            notes.append("No user or matching project installation.")
            continue
        install_path = entry.get("installPath")
        if not isinstance(install_path, str) or not install_path:
            notes.append("Install entry has no valid installPath.")
            continue
        try:
            path = Path(install_path).expanduser() / "skills"
        except (OSError, RuntimeError, ValueError) as exc:
            notes.append(f"Cannot resolve installPath: {exc}")
            continue
        source = _source(f"plugin:{key}", path)
        sources.append(source)
        if enabled.get(key) is not True:
            note = (
                "Skills not listed: plugin is disabled."
                if enabled.get(key) is False
                else "Skills not listed: plugin enabled state is unknown."
            )
            notes.append(note)
            source["notes"].append(note)
            # Source existence is useful even when its skills do not participate.
            _directories(path, source, root=True)
            continue
        plugin_skills = _read_skills(
            _skill_files(_directories(path, source, root=True)),
            source,
            "plugin",
            overrides,
            override_layers,
            usage,
            plugin=key,
        )
        commands_path = path.parent / "commands"
        if commands_path.is_dir():
            commands_source = _source(f"plugin-commands:{key}", commands_path)
            sources.append(commands_source)
            plugin_skills += _read_skills(
                _command_files(commands_path, commands_source),
                commands_source,
                "plugin",
                overrides,
                override_layers,
                usage,
                plugin=key,
            )
        row["visible_skills"] = sum(
            skill["tier"] in ("on", "name-only") for skill in plugin_skills
        )
        row["listing_chars"] = sum(skill["listing_chars"] for skill in plugin_skills)
        skills.extend(plugin_skills)

    total_chars = sum(skill["listing_chars"] for skill in skills)
    try:
        budget_chars = context_tokens * bytes_per_token * fraction
    except OverflowError as exc:
        raise ValueError("The computed listing budget must be finite") from exc
    if not _finite_number(budget_chars):
        raise ValueError("The computed listing budget must be finite")
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
            "tiers": {
                tier: sum(skill["tier"] == tier for skill in skills) for tier in TIERS
            },
        },
        "budget": {
            "context_tokens": context_tokens,
            "bytes_per_token": bytes_per_token,
            "fraction": fraction,
            "chars": budget_chars,
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
    """Render inventory facts and the four dispositions, without recommendations."""
    totals = report["totals"]
    budget = report["budget"]
    tier_counts = ", ".join(f"{tier}: {totals['tiers'][tier]}" for tier in TIERS)
    lines = [
        "# Skill portfolio",
        "",
        f"Skills: {totals['skills']} | Listing chars: {totals['listing_chars']} | {tier_counts}",
        "",
        f"Budget: {budget['chars']:g} chars = {budget['context_tokens']} context tokens "
        f"× {budget['bytes_per_token']:g} bytes/token × {budget['fraction']:g}; "
        f"over budget: {'yes' if budget['over_budget'] else 'no'}.",
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
            "| plugin | enabled | enabled by | visible skills | chars | notes |",
            "| --- | --- | --- | ---: | ---: | --- |",
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
    for skill in sorted(
        report["skills"], key=lambda item: (-item["listing_chars"], item["name"])
    ):
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
