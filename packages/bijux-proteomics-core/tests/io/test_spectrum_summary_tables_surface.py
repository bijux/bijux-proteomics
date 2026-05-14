# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_mzml
from bijux_proteomics.io.spectra import (
    build_spectrum_summary_table_report,
    parse_mgf,
    render_spectrum_distribution_tsv,
    render_spectrum_summary_tsv,
)


def _spectra_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "spectra" / name


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_mgf_summary_tables_report_ms2_assumption_and_distributions() -> None:
    report = parse_mgf(_spectra_fixture("multi.mgf"))
    summary = build_spectrum_summary_table_report(
        report.accepted_spectra,
        source_kind="mgf",
        rejected_count=len(report.rejected_blocks),
    )

    assert summary.source_kind == "mgf"
    assert summary.ms_level_policy == "mgf_assumed_ms2"
    assert summary.ms1_spectrum_count == 0
    assert summary.ms2_spectrum_count == 2
    assert summary.unknown_ms_level_count == 0
    assert summary.retention_time_min_seconds is not None
    assert summary.precursor_mz_distribution
    assert summary.peak_count_distribution


def test_mzml_summary_tables_report_ms1_ms2_and_render_tsv() -> None:
    report = parse_mzml(_format_fixture("practical_review.mzml"))
    summary = build_spectrum_summary_table_report(
        report.accepted_spectra,
        source_kind="mzml",
        rejected_count=len(report.rejected_spectra),
    )

    assert summary.source_kind == "mzml"
    assert summary.ms_level_policy == "reported"
    assert summary.ms1_spectrum_count == 1
    assert summary.ms2_spectrum_count == 1
    assert summary.retention_time_min_seconds == 60.0
    assert summary.retention_time_max_seconds == 65.0

    summary_tsv = render_spectrum_summary_tsv(summary)
    charge_tsv = render_spectrum_distribution_tsv(
        summary.charge_distribution,
        distribution_name="charge",
    )

    assert "ms1_spectrum_count" in summary_tsv
    assert "mzml" in summary_tsv
    assert "distribution\tbucket\tcount" in charge_tsv
