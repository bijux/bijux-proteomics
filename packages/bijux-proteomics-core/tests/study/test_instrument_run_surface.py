# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.study import (
    InstrumentRunRecord,
    build_instrument_run_summary_report,
)


def test_build_instrument_run_summary_report_tracks_batches_order_and_qc_runs() -> None:
    report = build_instrument_run_summary_report(
        (
            InstrumentRunRecord(
                run_id="run-001",
                instrument_id="inst-a",
                acquisition_method="DDA_HCD",
                acquisition_date="2026-05-01",
                batch_id="B1",
                run_order=2,
                qc_sample=False,
            ),
            InstrumentRunRecord(
                run_id="run-000",
                instrument_id="inst-a",
                acquisition_method="DDA_HCD",
                acquisition_date="2026-05-01",
                batch_id="B1",
                run_order=1,
                qc_sample=True,
            ),
        )
    )

    assert report.run_count == 2
    assert report.instrument_count == 1
    assert report.batch_count == 1
    assert report.qc_sample_count == 1
    assert report.records[0].run_id == "run-000"
