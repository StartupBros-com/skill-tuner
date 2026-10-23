"""Byte and filesystem contracts for the shared routing skill fixture."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from _test_skill import write_skill  # noqa: E402


class SkillFixtureTest(unittest.TestCase):
    def test_frozen_bytes_match_original_fixture_builders(self):
        # Captured from both original helpers at main 1252134. Keep the
        # existing dedent behavior even for multiline or delimiter-like text.
        cases = [
            (
                "ordinary", "Handles alpha.", "Alpha body.",
                "---\nname: ordinary\ndescription: Handles alpha.\n---\n\nAlpha body.\n",
            ),
            ("empty", "", "", "---\nname: empty\ndescription: \n---\n\n\n"),
            (
                "unicode", "Café 🧪", "Résumé 漢字\n",
                "---\nname: unicode\ndescription: Café 🧪\n---\n\nRésumé 漢字\n\n",
            ),
            (
                "multiline", ">-\n  Line one.\n  Line two.", "Body.\nNext line.",
                "            ---\n            name: multiline\n"
                "            description: >-\n  Line one.\n  Line two.\n"
                "            ---\n\n            Body.\nNext line.\n",
            ),
            (
                "whitespace", "  description  ", "  body\t \n\n",
                "---\nname: whitespace\ndescription:   description  \n"
                "---\n\n  body\t \n\n\n",
            ),
            (
                "delimiters", "A: B # C", "---\nname: untouched\n```\n",
                "            ---\n            name: delimiters\n"
                "            description: A: B # C\n            ---\n\n"
                "            ---\nname: untouched\n```\n\n",
            ),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for slug, description, body, expected in cases:
                with self.subTest(slug=slug):
                    path = write_skill(Path(tmp), slug, description, body)
                    self.assertEqual(expected.encode("utf-8"), path.read_bytes())

    def test_creates_missing_parents_and_returns_the_skill_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "missing" / "parent"
            path = write_skill(base, "nested/alpha", "Description.", "Body.")
            self.assertIsInstance(path, Path)
            self.assertEqual(base / "nested" / "alpha" / "SKILL.md", path)
            self.assertTrue(path.is_file())

    def test_overwrites_existing_file_and_preserves_sibling(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            path = write_skill(base, "alpha", "Old description.", "Old body.")
            sibling = path.parent / "other.md"
            sibling.write_bytes(b"leave me alone\n")
            again = write_skill(base, "alpha", "New description.", "New body.")
            self.assertEqual(path, again)
            self.assertEqual(
                b"---\nname: alpha\ndescription: New description.\n---\n\nNew body.\n",
                path.read_bytes(),
            )
            self.assertEqual(b"leave me alone\n", sibling.read_bytes())

    def test_mkdir_failure_propagates_without_writing(self):
        failure = PermissionError("fixture directory denied")
        with (
            mock.patch.object(Path, "mkdir", side_effect=failure) as mkdir,
            mock.patch.object(Path, "write_text") as write,
        ):
            with self.assertRaises(PermissionError) as caught:
                write_skill(Path("relative"), "alpha", "Description.", "Body.")
        self.assertIs(failure, caught.exception)
        mkdir.assert_called_once_with(parents=True, exist_ok=True)
        write.assert_not_called()

    def test_write_failure_propagates_after_creating_directory(self):
        failure = OSError("fixture write failed")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            def fail_write(path, content, *, encoding):
                self.assertEqual(base / "alpha" / "SKILL.md", path)
                self.assertTrue(path.parent.is_dir())
                self.assertEqual("utf-8", encoding)
                raise failure

            with mock.patch.object(Path, "write_text", autospec=True, side_effect=fail_write):
                with self.assertRaises(OSError) as caught:
                    write_skill(base, "alpha", "Description.", "Body.")
            self.assertIs(failure, caught.exception)
            self.assertFalse((base / "alpha" / "SKILL.md").exists())

    def test_file_in_place_of_skill_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            obstacle = base / "alpha"
            obstacle.write_bytes(b"keep this file")
            with self.assertRaises(FileExistsError):
                write_skill(base, "alpha", "Description.", "Body.")
            self.assertEqual(b"keep this file", obstacle.read_bytes())


if __name__ == "__main__":
    unittest.main()
