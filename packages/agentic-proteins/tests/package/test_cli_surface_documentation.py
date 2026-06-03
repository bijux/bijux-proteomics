# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins_testsupport.paths import repo_root


def test_cli_surface_documented() -> None:
    doc_path = (
        repo_root() / "docs" / "02-agentic-proteins" / "interfaces" / "cli-surface.md"
    )
    text = doc_path.read_text(encoding="utf-8")

    required_terms = (
        "CLI Surface",
        "src/agentic_proteins/interfaces/cli.py",
        "src/agentic_proteins/interfaces/http/app.py",
        "bijux-proteomics-runtime --help",
        "agentic-proteins --help",
        "compatibility CLI surface",
    )
    for term in required_terms:
        assert term in text
