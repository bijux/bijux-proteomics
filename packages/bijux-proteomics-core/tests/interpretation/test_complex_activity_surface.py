# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.interpretation import (
    ComplexActivityPolicy,
    ComplexMemberKind,
    ComplexMembershipRecord,
    build_complex_activity_report,
)
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _build_fixture_table():
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


def test_build_complex_activity_report_scores_complexes_with_limiting_members() -> None:
    design_entries = parse_experimental_design_table(
        _workflow_fixture("biological_report.design.tsv")
    ).accepted_entries
    fasta_records = parse_fasta_document(
        _workflow_fixture("biological_report_reference.fasta").read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    ).accepted_records
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
            member_kind=ComplexMemberKind.GENE,
            member_id="SIGB",
        ),
        ComplexMembershipRecord(
            complex_id="custom:triad",
            complex_name="Signal triad",
            source_name="custom",
            source_accession="CMPLX-01",
            member_kind=ComplexMemberKind.PROTEIN,
            member_id="O14920",
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
        fasta_records=fasta_records,
        policy=ComplexActivityPolicy(minimum_observed_member_count=2),
    )

    assert report.summary.complex_count == 2
    assert report.summary.condition_count == 2
    assert report.summary.condition_comparison_count == 2
    triad_scores = {
        entry.sample_id: entry
        for entry in report.sample_scores
        if entry.complex_id == "custom:triad"
    }
    assert triad_scores["T1"].activity_score is not None
    assert triad_scores["C1"].activity_score is not None
    assert triad_scores["T1"].activity_score > triad_scores["C1"].activity_score
    assert triad_scores["T1"].observed_member_count == 3
    assert triad_scores["T1"].confidence_status.value == "high"
    assert triad_scores["T1"].limiting_member_ids
    sparse_scores = {
        entry.sample_id: entry
        for entry in report.sample_scores
        if entry.complex_id == "custom:sparse"
    }
    assert sparse_scores["C1"].observed_member_count == 1
    assert sparse_scores["C1"].missing_member_count == 1
    assert sparse_scores["C1"].confidence_status.value == "low"
    assert sparse_scores["C1"].confidence_reason == (
        "observed member count 1 was below minimum 2"
    )
    triad_comparison = next(
        entry
        for entry in report.condition_comparisons
        if entry.complex_id == "custom:triad"
        and entry.condition_a == "control"
        and entry.condition_b == "treatment"
    )
    assert triad_comparison.activity_score_delta is not None
    assert triad_comparison.activity_score_delta > 0.0
    assert triad_comparison.condition_b_limiting_member_ids
    assert any(
        entry.member_kind is ComplexMemberKind.GENE and entry.observed
        for entry in report.member_contributions
    )
    assert any(
        entry.member_id == "Q99999"
        and "not present in the quantification table" in entry.reason
        for entry in report.unresolved_members
    )
