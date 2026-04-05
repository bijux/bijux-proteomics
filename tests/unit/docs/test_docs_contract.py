# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path
import re


ALLOWED_SECTION_ORDER = [
    "Overview",
    "Contracts",
    "Invariants",
    "Failure Modes",
    "Extension Points",
    "Exit Criteria",
]
FRONT_MATTER_FIELDS = ("**Scope:**", "**Audience:**", "**Guarantees:**", "**Non-Goals:**")
CODE_REF_RE = re.compile(
    r"((packages/agentic-proteins/src/agentic_proteins|tests|scripts)/[A-Za-z0-9_./-]+\.py|api/[A-Za-z0-9_./-]+\.yaml)"
)


def _repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in [path] + list(path.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("pyproject.toml not found for repo root")


def test_docs_contract() -> None:
    root = _repo_root()
    docs_dir = root / "docs"
    for doc in docs_dir.rglob("*.md"):
        text = doc.read_text()
        lines = text.splitlines()
        assert lines and lines[0].startswith("# ")
        title = lines[0][2:].strip()
        expected_title = "Bijux Proteomics" if doc.stem == "index" else doc.stem
        assert title == expected_title
        for idx, field in enumerate(FRONT_MATTER_FIELDS, start=2):
            assert len(lines) > idx
            assert lines[idx].strip().startswith(field)
            assert lines[idx].strip() != field
        assert any("Why:" in line for line in lines[:50])

        sections = [line[3:].strip() for line in lines if line.startswith("## ")]
        assert sections == ALLOWED_SECTION_ORDER
        assert not any(line.startswith("###") for line in lines)
        assert CODE_REF_RE.search(text)
        assert len(lines) <= 300
