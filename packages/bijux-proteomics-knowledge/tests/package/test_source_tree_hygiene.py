# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

KNOWLEDGE_TEST_ROOT = Path("packages/bijux-proteomics-knowledge/tests")


def test_knowledge_tests_follow_owned_boundary_families() -> None:
    allowed_top_level_paths = {
        "coverage",
        "conftest.py",
        "complexes",
        "contracts",
        "disease",
        "drugs",
        "features",
        "governance",
        "identity",
        "kinases",
        "memory",
        "orthologs",
        "package",
        "pathways",
        "references",
        "reviews",
    }
    observed_top_level_paths = {
        path.relative_to(KNOWLEDGE_TEST_ROOT).parts[0]
        for path in KNOWLEDGE_TEST_ROOT.rglob("*")
        if path != KNOWLEDGE_TEST_ROOT
    }

    assert observed_top_level_paths == allowed_top_level_paths
