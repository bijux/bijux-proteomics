# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared biomarker candidate ranking score helpers."""

from __future__ import annotations


def _score_effect_size(log2_fold_change: float | None) -> float:
    if log2_fold_change is None:
        return 0.0
    return max(0.0, min(1.0, abs(log2_fold_change) / 2.0))


def _score_annotation_labels(annotation_labels: tuple[str, ...]) -> float:
    if not annotation_labels:
        return 0.0
    prefixes = {
        label.split(":", 1)[0] if ":" in label else label for label in annotation_labels
    }
    return max(0.0, min(1.0, len(prefixes) / 4.0))


def _score_protein_specificity(
    *,
    unique_count: int,
    shared_count: int,
    identity_level: str,
    selected_uniqueness_score: float,
) -> float:
    peptide_total = max(1, unique_count + shared_count)
    unique_fraction = unique_count / peptide_total
    base = max(unique_fraction, selected_uniqueness_score)
    identity_adjustment = {
        "isoform_level": 0.10,
        "protein_level": 0.0,
        "gene_level": -0.15,
        "family_level": -0.25,
        "ambiguous": -0.35,
    }.get(identity_level, 0.0)
    return max(0.0, min(1.0, base + identity_adjustment))


def _score_protein_detectability(
    *,
    selected_detectability_score: float,
    unique_count: int,
    evidence_tier: str,
) -> float:
    tier_score = {
        "high": 0.90,
        "moderate": 0.65,
        "low": 0.35,
        "warning": 0.25,
    }.get(evidence_tier, 0.40)
    return max(
        0.0,
        min(
            1.0,
            max(selected_detectability_score, 0.50 * min(1.0, unique_count / 2.0))
            + (0.25 * tier_score),
        ),
    )


def _score_protein_assay_feasibility(
    *,
    selected_suitability_score: float,
    detectability_score: float,
    assay_score: float,
) -> float:
    baseline = max(selected_suitability_score, 0.60 * detectability_score)
    if assay_score > 0.0:
        baseline = (0.45 * baseline) + (0.55 * assay_score)
    return max(0.0, min(1.0, baseline))


def _score_ptm_specificity(
    *,
    localization_tier: str,
    identity_level: str,
    low_localization: bool,
    ambiguous: bool,
    shared_peptide: bool,
) -> float:
    base = {
        "high": 0.90,
        "moderate": 0.65,
        "low": 0.30,
        "unsupported": 0.10,
    }.get(localization_tier, 0.40)
    if low_localization:
        base -= 0.20
    if ambiguous:
        base -= 0.15
    if shared_peptide:
        base -= 0.15
    if identity_level in {"gene_level", "family_level", "ambiguous"}:
        base -= 0.10
    return max(0.0, min(1.0, base))


def _score_ptm_detectability(
    *,
    peptide_spectrum_count: int,
    observed_sample_count: int,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            (0.60 * min(1.0, peptide_spectrum_count / 5.0))
            + (0.40 * min(1.0, observed_sample_count / 4.0)),
        ),
    )


def _score_ptm_assay_feasibility(
    *,
    specificity_score: float,
    warning_count: int,
    protein_correction_status: str,
) -> float:
    score = 0.70 * specificity_score
    if protein_correction_status == "corrected":
        score += 0.10
    score -= min(0.20, 0.05 * warning_count)
    return max(0.0, min(1.0, score))


def _score_ptm_robustness(
    *,
    adjusted_p_value: float | None,
    imputation_dependent: bool,
    low_localization: bool,
    ambiguous: bool,
) -> float:
    if adjusted_p_value is None:
        score = 0.25
    else:
        score = max(0.0, min(1.0, 1.0 - (adjusted_p_value / 0.10)))
    if imputation_dependent:
        score -= 0.20
    if low_localization:
        score -= 0.15
    if ambiguous:
        score -= 0.10
    return max(0.0, min(1.0, score))
