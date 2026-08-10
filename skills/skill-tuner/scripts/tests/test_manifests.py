"""Packaging invariants for the dual-format plugin layout.

The repo ships two manifests for the same plugin: `.claude-plugin/plugin.json`
(Claude Code) and root `plugin.json` (Agent Plugins v1.0.0, agent-plugins.org).
Version bumps are manual, so these tests are the only thing keeping the two
manifests and the VERSION file from drifting apart.
"""

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

# §5.2 of the Agent Plugins spec: the manifest schema is closed.
AGENT_PLUGINS_FIELDS = {
    "$schema", "name", "version", "description", "author",
    "homepage", "repository", "license", "keywords", "extensions",
}
AGENT_PLUGINS_SCHEMA_URL = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
NAME_PATTERN = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")


def _load(relpath):
    return json.loads((REPO_ROOT / relpath).read_text())


def _frontmatter_name(skill_md):
    lines = skill_md.read_text().splitlines()
    assert lines[0] == "---", f"{skill_md} has no frontmatter"
    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


class TestManifestSync(unittest.TestCase):
    def test_versions_agree(self):
        version = (REPO_ROOT / "VERSION").read_text().strip()
        claude = _load(".claude-plugin/plugin.json")
        spec = _load("plugin.json")
        self.assertEqual(claude["version"], version)
        self.assertEqual(spec["version"], version)

    def test_shared_metadata_agrees(self):
        claude = _load(".claude-plugin/plugin.json")
        spec = _load("plugin.json")
        for field in ("name", "description", "author", "homepage",
                      "repository", "license", "keywords"):
            self.assertEqual(spec[field], claude[field], f"manifests disagree on {field}")


class TestAgentPluginsConformance(unittest.TestCase):
    def test_root_manifest_is_closed_schema(self):
        spec = _load("plugin.json")
        self.assertEqual(spec["$schema"], AGENT_PLUGINS_SCHEMA_URL)
        unknown = set(spec) - AGENT_PLUGINS_FIELDS
        self.assertFalse(unknown, f"fields outside the closed schema: {unknown}")
        self.assertRegex(spec["name"], NAME_PATTERN)

    def test_author_fields(self):
        author = _load("plugin.json").get("author", {})
        self.assertFalse(set(author) - {"name", "email", "url"})


class TestSkillLayout(unittest.TestCase):
    def test_skill_names_match_directories(self):
        # agentskills.io: frontmatter `name` must match the parent directory.
        skills_dir = REPO_ROOT / "skills"
        found = list(skills_dir.glob("*/SKILL.md"))
        self.assertGreaterEqual(len(found), 2, "expected the doctrine and tune skills")
        for skill_md in found:
            name = _frontmatter_name(skill_md)
            if name is not None:
                self.assertEqual(name, skill_md.parent.name)

    def test_no_legacy_commands_dir(self):
        # The tune runbook lives at skills/tune/SKILL.md so non-Claude clients
        # surface it; a resurrected commands/ would fork that single source.
        self.assertFalse((REPO_ROOT / "commands").exists())


if __name__ == "__main__":
    unittest.main()
