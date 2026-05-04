# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.interfaces.api import (
    AdapterConformanceRouteRequest,
    route_adapter_conformance_api,
)


def test_route_adapter_conformance_api_tracks_lost_and_unsupported_fields() -> None:
    response = route_adapter_conformance_api(
        AdapterConformanceRouteRequest(
            adapter_id="sage-v1",
            mapped_fields=("peptide", "score", "score"),
            lost_fields=("raw_scan_id",),
            unsupported_fields=("engine_specific_blob",),
            raw_evidence_policy="retain-raw-evidence-pointer",
        )
    )

    assert response.schema_ref == "api.adapter-conformance.route.v1"
    assert response.mapped_fields == ("peptide", "score")
    assert response.lost_fields == ("raw_scan_id",)
    assert response.raw_evidence_policy == "retain-raw-evidence-pointer"
