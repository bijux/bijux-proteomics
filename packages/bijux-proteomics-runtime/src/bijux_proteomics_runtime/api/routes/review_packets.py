# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable route contracts for review packet operations."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ReviewPacketRouteRequest(JsonModel):
    """Stable API request for review packet routes."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["create", "lookup", "diff", "export"]
    packet_id: str = Field(..., min_length=1)
    baseline_packet_id: str | None = None
    export_format: Literal["json", "tsv", "html"] = "json"


class ReviewPacketRouteIssue(JsonModel):
    """Issue emitted from review packet route handling."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class ReviewPacketRouteResponse(JsonModel):
    """Stable API response for review packet route handling."""

    model_config = ConfigDict(extra="forbid")

    operation: str = Field(..., min_length=1)
    packet_id: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    result_pointer: str = Field(..., min_length=1)
    issues: tuple[ReviewPacketRouteIssue, ...] = Field(default_factory=tuple)


def route_review_packet_api(
    payload: ReviewPacketRouteRequest,
) -> ReviewPacketRouteResponse:
    """Route review packet operations through one stable API surface."""

    issues: list[ReviewPacketRouteIssue] = []
    result_pointer = f"review/{payload.operation}/{payload.packet_id}"
    if payload.operation == "diff" and not payload.baseline_packet_id:
        issues.append(
            ReviewPacketRouteIssue(
                code="missing_baseline_packet_id",
                message="diff operation requires baseline_packet_id",
            )
        )
    if payload.operation == "export":
        result_pointer = f"review/export/{payload.packet_id}.{payload.export_format}"
    return ReviewPacketRouteResponse(
        operation=payload.operation,
        packet_id=payload.packet_id,
        schema_ref="api.review-packet.route.v1",
        result_pointer=result_pointer,
        issues=tuple(issues),
    )


__all__ = [
    "ReviewPacketRouteIssue",
    "ReviewPacketRouteRequest",
    "ReviewPacketRouteResponse",
    "route_review_packet_api",
]
