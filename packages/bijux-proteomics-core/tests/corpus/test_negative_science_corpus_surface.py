# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.corpus import (
    NegativeScienceCase,
    NegativeScienceCaseOutcome,
    build_negative_science_corpus_report,
)


def test_build_negative_science_corpus_report_counts_refusal_and_caveated_cases() -> (
    None
):
    report = build_negative_science_corpus_report(
        (
            NegativeScienceCase(
                case_id="neg-1",
                incoherence_reason="sample labels conflict with design groups",
                expected_outcome=NegativeScienceCaseOutcome.REFUSED,
                evidence_pointer="case:neg-1",
            ),
            NegativeScienceCase(
                case_id="neg-2",
                incoherence_reason="missing decoy support for database FDR claim",
                expected_outcome=NegativeScienceCaseOutcome.CAVEATED,
                evidence_pointer="case:neg-2",
            ),
        )
    )

    assert report.refusal_case_count == 1
    assert report.caveated_case_count == 1
