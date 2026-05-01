# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.product_api_iteration19 import (
    QuantReportRouteRequest,
    route_quant_report_api,
)


def test_route_quant_report_api_exposes_missingness_and_qc_surfaces() -> None:
    response = route_quant_report_api(
        QuantReportRouteRequest(
            report_kind="missingness",
            study_id="study-777",
        )
    )

    assert response.schema_ref == "api.quant-report.route.v1"
    assert response.report_pointer == "quant/missingness/study-777"
