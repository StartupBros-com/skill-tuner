"""Test-only SKILL.md fixture builder shared by routing and CLI tests."""

from __future__ import annotations

import textwrap
from pathlib import Path


def write_skill(base: Path, slug: str, description: str, body: str) -> Path:
    skill_dir = base / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        textwrap.dedent(
            f"""\
            ---
            name: {slug}
            description: {description}
            ---

            {body}
            """
        ),
        encoding="utf-8",
    )
    return skill_md
