# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review.evidence_graph_confidence import (
    EvidenceGraphConfidenceEntry,
    EvidenceGraphConfidenceReport,
    EvidenceGraphConfidenceTier,
)
from bijux_proteomics.review.evidence_graph import ProteomicsEvidenceNodeKind
from bijux_proteomics.study.design_validity import (
    ExperimentDesignValidityIssue,
    ExperimentDesignValidityReport,
    ExperimentDesignValiditySummary,
)
from bijux_proteomics.study.experiment_design import (
    ExperimentDesign,
    ExperimentDesignSample,
    ExperimentDesignSummary,
)
from bijux_proteomics_runtime.checkpoints import (
    ScientificCheckpointConfidenceStatus,
    ScientificCheckpointDecision,
    ScientificCheckpointInput,
    ScientificCheckpointQcStatus,
    ScientificCheckpointStage,
    ScientificStageSummary,
    build_scientific_checkpoints,
)


def _design(valid: bool) -> ExperimentDesignValidityReport:
    design = ExperimentDesign(
        entries=(),
        samples=(
            ExperimentDesignSample(
                sample_id="S1",
                condition="control",
                run_ids=("run-1",),
                technical_replicate_ids=("run-1",),
            ),
            ExperimentDesignSample(
                sample_id="S2",
                condition="treated",
                run_ids=("run-2",),
                technical_replicate_ids=("run-2",),
            ),
        ),
        runs=(),
        conditions=("control", "treated"),
        batches=(),
        pair_ids=(),
        timepoints=(),
        species=(),
        tissue_or_cell_types=(),
        perturbations=(),
        instruments=(),
        plexes=(),
        summary=ExperimentDesignSummary(
            sample_count=2,
            run_count=2,
            technical_replicate_count=2,
            condition_count=2,
            batch_count=0,
            pair_count=0,
            timepoint_count=0,
            plex_count=0,
            channel_count=0,
            species_count=0,
            tissue_or_cell_type_count=0,
            perturbation_count=0,
            instrument_count=0,
        ),
        note="test design",
    )
    issues = (
        ()
        if valid
        else (
            ExperimentDesignValidityIssue(
                code="invalid_contrast_missing_condition",
                message="treated condition is not supported by the submitted design",
                condition_ids=("treated",),
            ),
        )
    )
    return ExperimentDesignValidityReport(
        experiment_design=design,
        selected_conditions=("control", "treated"),
        issues=issues,
        summary=ExperimentDesignValiditySummary(
            issue_count=len(issues),
            sample_identity_conflict_count=0,
            duplicate_run_id_count=0,
            invalid_contrast_count=0 if valid else 1,
            confounded_batch_condition_count=0,
            broken_pair_count=0,
            missing_channel_count=0,
            missing_timepoint_order_count=0,
            valid_for_differential_analysis=valid,
        ),
        note="test design validity surface",
    )


def _biology_confidence(*tiers: EvidenceGraphConfidenceTier) -> EvidenceGraphConfidenceReport:
    entries = tuple(
        EvidenceGraphConfidenceEntry(
            claim_node_id=f"claim-{index}",
            claim_node_ref=f"claim-ref-{index}",
            subject_node_id=f"subject-{index}",
            subject_node_ref=f"subject-ref-{index}",
            subject_node_kind=ProteomicsEvidenceNodeKind.PROTEIN,
            propagated_score=0.9 if tier is EvidenceGraphConfidenceTier.HIGH else 0.2,
            confidence_tier=tier,
            upstream_node_ids=(),
            source_row_refs=(),
            rationale="test evidence confidence",
        )
        for index, tier in enumerate(tiers, start=1)
    )
    tier_counts: dict[str, int] = {}
    for entry in entries:
        tier_counts[entry.confidence_tier.value] = (
            tier_counts.get(entry.confidence_tier.value, 0) + 1
        )
    return EvidenceGraphConfidenceReport(
        entries=entries,
        entry_count=len(entries),
        tier_counts=tier_counts,
    )


def _stage(entity_count: int, rejected_count: int = 0) -> ScientificStageSummary:
    return ScientificStageSummary(
        entity_counts={"rows": entity_count},
        rejected_counts={"rows": rejected_count},
    )


def test_invalid_design_blocks_statistics_and_biology() -> None:
    report = build_scientific_checkpoints(
        ScientificCheckpointInput(
            workflow_id="lfq-invalid-design",
            import_stage=_stage(120, 3),
            qc_stage=_stage(118, 2),
            quantification_stage=_stage(90, 5),
            statistics_stage=_stage(0, 0),
            biology_stage=_stage(0, 0),
            qc_status=ScientificCheckpointQcStatus.PASS,
            design_validity=_design(False),
            biology_confidence=_biology_confidence(EvidenceGraphConfidenceTier.HIGH),
        )
    )

    statistics_entry = next(
        entry
        for entry in report.entries
        if entry.stage is ScientificCheckpointStage.STATISTICS
    )
    biology_entry = next(
        entry
        for entry in report.entries
        if entry.stage is ScientificCheckpointStage.BIOLOGY
    )

    assert statistics_entry.decision is ScientificCheckpointDecision.BLOCK
    assert (
        statistics_entry.confidence_status
        is ScientificCheckpointConfidenceStatus.BLOCKED
    )
    assert "statistics" in report.blocked_stage_ids
    assert biology_entry.decision is ScientificCheckpointDecision.BLOCK
    assert biology_entry.note.startswith("biology is blocked")


def test_failed_qc_downgrades_final_biology_claims_without_blocking_execution() -> None:
    report = build_scientific_checkpoints(
        ScientificCheckpointInput(
            workflow_id="lfq-failed-qc",
            import_stage=_stage(120, 3),
            qc_stage=_stage(118, 7),
            quantification_stage=_stage(90, 5),
            statistics_stage=_stage(65, 8),
            biology_stage=_stage(12, 1),
            qc_status=ScientificCheckpointQcStatus.FAIL,
            design_validity=_design(True),
            biology_confidence=_biology_confidence(EvidenceGraphConfidenceTier.HIGH),
        )
    )

    biology_entry = next(
        entry
        for entry in report.entries
        if entry.stage is ScientificCheckpointStage.BIOLOGY
    )
    statistics_entry = next(
        entry
        for entry in report.entries
        if entry.stage is ScientificCheckpointStage.STATISTICS
    )

    assert statistics_entry.decision is ScientificCheckpointDecision.CONTINUE
    assert biology_entry.decision is ScientificCheckpointDecision.CONTINUE
    assert (
        biology_entry.confidence_status
        is ScientificCheckpointConfidenceStatus.DOWNGRADED
    )
    assert "biology" in report.downgraded_stage_ids
    assert "QC failed" in biology_entry.note
