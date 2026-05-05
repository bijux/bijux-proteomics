# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.api.routes.evidence_graph import (
    EvidenceGraphQueryRouteRequest,
    route_evidence_graph_query_api,
)


def test_route_evidence_graph_query_api_supports_ptm_queries() -> None:
    response = route_evidence_graph_query_api(
        EvidenceGraphQueryRouteRequest(
            query_kind="ptm",
            query_id="PTM:S123",
            max_results=40,
        )
    )

    assert response.schema_ref == "api.evidence-graph.query.v1"
    assert response.query_pointer == "evidence/ptm/PTM:S123"
    assert response.result_count_hint == 40
