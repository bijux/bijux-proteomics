# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_knowledge.reviews as reviews


def test_review_package_surface_exports_only_owner_modules() -> None:
    assert reviews.__all__ == [
        "decision_briefs",
        "explanations",
        "flagship_evidence",
        "provenance",
        "trends",
    ]


def test_review_package_surface_does_not_leak_review_models_at_package_level() -> None:
    leaked_names = {
        "Field",
        "JsonModel",
        "KnowledgeDecisionBrief",
        "WorkflowClaimTier",
    }

    assert leaked_names.isdisjoint(set(dir(reviews)))
