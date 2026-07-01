# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Report facade ledgers for workflow reporting surfaces."""

from __future__ import annotations

from bijux_proteomics.workflow.facade_catalog import (
    WorkflowFacadeOwner,
    copy_facade_owners,
)

REPORT_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.reports.biological_reporting",
        rationale="biological result report ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.reports.biological_result_graph",
        rationale="biological result graph ownership",
    ),
)

WORKFLOW_ROOT_REPORT_HELPER_EXPORTS = (
    "write_biological_result_report_bundle",
    "render_biological_report_section_confidence_tsv",
    "render_biological_result_report_summary_tsv",
)

WORKFLOW_ROOT_REPORT_EXPORT_OPERATIONS = ("export_biological_result_report_bundle",)

WORKFLOW_ROOT_REPORT_OWNERS = copy_facade_owners(
    REPORT_FACADE_OWNERS,
    excluded_exports=WORKFLOW_ROOT_REPORT_HELPER_EXPORTS,
)


__all__ = [
    "REPORT_FACADE_OWNERS",
    "WORKFLOW_ROOT_REPORT_EXPORT_OPERATIONS",
    "WORKFLOW_ROOT_REPORT_HELPER_EXPORTS",
    "WORKFLOW_ROOT_REPORT_OWNERS",
    "WorkflowFacadeOwner",
]
