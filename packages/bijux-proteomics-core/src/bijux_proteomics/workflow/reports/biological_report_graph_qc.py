# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned lab-QC attachment helpers for biological result graph assembly."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
)

if TYPE_CHECKING:
    from bijux_proteomics_lab.handoffs.qc_feedback import (
        LabRunQcFeedbackEntry,
        LabRunQcFeedbackReport,
    )


def _attach_lab_run_qc_feedback(
    builder: ProteomicsEvidenceGraphBuilder,
    *,
    run_nodes_by_id: dict[str, ProteomicsEvidenceNode],
    run_sample_ids_by_id: dict[str, str],
    feedback_report: LabRunQcFeedbackReport,
) -> None:
    for entry in feedback_report.entries:
        run = run_nodes_by_id.get(entry.run_id)
        if run is None:
            raise ValueError(
                f"lab run qc feedback references an unknown workflow run: {entry.run_id}"
            )
        expected_sample_id = run_sample_ids_by_id[entry.run_id]
        if entry.sample_id != expected_sample_id:
            raise ValueError(
                "lab run qc feedback sample does not match the workflow design for "
                f"run {entry.run_id}: expected {expected_sample_id}, got {entry.sample_id}"
            )
        decision = builder.add_qc_decision(
            f"lab:{entry.run_id}",
            label=f"lab qc decision {entry.run_id}",
            claim_state=_qc_claim_state(entry),
            trust_class=_qc_trust_class(entry),
            context_refs=(
                ProteomicsEvidenceContextRef(
                    entity_type=ProteomicsEvidenceNodeKind.RUN,
                    entity_ref=entry.run_id,
                ),
                ProteomicsEvidenceContextRef(
                    entity_type=ProteomicsEvidenceNodeKind.SAMPLE,
                    entity_ref=entry.sample_id,
                ),
            ),
        )
        builder.add_run_governed_by_qc_decision(
            run.node_id,
            decision.node_id,
            source_row_ref=entry.source_refs[0]
            if entry.source_refs
            else f"lab_qc:{entry.run_id}",
            confidence=max(0.05, min(0.99, entry.composite_quality)),
            reason=entry.note,
        )


def _qc_claim_state(entry: LabRunQcFeedbackEntry) -> str:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackStatus

    if entry.status is LabRunQcFeedbackStatus.FAILED:
        return "failed"
    if entry.status is LabRunQcFeedbackStatus.CAUTION:
        return "caution"
    return "passed"


def _qc_trust_class(entry: LabRunQcFeedbackEntry) -> str:
    from bijux_proteomics_lab.handoffs.qc_feedback import LabRunQcFeedbackStatus

    if entry.status is LabRunQcFeedbackStatus.FAILED:
        return "low"
    if entry.status is LabRunQcFeedbackStatus.CAUTION:
        return "medium"
    return "high"
