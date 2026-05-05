# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from types import ModuleType

import bijux_proteomics_intelligence


def test_intelligence_public_api_exposes_curated_owner_namespaces() -> None:
    assert bijux_proteomics_intelligence.__all__ == [
        "benchmark_reviews",
        "briefs",
        "charter",
        "decision_paths",
        "evidence_posture",
        "evaluators",
        "follow_up_learning",
        "interpretation",
        "policies",
        "skeptical_review",
    ]


def test_intelligence_public_api_loads_owner_modules_lazily() -> None:
    assert isinstance(bijux_proteomics_intelligence.briefs, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.interpretation, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.decision_paths, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.evaluators, ModuleType)
    assert isinstance(bijux_proteomics_intelligence.charter, ModuleType)

    assert bijux_proteomics_intelligence.briefs.prioritize_candidates.__name__ == (
        "prioritize_candidates"
    )
    assert (
        bijux_proteomics_intelligence.interpretation.build_run_interpretation_summary.__name__
        == "build_run_interpretation_summary"
    )
    assert (
        bijux_proteomics_intelligence.decision_paths.build_review_board_decision_path.__name__
        == "build_review_board_decision_path"
    )
    assert (
        bijux_proteomics_intelligence.skeptical_review.build_skeptical_review_report.__name__
        == "build_skeptical_review_report"
    )
