# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable route contracts for PTM reports."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PtmReportRouteRequest(JsonModel):
    """Stable API request for PTM report routes."""

    model_config = ConfigDict(extra="forbid")

    report_kind: Literal["site", "localization", "motif", "occupancy", "caveat"]
    ptm_study_id: str = Field(..., min_length=1)


class PtmReportRouteResponse(JsonModel):
    """Stable API response for PTM report routes."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = Field(..., min_length=1)
    ptm_study_id: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    report_pointer: str = Field(..., min_length=1)


def route_ptm_report_api(
    payload: PtmReportRouteRequest,
) -> PtmReportRouteResponse:
    """Expose PTM site/localization/motif/occupancy/caveat reports via one schema."""

    return PtmReportRouteResponse(
        report_kind=payload.report_kind,
        ptm_study_id=payload.ptm_study_id,
        schema_ref="api.ptm-report.route.v1",
        report_pointer=f"ptm/{payload.report_kind}/{payload.ptm_study_id}",
    )


__all__ = [
    "PtmReportRouteRequest",
    "PtmReportRouteResponse",
    "route_ptm_report_api",
]
