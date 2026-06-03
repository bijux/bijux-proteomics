# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia import (
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
    assert report.entries[0].chemical_liability_penalty >= 0.0


def test_optimize_targeted_assay_candidates_penalizes_chemically_risky_peptides() -> (
    None
):
    report = optimize_targeted_assay_candidates(
        (
            TargetedAssayOptimizationCandidate(
                candidate_id="safe",
                peptide_sequence="ATIDEAR",
                uniqueness_score=0.86,
                detectability_score=0.82,
                ptm_ambiguity_penalty=0.1,
                qc_score=0.8,
            ),
            TargetedAssayOptimizationCandidate(
                candidate_id="risky",
                peptide_sequence="MNNQVVVVVVILKKDG",
                uniqueness_score=0.95,
                detectability_score=0.9,
                ptm_ambiguity_penalty=0.0,
                qc_score=0.95,
            ),
        )
    )

    assert report.entries[0].candidate_id == "safe"
    assert report.entries[0].chemical_liability_penalty == 0.0
    assert report.entries[1].candidate_id == "risky"
    assert report.entries[1].chemical_liability_penalty > 0.9
    assert "oxidation_prone_residues" in report.entries[1].chemical_liability_codes
