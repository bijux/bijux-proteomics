# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import ReviewGate, create_program_spec
from bijux_proteomics.programs import AssayRequirement
from bijux_proteomics_intelligence import summarize_workflow_readiness
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
)


def test_summarize_workflow_readiness_surfaces_missing_assay_and_reviews() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="workflow readiness",
        objective="show what still blocks proteomics progression",
        target_id="target-1",
        target_name="Target 1",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize target state",
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="assay-primary-binding",
            purpose="confirm target engagement",
            readout="binding_score",
            sample_kind="biophysical",
            blocking=True,
        )
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="review-pre-synthesis",
            name="Pre-synthesis review",
            required_roles=["scientist"],
            decision_inputs=["assay-primary-binding"],
            blocking=True,
        )
    )

    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="literature support",
                source="PMID:1",
                claim="Target is disease-relevant.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="struct-1",
                kind=EvidenceKind.STRUCTURE,
                title="structure support",
                source="model",
                claim="Folded state is plausible.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    summary = summarize_workflow_readiness(program, bundle)

    assert summary.missing_evidence_needs == ["assay"]
    assert summary.blocking_assay_ids == ["assay-primary-binding"]
    assert summary.blocking_review_gate_ids == ["review-pre-synthesis"]
    assert summary.blocked_step_count >= 2
    blocked = {
        step.step_id: step.blockers
        for step in summary.step_statuses
        if not step.ready
    }
    assert "prog-1-assay-execution" in blocked
    assert "blocking_assay:assay-primary-binding" in blocked["prog-1-assay-execution"]
    assert "prog-1-decision-review" in blocked
