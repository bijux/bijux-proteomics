# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bijux_proteomics.identification.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
)
from bijux_proteomics.quantification.contracts.study_qc import (
    SampleReliabilityQcEntry,
    SampleReliabilityQcStatus,
)
from bijux_proteomics.review.flagship_kernel import FlagshipScientificKernelReport
from bijux_proteomics.review.scientific_conflicts import ScientificConflictReport
from bijux_proteomics.review.scientific_story import ScientificConsistencyReport
from bijux_proteomics.review.evidence_graph_confidence import (
    EvidenceGraphConfidenceTier,
)
from bijux_proteomics.review.evidence_graph_downgrades import FinalClaimEvidenceTier
from bijux_proteomics.study.qc import (
    QcStatus,
    QcStatusReasonEntry,
    QcStatusReasonSource,
)
from bijux_proteomics.study.qc_benchmarks import QcPromotionBlockObservation
from bijux_proteomics.workflow.pipelines.advanced_diann import (
    AdvancedDiannProteinDecisionEntry,
)
from bijux_proteomics.workflow.result_manifest import (
    ResultManifestWarningEntry,
    ResultManifestWarningSeverity,
)
from bijux_proteomics.workflow.result_types import (
    RejectedEvidenceEntry,
    ResultWarningEntry,
    ResultWarningSeverity,
)


def test_reason_code_registry_rejects_unregistered_surface_codes() -> None:
    with pytest.raises(ValidationError, match="not registered"):
        ResultWarningEntry(
            warning_id="wf:1",
            warning_code="not_registered",
            source_surface="workflow",
            severity=ResultWarningSeverity.WARNING,
            message="bad",
        )

    with pytest.raises(ValidationError, match="not registered"):
        ResultManifestWarningEntry(
            warning_id="manifest:1",
            severity=ResultManifestWarningSeverity.WARNING,
            warning_code="not_registered",
            source_surface="manifest",
            message="bad",
        )

    with pytest.raises(ValidationError, match="not registered"):
        RejectedEvidenceEntry(
            evidence_id="e1",
            source_surface="workflow",
            reason_code="not_registered",
            message="bad",
        )

    with pytest.raises(ValidationError, match="not registered"):
        RejectedEvidenceTableEntry(
            source_file="input.tsv",
            row_number=1,
            entity_type="psm",
            entity_id="row-1",
            reason_code="not_registered",
            detail="bad",
        )

    with pytest.raises(ValidationError, match="not registered"):
        QcStatusReasonEntry(
            code="not_registered",
            status=QcStatus.FAIL,
            source=QcStatusReasonSource.LAB,
            message="bad",
        )

    with pytest.raises(ValidationError, match="not registered"):
        QcPromotionBlockObservation(
            run_id="run-1",
            failed_qc=True,
            attempted_decision_promotion=True,
            promotion_prevented=True,
            blocking_reason="not_registered",
        )


def test_reason_code_registry_rejects_unregistered_block_and_downgrade_codes() -> None:
    with pytest.raises(ValidationError, match="not registered"):
        SampleReliabilityQcEntry(
            sample_id="sample-1",
            qc_status=SampleReliabilityQcStatus.FAIL,
            blocked=True,
            status_reason_codes=("not_registered",),
        )

    with pytest.raises(ValidationError, match="not registered"):
        AdvancedDiannProteinDecisionEntry(
            protein_group_id="pg-1",
            representative_protein_ref="P11111",
            claim_node_ref="protein:claim",
            evidence_tier=FinalClaimEvidenceTier.MODERATE,
            confidence_tier=EvidenceGraphConfidenceTier.MODERATE,
            downgrade_reasons=("not_registered",),
        )

    with pytest.raises(ValidationError, match="not registered"):
        FlagshipScientificKernelReport(
            workflow_id="wf-1",
            flagship_family_id="flagship",
            artifact_path="artifacts/kernel.json",
            consistency=ScientificConsistencyReport(
                workflow_id="wf-1",
                composed_story=False,
                issues=(),
                note="note",
            ),
            conflicts=ScientificConflictReport(
                workflow_id="wf-1",
                findings=(),
            ),
            kernel_ready=False,
            blocked_reasons=("not_registered",),
            note="note",
        )
