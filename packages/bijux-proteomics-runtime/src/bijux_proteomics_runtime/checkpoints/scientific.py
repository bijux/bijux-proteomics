# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific stage checkpoints over import, QC, quantification, statistics, and biology."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.review.evidence_graph_confidence import (
    EvidenceGraphConfidenceReport,
)
from bijux_proteomics.study.design_validity import ExperimentDesignValidityReport
from bijux_proteomics_foundation import JsonModel


class ScientificCheckpointStage(StrEnum):
    """Scientific workflow stages that emit explicit runtime checkpoints."""

    IMPORT = "import"
    QC = "qc"
    QUANTIFICATION = "quantification"
    STATISTICS = "statistics"
    BIOLOGY = "biology"


class ScientificCheckpointQcStatus(StrEnum):
    """Compact QC posture preserved at each scientific checkpoint."""

    NOT_APPLICABLE = "not_applicable"
    PASSED = "pass"
    WARN = "warn"
    FAIL = "fail"


class ScientificCheckpointConfidenceStatus(StrEnum):
    """Confidence posture preserved at each scientific checkpoint."""

    NOT_APPLICABLE = "not_applicable"
    SUPPORTED = "supported"
    DOWNGRADED = "downgraded"
    BLOCKED = "blocked"


class ScientificCheckpointDecision(StrEnum):
    """Whether the scientific workflow should proceed past one checkpoint."""

    CONTINUE = "continue"
    BLOCK = "block"


class ScientificStageSummary(JsonModel):
    """Stable accepted and rejected counts for one scientific workflow stage."""

    model_config = ConfigDict(extra="forbid")

    entity_counts: dict[str, int] = Field(default_factory=dict)
    rejected_counts: dict[str, int] = Field(default_factory=dict)


class ScientificCheckpointInput(JsonModel):
    """Runtime-controlled scientific stage inputs evaluated into checkpoints."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    import_stage: ScientificStageSummary
    qc_stage: ScientificStageSummary
    quantification_stage: ScientificStageSummary
    statistics_stage: ScientificStageSummary
    biology_stage: ScientificStageSummary
    qc_status: ScientificCheckpointQcStatus = ScientificCheckpointQcStatus.PASSED
    design_validity: ExperimentDesignValidityReport
    biology_confidence: EvidenceGraphConfidenceReport | None = None


class ScientificCheckpointEntry(JsonModel):
    """One scientific checkpoint with explicit stage-level execution posture."""

    model_config = ConfigDict(extra="forbid")

    stage: ScientificCheckpointStage
    entity_counts: dict[str, int] = Field(default_factory=dict)
    rejected_counts: dict[str, int] = Field(default_factory=dict)
    qc_status: ScientificCheckpointQcStatus
    confidence_status: ScientificCheckpointConfidenceStatus
    decision: ScientificCheckpointDecision
    note: str = Field(..., min_length=1)


class ScientificCheckpointReport(JsonModel):
    """Reviewable scientific checkpoint ledger across a runtime workflow."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    entries: tuple[ScientificCheckpointEntry, ...] = Field(default_factory=tuple)
    blocked_stage_ids: tuple[str, ...] = Field(default_factory=tuple)
    downgraded_stage_ids: tuple[str, ...] = Field(default_factory=tuple)


def build_scientific_checkpoints(
    checkpoint_input: ScientificCheckpointInput,
) -> ScientificCheckpointReport:
    """Build scientific checkpoints that block invalid statistics and downgrade weak biology."""

    design_valid = (
        checkpoint_input.design_validity.summary.valid_for_differential_analysis
    )
    qc_status = checkpoint_input.qc_status
    statistics_blocked = not design_valid
    biology_downgraded = qc_status is ScientificCheckpointQcStatus.FAIL
    low_confidence_only = _biology_has_only_low_confidence(
        checkpoint_input.biology_confidence
    )

    entries = (
        ScientificCheckpointEntry(
            stage=ScientificCheckpointStage.IMPORT,
            entity_counts=dict(
                sorted(checkpoint_input.import_stage.entity_counts.items())
            ),
            rejected_counts=dict(
                sorted(checkpoint_input.import_stage.rejected_counts.items())
            ),
            qc_status=ScientificCheckpointQcStatus.NOT_APPLICABLE,
            confidence_status=ScientificCheckpointConfidenceStatus.NOT_APPLICABLE,
            decision=ScientificCheckpointDecision.CONTINUE,
            note="imported entities and rejected records are visible before scientific gating begins",
        ),
        ScientificCheckpointEntry(
            stage=ScientificCheckpointStage.QC,
            entity_counts=dict(sorted(checkpoint_input.qc_stage.entity_counts.items())),
            rejected_counts=dict(
                sorted(checkpoint_input.qc_stage.rejected_counts.items())
            ),
            qc_status=qc_status,
            confidence_status=(
                ScientificCheckpointConfidenceStatus.DOWNGRADED
                if qc_status is ScientificCheckpointQcStatus.FAIL
                else ScientificCheckpointConfidenceStatus.SUPPORTED
            ),
            decision=ScientificCheckpointDecision.CONTINUE,
            note=_qc_note(qc_status),
        ),
        ScientificCheckpointEntry(
            stage=ScientificCheckpointStage.QUANTIFICATION,
            entity_counts=dict(
                sorted(checkpoint_input.quantification_stage.entity_counts.items())
            ),
            rejected_counts=dict(
                sorted(checkpoint_input.quantification_stage.rejected_counts.items())
            ),
            qc_status=qc_status,
            confidence_status=(
                ScientificCheckpointConfidenceStatus.DOWNGRADED
                if qc_status is ScientificCheckpointQcStatus.FAIL
                else ScientificCheckpointConfidenceStatus.SUPPORTED
            ),
            decision=ScientificCheckpointDecision.CONTINUE,
            note=(
                "quantification continues, but failed QC keeps downstream claim confidence downgraded"
                if qc_status is ScientificCheckpointQcStatus.FAIL
                else "quantification proceeds under a nonfailed QC posture"
            ),
        ),
        ScientificCheckpointEntry(
            stage=ScientificCheckpointStage.STATISTICS,
            entity_counts=dict(
                sorted(checkpoint_input.statistics_stage.entity_counts.items())
            ),
            rejected_counts=dict(
                sorted(checkpoint_input.statistics_stage.rejected_counts.items())
            ),
            qc_status=qc_status,
            confidence_status=(
                ScientificCheckpointConfidenceStatus.BLOCKED
                if statistics_blocked
                else (
                    ScientificCheckpointConfidenceStatus.DOWNGRADED
                    if qc_status is ScientificCheckpointQcStatus.FAIL
                    else ScientificCheckpointConfidenceStatus.SUPPORTED
                )
            ),
            decision=(
                ScientificCheckpointDecision.BLOCK
                if statistics_blocked
                else ScientificCheckpointDecision.CONTINUE
            ),
            note=_statistics_note(
                checkpoint_input.design_validity, qc_status=qc_status
            ),
        ),
        ScientificCheckpointEntry(
            stage=ScientificCheckpointStage.BIOLOGY,
            entity_counts=dict(
                sorted(checkpoint_input.biology_stage.entity_counts.items())
            ),
            rejected_counts=dict(
                sorted(checkpoint_input.biology_stage.rejected_counts.items())
            ),
            qc_status=qc_status,
            confidence_status=(
                ScientificCheckpointConfidenceStatus.BLOCKED
                if statistics_blocked
                else (
                    ScientificCheckpointConfidenceStatus.DOWNGRADED
                    if biology_downgraded or low_confidence_only
                    else ScientificCheckpointConfidenceStatus.SUPPORTED
                )
            ),
            decision=(
                ScientificCheckpointDecision.BLOCK
                if statistics_blocked
                else ScientificCheckpointDecision.CONTINUE
            ),
            note=_biology_note(
                statistics_blocked=statistics_blocked,
                qc_status=qc_status,
                low_confidence_only=low_confidence_only,
            ),
        ),
    )

    return ScientificCheckpointReport(
        workflow_id=checkpoint_input.workflow_id,
        entries=entries,
        blocked_stage_ids=tuple(
            entry.stage.value
            for entry in entries
            if entry.decision is ScientificCheckpointDecision.BLOCK
        ),
        downgraded_stage_ids=tuple(
            entry.stage.value
            for entry in entries
            if entry.confidence_status
            is ScientificCheckpointConfidenceStatus.DOWNGRADED
        ),
    )


def render_scientific_checkpoints_tsv(
    entries: tuple[ScientificCheckpointEntry, ...],
) -> str:
    """Render scientific checkpoints as a deterministic TSV ledger."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "stage",
            "entity_counts",
            "rejected_counts",
            "qc_status",
            "confidence_status",
            "decision",
            "note",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.stage.value,
                _counts_text(entry.entity_counts),
                _counts_text(entry.rejected_counts),
                entry.qc_status.value,
                entry.confidence_status.value,
                entry.decision.value,
                entry.note,
            )
        )
    return handle.getvalue()


def _counts_text(counts: dict[str, int]) -> str:
    return ";".join(f"{key}={value}" for key, value in sorted(counts.items()))


def _qc_note(qc_status: ScientificCheckpointQcStatus) -> str:
    if qc_status is ScientificCheckpointQcStatus.FAIL:
        return (
            "failed QC does not stop import review, but it downgrades downstream claims"
        )
    if qc_status is ScientificCheckpointQcStatus.WARN:
        return "QC warnings preserve execution while keeping caution visible"
    return "QC passed without a governed downgrade trigger"


def _statistics_note(
    design_validity: ExperimentDesignValidityReport,
    *,
    qc_status: ScientificCheckpointQcStatus,
) -> str:
    if not design_validity.summary.valid_for_differential_analysis:
        issue_codes = ",".join(issue.code for issue in design_validity.issues[:3])
        return (
            "statistics are blocked because experiment design is invalid for differential "
            f"analysis ({issue_codes})"
        )
    if qc_status is ScientificCheckpointQcStatus.FAIL:
        return "statistics continue because design is valid, but failed QC downgrades downstream claim confidence"
    return "statistics continue because design validity supports differential analysis"


def _biology_note(
    *,
    statistics_blocked: bool,
    qc_status: ScientificCheckpointQcStatus,
    low_confidence_only: bool,
) -> str:
    if statistics_blocked:
        return "biology is blocked because invalid design prevented supported statistical results"
    if qc_status is ScientificCheckpointQcStatus.FAIL:
        return "biology continues, but final claims stay downgraded because QC failed earlier in the workflow"
    if low_confidence_only:
        return "biology continues with downgraded confidence because only low-confidence final claims remain"
    return "biology continues with supported final-claim confidence"


def _biology_has_only_low_confidence(
    report: EvidenceGraphConfidenceReport | None,
) -> bool:
    if report is None or report.entry_count == 0:
        return False
    high_count = report.tier_counts.get("high", 0)
    moderate_count = report.tier_counts.get("moderate", 0)
    low_count = report.tier_counts.get("low", 0)
    return low_count > 0 and high_count == 0 and moderate_count == 0


__all__ = [
    "ScientificCheckpointConfidenceStatus",
    "ScientificCheckpointDecision",
    "ScientificCheckpointEntry",
    "ScientificCheckpointInput",
    "ScientificCheckpointQcStatus",
    "ScientificCheckpointReport",
    "ScientificCheckpointStage",
    "ScientificStageSummary",
    "build_scientific_checkpoints",
    "render_scientific_checkpoints_tsv",
]
