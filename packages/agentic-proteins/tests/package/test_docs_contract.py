# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins_testsupport.paths import repo_root


def test_docs_contract() -> None:
    root = repo_root()
    docs_dir = root / "docs" / "02-agentic-proteins"
    for doc in docs_dir.rglob("*.md"):
        text = doc.read_text(encoding="utf-8")
        lines = text.splitlines()
        assert lines[:1] == ["---"]
        assert "title:" in text
        assert "audience:" in text
        assert "type:" in text
        assert "status:" in text
        assert "owner:" in text
        assert any(line.startswith("# ") for line in lines)

        sections = [line[3:].strip() for line in lines if line.startswith("## ")]
        assert sections
        assert not any(line.startswith("###") for line in lines)
        assert len(lines) <= 300
