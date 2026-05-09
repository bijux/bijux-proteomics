# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable route contracts for decision brief operations."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class DecisionBriefRouteRequest(JsonModel):
    """Stable API request for decision brief routes."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["create", "lookup", "diff", "export"]
    packet_id: str = Field(..., min_length=1)
    baseline_packet_id: str | None = None
    export_format: Literal["json", "tsv", "html"] = "json"


class DecisionBriefRouteIssue(JsonModel):
    """Issue emitted from decision brief route handling."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class DecisionBriefRouteResponse(JsonModel):
    """Stable API response for decision brief route handling."""

    model_config = ConfigDict(extra="forbid")

    operation: str = Field(..., min_length=1)
    packet_id: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    result_pointer: str = Field(..., min_length=1)
    issues: tuple[DecisionBriefRouteIssue, ...] = Field(default_factory=tuple)


def route_decision_brief_api(
    payload: DecisionBriefRouteRequest,
) -> DecisionBriefRouteResponse:
    """Route decision brief operations through one stable API surface."""

    issues: list[DecisionBriefRouteIssue] = []
    result_pointer = f"decision-brief/{payload.operation}/{payload.packet_id}"
    if payload.operation == "diff" and not payload.baseline_packet_id:
        issues.append(
            DecisionBriefRouteIssue(
                code="missing_baseline_packet_id",
                message="diff operation requires baseline_packet_id",
            )
        )
    if payload.operation == "export":
        result_pointer = f"decision-brief/export/{payload.packet_id}.{payload.export_format}"
    return DecisionBriefRouteResponse(
        operation=payload.operation,
        packet_id=payload.packet_id,
        schema_ref="api.decision-brief.route.v1",
        result_pointer=result_pointer,
        issues=tuple(issues),
    )


__all__ = [
    "DecisionBriefRouteIssue",
    "DecisionBriefRouteRequest",
    "DecisionBriefRouteResponse",
    "route_decision_brief_api",
]
