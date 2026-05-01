# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Product API and CLI surfaces for iteration 19."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ExampleWorkflowPackageEntry(JsonModel):
    """One package and the example workflows it exposes."""

    model_config = ConfigDict(extra="forbid")

    package_name: str = Field(..., min_length=1)
    workflow_ids: tuple[str, ...] = Field(default_factory=tuple)


class PackageLevelExampleWorkflowCatalog(JsonModel):
    """Catalog verifying package-level example workflow coverage."""

    model_config = ConfigDict(extra="forbid")

    required_packages: tuple[str, ...] = Field(default_factory=tuple)
    entries: tuple[ExampleWorkflowPackageEntry, ...] = Field(default_factory=tuple)
    missing_packages: tuple[str, ...] = Field(default_factory=tuple)
    compliant: bool


def build_package_level_example_workflow_catalog(
    entries: tuple[ExampleWorkflowPackageEntry, ...],
    *,
    required_packages: tuple[str, ...] = (
        "bijux-proteomics-core",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
    ),
) -> PackageLevelExampleWorkflowCatalog:
    """Verify every required package exposes at least one example workflow."""

    normalized = tuple(sorted(entries, key=lambda entry: entry.package_name))
    available = {
        entry.package_name
        for entry in normalized
        if entry.workflow_ids
    }
    missing = tuple(package for package in required_packages if package not in available)
    return PackageLevelExampleWorkflowCatalog(
        required_packages=required_packages,
        entries=normalized,
        missing_packages=missing,
        compliant=not missing,
    )


class CliWorkflowCommandEntry(JsonModel):
    """One CLI command mapped to a workflow-oriented surface.""" 

    model_config = ConfigDict(extra="forbid")

    command: str = Field(..., min_length=1)
    workflow_id: str = Field(..., min_length=1)
    scientific_question: str = Field(..., min_length=1)


class UnifiedCliWorkflowStoryReport(JsonModel):
    """Coverage report for workflow-oriented CLI command narratives."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CliWorkflowCommandEntry, ...] = Field(default_factory=tuple)
    internal_surface_commands: tuple[str, ...] = Field(default_factory=tuple)
    coherent_story: bool


def build_unified_cli_workflow_story(
    entries: tuple[CliWorkflowCommandEntry, ...],
) -> UnifiedCliWorkflowStoryReport:
    """Validate CLI commands describe workflow stories rather than package internals."""

    normalized = tuple(sorted(entries, key=lambda entry: entry.command))
    internal_surface_commands = tuple(
        entry.command
        for entry in normalized
        if any(token in entry.command for token in ("internal", "module", "package"))
    )
    return UnifiedCliWorkflowStoryReport(
        entries=normalized,
        internal_surface_commands=internal_surface_commands,
        coherent_story=not internal_surface_commands and bool(normalized),
    )


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
        result_pointer = (
            f"review/export/{payload.packet_id}.{payload.export_format}"
        )
    return ReviewPacketRouteResponse(
        operation=payload.operation,
        packet_id=payload.packet_id,
        schema_ref="api.review-packet.route.v1",
        result_pointer=result_pointer,
        issues=tuple(issues),
    )


class LabHandoffRouteRequest(JsonModel):
    """Stable API request for assay request, handoff export, and lifecycle status."""

    model_config = ConfigDict(extra="forbid")

    operation: Literal["request", "export", "status"]
    assay_request_id: str = Field(..., min_length=1)
    lifecycle_state: Literal["planned", "queued", "running", "completed", "rejected"] = (
        "planned"
    )
    export_format: Literal["json", "csv", "tsv"] = "json"


class LabHandoffRouteResponse(JsonModel):
    """Stable API response for lab handoff routes."""

    model_config = ConfigDict(extra="forbid")

    operation: str = Field(..., min_length=1)
    assay_request_id: str = Field(..., min_length=1)
    lifecycle_state: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    handoff_pointer: str = Field(..., min_length=1)


def route_lab_handoff_api(
    payload: LabHandoffRouteRequest,
) -> LabHandoffRouteResponse:
    """Route lab handoff operations through a stable product API surface."""

    pointer = f"lab/{payload.operation}/{payload.assay_request_id}"
    if payload.operation == "export":
        pointer = f"lab/export/{payload.assay_request_id}.{payload.export_format}"
    return LabHandoffRouteResponse(
        operation=payload.operation,
        assay_request_id=payload.assay_request_id,
        lifecycle_state=payload.lifecycle_state,
        schema_ref="api.lab-handoff.route.v1",
        handoff_pointer=pointer,
    )
