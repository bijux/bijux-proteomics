# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import (
    build_fragpipe_import_benchmark_report,
    render_fragpipe_benchmark_summary_tsv,
    render_fragpipe_count_comparisons_tsv,
    render_fragpipe_protein_group_comparison_tsv,
    render_fragpipe_q_value_comparison_tsv,
)


def _bundle_root() -> Path:
    return (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "search_result_bundles"
        / "fragpipe"
    )


def test_fragpipe_import_benchmark_renderers_expose_count_protein_and_qvalue_ledgers() -> (
    None
):
    root = _bundle_root()

    report = build_fragpipe_import_benchmark_report(
        root / "psm.tsv",
        peptide_tsv_path=root / "combined_peptide.tsv",
        protein_tsv_path=root / "combined_protein.tsv",
    )

    assert "source_psm_count" in render_fragpipe_benchmark_summary_tsv(report)
    assert "comparison_id" in render_fragpipe_count_comparisons_tsv(report)
    assert "missing_in_import" in render_fragpipe_protein_group_comparison_tsv(report)
    assert "absolute_difference" in render_fragpipe_q_value_comparison_tsv(
        report.q_value_behavior.psm_entries
    )
    assert "entity_kind" in render_fragpipe_q_value_comparison_tsv(
        report.q_value_behavior.peptide_entries
    )
