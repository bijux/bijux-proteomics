# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics import (
    annotate_spectrum_fragments,
    build_spectrum_metrics,
    build_spectrum_plot_payload,
    calculate_precursor_mass_error,
    export_spectrum_annotation_tsv,
    filter_spectrum_peaks,
    normalize_spectrum_peaks,
    parse_mgf,
    PeakNormalizationPolicy,
    render_mgf,
)


def _spectrum_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "spectra" / name


def test_spectrum_model_and_mgf_parser_accept_simple_fixture() -> None:
    report = parse_mgf(_spectrum_fixture("simple.mgf"))

    assert report.total_blocks == 1
    assert len(report.accepted_spectra) == 1
    spectrum = report.accepted_spectra[0]
    assert spectrum.spectrum_id == "scan=5001"
    assert spectrum.precursor_mz == 500.2
    assert spectrum.precursor_charge == 2
    assert spectrum.retention_time_seconds == 123.4
    assert len(spectrum.peaks) == 6


def test_mgf_parser_accepts_multi_block_and_rejects_malformed_fixture() -> None:
    accepted = parse_mgf(_spectrum_fixture("multi.mgf"))
    rejected = parse_mgf(_spectrum_fixture("malformed.mgf"))

    assert len(accepted.accepted_spectra) == 2
    assert accepted.accepted_spectra[1].spectrum_id == "scan=5002"
    assert accepted.accepted_spectra[1].title is None
    assert len(rejected.accepted_spectra) == 0
    assert len(rejected.rejected_blocks) == 2
    codes = {
        issue.code
        for block in rejected.rejected_blocks
        for issue in block.issues
    }
    assert "missing_precursor_mz" in codes
    assert "invalid_pepmass" in codes
    assert "invalid_peak_value" in codes
    assert "missing_end_ions" in codes


def test_mgf_writer_roundtrip_preserves_spectrum_contracts() -> None:
    report = parse_mgf(_spectrum_fixture("multi.mgf"))
    rendered = render_mgf(report.accepted_spectra)
    output_path = _spectrum_fixture("roundtrip.mgf")
    try:
        output_path.write_text(rendered)
        roundtrip = parse_mgf(output_path)
        assert len(roundtrip.accepted_spectra) == 2
        assert roundtrip.accepted_spectra[0].precursor_mz == report.accepted_spectra[0].precursor_mz
        assert roundtrip.accepted_spectra[1].precursor_charge == 3
    finally:
        output_path.unlink(missing_ok=True)


def test_spectrum_peak_normalization_sorts_merges_duplicates_and_drops_zero() -> None:
    spectrum = parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    normalized = normalize_spectrum_peaks(
        spectrum,
        policy=PeakNormalizationPolicy(merge_tolerance_da=0.0),
    )

    assert [peak.mz for peak in normalized.peaks] == sorted(peak.mz for peak in normalized.peaks)
    assert len(normalized.peaks) == 4
    duplicate_peak = next(peak for peak in normalized.peaks if abs(peak.mz - 150.0) < 1e-9)
    assert duplicate_peak.intensity == 45.0


def test_spectrum_filtering_supports_top_n_intensity_and_mz_window() -> None:
    spectrum = normalize_spectrum_peaks(parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0])
    report = filter_spectrum_peaks(
        spectrum,
        top_n=2,
        min_relative_intensity=0.5,
        mz_min=140.0,
        mz_max=400.0,
    )

    assert report.input_peak_count == 4
    assert report.output_peak_count == 2
    assert report.removed_by_mz_window == 1
    assert report.removed_by_intensity >= 1
    assert report.removed_by_rank >= 0


def test_spectrum_metrics_cover_tic_and_base_peak() -> None:
    spectrum = normalize_spectrum_peaks(parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0])
    metrics = build_spectrum_metrics(spectrum)

    assert metrics.peak_count == 4
    assert metrics.total_ion_current == 250.0
    assert metrics.base_peak_mz == 376.171426
    assert metrics.base_peak_intensity == 100.0


def test_precursor_mass_error_reports_dalton_and_ppm() -> None:
    error = calculate_precursor_mass_error(observed_mz=500.2, theoretical_mz=500.0)

    assert round(error.delta_da, 6) == 0.2
    assert round(error.delta_ppm, 3) == 400.0


def test_theoretical_fragment_matching_annotation_and_plot_payload_are_stable() -> None:
    spectrum = normalize_spectrum_peaks(parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0])
    annotation = annotate_spectrum_fragments(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=0.01,
        include_neutral_losses=False,
    )

    assert annotation.document_schema.document_kind == "spectrum_annotation"
    assert annotation.peptide == "PEPTIDE"
    labels = {match.fragment_label for match in annotation.matches}
    assert "b2+1" in labels
    assert "y3+1" in labels

    tsv_path = _spectrum_fixture("annotation.tsv")
    try:
        export_spectrum_annotation_tsv(annotation, tsv_path)
        header = tsv_path.read_text().splitlines()[0]
        assert header.startswith("spectrum_id\tpeptide\tseries")
    finally:
        tsv_path.unlink(missing_ok=True)

    payload = build_spectrum_plot_payload(spectrum, annotation=annotation)
    rendered = json.loads(payload.to_stable_json())
    assert rendered["document_schema"]["document_kind"] == "spectrum_plot_payload"
    labeled_peaks = [peak for peak in rendered["peaks"] if peak["labels"]]
    assert labeled_peaks
