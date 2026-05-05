# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.program_spec import create_program_spec
from bijux_proteomics.domain.reviews import ReviewGate
from bijux_proteomics_knowledge.memory.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
)
from bijux_proteomics_lab.planning import ExperimentBatch, ExperimentPlan
from bijux_proteomics_lab.planning.scheduling import InstrumentAvailability, LabCapacity
from bijux_proteomics_lab.readiness import (
    OperationalReadinessReport,
    ReagentAvailability,
    ReviewBacklogSnapshot,
    StaffingAvailability,
    build_operational_readiness_report,
    summarize_workflow_readiness,
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
        step.step_id: step.blockers for step in summary.step_statuses if not step.ready
    }
    assert "prog-1-assay-execution" in blocked
    assert "blocking_assay:assay-primary-binding" in blocked["prog-1-assay-execution"]
    assert "prog-1-decision-review" in blocked


def test_build_operational_readiness_report_combines_budget_staffing_and_backlog() -> (
    None
):
    plan = ExperimentPlan(
        program_id="prog-readiness",
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="binding batch",
                assay_ids=["a1"],
                priority=1,
                sample_requirements=["biophysical"],
            ),
            ExperimentBatch(
                batch_id="b2",
                objective="cellular batch",
                assay_ids=["a2"],
                priority=2,
                sample_requirements=["cellular"],
            ),
        ],
    )

    report = build_operational_readiness_report(
        plan,
        capacity=LabCapacity(
            cycle_id="cycle-readiness",
            max_batches=1,
            max_assays_per_batch=2,
        ),
        instrument_availability=[
            InstrumentAvailability(
                instrument_id="orbitrap",
                available_days=1.0,
                supported_sample_kinds=["biophysical"],
            )
        ],
        reagent_inventory=[
            ReagentAvailability(
                material_id="protein",
                available_units=0.5,
                minimum_units=1.0,
                unit="mg",
                lead_time_days=10.0,
            )
        ],
        staffing=[
            StaffingAvailability(
                role_name="mass-spec-operator",
                available_operators=0,
                required_operators=1,
                available_operator_days=0.0,
            )
        ],
        backlog=ReviewBacklogSnapshot(
            queued_review_entries=4,
            blocking_gate_ids=("gate-a",),
            deferred_batch_ids=("b3",),
            oldest_entry_days=9.0,
        ),
        budget_limit=1.5,
    )

    assert isinstance(report, OperationalReadinessReport)
    assert report.ready_for_execution is False
    assert report.deferred_batch_ids[:2] == ["b2", "b3"]
    assert report.blocking_material_ids == ["protein"]
    assert report.understaffed_roles == ["mass-spec-operator"]
    assert report.long_lead_material_ids == ["protein"]
    assert report.backlog_pressure_score > 0.5
    assert any(
        "blocking review gates remain queued" in note for note in report.risk_notes
    )
