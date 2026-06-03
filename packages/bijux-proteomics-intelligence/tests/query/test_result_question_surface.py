# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.workflow.interactive_result_bundle import (
    InteractiveResultBundle,
    InteractiveResultBundleSummary,
    InteractiveResultPathway,
    InteractiveResultProtein,
    InteractiveResultPtmSite,
    InteractiveResultQcEntry,
    InteractiveResultQcKind,
    InteractiveResultSample,
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
from bijux_proteomics_intelligence.query import (
    ResultQuestionKind,
    ResultQuestionSpec,
    ResultQuestionStatus,
    answer_result_question,
    render_result_question_answers_tsv,
)


def test_answer_result_question_returns_ids_for_every_supported_spec() -> None:
    result = _study_result_fixture()

    why_significant = answer_result_question(
        result,
        ResultQuestionSpec(
            question_id="q-why-significant",
            question_kind=ResultQuestionKind.WHY_SIGNIFICANT,
            subject_id="protein:pg1",
        ),
    )
    why_rejected = answer_result_question(
        result,
        ResultQuestionSpec(
            question_id="q-why-rejected",
            question_kind=ResultQuestionKind.WHY_REJECTED,
            subject_id="claim-rejected-1",
        ),
    )
    what_peptides_support = answer_result_question(
        result,
        ResultQuestionSpec(
            question_id="q-peptides",
            question_kind=ResultQuestionKind.WHAT_PEPTIDES_SUPPORT,
            subject_id="protein:pg1",
        ),
    )
    what_samples_failed = answer_result_question(
        result,
        ResultQuestionSpec(
            question_id="q-samples-failed",
            question_kind=ResultQuestionKind.WHAT_SAMPLES_FAILED,
        ),
    )
    what_weakens_claim = answer_result_question(
        result,
        ResultQuestionSpec(
            question_id="q-weakens-claim",
            question_kind=ResultQuestionKind.WHAT_WEAKENS_CLAIM,
            subject_id="P11111:S5:Phospho",
        ),
    )

    answers = (
        why_significant,
        why_rejected,
        what_peptides_support,
        what_samples_failed,
        what_weakens_claim,
    )
    assert all(answer.status is ResultQuestionStatus.ANSWERED for answer in answers)
    assert all(answer.referenced_ids for answer in answers)
    assert why_significant.referenced_ids == (
        "protein:pg1",
        "pep-1",
        "pep-2",
        "graph:protein:pg1",
    )
    assert why_rejected.referenced_ids == (
        "claim-rejected-1",
        "pathway:stress_response",
    )
    assert what_peptides_support.referenced_ids == ("pep-1", "pep-2")
    assert what_samples_failed.referenced_ids == ("S2", "qc-run-1")
    assert what_weakens_claim.referenced_ids == (
        "low_localization",
        "missing_protein_baseline",
        "claim:ptm:1",
    )


def test_render_result_question_answers_tsv_preserves_id_fields() -> None:
    result = _study_result_fixture()
    answer = answer_result_question(
        result,
        ResultQuestionSpec(
            question_id="q-samples-failed",
            question_kind=ResultQuestionKind.WHAT_SAMPLES_FAILED,
        ),
    )

    assert render_result_question_answers_tsv((answer,)).splitlines()[0] == (
        "question_id\tquestion_kind\tstatus\tsubject_id\tanswer_text\treferenced_ids\tnote"
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
                summary_text="rejected from final narrative because the pathway failed one or more evidence checks",
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
            samples=(
                InteractiveResultSample(
                    sample_id="S1", condition="control", outlier=False
                ),
                InteractiveResultSample(
                    sample_id="S2",
                    condition="treated",
                    outlier=True,
                    outlier_reasons=("run_qc_fail",),
                ),
            ),
            proteins=(
                InteractiveResultProtein(
                    object_id="protein:pg1",
                    representative_protein_ref="P11111",
                    condition_a="control",
                    condition_b="treated",
                    log2_fold_change=1.4,
                    adjusted_p_value=0.01,
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
                    adjusted_p_value=0.02,
                    log2_fold_change=1.7,
                    warning_codes=("low_localization", "missing_protein_baseline"),
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
