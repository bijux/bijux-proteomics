# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation import (
    build_ppi_network_module_report,
    parse_ppi_edge_table,
    parse_protein_reference_table,
    parse_protein_set_table,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_build_ppi_network_module_report_keeps_isolated_proteins_outside_modules() -> (
    None
):
    significant = parse_protein_reference_table(_fixture_path("ppi_significant.tsv"))
    edges = parse_ppi_edge_table(_fixture_path("ppi_edges.tsv"))
    protein_sets = parse_protein_set_table(_fixture_path("protein_set_enrichment.tsv"))

    report = build_ppi_network_module_report(
        significant.accepted_entries,
        edges.accepted_records,
        protein_set_records=protein_sets.accepted_records,
    )

    assert report.summary.significant_protein_count == 5
    assert report.summary.retained_edge_count == 2
    assert report.summary.module_count == 1
    assert report.summary.isolated_protein_count == 2
    module = report.modules[0]
    assert module.module_id == "ppi_module:P001,P002,P003"
    assert module.protein_refs == ("P001", "P002", "P003")
    assert module.hub_protein_refs == ("P002",)
    assert {entry.protein_ref for entry in report.isolated_proteins} == {"P004", "P999"}
    assert all(entry.module_id == module.module_id for entry in report.edge_entries)
    assert any(
        entry.module_id == module.module_id and entry.set_id == "stress_panel"
        for entry in report.module_enrichments
    )
