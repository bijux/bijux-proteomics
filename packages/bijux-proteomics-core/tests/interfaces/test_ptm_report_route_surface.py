# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.interfaces.api import (
    PtmReportRouteRequest,
    route_ptm_report_api,
)


def test_route_ptm_report_api_exposes_occupancy_surface() -> None:
    response = route_ptm_report_api(
        PtmReportRouteRequest(
            report_kind="occupancy",
            ptm_study_id="ptm-study-11",
        )
    )

    assert response.schema_ref == "api.ptm-report.route.v1"
    assert response.report_pointer == "ptm/occupancy/ptm-study-11"
