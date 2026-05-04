# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.interfaces.api import (
    LabHandoffRouteRequest,
    route_lab_handoff_api,
)


def test_route_lab_handoff_api_exports_lifecycle_surface() -> None:
    response = route_lab_handoff_api(
        LabHandoffRouteRequest(
            operation="export",
            assay_request_id="assay-22",
            lifecycle_state="queued",
            export_format="tsv",
        )
    )

    assert response.schema_ref == "api.lab-handoff.route.v1"
    assert response.handoff_pointer == "lab/export/assay-22.tsv"
    assert response.lifecycle_state == "queued"
