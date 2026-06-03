# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.psm_features import PsmFeatureRow
from bijux_proteomics.identification.psm_rescoring import (
    PsmRescoringFeatureParameter,
    PsmRescoringModel,
    explain_rescored_psm,
    fit_target_decoy_logistic_model,
    render_psm_rescoring_explanation_tsv,
    render_psm_rescoring_tsv,
)


def _feature_row(
    psm_id: str,
    *,
    score_native: float,
    precursor_ppm_error: float,
    matched_ion_count: int,
    explained_intensity: float,
    top_peak_unmatched_fraction: float,
    target_decoy_label: TargetDecoyLabel,
    q_value_native: float | None = None,
) -> PsmFeatureRow:
    return PsmFeatureRow(
        psm_id=psm_id,
        spectrum_id=f"{psm_id}-scan",
        score_native=score_native,
        q_value_native=q_value_native,
        charge=2,
        peptide_length=8,
        missed_cleavages=0,
        precursor_ppm_error=precursor_ppm_error,
        matched_ion_count=matched_ion_count,
        explained_intensity=explained_intensity,
        spectrum_entropy=0.82 if matched_ion_count >= 6 else 0.18,
        top_peak_unmatched_fraction=top_peak_unmatched_fraction,
        target_decoy_label=target_decoy_label,
    )


def test_fit_target_decoy_logistic_model_improves_target_decoy_separation() -> None:
    feature_table = (
        _feature_row(
            "decoy-lead",
            score_native=120.0,
            q_value_native=0.001,
            precursor_ppm_error=16.5,
            matched_ion_count=0,
            explained_intensity=0.0,
            top_peak_unmatched_fraction=1.0,
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        _feature_row(
            "target-strong-a",
            score_native=101.0,
            q_value_native=0.02,
            precursor_ppm_error=0.4,
            matched_ion_count=10,
            explained_intensity=0.94,
            top_peak_unmatched_fraction=0.04,
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        _feature_row(
            "target-strong-b",
            score_native=99.0,
            q_value_native=0.03,
            precursor_ppm_error=-0.6,
            matched_ion_count=9,
            explained_intensity=0.91,
            top_peak_unmatched_fraction=0.07,
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        _feature_row(
            "decoy-mid",
            score_native=96.0,
            q_value_native=0.04,
            precursor_ppm_error=-11.0,
            matched_ion_count=1,
            explained_intensity=0.08,
            top_peak_unmatched_fraction=0.92,
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        _feature_row(
            "target-support-a",
            score_native=94.0,
            q_value_native=0.05,
            precursor_ppm_error=1.0,
            matched_ion_count=8,
            explained_intensity=0.88,
            top_peak_unmatched_fraction=0.12,
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        _feature_row(
            "target-support-b",
            score_native=92.0,
            q_value_native=0.07,
            precursor_ppm_error=-1.2,
            matched_ion_count=7,
            explained_intensity=0.84,
            top_peak_unmatched_fraction=0.16,
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )

    report = fit_target_decoy_logistic_model(feature_table)
    rendered = render_psm_rescoring_tsv(report)

    by_psm_id = {entry.psm_id: entry for entry in report.entries}

    assert report.summary.rescored_auc > report.summary.native_auc
    assert report.summary.separation_gain > 0.0
    assert by_psm_id["decoy-lead"].rank_before == 1
    assert by_psm_id["decoy-lead"].rank_after > by_psm_id["target-strong-a"].rank_after
    assert by_psm_id["target-strong-a"].rescored_probability > 0.9
    assert by_psm_id["decoy-lead"].rescored_probability < 0.1
    assert report.summary.q_values_monotonic is True
    assert "rescored_probability" in rendered
    assert "rank_after" in rendered


def test_fit_target_decoy_logistic_model_rejects_nonseparable_fixture() -> None:
    feature_table = (
        _feature_row(
            "target-a",
            score_native=80.0,
            q_value_native=0.2,
            precursor_ppm_error=2.0,
            matched_ion_count=4,
            explained_intensity=0.5,
            top_peak_unmatched_fraction=0.5,
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        _feature_row(
            "target-b",
            score_native=80.0,
            q_value_native=0.2,
            precursor_ppm_error=2.0,
            matched_ion_count=4,
            explained_intensity=0.5,
            top_peak_unmatched_fraction=0.5,
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        _feature_row(
            "decoy-a",
            score_native=80.0,
            q_value_native=0.2,
            precursor_ppm_error=2.0,
            matched_ion_count=4,
            explained_intensity=0.5,
            top_peak_unmatched_fraction=0.5,
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
        _feature_row(
            "decoy-b",
            score_native=80.0,
            q_value_native=0.2,
            precursor_ppm_error=2.0,
            matched_ion_count=4,
            explained_intensity=0.5,
            top_peak_unmatched_fraction=0.5,
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )

    with pytest.raises(ValueError, match="insufficient_target_decoy_separation"):
        fit_target_decoy_logistic_model(feature_table)


def test_explain_rescored_psm_reports_negative_precursor_error_and_intensity_terms() -> (
    None
):
    feature_row = _feature_row(
        "target-explained",
        score_native=97.0,
        q_value_native=0.02,
        precursor_ppm_error=18.0,
        matched_ion_count=1,
        explained_intensity=0.05,
        top_peak_unmatched_fraction=0.94,
        target_decoy_label=TargetDecoyLabel.TARGET,
    )
    model = PsmRescoringModel(
        intercept=0.3,
        feature_parameters=(
            PsmRescoringFeatureParameter(
                feature_name="precursor_ppm_error",
                transform="absolute",
                mean=2.0,
                scale=4.0,
                weight=-1.25,
            ),
            PsmRescoringFeatureParameter(
                feature_name="explained_intensity",
                transform="identity",
                mean=0.75,
                scale=0.2,
                weight=0.9,
            ),
            PsmRescoringFeatureParameter(
                feature_name="matched_ion_count",
                transform="identity",
                mean=7.0,
                scale=2.0,
                weight=0.6,
            ),
        ),
        regularization_strength=0.01,
        iteration_count=12,
        convergence_delta=1e-7,
        native_auc=0.61,
        rescored_auc=0.88,
    )

    explanation = explain_rescored_psm(model, feature_row)
    rendered = render_psm_rescoring_explanation_tsv(explanation)
    by_feature = {entry.feature_name: entry for entry in explanation}

    assert by_feature["precursor_ppm_error"].standardized_value > 0.0
    assert by_feature["precursor_ppm_error"].signed_contribution < 0.0
    assert by_feature["explained_intensity"].standardized_value < 0.0
    assert by_feature["explained_intensity"].signed_contribution < 0.0
    assert by_feature["matched_ion_count"].signed_contribution < 0.0
    assert "signed_contribution" in rendered
    assert "feature_name" in rendered


def test_explain_rescored_psm_rejects_unknown_model_feature_names() -> None:
    feature_row = _feature_row(
        "target-invalid-model",
        score_native=91.0,
        precursor_ppm_error=0.5,
        matched_ion_count=8,
        explained_intensity=0.9,
        top_peak_unmatched_fraction=0.05,
        target_decoy_label=TargetDecoyLabel.TARGET,
    )
    model = PsmRescoringModel(
        intercept=0.0,
        feature_parameters=(
            PsmRescoringFeatureParameter(
                feature_name="not_a_real_feature",
                transform="identity",
                mean=0.0,
                scale=1.0,
                weight=1.0,
            ),
        ),
        regularization_strength=0.01,
        iteration_count=1,
        convergence_delta=0.0,
        native_auc=0.5,
        rescored_auc=0.5,
    )

    with pytest.raises(
        ValueError,
        match="rescoring model feature parameters must use supported PSM features",
    ):
        explain_rescored_psm(model, feature_row)
