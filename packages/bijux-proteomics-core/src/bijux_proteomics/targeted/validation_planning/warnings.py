# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Warning policy for targeted validation experiment planning."""

from __future__ import annotations

from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted.panel_design import TargetedPanelWarningCode

from .models import (
    ValidationExperimentWarningCode,
    ValidationExperimentWarningEntry,
    ValidationExperimentWarningSeverity,
    ValidationPlanningBiomarkerCandidateInput,
    ValidationPlanningOmittedCandidateInput,
    ValidationPlanningPanelAssayInput,
    ValidationPlanningPilotVarianceInput,
    ValidationPlanningSelectedPeptideInput,
)


def warning_codes_for_plan(
    *,
    biomarker: ValidationPlanningBiomarkerCandidateInput,
    assay: ValidationPlanningPanelAssayInput,
    selected: ValidationPlanningSelectedPeptideInput | None,
    pilot: ValidationPlanningPilotVarianceInput | None,
    expected_missingness_fraction: float,
    assay_risk_score_value: float,
    proposed_samples_per_group: int,
    recommended_samples_per_group: int,
) -> tuple[ValidationExperimentWarningCode, ...]:
    """Derive warning codes for one assay-backed validation plan entry."""

    warnings: list[ValidationExperimentWarningCode] = []
    if proposed_samples_per_group < recommended_samples_per_group:
        warnings.append(ValidationExperimentWarningCode.UNDERPOWERED_DESIGN)
    if expected_missingness_fraction >= 0.35:
        warnings.append(ValidationExperimentWarningCode.HIGH_EXPECTED_MISSINGNESS)
    if assay_risk_score_value >= 0.55:
        warnings.append(ValidationExperimentWarningCode.HIGH_ASSAY_RISK)
    if assay.uniqueness_class is not PeptideUniquenessClass.UNIQUE:
        warnings.append(ValidationExperimentWarningCode.NON_UNIQUE_TARGET)
    if TargetedPanelWarningCode.REDUCED_TRANSITION_SUPPORT in assay.warning_codes:
        warnings.append(ValidationExperimentWarningCode.REDUCED_TRANSITION_SUPPORT)
    if biomarker.penalty_total > 0.0:
        warnings.append(ValidationExperimentWarningCode.CANDIDATE_PENALIZED)
    if pilot is None:
        warnings.append(ValidationExperimentWarningCode.MISSING_PILOT_VARIANCE)
    elif pilot.used_global_variance_fallback:
        warnings.append(ValidationExperimentWarningCode.VARIANCE_FALLBACK_USED)
    if selected is None:
        warnings.append(ValidationExperimentWarningCode.MISSING_SELECTION_CONTEXT)
    return tuple(warnings)


def warning_entry_for_plan(
    *,
    warning_code: ValidationExperimentWarningCode,
    biomarker: ValidationPlanningBiomarkerCandidateInput,
    assay: ValidationPlanningPanelAssayInput,
) -> ValidationExperimentWarningEntry:
    """Build one warning row for an assay-backed validation plan."""

    severity = _warning_severity(warning_code)
    return ValidationExperimentWarningEntry(
        warning_id=f"{assay.assay_entry_id}:{warning_code.value}",
        severity=severity,
        warning_code=warning_code,
        biomarker_candidate_id=biomarker.candidate_id,
        assay_entry_id=assay.assay_entry_id,
        target_protein_ref=assay.target_protein_ref,
        peptide_sequence=assay.peptide_sequence,
        message=_warning_message(
            warning_code=warning_code,
            biomarker=biomarker,
            assay=assay,
        ),
    )


def omitted_candidate_warning_entry(
    omitted: ValidationPlanningOmittedCandidateInput,
) -> ValidationExperimentWarningEntry:
    """Build the reminder row for a candidate omitted before panelization."""

    return ValidationExperimentWarningEntry(
        warning_id=f"{omitted.candidate_id}:site_candidate_not_panelized",
        severity=ValidationExperimentWarningSeverity.CAUTION,
        warning_code=ValidationExperimentWarningCode.SITE_CANDIDATE_NOT_PANELIZED,
        biomarker_candidate_id=omitted.candidate_id,
        assay_entry_id=None,
        target_protein_ref=omitted.target_protein_ref,
        peptide_sequence=None,
        message=omitted.omission_reason,
    )


def _warning_severity(
    warning_code: ValidationExperimentWarningCode,
) -> ValidationExperimentWarningSeverity:
    if warning_code in {
        ValidationExperimentWarningCode.UNDERPOWERED_DESIGN,
        ValidationExperimentWarningCode.HIGH_ASSAY_RISK,
        ValidationExperimentWarningCode.HIGH_EXPECTED_MISSINGNESS,
    }:
        return ValidationExperimentWarningSeverity.HIGH
    if warning_code in {
        ValidationExperimentWarningCode.NON_UNIQUE_TARGET,
        ValidationExperimentWarningCode.REDUCED_TRANSITION_SUPPORT,
        ValidationExperimentWarningCode.SITE_CANDIDATE_NOT_PANELIZED,
        ValidationExperimentWarningCode.VARIANCE_FALLBACK_USED,
    }:
        return ValidationExperimentWarningSeverity.CAUTION
    return ValidationExperimentWarningSeverity.NOTICE


def _warning_message(
    *,
    warning_code: ValidationExperimentWarningCode,
    biomarker: ValidationPlanningBiomarkerCandidateInput,
    assay: ValidationPlanningPanelAssayInput,
) -> str:
    if warning_code is ValidationExperimentWarningCode.UNDERPOWERED_DESIGN:
        return "proposed replicate count per group is below the recommended minimum for this assay-backed validation target"
    if warning_code is ValidationExperimentWarningCode.HIGH_EXPECTED_MISSINGNESS:
        return "expected missingness remains high for this peptide assay and should be budgeted explicitly in validation design"
    if warning_code is ValidationExperimentWarningCode.HIGH_ASSAY_RISK:
        return "assay interference risk remains elevated and increases the chance of inconclusive validation signal"
    if warning_code is ValidationExperimentWarningCode.NON_UNIQUE_TARGET:
        return "selected peptide is not unique to one target protein and requires cautious interpretation in validation"
    if warning_code is ValidationExperimentWarningCode.REDUCED_TRANSITION_SUPPORT:
        return "panel retains fewer transitions than originally selected, reducing targeted assay redundancy"
    if warning_code is ValidationExperimentWarningCode.CANDIDATE_PENALIZED:
        return "biomarker candidate already carries evidence penalties and should not be treated as a low-risk validation target"
    if warning_code is ValidationExperimentWarningCode.MISSING_PILOT_VARIANCE:
        return "pilot variance input was not available, so sample recommendation falls back to heuristic planning rather than pilot-backed power"
    if warning_code is ValidationExperimentWarningCode.VARIANCE_FALLBACK_USED:
        return "pilot variance for this target used a global fallback rather than condition-specific replicate variance"
    if warning_code is ValidationExperimentWarningCode.MISSING_SELECTION_CONTEXT:
        return "selected-peptide observability context was missing for this assay and missingness was estimated conservatively"
    return f"{biomarker.display_label} remains outside the final targeted panel: {assay.warning_note}"


__all__ = [
    "omitted_candidate_warning_entry",
    "warning_codes_for_plan",
    "warning_entry_for_plan",
]
