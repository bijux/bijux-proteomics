# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import build_diann_benchmark_report


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_diann_benchmark_report_preserves_protein_group_quantities() -> None:
    report = build_diann_benchmark_report(_fixture("diann_biological_report.tsv"))

    assert report.summary.source_protein_quantity_count == 30
    assert report.summary.imported_protein_quantity_count == 30
    assert report.summary.exact_protein_quantity_match_count == 30
    assert report.summary.max_protein_quantity_difference == 0.0
    assert report.summary.protein_quantities_matched is True

    comparison_lookup = {
        (entry.entity_id, entry.sample_id): entry
        for entry in report.protein_quantity_comparisons
    }
    assert comparison_lookup[("PG001", "T1")].source_quantity == 1600.0
    assert comparison_lookup[("PG001", "T1")].imported_quantity == 1600.0
    assert comparison_lookup[("PG002", "C2")].source_quantity == 1750.0
    assert comparison_lookup[("PG002", "C2")].imported_quantity == 1750.0
