# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.product_api_iteration19 import (
    ReviewPacketRouteRequest,
    route_review_packet_api,
)


def test_route_review_packet_api_requires_baseline_for_diff() -> None:
    response = route_review_packet_api(
        ReviewPacketRouteRequest(
            operation="diff",
            packet_id="rp-new",
        )
    )

    assert response.schema_ref == "api.review-packet.route.v1"
    assert response.issues[0].code == "missing_baseline_packet_id"
