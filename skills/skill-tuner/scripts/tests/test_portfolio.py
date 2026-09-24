"""Portfolio inventory acceptance tests, one scenario per issue #57 test bullet.

Every inventory, settings file, plugin install, and output directory lives
inside its test's TemporaryDirectory. No real Claude configuration or model
adapter is used.
"""

from __future__ import annotations

import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import portfolio  # noqa: E402
import tune  # noqa: E402


IGNORED_OVERRIDE_NOTE = (
    "skillOverrides entry ignored: plugin skills are not affected "
    "(Claude Code docs; measured 2.1.280)"
)
TIERS = ("on", "name-only", "user-invocable-only", "off")


def _write_json(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _write_skill(directory: Path, frontmatter: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "SKILL.md"
    path.write_text(f"---\n{frontmatter}\n---\n\nSkill body.\n", encoding="utf-8")
    return path


def _write_command(path: Path, frontmatter: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\nCommand body.\n", encoding="utf-8")
    return path


def _install(path: Path, *, project: Path | None = None) -> dict:
    entry = {
        "scope": "project" if project is not None else "user",
        "installPath": str(path),
        "version": "1.0.0",
    }
    if project is not None:
        entry["projectPath"] = str(project.resolve())
    return entry


def _enable_plugin(base: Path, install: Path) -> None:
    _write_json(
        base / "home" / "plugins" / "installed_plugins.json",
        {"plugins": {"toolkit@market": [_install(install)]}},
    )
    _write_json(
        base / "home" / "settings.json", {"enabledPlugins": {"toolkit@market": True}}
    )


def _run(base: Path, **overrides) -> dict:
    options = {
        "claude_home": base / "home",
        "claude_json": base / "claude.json",
        "project": base / "project",
        "env": {},
    }
    options.update(overrides)
    return portfolio.run_portfolio(**options)


def _skills(report: dict) -> dict:
    return {row["name"]: row for row in report["skills"]}


def _plugins(report: dict) -> dict:
    return {row["plugin"]: row for row in report["plugins"]}


def _sources(report: dict) -> dict:
    return {row["name"]: row for row in report["sources"]}


def _snapshot(base: Path) -> dict:
    """Capture fixture files and directories so read-only calls cannot hide writes."""
    return {
        str(path.relative_to(base)): None if path.is_dir() else path.read_bytes()
        for path in base.rglob("*")
    }


class PortfolioTest(unittest.TestCase):
    def test_every_source_and_frontmatter_name_is_inventoried(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            project = base / "project"
            _write_skill(
                home / "skills" / "user-directory",
                'name: "user-named" # display name\ndescription: "Quoted description."',
            )
            linked = base / "linked-skill"
            _write_skill(
                linked,
                "name: 'user-linked'\ndescription: >\n  Folded first\n  folded second",
            )
            (home / "skills" / "linked").symlink_to(linked, target_is_directory=True)
            (home / "skills" / "broken").symlink_to(
                base / "absent-skill", target_is_directory=True
            )
            _write_skill(
                home / "skills" / "synced", "name: must-not-list\ndescription: decoy"
            )
            _write_skill(
                home / "skills" / "synced" / "account" / "cloud-directory",
                "name: cloud-named\ndescription: |\n  Literal first\n  literal second",
            )
            _write_skill(
                project / ".claude" / "skills" / "project-fallback",
                "description: Project description.",
            )
            plugin_installs = {}
            for plugin in ("toolkit", "disabled", "unknown"):
                install = base / plugin
                _write_skill(
                    install / "skills" / "plugin.directory!",
                    "name: plugin-named\ndescription: Plugin description.",
                )
                plugin_installs[f"{plugin}@market"] = [_install(install)]
            _write_json(
                home / "plugins" / "installed_plugins.json",
                {"plugins": plugin_installs},
            )
            _write_json(
                home / "settings.json",
                {"enabledPlugins": {"toolkit@market": True, "disabled@market": False}},
            )
            _write_json(project / ".claude" / "settings.json", {})
            _write_json(project / ".claude" / "settings.local.json", {})
            _write_json(base / "claude.json", {"skillUsage": {}})

            report = _run(base)
            skills = _skills(report)
            self.assertEqual(
                {name: row["source"] for name, row in skills.items()},
                {
                    "user-directory": "user",
                    "linked": "user",
                    "anthropic-skills:cloud-directory": "synced",
                    "project-fallback": "project",
                    "toolkit:plugin-directory-": "plugin",
                },
            )
            for name, description in (
                ("user-directory", "Quoted description."),
                ("linked", "Folded first folded second"),
                ("anthropic-skills:cloud-directory", "Literal first\nliteral second"),
            ):
                with self.subTest(name=name):
                    self.assertEqual(
                        skills[name]["listing_chars"], len(name) + 4 + len(description)
                    )
            self.assertEqual(
                skills["toolkit:plugin-directory-"]["plugin"], "toolkit@market"
            )
            for name, display_name in (
                ("user-directory", "user-named"),
                ("linked", "user-linked"),
                ("anthropic-skills:cloud-directory", "cloud-named"),
                ("project-fallback", None),
                ("toolkit:plugin-directory-", "plugin-named"),
            ):
                self.assertEqual(skills[name]["display_name"], display_name)
            sources = _sources(report)
            for name, count in (("user", 2), ("synced", 1), ("project", 1)):
                with self.subTest(source=name):
                    self.assertEqual(sources[name]["status"], "ok")
                    self.assertEqual(sources[name]["count"], count)
                    self.assertIn("path", sources[name])
            for name in (
                "settings:user",
                "settings:project",
                "settings:local",
                "usage",
                "plugins",
            ):
                self.assertEqual(sources[name]["status"], "ok")
            self.assertTrue(any("broken" in note for note in sources["user"]["notes"]))
            plugins = _plugins(report)
            self.assertEqual(set(plugins), set(plugin_installs))
            self.assertIs(plugins["disabled@market"]["enabled"], False)
            self.assertIsNone(plugins["unknown@market"]["enabled"])
            self.assertIsNone(plugins["unknown@market"]["enabled_by"])
            for name in ("disabled@market", "unknown@market"):
                self.assertEqual(plugins[name]["visible_skills"], 0)
                self.assertEqual(plugins[name]["listing_chars"], 0)

    def test_runtime_directory_name_drives_overrides_usage_and_display_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_skill(
                base / "home" / "skills" / "directory-name",
                "name: display-name\ndescription: Directory identity.",
            )
            _write_skill(
                base / "project" / ".claude" / "skills" / "project-name",
                "name: project-display\ndescription: Project identity.",
            )
            _write_skill(
                base / "home" / "skills" / "same-name",
                "name: same-name\ndescription: Same identity.",
            )
            _write_json(
                base / "home" / "settings.json",
                {
                    "skillOverrides": {
                        "directory-name": "off",
                        "project-name": "name-only",
                    }
                },
            )
            _write_json(
                base / "claude.json",
                {
                    "skillUsage": {
                        "directory-name": {"usageCount": 7},
                        "display-name": {"usageCount": 999},
                        "project-name": {"usageCount": 3},
                        "project-display": {"usageCount": 999},
                    }
                },
            )

            skills = _skills(_run(base))
            row = skills["directory-name"]
            self.assertEqual(row["name"], "directory-name")
            self.assertEqual(row["tier"], "off")
            self.assertEqual(row["tier_reason"], "override:user")
            self.assertEqual(row["uses"], 7)
            self.assertEqual(row["usage_key"], "directory-name")
            self.assertEqual(row["display_name"], "display-name")
            self.assertEqual(row["listing_chars"], 0)
            project = skills["project-name"]
            self.assertEqual(project["tier"], "name-only")
            self.assertEqual(project["listing_chars"], len("project-name") + 2)
            self.assertEqual(project["uses"], 3)
            self.assertEqual(project["usage_key"], "project-name")
            self.assertEqual(project["display_name"], "project-display")
            self.assertIsNone(skills["same-name"]["display_name"])

    def test_frontmatter_disable_beats_an_on_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            frontmatter = (
                "name: guarded\ndescription: Explicit invocation.\n"
                "disable-model-invocation: true # manual only"
            )
            _write_skill(base / "home" / "skills" / "guarded", frontmatter)
            install = base / "plugin"
            _write_skill(install / "skills" / "guarded", frontmatter)
            _write_json(
                base / "home" / "plugins" / "installed_plugins.json",
                {"plugins": {"toolkit@market": [_install(install)]}},
            )
            _write_json(
                base / "home" / "settings.json",
                {
                    "skillOverrides": {"guarded": "on", "toolkit:guarded": "on"},
                    "enabledPlugins": {"toolkit@market": True},
                },
            )
            _write_json(
                base / "project" / ".claude" / "settings.local.json",
                {"skillOverrides": {"guarded": "on"}},
            )

            report = _run(base)
            for row in report["skills"]:
                with self.subTest(name=row["name"]):
                    self.assertEqual(row["tier"], "user-invocable-only")
                    self.assertEqual(row["tier_reason"], "frontmatter")
                    self.assertEqual(row["listing_chars"], 0)
            self.assertEqual(report["totals"]["skills"], 2)
            self.assertEqual(_plugins(report)["toolkit@market"]["visible_skills"], 0)

    def test_plugin_override_is_ignored_and_keeps_listing_chars(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            install = base / "plugin"
            _write_skill(
                install / "skills" / "task", "name: task\ndescription: Does tasks."
            )
            _write_json(
                base / "home" / "plugins" / "installed_plugins.json",
                {"plugins": {"toolkit@market": [_install(install)]}},
            )
            _write_json(
                base / "home" / "settings.json",
                {"enabledPlugins": {"toolkit@market": True}},
            )
            _write_json(
                base / "project" / ".claude" / "settings.local.json",
                {"skillOverrides": {"toolkit:task": "off"}},
            )

            report = _run(base)
            row = _skills(report)["toolkit:task"]
            self.assertEqual(row["tier"], "on")
            self.assertEqual(row["tier_reason"], "default")
            self.assertIn(IGNORED_OVERRIDE_NOTE, row["notes"])
            self.assertEqual(
                row["listing_chars"], len("toolkit:task") + 4 + len("Does tasks.")
            )
            plugin = _plugins(report)["toolkit@market"]
            self.assertEqual(plugin["visible_skills"], 1)
            self.assertEqual(plugin["listing_chars"], row["listing_chars"])

    def test_settings_layers_merge_keywise_and_control_plugin_enablement(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            settings = base / "project" / ".claude"
            for name in ("local-choice", "project-choice", "user-choice", "retained"):
                _write_skill(
                    home / "skills" / name, f"name: {name}\ndescription: Description."
                )
            plugin_names = (
                "local-on",
                "local-off",
                "project-on",
                "project-off",
                "user-on",
            )
            installs = {}
            for name in plugin_names:
                install = base / name
                _write_skill(install / "skills" / "task", "description: Description.")
                installs[f"{name}@market"] = [_install(install)]
            _write_json(
                home / "plugins" / "installed_plugins.json", {"plugins": installs}
            )
            _write_json(
                home / "settings.json",
                {
                    "skillOverrides": {
                        "local-choice": "on",
                        "project-choice": "on",
                        "user-choice": "name-only",
                        "retained": "off",
                    },
                    "enabledPlugins": {
                        "local-on@market": True,
                        "local-off@market": False,
                        "project-on@market": False,
                        "project-off@market": True,
                        "user-on@market": True,
                    },
                },
            )
            _write_json(
                settings / "settings.json",
                {
                    "skillOverrides": {
                        "local-choice": "name-only",
                        "project-choice": "name-only",
                    },
                    "enabledPlugins": {
                        "local-on@market": False,
                        "local-off@market": True,
                        "project-on@market": True,
                        "project-off@market": False,
                    },
                },
            )
            _write_json(
                settings / "settings.local.json",
                {
                    "skillOverrides": {"local-choice": "off"},
                    "enabledPlugins": {
                        "local-on@market": True,
                        "local-off@market": False,
                    },
                },
            )

            report = _run(base)
            skills = _skills(report)
            for name, tier, layer in (
                ("local-choice", "off", "local"),
                ("project-choice", "name-only", "project"),
                ("user-choice", "name-only", "user"),
                ("retained", "off", "user"),
            ):
                with self.subTest(skill=name):
                    self.assertEqual(skills[name]["tier"], tier)
                    self.assertEqual(skills[name]["tier_reason"], f"override:{layer}")
            plugins = _plugins(report)
            for name, enabled, layer in (
                ("local-on", True, "local"),
                ("local-off", False, "local"),
                ("project-on", True, "project"),
                ("project-off", False, "project"),
                ("user-on", True, "user"),
            ):
                with self.subTest(plugin=name):
                    row = plugins[f"{name}@market"]
                    self.assertIs(row["enabled"], enabled)
                    self.assertEqual(row["enabled_by"], layer)
                    self.assertEqual(f"{name}:task" in skills, enabled)
                    self.assertEqual(row["visible_skills"], int(enabled))
                    self.assertEqual(row["listing_chars"] > 0, enabled)

    def test_project_scope_install_wins_only_for_its_resolved_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = base / "project"
            project.mkdir()
            alias = base / "project-link"
            alias.symlink_to(project, target_is_directory=True)
            unrelated = base / "unrelated-project"
            unrelated.mkdir()
            other = base / "other-project"
            other.mkdir()
            entries = []
            for scope_project, name in (
                (other, "other"),
                (None, "user"),
                (project, "own"),
            ):
                install = base / f"{name}-install"
                _write_skill(install / "skills" / name, f"description: {name} install.")
                entries.append(_install(install, project=scope_project))
            _write_json(
                base / "home" / "plugins" / "installed_plugins.json",
                {"plugins": {"toolkit@market": entries}},
            )
            _write_json(
                base / "home" / "settings.json",
                {"enabledPlugins": {"toolkit@market": True}},
            )

            for selected, expected in (
                (alias, "own"),
                (unrelated, "user"),
                (other, "other"),
            ):
                with self.subTest(project=selected):
                    report = _run(base, project=selected)
                    self.assertEqual(set(_skills(report)), {f"toolkit:{expected}"})
                    self.assertEqual(
                        _plugins(report)["toolkit@market"]["visible_skills"], 1
                    )

    def test_local_plugin_install_precedes_project_and_user_for_matching_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = base / "project"
            project.mkdir()
            alias = base / "project-link"
            alias.symlink_to(project, target_is_directory=True)
            entries = {}
            for scope in ("user", "project", "local", "foreign-local"):
                install = base / scope
                _write_skill(
                    install / "skills" / scope, f"description: {scope} install."
                )
                entry = _install(install, project=alias if scope != "user" else None)
                if scope in ("local", "foreign-local"):
                    entry["scope"] = "local"
                if scope == "foreign-local":
                    entry["projectPath"] = str(base / "other-project")
                entries[scope] = entry
            _write_json(
                base / "home" / "settings.json",
                {"enabledPlugins": {"toolkit@market": True}},
            )
            for selected, expected in (
                (("local",), "local"),
                (("user", "project", "local"), "local"),
                (("foreign-local", "user", "project"), "project"),
                (("foreign-local", "user"), "user"),
                (("foreign-local",), None),
            ):
                with self.subTest(installs=selected):
                    _write_json(
                        base / "home" / "plugins" / "installed_plugins.json",
                        {
                            "plugins": {
                                "toolkit@market": [entries[key] for key in selected]
                            }
                        },
                    )
                    report = _run(base)
                    self.assertEqual(
                        set(_skills(report)),
                        {f"toolkit:{expected}"} if expected else set(),
                    )
                    if expected is None:
                        notes = " ".join(_plugins(report)["toolkit@market"]["notes"])
                        for scope in ("local", "project", "user"):
                            self.assertIn(scope, notes)

    def test_plugin_manifest_adds_skills_commands_and_deduplicates_resolved_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            install = base / "plugin"
            default_skill = _write_skill(
                install / "skills" / "default", "description: Default skill."
            )
            extra_skill = _write_skill(
                install / "extras" / "extra.name",
                "name: ignored\ndescription: Extra skill.",
            )
            root_skill = _write_skill(
                install / "single-root",
                "name: '  toolkit:Root.Name!  '\ndescription: Single root.",
            )
            fallback_skill = _write_skill(
                install / "fallback.root",
                "name: ' toolkit: '\ndescription: Fallback root.",
            )
            (install / "extra-alias").symlink_to(
                install / "extras", target_is_directory=True
            )
            _write_skill(
                install, "name: ignored-install-root\ndescription: Ignored root."
            )
            _write_command(
                install / "commands" / "default-command.md",
                "description: Default command.",
            )
            _write_command(
                install / "command-extras" / "directory-command.md",
                "name: ignored\ndescription: Declared directory.",
            )
            _write_command(
                install / "standalone.md", "name: ignored\ndescription: Declared file."
            )
            _write_json(
                install / ".claude-plugin" / "plugin.json",
                {
                    "skills": [
                        "./skills",
                        "./extras",
                        "./extra-alias",
                        "./single-root",
                        "./fallback.root",
                        ".",
                    ],
                    "commands": ["./commands", "./command-extras", "./standalone.md"],
                },
            )
            _enable_plugin(base, install)

            report = _run(base)
            skills = _skills(report)
            self.assertEqual(
                set(skills),
                {
                    "toolkit:default",
                    "toolkit:extra-name",
                    "toolkit:Root-Name-",
                    "toolkit:fallback-root",
                    "toolkit:default-command",
                    "toolkit:directory-command",
                    "toolkit:standalone",
                },
            )
            self.assertEqual(len(report["skills"]), len(skills))
            for name, path in (
                ("toolkit:default", default_skill),
                ("toolkit:extra-name", extra_skill),
                ("toolkit:Root-Name-", root_skill),
                ("toolkit:fallback-root", fallback_skill),
            ):
                self.assertEqual(Path(skills[name]["path"]), path)
            self.assertEqual(skills["toolkit:extra-name"]["display_name"], "ignored")
            self.assertEqual(
                skills["toolkit:Root-Name-"]["listing_chars"],
                len("toolkit:Root-Name-") + 4 + len("Single root."),
            )
            self.assertIs(_plugins(report)["toolkit@market"]["complete"], True)

    def test_plugin_manifest_accepts_string_paths_and_single_root_name_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            install = base / "plugin"
            _write_skill(install / "single.root", "description: Directory fallback.")
            _write_command(install / "one.md", "description: One command.")
            _write_json(
                install / ".claude-plugin" / "plugin.json",
                {"skills": "./single.root", "commands": "./one.md"},
            )
            _enable_plugin(base, install)
            report = _run(base)
            self.assertEqual(
                set(_skills(report)), {"toolkit:single-root", "toolkit:one"}
            )
            self.assertIs(_plugins(report)["toolkit@market"]["complete"], True)

    def test_plugin_install_root_is_single_skill_only_without_skills_paths(self):
        for manifest, default_directory, expected in (
            (None, False, True),
            ({}, False, True),
            ({"skills": []}, False, False),
            ({}, True, False),
        ):
            with self.subTest(manifest=manifest, default_directory=default_directory):
                with tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    install = base / "plugin"
                    _write_skill(
                        install, "name: 'toolkit:Root.Name'\ndescription: Install root."
                    )
                    if manifest is not None:
                        _write_json(
                            install / ".claude-plugin" / "plugin.json", manifest
                        )
                    if default_directory:
                        (install / "skills").mkdir()
                    _enable_plugin(base, install)
                    report = _run(base)
                    self.assertEqual(
                        set(_skills(report)),
                        {"toolkit:Root-Name"} if expected else set(),
                    )
                    self.assertIs(_plugins(report)["toolkit@market"]["complete"], True)

    def test_default_plugin_skills_path_can_be_a_single_skill_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            install = base / "plugin"
            _write_skill(
                install / "skills",
                "name: ' toolkit:Default.Root '\ndescription: Default root.",
            )
            _enable_plugin(base, install)
            report = _run(base)
            self.assertEqual(set(_skills(report)), {"toolkit:Default-Root"})
            self.assertIs(_plugins(report)["toolkit@market"]["complete"], True)

    def test_declared_commands_install_root_contributes_top_level_markdown_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            install = base / "plugin"
            _write_skill(install, "name: decoy\ndescription: Root command file.")
            _write_command(install / "verify.md", "description: Verify.")
            _write_json(
                install / ".claude-plugin" / "plugin.json",
                {"skills": [], "commands": "."},
            )
            _enable_plugin(base, install)
            report = _run(base)
            self.assertEqual(set(_skills(report)), {"toolkit:SKILL", "toolkit:verify"})
            self.assertIs(_plugins(report)["toolkit@market"]["complete"], True)

    def test_unreadable_plugin_manifest_does_not_guess_install_root_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            install = base / "plugin"
            _write_skill(install, "name: root\ndescription: Unknown loading status.")
            manifest = install / ".claude-plugin" / "plugin.json"
            manifest.parent.mkdir()
            manifest.write_text("{invalid", encoding="utf-8")
            _enable_plugin(base, install)
            report = _run(base)
            self.assertEqual(report["skills"], [])
            self.assertIs(_plugins(report)["toolkit@market"]["complete"], False)

    def test_plugin_declared_paths_cannot_escape_the_install_root(self):
        for field in ("skills", "commands"):
            for symlink in (False, True):
                with self.subTest(field=field, symlink=symlink):
                    with tempfile.TemporaryDirectory() as tmp:
                        base = Path(tmp)
                        install = base / "plugin"
                        _write_skill(
                            install / "skills" / "valid", "description: Valid."
                        )
                        outside = base / "outside"
                        _write_skill(outside / "hidden", "description: Must not load.")
                        _write_command(
                            outside / "hidden.md", "description: Must not load."
                        )
                        declared = "../outside"
                        if symlink:
                            (install / "escape").symlink_to(
                                outside, target_is_directory=True
                            )
                            declared = "./escape"
                        _write_json(
                            install / ".claude-plugin" / "plugin.json",
                            {field: declared},
                        )
                        _enable_plugin(base, install)
                        report = _run(base)
                        self.assertEqual(set(_skills(report)), {"toolkit:valid"})
                        row = _plugins(report)["toolkit@market"]
                        self.assertIs(row["complete"], False)
                        self.assertTrue(
                            any(
                                "outside" in note or "escape" in note
                                for note in row["notes"]
                            ),
                            row["notes"],
                        )

    def test_plugin_missing_or_unsupported_declared_paths_are_incomplete(self):
        for field, declared in (
            ("skills", "./missing"),
            ("skills", {"inline": "Skill content"}),
            ("skills", ["./extras", 5]),
            ("commands", "./missing"),
            ("commands", "./plain.txt"),
            ("commands", {"inline": "Command content"}),
            ("commands", "Inline command content\nwith another line"),
        ):
            with self.subTest(field=field, declared=declared):
                with tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    install = base / "plugin"
                    _write_skill(install / "skills" / "valid", "description: Valid.")
                    (install / "extras").mkdir()
                    (install / "plain.txt").write_text(
                        "Not a command.", encoding="utf-8"
                    )
                    _write_json(
                        install / ".claude-plugin" / "plugin.json", {field: declared}
                    )
                    _enable_plugin(base, install)
                    report = _run(base)
                    self.assertEqual(set(_skills(report)), {"toolkit:valid"})
                    row = _plugins(report)["toolkit@market"]
                    self.assertIs(row["complete"], False)
                    self.assertTrue(row["notes"])
                    if field == "commands" and declared != "./missing":
                        self.assertTrue(
                            any("not inventoried" in note for note in row["notes"]),
                            row["notes"],
                        )

    def test_plugin_unreadable_manifest_or_skill_marks_partial_inventory(self):
        for contents in (b"not JSON", b"[]", b"\xff"):
            with self.subTest(contents=contents):
                with tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    install = base / "plugin"
                    _write_skill(install / "skills" / "valid", "description: Valid.")
                    manifest = install / ".claude-plugin" / "plugin.json"
                    manifest.parent.mkdir()
                    manifest.write_bytes(contents)
                    _enable_plugin(base, install)
                    report = _run(base)
                    self.assertEqual(set(_skills(report)), {"toolkit:valid"})
                    row = _plugins(report)["toolkit@market"]
                    self.assertIs(row["complete"], False)
                    self.assertTrue(
                        any(
                            "manifest" in note.lower() or "plugin.json" in note
                            for note in row["notes"]
                        ),
                        row["notes"],
                    )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            install = base / "plugin"
            unreadable = _write_skill(
                install / "skills" / "broken", "description: Broken."
            )
            unreadable.write_bytes(b"\xff")
            _enable_plugin(base, install)
            report = _run(base)
            self.assertEqual(report["skills"], [])
            row = _plugins(report)["toolkit@market"]
            self.assertIs(row["complete"], False)
            self.assertTrue(
                any("broken" in note for note in row["notes"]), row["notes"]
            )

    def test_usage_fallback_is_synced_only_and_missing_usage_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            for name in ("cloud", "exact-cloud", "unknown-cloud"):
                _write_skill(
                    home / "skills" / "synced" / "account" / name,
                    f"name: {name}\ndescription: Cloud skill.",
                )
            _write_skill(home / "skills" / "unknown-user", "description: User skill.")
            install = base / "plugin"
            for name in ("collision", "exact"):
                _write_skill(
                    install / "skills" / name,
                    f"name: {name}\ndescription: Plugin skill.",
                )
            _write_json(
                home / "plugins" / "installed_plugins.json",
                {"plugins": {"toolkit@market": [_install(install)]}},
            )
            _write_json(
                home / "settings.json", {"enabledPlugins": {"toolkit@market": True}}
            )
            _write_json(
                base / "claude.json",
                {
                    "skillUsage": {
                        "cloud": {"usageCount": 7, "lastUsedAt": 0},
                        "exact-cloud": {"usageCount": 999, "lastUsedAt": 0},
                        "anthropic-skills:exact-cloud": {
                            "usageCount": 0,
                            "lastUsedAt": 1704067200000,
                        },
                        "collision": {"usageCount": 999, "lastUsedAt": 0},
                        "toolkit:exact": {"usageCount": 3, "lastUsedAt": 1704067200000},
                    }
                },
            )

            skills = _skills(_run(base))
            for name, key, uses, expected_date in (
                (
                    "anthropic-skills:cloud",
                    "cloud",
                    7,
                    datetime(1970, 1, 1, tzinfo=timezone.utc),
                ),
                (
                    "anthropic-skills:exact-cloud",
                    "anthropic-skills:exact-cloud",
                    0,
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                ),
                (
                    "toolkit:exact",
                    "toolkit:exact",
                    3,
                    datetime(2024, 1, 1, tzinfo=timezone.utc),
                ),
            ):
                with self.subTest(skill=name):
                    row = skills[name]
                    self.assertEqual(row["uses"], uses)
                    self.assertEqual(row["usage_key"], key)
                    self.assertEqual(
                        datetime.fromisoformat(row["last_used"].replace("Z", "+00:00")),
                        expected_date,
                    )
            for name in (
                "toolkit:collision",
                "unknown-user",
                "anthropic-skills:unknown-cloud",
            ):
                with self.subTest(unknown=name):
                    self.assertIsNone(skills[name]["uses"])
                    self.assertIsNone(skills[name]["last_used"])
                    self.assertIsNone(skills[name]["usage_key"])
            for usage_path in (
                base / "missing.json",
                _write_json(base / "no-usage.json", {}),
            ):
                with self.subTest(usage_path=usage_path):
                    report = _run(base, claude_json=usage_path)
                    for row in report["skills"]:
                        self.assertIsNone(row["uses"])
                        self.assertIsNone(row["last_used"])
                        self.assertIsNone(row["usage_key"])

    def test_listing_char_formula_for_all_tiers_caps_and_when_to_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            fixtures = {
                "full": (
                    "description: abc\nwhen_to_use: 'de'",
                    "on",
                    len("full") + 4 + len("abc - de"),
                ),
                "capped": (
                    f"description: {'a' * 1500}\nwhen_to_use: {'b' * 100}",
                    "on",
                    len("capped") + 4 + 1536,
                ),
                "description-cap": (
                    f"description: {'x' * 1600}",
                    "on",
                    len("description-cap") + 4 + 1536,
                ),
                "literal": (
                    'description: ""\nwhen_to_use: |\n  first\n  second',
                    "on",
                    len("literal") + 4 + len(" - first\nsecond"),
                ),
                "literal-marker": (
                    'description: ""\nwhen_to_use: | # keep literal lines\n  first\n  ---\n  second',
                    "on",
                    len("literal-marker") + 4 + len(" - first\n---\nsecond"),
                ),
                "unicode": ('description: "é🙂"', "on", len("unicode") + 4 + 2),
                "named": (
                    "description: A long description.\nwhen_to_use: More words.",
                    "name-only",
                    len("named") + 2,
                ),
                "manual": ("description: Manual invocation.", "user-invocable-only", 0),
                "off": ("description: Turned off.", "off", 0),
            }
            for name, (frontmatter, _tier, _chars) in fixtures.items():
                _write_skill(
                    base / "home" / "skills" / name, f"name: {name}\n{frontmatter}"
                )
            _write_json(
                base / "home" / "settings.json",
                {
                    "skillOverrides": {
                        name: tier for name, (_, tier, _) in fixtures.items()
                    }
                },
            )

            report = _run(base)
            skills = _skills(report)
            for name, (_, tier, chars) in fixtures.items():
                with self.subTest(skill=name, tier=tier):
                    self.assertEqual(skills[name]["tier"], tier)
                    self.assertEqual(skills[name]["listing_chars"], chars)
            self.assertEqual(report["formula_source"], "Claude Code 2.1.280")
            self.assertEqual(report["totals"]["skills"], len(fixtures))
            listed = sum(
                tier in ("on", "name-only") for _, tier, _ in fixtures.values()
            )
            self.assertEqual(report["totals"]["listed"], listed)
            self.assertEqual(
                report["totals"]["listing_chars"],
                sum(chars for _, _, chars in fixtures.values()) + max(0, listed - 1),
            )
            self.assertEqual(
                report["totals"]["tiers"],
                {
                    tier: sum(item[1] == tier for item in fixtures.values())
                    for tier in TIERS
                },
            )

    def test_listing_description_cap_merges_user_project_and_local_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_skill(
                base / "home" / "skills" / "capped",
                "description: abcdef\nwhen_to_use: ghijkl",
            )
            layers = (
                (base / "home" / "settings.json", 12),
                (base / "project" / ".claude" / "settings.json", 8),
                (base / "project" / ".claude" / "settings.local.json", 4),
            )
            for settings_path, cap in layers:
                with self.subTest(layer=settings_path):
                    _write_json(settings_path, {"skillListingMaxDescChars": cap})
                    report = _run(base)
                    expected = len("capped") + 4 + min(len("abcdef - ghijkl"), cap)
                    self.assertEqual(
                        _skills(report)["capped"]["listing_chars"], expected
                    )
                    self.assertEqual(report["totals"]["listing_chars"], expected)

    def test_invalid_setting_values_keep_previous_layer_and_note_the_source(self):
        cases = (
            ("skillOverrides", "task", ("invalid-tier",), "name-only"),
            ("enabledPlugins", "toolkit@market", ("true",), True),
            (
                "skillListingBudgetFraction",
                None,
                ("0.2", True, 0, -1, 1.5, float("nan")),
                0.25,
            ),
            ("skillListingMaxDescChars", None, (0, -1, 2.5, True), 5),
        )
        for setting, entry, invalid_values, previous in cases:
            for layer_index, layer in enumerate(("user", "project", "local")):
                for invalid in invalid_values:
                    with self.subTest(setting=setting, layer=layer, value=invalid):
                        with tempfile.TemporaryDirectory() as tmp:
                            base = Path(tmp)
                            description = "A description long enough to reach the cap."
                            _write_skill(
                                base / "home" / "skills" / "task",
                                f"description: {description}",
                            )
                            install = base / "plugin"
                            _write_skill(
                                install / "skills" / "task", "description: Plugin."
                            )
                            _write_json(
                                base / "home" / "plugins" / "installed_plugins.json",
                                {"plugins": {"toolkit@market": [_install(install)]}},
                            )
                            paths = (
                                base / "home" / "settings.json",
                                base / "project" / ".claude" / "settings.json",
                                base / "project" / ".claude" / "settings.local.json",
                            )
                            if layer_index:
                                value = {entry: previous} if entry else previous
                                _write_json(paths[layer_index - 1], {setting: value})
                            value = {entry: invalid} if entry else invalid
                            _write_json(paths[layer_index], {setting: value})

                            report = _run(base)
                            notes = _sources(report)[f"settings:{layer}"]["notes"]
                            self.assertTrue(
                                any(
                                    f"Ignored invalid {setting}" in note
                                    for note in notes
                                ),
                                notes,
                            )
                            if setting == "skillOverrides":
                                row = _skills(report)["task"]
                                self.assertEqual(
                                    row["tier"], previous if layer_index else "on"
                                )
                                expected_reason = (
                                    f"override:{('user', 'project')[layer_index - 1]}"
                                    if layer_index
                                    else "default"
                                )
                                self.assertEqual(row["tier_reason"], expected_reason)
                            elif setting == "enabledPlugins":
                                row = _plugins(report)["toolkit@market"]
                                self.assertIs(
                                    row["enabled"], previous if layer_index else None
                                )
                                self.assertEqual(
                                    row["enabled_by"],
                                    ("user", "project")[layer_index - 1]
                                    if layer_index
                                    else None,
                                )
                            elif setting == "skillListingBudgetFraction":
                                self.assertEqual(
                                    report["budget"]["fraction"],
                                    previous if layer_index else 0.01,
                                )
                            else:
                                cap = previous if layer_index else 1536
                                self.assertEqual(
                                    _skills(report)["task"]["listing_chars"],
                                    len("task") + 4 + min(len(description), cap),
                                )

    def test_missing_sources_and_unreadable_json_are_reported_without_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            settings = base / "home" / "settings.json"
            settings.parent.mkdir()
            settings.write_text("{broken JSON", encoding="utf-8")
            local = base / "project" / ".claude" / "settings.local.json"
            local.parent.mkdir(parents=True)
            local.write_bytes(b"\xff")

            report = _run(base)
            self.assertEqual(report["skills"], [])
            self.assertEqual(report["totals"]["listing_chars"], 0)
            sources = _sources(report)
            for name in (
                "user",
                "synced",
                "project",
                "user-command",
                "project-command",
                "plugins",
                "usage",
                "settings:project",
            ):
                with self.subTest(missing=name):
                    self.assertEqual(sources[name]["status"], "missing")
                    self.assertEqual(sources[name]["count"], 0)
            for name in ("user", "project", "user-command", "project-command"):
                self.assertTrue(
                    any(
                        "Missing directory or broken symlink" in note
                        for note in sources[name]["notes"]
                    ),
                    sources[name]["notes"],
                )
            for name in ("settings:user", "settings:local"):
                with self.subTest(unreadable=name):
                    self.assertEqual(sources[name]["status"], "unreadable")
                    self.assertTrue(sources[name]["notes"])
            for path, source in (
                (base / "home" / "plugins" / "installed_plugins.json", "plugins"),
                (base / "claude.json", "usage"),
            ):
                with self.subTest(unreadable=source):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("not JSON", encoding="utf-8")
                    current = _run(base)
                    self.assertEqual(_sources(current)[source]["status"], "unreadable")
                    self.assertTrue(_sources(current)[source]["notes"])

    def test_settings_budget_fraction_and_context_size_control_over_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_skill(
                base / "home" / "skills" / "budgeted",
                "description: A short description.",
            )
            default = _run(base)
            self.assertEqual(default["budget"]["fraction"], 0.01)
            self.assertEqual(default["budget"]["chars"], 200000 * 3 * 0.01)
            _write_json(
                base / "home" / "settings.json", {"skillListingBudgetFraction": 0.02}
            )
            _write_json(
                base / "project" / ".claude" / "settings.json",
                {"skillListingBudgetFraction": 0.03},
            )
            local = base / "project" / ".claude" / "settings.local.json"
            _write_json(local, {"skillListingBudgetFraction": 0.04})

            for context, expected_over in (
                (1000, False),
                (29, True),
                (10, True),
                (0, True),
            ):
                with self.subTest(context=context):
                    report = _run(base, context_tokens=context, bytes_per_token=2.5)
                    budget = report["budget"]
                    self.assertEqual(budget["fraction"], 0.04)
                    self.assertEqual(
                        budget["chars"], max(1, math.floor(context * 2.5 * 0.04))
                    )
                    self.assertIs(budget["over_budget"], expected_over)
                    self.assertIn("usage", budget["note"])
                    self.assertIn("bare names", budget["note"])
            _write_json(local, {"skillListingBudgetFraction": 1})
            exact = _run(
                base,
                context_tokens=default["totals"]["listing_chars"],
                bytes_per_token=1,
            )
            self.assertEqual(exact["budget"]["chars"], exact["totals"]["listing_chars"])
            self.assertIs(exact["budget"]["over_budget"], False)
            with self.assertRaises(ValueError):
                _run(base, bytes_per_token=1e308)

    def test_budget_bounds_and_plugin_savings_account_for_bare_names_and_newlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            install = base / "plugin"
            descriptions = {
                "anchor": "a" * 60,
                "toolkit:first": "b" * 100,
                "toolkit:second": "c" * 80,
            }
            _write_skill(
                base / "home" / "skills" / "anchor",
                f"description: {descriptions['anchor']}",
            )
            for name in ("first", "second"):
                _write_skill(
                    install / "skills" / name,
                    f"description: {descriptions['toolkit:' + name]}",
                )
            _write_skill(
                base / "home" / "skills" / "bare", "description: Not listed in full."
            )
            _write_skill(
                base / "home" / "skills" / "manual",
                "description: Manual.\ndisable-model-invocation: true",
            )
            _enable_plugin(base, install)
            _write_json(
                base / "home" / "settings.json",
                {
                    "enabledPlugins": {"toolkit@market": True},
                    "skillOverrides": {"bare": "name-only"},
                    "skillListingBudgetFraction": 1,
                },
            )
            entry_chars = {
                name: len(name) + 4 + len(description)
                for name, description in descriptions.items()
            }
            entry_chars["bare"] = len("bare") + 2
            demand = sum(entry_chars.values()) + len(entry_chars) - 1
            bare_floor = (
                sum(len(name) + 2 for name in entry_chars) + len(entry_chars) - 1
            )
            remaining_names = ("anchor", "bare")
            remaining_demand = sum(entry_chars[name] for name in remaining_names) + 1
            remaining_floor = sum(len(name) + 2 for name in remaining_names) + 1
            for context in (
                0,
                1,
                bare_floor - 1,
                bare_floor,
                bare_floor + 5,
                demand - 1,
                demand,
                demand + 100,
            ):
                with self.subTest(context=context):
                    report = _run(base, context_tokens=context, bytes_per_token=1)
                    budget_chars = max(1, context)
                    rendered = (
                        demand
                        if demand <= budget_chars
                        else min(demand, max(budget_chars, bare_floor))
                    )
                    without_plugin = (
                        remaining_demand
                        if remaining_demand <= budget_chars
                        else min(remaining_demand, max(budget_chars, remaining_floor))
                    )
                    self.assertEqual(report["totals"]["listed"], len(entry_chars))
                    self.assertEqual(report["totals"]["listing_chars"], demand)
                    budget = report["budget"]
                    self.assertEqual(budget["chars"], budget_chars)
                    self.assertIs(type(budget["chars"]), int)
                    self.assertEqual(budget["demand_chars"], demand)
                    self.assertEqual(budget["bare_floor_chars"], bare_floor)
                    self.assertEqual(budget["rendered_max_chars"], rendered)
                    self.assertIs(budget["over_budget"], demand > budget_chars)
                    plugin = _plugins(report)["toolkit@market"]
                    self.assertEqual(
                        plugin["listing_chars"],
                        entry_chars["toolkit:first"] + entry_chars["toolkit:second"],
                    )
                    self.assertEqual(plugin["saving_chars"], rendered - without_plugin)
                    markdown = portfolio.render_report(report).lower()
                    for label in (
                        "demand",
                        "budget",
                        "over budget",
                        "rendered max",
                        "bare floor",
                        "saves",
                    ):
                        self.assertIn(label, markdown)
                    self.assertIn("at most", budget["note"])
                    self.assertIn("demand", budget["note"])
            empty = _run(base, claude_home=base / "empty", context_tokens=0)
            self.assertEqual(empty["totals"]["listed"], 0)
            self.assertEqual(empty["budget"]["chars"], 1)
            for key in ("demand_chars", "bare_floor_chars", "rendered_max_chars"):
                self.assertEqual(empty["budget"][key], 0)

    def test_plugin_removal_can_save_zero_chars_while_other_descriptions_fill_budget(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            install = base / "plugin"
            _write_skill(
                base / "home" / "skills" / "large", f"description: {'x' * 1000}"
            )
            _write_skill(install / "skills" / "small", "description: Small.")
            _enable_plugin(base, install)
            _write_json(
                base / "home" / "settings.json",
                {
                    "enabledPlugins": {"toolkit@market": True},
                    "skillListingBudgetFraction": 1,
                },
            )
            report = _run(base, context_tokens=100, bytes_per_token=1)
            plugin = _plugins(report)["toolkit@market"]
            self.assertEqual(
                plugin["listing_chars"], len("toolkit:small") + 4 + len("Small.")
            )
            self.assertEqual(plugin["saving_chars"], 0)
            self.assertEqual(report["budget"]["rendered_max_chars"], 100)

    def test_cli_json_is_read_only_and_default_output_writes_both_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for name, description in (
                ("zulu", "same"),
                ("alfa", "same"),
                ("bigger", "Longer description."),
            ):
                _write_skill(
                    base / "home" / "skills" / name,
                    f"name: {name}\ndescription: {description}",
                )
            reports = base / "reports"
            argv = [
                "portfolio",
                "--claude-home",
                str(base / "home"),
                "--claude-json",
                str(base / "claude.json"),
                "--project",
                str(base / "project"),
                "--context-tokens",
                "1000",
                "--bytes-per-token",
                "3",
                "--reports-dir",
                str(reports),
            ]
            runner = base / "runner"
            runner.mkdir()
            for source in SCRIPTS_DIR.glob("*.py"):
                shutil.copy2(source, runner / source.name)
            before = _snapshot(base)
            stdout = io.StringIO()
            with (
                redirect_stdout(stdout),
                mock.patch.object(
                    tune, "call_adapter", side_effect=AssertionError("model call")
                ),
                mock.patch(
                    "socket.create_connection",
                    side_effect=AssertionError("network call"),
                ),
                mock.patch(
                    "subprocess.Popen", side_effect=AssertionError("subprocess call")
                ),
                mock.patch.object(
                    Path, "mkdir", side_effect=AssertionError("directory write")
                ),
                mock.patch.object(
                    Path, "write_text", side_effect=AssertionError("file write")
                ),
                mock.patch.object(
                    Path, "write_bytes", side_effect=AssertionError("file write")
                ),
            ):
                self.assertEqual(tune.main([*argv, "--json"]), 0)
            document = json.loads(stdout.getvalue())
            self.assertEqual(_snapshot(base), before)
            self.assertFalse(reports.exists())
            self.assertEqual(document["budget"]["chars"], 1000 * 3 * 0.01)

            # A fresh interpreter must also avoid creating sibling __pycache__
            # files: the in-process call above already imported portfolio.
            environment = dict(os.environ)
            environment.pop("PYTHONDONTWRITEBYTECODE", None)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            cold = subprocess.run(
                [sys.executable, str(runner / "tune.py"), *argv, "--json"],
                cwd=base,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            self.assertEqual(cold.returncode, 0, cold.stderr)
            self.assertEqual(json.loads(cold.stdout)["skills"], document["skills"])
            self.assertEqual(_snapshot(base), before)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(tune.main(argv), 0)
            markdown_path = Path(stdout.getvalue().strip())
            self.assertEqual(markdown_path.name, "report.md")
            self.assertEqual(markdown_path.parent.parent, reports)
            self.assertRegex(markdown_path.parent.name, r"^portfolio-\d{8}-\d{6}$")
            self.assertEqual(
                {path.name for path in markdown_path.parent.iterdir()},
                {"report.json", "report.md"},
            )
            saved = json.loads(
                markdown_path.with_suffix(".json").read_text(encoding="utf-8")
            )
            self.assertEqual(saved["skills"], document["skills"])
            self.assertEqual(saved["totals"], document["totals"])
            after = _snapshot(base)
            self.assertEqual(
                {
                    path: value
                    for path, value in after.items()
                    if path != "reports" and not path.startswith("reports/")
                },
                before,
            )

            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertTrue(markdown.startswith("#"))
            self.assertIn("Claude Code 2.1.280", markdown)
            self.assertIn("unknown", markdown)
            self.assertIn(
                "skill | source | tier | chars | uses | last used | notes",
                markdown.lower(),
            )
            for source in document["sources"]:
                self.assertIn(source["name"], markdown)
                self.assertIn(source["status"], markdown)
            table_names = [
                line.split("|")[1].strip().strip("`")
                for line in markdown.splitlines()
                if line.startswith("|")
            ]
            self.assertEqual(
                [name for name in table_names if name in _skills(document)],
                ["bigger", "alfa", "zulu"],
            )
            self.assertEqual(
                document["question"], "Should the model start this skill on its own?"
            )
            self.assertIn(document["question"], markdown)
            self.assertEqual(
                document["dispositions"],
                [
                    "keep",
                    "fix the description so it fires",
                    "name-only",
                    "/-only (user-invocable-only)",
                ],
            )
            for disposition in document["dispositions"]:
                self.assertIn(disposition, markdown)

    def test_markdown_escapes_note_pipes_and_newlines_without_extra_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_skill(base / "home" / "skills" / "escaped", "description: Escaped.")
            report = _run(base)
            report["skills"][0]["notes"] = ["First | alternative\r\nSecond line"]
            markdown = portfolio.render_report(report)
            header = next(
                line for line in markdown.splitlines() if line.startswith("| skill |")
            )
            row = next(
                line for line in markdown.splitlines() if line.startswith("| escaped |")
            )
            split_header = re.split(r"(?<!\\)\|", header)
            split_row = re.split(r"(?<!\\)\|", row)
            self.assertEqual(len(split_row), len(split_header))
            notes_index = [cell.strip() for cell in split_header].index("notes")
            self.assertEqual(
                split_row[notes_index].strip(),
                "First \\| alternative<br>Second line",
            )

    def test_dangling_skill_and_command_links_are_noted_not_unreadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            skill_dir = base / "home" / "skills" / "gone"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").symlink_to(base / "missing-skill.md")
            commands = base / "home" / "commands"
            commands.mkdir(parents=True)
            (commands / "gone.md").symlink_to(base / "missing-command.md")
            report = _run(base)
            self.assertEqual(report["skills"], [])
            sources = _sources(report)
            self.assertEqual(sources["user"]["status"], "ok")
            self.assertIn(
                f"Broken symlink: {skill_dir / 'SKILL.md'}", sources["user"]["notes"]
            )
            self.assertEqual(sources["user-command"]["status"], "ok")
            self.assertIn(
                f"Broken symlink or missing entry: {commands / 'gone.md'}",
                sources["user-command"]["notes"],
            )

    def test_render_report_preserves_inventory_skill_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for name in ("short", "longer-name"):
                _write_skill(
                    base / "home" / "skills" / name, "description: Description."
                )
            report = _run(base)
            report["skills"].reverse()
            rendered = portfolio.render_report(report)
            names = [
                line.split("|")[1].strip()
                for line in rendered.splitlines()
                if line.startswith("| short |") or line.startswith("| longer-name |")
            ]
            self.assertEqual(names, [row["name"] for row in report["skills"]])

    def test_cli_report_directory_collision_retries_without_touching_existing_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_skill(base / "home" / "skills" / "task", "description: Task.")
            reports = base / "reports"
            first = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
            second = datetime(2026, 9, 23, 12, 0, 1, tzinfo=timezone.utc)
            collision = reports / f"portfolio-{first.strftime('%Y%m%d-%H%M%S')}"
            collision.mkdir(parents=True)
            (collision / "report.json").write_text(
                "Existing JSON report.\n", encoding="utf-8"
            )
            (collision / "report.md").write_text(
                "Existing Markdown report.\n", encoding="utf-8"
            )
            before = _snapshot(collision)
            stdout = io.StringIO()
            with (
                redirect_stdout(stdout),
                mock.patch("datetime.datetime") as clock,
                mock.patch.object(tune.time, "sleep") as sleep,
            ):
                clock.now.side_effect = [first, second]
                result = tune.main(
                    [
                        "portfolio",
                        "--claude-home",
                        str(base / "home"),
                        "--claude-json",
                        str(base / "claude.json"),
                        "--project",
                        str(base / "project"),
                        "--reports-dir",
                        str(reports),
                    ]
                )
            self.assertEqual(result, 0)
            sleep.assert_called_once_with(0.05)
            self.assertEqual(clock.now.call_count, 2)
            self.assertEqual(_snapshot(collision), before)
            output = Path(stdout.getvalue().strip())
            self.assertEqual(
                output.parent, reports / f"portfolio-{second.strftime('%Y%m%d-%H%M%S')}"
            )
            self.assertEqual(
                {path.name for path in output.parent.iterdir()},
                {"report.json", "report.md"},
            )
            saved = json.loads(output.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(set(_skills(saved)), {"task"})
            self.assertEqual(
                output.read_text(encoding="utf-8"), portfolio.render_report(saved)
            )

    def test_commands_share_the_listing_and_are_named_by_file_stem(self):
        # Claude Code lists commands beside skills (measured: ~/.claude/commands and
        # plugin commands/ entries appear in a 2.1.280 session's skill_listing).
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            project = base / "project"

            def command(path: Path, frontmatter: str) -> None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"---\n{frontmatter}\n---\n\nBody.\n", encoding="utf-8")

            command(home / "commands" / "triage.md", "description: Triage denials.")
            (home / "commands" / "nested").mkdir()
            command(
                project / ".claude" / "commands" / "ship.md", "description: Ship it."
            )
            for plugin in ("tools", "off"):
                install = base / plugin
                (install / "skills").mkdir(parents=True)
                # A frontmatter `name` must not rename a command: the file stem is its name.
                command(
                    install / "commands" / "rescue.md",
                    "name: decoy\ndescription: Rescue.",
                )
                command(
                    install / "commands" / "review.md",
                    "description: Review.\ndisable-model-invocation: true",
                )
            _write_json(
                home / "plugins" / "installed_plugins.json",
                {
                    "plugins": {
                        "tools@m": [_install(base / "tools")],
                        "off@m": [_install(base / "off")],
                    }
                },
            )
            _write_json(
                home / "settings.json",
                {"enabledPlugins": {"tools@m": True, "off@m": False}},
            )
            _write_json(
                base / "claude.json",
                {"skillUsage": {"tools:rescue": {"usageCount": 4}}},
            )

            report = _run(base)
            skills = _skills(report)

            self.assertEqual(skills["triage"]["source"], "user-command")
            self.assertEqual(
                skills["triage"]["listing_chars"],
                len("triage") + 4 + len("Triage denials."),
            )
            self.assertEqual(skills["ship"]["source"], "project-command")
            self.assertIn("tools:rescue", skills)
            self.assertNotIn("tools:decoy", skills)
            self.assertEqual(skills["tools:rescue"]["uses"], 4)
            self.assertEqual(skills["tools:review"]["tier"], "user-invocable-only")
            self.assertEqual(skills["tools:review"]["listing_chars"], 0)
            self.assertNotIn("off:rescue", skills)
            self.assertEqual(_plugins(report)["tools@m"]["visible_skills"], 1)
            sources = _sources(report)
            self.assertIn(
                "Subfolder not inventoried: nested", sources["user-command"]["notes"]
            )
            self.assertEqual(sources["plugin-commands:tools@m"]["count"], 2)

    def test_project_worktree_usage_does_not_leak_to_another_repository(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            first = base / "repository-a"
            second = base / "repository-b"
            worktree = first / ".claude" / "worktrees" / "other-task"
            for project in (first, second):
                _write_skill(
                    project / ".claude" / "skills" / "verify", "description: Verify."
                )
            _write_json(
                base / "claude.json",
                {
                    "projects": {str(first): {}, str(second): {}, str(worktree): {}},
                    "skillUsage": {
                        "verify": {"usageCount": 2},
                        ".claude/worktrees/other-task:verify": {"usageCount": 6},
                    },
                },
            )
            first_row = _skills(_run(base, project=first))["verify"]
            second_row = _skills(_run(base, project=second))["verify"]
            self.assertEqual(first_row["uses"], 8)
            self.assertEqual(second_row["uses"], 2)
            self.assertEqual(second_row["usage_keys"], ["verify"])
            self.assertFalse(
                any("cannot be traced" in note for note in second_row["notes"])
            )
            for row in (first_row, second_row):
                self.assertEqual(row["shared_key_projects"], 1)
                self.assertIn(
                    "usage key verify is shared with 1 other project(s) that define it; uses may include theirs",
                    row["notes"],
                )

    def test_untraceable_worktree_usage_is_not_counted_and_reports_its_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_skill(
                base / "project" / ".claude" / "skills" / "verify",
                "description: Verify.",
            )
            _write_command(
                base / "project" / ".claude" / "commands" / "ship.md",
                "description: Ship.",
            )
            _write_json(
                base / "claude.json",
                {
                    "skillUsage": {
                        "verify": {"usageCount": 3},
                        ".claude/worktrees/missing-a:verify": {"usageCount": 5},
                        ".claude/worktrees/missing-b:verify": {"usageCount": 7},
                        ".claude/worktrees/missing-a:ship": {"usageCount": 4},
                    }
                },
            )
            skills = _skills(_run(base))
            self.assertEqual(skills["verify"]["uses"], 3)
            self.assertEqual(skills["verify"]["usage_keys"], ["verify"])
            self.assertIn(
                "12 uses under 2 worktree or ancestor-directory key(s) that cannot be traced to a project are not counted",
                skills["verify"]["notes"],
            )
            self.assertIsNone(skills["ship"]["uses"])
            self.assertEqual(skills["ship"]["usage_keys"], [])
            self.assertIn(
                "4 uses under 1 worktree or ancestor-directory key(s) that cannot be traced to a project are not counted",
                skills["ship"]["notes"],
            )

    def test_invalid_attributed_usage_count_does_not_report_a_partial_sum(self):
        for entry in (
            {"usageCount": "7"},
            {"usageCount": True},
            {"usageCount": -1},
            {},
        ):
            with self.subTest(entry=entry):
                with tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    project = base / "project"
                    _write_skill(
                        project / ".claude" / "skills" / "verify",
                        "description: Verify.",
                    )
                    _write_json(
                        base / "claude.json",
                        {
                            "projects": {
                                str(project / ".claude" / "worktrees" / "own"): {}
                            },
                            "skillUsage": {
                                "verify": {"usageCount": 5},
                                ".claude/worktrees/own:verify": entry,
                            },
                        },
                    )
                    row = _skills(_run(base))["verify"]
                    self.assertIsNone(row["uses"])
                    self.assertIn(
                        "Usage count is unknown for one or more attributed keys; uses are unknown.",
                        row["notes"],
                    )

    def test_existing_worktree_path_is_evidence_without_a_known_project_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            checkout = base / "project"
            nested = (
                checkout
                / ".claude"
                / "worktrees"
                / "outer"
                / ".claude"
                / "worktrees"
                / "inner"
            )
            nested.mkdir(parents=True)
            _write_skill(
                checkout / ".claude" / "skills" / "verify", "description: Verify."
            )
            _write_json(
                base / "claude.json",
                {
                    "skillUsage": {
                        ".claude/worktrees/outer:verify": {"usageCount": 2},
                        ".claude/worktrees/outer/.claude/worktrees/inner:verify": {
                            "usageCount": 3
                        },
                    }
                },
            )
            row = _skills(_run(base))["verify"]
            self.assertEqual(row["uses"], 5)
            self.assertEqual(len(row["usage_keys"]), 2)
            self.assertFalse(any("cannot be traced" in note for note in row["notes"]))

    def test_shared_usage_key_projects_are_counted_for_user_project_skills_and_commands(
        self,
    ):
        for source in ("user", "project", "user-command", "project-command"):
            with self.subTest(source=source):
                with tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    checkout = base / "project"
                    skill_root = (
                        base / "home"
                        if source.startswith("user")
                        else checkout / ".claude"
                    )
                    if source.endswith("command"):
                        _write_command(
                            skill_root / "commands" / "verify.md",
                            "description: Verify.",
                        )
                    else:
                        _write_skill(
                            skill_root / "skills" / "verify", "description: Verify."
                        )
                    skill_project = base / "other-skill"
                    command_project = base / "other-command"
                    descendant = checkout / ".claude" / "worktrees" / "own-task"
                    # Another repository's worktree is the same other project.
                    other_worktree = skill_project / ".claude" / "worktrees" / "task"
                    for project in (skill_project, descendant, other_worktree):
                        _write_skill(
                            project / ".claude" / "skills" / "verify",
                            "description: Shared.",
                        )
                    _write_command(
                        command_project / ".claude" / "commands" / "verify.md",
                        "description: Shared command.",
                    )
                    # A project defining both contributes one, and descendants of
                    # this checkout do not become "other projects".
                    _write_command(
                        skill_project / ".claude" / "commands" / "verify.md",
                        "description: Also shared.",
                    )
                    _write_json(
                        base / "claude.json",
                        {
                            "projects": {
                                str(project): {}
                                for project in (
                                    checkout,
                                    descendant,
                                    skill_project,
                                    other_worktree,
                                    command_project,
                                    base / "unrelated",
                                )
                            },
                            "skillUsage": {"verify": {"usageCount": 11}},
                        },
                    )
                    row = _skills(_run(base))["verify"]
                    self.assertEqual(row["source"], source)
                    self.assertEqual(row["uses"], 11)
                    self.assertEqual(row["shared_key_projects"], 2)
                    self.assertIn(
                        "usage key verify is shared with 2 other project(s) that define it; uses may include theirs",
                        row["notes"],
                    )
                    _write_json(
                        base / "claude.json",
                        {"skillUsage": {"verify": {"usageCount": 11}}},
                    )
                    unshared = _skills(_run(base))["verify"]
                    self.assertEqual(unshared["shared_key_projects"], 0)
                    self.assertFalse(
                        any("is shared with" in note for note in unshared["notes"])
                    )

    def test_project_usage_sums_worktree_and_ancestor_keys_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            checkout = base / "repo"
            worktree = checkout / ".claude" / "worktrees" / "wt"
            for root in (checkout, worktree):
                _write_skill(
                    root / ".claude" / "skills" / "verify", "description: Verify."
                )
                (root / ".claude" / "commands").mkdir(parents=True)
                (root / ".claude" / "commands" / "ship.md").write_text(
                    "---\ndescription: Ship.\n---\n", encoding="utf-8"
                )
            _write_skill(base / "home" / "skills" / "lint", "description: Lint.")
            summed = {
                "verify": {"usageCount": 50, "lastUsedAt": 1704067200000},
                ".claude/worktrees/task-a:verify": {
                    "usageCount": 1,
                    "lastUsedAt": 1706745600000,
                },
                ".claude/worktrees/task-b/repo:verify": {"usageCount": 2},
                f"{base.name}/repo:verify": {"usageCount": 3},
            }
            ignored = {
                # One segment reads as a plugin key; the others are other directories.
                "repo:verify": {"usageCount": 100},
                "other/.claude/worktrees/task-c:verify": {"usageCount": 100},
                ".claude/worktrees/task-d/apps/web:verify": {"usageCount": 100},
                ".claude/worktrees/task-a:lint": {"usageCount": 100},
            }
            _write_json(
                base / "claude.json",
                {
                    # The session directories that recorded the ancestor keys.
                    "projects": {
                        str(checkout / ".claude" / "worktrees" / "task-a"): {},
                        str(base): {},
                        str(base.parent): {},
                    },
                    "skillUsage": {
                        **summed,
                        **ignored,
                        ".claude/worktrees/task-a:ship": {"usageCount": 4},
                    },
                },
            )

            for project in (checkout, worktree):
                with self.subTest(project=project):
                    skills = _skills(_run(base, project=project))
                    verify = skills["verify"]
                    self.assertEqual(verify["uses"], 56)
                    self.assertEqual(verify["usage_key"], "verify")
                    self.assertEqual(set(verify["usage_keys"]), set(summed))
                    self.assertEqual(
                        datetime.fromisoformat(verify["last_used"]),
                        datetime(2024, 2, 1, tzinfo=timezone.utc),
                    )
                    self.assertIn(
                        "uses summed over 4 usage keys "
                        "(worktree copies or ancestor-directory sessions)",
                        verify["notes"],
                    )
                    self.assertEqual(skills["ship"]["uses"], 4)
                    self.assertEqual(
                        skills["ship"]["usage_key"], ".claude/worktrees/task-a:ship"
                    )
                    self.assertIsNone(skills["lint"]["uses"])

    def test_ancestor_key_counts_only_where_its_session_directory_is_known(self):
        untraced = (
            "999 uses under 1 worktree or ancestor-directory key(s) that cannot "
            "be traced to a project are not counted"
        )
        shared = (
            "usage key SITES/backend:verify may also hold uses from 1 other "
            "project(s) at the same relative path"
        )
        for known, expected in (
            # Only workA's session could have recorded SITES/backend:verify.
            (("work-a",), {"work-a": (999, []), "work-b": (None, [])}),
            (
                ("work-a", "work-b"),
                {"work-a": (999, [shared]), "work-b": (999, [shared])},
            ),
            ((), {"work-a": (None, [untraced]), "work-b": (None, [untraced])}),
        ):
            with self.subTest(known=known):
                with tempfile.TemporaryDirectory() as tmp:
                    base = Path(tmp)
                    for root in ("work-a", "work-b"):
                        _write_skill(
                            base
                            / root
                            / "SITES"
                            / "backend"
                            / ".claude"
                            / "skills"
                            / "verify",
                            "description: Verify.",
                        )
                    _write_json(
                        base / "claude.json",
                        {
                            "projects": {str(base / root): {} for root in known},
                            "skillUsage": {"SITES/backend:verify": {"usageCount": 999}},
                        },
                    )
                    for root, (uses, notes) in expected.items():
                        row = _skills(
                            _run(base, project=base / root / "SITES" / "backend")
                        )["verify"]
                        self.assertEqual(row["uses"], uses)
                        for note in (shared, untraced):
                            self.assertEqual(note in row["notes"], note in notes)

    def test_worktree_key_two_checkouts_could_record_is_counted_and_noted(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for root in ("first", "second"):
                for directory in (
                    base / root,
                    base / root / ".claude" / "worktrees" / "fix",
                ):
                    _write_skill(
                        directory / ".claude" / "skills" / "verify",
                        "description: Verify.",
                    )
            _write_json(
                base / "claude.json",
                {
                    "projects": {str(base / "first"): {}, str(base / "second"): {}},
                    "skillUsage": {".claude/worktrees/fix:verify": {"usageCount": 6}},
                },
            )
            for root in ("first", "second"):
                row = _skills(_run(base, project=base / root))["verify"]
                self.assertEqual(row["uses"], 6)
                self.assertIn(
                    "usage key .claude/worktrees/fix:verify may also hold uses "
                    "from 1 other project(s) at the same relative path",
                    row["notes"],
                )

    def test_env_budget_reads_the_value_as_claude_code_does(self):
        for raw, expected in (
            ("30000", 30000),
            (" 30000 ", 30000),
            ("30,000", 30000),
            ("30_000", 30000),
            ("1e3", 1000),
            ("0x10", 16),
            ("5000.7", 5000.7),
            ("-5", -5),
            (5000, 5000),
            ("Infinity", math.inf),
            ("", None),
            ("0", None),
            ("-0", None),
            ("abc", None),
            ("-0x10", None),
            ("30,00", None),
            ("infinity", None),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(portfolio.env_budget(raw), expected)

    def test_budget_env_replaces_the_formula_in_claude_codes_precedence(self):
        key = portfolio.BUDGET_ENV
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _write_skill(base / "home" / "skills" / "long", "description: " + "x" * 300)
            settings = {
                "user": base / "home" / "settings.json",
                "project": base / "project" / ".claude" / "settings.json",
                "local": base / "project" / ".claude" / "settings.local.json",
            }
            cases = (
                ({}, {}, {}, None, 6000, "formula"),
                ({}, {}, {key: "40"}, None, 40, f"{key} (environment)"),
                ({}, {key: "50"}, {key: "40"}, None, 50, f"{key} (~/.claude.json env)"),
                (
                    {"user": "60"},
                    {key: "50"},
                    {key: "40"},
                    None,
                    60,
                    f"{key} (user settings env)",
                ),
                (
                    {"user": "60", "project": "70"},
                    {},
                    {},
                    None,
                    70,
                    f"{key} (project settings env)",
                ),
                (
                    {"project": "70", "local": "80.9"},
                    {},
                    {},
                    None,
                    80,
                    f"{key} (local settings env)",
                ),
                ({"local": "0"}, {}, {key: "40"}, None, 6000, "formula"),
                ({}, {}, {key: "Infinity"}, "is not finite", 6000, "formula"),
            )
            for layers, global_env, environ, note, chars, source in cases:
                with self.subTest(
                    layers=layers, global_env=global_env, environ=environ
                ):
                    for layer, path in settings.items():
                        _write_json(
                            path,
                            {"env": {key: layers[layer]}} if layer in layers else {},
                        )
                    _write_json(base / "claude.json", {"env": global_env})
                    report = _run(base, env=environ)
                    budget = report["budget"]
                    self.assertEqual(
                        (budget["chars"], budget["source"]), (chars, source)
                    )
                    # One entry: len("long") + 4 + 300 description chars.
                    self.assertEqual(budget["demand_chars"], 308)
                    self.assertEqual(budget["over_budget"], 308 > chars)
                    if note:
                        self.assertTrue(any(note in text for text in budget["notes"]))
                    else:
                        self.assertEqual(budget["notes"], [])
                    markdown = portfolio.render_report(report)
                    if source == "formula":
                        self.assertIn(
                            f"Budget: {chars} chars = max(1, floor(", markdown
                        )
                    else:
                        self.assertIn(f"Budget: {chars} chars from {source};", markdown)


if __name__ == "__main__":
    unittest.main()
