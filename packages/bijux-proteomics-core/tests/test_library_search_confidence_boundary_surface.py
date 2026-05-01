# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification_iteration04 import (
    ConfidenceResultFamily,
    LibrarySearchConfidenceBoundaryInput,
    evaluate_library_search_confidence_boundary,
)


def test_library_search_confidence_boundary_classifies_supported_families() -> None:
    report = evaluate_library_search_confidence_boundary(
        (
            LibrarySearchConfidenceBoundaryInput(
                run_id="dda-a",
                family_hint="database",
                has_target_decoy=True,
                has_library_scores=False,
            ),
            LibrarySearchConfidenceBoundaryInput(
                run_id="open-a",
                family_hint="open_search",
                has_target_decoy=True,
                has_library_scores=False,
            ),
            LibrarySearchConfidenceBoundaryInput(
                run_id="library-a",
                family_hint="spectral-library",
                has_target_decoy=False,
                has_library_scores=True,
            ),
            LibrarySearchConfidenceBoundaryInput(
                run_id="dia-a",
                family_hint="dia",
                has_target_decoy=False,
                has_library_scores=True,
                is_dia=True,
            ),
        )
    )

    assert report.classified_families["dda-a"] is ConfidenceResultFamily.DATABASE_DDA
    assert report.classified_families["open-a"] is ConfidenceResultFamily.OPEN_SEARCH
    assert (
        report.classified_families["library-a"]
        is ConfidenceResultFamily.SPECTRAL_LIBRARY
    )
    assert report.classified_families["dia-a"] is ConfidenceResultFamily.DIA_LIBRARY


def test_library_search_confidence_boundary_refuses_incompatible_family_mixtures() -> (
    None
):
    report = evaluate_library_search_confidence_boundary(
        (
            LibrarySearchConfidenceBoundaryInput(
                run_id="open-a",
                family_hint="open_search",
                has_target_decoy=True,
                has_library_scores=False,
            ),
            LibrarySearchConfidenceBoundaryInput(
                run_id="library-a",
                family_hint="library",
                has_target_decoy=False,
                has_library_scores=True,
            ),
        )
    )

    assert report.compatible is False
    assert any(issue.code == "open_vs_library_mixture" for issue in report.issues)
