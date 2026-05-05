# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable workflow-story contracts for package examples and CLI narratives."""

from __future__ import annotations

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
    available = {entry.package_name for entry in normalized if entry.workflow_ids}
    missing = tuple(
        package for package in required_packages if package not in available
    )
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


__all__ = [
    "CliWorkflowCommandEntry",
    "ExampleWorkflowPackageEntry",
    "PackageLevelExampleWorkflowCatalog",
    "UnifiedCliWorkflowStoryReport",
    "build_package_level_example_workflow_catalog",
    "build_unified_cli_workflow_story",
]
