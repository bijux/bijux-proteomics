# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    propagate_evidence_graph_confidence,
    render_evidence_graph_confidence_tsv,
)

from .test_evidence_graph_confidence_surface import build_confidence_fixture_graph


def test_evidence_graph_confidence_renders_deterministic_tsv() -> None:
    report = propagate_evidence_graph_confidence(build_confidence_fixture_graph())

    rendered = render_evidence_graph_confidence_tsv(report)
    lines = rendered.strip().splitlines()

    assert (
        "claim_node_id\tclaim_node_ref\tsubject_node_id\tsubject_node_ref" in rendered
    )
    assert "confidence_tier" in lines[0]
    assert len(lines) == 6
    assert "\thigh\t" in rendered
    assert "\tlow\t" in rendered
    assert '"entry_count": 5' in report.to_stable_json()
