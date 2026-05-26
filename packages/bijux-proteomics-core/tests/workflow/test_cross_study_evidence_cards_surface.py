# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.interpretation import PathwayMemberKind
from bijux_proteomics.workflow.cross_study_effect_comparison import (
    CrossStudyEffectDirection,
    CrossStudyProteinEffectObservation,
    build_cross_study_effect_comparison_report_from_observations,
)
from bijux_proteomics.workflow.cross_study_evidence_cards import (
    CrossStudyEvidenceCardStatus,
    CrossStudyEvidenceDatasetState,
    build_cross_study_evidence_card_report,
    render_cross_study_evidence_card_tsv,
    render_cross_study_evidence_dataset_tsv,
)
from bijux_proteomics.workflow.cross_study_meta_analysis import (
    build_cross_study_meta_analysis_report_from_observations,
)
from bijux_proteomics.workflow.cross_study_pathway_comparison import (
    CrossStudyPathwayObservation,
    CrossStudyPathwaySignalKind,
    build_cross_study_pathway_comparison_report_from_observations,
)
from bijux_proteomics.workflow.cross_study_protein_harmonization import (
    CrossStudyProteinObservationSourceKind,
)
from bijux_proteomics.workflow.public_benchmark_runner import (
    PublicBenchmarkSuiteReport,
)
from bijux_proteomics.workflow.public_dataset_comparison import (
    PublicDatasetComparisonDatasetStatus,
    PublicDatasetComparisonDatasetSummary,
    PublicDatasetComparisonFailureEntry,
    PublicDatasetComparisonReport,
    PublicDatasetComparisonSummary,
)
from bijux_proteomics.workflow.study_result import ProteomicsStudyKind


def _suite_report(*, passed_count: int, failed_count: int) -> PublicBenchmarkSuiteReport:
    return PublicBenchmarkSuiteReport(
        benchmark_root="synthetic_benchmarks",
        output_root="synthetic_runs",
        runs=(),
        passed_count=passed_count,
        failed_count=failed_count,
        note="synthetic suite",
    )


def _dataset_summary(
    *,
    dataset_id: str,
    status: PublicDatasetComparisonDatasetStatus,
    condition_a: str = "treated",
    condition_b: str = "control",
    failure_count: int = 0,
) -> PublicDatasetComparisonDatasetSummary:
    return PublicDatasetComparisonDatasetSummary(
        dataset_id=dataset_id,
        accession=f"synthetic:{dataset_id}",
        species="Homo sapiens",
        search_engine="lfq",
        condition_a=condition_a,
        condition_b=condition_b,
        status=status,
        failure_count=failure_count,
        study_kind=ProteomicsStudyKind.LABEL_FREE
        if status is PublicDatasetComparisonDatasetStatus.PASSED
        else None,
        design_entry_count=4 if status is PublicDatasetComparisonDatasetStatus.PASSED else None,
        significant_entity_count=1
        if status is PublicDatasetComparisonDatasetStatus.PASSED
        else None,
        protein_card_count=1 if status is PublicDatasetComparisonDatasetStatus.PASSED else None,
        conclusion_count=1 if status is PublicDatasetComparisonDatasetStatus.PASSED else None,
        effect_comparison_supported=status is PublicDatasetComparisonDatasetStatus.PASSED,
        pathway_comparison_supported=status is PublicDatasetComparisonDatasetStatus.PASSED,
        note="synthetic dataset summary",
    )


def test_cross_study_evidence_cards_preserve_conflicting_protein_and_failed_dataset_visibility() -> (
    None
):
    observations = (
        CrossStudyProteinEffectObservation(
            observation_id="study_a:protein_1",
            study_id="study_a",
            study_label="study a",
            study_kind=ProteomicsStudyKind.LABEL_FREE,
            species="Homo sapiens",
            source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
            source_surface="protein_cards",
            source_entity_id="protein_1",
            representative_protein_ref="P11111",
            protein_refs=("P11111",),
            accession_aliases=(),
            gene_symbol="STAT1",
            condition_a="treated",
            condition_b="control",
            log2_fold_change=1.2,
            direction=CrossStudyEffectDirection.UP,
            p_value=0.001,
            adjusted_p_value=0.01,
            standard_error=0.2,
            confidence_interval_low=0.808,
            confidence_interval_high=1.592,
            robustness_score=0.8,
            significant=True,
            note="study a effect",
        ),
        CrossStudyProteinEffectObservation(
            observation_id="study_b:protein_1",
            study_id="study_b",
            study_label="study b",
            study_kind=ProteomicsStudyKind.DIA,
            species="Homo sapiens",
            source_kind=CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
            source_surface="protein_cards",
            source_entity_id="protein_1",
            representative_protein_ref="A0A0HUMAN1",
            protein_refs=("A0A0HUMAN1",),
            accession_aliases=("P11111",),
            gene_symbol="STAT1",
            condition_a="treated",
            condition_b="control",
            log2_fold_change=-1.1,
            direction=CrossStudyEffectDirection.DOWN,
            p_value=0.002,
            adjusted_p_value=0.02,
            standard_error=0.3,
            confidence_interval_low=-1.688,
            confidence_interval_high=-0.512,
            robustness_score=0.7,
            significant=True,
            note="study b effect",
        ),
    )
    effect_report = build_cross_study_effect_comparison_report_from_observations(
        observations,
        input_study_count=2,
    )
    meta_report = build_cross_study_meta_analysis_report_from_observations(
        observations,
        input_study_count=2,
    )
    comparison_report = PublicDatasetComparisonReport(
        benchmark_root="synthetic_benchmarks",
        run_output_root="synthetic_runs",
        suite_report=_suite_report(passed_count=2, failed_count=1),
        dataset_summaries=(
            _dataset_summary(
                dataset_id="study_a",
                status=PublicDatasetComparisonDatasetStatus.PASSED,
            ),
            _dataset_summary(
                dataset_id="study_b",
                status=PublicDatasetComparisonDatasetStatus.PASSED,
            ),
            _dataset_summary(
                dataset_id="study_failed",
                status=PublicDatasetComparisonDatasetStatus.FAILED,
                failure_count=1,
            ),
        ),
        failure_entries=(
            PublicDatasetComparisonFailureEntry(
                dataset_id="study_failed",
                accession="synthetic:study_failed",
                search_engine="lfq",
                failure_kind="missing_required_schema",
                subject="protein_groups_txt",
                message="synthetic missing bundle",
            ),
        ),
        effect_comparison_report=effect_report,
        meta_analysis_report=meta_report,
        pathway_comparison_report=None,
        summary=PublicDatasetComparisonSummary(
            descriptor_count=3,
            passed_dataset_count=2,
            failed_dataset_count=1,
            failure_entry_count=1,
            successful_study_count=2,
            effect_support_study_count=2,
            pathway_support_study_count=0,
            combined_effect_group_count=1,
            replicated_effect_group_count=0,
            meta_analysis_entry_count=1,
            combined_pathway_comparison_count=0,
            shared_pathway_signal_count=0,
        ),
        note="synthetic comparison report",
    )

    report = build_cross_study_evidence_card_report(comparison_report)

    assert report.summary.card_count == 1
    card = report.cards[0]
    assert card.card_id == "cross-study-protein-card:harmonized_protein_001"
    assert card.final_status is CrossStudyEvidenceCardStatus.CONFLICTING_DATASETS
    assert card.positive_dataset_ids == ("study_a",)
    assert card.negative_dataset_ids == ("study_b",)
    assert card.significant_dataset_ids == ("study_a", "study_b")
    assert card.failed_dataset_ids == ("study_failed",)
    assert card.source_row_refs == ()
    assert card.derived_no_source_reason is not None
    assert {
        entry.dataset_state for entry in card.dataset_entries
    } == {
        CrossStudyEvidenceDatasetState.POSITIVE_SIGNAL,
        CrossStudyEvidenceDatasetState.NEGATIVE_SIGNAL,
        CrossStudyEvidenceDatasetState.DATASET_FAILED,
    }
    assert "conflicting_datasets" in render_cross_study_evidence_card_tsv(report)
    assert "derived_no_source_reason" in render_cross_study_evidence_card_tsv(report)
    dataset_tsv = render_cross_study_evidence_dataset_tsv(report)
    assert "dataset_failed" in dataset_tsv
    assert "negative_signal" in dataset_tsv


def test_cross_study_evidence_cards_preserve_shared_pathway_signal_and_coverage_range() -> (
    None
):
    pathway_report = build_cross_study_pathway_comparison_report_from_observations(
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
                coverage_fraction=0.75,
                foreground_overlap_count=6,
                background_member_count=10,
                note="study b enrichment",
            ),
        ),
        input_study_count=2,
    )
    comparison_report = PublicDatasetComparisonReport(
        benchmark_root="synthetic_benchmarks",
        run_output_root="synthetic_runs",
        suite_report=_suite_report(passed_count=2, failed_count=0),
        dataset_summaries=(
            _dataset_summary(
                dataset_id="study_a",
                status=PublicDatasetComparisonDatasetStatus.PASSED,
            ),
            _dataset_summary(
                dataset_id="study_b",
                status=PublicDatasetComparisonDatasetStatus.PASSED,
            ),
        ),
        failure_entries=(),
        effect_comparison_report=None,
        meta_analysis_report=None,
        pathway_comparison_report=pathway_report,
        summary=PublicDatasetComparisonSummary(
            descriptor_count=2,
            passed_dataset_count=2,
            failed_dataset_count=0,
            failure_entry_count=0,
            successful_study_count=2,
            effect_support_study_count=0,
            pathway_support_study_count=2,
            combined_effect_group_count=0,
            replicated_effect_group_count=0,
            meta_analysis_entry_count=0,
            combined_pathway_comparison_count=1,
            shared_pathway_signal_count=1,
        ),
        note="synthetic comparison report",
    )

    report = build_cross_study_evidence_card_report(comparison_report)

    assert report.summary.card_count == 1
    card = report.cards[0]
    assert (
        card.card_id
        == "cross-study-pathway-card:enrichment_pathway_r_hsa_123_reactome_stress_response_protein"
    )
    assert card.subject_id == "reactome:stress_response"
    assert card.final_status is CrossStudyEvidenceCardStatus.CONSISTENT_REPLICATION
    assert card.significant_dataset_ids == ("study_a", "study_b")
    assert round(card.pathway_coverage_range or 0.0, 2) == 0.15
    assert card.failed_dataset_ids == ()
    assert "consistent_replication" in render_cross_study_evidence_card_tsv(report)
