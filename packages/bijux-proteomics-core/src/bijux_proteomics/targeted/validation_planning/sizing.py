# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Sizing and observability heuristics for validation experiment planning."""

from __future__ import annotations

import math

from bijux_proteomics.sequences.peptide_chemical_liability import (
    PeptideChemicalLiabilityTier,
)
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.assay_interference import (
    TargetedAssayInterferenceRiskTier,
)
from bijux_proteomics.targeted.panel_design import TargetedPanelWarningCode

from .models import (
    ValidationExperimentPlanningMode,
    ValidationExperimentPlanningPolicy,
    ValidationPlanningBiomarkerCandidateInput,
    ValidationPlanningPanelAssayInput,
    ValidationPlanningPilotVarianceInput,
    ValidationPlanningSelectedPeptideInput,
)


def pilot_variance_by_protein_ref(
    entries: tuple[ValidationPlanningPilotVarianceInput, ...],
) -> dict[str, ValidationPlanningPilotVarianceInput]:
    """Index pilot variance entries by stable protein reference."""

    lookup: dict[str, ValidationPlanningPilotVarianceInput] = {}
    for entry in entries:
        for protein_ref in entry.protein_refs:
            lookup.setdefault(protein_ref, entry)
        lookup.setdefault(entry.entity_id, entry)
    return lookup


def assay_risk_score(assay: ValidationPlanningPanelAssayInput) -> float:
    """Estimate assay execution risk from interference tier and panel warnings."""

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


def expected_missingness_fraction(
    *,
    selected: ValidationPlanningSelectedPeptideInput | None,
    assay: ValidationPlanningPanelAssayInput,
    pilot: ValidationPlanningPilotVarianceInput | None,
) -> float:
    """Estimate validation missingness from peptide observability and assay risk."""

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


def recommended_samples_per_group(
    *,
    biomarker: ValidationPlanningBiomarkerCandidateInput,
    assay: ValidationPlanningPanelAssayInput,
    selected: ValidationPlanningSelectedPeptideInput | None,
    pilot: ValidationPlanningPilotVarianceInput | None,
    expected_missingness_fraction: float,
    assay_risk_score_value: float,
    policy: ValidationExperimentPlanningPolicy,
) -> tuple[ValidationExperimentPlanningMode, int]:
    """Recommend per-group sample counts from pilot or heuristic evidence."""

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
            1.0 + (0.45 * assay_risk_score_value) + (0.35 * biomarker.uncertainty)
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
    if assay_risk_score_value >= 0.55:
        recommended += 2
    if assay_risk_score_value >= 0.75:
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


__all__ = [
    "assay_risk_score",
    "expected_missingness_fraction",
    "pilot_variance_by_protein_ref",
    "recommended_samples_per_group",
]
