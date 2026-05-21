# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia import build_diann_run_qc_report


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "diann"
    )


def test_build_diann_run_qc_report_keeps_run_identity_counts_visible() -> None:
    report = build_diann_run_qc_report(_bundle_root() / "diann_run_qc_report.tsv")

    assert report.source_name == "DIA-NN"
    assert report.summary.run_count == 3
    assert report.summary.sample_count == 3
    assert report.summary.union_precursor_key_count == 4
    assert report.summary.union_protein_group_id_count == 3
    assert report.summary.union_protein_id_count == 4
    assert report.summary.flagged_run_count == 0
    assert "identity burden visible per run" in report.note

    first_run = report.run_entries[0]
    assert first_run.run_name == "raw_A"
    assert first_run.sample_name == "sample_A"
    assert first_run.precursor_id_count == 4
    assert first_run.precursor_key_count == 4
    assert first_run.protein_group_id_count == 3
    assert first_run.protein_id_count == 4
    assert first_run.observed_precursor_quantity_count == 4
    assert first_run.observed_protein_quantity_count == 3

    weak_run = report.run_entries[2]
    assert weak_run.run_name == "raw_C"
    assert weak_run.precursor_id_count == 1
    assert weak_run.precursor_key_count == 1
    assert weak_run.protein_group_id_count == 1
    assert weak_run.protein_id_count == 1


def test_build_diann_run_qc_report_respects_decoy_and_q_value_filters() -> None:
    report = build_diann_run_qc_report(
        _bundle_root() / "diann_run_qc_report.tsv",
        include_decoys=False,
        max_q_value=0.0035,
    )

    assert report.summary.run_count == 2
    assert report.summary.union_precursor_key_count == 4
    assert tuple(entry.run_name for entry in report.run_entries) == ("raw_A", "raw_B")
