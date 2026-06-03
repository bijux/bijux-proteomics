# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import build_fragpipe_import_benchmark_report


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "fragpipe"
    )


def test_fragpipe_import_benchmark_report_preserves_q_value_counts_and_ordering() -> (
    None
):
    root = _bundle_root()

    report = build_fragpipe_import_benchmark_report(
        root / "psm.tsv",
        peptide_tsv_path=root / "combined_peptide.tsv",
        protein_tsv_path=root / "combined_protein.tsv",
    )

    assert report.summary.source_q_value_psm_count == 3
    assert report.summary.imported_q_value_psm_count == 3
    assert report.summary.source_q_value_peptide_count == 2
    assert report.summary.imported_q_value_peptide_count == 2
    assert report.summary.q_value_behavior_matched is True
    assert report.q_value_behavior.source_psm_q_values_monotonic is True
    assert report.q_value_behavior.imported_psm_q_values_monotonic is True
    assert report.q_value_behavior.source_peptide_q_values_monotonic is True
    assert report.q_value_behavior.imported_peptide_q_values_monotonic is True
    assert report.q_value_behavior.max_psm_absolute_difference == 0.0
    assert report.q_value_behavior.max_peptide_absolute_difference == 0.0
    assert tuple(entry.entity_id for entry in report.q_value_behavior.psm_entries) == (
        "runA.1001.1001.2",
        "runA.1002.1002.3",
        "runA.1003.1003.2",
    )
    assert tuple(
        entry.entity_id for entry in report.q_value_behavior.peptide_entries
    ) == (
        "ACDMK|AC[+57.021464]DM[+15.994915]K|3",
        "PEPTIDE|PEP[+15.994915]TIDE|2",
    )
