# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Root workflow facade assembly for compatibility exports and subpackage access."""

from __future__ import annotations

from bijux_proteomics.workflow.facade_benchmark_catalog import (
    BENCHMARK_FACADE_OWNERS,
    WORKFLOW_ROOT_DEMO_OWNERS,
)
from bijux_proteomics.workflow.facade_card_catalog import WORKFLOW_ROOT_CARD_OWNERS
from bijux_proteomics.workflow.facade_catalog import WorkflowFacadeOwner
from bijux_proteomics.workflow.facade_export_catalog import WORKFLOW_ROOT_EXPORT_OWNERS
from bijux_proteomics.workflow.facade_pipeline_catalog import WORKFLOW_ROOT_PIPELINE_OWNERS
from bijux_proteomics.workflow.facade_report_catalog import WORKFLOW_ROOT_REPORT_OWNERS
from bijux_proteomics.workflow.facade_study_catalog import WORKFLOW_ROOT_STUDY_OWNERS


WORKFLOW_ROOT_SUBMODULES = {
    "benchmarks": "bijux_proteomics.workflow.benchmarks",
    "cards": "bijux_proteomics.workflow.cards",
    "cross_study_protein_harmonization": "bijux_proteomics.workflow.cross_study_protein_harmonization",
    "demo": "bijux_proteomics.workflow.demo",
    "exports": "bijux_proteomics.workflow.exports",
    "pipelines": "bijux_proteomics.workflow.pipelines",
    "public_benchmark_descriptors": "bijux_proteomics.workflow.public_benchmark_descriptors",
    "reports": "bijux_proteomics.workflow.reports",
    "studies": "bijux_proteomics.workflow.studies",
}

WORKFLOW_ROOT_SHARED_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.result_types",
        rationale="shared workflow result record ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.blueprint",
        rationale="workflow blueprint ownership",
    ),
)

WORKFLOW_ROOT_OWNERS = (
    *WORKFLOW_ROOT_SHARED_OWNERS,
    *WORKFLOW_ROOT_REPORT_OWNERS,
    *WORKFLOW_ROOT_EXPORT_OWNERS,
    *WORKFLOW_ROOT_PIPELINE_OWNERS,
    *WORKFLOW_ROOT_STUDY_OWNERS,
    *WORKFLOW_ROOT_CARD_OWNERS,
    *BENCHMARK_FACADE_OWNERS,
    *WORKFLOW_ROOT_DEMO_OWNERS,
)


__all__ = [
    "WORKFLOW_ROOT_OWNERS",
    "WORKFLOW_ROOT_SHARED_OWNERS",
    "WORKFLOW_ROOT_SUBMODULES",
    "WorkflowFacadeOwner",
]
