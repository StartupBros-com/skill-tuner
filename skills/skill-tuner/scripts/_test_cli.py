"""Shared stdout capture for in-process CLI tests."""

import contextlib
import io

import tune


def run_cli(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = tune.main(list(argv))
    return code, out.getvalue()
