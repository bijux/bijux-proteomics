# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    build_evidence_graph_final_result_table,
    render_evidence_graph_final_results_tsv,
)

from .test_evidence_graph_contradiction_surface import build_contradiction_fixture_graph
from .test_evidence_graph_downgrade_surface import build_downgrade_fixture_graph


def test_evidence_graph_final_result_table_renders_evidence_tiers_and_downgrade_reasons() -> (
    None
):
    report = build_evidence_graph_final_result_table(build_downgrade_fixture_graph())

    rendered = render_evidence_graph_final_results_tsv(report)
    lines = rendered.strip().splitlines()

    assert (
        "claim_node_id\tclaim_node_ref\tsubject_node_id\tsubject_node_ref" in rendered
    )
    assert "evidence_tier" in lines[0]
    assert "downgrade_reasons" in lines[0]
    assert "\tambiguous\tshared_peptide_only\t" in rendered
    assert "\tmoderate\tpoor_run_qc\t" in rendered
    assert "\thigh_confidence\t\t" in rendered
    assert len(lines) == 8


def test_evidence_graph_final_result_table_renders_contradiction_downgrade_reasons() -> (
    None
):
    report = build_evidence_graph_final_result_table(
        build_contradiction_fixture_graph()
    )

    rendered = render_evidence_graph_final_results_tsv(report)

    assert "\tlow\tweak\tsevere_contradiction\t" in rendered
    assert "\tmoderate\tweak\tcontradiction_caution\t" in rendered
