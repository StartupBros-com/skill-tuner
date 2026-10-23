"""Contract checks for the shared in-process CLI test helper."""

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from _test_cli import run_cli  # noqa: E402
import tune  # noqa: E402


class RunCliTest(unittest.TestCase):
    def setUp(self):
        # These tests must never launch a real CLI or contact a provider.
        for target in ("subprocess.Popen", "socket.create_connection", "socket.socket"):
            self.enterContext(mock.patch(target, side_effect=AssertionError(target)))

    def test_forwards_arguments_as_a_list_and_returns_status_and_stdout(self):
        def main(argv):
            self.assertEqual(["compare", "", "two words", "λ"], argv)
            self.assertIs(type(argv), list)
            print("first")
            print("λ", end="")
            return 7

        with mock.patch.object(tune, "main", side_effect=main) as call:
            self.assertEqual((7, "first\nλ"), run_cli("compare", "", "two words", "λ"))
        call.assert_called_once()

    def test_no_arguments_and_no_output(self):
        with mock.patch.object(tune, "main", return_value=0) as call:
            self.assertEqual((0, ""), run_cli())
        call.assert_called_once_with([])

    def test_each_call_has_a_fresh_output_buffer(self):
        with mock.patch.object(tune, "main", side_effect=lambda argv: print(argv[0]) or 0):
            self.assertEqual((0, "one\n"), run_cli("one"))
            self.assertEqual((0, "two\n"), run_cli("two"))

    def test_restores_stdout_and_does_not_capture_stderr(self):
        stdout, stderr = io.StringIO(), io.StringIO()

        def main(argv):
            print("out")
            print("err", file=sys.stderr)
            return 2

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with mock.patch.object(tune, "main", side_effect=main):
                self.assertEqual((2, "out\n"), run_cli())
            self.assertIs(sys.stdout, stdout)
            print("after")
        self.assertEqual("after\n", stdout.getvalue())
        self.assertEqual("err\n", stderr.getvalue())

    def test_exceptions_propagate_and_stdout_is_restored(self):
        for error in (ValueError("failed"), SystemExit(2)):
            with self.subTest(error=type(error).__name__):
                original_stdout = sys.stdout

                def main(argv):
                    print("before failure")
                    raise error

                with mock.patch.object(tune, "main", side_effect=main):
                    with self.assertRaises(type(error)) as raised:
                        run_cli("compare")
                self.assertIs(raised.exception, error)
                self.assertIs(sys.stdout, original_stdout)


if __name__ == "__main__":
    unittest.main()
