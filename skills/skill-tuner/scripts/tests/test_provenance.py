"""Tests for run provenance (Unit 9.1).

provenance.py is the single input chokepoint: every byte an eval feeds to a
model is read through ``resolve_input``, which returns the content *and* the
record of where it came from. That pairing is the point -- a reader that does
not record cannot be used to smuggle an unrecorded input into a run, the same
way tune.call_adapter is the single output chokepoint no eval path can dodge.

These tests drive real temporary git repositories rather than mocking git.
The behaviour under test *is* the git interaction -- resolving a pinned ref,
noticing a dirty worktree, degrading outside a repo -- and a mock would only
assert that the mock was called.

Scenarios:
1. Worktree resolution returns content, a stable sha256, and git identity.
2. A pinned ref returns the *committed* content, not the working tree's.
3. The dirty flag distinguishes an edited worktree from a clean one.
4. A pin that cannot be resolved fails loudly instead of falling back.
5. Outside a repo, unpinned resolution degrades; pinned resolution refuses.
6. build_manifest records inputs, model pin, CLI version, and timestamps.
7. verify_manifest detects changed, missing, and unchanged inputs, and
   notices a CLI-version change between the run and now.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import provenance  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


class WorktreeResolutionTest(unittest.TestCase):
    def test_returns_content_hash_and_git_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)
            target = repo / "doc.md"
            target.write_text("hello\n", encoding="utf-8")
            commit = _commit_all(repo, "add doc")

            resolved = provenance.resolve_input(target, role="target")

            self.assertEqual("hello\n", resolved.text)
            self.assertEqual(
                "sha256:" + hashlib.sha256(b"hello\n").hexdigest(), resolved.sha256
            )
            self.assertEqual("worktree", resolved.source)
            self.assertEqual(commit, resolved.git_commit)
            self.assertEqual("doc.md", resolved.git_path)
            self.assertFalse(resolved.dirty)

    def test_to_dict_omits_the_content_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)
            target = repo / "doc.md"
            target.write_text("hello\n", encoding="utf-8")
            _commit_all(repo, "add doc")

            payload = provenance.resolve_input(target, role="target").to_dict()

            self.assertNotIn("text", payload)
            self.assertEqual("target", payload["role"])
            self.assertIn("sha256", payload)


class PinnedResolutionTest(unittest.TestCase):
    def test_pin_returns_committed_content_not_the_working_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)
            target = repo / "doc.md"
            target.write_text("committed\n", encoding="utf-8")
            commit = _commit_all(repo, "add doc")
            target.write_text("uncommitted edit\n", encoding="utf-8")

            pinned = provenance.resolve_input(target, role="target", pin="HEAD")

            self.assertEqual("committed\n", pinned.text)
            self.assertEqual("git:HEAD", pinned.source)
            self.assertEqual(commit, pinned.git_commit)
            self.assertTrue(pinned.dirty)  # uncommitted modification exists
            self.assertTrue(pinned.differs_from_worktree)

            worktree = provenance.resolve_input(target, role="target")
            self.assertEqual("uncommitted edit\n", worktree.text)
            self.assertNotEqual(pinned.sha256, worktree.sha256)

    def test_clean_worktree_is_not_dirty_against_its_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)
            target = repo / "doc.md"
            target.write_text("stable\n", encoding="utf-8")
            _commit_all(repo, "add doc")

            pinned = provenance.resolve_input(target, role="target", pin="HEAD")
            self.assertFalse(pinned.dirty)
            self.assertFalse(pinned.differs_from_worktree)

    def test_clean_tree_behind_the_pin_is_not_dirty_but_does_differ(self):
        # The real case this distinction exists for: nothing is uncommitted,
        # the branch is simply behind the ref being pinned. One flag would
        # have to lie about one of those.
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)
            target = repo / "doc.md"
            target.write_text("v1\n", encoding="utf-8")
            first = _commit_all(repo, "v1")
            target.write_text("v2 with more content\n", encoding="utf-8")
            _commit_all(repo, "v2")
            # Move the worktree back to v1: clean tree, older content.
            _git(repo, "checkout", "-q", first)

            pinned = provenance.resolve_input(target, role="target", pin="main")

            self.assertEqual("v2 with more content\n", pinned.text)
            self.assertFalse(pinned.dirty)  # nothing uncommitted
            self.assertTrue(pinned.differs_from_worktree)  # but disk is older

    def test_unresolvable_pin_raises_rather_than_falling_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)
            target = repo / "doc.md"
            target.write_text("x\n", encoding="utf-8")
            _commit_all(repo, "add doc")

            # A ref that does not exist must not silently degrade to the
            # working tree -- that is exactly the substitution the pin exists
            # to prevent.
            with self.assertRaises(provenance.ProvenanceError):
                provenance.resolve_input(target, role="target", pin="origin/nope")

    def test_path_absent_from_the_pinned_ref_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)
            (repo / "committed.md").write_text("x\n", encoding="utf-8")
            _commit_all(repo, "initial")
            newcomer = repo / "untracked.md"
            newcomer.write_text("new\n", encoding="utf-8")

            with self.assertRaises(provenance.ProvenanceError):
                provenance.resolve_input(newcomer, role="target", pin="HEAD")


class OutsideARepoTest(unittest.TestCase):
    def test_unpinned_resolution_degrades_gracefully(self):
        with tempfile.TemporaryDirectory() as tmp:
            loose = Path(tmp) / "loose.md"
            loose.write_text("no repo here\n", encoding="utf-8")

            resolved = provenance.resolve_input(loose, role="doctrine")

            self.assertEqual("no repo here\n", resolved.text)
            self.assertEqual("worktree", resolved.source)
            self.assertIsNone(resolved.git_commit)
            self.assertIsNone(resolved.dirty)

    def test_pinned_resolution_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            loose = Path(tmp) / "loose.md"
            loose.write_text("no repo here\n", encoding="utf-8")

            with self.assertRaises(provenance.ProvenanceError):
                provenance.resolve_input(loose, role="doctrine", pin="origin/main")

    def test_missing_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(provenance.ProvenanceError):
                provenance.resolve_input(Path(tmp) / "nope.md", role="target")


class BuildManifestTest(unittest.TestCase):
    def _one_input(self, tmp: str) -> provenance.ResolvedInput:
        doc = Path(tmp) / "doc.md"
        doc.write_text("body\n", encoding="utf-8")
        return provenance.resolve_input(doc, role="target")

    def test_records_inputs_model_and_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = provenance.build_manifest(
                run_id="run-1",
                inputs=[self._one_input(tmp)],
                model_pin="claude-sonnet-5",
                resolved_models=["claude-sonnet-5"],
                started_at="2026-08-07T00:00:00Z",
                finished_at="2026-08-07T00:10:00Z",
                cli_version="2.1.224",
                tool_version="0.1.0",
            )

            self.assertEqual("run-1", manifest["run_id"])
            self.assertEqual("claude-sonnet-5", manifest["model_pin"])
            self.assertEqual(["claude-sonnet-5"], manifest["resolved_models"])
            self.assertEqual("2.1.224", manifest["cli_version"])
            self.assertEqual("0.1.0", manifest["tool_version"])
            self.assertEqual("2026-08-07T00:00:00Z", manifest["started_at"])
            self.assertEqual(1, len(manifest["inputs"]))
            self.assertNotIn("text", manifest["inputs"][0])

    def test_manifest_is_json_serializable(self):
        import json

        with tempfile.TemporaryDirectory() as tmp:
            manifest = provenance.build_manifest(
                run_id="run-1",
                inputs=[self._one_input(tmp)],
                model_pin="m",
                started_at="a",
                finished_at="b",
                cli_version=None,
            )
            json.loads(json.dumps(manifest))  # must not raise


class VerifyManifestTest(unittest.TestCase):
    def _manifest_for(self, path: Path, **kw) -> dict:
        return provenance.build_manifest(
            run_id="run-1",
            inputs=[provenance.resolve_input(path, role="target", **kw)],
            model_pin="m",
            started_at="a",
            finished_at="b",
            cli_version="2.1.221",
        )

    def test_unchanged_input_reports_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("same\n", encoding="utf-8")
            manifest = self._manifest_for(doc)

            report = provenance.verify_manifest(manifest, cli_version="2.1.221")

            self.assertFalse(report["drifted"])
            self.assertEqual("unchanged", report["inputs"][0]["status"])

    def test_edited_input_reports_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("before\n", encoding="utf-8")
            manifest = self._manifest_for(doc)
            doc.write_text("after\n", encoding="utf-8")

            report = provenance.verify_manifest(manifest, cli_version="2.1.221")

            self.assertTrue(report["drifted"])
            self.assertEqual("changed", report["inputs"][0]["status"])

    def test_deleted_input_reports_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("gone soon\n", encoding="utf-8")
            manifest = self._manifest_for(doc)
            doc.unlink()

            report = provenance.verify_manifest(manifest, cli_version="2.1.221")

            self.assertTrue(report["drifted"])
            self.assertEqual("missing", report["inputs"][0]["status"])

    def test_cli_upgrade_is_drift(self):
        # The doctrine's own time-relative rule: a receipt measured on one CLI
        # is not evidence about the next one. Same inputs, newer binary, still
        # drifted.
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("same\n", encoding="utf-8")
            manifest = self._manifest_for(doc)

            report = provenance.verify_manifest(manifest, cli_version="2.1.224")

            self.assertTrue(report["drifted"])
            self.assertEqual("unchanged", report["inputs"][0]["status"])
            self.assertEqual("2.1.221", report["cli_version"]["recorded"])
            self.assertEqual("2.1.224", report["cli_version"]["current"])
            self.assertTrue(report["cli_version"]["changed"])


if __name__ == "__main__":
    unittest.main()
