# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import math
from pathlib import Path

from bijux_proteomics.quantification import (
    ProteinMatrixTargetKind,
    build_peptide_intensity_matrix_from_features,
    build_peptide_profile_inconsistency_report,
    parse_ms1_feature_table,
    render_peptide_profile_inconsistency_tsv,
)


def _quant_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def test_peptide_profile_inconsistency_flags_directionally_inverted_peptides() -> None:
    parse_report = parse_ms1_feature_table(
        _quant_fixture("protein_profile_inconsistency_features.tsv")
    )
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        parse_report.accepted_records
    )

    report = build_peptide_profile_inconsistency_report(
        peptide_matrix,
        target_kind=ProteinMatrixTargetKind.PROTEIN,
    )
    by_peptide = {entry.peptide_id: entry for entry in report.entries}

    assert report.summary.protein_row_count == 1
    assert report.summary.evaluated_entry_count == 4
    assert report.summary.inconsistent_entry_count == 1
    assert by_peptide["PEPVVK"].inconsistent_with_protein_profile is True
    assert by_peptide["PEPVVK"].outlier_reason.value == "directional_profile_inversion"
    assert math.isclose(
        by_peptide["PEPVVK"].correlation_to_protein_profile or 0.0,
        -1.0,
    )
    assert by_peptide["PEPVVK"].profile_agreement_score == 0.2
    assert len(by_peptide["PEPVVK"].sample_residuals) == 3
    assert by_peptide["PEPAAK"].inconsistent_with_protein_profile is False
    assert by_peptide["PEPAAK"].profile_agreement_score == 1.0


def test_peptide_profile_inconsistency_renderer_preserves_residual_ledgers() -> None:
    parse_report = parse_ms1_feature_table(
        _quant_fixture("protein_profile_inconsistency_features.tsv")
    )
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        parse_report.accepted_records
    )
    report = build_peptide_profile_inconsistency_report(peptide_matrix)

    rendered = render_peptide_profile_inconsistency_tsv(report)

    assert (
        "entity_id\ttarget_kind\tpeptide_id\tpeptide_sequence\tprotein_refs\treference_peptide_ids\toverlap_sample_count\treference_peptide_count\tcorrelation_to_protein_profile\tresidual_rmsd_log2\tmax_abs_residual_log2\tprofile_agreement_score\tinconsistent_with_protein_profile\toutlier_reason\tsample_residuals_log2"
        in rendered
    )
    assert (
        "P1\tprotein\tPEPVVK\tPEPVVK\tP1\tPEPAAK;PEPCCK;PEPDDK\t3\t3\t-1.0000\t1.6330\t2.0000\t0.2000\ttrue\tdirectional_profile_inversion\tS1:2.0000;S2:0.0000;S3:-2.0000"
        in rendered
    )
