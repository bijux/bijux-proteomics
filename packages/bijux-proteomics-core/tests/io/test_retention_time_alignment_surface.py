# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from math import isclose
from pathlib import Path

from bijux_proteomics.io.chromatographic_peak_picking import (
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.retention_time_alignment import (
    RetentionTimeAlignmentAnchor,
    align_chromatographic_peak_retention_times,
    extract_mzml_retention_time_alignment,
    fit_rt_alignment,
    render_retention_time_alignment_failed_anchors_tsv,
    render_retention_time_alignment_models_tsv,
    render_retention_time_alignment_residuals_tsv,
    render_rt_alignment_fit_models_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_fit_rt_alignment_reduces_shifted_run_anchor_residuals() -> None:
    report = fit_rt_alignment(
        (
            _anchor("shifted_run", "anchor_alpha", 20.0, 10.0, 1.0),
            _anchor("shifted_run", "anchor_beta", 50.0, 40.0, 1.0),
            _anchor("shifted_run", "anchor_gamma", 80.0, 60.0, 0.5),
        ),
        min_anchor_count=2,
    )
    model = report.models[0]
    rendered = render_rt_alignment_fit_models_tsv(report)

    assert model.alignment_model == "confidence_weighted_shift"
    assert isclose(model.rt_shift or 0.0, 10.0, abs_tol=1e-9)
    assert isclose(model.rt_residual_median or 0.0, 0.0, abs_tol=1e-9)
    assert isclose(model.unaligned_rt_residual_median or 0.0, 10.0, abs_tol=1e-9)
    assert model.rt_residual_median is not None
    assert model.unaligned_rt_residual_median is not None
    assert model.rt_residual_median < model.unaligned_rt_residual_median
    assert rendered.splitlines()[0] == (
        "run_id\talignment_model\trt_shift\trt_residual_median\tfailed_anchor_count"
    )
    assert "shifted_run\tconfidence_weighted_shift\t10\t0\t0" in rendered


def test_align_chromatographic_peak_retention_times_builds_shift_models_and_flags_drift() -> (
    None
):
    reference_report = extract_mzml_chromatographic_peaks(
        _format_fixture("rt_alignment_reference.mzml"),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
    )
    shifted_report = extract_mzml_chromatographic_peaks(
        _format_fixture("rt_alignment_shifted.mzml"),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
    )

    report = align_chromatographic_peak_retention_times(
        (reference_report, shifted_report),
        aligned_rt_tolerance_seconds=5.0,
    )

    assert report.reference_run_id == "rt_alignment_reference"
    assert len(report.run_models) == 2
    assert report.run_models[0].status.value == "reference"
    assert report.run_models[0].shift_seconds == 0.0
    assert report.run_models[0].alignment_model == "reference_identity"
    assert report.run_models[0].rt_shift == 0.0
    assert report.run_models[1].run_id == "rt_alignment_shifted"
    assert report.run_models[1].status.value == "aligned"
    assert report.run_models[1].alignment_model == "confidence_weighted_shift"
    assert report.run_models[1].anchor_count == 3
    assert report.run_models[1].failed_anchor_count == 1
    assert isclose(report.run_models[1].rt_shift or 0.0, 10.0, abs_tol=1e-9)
    assert isclose(report.run_models[1].rt_residual_median or 0.0, 0.0, abs_tol=1e-9)
    assert isclose(report.run_models[1].shift_seconds or 0.0, 10.0, abs_tol=1e-9)
    assert isclose(
        report.run_models[1].median_absolute_residual_seconds or 0.0,
        0.0,
        abs_tol=1e-9,
    )
    assert isclose(
        report.run_models[1].max_absolute_residual_seconds or 0.0,
        10.0,
        abs_tol=1e-9,
    )
    assert len(report.residuals) == 3
    assert len(report.flagged_residuals) == 1
    drifted_anchor = report.flagged_residuals[0]
    assert drifted_anchor.target_id == "anchor_gamma"
    assert isclose(drifted_anchor.reference_apex_time_seconds, 60.0, abs_tol=1e-9)
    assert isclose(drifted_anchor.observed_apex_time_seconds, 80.0, abs_tol=1e-9)
    assert isclose(drifted_anchor.aligned_apex_time_seconds, 70.0, abs_tol=1e-9)
    assert isclose(drifted_anchor.residual_seconds, 10.0, abs_tol=1e-9)
    assert drifted_anchor.outside_aligned_tolerance is True
    assert len(report.failed_anchors) == 1
    assert report.failed_anchors[0].target_id == "anchor_delta"
    assert report.failed_anchors[0].reason == "missing_run_peak"


def test_extract_mzml_retention_time_alignment_composes_peak_extraction() -> None:
    report = extract_mzml_retention_time_alignment(
        (
            _format_fixture("rt_alignment_reference.mzml"),
            _format_fixture("rt_alignment_shifted.mzml"),
        ),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
    )

    assert report.reference_run_id == "rt_alignment_reference"
    assert len(report.peak_reports) == 2
    assert report.peak_reports[0].trace_report.eligible_spectra == 10
    assert report.peak_reports[1].trace_report.eligible_spectra == 10
    assert [model.run_id for model in report.run_models] == [
        "rt_alignment_reference",
        "rt_alignment_shifted",
    ]


def test_render_retention_time_alignment_tsv_surfaces_emit_models_residuals_and_failures() -> (
    None
):
    report = extract_mzml_retention_time_alignment(
        (
            _format_fixture("rt_alignment_reference.mzml"),
            _format_fixture("rt_alignment_shifted.mzml"),
        ),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
    )

    models_tsv = render_retention_time_alignment_models_tsv(report)
    residuals_tsv = render_retention_time_alignment_residuals_tsv(report)
    failed_tsv = render_retention_time_alignment_failed_anchors_tsv(report)

    assert models_tsv.splitlines()[0] == (
        "run_id\tsource_path\treference_run_id\tstatus\tanchor_count\talignment_model\t"
        "rt_shift\trt_residual_median\tfailed_anchor_count\tshift_seconds\t"
        "median_absolute_residual_seconds\tmax_absolute_residual_seconds\tfailure_reason"
    )
    assert "rt_alignment_shifted\t" in models_tsv
    assert (
        "\taligned\t3\tconfidence_weighted_shift\t10\t0\t1\t10\t0\t10\t" in models_tsv
    )
    assert residuals_tsv.splitlines()[0] == (
        "run_id\tsource_path\ttarget_id\treference_peak_id\trun_peak_id\t"
        "reference_apex_time_seconds\tobserved_apex_time_seconds\t"
        "aligned_apex_time_seconds\tshift_seconds\tresidual_seconds\t"
        "absolute_residual_seconds\toutside_aligned_tolerance"
    )
    assert "rt_alignment_shifted\t" in residuals_tsv
    assert (
        "anchor_gamma\tanchor_gamma_peak_001\tanchor_gamma_peak_001\t60\t80\t70\t10\t10\t10\ttrue"
        in residuals_tsv
    )
    assert failed_tsv.splitlines()[0] == (
        "run_id\tsource_path\ttarget_id\treason\treference_peak_count\trun_peak_count"
    )
    assert "rt_alignment_shifted\t" in failed_tsv
    assert "\tanchor_delta\tmissing_run_peak\t1\t0" in failed_tsv


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
