"""Portfolio inventory acceptance tests, one scenario per issue #57 test bullet.

Every inventory, settings file, plugin install, and output directory lives
inside its test's TemporaryDirectory. No real Claude configuration or model
adapter is used.
"""

from __future__ import annotations

import io
import json
import os
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


def _install(path: Path, *, project: Path | None = None) -> dict:
    entry = {
        "scope": "project" if project is not None else "user",
        "installPath": str(path),
        "version": "1.0.0",
    }
    if project is not None:
        entry["projectPath"] = str(project.resolve())
    return entry


def _run(base: Path, **overrides) -> dict:
    options = {
        "claude_home": base / "home",
        "claude_json": base / "claude.json",
        "project": base / "project",
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
                    install / "skills" / "plugin-directory",
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
                    "user-named": "user",
                    "user-linked": "user",
                    "anthropic-skills:cloud-named": "synced",
                    "project-fallback": "project",
                    "toolkit:plugin-named": "plugin",
                },
            )
            for name, description in (
                ("user-named", "Quoted description."),
                ("user-linked", "Folded first folded second"),
                ("anthropic-skills:cloud-named", "Literal first\nliteral second"),
            ):
                with self.subTest(name=name):
                    self.assertEqual(
                        skills[name]["listing_chars"], len(name) + 4 + len(description)
                    )
            self.assertEqual(skills["toolkit:plugin-named"]["plugin"], "toolkit@market")
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
                    len("full") + 4 + 5,
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
                    len("literal") + 4 + len("first\nsecond"),
                ),
                "literal-marker": (
                    'description: ""\nwhen_to_use: | # keep literal lines\n  first\n  ---\n  second',
                    "on",
                    len("literal-marker") + 4 + len("first\n---\nsecond"),
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
            self.assertEqual(
                report["totals"]["listing_chars"],
                sum(chars for _, _, chars in fixtures.values()),
            )
            self.assertEqual(
                report["totals"]["tiers"],
                {
                    tier: sum(item[1] == tier for item in fixtures.values())
                    for tier in TIERS
                },
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
                "plugins",
                "usage",
                "settings:project",
            ):
                with self.subTest(missing=name):
                    self.assertEqual(sources[name]["status"], "missing")
                    self.assertEqual(sources[name]["count"], 0)
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

            for context, expected_over in ((1000, False), (10, True), (0, True)):
                with self.subTest(context=context):
                    report = _run(base, context_tokens=context, bytes_per_token=2.5)
                    budget = report["budget"]
                    self.assertEqual(budget["fraction"], 0.04)
                    self.assertEqual(budget["chars"], context * 2.5 * 0.04)
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
            command(project / ".claude" / "commands" / "ship.md", "description: Ship it.")
            for plugin in ("tools", "off"):
                install = base / plugin
                (install / "skills").mkdir(parents=True)
                # A frontmatter `name` must not rename a command: the file stem is its name.
                command(install / "commands" / "rescue.md", "name: decoy\ndescription: Rescue.")
                command(
                    install / "commands" / "review.md",
                    "description: Review.\ndisable-model-invocation: true",
                )
            _write_json(
                home / "plugins" / "installed_plugins.json",
                {"plugins": {"tools@m": [_install(base / "tools")], "off@m": [_install(base / "off")]}},
            )
            _write_json(home / "settings.json", {"enabledPlugins": {"tools@m": True, "off@m": False}})
            _write_json(base / "claude.json", {"skillUsage": {"tools:rescue": {"usageCount": 4}}})

            report = _run(base)
            skills = _skills(report)

            self.assertEqual(skills["triage"]["source"], "user-command")
            self.assertEqual(skills["triage"]["listing_chars"], len("triage") + 4 + len("Triage denials."))
            self.assertEqual(skills["ship"]["source"], "project-command")
            self.assertIn("tools:rescue", skills)
            self.assertNotIn("tools:decoy", skills)
            self.assertEqual(skills["tools:rescue"]["uses"], 4)
            self.assertEqual(skills["tools:review"]["tier"], "user-invocable-only")
            self.assertEqual(skills["tools:review"]["listing_chars"], 0)
            self.assertNotIn("off:rescue", skills)
            self.assertEqual(_plugins(report)["tools@m"]["visible_skills"], 1)
            sources = _sources(report)
            self.assertIn("Subfolder not inventoried: nested", sources["user-command"]["notes"])
            self.assertEqual(sources["plugin-commands:tools@m"]["count"], 2)


if __name__ == "__main__":
    unittest.main()
