# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    is_registered_reason_code,
    reason_code_categories,
    reason_code_registry,
)
from bijux_proteomics.identification.protein_evidence import (
    ProteinEvidenceDowngradeReason,
)
from bijux_proteomics.review.evidence_graph_downgrades import (
    EvidenceGraphDowngradeReason,
)


def test_reason_code_registry_exposes_workflow_qc_and_downgrade_categories() -> None:
    registry = {entry.code: entry.categories for entry in reason_code_registry()}

    assert ReasonCodeCategory.RESULT_WARNING in registry["rejected_evidence_present"]
    assert ReasonCodeCategory.QC_REASON in registry["identification_rate"]
    assert ReasonCodeCategory.WORKFLOW_BLOCK in registry["multi_batch_shift"]
    assert ReasonCodeCategory.CLAIM_DOWNGRADE in registry["shared_peptide_only"]

    assert is_registered_reason_code(
        "failed_qc_blocks_biological_promotion",
        ReasonCodeCategory.WORKFLOW_BLOCK,
    )
    assert not is_registered_reason_code(
        "failed_qc_blocks_biological_promotion",
        ReasonCodeCategory.RESULT_WARNING,
    )


def test_reason_code_registry_covers_claim_downgrade_enums() -> None:
    registered = {
        entry.code
        for entry in reason_code_registry()
        if ReasonCodeCategory.CLAIM_DOWNGRADE in entry.categories
    }

    assert {
        reason.value for reason in ProteinEvidenceDowngradeReason
    } <= registered
    assert {
        reason.value for reason in EvidenceGraphDowngradeReason
    } <= registered
    assert reason_code_categories("shared_peptide_only")
