# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins_testsupport.paths import repo_root


def test_conceptual_onboarding_passes() -> None:
    root = repo_root()
    text = (
        root / "docs" / "02-agentic-proteins" / "foundation" / "domain-language.md"
    ).read_text()
    required = (
        "Domain Language",
        "Package Vocabulary Anchors",
        "agentic-proteins",
        "agentic_proteins",
        "packages/agentic-proteins",
    )
    for term in required:
        assert term in text
