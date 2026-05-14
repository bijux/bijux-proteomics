# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.api.routes.decision_briefs import (
    DecisionBriefRouteRequest,
    route_decision_brief_api,
)


def test_route_decision_brief_api_requires_baseline_for_diff() -> None:
    response = route_decision_brief_api(
        DecisionBriefRouteRequest(
            operation="diff",
            packet_id="rp-new",
        )
    )

    assert response.schema_ref == "api.decision-brief.route.v1"
    assert response.issues[0].code == "missing_baseline_packet_id"
