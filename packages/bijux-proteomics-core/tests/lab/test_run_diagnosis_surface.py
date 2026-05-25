# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.lab import (
    LabQcStatus,
    RunDiagnosisQcEntry,
    RunFailureClass,
    classify_run_failure,
    render_run_diagnosis_tsv,
)


def test_classify_run_failure_separates_chromatography_identification_and_intensity_failures() -> None:
    rows = classify_run_failure(
        (
            RunDiagnosisQcEntry(
                run_id="run_reference",
                tic=1_000_000.0,
                bpc=150_000.0,
                ms1_count=1200,
                ms2_count=9000,
                id_count=1800,
                median_rt=1800.0,
                median_peak_width=12.0,
                missingness=0.08,
            ),
            RunDiagnosisQcEntry(
                run_id="run_chrom",
                tic=940_000.0,
                bpc=138_000.0,
                ms1_count=1180,
                ms2_count=8200,
                id_count=1400,
                median_rt=2250.0,
                median_peak_width=21.0,
                missingness=0.34,
            ),
            RunDiagnosisQcEntry(
                run_id="run_ident",
                tic=980_000.0,
                bpc=148_000.0,
                ms1_count=1190,
                ms2_count=9100,
                id_count=420,
                median_rt=1810.0,
                median_peak_width=12.5,
                missingness=0.10,
            ),
            RunDiagnosisQcEntry(
                run_id="run_signal",
                tic=320_000.0,
                bpc=41_000.0,
                ms1_count=520,
                ms2_count=6700,
                id_count=980,
                median_rt=1790.0,
                median_peak_width=12.3,
                missingness=0.31,
            ),
        )
    )
    lookup = {row.run_id: row for row in rows}

    assert lookup["run_reference"].status is LabQcStatus.PASS
    assert lookup["run_reference"].failure_class is RunFailureClass.NO_FAILURE

    assert lookup["run_chrom"].status is LabQcStatus.FAIL
    assert lookup["run_chrom"].failure_class is RunFailureClass.CHROMATOGRAPHY_FAILURE
    assert lookup["run_chrom"].primary_reason in {
        "broad_peak_width",
        "retention_time_shift",
    }

    assert lookup["run_ident"].status is LabQcStatus.FAIL
    assert lookup["run_ident"].failure_class is RunFailureClass.IDENTIFICATION_FAILURE
    assert lookup["run_ident"].primary_reason == "low_identification_yield"

    assert lookup["run_signal"].status is LabQcStatus.FAIL
    assert lookup["run_signal"].failure_class is RunFailureClass.INTENSITY_FAILURE
    assert lookup["run_signal"].primary_reason in {"low_tic", "low_bpc", "low_ms1_count"}


def test_classify_run_failure_renders_tsv_and_preserves_secondary_reasons() -> None:
    rows = classify_run_failure(
        (
            RunDiagnosisQcEntry(
                run_id="run_a",
                tic=1_000_000.0,
                bpc=150_000.0,
                ms1_count=1200,
                ms2_count=9000,
                id_count=1800,
                median_rt=1800.0,
                median_peak_width=12.0,
                missingness=0.08,
            ),
            RunDiagnosisQcEntry(
                run_id="run_b",
                tic=450_000.0,
                bpc=62_000.0,
                ms1_count=640,
                ms2_count=8600,
                id_count=560,
                median_rt=1820.0,
                median_peak_width=12.8,
                missingness=0.27,
            ),
            RunDiagnosisQcEntry(
                run_id="run_c",
                tic=970_000.0,
                bpc=144_000.0,
                ms1_count=1185,
                ms2_count=9050,
                id_count=1760,
                median_rt=1795.0,
                median_peak_width=12.1,
                missingness=0.09,
            ),
        )
    )
    rendered = render_run_diagnosis_tsv(rows)
    run_b = next(row for row in rows if row.run_id == "run_b")

    assert run_b.status in {LabQcStatus.CAUTION, LabQcStatus.FAIL}
    assert run_b.secondary_reasons
    assert rendered.startswith(
        "run_id\tstatus\tfailure_class\tprimary_reason\tsecondary_reasons\n"
    )
    assert "run_b" in rendered
