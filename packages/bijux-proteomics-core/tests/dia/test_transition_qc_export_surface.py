# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import (
    build_transition_qc_report_from_table,
    render_transition_qc_sample_tsv,
    render_transition_qc_summary_tsv,
    render_transition_qc_transition_tsv,
    render_transition_qc_weak_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_render_transition_qc_exports_keep_transition_and_weak_ledgers_visible() -> (
    None
):
    report = build_transition_qc_report_from_table(
        _format_fixture("transition_quant.tsv")
    )

    summary_tsv = render_transition_qc_summary_tsv(report)
    transition_tsv = render_transition_qc_transition_tsv(report)
    sample_tsv = render_transition_qc_sample_tsv(report)
    weak_tsv = render_transition_qc_weak_tsv(report)

    assert "source_name\tprecursor_count\ttransition_count" in summary_tsv
    assert (
        "transition_id\tprecursor_id\tprecursor_charge\tpeptide_sequence"
        in transition_tsv
    )
    assert (
        "transition_id\tprecursor_id\tsample_id\trun_ids\tintensity\tretention_time_minutes"
        in sample_tsv
    )
    assert "transition_id\tprecursor_id\tdetected_sample_count" in weak_tsv
    assert "transition table\t2\t4\t3\t7\t5\t1" in summary_tsv
    assert (
        "tr_y6_b\tprec_b\t3\tACDMPEP\tP002\ty6\t512.3\t715.4\t1\t2\t6000\t6000\t6000\t18.2"
        in (transition_tsv)
    )
    assert "tr_y7_a\tprec_a\ts1\trun_a\t120000\t12.5\t0.002\t160000\t0.75\t1\ttrue" in (
        sample_tsv
    )
    assert (
        "tr_y6_b\tprec_b\t1\t3\t0.333333\t0.0789474\tlow sample detection fraction;low median precursor-relative share"
        in (weak_tsv)
    )
