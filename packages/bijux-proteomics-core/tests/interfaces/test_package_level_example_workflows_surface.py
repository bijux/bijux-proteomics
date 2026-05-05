# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_runtime.api.product_routes import (
    ExampleWorkflowPackageEntry,
    build_package_level_example_workflow_catalog,
)


def test_build_package_level_example_workflow_catalog_flags_missing_packages() -> None:
    report = build_package_level_example_workflow_catalog(
        (
            ExampleWorkflowPackageEntry(
                package_name="bijux-proteomics-core",
                workflow_ids=("workflow.dda-basic",),
            ),
            ExampleWorkflowPackageEntry(
                package_name="bijux-proteomics-intelligence",
                workflow_ids=("workflow.review-board",),
            ),
            ExampleWorkflowPackageEntry(
                package_name="bijux-proteomics-knowledge",
                workflow_ids=(),
            ),
            ExampleWorkflowPackageEntry(
                package_name="bijux-proteomics-lab",
                workflow_ids=("workflow.lab-handoff",),
            ),
        )
    )

    assert report.compliant is False
    assert report.missing_packages == ("bijux-proteomics-knowledge",)
