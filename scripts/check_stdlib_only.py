#!/usr/bin/env python3
"""Assert the shipped runner imports nothing but the standard library (R7).

R7 is a promise to adopters: the eval runner installs with the plugin and
runs on a bare machine, so `pip install` is never a prerequisite. Nothing was
enforcing it -- the constraint lived in a plan document and in the discipline
of whoever last edited the scripts, which is exactly the kind of rule that
holds until the first convenient afternoon.

This is a repo-maintenance tool. It is not part of the bundled skill, makes
no model calls, and imports only stdlib itself.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SHIPPED_DIR = REPO_ROOT / "skills" / "skill-tuner" / "scripts"

# Modules that live beside the shipped scripts and import each other.
LOCAL_MODULES = {"tune", "probe", "routing_parity", "provenance", "compare"}


def _top_level_imports(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # `from . import x` has no module name to police.
            if node.level == 0 and node.module:
                found.add(node.module.split(".")[0])
    return found


def main() -> int:
    if not hasattr(sys, "stdlib_module_names"):  # pragma: no cover
        print("need Python 3.10+ to introspect the stdlib module list")
        return 2

    allowed = set(sys.stdlib_module_names) | LOCAL_MODULES
    offenders: list[str] = []
    checked = 0

    for path in sorted(SHIPPED_DIR.rglob("*.py")):
        checked += 1
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name in sorted(_top_level_imports(tree) - allowed):
            offenders.append(f"{path.relative_to(REPO_ROOT)}: imports {name!r}")

    if offenders:
        print("Third-party imports found in the shipped runner (violates R7):")
        for line in offenders:
            print(f"  {line}")
        return 1

    print(f"stdlib-only: OK ({checked} shipped file(s) checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
