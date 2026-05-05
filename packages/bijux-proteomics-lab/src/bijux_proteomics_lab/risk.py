# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Assay-risk models for operational follow-up decisions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import AssayId, JsonModel


class AssayRiskSeverity(StrEnum):
    """Severity level for one assay risk finding."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class AssayRiskCode(StrEnum):
    """Operational assay risks that can make a handoff irresponsible."""

    WEAK_PEPTIDE_UNIQUENESS = "weak_peptide_uniqueness"
    POOR_LOCALIZATION = "poor_localization"
    WEAK_QUANT_REPRODUCIBILITY = "weak_quant_reproducibility"
    LIKELY_ASSAY_FAILURE = "likely_assay_failure"


class AssayRiskFinding(JsonModel):
    """One concrete assay risk finding."""

    model_config = ConfigDict(extra="forbid")

    code: AssayRiskCode
    severity: AssayRiskSeverity
    summary: str = Field(..., min_length=1)
    rationale: list[str] = Field(default_factory=list)
    mitigation: list[str] = Field(default_factory=list)


class AssayRiskAssessment(JsonModel):
    """Aggregated assay risk assessment for follow-up readiness."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    overall_risk_score: float = Field(..., ge=0.0, le=1.0)
    supported_for_follow_up: bool = Field(
        ..., description="Whether current assay risk is acceptable for follow-up."
    )
    findings: tuple[AssayRiskFinding, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def _severity_from_gap(gap: float) -> AssayRiskSeverity:
    if gap >= 0.3:
        return AssayRiskSeverity.HIGH
    if gap >= 0.15:
        return AssayRiskSeverity.MODERATE
    return AssayRiskSeverity.LOW


def assess_assay_risk(
    *,
    assay_id: AssayId,
    peptide_uniqueness_score: float,
    localization_probability: float | None,
    quant_reproducibility_score: float,
    assay_feasibility_score: float,
    predicted_failure_risk: float,
) -> AssayRiskAssessment:
    """Assess whether assay-level scientific and execution risk is acceptable."""
    findings: list[AssayRiskFinding] = []

    if peptide_uniqueness_score < 0.75:
        gap = 0.75 - peptide_uniqueness_score
        findings.append(
            AssayRiskFinding(
                code=AssayRiskCode.WEAK_PEPTIDE_UNIQUENESS,
                severity=_severity_from_gap(gap),
                summary="transition evidence depends on weak peptide uniqueness",
                rationale=[
                    f"peptide_uniqueness_score={peptide_uniqueness_score:.2f} is below the review threshold",
                ],
                mitigation=[
                    "replace the peptide with a more unique surrogate",
                    "add orthogonal confirmation before irreversible follow-up",
                ],
            )
        )

    if localization_probability is not None and localization_probability < 0.85:
        gap = 0.85 - localization_probability
        findings.append(
            AssayRiskFinding(
                code=AssayRiskCode.POOR_LOCALIZATION,
                severity=_severity_from_gap(gap),
                summary="site localization confidence is too weak for strong assay claims",
                rationale=[
                    f"localization_probability={localization_probability:.2f} does not support confident site-specific interpretation",
                ],
                mitigation=[
                    "increase localization evidence before targeted follow-up",
                    "avoid site-specific escalation until localization improves",
                ],
            )
        )

    if quant_reproducibility_score < 0.7:
        gap = 0.7 - quant_reproducibility_score
        findings.append(
            AssayRiskFinding(
                code=AssayRiskCode.WEAK_QUANT_REPRODUCIBILITY,
                severity=_severity_from_gap(gap),
                summary="quantitative reproducibility is too weak for confident operational follow-up",
                rationale=[
                    f"quant_reproducibility_score={quant_reproducibility_score:.2f} is below the review threshold",
                ],
                mitigation=[
                    "repeat the assay with matched controls and stricter replicate handling",
                    "treat the current signal as exploratory until reproducibility improves",
                ],
            )
        )

    failure_pressure = max(predicted_failure_risk, 1.0 - assay_feasibility_score)
    if failure_pressure > 0.4:
        findings.append(
            AssayRiskFinding(
                code=AssayRiskCode.LIKELY_ASSAY_FAILURE,
                severity=(
                    AssayRiskSeverity.HIGH
                    if failure_pressure >= 0.6
                    else AssayRiskSeverity.MODERATE
                ),
                summary="operational evidence suggests the assay is likely to fail or stall",
                rationale=[
                    f"predicted_failure_risk={predicted_failure_risk:.2f}",
                    f"assay_feasibility_score={assay_feasibility_score:.2f}",
                ],
                mitigation=[
                    "review controls, turnaround, and sample modality before scheduling",
                    "prefer a lower-risk orthogonal assay when available",
                ],
            )
        )

    severity_weight = {
        AssayRiskSeverity.LOW: 0.2,
        AssayRiskSeverity.MODERATE: 0.5,
        AssayRiskSeverity.HIGH: 0.85,
    }
    finding_pressure = sum(severity_weight[item.severity] for item in findings)
    base_risk = max(
        0.0,
        min(
            (
                (1.0 - peptide_uniqueness_score) * 0.25
                + ((1.0 - localization_probability) * 0.15 if localization_probability is not None else 0.0)
                + (1.0 - quant_reproducibility_score) * 0.25
                + predicted_failure_risk * 0.2
                + (1.0 - assay_feasibility_score) * 0.15
                + (finding_pressure * 0.08)
            ),
            1.0,
        ),
    )
    overall_risk_score = round(base_risk, 4)
    supported_for_follow_up = overall_risk_score < 0.45 and not any(
        item.severity is AssayRiskSeverity.HIGH for item in findings
    )
    notes = (
        ("assay risk remains acceptable for follow-up",)
        if supported_for_follow_up
        else ("assay risk should block or downgrade the follow-up handoff",)
    )

    return AssayRiskAssessment(
        assay_id=assay_id,
        overall_risk_score=overall_risk_score,
        supported_for_follow_up=supported_for_follow_up,
        findings=tuple(findings),
        notes=notes,
    )


__all__ = [
    "AssayRiskAssessment",
    "AssayRiskCode",
    "AssayRiskFinding",
    "AssayRiskSeverity",
    "assess_assay_risk",
]
