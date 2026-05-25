# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.workflow.pipelines.advanced_diann import AdvancedDiannWorkflowReport
from bijux_proteomics.workflow.pipelines.advanced_fragpipe import (
    AdvancedFragpipeWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_maxquant import (
    AdvancedMaxquantWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_ptm import AdvancedPtmWorkflowReport
from bijux_proteomics.workflow.pipelines.advanced_targeted import (
    TargetedValidationWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_tmt import AdvancedTmtWorkflowReport
from bijux_proteomics.workflow.pipelines.discovery_to_assay import DiscoveryToAssayReport
from bijux_proteomics.workflow.pipelines.multi_study import MultiStudyComparisonReport
from bijux_proteomics.workflow.pipelines.orchestrator import (
    WorkflowResult as OrchestratorWorkflowResult,
)
from bijux_proteomics.workflow.result_types import BiologyResult, WorkflowResult


def test_major_workflow_reports_subclass_standardized_result_types() -> None:
    biology_reports = (
        AdvancedDiannWorkflowReport,
        AdvancedFragpipeWorkflowReport,
        AdvancedMaxquantWorkflowReport,
        AdvancedPtmWorkflowReport,
        TargetedValidationWorkflowReport,
        AdvancedTmtWorkflowReport,
        MultiStudyComparisonReport,
    )

    for report_type in biology_reports:
        assert issubclass(report_type, BiologyResult)

    for report_type in (
        DiscoveryToAssayReport,
        OrchestratorWorkflowResult,
    ):
        assert issubclass(report_type, WorkflowResult)


def test_major_workflow_reports_expose_standardized_result_fields() -> None:
    for report_type in (
        AdvancedDiannWorkflowReport,
        AdvancedFragpipeWorkflowReport,
        AdvancedMaxquantWorkflowReport,
        AdvancedPtmWorkflowReport,
        TargetedValidationWorkflowReport,
        AdvancedTmtWorkflowReport,
        DiscoveryToAssayReport,
        MultiStudyComparisonReport,
        OrchestratorWorkflowResult,
    ):
        fields = report_type.model_fields
        assert "manifest" in fields
        assert "artifacts" in fields
        assert "warnings" in fields
        assert "rejected_evidence" in fields
