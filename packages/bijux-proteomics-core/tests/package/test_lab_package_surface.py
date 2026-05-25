# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics.lab as lab


def test_lab_package_exports_run_diagnosis_surface() -> None:
    rows = lab.classify_run_failure(
        (
            lab.RunDiagnosisQcEntry(
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
            lab.RunDiagnosisQcEntry(
                run_id="run_identification",
                tic=980_000.0,
                bpc=148_000.0,
                ms1_count=1190,
                ms2_count=9100,
                id_count=420,
                median_rt=1810.0,
                median_peak_width=12.5,
                missingness=0.10,
            ),
            lab.RunDiagnosisQcEntry(
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
    rendered = lab.render_run_diagnosis_tsv(rows)

    assert hasattr(lab, "classify_run_failure")
    assert hasattr(lab, "render_run_diagnosis_tsv")
    assert any(
        row.failure_class is lab.RunFailureClass.IDENTIFICATION_FAILURE for row in rows
    )
    assert "secondary_reasons" in rendered
