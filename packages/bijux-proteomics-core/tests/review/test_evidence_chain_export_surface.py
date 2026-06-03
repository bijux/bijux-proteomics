# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    reconstruct_pathway_evidence_chain,
    reconstruct_protein_evidence_chain,
    reconstruct_ptm_site_evidence_chain,
    render_evidence_chain_tsv,
)

from .test_evidence_chain_reconstruction_surface import (
    build_reconstruction_fixture_graph,
)


def test_evidence_chain_reports_render_tsv_and_json() -> None:
    graph = build_reconstruction_fixture_graph()

    protein = reconstruct_protein_evidence_chain(
        graph,
        protein_id="P11111",
        statistical_result_id="protein:treatment_vs_control:P11111",
    )
    ptm = reconstruct_ptm_site_evidence_chain(
        graph,
        ptm_site_id="P11111:S3:Phospho",
        statistical_result_id="ptm:treatment_vs_control:P11111:S3:Phospho",
    )
    pathway = reconstruct_pathway_evidence_chain(
        graph,
        pathway_id="R-HSA-199420",
        statistical_result_id="pathway:treatment_vs_control:R-HSA-199420",
    )

    rendered = render_evidence_chain_tsv(protein)
    assert "claim_kind\tclaim_id\tstatistical_result_id\trelation" in rendered
    assert "protein_stats.tsv" in rendered
    assert '"source_row_count"' in protein.to_stable_json()
    assert '"ptm_site"' in ptm.to_stable_json()
    assert '"pathway"' in pathway.to_stable_json()
