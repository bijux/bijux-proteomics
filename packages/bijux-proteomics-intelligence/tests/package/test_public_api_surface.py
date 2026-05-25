# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from importlib import import_module
from types import ModuleType

import bijux_proteomics_intelligence


def test_intelligence_public_api_exposes_curated_owner_namespaces() -> None:
    assert bijux_proteomics_intelligence.__all__ == [
        "candidates",
        "claims",
        "governance",
        "interpretation",
        "judgment",
        "learning",
        "posture",
        "reviews",
    ]


def test_intelligence_public_api_loads_owner_modules_lazily() -> None:
    assert isinstance(bijux_proteomics_intelligence.candidates, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.claims, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.governance, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.interpretation, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.judgment, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.learning, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.posture, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.reviews, ModuleType)

    assert bijux_proteomics_intelligence.candidates.__name__ == (
        "bijux_proteomics_intelligence.candidates"
    )
    assert bijux_proteomics_intelligence.claims.__name__ == (
        "bijux_proteomics_intelligence.claims"
    )
    assert bijux_proteomics_intelligence.governance.__name__ == (
        "bijux_proteomics_intelligence.governance"
    )
    assert bijux_proteomics_intelligence.reviews.__name__ == (
        "bijux_proteomics_intelligence.reviews"
    )
    assert (
        import_module(
            "bijux_proteomics_intelligence.candidates.selection"
        ).select_candidates.__name__
        == "select_candidates"
    )
    assert (
        import_module(
            "bijux_proteomics_intelligence.claims.support"
        ).validate_claim_support.__name__
        == "validate_claim_support"
    )
    assert (
        import_module(
            "bijux_proteomics_intelligence.governance.charter"
        ).__name__.split(".")[-1]
        == "charter"
    )
    assert (
        import_module(
            "bijux_proteomics_intelligence.judgment.paths"
        ).build_review_board_decision_path.__name__
        == "build_review_board_decision_path"
    )
    assert (
        import_module(
            "bijux_proteomics_intelligence.learning.adaptation"
        ).apply_planned_observed_learning_loop.__name__
        == "apply_planned_observed_learning_loop"
    )
    assert (
        import_module(
            "bijux_proteomics_intelligence.posture.skeptical"
        ).build_skeptical_review_report.__name__
        == "build_skeptical_review_report"
    )
    assert (
        import_module(
            "bijux_proteomics_intelligence.reviews.candidates"
        ).build_candidate_comparison_packet.__name__
        == "build_candidate_comparison_packet"
    )
    assert (
        bijux_proteomics_intelligence.interpretation.build_run_interpretation_summary.__name__
        == "build_run_interpretation_summary"
    )
