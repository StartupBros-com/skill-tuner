"""Offline contracts for portfolio's source-error bookkeeping."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import portfolio


class InventoryErrorsTest(unittest.TestCase):
    def source(self):
        return {"name": "fixture", "path": "fixture", "status": "ok",
                "count": 7, "notes": ["earlier note"]}

    def assert_source(self, source, notes, *, status="unreadable", count=7):
        self.assertEqual(source, {"name": "fixture", "path": "fixture",
                                 "status": status, "count": count,
                                 "notes": ["earlier note", *notes]})

    def test_json_decode_and_read_failures_preserve_exact_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.json"
            for contents in (b"{broken", b"\xff"):
                with self.subTest(contents=contents):
                    path.write_bytes(contents)
                    try:
                        json.loads(path.read_text(encoding="utf-8"))
                    except (UnicodeError, ValueError) as exc:
                        expected = f"Cannot read JSON: {exc}"
                    source = self.source()
                    self.assertEqual(portfolio._read_json(path, source), {})
                    self.assert_source(source, [expected])
            source = self.source()
            with mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                self.assertEqual(portfolio._read_json(path, source), {})
            self.assert_source(source, ["Cannot read JSON: denied"])

    def test_non_object_json_refuses_without_resetting_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.json"
            for value in ([], None, "text", 3, True):
                with self.subTest(value=value):
                    path.write_text(json.dumps(value), encoding="utf-8")
                    source = self.source()
                    self.assertEqual(portfolio._read_json(path, source), {})
                    self.assert_source(source, ["Expected a JSON object."])

    def test_directory_listing_errors_preserve_exact_notes(self):
        path = Path("inventory")
        for error in (PermissionError("denied"), ValueError("invalid path")):
            with self.subTest(error=type(error).__name__):
                source = self.source()
                with mock.patch.object(Path, "iterdir", side_effect=error):
                    self.assertEqual(portfolio._directory_entries(path, source), [])
                self.assert_source(source, [f"Cannot list inventory: {error}"])

    def test_directory_inspection_continues_after_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad, good = root / "a-bad", root / "b-good"
            bad.mkdir()
            good.mkdir()
            original_stat = Path.stat

            def stat(path, *args, **kwargs):
                if path == bad:
                    raise PermissionError("denied")
                return original_stat(path, *args, **kwargs)

            source = self.source()
            with mock.patch.object(Path, "stat", stat):
                self.assertEqual(portfolio._directories(root, source), [good])
            self.assert_source(source, [f"Cannot inspect {bad}: denied"])

    def test_skill_read_errors_continue_and_count_only_successes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unreadable, invalid, good = (root / name for name in ("denied.md", "invalid.md", "good.md"))
            unreadable.write_text("ignored", encoding="utf-8")
            invalid.write_bytes(b"\xff")
            good.write_text("---\ndescription: Good skill.\n---\n", encoding="utf-8")
            try:
                invalid.read_text(encoding="utf-8")
            except UnicodeError as exc:
                invalid_note = f"Cannot read {invalid}: {exc}"
            original_read = Path.read_text

            def read(path, *args, **kwargs):
                if path == unreadable:
                    raise PermissionError("denied")
                return original_read(path, *args, **kwargs)

            source = self.source()
            with mock.patch.object(Path, "read_text", read):
                rows = portfolio._read_skills(
                    [(p, p.stem, False) for p in (unreadable, invalid, good)],
                    source, "user", {}, {},
                )
            self.assertEqual([row["name"] for row in rows], ["good"])
            self.assertEqual(rows[0]["description"], "Good skill.")
            self.assert_source(source, [f"Cannot read {unreadable}: denied", invalid_note], count=8)

    def test_missing_sources_keep_distinct_status_and_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            source = self.source()
            self.assertEqual(portfolio._read_json(missing, source), {})
            self.assert_source(source, ["Source file is missing."], status="missing")
            for root in (False, True):
                source = self.source()
                self.assertEqual(portfolio._directory_entries(missing, source, root=root), [])
                self.assert_source(source, [f"Missing directory or broken symlink: {missing}"],
                                   status="missing" if root else "ok")
            source = self.source()
            self.assertEqual(portfolio._read_skills([(missing, "missing", False)], source, "user", {}, {}), [])
            self.assert_source(source, [], status="ok")

    def test_successful_reads_preserve_existing_error_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.json"
            path.write_text('{"answer": 42}', encoding="utf-8")
            source = self.source()
            source["status"] = "unreadable"
            self.assertEqual(portfolio._read_json(path, source), {"answer": 42})
            self.assert_source(source, [], count=1)
            self.assertEqual(portfolio._directory_entries(path.parent, source), [path])
            self.assert_source(source, [], count=1)


if __name__ == "__main__":
    unittest.main()
