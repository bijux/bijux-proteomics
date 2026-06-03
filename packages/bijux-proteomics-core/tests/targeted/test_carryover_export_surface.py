# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io import parse_experimental_design_table
from bijux_proteomics.targeted import (
    build_skyline_result_import_report,
    build_targeted_carryover_report,
    render_targeted_carryover_candidates_tsv,
    render_targeted_carryover_summary_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_render_targeted_carryover_exports_keep_ordered_review_visible() -> None:
    import_report = build_skyline_result_import_report(
        _format_fixture("skyline_targeted_carryover_results.tsv")
    )
    design_entries = parse_experimental_design_table(
        _format_fixture("skyline_targeted_carryover.design.tsv")
    ).accepted_entries
    report = build_targeted_carryover_report(import_report, design_entries)

    summary_tsv = render_targeted_carryover_summary_tsv(report)
    candidates_tsv = render_targeted_carryover_candidates_tsv(report)

    assert (
        "source_name\trun_count\tprecursor_count\tcandidate_entry_count" in summary_tsv
    )
    assert "Skyline\t4\t2\t2\t2\t1" in summary_tsv
    assert (
        "source_high.raw\tsource_high\t1\tblank_after_source.raw\tblank_after_source\t2\t1\tCARRYPEP/2\tCARRYPEP\tP100\t200000\t4000\t0.020000\t0.9333\thigh_intensity_previous_run|low_level_repeated_signal|immediate_run_order_followup"
        in candidates_tsv
    )
    assert (
        "source_high.raw\tsource_high\t1\ttarget_sample.raw\ttarget_sample\t3\t2\tCARRYPEP/2\tCARRYPEP\tP100\t200000\t2000\t0.010000\t0.8000\thigh_intensity_previous_run|low_level_repeated_signal"
        in candidates_tsv
    )
