# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import create_program_spec
from bijux_proteomics.programs import AssayRequirement, ReviewGate
from bijux_proteomics_knowledge import EvidenceBundle, EvidenceKind, EvidenceRecord, EvidenceStrength
from bijux_proteomics_lab import (
    AssayObservation,
    ProgressDecision,
    build_review_packet,
    plan_experiment_batches,
    recommend_next_cycle,
)


def test_plan_experiment_batches_prioritizes_blocking_assays() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="binder recovery",
        objective="recover binding and reduce aggregation",
        target_id="target-1",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a binding competent state",
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="synthesis-review",
            name="Synthesis review",
            required_roles=["scientist"],
            decision_inputs=["evidence_bundle"],
            blocking=True,
        )
    )
    program.assay_panel.extend(
        [
            AssayRequirement(
                assay_id="primary-binding",
                purpose="confirm target engagement",
                readout="binding_score",
                sample_kind="biophysical",
                blocking=True,
            ),
            AssayRequirement(
                assay_id="expression-screen",
                purpose="check manufacturability",
                readout="yield_mg_per_l",
                sample_kind="expression",
                blocking=False,
            ),
        ]
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Target is tractable.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    plan = plan_experiment_batches(program, bundle)

    assert [batch.batch_id for batch in plan.batches] == [
        "prog-1-gate-batch",
        "prog-1-optimization-batch",
    ]
    assert plan.review_queue == ["synthesis-review"]
    assert "structure" in plan.evidence_gaps


def test_build_review_packet_marks_failed_assays_as_blockers() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="binder recovery",
        objective="recover binding and reduce aggregation",
        target_id="target-1",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a binding competent state",
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Target is tractable.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay",
                source="lab",
                claim="A first candidate retains activity.",
                confidence=0.8,
                strength=EvidenceStrength.DECISIVE,
            ),
            EvidenceRecord(
                evidence_id="structure-1",
                kind=EvidenceKind.STRUCTURE,
                title="Structure",
                source="model",
                claim="Fold remains plausible.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    packet = build_review_packet(
        program,
        bundle,
        [
            AssayObservation(
                assay_id="primary-binding",
                metric="binding_score",
                value=0.42,
                passed=False,
            )
        ],
    )

    assert packet.ready_for_synthesis is False
    assert "failed assays: primary-binding" in packet.blocking_findings


def test_recommend_next_cycle_requests_redesign_after_failed_assay() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="binder recovery",
        objective="recover binding and reduce aggregation",
        target_id="target-1",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a binding competent state",
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="primary-binding",
            purpose="confirm target engagement",
            readout="binding_score",
            sample_kind="biophysical",
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
                title="Paper",
                source="PMID:1",
                claim="Target is tractable.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay",
                source="lab",
                claim="A first candidate retains activity.",
                confidence=0.8,
                strength=EvidenceStrength.DECISIVE,
            ),
            EvidenceRecord(
                evidence_id="structure-1",
                kind=EvidenceKind.STRUCTURE,
                title="Structure",
                source="model",
                claim="Fold remains plausible.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    plan = recommend_next_cycle(
        program,
        bundle,
        [
            AssayObservation(
                assay_id="primary-binding",
                metric="binding_score",
                value=0.42,
                passed=False,
            )
        ],
    )

    assert plan.decision is ProgressDecision.REDESIGN
    assert plan.assay_backlog == ["primary-binding"]
