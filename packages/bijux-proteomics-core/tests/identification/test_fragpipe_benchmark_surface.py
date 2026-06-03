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


def test_fragpipe_import_benchmark_report_preserves_source_row_counts_and_protein_groups() -> (
    None
):
    root = _bundle_root()

    report = build_fragpipe_import_benchmark_report(
        root / "psm.tsv",
        peptide_tsv_path=root / "combined_peptide.tsv",
        protein_tsv_path=root / "combined_protein.tsv",
    )

    assert report.summary.source_psm_count == 3
    assert report.summary.imported_psm_count == 3
    assert report.summary.source_peptide_count == 2
    assert report.summary.imported_peptide_count == 2
    assert report.summary.source_protein_group_count == 3
    assert report.summary.imported_protein_group_count == 3
    assert report.summary.psm_count_matched is True
    assert report.summary.peptide_count_matched is True
    assert report.summary.protein_group_count_matched is True
    assert report.summary.protein_group_overlap_count == 3
    assert report.summary.missing_protein_group_count == 0
    assert report.summary.extra_protein_group_count == 0
    assert report.protein_group_comparison.matched is True
    assert report.protein_group_comparison.source_protein_refs == (
        "DECOY_sp|P99999|DECOY_PROT",
        "sp|P12345|KINASE_HUMAN",
        "sp|P23456|TRANSFER_HUMAN",
    )
