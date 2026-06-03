# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Contaminant and acquisition-artifact interpretation owners."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.lab.qc import (
    LcmsRunQcReport,
    QcAssessmentSeverity,
    QcRunAssessmentReport,
)
from bijux_proteomics.quantification import BatchEffectAdvisoryReport
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.interpretation.pathways import (
    InterpretationClaimScope,
)


class ContaminantArtifactFinding(JsonModel):
    """One likely contaminant or workflow artifact explanation."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    severity: QcAssessmentSeverity
    supporting_metrics: dict[str, float] = Field(default_factory=dict)
    suggested_action: str = Field(..., min_length=1)


class QcOperatorAction(JsonModel):
    """Concrete operator action linked to one or more QC-derived findings."""

    model_config = ConfigDict(extra="forbid")

    action_code: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    trigger_finding_codes: tuple[str, ...] = Field(default_factory=tuple)
    required_before_progression: bool = Field(default=True)


class ContaminantArtifactIntelligence(JsonModel):
    """Interpretation of likely contamination or acquisition artifacts."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    findings: tuple[ContaminantArtifactFinding, ...] = Field(default_factory=tuple)
    biological_claim_scope: InterpretationClaimScope = (
        InterpretationClaimScope.ADVISORY_ONLY
    )
    overclaim_guardrails: tuple[str, ...] = Field(default_factory=tuple)
    operator_actions: tuple[QcOperatorAction, ...] = Field(default_factory=tuple)
    interpretation_summary: str = Field(..., min_length=1)


def _build_qc_operator_actions(
    findings: tuple[ContaminantArtifactFinding, ...],
) -> tuple[QcOperatorAction, ...]:
    actions: list[QcOperatorAction] = []
    finding_codes = {finding.code for finding in findings}
    if "contaminant-burden" in finding_codes:
        actions.append(
            QcOperatorAction(
                action_code="inspect-cleanup-and-carryover-controls",
                summary=(
                    "inspect cleanup workflow, wash steps, and carryover controls before trusting downstream biology"
                ),
                trigger_finding_codes=("contaminant-burden",),
            )
        )
    if "digestion-specificity-loss" in finding_codes:
        actions.append(
            QcOperatorAction(
                action_code="review-digestion-conditions",
                summary=(
                    "review digestion chemistry and protease setup before treating peptide-level evidence as stable"
                ),
                trigger_finding_codes=("digestion-specificity-loss",),
            )
        )
    if "mass-calibration-drift" in finding_codes:
        actions.append(
            QcOperatorAction(
                action_code="recalibrate-mass-accuracy",
                summary=(
                    "recalibrate instrument mass accuracy and verify precursor matching before progression"
                ),
                trigger_finding_codes=("mass-calibration-drift",),
            )
        )
    if "low-identification-rate" in finding_codes:
        actions.append(
            QcOperatorAction(
                action_code="audit-search-and-acquisition-match",
                summary=(
                    "audit database choice, search settings, and acquisition quality before relying on identification outcomes"
                ),
                trigger_finding_codes=("low-identification-rate",),
            )
        )
    if not actions:
        actions.append(
            QcOperatorAction(
                action_code="continue-biological-interpretation",
                summary="qc surface does not currently demand corrective operator intervention",
                trigger_finding_codes=("no-major-artifact",),
                required_before_progression=False,
            )
        )
    return tuple(actions)


def interpret_contaminant_artifacts(
    run_report: LcmsRunQcReport,
    run_assessment: QcRunAssessmentReport,
) -> ContaminantArtifactIntelligence:
    """Explain likely contaminants or workflow artifacts from QC metrics."""
    findings: list[ContaminantArtifactFinding] = []
    if run_report.contaminant_summary.contaminant_psm_fraction >= 0.1:
        findings.append(
            ContaminantArtifactFinding(
                code="contaminant-burden",
                summary="Contaminant burden is high enough to suggest sample carryover or cleanup failure.",
                severity=QcAssessmentSeverity.WARNING,
                supporting_metrics={
                    "contaminant_psm_fraction": run_report.contaminant_summary.contaminant_psm_fraction,
                },
                suggested_action="inspect sample cleanup, wash steps, and contaminant database composition",
            )
        )
    if run_report.missed_cleavage_rate >= 0.2:
        findings.append(
            ContaminantArtifactFinding(
                code="digestion-specificity-loss",
                summary="Missed-cleavage pressure suggests incomplete digestion or protease mismatch.",
                severity=QcAssessmentSeverity.WARNING,
                supporting_metrics={
                    "missed_cleavage_rate": run_report.missed_cleavage_rate
                },
                suggested_action="inspect digestion conditions and enzyme configuration",
            )
        )
    if (
        run_report.mass_error.median_abs_ppm is not None
        and run_report.mass_error.median_abs_ppm >= 10.0
    ):
        findings.append(
            ContaminantArtifactFinding(
                code="mass-calibration-drift",
                summary="Precursor error is elevated enough to suggest calibration or alignment drift.",
                severity=QcAssessmentSeverity.FAILED
                if run_assessment.blocked
                else QcAssessmentSeverity.WARNING,
                supporting_metrics={
                    "median_abs_mass_error_ppm": run_report.mass_error.median_abs_ppm
                },
                suggested_action="inspect instrument calibration and precursor matching settings",
            )
        )
    if run_report.identification_rate < 0.2:
        findings.append(
            ContaminantArtifactFinding(
                code="low-identification-rate",
                summary="Low identification rate suggests acquisition or search-configuration mismatch.",
                severity=QcAssessmentSeverity.FAILED
                if run_assessment.blocked
                else QcAssessmentSeverity.WARNING,
                supporting_metrics={
                    "identification_rate": run_report.identification_rate
                },
                suggested_action="review search parameters, database choice, and acquisition quality",
            )
        )
    if not findings:
        findings.append(
            ContaminantArtifactFinding(
                code="no-major-artifact",
                summary="No dominant contaminant or acquisition artifact stands out from the QC surface.",
                severity=QcAssessmentSeverity.PASSED,
                supporting_metrics={},
                suggested_action="continue with biological interpretation",
            )
        )
    finalized_findings = tuple(findings)
    return ContaminantArtifactIntelligence(
        run_id=run_report.run_id,
        findings=finalized_findings,
        overclaim_guardrails=(
            "contaminant findings explain technical risk and sample quality, not biological mechanism",
            "treat acquisition-artifact language as operator guidance until orthogonal biological evidence agrees",
        ),
        operator_actions=_build_qc_operator_actions(finalized_findings),
        interpretation_summary=findings[0].summary,
    )


def extract_contaminant_theme(
    batch_report: BatchEffectAdvisoryReport,
) -> str | None:
    """Return the dominant batch shift as one compact theme if present."""
    flagged = [entry for entry in batch_report.batches if entry.flagged]
    if not flagged:
        return None
    largest = max(flagged, key=lambda entry: abs(entry.shift_from_global))
    return f"{largest.batch_id} shows the strongest batch-level intensity shift"
