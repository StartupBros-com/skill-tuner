"""Test for skill-tuner's doctor.sh preflight (Unit 6).

doctor.sh is a pro-gate-style ok/warn/blocking shell preflight, not a Python
module, so it's tested the way it's meant to run: shelled out to directly,
checking exit code and output. This proves the one behavior the unit spec
calls out explicitly -- a PATH with no `claude` on it makes the run exit
non-zero -- rather than re-testing bash line by line.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
DOCTOR_SH = SCRIPTS_DIR / "doctor.sh"


def _path_without_claude() -> str:
    """The current PATH with every directory that holds a `claude`
    executable removed, so the check is robust to wherever this machine's
    claude happens to be installed (mise shim, npm global, /usr/local/bin,
    ...) while every other tool doctor.sh needs (bash, python3, grep,
    dirname) stays reachable from its own, different directory."""
    dirs = os.environ.get("PATH", "").split(os.pathsep)
    kept = [d for d in dirs if d and not (Path(d) / "claude").exists()]
    return os.pathsep.join(kept)


class DoctorPreflightTest(unittest.TestCase):
    def test_doctor_sh_exists_and_is_executable(self):
        self.assertTrue(DOCTOR_SH.exists(), f"doctor.sh not found at {DOCTOR_SH}")
        self.assertTrue(os.access(DOCTOR_SH, os.X_OK), "doctor.sh must be executable")

    def test_stripped_path_without_claude_exits_non_zero_and_names_claude(self):
        env = dict(os.environ)
        env["PATH"] = _path_without_claude()

        result = subprocess.run([str(DOCTOR_SH)], capture_output=True, text=True, env=env)

        self.assertNotEqual(
            0,
            result.returncode,
            f"doctor.sh should exit non-zero when claude is missing from PATH\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn("claude", (result.stdout + result.stderr).lower())

    def test_path_with_claude_present_exits_zero(self):
        """Control for the test above: when claude *is* reachable, the same
        run must succeed.

        The claude on PATH is synthesized rather than borrowed from the
        machine. This test previously used the ambient PATH and passed only
        where the Claude CLI happened to be installed -- green on a
        developer's box, red on any CI runner, which is exactly the coupling
        a unit test should not have. A stub also pins what "present" means:
        a claude whose --help advertises the two flags the adapter builds its
        command from.
        """
        with tempfile.TemporaryDirectory() as tmp:
            stub_dir = Path(tmp)
            stub = stub_dir / "claude"
            stub.write_text(
                "#!/bin/sh\n"
                'if [ "$1" = "--help" ]; then\n'
                '  echo "--setting-sources <sources>"\n'
                '  echo "--output-format <format>"\n'
                "  exit 0\n"
                "fi\n"
                "exit 0\n",
                encoding="utf-8",
            )
            stub.chmod(0o755)

            env = dict(os.environ)
            env["PATH"] = os.pathsep.join([str(stub_dir), _path_without_claude()])

            result = subprocess.run(
                [str(DOCTOR_SH)], capture_output=True, text=True, env=env
            )

        self.assertEqual(
            0,
            result.returncode,
            f"doctor.sh should exit zero when claude is on PATH\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn("--setting-sources", result.stdout)


if __name__ == "__main__":
    unittest.main()
