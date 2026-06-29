# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Build targeted validation experiment planning reports."""

from __future__ import annotations

from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted.panel_design import TargetedPanelWarningCode

from .models import (
    ValidationExperimentPlanEntry,
    ValidationExperimentPlanningMode,
    ValidationExperimentPlanningPolicy,
    ValidationExperimentPlanningReport,
    ValidationExperimentPlanningSummary,
    ValidationExperimentWarningCode,
    ValidationExperimentWarningEntry,
    ValidationExperimentWarningSeverity,
    ValidationPlanningBiomarkerCandidateInput,
    ValidationPlanningOmittedCandidateInput,
    ValidationPlanningPanelAssayInput,
    ValidationPlanningPilotVarianceInput,
    ValidationPlanningSelectedPeptideInput,
)
from .sizing import (
    assay_risk_score,
    expected_missingness_fraction,
    pilot_variance_by_protein_ref,
    recommended_samples_per_group,
)


def build_validation_experiment_planning_report(
    biomarker_candidates: tuple[ValidationPlanningBiomarkerCandidateInput, ...],
    selected_peptides: tuple[ValidationPlanningSelectedPeptideInput, ...],
    panel_assays: tuple[ValidationPlanningPanelAssayInput, ...],
    *,
    pilot_variance_entries: tuple[ValidationPlanningPilotVarianceInput, ...] = (),
    omitted_candidates: tuple[ValidationPlanningOmittedCandidateInput, ...] = (),
    policy: ValidationExperimentPlanningPolicy | None = None,
) -> ValidationExperimentPlanningReport:
    """Plan targeted validation experiments from owned panel and biomarker evidence."""

    active_policy = policy or ValidationExperimentPlanningPolicy()
    biomarker_by_id = {entry.candidate_id: entry for entry in biomarker_candidates}
    selected_by_key = {
        (entry.target_protein_ref, entry.canonical_peptide): entry
        for entry in selected_peptides
    }
    pilot_by_protein_ref = pilot_variance_by_protein_ref(pilot_variance_entries)

    plan_entries: list[ValidationExperimentPlanEntry] = []
    warning_entries: list[ValidationExperimentWarningEntry] = []
    seen_warning_ids: set[str] = set()
    for assay in sorted(
        panel_assays,
        key=lambda entry: (
            entry.biomarker_priority_rank,
            entry.target_protein_ref,
            entry.assay_entry_id,
        ),
    ):
        biomarker = biomarker_by_id.get(assay.biomarker_candidate_id)
        if biomarker is None:
            continue
        selected = selected_by_key.get(
            (assay.target_protein_ref, assay.canonical_peptide)
        )
        pilot = pilot_by_protein_ref.get(assay.target_protein_ref)
        assay_risk_score_value = assay_risk_score(assay)
        expected_missingness = expected_missingness_fraction(
            selected=selected,
            assay=assay,
            pilot=pilot,
        )
        planning_mode, recommended_samples = recommended_samples_per_group(
            biomarker=biomarker,
            assay=assay,
            selected=selected,
            pilot=pilot,
            expected_missingness_fraction=expected_missingness,
            assay_risk_score_value=assay_risk_score_value,
            policy=active_policy,
        )
        warning_codes = _warning_codes_for_plan(
            biomarker=biomarker,
            assay=assay,
            selected=selected,
            pilot=pilot,
            expected_missingness_fraction=expected_missingness,
            assay_risk_score_value=assay_risk_score_value,
            proposed_samples_per_group=active_policy.proposed_samples_per_group,
            recommended_samples_per_group=recommended_samples,
        )
        underpowered = (
            ValidationExperimentWarningCode.UNDERPOWERED_DESIGN in warning_codes
        )
        plan_entries.append(
            ValidationExperimentPlanEntry(
                assay_entry_id=assay.assay_entry_id,
                biomarker_candidate_id=biomarker.candidate_id,
                biomarker_candidate_kind=biomarker.candidate_kind,
                biomarker_display_label=biomarker.display_label,
                biomarker_priority_rank=biomarker.priority_rank,
                target_protein_ref=assay.target_protein_ref,
                target_protein_group_id=assay.target_protein_group_id,
                gene_symbol=assay.gene_symbol,
                peptide_sequence=assay.peptide_sequence,
                canonical_peptide=assay.canonical_peptide,
                uniqueness_class=assay.uniqueness_class,
                uniqueness_score=assay.uniqueness_score,
                selected_transition_count=assay.selected_transition_count,
                exported_transition_count=assay.exported_transition_count,
                assay_interference_risk_tier=assay.assay_interference_risk_tier,
                assay_risk_score=assay_risk_score_value,
                expected_missingness_fraction=expected_missingness,
                effect_size=biomarker.effect_size,
                robustness_score=biomarker.robustness_score,
                pilot_pooled_log2_stddev=None
                if pilot is None
                else pilot.pooled_log2_stddev,
                pilot_observed_sample_count=None
                if pilot is None
                else pilot.observed_sample_count,
                planning_mode=planning_mode,
                proposed_samples_per_group=active_policy.proposed_samples_per_group,
                recommended_minimum_samples_per_group=recommended_samples,
                underpowered=underpowered,
                warning_codes=warning_codes,
                planning_note=_planning_note(
                    biomarker=biomarker,
                    planning_mode=planning_mode,
                    expected_missingness_fraction=expected_missingness,
                    assay_risk_score_value=assay_risk_score_value,
                    recommended_samples_per_group=recommended_samples,
                    proposed_samples_per_group=active_policy.proposed_samples_per_group,
                    pilot=pilot,
                ),
            )
        )
        for warning_code in warning_codes:
            warning_entry = _warning_entry_for_plan(
                warning_code=warning_code,
                biomarker=biomarker,
                assay=assay,
            )
            if warning_entry.warning_id in seen_warning_ids:
                continue
            seen_warning_ids.add(warning_entry.warning_id)
            warning_entries.append(warning_entry)

    for omitted in sorted(
        omitted_candidates,
        key=lambda entry: (entry.priority_rank, entry.candidate_id),
    ):
        warning_entry = ValidationExperimentWarningEntry(
            warning_id=f"{omitted.candidate_id}:site_candidate_not_panelized",
            severity=ValidationExperimentWarningSeverity.CAUTION,
            warning_code=ValidationExperimentWarningCode.SITE_CANDIDATE_NOT_PANELIZED,
            biomarker_candidate_id=omitted.candidate_id,
            assay_entry_id=None,
            target_protein_ref=omitted.target_protein_ref,
            peptide_sequence=None,
            message=omitted.omission_reason,
        )
        if warning_entry.warning_id in seen_warning_ids:
            continue
        seen_warning_ids.add(warning_entry.warning_id)
        warning_entries.append(warning_entry)

    ordered_plan_entries = tuple(
        sorted(
            plan_entries,
            key=lambda entry: (
                entry.biomarker_priority_rank,
                entry.recommended_minimum_samples_per_group,
                entry.assay_entry_id,
            ),
        )
    )
    ordered_warning_entries = tuple(
        sorted(
            warning_entries,
            key=lambda entry: (
                entry.severity.value,
                entry.biomarker_candidate_id,
                "" if entry.assay_entry_id is None else entry.assay_entry_id,
                entry.warning_code.value,
            ),
        )
    )
    return ValidationExperimentPlanningReport(
        policy=active_policy,
        summary=ValidationExperimentPlanningSummary(
            biomarker_candidate_count=len(biomarker_candidates),
            planned_target_count=len(
                {entry.biomarker_candidate_id for entry in ordered_plan_entries}
            ),
            planned_assay_count=len(ordered_plan_entries),
            omitted_candidate_count=len(omitted_candidates),
            proposed_samples_per_group=active_policy.proposed_samples_per_group,
            recommended_panel_samples_per_group=max(
                (
                    entry.recommended_minimum_samples_per_group
                    for entry in ordered_plan_entries
                ),
                default=active_policy.proposed_samples_per_group,
            ),
            underpowered_assay_count=sum(
                1 for entry in ordered_plan_entries if entry.underpowered
            ),
            high_expected_missingness_assay_count=sum(
                1
                for entry in ordered_plan_entries
                if entry.expected_missingness_fraction >= 0.4
            ),
            high_assay_risk_assay_count=sum(
                1 for entry in ordered_plan_entries if entry.assay_risk_score >= 0.55
            ),
            pilot_backed_assay_count=sum(
                1
                for entry in ordered_plan_entries
                if entry.planning_mode is ValidationExperimentPlanningMode.PILOT_BACKED
            ),
            heuristic_assay_count=sum(
                1
                for entry in ordered_plan_entries
                if entry.planning_mode is ValidationExperimentPlanningMode.HEURISTIC
            ),
            warning_count=len(ordered_warning_entries),
        ),
        plan_entries=ordered_plan_entries,
        warnings=ordered_warning_entries,
        note=(
            "validation experiment planning combines biomarker effect size and robustness, "
            "selected-peptide observability, panel assay risk, and optional pilot variance so "
            "underpowered targeted designs are flagged before validation runs are scheduled"
        ),
    )

def _warning_codes_for_plan(
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


def _warning_entry_for_plan(
    *,
    warning_code: ValidationExperimentWarningCode,
    biomarker: ValidationPlanningBiomarkerCandidateInput,
    assay: ValidationPlanningPanelAssayInput,
) -> ValidationExperimentWarningEntry:
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


def _planning_note(
    *,
    biomarker: ValidationPlanningBiomarkerCandidateInput,
    planning_mode: ValidationExperimentPlanningMode,
    expected_missingness_fraction: float,
    assay_risk_score_value: float,
    recommended_samples_per_group: int,
    proposed_samples_per_group: int,
    pilot: ValidationPlanningPilotVarianceInput | None,
) -> str:
    base = (
        f"{planning_mode.value.replace('_', ' ')} planning recommends at least "
        f"{recommended_samples_per_group} samples per group from effect size, robustness, "
        f"expected missingness {expected_missingness_fraction:.2f}, and assay risk {assay_risk_score_value:.2f}"
    )
    if (
        planning_mode is ValidationExperimentPlanningMode.PILOT_BACKED
        and pilot is not None
    ):
        base += (
            f"; pilot log2 standard deviation {pilot.pooled_log2_stddev:.2f} was available "
            f"for {biomarker.target_protein_ref}"
        )
    if proposed_samples_per_group < recommended_samples_per_group:
        base += f"; proposed design with {proposed_samples_per_group} samples per group is underpowered"
    return base


__all__ = [
    "build_validation_experiment_planning_report",
]
