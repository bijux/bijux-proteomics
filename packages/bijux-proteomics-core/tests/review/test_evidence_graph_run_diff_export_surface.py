# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    compare_evidence_graph_runs,
    render_evidence_graph_run_diff_tsv,
)

from .test_evidence_graph_run_diff_surface import build_run_diff_fixture_graphs


def test_evidence_graph_run_diff_renders_scientific_change_tsv() -> None:
    left_graph, right_graph = build_run_diff_fixture_graphs()

    report = compare_evidence_graph_runs(left_graph, right_graph)
    rendered = render_evidence_graph_run_diff_tsv(report)
    lines = rendered.strip().splitlines()

    assert (
        "category\tchange_kind\tentity_ref\tleft_claim_state\tright_claim_state"
        in rendered
    )
    assert "\tremoved\tP20002\t" in rendered
    assert "\tadded\tP30003\t" in rendered
    assert "\tchanged\tPEPDIFF\tupregulated\tunchanged\t" in rendered
    assert len(lines) == 8
