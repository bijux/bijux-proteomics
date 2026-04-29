# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import (
    build_instrument_batch_qc_report,
    build_lcms_run_qc_report,
    calculate_peptide_mz,
    parse_experimental_design_table,
    PsmRecord,
    QcDigestionSpecificity,
    SpectrumModel,
    SpectrumPeak,
    TargetDecoyLabel,
)


PROTEIN_SEQUENCES = {
    "P11111": "KACDEFGKRAA",
    "CON__KERATIN": "KMSSQQLLLLKA",
}


def _qc_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "qc" / name


def _design_entries() -> dict[str, object]:
    report = parse_experimental_design_table(_qc_fixture("batch.design.tsv"))
    return {entry.sample_id: entry for entry in report.accepted_entries}


def _spectrum_for_peptide(
    spectrum_id: str,
    peptide: str,
    *,
    charge: int,
    retention_time_seconds: float,
    ppm_error: float,
) -> SpectrumModel:
    theoretical_mz = calculate_peptide_mz(peptide, charge=charge)
    observed_mz = theoretical_mz * (1.0 + (ppm_error / 1_000_000.0))
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=observed_mz,
        precursor_charge=charge,
        retention_time_seconds=retention_time_seconds,
        peaks=(
            SpectrumPeak(mz=max(observed_mz - 20.0, 50.0), intensity=1200.0),
            SpectrumPeak(mz=observed_mz, intensity=4200.0),
            SpectrumPeak(mz=observed_mz + 15.0, intensity=800.0),
        ),
    )


def _unidentified_spectrum(
    spectrum_id: str,
    *,
    charge: int,
    retention_time_seconds: float,
) -> SpectrumModel:
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=500.0,
        precursor_charge=charge,
        retention_time_seconds=retention_time_seconds,
        peaks=(
            SpectrumPeak(mz=200.0, intensity=1000.0),
            SpectrumPeak(mz=500.0, intensity=3000.0),
        ),
    )


def _psm(
    spectrum_id: str,
    peptide: str,
    *,
    charge: int,
    score: float,
    protein_refs: tuple[str, ...],
) -> PsmRecord:
    return PsmRecord(
        spectrum_id=spectrum_id,
        peptide=peptide,
        canonical_peptide=peptide,
        charge=charge,
        score=score,
        q_value=0.01,
        protein_refs=protein_refs,
        target_decoy_label=TargetDecoyLabel.TARGET,
    )


def _run_a_spectra() -> tuple[SpectrumModel, ...]:
    return (
        _spectrum_for_peptide("run-a:scan-001", "ACDEFGK", charge=2, retention_time_seconds=100.0, ppm_error=1.0),
        _spectrum_for_peptide("run-a:scan-002", "ACDEFGKR", charge=3, retention_time_seconds=160.0, ppm_error=-1.5),
        _spectrum_for_peptide("run-a:scan-003", "CDEFGK", charge=2, retention_time_seconds=220.0, ppm_error=2.0),
        _spectrum_for_peptide("run-a:scan-004", "DEFG", charge=1, retention_time_seconds=280.0, ppm_error=-2.5),
        _spectrum_for_peptide("run-a:scan-005", "MSSQQLLLLK", charge=2, retention_time_seconds=340.0, ppm_error=1.2),
        _unidentified_spectrum("run-a:scan-006", charge=2, retention_time_seconds=400.0),
    )


def _run_a_psms() -> tuple[PsmRecord, ...]:
    return (
        _psm("run-a:scan-001", "ACDEFGK", charge=2, score=120.0, protein_refs=("P11111",)),
        _psm("run-a:scan-002", "ACDEFGKR", charge=3, score=118.0, protein_refs=("P11111",)),
        _psm("run-a:scan-003", "CDEFGK", charge=2, score=110.0, protein_refs=("P11111",)),
        _psm("run-a:scan-004", "DEFG", charge=1, score=90.0, protein_refs=("P11111",)),
        _psm("run-a:scan-005", "MSSQQLLLLK", charge=2, score=87.0, protein_refs=("CON__KERATIN",)),
    )


def _run_b_spectra() -> tuple[SpectrumModel, ...]:
    return (
        _spectrum_for_peptide("run-b:scan-001", "ACDEFGK", charge=2, retention_time_seconds=105.0, ppm_error=0.8),
        _spectrum_for_peptide("run-b:scan-002", "ACDEFGKR", charge=3, retention_time_seconds=165.0, ppm_error=-1.1),
        _spectrum_for_peptide("run-b:scan-003", "CDEFGK", charge=2, retention_time_seconds=230.0, ppm_error=1.7),
        _spectrum_for_peptide("run-b:scan-004", "MSSQQLLLLK", charge=2, retention_time_seconds=295.0, ppm_error=1.4),
        _unidentified_spectrum("run-b:scan-005", charge=2, retention_time_seconds=360.0),
        _unidentified_spectrum("run-b:scan-006", charge=3, retention_time_seconds=420.0),
    )


def _run_b_psms() -> tuple[PsmRecord, ...]:
    return (
        _psm("run-b:scan-001", "ACDEFGK", charge=2, score=122.0, protein_refs=("P11111",)),
        _psm("run-b:scan-002", "ACDEFGKR", charge=3, score=117.0, protein_refs=("P11111",)),
        _psm("run-b:scan-003", "CDEFGK", charge=2, score=111.0, protein_refs=("P11111",)),
        _psm("run-b:scan-004", "MSSQQLLLLK", charge=2, score=88.0, protein_refs=("CON__KERATIN",)),
    )


def _run_c_spectra() -> tuple[SpectrumModel, ...]:
    return (
        _spectrum_for_peptide("run-c:scan-001", "ACDEFGK", charge=2, retention_time_seconds=110.0, ppm_error=12.0),
        _spectrum_for_peptide("run-c:scan-002", "MSSQQLLLLK", charge=2, retention_time_seconds=175.0, ppm_error=-14.0),
        _unidentified_spectrum("run-c:scan-003", charge=2, retention_time_seconds=240.0),
        _unidentified_spectrum("run-c:scan-004", charge=2, retention_time_seconds=305.0),
        _unidentified_spectrum("run-c:scan-005", charge=3, retention_time_seconds=370.0),
        _unidentified_spectrum("run-c:scan-006", charge=2, retention_time_seconds=435.0),
    )


def _run_c_psms() -> tuple[PsmRecord, ...]:
    return (
        _psm("run-c:scan-001", "ACDEFGK", charge=2, score=101.0, protein_refs=("P11111",)),
        _psm("run-c:scan-002", "MSSQQLLLLK", charge=2, score=74.0, protein_refs=("CON__KERATIN",)),
    )


def test_build_lcms_run_qc_report_captures_run_level_metrics() -> None:
    design_entry = _design_entries()["S1"]
    report = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entry,
        protein_sequences=PROTEIN_SEQUENCES,
    )

    specificity = {entry.specificity: entry for entry in report.digestion_specificity}

    assert report.run_id == "run-a"
    assert report.sample_id == "S1"
    assert report.batch == "B1"
    assert report.spectrum_count == 6
    assert report.identified_spectrum_count == 5
    assert round(report.identification_rate, 3) == 0.833
    assert report.mass_error.matched_psm_count == 5
    assert report.retention_time.span_seconds == 300.0
    assert report.retention_time.identified_span_seconds == 240.0
    assert report.missed_cleavage_count == 1
    assert report.missed_cleavage_rate == 0.2
    assert report.contaminant_summary.contaminant_psm_count == 1
    assert report.contaminant_summary.contaminant_psm_fraction == 0.2
    assert specificity[QcDigestionSpecificity.ENZYMATIC].count == 3
    assert specificity[QcDigestionSpecificity.SEMI_SPECIFIC].count == 1
    assert specificity[QcDigestionSpecificity.NON_SPECIFIC].count == 1


def test_build_lcms_run_qc_report_tracks_charge_and_contaminant_distribution() -> None:
    report = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        protein_sequences=PROTEIN_SEQUENCES,
    )

    spectrum_charges = {entry.charge_label: entry.count for entry in report.spectrum_charge_distribution}
    identified_charges = {entry.charge_label: entry.count for entry in report.identified_charge_distribution}

    assert spectrum_charges == {"1": 1, "2": 4, "3": 1}
    assert identified_charges == {"1": 1, "2": 3, "3": 1}
    assert report.contaminant_summary.contaminant_protein_counts == {"CON__KERATIN": 1}
    assert report.mass_error.median_abs_ppm is not None
    assert report.mass_error.max_abs_ppm is not None


def test_build_instrument_batch_qc_report_flags_outlier_run() -> None:
    design_entries = _design_entries()
    run_a = build_lcms_run_qc_report(
        _run_a_spectra(),
        _run_a_psms(),
        design_entry=design_entries["S1"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    run_b = build_lcms_run_qc_report(
        _run_b_spectra(),
        _run_b_psms(),
        design_entry=design_entries["S2"],
        protein_sequences=PROTEIN_SEQUENCES,
    )
    run_c = build_lcms_run_qc_report(
        _run_c_spectra(),
        _run_c_psms(),
        design_entry=design_entries["S3"],
        protein_sequences=PROTEIN_SEQUENCES,
    )

    batch_report = build_instrument_batch_qc_report((run_a, run_b, run_c))
    outlier = next(entry for entry in batch_report.runs if entry.run_id == "run-c")

    assert batch_report.batch_id == "B1"
    assert batch_report.instrument == "Orbitrap-A"
    assert batch_report.run_count == 3
    assert batch_report.outlier_run_ids == ("run-c",)
    assert "low_identification_rate" in outlier.outlier_reasons
    assert "high_mass_error" in outlier.outlier_reasons
