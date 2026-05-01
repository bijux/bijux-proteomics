# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia_iteration12 import (
    DiaMissingnessReason,
    DiaQuantMissingnessEntry,
    build_dia_quant_missingness_report,
)


def test_build_dia_quant_missingness_report_counts_reasons() -> None:
    report = build_dia_quant_missingness_report(
        (
            DiaQuantMissingnessEntry(
                precursor_id="p1",
                peptide_sequence="PEPTIDEK",
                protein_group_id="pg1",
                run_id="run-a",
                reason=DiaMissingnessReason.LIBRARY_COVERAGE_GAP,
            ),
            DiaQuantMissingnessEntry(
                precursor_id="p2",
                peptide_sequence="PEPTIDER",
                protein_group_id="pg1",
                run_id="run-a",
                reason=DiaMissingnessReason.LIBRARY_COVERAGE_GAP,
            ),
            DiaQuantMissingnessEntry(
                precursor_id="p3",
                peptide_sequence="ACDMPEP",
                protein_group_id="pg2",
                run_id="run-b",
                reason=DiaMissingnessReason.SIGNAL_BELOW_THRESHOLD,
            ),
        )
    )

    assert report.reason_counts["library_coverage_gap"] == 2
    assert report.reason_counts["signal_below_threshold"] == 1
