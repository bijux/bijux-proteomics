# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    ComplexMemberKind,
    ComplexMembershipRecord,
    build_complex_activity_report,
    render_complex_activity_condition_comparison_tsv,
    render_complex_activity_condition_score_tsv,
    render_complex_activity_matrix_tsv,
    render_complex_activity_sample_score_tsv,
    render_complex_activity_summary_tsv,
    render_complex_activity_unresolved_member_tsv,
    render_complex_member_contribution_tsv,
)
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    LabelFreeQuantTable,
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _build_fixture_table() -> LabelFreeQuantTable:
    parse_report = parse_ms1_feature_table(
        _workflow_fixture("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
        ),
    )
    protein_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    return normalize_label_free_table(
        protein_table,
        method=NormalizationMethod.MEDIAN,
    )


def test_render_complex_activity_ledgers() -> None:
    design_entries = parse_experimental_design_table(
        _workflow_fixture("biological_report.design.tsv")
    ).accepted_entries
    complex_records = (
        ComplexMembershipRecord(
            complex_id="custom:triad",
            complex_name="Signal triad",
            source_name="custom",
            source_accession="CMPLX-01",
            member_kind=ComplexMemberKind.PROTEIN,
            member_id="P04637",
        ),
        ComplexMembershipRecord(
            complex_id="custom:triad",
            complex_name="Signal triad",
            source_name="custom",
            source_accession="CMPLX-01",
            member_kind=ComplexMemberKind.PROTEIN,
            member_id="Q9Y243",
        ),
        ComplexMembershipRecord(
            complex_id="custom:sparse",
            complex_name="Sparse complex",
            source_name="custom",
            source_accession="CMPLX-02",
            member_kind=ComplexMemberKind.PROTEIN,
            member_id="P04637",
        ),
        ComplexMembershipRecord(
            complex_id="custom:sparse",
            complex_name="Sparse complex",
            source_name="custom",
            source_accession="CMPLX-02",
            member_kind=ComplexMemberKind.PROTEIN,
            member_id="Q99999",
        ),
    )

    report = build_complex_activity_report(
        _build_fixture_table(),
        complex_records,
        design_entries=design_entries,
    )

    summary_tsv = render_complex_activity_summary_tsv(report)
    matrix_tsv = render_complex_activity_matrix_tsv(report)
    sample_tsv = render_complex_activity_sample_score_tsv(report)
    condition_tsv = render_complex_activity_condition_score_tsv(report)
    comparison_tsv = render_complex_activity_condition_comparison_tsv(report)
    contribution_tsv = render_complex_member_contribution_tsv(report)
    unresolved_tsv = render_complex_activity_unresolved_member_tsv(report)

    assert summary_tsv.splitlines()[0].startswith("entity_level\tmeasure_kind")
    assert (
        "complex_id\tcomplex_name\tsource_name\tsource_accession\tC1\tC2\tC3\tT1\tT2\tT3"
        in matrix_tsv
    )
    assert "sample_id\tcondition\tbatch\tactivity_score" in sample_tsv
    assert "limiting_member_ids" in sample_tsv.splitlines()[0]
    assert "condition_a_confidence_status" in comparison_tsv.splitlines()[0]
    assert "member_kind\tmember_id\tresolved_protein_refs" in contribution_tsv
    assert "Q99999" in unresolved_tsv
    assert "\tlow\t" in condition_tsv or "\tlow\t" in sample_tsv
