# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Product API and CLI surfaces for iteration 19."""

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
