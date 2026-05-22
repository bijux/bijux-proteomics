# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    build_diann_benchmark_report,
    render_diann_benchmark_count_comparisons_tsv,
    render_diann_benchmark_protein_quantities_tsv,
    render_diann_benchmark_summary_tsv,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_diann_benchmark_renderers_emit_stable_ledgers() -> None:
    report = build_diann_benchmark_report(_fixture("diann_biological_report.tsv"))

    summary_tsv = render_diann_benchmark_summary_tsv(report)
    count_tsv = render_diann_benchmark_count_comparisons_tsv(report)
    quantity_tsv = render_diann_benchmark_protein_quantities_tsv(report)

    assert "field\tvalue" in summary_tsv
    assert "protein_quantities_matched\ttrue" in summary_tsv
    assert "comparison_id\tsource_count\timported_count\tmatched" in count_tsv
    assert "excluded_q_value_rows\t1\t1\ttrue" in count_tsv
    assert "entity_id\tsample_id\tsource_quantity\timported_quantity" in quantity_tsv
    assert "PG001\tT1\t1600\t1600\t0\ttrue" in quantity_tsv
