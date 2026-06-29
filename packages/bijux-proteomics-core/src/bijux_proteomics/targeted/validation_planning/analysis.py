# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Build targeted validation experiment planning reports."""

from __future__ import annotations

import math

from bijux_proteomics.sequences import (
    PeptideChemicalLiabilityTier,
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.assay_interference import (
    TargetedAssayInterferenceRiskTier,
)
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
    pilot_by_protein_ref = _pilot_variance_by_protein_ref(pilot_variance_entries)

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
        assay_risk_score = _assay_risk_score(assay)
        expected_missingness = _expected_missingness_fraction(
            selected=selected,
            assay=assay,
            pilot=pilot,
        )
        planning_mode, recommended_samples = _recommended_samples_per_group(
            biomarker=biomarker,
            assay=assay,
            selected=selected,
            pilot=pilot,
            expected_missingness_fraction=expected_missingness,
            assay_risk_score=assay_risk_score,
            policy=active_policy,
        )
        warning_codes = _warning_codes_for_plan(
            biomarker=biomarker,
            assay=assay,
            selected=selected,
            pilot=pilot,
            expected_missingness_fraction=expected_missingness,
            assay_risk_score=assay_risk_score,
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
                assay_risk_score=assay_risk_score,
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
                    assay_risk_score=assay_risk_score,
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
def _pilot_variance_by_protein_ref(
    entries: tuple[ValidationPlanningPilotVarianceInput, ...],
) -> dict[str, ValidationPlanningPilotVarianceInput]:
    lookup: dict[str, ValidationPlanningPilotVarianceInput] = {}
    for entry in entries:
        for protein_ref in entry.protein_refs:
            lookup.setdefault(protein_ref, entry)
        lookup.setdefault(entry.entity_id, entry)
    return lookup


def _assay_risk_score(assay: ValidationPlanningPanelAssayInput) -> float:
    score = {
        TargetedAssayInterferenceRiskTier.LOW: 0.18,
        TargetedAssayInterferenceRiskTier.MEDIUM: 0.52,
        TargetedAssayInterferenceRiskTier.HIGH: 0.82,
    }[assay.assay_interference_risk_tier]
    if TargetedPanelWarningCode.CANDIDATE_PENALIZED in assay.warning_codes:
        score += 0.08
    if TargetedPanelWarningCode.NON_UNIQUE_TARGET in assay.warning_codes:
        score += 0.12
    if TargetedPanelWarningCode.REDUCED_TRANSITION_SUPPORT in assay.warning_codes:
        score += 0.10
    if TargetedPanelWarningCode.MISSING_EXPECTED_RETENTION_TIME in assay.warning_codes:
        score += 0.05
    return max(0.0, min(1.0, score))


def _expected_missingness_fraction(
    *,
    selected: ValidationPlanningSelectedPeptideInput | None,
    assay: ValidationPlanningPanelAssayInput,
    pilot: ValidationPlanningPilotVarianceInput | None,
) -> float:
    if selected is None:
        heuristic = 0.45
    else:
        detection_component = 0.30 * (
            1.0
            - (
                selected.detection_frequency
                if selected.detection_frequency is not None
                else 0.75
            )
        )
        replicate_component = 0.15 * (
            1.0
            - (
                selected.replicate_consistency
                if selected.replicate_consistency is not None
                else 0.75
            )
        )
        detectability_component = 0.20 * (1.0 - selected.detectability_score)
        suitability_component = 0.15 * (1.0 - selected.suitability_score)
        uniqueness_component = 0.10 * (1.0 - assay.uniqueness_score)
        liability_component = {
            PeptideChemicalLiabilityTier.PREFERRED: 0.04,
            PeptideChemicalLiabilityTier.CAUTION: 0.10,
            PeptideChemicalLiabilityTier.AVOID: 0.22,
        }[selected.liability_tier]
        risk_component = 0.0
        if (
            assay.assay_interference_risk_tier
            is TargetedAssayInterferenceRiskTier.MEDIUM
        ):
            risk_component = 0.08
        elif (
            assay.assay_interference_risk_tier is TargetedAssayInterferenceRiskTier.HIGH
        ):
            risk_component = 0.18
        if TargetedPanelWarningCode.REDUCED_TRANSITION_SUPPORT in assay.warning_codes:
            risk_component += 0.06
        heuristic = (
            detection_component
            + replicate_component
            + detectability_component
            + suitability_component
            + uniqueness_component
            + liability_component
            + risk_component
        )
    if pilot is None:
        return max(0.0, min(1.0, heuristic))
    return max(0.0, min(1.0, max(heuristic, pilot.missing_fraction)))


def _recommended_samples_per_group(
    *,
    biomarker: ValidationPlanningBiomarkerCandidateInput,
    assay: ValidationPlanningPanelAssayInput,
    selected: ValidationPlanningSelectedPeptideInput | None,
    pilot: ValidationPlanningPilotVarianceInput | None,
    expected_missingness_fraction: float,
    assay_risk_score: float,
    policy: ValidationExperimentPlanningPolicy,
) -> tuple[ValidationExperimentPlanningMode, int]:
    effect_size = None if biomarker.effect_size is None else abs(biomarker.effect_size)
    if (
        pilot is not None
        and effect_size is not None
        and effect_size >= 0.15
        and pilot.pooled_log2_stddev > 0.0
    ):
        effective_replicates = _required_effective_replicates_per_group(
            pooled_log2_stddev=pilot.pooled_log2_stddev,
            target_effect_size=effect_size,
            fdr_target=policy.fdr_target,
            target_power=policy.target_power,
        )
        burden_multiplier = 1.0 / max(0.20, 1.0 - expected_missingness_fraction)
        risk_multiplier = (
            1.0 + (0.45 * assay_risk_score) + (0.35 * biomarker.uncertainty)
        )
        recommended = math.ceil(
            effective_replicates * burden_multiplier * risk_multiplier
        )
        return (
            ValidationExperimentPlanningMode.PILOT_BACKED,
            max(policy.heuristic_minimum_samples_per_group, recommended),
        )

    recommended = policy.heuristic_minimum_samples_per_group
    if effect_size is None:
        recommended += 4
    elif effect_size >= 1.5:
        recommended += 0
    elif effect_size >= 1.0:
        recommended += 1
    elif effect_size >= 0.75:
        recommended += 2
    elif effect_size >= 0.50:
        recommended += 4
    elif effect_size >= 0.35:
        recommended += 6
    else:
        recommended += 8
    if biomarker.robustness_score < 0.55:
        recommended += 2
    if biomarker.robustness_score < 0.35:
        recommended += 2
    if assay_risk_score >= 0.55:
        recommended += 2
    if assay_risk_score >= 0.75:
        recommended += 2
    if expected_missingness_fraction >= 0.35:
        recommended += 2
    if expected_missingness_fraction >= 0.50:
        recommended += 2
    if assay.uniqueness_class is not PeptideUniquenessClass.UNIQUE:
        recommended += 1
    if TargetedPanelWarningCode.REDUCED_TRANSITION_SUPPORT in assay.warning_codes:
        recommended += 1
    if biomarker.penalty_total > 0.0:
        recommended += 1
    if biomarker.uncertainty >= 0.25:
        recommended += 1
    if biomarker.uncertainty >= 0.45:
        recommended += 2
    if selected is None:
        recommended += 1
    return ValidationExperimentPlanningMode.HEURISTIC, max(
        policy.heuristic_minimum_samples_per_group,
        recommended,
    )


def _required_effective_replicates_per_group(
    *,
    pooled_log2_stddev: float,
    target_effect_size: float,
    fdr_target: float,
    target_power: float,
) -> float:
    z_alpha = _inverse_standard_normal_cdf(1.0 - (fdr_target / 2.0))
    z_beta = _inverse_standard_normal_cdf(target_power)
    return 2.0 * (((z_alpha + z_beta) * pooled_log2_stddev) / target_effect_size) ** 2


def _inverse_standard_normal_cdf(probability: float) -> float:
    if not 0.0 < probability < 1.0:
        raise ValueError("probability must lie strictly between zero and one")
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    )
    lower_tail = 0.02425
    upper_tail = 1.0 - lower_tail
    if probability < lower_tail:
        q = math.sqrt(-2.0 * math.log(probability))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )
    if probability > upper_tail:
        q = math.sqrt(-2.0 * math.log(1.0 - probability))
        return -(
            (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5])
            / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )
    q = probability - 0.5
    r = q * q
    return (
        (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
    ) / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)


def _warning_codes_for_plan(
    *,
    biomarker: ValidationPlanningBiomarkerCandidateInput,
    assay: ValidationPlanningPanelAssayInput,
    selected: ValidationPlanningSelectedPeptideInput | None,
    pilot: ValidationPlanningPilotVarianceInput | None,
    expected_missingness_fraction: float,
    assay_risk_score: float,
    proposed_samples_per_group: int,
    recommended_samples_per_group: int,
) -> tuple[ValidationExperimentWarningCode, ...]:
    warnings: list[ValidationExperimentWarningCode] = []
    if proposed_samples_per_group < recommended_samples_per_group:
        warnings.append(ValidationExperimentWarningCode.UNDERPOWERED_DESIGN)
    if expected_missingness_fraction >= 0.35:
        warnings.append(ValidationExperimentWarningCode.HIGH_EXPECTED_MISSINGNESS)
    if assay_risk_score >= 0.55:
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
    assay_risk_score: float,
    recommended_samples_per_group: int,
    proposed_samples_per_group: int,
    pilot: ValidationPlanningPilotVarianceInput | None,
) -> str:
    base = (
        f"{planning_mode.value.replace('_', ' ')} planning recommends at least "
        f"{recommended_samples_per_group} samples per group from effect size, robustness, "
        f"expected missingness {expected_missingness_fraction:.2f}, and assay risk {assay_risk_score:.2f}"
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
