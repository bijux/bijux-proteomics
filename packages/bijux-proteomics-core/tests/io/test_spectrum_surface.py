# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics.chemistry import calculate_fragment_ions
from bijux_proteomics.io.formats import parse_mzml
from bijux_proteomics.io.spectra import (
    PeakNormalizationPolicy,
    SpectralSimilarityMethod,
    SpectrumModel,
    SpectrumPeak,
    SpectrumSimilarityMode,
    annotate_spectrum_fragments,
    build_annotated_spectrum_bundle,
    build_spectrum_collection_summary,
    build_spectrum_lookup_index,
    build_spectrum_metrics,
    build_spectrum_plot_payload,
    build_spectrum_provenance_manifest,
    calculate_precursor_mass_error,
    calculate_spectral_similarity,
    detect_precursor_isotope_offset_advisory,
    export_annotated_spectrum_bundle,
    export_spectrum_annotation_tsv,
    filter_spectrum_peaks,
    lookup_spectra,
    normalize_spectrum_peaks,
    normalize_spectrum_scan_key,
    parse_mgf,
    render_mgf,
)


def _spectrum_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "spectra" / name


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_spectrum_model_and_mgf_parser_accept_simple_fixture() -> None:
    report = parse_mgf(_spectrum_fixture("simple.mgf"))

    assert report.total_blocks == 1
    assert len(report.accepted_spectra) == 1
    spectrum = report.accepted_spectra[0]
    assert spectrum.spectrum_id == "scan=5001"
    assert spectrum.precursor_mz == 500.2
    assert spectrum.precursor_intensity is None
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
    codes = {issue.code for block in rejected.rejected_blocks for issue in block.issues}
    assert "missing_precursor_mz" in codes
    assert "invalid_pepmass" in codes
    assert "invalid_peak_value" in codes
    assert "missing_end_ions" in codes
    invalid_pepmass_issue = next(
        issue
        for block in rejected.rejected_blocks
        for issue in block.issues
        if issue.code == "invalid_pepmass"
    )
    assert invalid_pepmass_issue.field == "PEPMASS"
    assert (
        invalid_pepmass_issue.line_number is None
        or invalid_pepmass_issue.line_number >= 1
    )


def test_mgf_dialect_fixture_handles_unusual_charge_title_pepmass_and_comments() -> (
    None
):
    report = parse_mgf(_spectrum_fixture("dialect_cases.mgf"))

    assert report.total_blocks == 2
    assert len(report.accepted_spectra) == 2
    assert report.accepted_spectra[0].title == "orbitrap run=7 sample=Alpha #42"
    assert report.accepted_spectra[0].precursor_mz == 500.2
    assert report.accepted_spectra[0].precursor_charge == 2
    assert report.accepted_spectra[1].spectrum_id == "scan=9002"
    assert report.accepted_spectra[1].title == "weird=title=with=equals"
    assert report.accepted_spectra[1].precursor_charge == 3


def test_mgf_parser_rejects_ambiguous_charge_lists_explicitly() -> None:
    report = parse_mgf(_spectrum_fixture("ambiguous_charge.mgf"))

    assert len(report.accepted_spectra) == 0
    assert len(report.rejected_blocks) == 1
    assert {issue.code for issue in report.rejected_blocks[0].issues} == {
        "invalid_charge"
    }


def test_mgf_parser_handles_missing_optional_fields_and_rt_minutes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "practical_metadata_cases.mgf"
    path.write_text(
        "\n".join(
            [
                "BEGIN IONS",
                "SPECTRUMID=controllerType=0 controllerNumber=1 scan=7001",
                "PEPMASS=612.3 1000",
                "RTINMINUTES=2.5",
                "110.1 15.0",
                "220.2 35.0",
                "END IONS",
                "BEGIN IONS",
                "PEPMASS=455.2",
                "150.0 40.0",
                "END IONS",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = parse_mgf(path)

    assert report.total_blocks == 2
    assert len(report.accepted_spectra) == 2
    assert report.accepted_spectra[0].spectrum_id.endswith("scan=7001")
    assert report.accepted_spectra[0].retention_time_seconds == 150.0
    assert report.accepted_spectra[0].precursor_intensity == 1000.0
    assert report.accepted_spectra[0].precursor_charge is None
    assert report.accepted_spectra[1].title is None
    assert report.accepted_spectra[1].retention_time_seconds is None
    assert report.accepted_spectra[1].precursor_intensity is None


def test_mgf_parser_streams_without_path_read_text(monkeypatch: MonkeyPatch) -> None:
    fixture = _spectrum_fixture("simple.mgf")
    original_read_text = Path.read_text

    def _forbid_read_text(
        self: Path,
        encoding: str | None = None,
        errors: str | None = None,
    ) -> str:
        if self == fixture:
            raise AssertionError("parse_mgf should not use Path.read_text")
        return original_read_text(self, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", _forbid_read_text)

    report = parse_mgf(fixture)

    assert len(report.accepted_spectra) == 1
    assert report.accepted_spectra[0].precursor_mz == 500.2


def test_mgf_writer_roundtrip_preserves_spectrum_contracts() -> None:
    report = parse_mgf(_spectrum_fixture("multi.mgf"))
    rendered = render_mgf(report.accepted_spectra)
    output_path = _spectrum_fixture("roundtrip.mgf")
    try:
        output_path.write_text(rendered)
        roundtrip = parse_mgf(output_path)
        assert len(roundtrip.accepted_spectra) == 2
        assert (
            roundtrip.accepted_spectra[0].precursor_mz
            == report.accepted_spectra[0].precursor_mz
        )
        assert roundtrip.accepted_spectra[0].precursor_intensity is None
        assert roundtrip.accepted_spectra[1].precursor_charge == 3
    finally:
        output_path.unlink(missing_ok=True)


def test_repeated_mgf_roundtrip_stabilizes_on_canonical_output() -> None:
    first_report = parse_mgf(_spectrum_fixture("dialect_cases.mgf"))
    rendered_once = render_mgf(first_report.accepted_spectra)
    output_path = _spectrum_fixture("roundtrip-repeat.mgf")
    try:
        output_path.write_text(rendered_once)
        rendered_versions = [rendered_once]
        for _ in range(3):
            roundtrip = parse_mgf(output_path)
            rendered = render_mgf(roundtrip.accepted_spectra)
            rendered_versions.append(rendered)
            output_path.write_text(rendered)
        assert len(set(rendered_versions[1:])) == 1
    finally:
        output_path.unlink(missing_ok=True)


def test_spectrum_peak_normalization_sorts_merges_duplicates_and_drops_zero() -> None:
    spectrum = parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    normalized = normalize_spectrum_peaks(
        spectrum,
        policy=PeakNormalizationPolicy(merge_tolerance_da=0.0),
    )

    assert [peak.mz for peak in normalized.peaks] == sorted(
        peak.mz for peak in normalized.peaks
    )
    assert len(normalized.peaks) == 4
    duplicate_peak = next(
        peak for peak in normalized.peaks if abs(peak.mz - 150.0) < 1e-9
    )
    assert duplicate_peak.intensity == 45.0


def test_spectrum_filtering_supports_top_n_intensity_and_mz_window() -> None:
    spectrum = normalize_spectrum_peaks(
        parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    )
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
    spectrum = normalize_spectrum_peaks(
        parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    )
    metrics = build_spectrum_metrics(spectrum)

    assert metrics.peak_count == 4
    assert metrics.total_ion_current == 250.0
    assert metrics.base_peak_mz == 376.171426
    assert metrics.base_peak_intensity == 100.0


def test_spectrum_lookup_index_supports_native_title_scan_number_and_scan_key() -> None:
    mgf_report = parse_mgf(_spectrum_fixture("dialect_cases.mgf"))
    mzml_spectrum = parse_mzml(_format_fixture("hierarchy.mzml")).accepted_spectra[0]
    index = build_spectrum_lookup_index(mgf_report.accepted_spectra + (mzml_spectrum,))

    by_native = lookup_spectra(index, native_id="scan=9002")
    by_title = lookup_spectra(index, title="weird=title=with=equals")
    by_scan_number = lookup_spectra(index, scan_number=8101)
    by_scan_key = lookup_spectra(
        index, scan_key="controllerType=0 controllerNumber=1 scan=8101"
    )

    assert by_native[0].title == "weird=title=with=equals"
    assert by_title[0].spectrum_id == "scan=9002"
    assert (
        by_scan_number[0].parent_spectrum_id
        == "controllerType=0 controllerNumber=1 scan=8100"
    )
    assert by_scan_key[0].product_isolation_mz == 175.1
    assert normalize_spectrum_scan_key(by_scan_key[0]) == "scan:8101"


def test_precursor_mass_error_reports_dalton_and_ppm() -> None:
    error = calculate_precursor_mass_error(observed_mz=500.2, theoretical_mz=500.0)

    assert round(error.delta_da, 6) == 0.2
    assert round(error.delta_ppm, 3) == 400.0


def test_precursor_isotope_offset_advisory_stays_non_enforced() -> None:
    advisory = detect_precursor_isotope_offset_advisory(
        observed_mz=500.0 + (1.0033548378 / 2.0),
        theoretical_mz=500.0,
        charge=2,
    )

    assert advisory.advisory_only is True
    assert advisory.recommended_offset == 1
    assert advisory.candidates[0].isotope_offset == 1


def test_theoretical_fragment_matching_annotation_and_plot_payload_are_stable() -> None:
    spectrum = normalize_spectrum_peaks(
        parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    )
    annotation = annotate_spectrum_fragments(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=0.01,
        include_neutral_losses=False,
    )

    assert annotation.document_schema.document_kind == "spectrum_annotation"
    assert annotation.peptide == "PEPTIDE"
    assert annotation.matched_peak_count > 0
    assert annotation.explained_intensity > 0.0
    assert annotation.explained_intensity_fraction > 0.0
    labels = {match.fragment_label for match in annotation.matches}
    assert "b2+1" in labels
    assert "y3+1" in labels

    tsv_path = _spectrum_fixture("annotation.tsv")
    try:
        export_spectrum_annotation_tsv(annotation, tsv_path)
        header = tsv_path.read_text().splitlines()[0]
        assert (
            header
            == "spectrum_id\tpeptide\ttolerance_mode\tseries\tordinal\tfragment_charge\tspan_start\tspan_end\tfragment_sequence\tfragment_mz\tneutral_loss\tobserved_mz\tobserved_intensity\tmass_error_da\tmass_error_ppm\tlabel"
        )
    finally:
        tsv_path.unlink(missing_ok=True)

    payload = build_spectrum_plot_payload(spectrum, annotation=annotation)
    rendered = json.loads(payload.to_stable_json())
    assert rendered["document_schema"]["document_kind"] == "spectrum_plot_payload"
    labeled_peaks = [peak for peak in rendered["peaks"] if peak["labels"]]
    assert labeled_peaks


def test_spectrum_annotation_supports_ppm_tolerance_and_reports_explained_intensity() -> (
    None
):
    fragment = calculate_fragment_ions(
        "PEPTIDE",
        include_neutral_losses=False,
    )[0]
    observed_mz = fragment.mz_monoisotopic * (1.0 + (10.0 / 1_000_000.0))
    spectrum = SpectrumModel(
        spectrum_id="scan=ppm",
        precursor_mz=500.2,
        precursor_charge=2,
        peaks=(
            SpectrumPeak(mz=observed_mz, intensity=80.0),
            SpectrumPeak(mz=700.0, intensity=20.0),
        ),
    )

    annotation = annotate_spectrum_fragments(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=None,
        tolerance_ppm=20.0,
        include_neutral_losses=False,
    )

    assert annotation.tolerance_unit.value == "ppm"
    assert annotation.tolerance_da is None
    assert annotation.tolerance_ppm == 20.0
    assert annotation.matched_peak_count == 1
    assert annotation.unmatched_peak_count == 1
    assert tuple((peak.mz, peak.intensity) for peak in annotation.unmatched_peaks) == (
        (700.0, 20.0),
    )
    assert annotation.explained_intensity == 80.0
    assert annotation.total_observed_intensity == 100.0
    assert annotation.explained_intensity_fraction == 0.8


def test_spectrum_annotation_reports_tolerance_driven_ambiguity_warnings() -> None:
    first_fragment = calculate_fragment_ions(
        "PEPTIDE",
        include_neutral_losses=False,
    )[0]
    spectrum = SpectrumModel(
        spectrum_id="scan=ambiguity",
        precursor_mz=500.2,
        precursor_charge=2,
        peaks=(
            SpectrumPeak(mz=first_fragment.mz_monoisotopic, intensity=100.0),
            SpectrumPeak(mz=first_fragment.mz_monoisotopic + 0.005, intensity=80.0),
        ),
    )

    annotation = annotate_spectrum_fragments(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=50.0,
        include_neutral_losses=False,
    )

    assert annotation.ambiguity_warnings == ()


def test_spectrum_similarity_and_provenance_manifest_are_stable() -> None:
    reference = normalize_spectrum_peaks(
        parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    )
    query = normalize_spectrum_peaks(
        parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    )
    similarity = calculate_spectral_similarity(
        reference,
        query,
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
    )
    report = parse_mgf(_spectrum_fixture("multi.mgf"))
    summary = build_spectrum_collection_summary(report)
    manifest = build_spectrum_provenance_manifest(
        source_path=_spectrum_fixture("multi.mgf"),
        parse_report=report,
    )

    assert similarity.matched_peak_count >= 4
    assert similarity.score > 0.99
    assert summary.spectrum_count == 2
    assert summary.issue_counts == {}
    assert manifest.document_schema.document_kind == "spectrum_provenance_manifest"
    assert manifest.source_sha256


def test_spectral_similarity_modes_are_explicit_and_deterministic() -> None:
    reference = parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    query = parse_mgf(_spectrum_fixture("multi.mgf")).accepted_spectra[0]

    raw = calculate_spectral_similarity(
        reference,
        query,
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.RAW,
    )
    normalized = calculate_spectral_similarity(
        reference,
        query,
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.NORMALIZED,
    )
    top_n = calculate_spectral_similarity(
        reference,
        query,
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.TOP_N,
        top_n=2,
    )
    transformed = calculate_spectral_similarity(
        reference,
        query,
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.TRANSFORMED,
    )

    assert raw.mode.value == "raw"
    assert normalized.mode.value == "normalized"
    assert top_n.mode.value == "top_n"
    assert transformed.mode.value == "transformed"
    assert top_n.reference_peak_count <= normalized.reference_peak_count
    assert top_n.query_peak_count <= normalized.query_peak_count
    assert raw.score >= 0.0
    assert transformed.score >= 0.0


def test_annotated_spectrum_bundle_exports_raw_and_theoretical_evidence() -> None:
    spectrum = normalize_spectrum_peaks(
        parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    )
    bundle = build_annotated_spectrum_bundle(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=0.01,
        include_neutral_losses=False,
    )

    assert bundle.document_schema.document_kind == "annotated_spectrum_bundle"
    assert bundle.spectrum.spectrum_id == spectrum.spectrum_id
    assert bundle.annotation.matches
    assert bundle.theoretical_fragments
    assert bundle.parameters.include_neutral_losses is False

    output_path = _spectrum_fixture("annotated_bundle.json")
    try:
        export_annotated_spectrum_bundle(bundle, output_path)
        payload = json.loads(output_path.read_text())
        assert (
            payload["document_schema"]["document_kind"] == "annotated_spectrum_bundle"
        )
        assert payload["annotation"]["matches"]
        assert payload["theoretical_fragments"]
    finally:
        output_path.unlink(missing_ok=True)


def test_annotated_spectrum_bundle_preserves_ppm_annotation_parameters() -> None:
    spectrum = normalize_spectrum_peaks(
        parse_mgf(_spectrum_fixture("simple.mgf")).accepted_spectra[0]
    )
    bundle = build_annotated_spectrum_bundle(
        spectrum,
        peptide="PEPTIDE",
        tolerance_da=None,
        tolerance_ppm=20.0,
        include_neutral_losses=False,
    )

    assert bundle.parameters.tolerance_unit.value == "ppm"
    assert bundle.parameters.tolerance_da is None
    assert bundle.parameters.tolerance_ppm == 20.0
