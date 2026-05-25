# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.next_steps import (
    NextExperimentRecommendationEntry,
    NextExperimentRecommendationType,
    recommend_next_experiments,
    render_next_experiments_tsv,
)
from bijux_proteomics.workflow.interactive_result_bundle import (
    InteractiveResultBundle,
    InteractiveResultBundleSummary,
    InteractiveResultPathway,
    InteractiveResultProtein,
    InteractiveResultPtmSite,
    InteractiveResultQcEntry,
    InteractiveResultQcKind,
)
from bijux_proteomics.workflow.study_result import (
    ProteomicsStudyConclusionEntry,
    ProteomicsStudyConclusionKind,
    ProteomicsStudyDesignEntry,
    ProteomicsStudyDesignSnapshot,
    ProteomicsStudyKind,
    ProteomicsStudyResult,
    ProteomicsStudyResultSummary,
)


def test_recommend_next_experiments_keeps_each_follow_up_linked_to_specific_trigger() -> (
    None
):
    report = recommend_next_experiments(_study_result_fixture())

    assert report.entries == (
        NextExperimentRecommendationEntry(
            recommendation_id="pathway_member_resolution:pathway:stress_response",
            entity_id="pathway:stress_response",
            recommendation_type=(
                NextExperimentRecommendationType.PATHWAY_MEMBER_RESOLUTION
            ),
            triggering_evidence=(
                "pathway:stress_response",
                "P11111",
                "member:missing-1",
            ),
            required_inputs=(
                "member_target_list",
                "orthogonal_member_assay",
                "pathway_context_review",
            ),
        ),
        NextExperimentRecommendationEntry(
            recommendation_id="ptm_relocalization:P11111:S5:Phospho",
            entity_id="P11111:S5:Phospho",
            recommendation_type=NextExperimentRecommendationType.PTM_RELOCALIZATION,
            triggering_evidence=(
                "P11111:S5:Phospho",
                "low_localization",
                "claim:ptm:1",
                "S2",
            ),
            required_inputs=(
                "site_localizing_fragmentation",
                "protein_baseline_matrix",
                "modified_peptide_review",
            ),
        ),
        NextExperimentRecommendationEntry(
            recommendation_id="rejected_claim_resolution:claim-rejected-1",
            entity_id="pathway:stress_response",
            recommendation_type=(
                NextExperimentRecommendationType.REJECTED_CLAIM_RESOLUTION
            ),
            triggering_evidence=(
                "claim-rejected-1",
                "pathway:stress_response",
                "claim_validation_report",
            ),
            required_inputs=(
                "missing_support_review",
                "orthogonal_resolution_assay",
            ),
        ),
        NextExperimentRecommendationEntry(
            recommendation_id="sample_qc_rerun:S2:qc-run-1",
            entity_id="S2",
            recommendation_type=NextExperimentRecommendationType.SAMPLE_QC_RERUN,
            triggering_evidence=("qc-run-1", "identification_rate_low"),
            required_inputs=(
                "sample_material",
                "instrument_method",
                "qc_failure_review",
            ),
        ),
        NextExperimentRecommendationEntry(
            recommendation_id="targeted_validation:P11111",
            entity_id="P11111",
            recommendation_type=NextExperimentRecommendationType.TARGETED_VALIDATION,
            triggering_evidence=("protein:pg1", "pep-1", "pep-2", "graph:protein:pg1"),
            required_inputs=(
                "target_peptide_panel",
                "transition_design",
                "orthogonal_quant_readout",
            ),
        ),
    )
    assert report.summary.recommendation_count == 5
    assert report.summary.pathway_member_resolution_count == 1
    assert report.summary.ptm_relocalization_count == 1
    assert report.summary.rejected_claim_resolution_count == 1
    assert report.summary.sample_qc_rerun_count == 1
    assert report.summary.targeted_validation_count == 1


def test_render_next_experiments_tsv_preserves_required_fields() -> None:
    report = recommend_next_experiments(_study_result_fixture())

    assert render_next_experiments_tsv(report.entries).splitlines()[0] == (
        "recommendation_id\tentity_id\trecommendation_type\ttriggering_evidence\trequired_inputs"
    )


def _study_result_fixture() -> ProteomicsStudyResult:
    return ProteomicsStudyResult(
        study_kind=ProteomicsStudyKind.ARCHIVED,
        source_surface="fixture",
        design=ProteomicsStudyDesignSnapshot(
            entries=(
                ProteomicsStudyDesignEntry(sample_id="S1", condition="control"),
                ProteomicsStudyDesignEntry(sample_id="S2", condition="treated"),
            ),
            sample_count=2,
            condition_count=2,
            batch_count=0,
            paired_sample_count=0,
            multiplexed_sample_count=0,
            note="fixture design",
        ),
        biological_conclusions=(
            ProteomicsStudyConclusionEntry(
                conclusion_id="claim-rejected-1",
                kind=ProteomicsStudyConclusionKind.REJECTED_CLAIM,
                subject_id="pathway:stress_response",
                subject_label="stress response",
                status="rejected",
                score=0.2,
                evidence_surface="claim_validation_report",
                summary_text="pathway claim was rejected from the final report",
            ),
        ),
        interactive_result_bundle=InteractiveResultBundle(
            source_reports=(),
            summary=InteractiveResultBundleSummary(
                biological_report_available=True,
                ptm_report_available=True,
                run_qc_input_count=1,
                sample_count=2,
                protein_count=1,
                peptide_count=0,
                ptm_site_count=1,
                pathway_count=1,
                qc_entry_count=1,
                card_count=0,
                graph_node_count=0,
                graph_edge_count=0,
                plot_count=0,
            ),
            samples=(),
            proteins=(
                InteractiveResultProtein(
                    object_id="protein:pg1",
                    representative_protein_ref="P11111",
                    adjusted_p_value=0.01,
                    log2_fold_change=1.4,
                    significant=True,
                    peptide_ids=("pep-1", "pep-2"),
                    graph_node_ids=("graph:protein:pg1",),
                ),
            ),
            peptides=(),
            ptm_sites=(
                InteractiveResultPtmSite(
                    site_key="P11111:S5:Phospho",
                    protein_ref="P11111",
                    localization_tier="low",
                    adjusted_p_value=0.02,
                    warning_codes=("low_localization",),
                    claim_ids=("claim:ptm:1",),
                    sample_ids=("S2",),
                ),
            ),
            pathways=(
                InteractiveResultPathway(
                    pathway_id="pathway:stress_response",
                    adjusted_p_value=0.04,
                    supporting_protein_refs=("P11111",),
                    unresolved_member_ids=("member:missing-1",),
                ),
            ),
            qc_entries=(
                InteractiveResultQcEntry(
                    qc_id="qc-run-1",
                    qc_kind=InteractiveResultQcKind.RUN_QC_ASSESSMENT,
                    scope="sample",
                    entity_id="S2",
                    status="failed",
                    severity="failed",
                    reason_codes=("identification_rate_low",),
                    message="sample failed run QC",
                    source_surface="run_qc_assessment",
                ),
            ),
            cards=(),
            graph_nodes=(),
            graph_edges=(),
            plots=(),
            note="fixture interactive bundle",
        ),
        summary=ProteomicsStudyResultSummary(
            design_entry_count=2,
            matrix_surface_count=0,
            statistic_surface_count=0,
            qc_surface_count=0,
            card_surface_count=0,
            conclusion_count=1,
        ),
        note="fixture study result",
    )
