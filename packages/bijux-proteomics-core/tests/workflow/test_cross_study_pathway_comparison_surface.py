# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import PathwayMemberKind
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    build_proteomics_study_result,
    build_tmt_experiment_workflow_bundle,
)
from bijux_proteomics.workflow.cross_study_pathway_comparison import (
    CrossStudyPathwayComparisonStatus,
    CrossStudyPathwayContrastAlignmentStatus,
    CrossStudyPathwayDirection,
    CrossStudyPathwayObservation,
    CrossStudyPathwaySignalKind,
    build_cross_study_pathway_comparison_report_from_observations,
    extract_cross_study_pathway_observations,
    render_cross_study_opposite_pathway_signal_tsv,
    render_cross_study_pathway_comparison_tsv,
    render_cross_study_shared_pathway_signal_tsv,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinStudyInput,
)
from bijux_proteomics.workflow.study_result import ProteomicsStudyKind


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _multiplex_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / name


def test_extract_cross_study_pathway_observations_preserves_activity_and_enrichment_surfaces() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    biological_report = build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    tmt_workflow = build_tmt_experiment_workflow_bundle(
        _multiplex_fixture("maxquant_tmt_evidence.tsv"),
        _multiplex_fixture("tmt.design.tsv"),
        control_channel="126",
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )

    extraction = extract_cross_study_pathway_observations(
        (
            CrossStudyProteinStudyInput(
                study_id="label_free_study",
                study_result=build_proteomics_study_result(biological_report),
            ),
            CrossStudyProteinStudyInput(
                study_id="tmt_study",
                study_result=build_proteomics_study_result(tmt_workflow),
            ),
        )
    )

    assert extraction.summary.supported_study_count == 1
    assert extraction.summary.unsupported_study_count == 1
    assert extraction.summary.observation_count == 2
    assert extraction.summary.activity_observation_count == 1
    assert extraction.summary.enrichment_observation_count == 1
    assert extraction.unsupported_studies[0].study_id == "tmt_study"
    assert {entry.signal_kind for entry in extraction.observations} == {
        CrossStudyPathwaySignalKind.ACTIVITY,
        CrossStudyPathwaySignalKind.ENRICHMENT,
    }
    assert {entry.coverage_fraction for entry in extraction.observations} == {1.0}


def test_extract_cross_study_pathway_observations_marks_missing_pathway_surfaces_unsupported() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    biological_report = build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )

    extraction = extract_cross_study_pathway_observations(
        (
            CrossStudyProteinStudyInput(
                study_id="label_free_without_pathways",
                study_result=build_proteomics_study_result(biological_report),
            ),
        )
    )

    assert extraction.summary.supported_study_count == 0
    assert extraction.summary.unsupported_study_count == 1
    assert extraction.summary.observation_count == 0
    assert extraction.unsupported_studies[0].study_id == "label_free_without_pathways"


def test_cross_study_pathway_comparison_reports_shared_enrichment_and_coverage_differences() -> (
    None
):
    report = build_cross_study_pathway_comparison_report_from_observations(
        (
            CrossStudyPathwayObservation(
                observation_id="study_a:enrichment:stress_response",
                study_id="study_a",
                study_label="study a",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                signal_kind=CrossStudyPathwaySignalKind.ENRICHMENT,
                pathway_id="reactome:stress_response",
                pathway_name="Stress response",
                source_name="reactome",
                source_accession="R-HSA-123",
                member_kind=PathwayMemberKind.PROTEIN,
                p_value=0.001,
                adjusted_p_value=0.01,
                enrichment_ratio=2.3,
                significant=True,
                total_member_count=20,
                foreground_overlap_count=9,
                background_member_count=10,
                coverage_fraction=0.9,
                note="study a enrichment",
            ),
            CrossStudyPathwayObservation(
                observation_id="study_b:enrichment:stress_response",
                study_id="study_b",
                study_label="study b",
                study_kind=ProteomicsStudyKind.DIA,
                signal_kind=CrossStudyPathwaySignalKind.ENRICHMENT,
                pathway_id="reactome:stress_response",
                pathway_name="Stress response",
                source_name="reactome",
                source_accession="R-HSA-123",
                member_kind=PathwayMemberKind.PROTEIN,
                p_value=0.004,
                adjusted_p_value=0.03,
                enrichment_ratio=1.8,
                significant=True,
                total_member_count=18,
                foreground_overlap_count=5,
                background_member_count=10,
                coverage_fraction=0.5,
                note="study b enrichment",
            ),
        )
    )

    comparison = report.comparisons[0]
    assert (
        comparison.comparison_id
        == "enrichment_pathway_r_hsa_123_reactome_stress_response_protein"
    )
    assert (
        comparison.comparison_status is CrossStudyPathwayComparisonStatus.SHARED_SIGNAL
    )
    assert comparison.shared_signal is True
    assert comparison.minimum_coverage_fraction == 0.5
    assert comparison.maximum_coverage_fraction == 0.9
    assert comparison.coverage_fraction_range == 0.4
    assert comparison.minimum_total_member_count == 18
    assert comparison.maximum_total_member_count == 20
    assert "shared_signal" in render_cross_study_shared_pathway_signal_tsv(report)
    assert "coverage_fraction_range" in render_cross_study_pathway_comparison_tsv(
        report
    )


def test_cross_study_pathway_comparison_marks_opposite_activity_after_reversed_contrast_normalization() -> (
    None
):
    report = build_cross_study_pathway_comparison_report_from_observations(
        (
            CrossStudyPathwayObservation(
                observation_id="study_a:activity:response",
                study_id="study_a",
                study_label="study a",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                signal_kind=CrossStudyPathwaySignalKind.ACTIVITY,
                pathway_id="custom:response",
                pathway_name="Stress response pathway",
                source_name="custom",
                source_accession="BIO-01",
                condition_a="treated",
                condition_b="control",
                direction=CrossStudyPathwayDirection.UP,
                activity_score_delta=0.8,
                significant=True,
                total_member_count=3,
                condition_a_coverage_fraction=1.0,
                condition_b_coverage_fraction=0.9,
                coverage_fraction=0.95,
                note="study a activity",
            ),
            CrossStudyPathwayObservation(
                observation_id="study_b:activity:response",
                study_id="study_b",
                study_label="study b",
                study_kind=ProteomicsStudyKind.DIA,
                signal_kind=CrossStudyPathwaySignalKind.ACTIVITY,
                pathway_id="custom:response",
                pathway_name="Stress response pathway",
                source_name="custom",
                source_accession="BIO-01",
                condition_a="control",
                condition_b="treated",
                direction=CrossStudyPathwayDirection.UP,
                activity_score_delta=0.7,
                significant=True,
                total_member_count=4,
                condition_a_coverage_fraction=0.8,
                condition_b_coverage_fraction=0.7,
                coverage_fraction=0.75,
                note="study b reversed-order activity",
            ),
        )
    )

    comparison = report.comparisons[0]
    assert (
        comparison.contrast_alignment_status
        is CrossStudyPathwayContrastAlignmentStatus.REVERSED_ORDER_NORMALIZED
    )
    assert (
        comparison.comparison_status
        is CrossStudyPathwayComparisonStatus.OPPOSITE_SIGNAL
    )
    assert comparison.opposite_signal is True
    assert set(comparison.normalized_significant_directions) == {
        CrossStudyPathwayDirection.UP,
        CrossStudyPathwayDirection.DOWN,
    }
    assert "opposite_signal" in render_cross_study_opposite_pathway_signal_tsv(report)


def test_cross_study_pathway_comparison_keeps_heterogeneous_activity_contrasts_separate() -> (
    None
):
    report = build_cross_study_pathway_comparison_report_from_observations(
        (
            CrossStudyPathwayObservation(
                observation_id="study_a:activity:response",
                study_id="study_a",
                study_label="study a",
                study_kind=ProteomicsStudyKind.LABEL_FREE,
                signal_kind=CrossStudyPathwaySignalKind.ACTIVITY,
                pathway_id="custom:response",
                pathway_name="Stress response pathway",
                source_name="custom",
                source_accession="BIO-01",
                condition_a="treated",
                condition_b="control",
                direction=CrossStudyPathwayDirection.UP,
                activity_score_delta=0.8,
                significant=True,
                total_member_count=3,
                condition_a_coverage_fraction=1.0,
                condition_b_coverage_fraction=1.0,
                coverage_fraction=1.0,
                note="study a activity",
            ),
            CrossStudyPathwayObservation(
                observation_id="study_b:activity:response",
                study_id="study_b",
                study_label="study b",
                study_kind=ProteomicsStudyKind.TMT,
                signal_kind=CrossStudyPathwaySignalKind.ACTIVITY,
                pathway_id="custom:response",
                pathway_name="Stress response pathway",
                source_name="custom",
                source_accession="BIO-01",
                condition_a="resistant",
                condition_b="sensitive",
                direction=CrossStudyPathwayDirection.UP,
                activity_score_delta=0.9,
                significant=True,
                total_member_count=3,
                condition_a_coverage_fraction=0.8,
                condition_b_coverage_fraction=0.8,
                coverage_fraction=0.8,
                note="study b different contrast",
            ),
        )
    )

    comparison = report.comparisons[0]
    assert (
        comparison.contrast_alignment_status
        is CrossStudyPathwayContrastAlignmentStatus.HETEROGENEOUS_CONTRASTS
    )
    assert (
        comparison.comparison_status
        is CrossStudyPathwayComparisonStatus.HETEROGENEOUS_CONTRASTS
    )
    assert "heterogeneous_contrasts" in render_cross_study_pathway_comparison_tsv(
        report
    )
