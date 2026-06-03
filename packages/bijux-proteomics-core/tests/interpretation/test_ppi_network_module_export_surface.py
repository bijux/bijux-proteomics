# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    build_ppi_network_module_report,
    parse_ppi_edge_table,
    parse_protein_reference_table,
    parse_protein_set_table,
    render_ppi_isolated_protein_tsv,
    render_ppi_module_enrichment_tsv,
    render_ppi_module_tsv,
    render_ppi_network_edge_tsv,
    render_ppi_network_module_summary_tsv,
    render_rejected_ppi_edge_tsv,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_ppi_network_module_renderers_emit_edge_module_isolated_and_enrichment_ledgers() -> (
    None
):
    significant = parse_protein_reference_table(_fixture_path("ppi_significant.tsv"))
    edges = parse_ppi_edge_table(_fixture_path("ppi_edges.tsv"))
    invalid_edges = parse_ppi_edge_table(_fixture_path("ppi_edges_invalid.tsv"))
    protein_sets = parse_protein_set_table(_fixture_path("protein_set_enrichment.tsv"))
    report = build_ppi_network_module_report(
        significant.accepted_entries,
        edges.accepted_records,
        protein_set_records=protein_sets.accepted_records,
    )

    summary_tsv = render_ppi_network_module_summary_tsv(report)
    edge_tsv = render_ppi_network_edge_tsv(report)
    module_tsv = render_ppi_module_tsv(report)
    isolated_tsv = render_ppi_isolated_protein_tsv(report)
    enrichment_tsv = render_ppi_module_enrichment_tsv(report)
    rejected_tsv = render_rejected_ppi_edge_tsv(invalid_edges)

    assert summary_tsv.splitlines()[0].startswith(
        "significant_protein_count\tretained_edge_count"
    )
    assert "ppi_module:P001,P002,P003" in edge_tsv
    assert "hub_protein_refs" in module_tsv.splitlines()[0]
    assert "P004" in isolated_tsv
    assert "stress_panel" in enrichment_tsv
    assert "duplicate undirected ppi edge for P001 and P002" in rejected_tsv
