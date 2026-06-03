# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from math import isclose

from bijux_proteomics.io.retention_time_alignment import (
    RetentionTimeAlignmentAnchor,
    RetentionTimeIdentificationRow,
    apply_rt_residuals,
    fit_rt_alignment,
    render_rt_residual_penalties_tsv,
)


def test_apply_rt_residuals_downgrades_high_confidence_outliers_after_alignment() -> (
    None
):
    model_report = fit_rt_alignment(
        (
            _anchor("shifted_run", "anchor_alpha", 20.0, 10.0, 1.0),
            _anchor("shifted_run", "anchor_beta", 50.0, 40.0, 1.0),
            _anchor("shifted_run", "anchor_gamma", 80.0, 70.0, 0.8),
        ),
        min_anchor_count=2,
    )
    rows = apply_rt_residuals(
        (
            _identification(
                "high_confidence_supported", "shifted_run", 50.0, 40.0, 0.98
            ),
            _identification("high_confidence_outlier", "shifted_run", 62.0, 40.0, 0.99),
            _identification("low_confidence_outlier", "shifted_run", 62.0, 40.0, 0.25),
        ),
        model_report,
        aligned_rt_tolerance_seconds=5.0,
        high_confidence_threshold=0.9,
    )
    rendered = render_rt_residual_penalties_tsv(rows)
    by_id = {row.entity_id: row for row in rows}

    assert isclose(by_id["high_confidence_supported"].expected_rt, 50.0, abs_tol=1e-9)
    assert isclose(by_id["high_confidence_supported"].rt_residual, 0.0, abs_tol=1e-9)
    assert by_id["high_confidence_supported"].rt_outlier is False
    assert by_id["high_confidence_supported"].rt_confidence_penalty == 1.0

    assert isclose(by_id["high_confidence_outlier"].expected_rt, 50.0, abs_tol=1e-9)
    assert isclose(by_id["high_confidence_outlier"].rt_residual, 12.0, abs_tol=1e-9)
    assert by_id["high_confidence_outlier"].rt_outlier is True
    assert by_id["high_confidence_outlier"].rt_confidence_penalty < 0.5

    assert by_id["low_confidence_outlier"].rt_outlier is True
    assert by_id["low_confidence_outlier"].rt_confidence_penalty == 1.0
    assert (
        "entity_id\tobserved_rt\texpected_rt\trt_residual\trt_outlier\trt_confidence_penalty"
        in rendered
    )
    assert "high_confidence_outlier\t62\t50\t12\ttrue\t0.2000" in rendered


def _anchor(
    run_id: str,
    peptide_id: str,
    observed_rt: float,
    reference_rt: float,
    anchor_confidence: float,
) -> RetentionTimeAlignmentAnchor:
    return RetentionTimeAlignmentAnchor(
        run_id=run_id,
        peptide_id=peptide_id,
        observed_rt=observed_rt,
        reference_rt=reference_rt,
        anchor_confidence=anchor_confidence,
    )


def _identification(
    entity_id: str,
    run_id: str,
    observed_rt: float,
    expected_rt: float,
    imported_confidence: float,
) -> RetentionTimeIdentificationRow:
    return RetentionTimeIdentificationRow(
        entity_id=entity_id,
        run_id=run_id,
        observed_rt=observed_rt,
        expected_rt=expected_rt,
        imported_confidence=imported_confidence,
    )
