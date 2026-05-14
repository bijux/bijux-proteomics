# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable route contracts for quantification reports."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class QuantReportRouteRequest(JsonModel):
    """Stable API request for quantification report routes."""

    model_config = ConfigDict(extra="forbid")

    report_kind: Literal["normalization", "differential-abundance", "missingness", "qc"]
    study_id: str = Field(..., min_length=1)


class QuantReportRouteResponse(JsonModel):
    """Stable API response for quantification report routes."""

    model_config = ConfigDict(extra="forbid")

    report_kind: str = Field(..., min_length=1)
    study_id: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    report_pointer: str = Field(..., min_length=1)


def route_quant_report_api(
    payload: QuantReportRouteRequest,
) -> QuantReportRouteResponse:
    """Expose normalization, DA, missingness, and QC routes through one schema."""

    return QuantReportRouteResponse(
        report_kind=payload.report_kind,
        study_id=payload.study_id,
        schema_ref="api.quant-report.route.v1",
        report_pointer=f"quant/{payload.report_kind}/{payload.study_id}",
    )


__all__ = [
    "QuantReportRouteRequest",
    "QuantReportRouteResponse",
    "route_quant_report_api",
]
