# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json

from bijux_proteomics.review import (
    export_proteomics_evidence_graph,
    render_proteomics_evidence_graph_compact_json,
    render_proteomics_evidence_graph_edges_tsv,
    render_proteomics_evidence_graph_nodes_tsv,
)

from .test_evidence_graph_export_surface import build_graph_export_fixture


def test_evidence_graph_export_renders_external_inspection_assets() -> None:
    bundle = export_proteomics_evidence_graph(build_graph_export_fixture())

    node_tsv = render_proteomics_evidence_graph_nodes_tsv(bundle)
    edge_tsv = render_proteomics_evidence_graph_edges_tsv(bundle)
    compact_json = render_proteomics_evidence_graph_compact_json(bundle)
    payload = json.loads(compact_json)

    assert (
        "node_id\tentity_type\tentity_ref\tlabel\tclaim_state\ttrust_class" in node_tsv
    )
    assert (
        "protein:P11111\tprotein\tP11111\tP11111\tobserved\treviewed\tcx-1\tsample:S1"
        in node_tsv
    )
    assert (
        "source_node_id\ttarget_node_id\trelation\tsource_row_ref\tconfidence\tevidence_type\treason\tsupport_count"
        in edge_tsv
    )
    assert (
        "peptide:PEPTIDE\tprotein:P11111\tpeptide_quantifies_protein\tprotein_matrix.tsv:4\t0.93\tquantification"
        in edge_tsv
    )
    assert payload["node_count"] == 6
    assert payload["edge_count"] == 5
    assert payload["contradiction_node_count"] == 1
    assert payload["nodes"][1]["id"] == "protein:P11111"
    assert payload["nodes"][1]["contradictions"] == ["cx-1"]
    assert payload["edges"][0]["row_ref"] == "protein_matrix.tsv:4"
    assert payload["edges"][0]["confidence"] == 0.93
    assert payload["edges"][0]["reason"] == "strong peptide quantifies protein P11111"
