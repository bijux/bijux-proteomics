# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.workflow.pipelines.advanced_diann import (
    AdvancedDiannWorkflowReport,
)
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
from bijux_proteomics.workflow.pipelines.discovery_to_assay import (
    DiscoveryToAssayReport,
)
from bijux_proteomics.workflow.pipelines.multi_study import MultiStudyComparisonReport
from bijux_proteomics.workflow.pipelines.orchestrator import (
    WorkflowResult as OrchestratorWorkflowResult,
)
from bijux_proteomics.workflow.result_types import (
    BiologyResult,
    WorkflowResult,
    build_rejected_evidence_entry,
    render_result_rejected_evidence_tsv,
)


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
    advanced_family_reports = (
        AdvancedDiannWorkflowReport,
        AdvancedFragpipeWorkflowReport,
        AdvancedMaxquantWorkflowReport,
        AdvancedPtmWorkflowReport,
        TargetedValidationWorkflowReport,
        AdvancedTmtWorkflowReport,
    )
    for report_type in advanced_family_reports:
        fields = report_type.model_fields
        assert "manifest" in fields
        assert "family_protocol" in fields
        assert "artifacts" in fields
        assert "warnings" in fields
        assert "rejected_evidence" in fields

    for report_type in (
        DiscoveryToAssayReport,
        MultiStudyComparisonReport,
        OrchestratorWorkflowResult,
    ):
        fields = report_type.model_fields
        assert "manifest" in fields
        assert "artifacts" in fields
        assert "warnings" in fields
        assert "rejected_evidence" in fields


def test_render_result_rejected_evidence_tsv_uses_stable_shared_columns() -> None:
    rendered = render_result_rejected_evidence_tsv(
        (
            build_rejected_evidence_entry(
                evidence_id="workflow:protein:P12345:missing_signal",
                source_surface="workflow_biology",
                source_file="proteinGroups.txt",
                row_number=17,
                entity_type="protein_group",
                entity_id="P12345",
                reason_code="missing_lfq_signal",
                message="filtered protein group due to missing lfq signal",
                related_artifact="rejected_evidence.tsv",
            ),
        )
    )

    assert rendered.splitlines()[0] == (
        "rejected_evidence_id\tsource_surface\tsource_file\trow_number\t"
        "entity_type\tentity_id\treason_code\tdetail\trelated_artifact"
    )
    assert "workflow_biology\tproteinGroups.txt\t17\tprotein_group\tP12345" in rendered
