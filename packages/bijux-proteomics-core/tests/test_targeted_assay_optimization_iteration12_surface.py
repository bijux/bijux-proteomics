# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia_iteration12 import (
    TargetedAssayOptimizationCandidate,
    optimize_targeted_assay_candidates,
)


def test_optimize_targeted_assay_candidates_prioritizes_stronger_candidates() -> None:
    report = optimize_targeted_assay_candidates(
        (
            TargetedAssayOptimizationCandidate(
                candidate_id="cand-a",
                peptide_sequence="PEPTIDEK",
                uniqueness_score=0.9,
                detectability_score=0.85,
                ptm_ambiguity_penalty=0.1,
                qc_score=0.8,
            ),
            TargetedAssayOptimizationCandidate(
                candidate_id="cand-b",
                peptide_sequence="PEPTIDER",
                uniqueness_score=0.6,
                detectability_score=0.7,
                ptm_ambiguity_penalty=0.25,
                qc_score=0.7,
            ),
        )
    )

    assert report.entries[0].candidate_id == "cand-a"
    assert report.entries[0].rank == 1
