# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from tests.helpers.paths import repo_root


def test_conceptual_onboarding_passes() -> None:
    root = repo_root()
    text = (root / "docs" / "concepts" / "core_concepts.md").read_text()
    required = (
        "agent:",
        "protein:",
        "signal:",
        "pathway:",
        "regulation:",
        "constraints",
        "failure",
        "recovery",
    )
    for term in required:
        assert term in text
