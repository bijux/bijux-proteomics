# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    detect_evidence_graph_contradictions,
    render_evidence_graph_contradictions_tsv,
)

from .test_evidence_graph_contradiction_surface import build_contradiction_fixture_graph


def test_evidence_graph_contradictions_render_contradictions_tsv() -> None:
    report = detect_evidence_graph_contradictions(build_contradiction_fixture_graph())

    rendered = render_evidence_graph_contradictions_tsv(report)
    lines = rendered.strip().splitlines()

    assert "contradiction_id\tkind\tseverity\tclaim_node_id" in rendered
    assert "protein_unchanged_with_changed_peptides" in rendered
    assert "ptm_change_explained_by_protein" in rendered
    assert "pathway_enrichment_with_weak_proteins" in rendered
    assert len(lines) == 4
    assert lines[1].startswith(
        "contradiction:pathway:treatment_vs_control:R-HSA-199420:weak-support\t"
    )
    assert '"contradiction_count": 3' in report.to_stable_json()
