# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.interpretation import (
    PathwayActivityPolicy,
    PathwayMemberKind,
    PathwayMembershipRecord,
    build_pathway_activity_report,
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


def test_build_pathway_activity_report_scores_pathways_with_member_coverage() -> None:
    design_entries = parse_experimental_design_table(
        _workflow_fixture("biological_report.design.tsv")
    ).accepted_entries
    fasta_records = parse_fasta_document(
        _workflow_fixture("biological_report_reference.fasta").read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    ).accepted_records
    pathway_records = (
        PathwayMembershipRecord(
            pathway_id="custom:response",
            pathway_name="Stress response pathway",
            source_name="custom",
            source_accession="BIO-01",
            member_kind=PathwayMemberKind.PROTEIN,
            member_id="P04637",
        ),
        PathwayMembershipRecord(
            pathway_id="custom:response",
            pathway_name="Stress response pathway",
            source_name="custom",
            source_accession="BIO-01",
            member_kind=PathwayMemberKind.PROTEIN,
            member_id="O14920",
        ),
        PathwayMembershipRecord(
            pathway_id="custom:response",
            pathway_name="Stress response pathway",
            source_name="custom",
            source_accession="BIO-01",
            member_kind=PathwayMemberKind.GENE,
            member_id="SIGB",
        ),
        PathwayMembershipRecord(
            pathway_id="custom:sparse",
            pathway_name="Sparse pathway",
            source_name="custom",
            source_accession="BIO-02",
            member_kind=PathwayMemberKind.PROTEIN,
            member_id="P04637",
        ),
        PathwayMembershipRecord(
            pathway_id="custom:sparse",
            pathway_name="Sparse pathway",
            source_name="custom",
            source_accession="BIO-02",
            member_kind=PathwayMemberKind.PROTEIN,
            member_id="Q99999",
        ),
    )

    report = build_pathway_activity_report(
        _build_fixture_table(),
        pathway_records,
        design_entries=design_entries,
        fasta_records=fasta_records,
        policy=PathwayActivityPolicy(minimum_observed_member_count=2),
    )

    assert report.summary.pathway_count == 2
    assert report.summary.condition_count == 2
    assert report.summary.condition_comparison_count == 2
    response_scores = {
        entry.sample_id: entry
        for entry in report.sample_scores
        if entry.pathway_id == "custom:response"
    }
    assert response_scores["T1"].activity_score is not None
    assert response_scores["C1"].activity_score is not None
    assert response_scores["T1"].activity_score > response_scores["C1"].activity_score
    assert response_scores["T1"].observed_member_count == 3
    assert response_scores["T1"].confidence_status.value == "high"
    sparse_scores = {
        entry.sample_id: entry
        for entry in report.sample_scores
        if entry.pathway_id == "custom:sparse"
    }
    assert sparse_scores["C1"].observed_member_count == 1
    assert sparse_scores["C1"].missing_member_count == 1
    assert sparse_scores["C1"].confidence_status.value == "low"
    assert sparse_scores["C1"].confidence_reason == (
        "observed member count 1 was below minimum 2"
    )
    assert report.summary.low_confidence_sample_score_count >= 1
    assert any(
        entry.member_kind is PathwayMemberKind.GENE and entry.observed
        for entry in report.member_contributions
    )
    assert any(
        entry.member_id == "Q99999"
        and "not present in the quantification table" in entry.reason
        for entry in report.unresolved_members
    )
