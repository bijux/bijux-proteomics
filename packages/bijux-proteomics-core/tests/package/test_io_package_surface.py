# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import io
from bijux_proteomics.identification import (
    SearchResultColumnMapping,
    TargetDecoyLabel,
    parse_psm_tsv,
)
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak
from bijux_proteomics.io.spectral_library import (
    SpectralLibraryEntry,
    SpectralLibraryFormat,
)
import bijux_proteomics.targeted as targeted


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_io_package_exports_mzml_reader_owner_surface() -> None:
    report = io.parse_mzml(_format_fixture("simple.mzml"))
    review = io.build_mzml_practical_review_report(
        _format_fixture("practical_review.mzml")
    )

    assert hasattr(io, "parse_mzml")
    assert hasattr(io, "inspect_mzml_decoding_support")
    assert hasattr(io, "build_mzml_practical_review_report")
    assert report.metadata.instrument_names == ("Q Exactive",)
    assert review.decoding_support.supported is True


def test_io_package_exports_spectrum_quality_owner_surface() -> None:
    report = io.build_spectrum_run_qc_report(
        (
            SpectrumModel(
                spectrum_id="scan=1",
                precursor_mz=500.2,
                precursor_intensity=50000.0,
                precursor_charge=2,
                peaks=tuple(
                    SpectrumPeak(mz=100.0 + offset, intensity=100.0)
                    for offset in range(8)
                ),
            ),
        ),
        source_kind="mgf",
    )
    rendered = io.render_spectrum_run_qc_spectra_tsv(report)

    assert hasattr(io, "build_spectrum_run_qc_report")
    assert hasattr(io, "render_spectrum_run_qc_spectra_tsv")
    assert report.spectrum_metrics[0].quality_tier.value == "high"
    assert "quality_tier" in rendered


def test_io_package_exports_spectrum_noise_owner_surface() -> None:
    rows = io.estimate_peak_noise(
        (
            SpectrumPeak(mz=100.0, intensity=5.0),
            SpectrumPeak(mz=101.0, intensity=10.0),
            SpectrumPeak(mz=102.0, intensity=40.0),
        )
    )
    rendered = io.render_peak_noise_tsv(rows)

    assert hasattr(io, "estimate_peak_noise")
    assert hasattr(io, "render_peak_noise_tsv")
    assert rows[0].peak_class.value == "noise"
    assert rows[2].peak_class.value == "signal"
    assert "peak_class" in rendered


def test_io_package_exports_peak_list_deisotoping_owner_surface() -> None:
    clusters = io.deisotope_peaks(
        (
            SpectrumPeak(mz=500.00000, intensity=120.0),
            SpectrumPeak(mz=501.00335, intensity=90.0),
            SpectrumPeak(mz=502.00671, intensity=45.0),
        )
    )
    rendered = io.render_deisotoped_peaks_tsv(clusters)

    assert hasattr(io, "deisotope_peaks")
    assert hasattr(io, "render_deisotoped_peaks_tsv")
    assert len(clusters) == 1
    assert clusters[0].charge == 1
    assert clusters[0].cluster_peak_indices == (0, 1, 2)
    assert "cluster_peak_indices" in rendered


def test_io_package_exports_spectrum_entropy_owner_surface() -> None:
    score = io.score_spectrum_entropy(
        (
            SpectrumPeak(mz=100.0, intensity=100.0),
            SpectrumPeak(mz=101.0, intensity=100.0),
            SpectrumPeak(mz=102.0, intensity=100.0),
            SpectrumPeak(mz=103.0, intensity=100.0),
            SpectrumPeak(mz=104.0, intensity=100.0),
            SpectrumPeak(mz=105.0, intensity=100.0),
        )
    )
    rendered = io.render_spectrum_entropy_tsv(score)

    assert hasattr(io, "score_spectrum_entropy")
    assert hasattr(io, "render_spectrum_entropy_tsv")
    assert score.entropy_quality_tier.value == "rich_fragment"
    assert score.normalized_entropy > 0.99
    assert "entropy_quality_tier" in rendered


def test_io_package_exports_spectral_library_intensity_agreement_owner_surface() -> (
    None
):
    agreement = io.compare_observed_to_library(
        SpectrumModel(
            spectrum_id="observed-library-check",
            precursor_mz=500.2,
            precursor_charge=2,
            peaks=(
                SpectrumPeak(mz=100.001, intensity=220.0),
                SpectrumPeak(mz=150.001, intensity=610.0),
                SpectrumPeak(mz=200.001, intensity=1000.0),
                SpectrumPeak(mz=250.001, intensity=790.0),
            ),
        ),
        SpectralLibraryEntry(
            library_entry_id="library:surface",
            source_format=SpectralLibraryFormat.MSP,
            spectrum_id="library:surface:spectrum",
            precursor_mz=500.2,
            precursor_charge=2,
            peptide_sequence="PEPTIDE",
            canonical_peptide="PEPTIDE",
            modification_count=0,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            spectrum=SpectrumModel(
                spectrum_id="library:surface:spectrum",
                precursor_mz=500.2,
                precursor_charge=2,
                peaks=(
                    SpectrumPeak(mz=100.0, intensity=1000.0),
                    SpectrumPeak(mz=150.0, intensity=800.0),
                    SpectrumPeak(mz=200.0, intensity=600.0),
                    SpectrumPeak(mz=250.0, intensity=200.0),
                ),
            ),
        ),
    )
    rendered = io.render_spectral_library_intensity_agreement_tsv((agreement,))

    assert hasattr(io, "compare_observed_to_library")
    assert hasattr(io, "render_spectral_library_intensity_agreement_tsv")
    assert agreement.intensity_agreement_tier.value == "downgraded"
    assert agreement.ranked_fragment_agreement < 0.6
    assert "missing_dominant_fragments" in rendered


def test_io_package_exports_transition_table_owner_surface() -> None:
    report = io.parse_transition_table(_format_fixture("transition_quant.tsv"))
    first_entry = report.accepted_entries[0]
    domain_record = first_entry.to_domain_record()

    assert hasattr(io, "parse_transition_table")
    assert len(report.accepted_entries) == 7
    assert first_entry.precursor_charge == 2
    assert first_entry.retention_time_minutes == 12.5
    assert domain_record.precursor_charge == 2
    assert domain_record.retention_time_minutes == 12.5


def test_io_package_exports_xic_extraction_owner_surface() -> None:
    report = io.extract_mzml_xic_traces(
        _format_fixture("xic_review.mzml"),
        _format_fixture("xic_targets.tsv"),
        tolerance_ppm=10.0,
    )
    rendered = io.render_xic_traces_tsv(report)

    assert hasattr(io, "parse_xic_target_table")
    assert hasattr(io, "extract_xic")
    assert hasattr(io, "extract_mzml_xic_traces")
    assert hasattr(io, "render_xic_extraction_tsv")
    assert hasattr(io, "render_xic_traces_tsv")
    assert report.eligible_spectra == 3
    assert len(report.trace_points) == 8
    assert "target_alpha\tscan=7000\t10\t500.000000" in rendered


def test_io_package_exports_chromatographic_peak_picking_owner_surface() -> None:
    report = io.extract_mzml_chromatographic_peaks(
        _format_fixture("chromatographic_peak_profile.mzml"),
        _format_fixture("chromatographic_peak_targets.tsv"),
        tolerance_ppm=10.0,
    )
    rendered = io.render_chromatographic_peaks_tsv(report)

    assert hasattr(io, "pick_chromatographic_peaks")
    assert hasattr(io, "pick_peak")
    assert hasattr(io, "extract_mzml_chromatographic_peaks")
    assert hasattr(io, "render_picked_chromatographic_peaks_tsv")
    assert hasattr(io, "render_chromatographic_peaks_tsv")
    assert len(report.peaks) == 3
    assert report.peaks[0].overlap_flag is True
    assert "target_single_peak_001\ttarget_single\t0\t60\t30\t160" in rendered


def test_io_package_exports_peak_shape_scoring_owner_surface() -> None:
    shape = io.score_peak_shape(
        (
            io.XicExtractionPoint(
                target_id="shape_target",
                rt=0.0,
                mz_lower=499.99,
                mz_upper=500.01,
                intensity=0.0,
                scan_id="scan=1",
            ),
            io.XicExtractionPoint(
                target_id="shape_target",
                rt=10.0,
                mz_lower=499.99,
                mz_upper=500.01,
                intensity=25.0,
                scan_id="scan=2",
            ),
            io.XicExtractionPoint(
                target_id="shape_target",
                rt=20.0,
                mz_lower=499.99,
                mz_upper=500.01,
                intensity=90.0,
                scan_id="scan=3",
            ),
            io.XicExtractionPoint(
                target_id="shape_target",
                rt=30.0,
                mz_lower=499.99,
                mz_upper=500.01,
                intensity=160.0,
                scan_id="scan=4",
            ),
            io.XicExtractionPoint(
                target_id="shape_target",
                rt=40.0,
                mz_lower=499.99,
                mz_upper=500.01,
                intensity=90.0,
                scan_id="scan=5",
            ),
            io.XicExtractionPoint(
                target_id="shape_target",
                rt=50.0,
                mz_lower=499.99,
                mz_upper=500.01,
                intensity=25.0,
                scan_id="scan=6",
            ),
            io.XicExtractionPoint(
                target_id="shape_target",
                rt=60.0,
                mz_lower=499.99,
                mz_upper=500.01,
                intensity=0.0,
                scan_id="scan=7",
            ),
        )
    )
    rendered = io.render_peak_shape_score_tsv((shape,))

    assert hasattr(io, "score_peak_shape")
    assert hasattr(io, "render_peak_shape_score_tsv")
    assert shape.shape_quality_tier.value == "gaussian_like"
    assert shape.smoothness_score > 0.9
    assert "shape_quality_tier" in rendered


def test_io_package_exports_retention_time_alignment_owner_surface() -> None:
    fit_report = io.fit_rt_alignment(
        (
            io.RetentionTimeAlignmentAnchor(
                run_id="shifted_run",
                peptide_id="anchor_alpha",
                observed_rt=20.0,
                reference_rt=10.0,
                anchor_confidence=1.0,
            ),
            io.RetentionTimeAlignmentAnchor(
                run_id="shifted_run",
                peptide_id="anchor_beta",
                observed_rt=50.0,
                reference_rt=40.0,
                anchor_confidence=1.0,
            ),
        ),
        min_anchor_count=2,
    )
    report = io.extract_mzml_retention_time_alignment(
        (
            _format_fixture("rt_alignment_reference.mzml"),
            _format_fixture("rt_alignment_shifted.mzml"),
        ),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
    )
    fit_rendered = io.render_rt_alignment_fit_models_tsv(fit_report)
    penalty_rows = io.apply_rt_residuals(
        (
            io.RetentionTimeIdentificationRow(
                entity_id="high_confidence_outlier",
                run_id="shifted_run",
                observed_rt=62.0,
                expected_rt=40.0,
                imported_confidence=0.99,
            ),
        ),
        fit_report,
        aligned_rt_tolerance_seconds=5.0,
    )
    penalty_rendered = io.render_rt_residual_penalties_tsv(penalty_rows)
    rendered = io.render_retention_time_alignment_residuals_tsv(report)

    assert hasattr(io, "fit_rt_alignment")
    assert hasattr(io, "apply_rt_residuals")
    assert hasattr(io, "align_chromatographic_peak_retention_times")
    assert hasattr(io, "extract_mzml_retention_time_alignment")
    assert hasattr(io, "render_rt_alignment_fit_models_tsv")
    assert hasattr(io, "render_rt_residual_penalties_tsv")
    assert hasattr(io, "render_retention_time_alignment_models_tsv")
    assert hasattr(io, "render_retention_time_alignment_residuals_tsv")
    assert hasattr(io, "render_retention_time_alignment_failed_anchors_tsv")
    assert fit_report.models[0].alignment_model == "confidence_weighted_shift"
    assert fit_report.models[0].rt_shift == 10.0
    assert penalty_rows[0].rt_outlier is True
    assert penalty_rows[0].rt_confidence_penalty == 0.2
    assert report.run_models[1].status.value == "aligned"
    assert report.run_models[1].alignment_model == "confidence_weighted_shift"
    assert report.run_models[1].rt_shift == 10.0
    assert len(report.flagged_residuals) == 1
    assert "shifted_run\tconfidence_weighted_shift\t10\t0\t0" in fit_rendered
    assert "high_confidence_outlier\t62\t50\t12\ttrue\t0.2000" in penalty_rendered
    assert (
        "anchor_gamma\tanchor_gamma_peak_001\tanchor_gamma_peak_001\t60\t80\t70"
        in rendered
    )


def test_io_package_exports_chromatographic_evidence_owner_surface() -> None:
    report = io.extract_mzml_chromatographic_evidence(
        (
            _format_fixture("rt_alignment_reference.mzml"),
            _format_fixture("rt_alignment_shifted.mzml"),
        ),
        _format_fixture("rt_alignment_targets.tsv"),
        tolerance_ppm=10.0,
        aligned_rt_tolerance_seconds=5.0,
    )
    rendered = io.render_chromatographic_peptide_evidence_tsv(report)

    assert hasattr(io, "score_chromatographic_evidence")
    assert hasattr(io, "extract_mzml_chromatographic_evidence")
    assert hasattr(io, "render_chromatographic_target_evidence_tsv")
    assert hasattr(io, "render_chromatographic_peptide_evidence_tsv")
    assert len(report.target_entries) == 4
    assert report.peptide_entries[0].chromatographic_evidence_score == 1.0
    assert (
        "PEPD\tanchor_delta\t2\t1\t1.0000\t1.0000\t1.0000\t0.0000\t0.5000\t0.7250"
        in rendered
    )


def test_io_package_exports_dia_fragment_coelution_owner_surface() -> None:
    raw_scores = io.score_fragment_coelution(
        (
            io.DiaFragmentTracePoint(
                precursor_id="prec_alpha",
                fragment_id="frag_y7",
                rt=10.0,
                intensity=10.0,
            ),
            io.DiaFragmentTracePoint(
                precursor_id="prec_alpha",
                fragment_id="frag_y7",
                rt=20.0,
                intensity=60.0,
            ),
            io.DiaFragmentTracePoint(
                precursor_id="prec_alpha",
                fragment_id="frag_y7",
                rt=30.0,
                intensity=10.0,
            ),
            io.DiaFragmentTracePoint(
                precursor_id="prec_alpha",
                fragment_id="frag_y8",
                rt=20.0,
                intensity=8.0,
            ),
            io.DiaFragmentTracePoint(
                precursor_id="prec_alpha",
                fragment_id="frag_y8",
                rt=30.0,
                intensity=55.0,
            ),
            io.DiaFragmentTracePoint(
                precursor_id="prec_alpha",
                fragment_id="frag_y8",
                rt=40.0,
                intensity=8.0,
            ),
        )
    )
    report = io.extract_mzml_dia_fragment_trace_coelution(
        (_format_fixture("dia_fragment_coelution.mzml"),),
        _format_fixture("dia_fragment_targets.tsv"),
        tolerance_ppm=10.0,
    )
    raw_rendered = io.render_dia_fragment_trace_coelution_tsv(raw_scores)
    rendered = io.render_dia_fragment_coelution_runs_tsv(report)

    assert hasattr(io, "score_fragment_coelution")
    assert hasattr(io, "score_dia_fragment_trace_coelution")
    assert hasattr(io, "extract_mzml_dia_fragment_trace_coelution")
    assert hasattr(io, "render_dia_fragment_trace_coelution_tsv")
    assert hasattr(io, "render_dia_fragment_coelution_runs_tsv")
    assert hasattr(io, "render_dia_fragment_coelution_fragments_tsv")
    assert raw_scores[0].failed_fragments == ("frag_y8",)
    assert raw_scores[0].coelution_score < 0.8
    assert len(report.run_entries) == 2
    assert report.run_entries[0].coelution_score == 1.0
    assert "prec_alpha\t2\t10.0000" in raw_rendered
    assert "prec_beta\tPEPB\tbeta_y7\t3\t2\t1\t10.0000\t0.5578\t0.2971" in rendered


def test_io_package_exports_fragment_ratio_stability_owner_surface() -> None:
    targeted_import_report = targeted.build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    targeted_report = io.build_targeted_fragment_ratio_stability_report(
        targeted_import_report
    )
    rendered = io.render_fragment_ratio_stability_fragments_tsv(targeted_report)

    assert hasattr(io, "build_targeted_fragment_ratio_stability_report")
    assert hasattr(io, "score_dia_fragment_ratio_stability")
    assert hasattr(io, "extract_mzml_dia_fragment_ratio_stability")
    assert hasattr(io, "render_fragment_ratio_stability_fragments_tsv")
    assert hasattr(io, "render_fragment_ratio_stability_observations_tsv")
    assert targeted_report.summary.fragment_entry_count == 4
    assert targeted_report.summary.unstable_fragment_count == 1
    assert (
        "targeted\tPEPTIDEK/2\tPEPTIDEK\ty8\t4\t3\t0.236842\t0.396731\t1\ttrue"
        in rendered
    )


def test_io_package_exports_chimeric_spectrum_owner_surface() -> None:
    spectra = io.parse_mzml(
        _format_fixture("chimeric_spectrum_review.mzml")
    ).accepted_spectra
    psm_records = parse_psm_tsv(
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "psm"
        / "chimeric_spectrum_candidates.tsv",
        mapping=SearchResultColumnMapping(
            spectrum_id="spectrum_id",
            peptide="peptide",
            charge="charge",
            score="score",
            q_value="q_value",
            protein_refs="proteins",
        ),
    ).accepted_records
    report = io.score_chimeric_spectra_from_psms(spectra, psm_records)
    rendered = io.render_chimeric_spectrum_competing_evidence_tsv(report)

    assert hasattr(io, "score_chimeric_spectra")
    assert hasattr(io, "score_chimeric_spectra_from_psms")
    assert hasattr(io, "render_chimeric_spectrum_spectra_tsv")
    assert hasattr(io, "render_chimeric_spectrum_competing_evidence_tsv")
    assert report.summary.flagged_chimeric_count == 0
    assert report.spectra[0].spectrum_id == "scan=9001"
    assert "scan=9002\tTIDEPEP\t2\tP22222\t45.0000" in rendered


def test_io_package_exports_raw_signal_evidence_card_owner_surface() -> None:
    report = io.extract_mzml_raw_signal_evidence_cards(
        (
            _format_fixture("raw_signal_card_reference.mzml"),
            _format_fixture("raw_signal_card_shifted.mzml"),
        ),
        _format_fixture("raw_signal_card_targets.tsv"),
        fragment_target_table=_format_fixture("raw_signal_card_fragment_targets.tsv"),
        spectrum_mzml_path=_format_fixture("chimeric_spectrum_review.mzml"),
        psm_path=(
            Path(__file__).resolve().parents[1]
            / "fixtures"
            / "psm"
            / "chimeric_spectrum_candidates.tsv"
        ),
        tolerance_ppm=10.0,
        fragment_ms_level=1,
        selected_precursor_ids=("prec_peptide",),
    )
    rendered = io.render_raw_signal_evidence_card_tsv(report)

    assert hasattr(io, "build_raw_signal_evidence_card_report")
    assert hasattr(io, "extract_mzml_raw_signal_evidence_cards")
    assert hasattr(io, "render_raw_signal_evidence_card_summary_tsv")
    assert hasattr(io, "render_raw_signal_evidence_card_tsv")
    assert hasattr(io, "render_raw_signal_evidence_cards_html")
    assert report.summary.card_count == 1
    assert report.cards[0].precursor_id == "prec_peptide"
    assert report.cards[0].fragment_run_entries[1].failed_fragment_ids == (
        "peptide_b4",
        "peptide_y8",
    )
    assert "raw-signal-card:prec_peptide\tprec_peptide\tPEPTIDE" in rendered


def test_io_package_exports_precursor_isotope_fit_owner_surface() -> None:
    report = io.extract_mzml_precursor_isotope_fit(
        (
            _format_fixture("precursor_isotope_fit_reference.mzml"),
            _format_fixture("precursor_isotope_fit_shifted.mzml"),
            _format_fixture("precursor_isotope_fit_wrong_charge.mzml"),
        ),
        _format_fixture("precursor_isotope_fit_targets.tsv"),
        extraction_tolerance_da=0.05,
        fit_tolerance_da=0.05,
        max_isotope_index=2,
    )
    rendered = io.render_precursor_isotope_fit_entries_tsv(report)

    assert hasattr(io, "extract_mzml_precursor_isotope_fit")
    assert hasattr(io, "render_precursor_isotope_fit_summary_tsv")
    assert hasattr(io, "render_precursor_isotope_fit_entries_tsv")
    assert hasattr(io, "render_precursor_isotope_fit_peaks_tsv")
    assert report.summary.flagged_entry_count == 2
    assert report.entries[0].run_id == "precursor_isotope_fit_reference"
    assert "precursor_isotope_fit_shifted\tprec_peptide_ms1\tprec_peptide" in rendered


def test_io_package_exports_precursor_validation_owner_surface() -> None:
    peptide_mass = 781.34938
    monoisotopic_mz = (peptide_mass + (2 * 1.007276466812)) / 2
    report = io.validate_precursor_isotope_charge(
        (
            io.PrecursorValidationWindow(
                precursor_id="precursor-001",
                rt=120.0,
                peaks=(
                    SpectrumPeak(mz=monoisotopic_mz, intensity=1200.0),
                    SpectrumPeak(
                        mz=monoisotopic_mz + (1.0033548378 / 2),
                        intensity=540.0,
                    ),
                    SpectrumPeak(
                        mz=monoisotopic_mz + ((2 * 1.0033548378) / 2),
                        intensity=210.0,
                    ),
                ),
            ),
        ),
        (
            io.PrecursorValidationQuery(
                precursor_id="precursor-001",
                assigned_mz=monoisotopic_mz,
                assigned_charge=3,
                rt=120.0,
                peptide_mass=peptide_mass,
            ),
        ),
    )
    rendered = io.render_precursor_validation_entries_tsv(report)

    assert hasattr(io, "validate_precursor_isotope_charge")
    assert hasattr(io, "render_precursor_validation_entries_tsv")
    assert hasattr(io, "render_precursor_validation_summary_tsv")
    assert report.entries[0].inferred_charge == 2
    assert "charge_mismatch" in rendered


def test_io_package_exports_input_integrity_owner_surface(tmp_path: Path) -> None:
    input_path = tmp_path / "integrity.tsv"
    input_path.write_text(
        ("sample_id\tintensity\tprotein_id\nS1\t100.0\tP1\nS1\tinvalid\tP2\n"),
        encoding="utf-8",
    )

    report = io.scan_input_integrity((input_path,))
    rendered = io.render_input_integrity_issues_tsv(report)

    assert hasattr(io, "scan_input_integrity")
    assert hasattr(io, "render_input_integrity_issues_tsv")
    assert report.total_issue_count == 2
    assert {issue.issue_code for issue in report.files[0].issues} == {
        "duplicate_id",
        "invalid_numeric_value",
    }
    assert "invalid_numeric_value" in rendered
