# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.program_spec import EvidenceNeed, create_program_spec
from bijux_proteomics.domain.reviews import ReviewGate
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
)
from bijux_proteomics_lab.outcomes import (
    AssayOutcome,
    AssayResultState,
    ExperimentOutcome,
    RerunPolicy,
)
from bijux_proteomics_lab.planning import (
    AdvisoryAssayPlan,
    AssayDependency,
    AssayFamily,
    AssayIntent,
    AssayObservation,
    AssayPlanKind,
    CandidatePrioritySignal,
    ConflictAssayPolicy,
    ExecutableAssayPlan,
    ExperimentBatch,
    ExperimentPlan,
    FamilyCapacity,
    InstrumentAvailability,
    LabCapacity,
    MaterialInventory,
    MaterialRequirement,
    OrthogonalPolicy,
    PlanningPolicy,
    ProgressDecision,
    align_lab_priority_queue,
    assay_family_priority,
    assess_dependency_integrity,
    assess_gate_coverage_gaps,
    assess_material_constraints,
    build_advisory_assay_plan,
    build_executable_assay_plan,
    build_execution_capacity_advisory,
    build_follow_up_practicality_report,
    build_lab_cycle_brief,
    build_lab_execution_request,
    build_lab_review_packet_bundle,
    build_review_packet,
    build_review_risk_profile,
    build_workflow_batch_outline,
    compare_schedule_scenarios,
    dependency_critical_path,
    dependency_order,
    derive_lab_execution_directive,
    detect_dependency_cycle,
    estimate_assay_execution_burden,
    map_assay_contradiction_pressure,
    plan_conflict_resolution_assays,
    plan_experiment_batches,
    plan_hypothesis_falsification_assays,
    plan_material_reservations,
    plan_uncertainty_reduction_assays,
    prioritize_batches_by_material_feasibility,
    prioritize_next_assays,
    recommend_next_best_experiment,
    recommend_next_cycle,
    recommend_next_cycle_from_outcome,
    recommend_orthogonal_confirmation,
    report_execution_plan_uncertainty,
    schedule_experiment_plan,
    schedule_with_family_capacity,
    score_assay_gate_impact,
    score_assay_information_gain,
    summarize_assay_portfolio_balance,
    summarize_schedule_pressure,
    validate_experiment_plan,
)
from bijux_proteomics_lab.readiness import (
    ControlReadinessSignal,
    EvidenceReadinessSignal,
    OperationalReadinessReport,
    ProvenanceReadinessSignal,
    ReagentAvailability,
    ReviewBacklogSnapshot,
    StaffingAvailability,
    build_operational_readiness_report,
)


def _planning_fixture(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "fixtures"
                / "planning"
                / name
            ).read_text(encoding="utf-8")
        ),
    )

def test_build_execution_capacity_advisory_combines_budget_and_instrument_pressure() -> (
    None
):
    plan = ExperimentPlan(
        program_id="prog-capacity",
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

    advisory = build_execution_capacity_advisory(
        plan,
        LabCapacity(cycle_id="cycle-1", max_batches=1, max_assays_per_batch=2),
        [
            InstrumentAvailability(
                instrument_id="orbitrap",
                available_days=1.0,
                supported_sample_kinds=["biophysical"],
            )
        ],
        budget_limit=1.5,
    )

    assert advisory.feasible_batch_ids == ["b1"]
    assert advisory.deferred_batch_ids == ["b2"]
    assert advisory.deferred_reasons == {
        "b2": "cycle batch capacity exhausted",
    }
    assert advisory.estimated_total_cost == 1.15
    assert advisory.budget_remaining == 0.35
    assert advisory.practicality_score == 0.42

def test_schedule_experiment_plan_respects_batch_and_assay_capacity() -> None:
    plan = ExperimentPlan(
        program_id="prog-1",
        batches=[
            ExperimentBatch(
                batch_id="batch-1",
                objective="blocking",
                assay_ids=["a1", "a2", "a3"],
                priority=1,
            ),
            ExperimentBatch(
                batch_id="batch-2",
                objective="supporting",
                assay_ids=["b1"],
                priority=2,
            ),
        ],
    )

    scheduled = schedule_experiment_plan(
        plan,
        LabCapacity(cycle_id="cycle-1", max_batches=1, max_assays_per_batch=2),
        dependencies=[AssayDependency(assay_id="a2", requires_assay_id="a1")],
    )

    assert scheduled.scheduled_batches[0].assay_ids == ["a1", "a2"]
    assert scheduled.scheduled_batches[0].deferred_assay_ids == ["a3"]
    assert scheduled.unscheduled_batches == ["batch-2"]

def test_summarize_schedule_pressure_reports_utilization_and_deferred_assays() -> None:
    plan = ExperimentPlan(
        program_id="prog-pressure",
        batches=[
            ExperimentBatch(
                batch_id="batch-1",
                objective="blocking",
                assay_ids=["a1", "a2", "a3"],
                priority=1,
            )
        ],
    )
    capacity = LabCapacity(
        cycle_id="cycle-pressure", max_batches=1, max_assays_per_batch=2
    )
    scheduled = schedule_experiment_plan(plan, capacity)
    report = summarize_schedule_pressure(scheduled, capacity)

    assert report.cycle_id == "cycle-pressure"
    assert report.assay_slot_utilization == 1.0
    assert report.deferred_assay_count == 1

def test_prioritize_batches_by_material_feasibility_promotes_ready_batches() -> None:
    plan = ExperimentPlan(
        program_id="prog-material",
        batches=[
            ExperimentBatch(
                batch_id="batch-ready",
                objective="ready",
                assay_ids=["a1"],
                priority=1,
                sample_requirements=["protein"],
            ),
            ExperimentBatch(
                batch_id="batch-blocked",
                objective="blocked",
                assay_ids=["a2"],
                priority=2,
                sample_requirements=["cells"],
            ),
        ],
    )
    ranked = prioritize_batches_by_material_feasibility(
        plan,
        requirements=[
            MaterialRequirement(
                material_id="protein-stock",
                sample_kind="protein",
                minimum_units=1,
                unit="mg",
            ),
            MaterialRequirement(
                material_id="cell-stock",
                sample_kind="cells",
                minimum_units=10,
                unit="ml",
            ),
        ],
        inventory=[
            MaterialInventory(material_id="protein-stock", available_units=5),
            MaterialInventory(material_id="cell-stock", available_units=2),
        ],
    )

    assert ranked[0].batch_id == "batch-ready"
    assert ranked[1].material_ready is False

def test_compare_schedule_scenarios_recommends_lowest_deferred_assay_load() -> None:
    plan = ExperimentPlan(
        program_id="prog-sim",
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="batch",
                assay_ids=["a1", "a2"],
                priority=1,
            )
        ],
    )
    comparison = compare_schedule_scenarios(
        plan,
        scenarios=[
            LabCapacity(cycle_id="tight", max_batches=1, max_assays_per_batch=1),
            LabCapacity(cycle_id="relaxed", max_batches=1, max_assays_per_batch=3),
        ],
    )

    assert comparison.recommended_scenario_id == "relaxed"

def test_schedule_with_family_capacity_respects_family_limits() -> None:
    plan = ExperimentPlan(
        program_id="prog-4",
        batches=[
            ExperimentBatch(
                batch_id="batch-1",
                objective="family capacity",
                assay_ids=["a1", "a2"],
                sample_requirements=["biophysical", "expression"],
                assay_sample_kinds={"a1": "biophysical", "a2": "expression"},
                priority=1,
            )
        ],
    )

    scheduled = schedule_with_family_capacity(
        plan,
        LabCapacity(cycle_id="cycle-1", max_batches=1, max_assays_per_batch=2),
        family_capacities=[
            FamilyCapacity(family=AssayFamily.BIOPHYSICAL, max_assays=1),
            FamilyCapacity(family=AssayFamily.EXPRESSION, max_assays=0),
        ],
    )

    assert scheduled.scheduled_batches[0].assay_ids == ["a1"]
    assert "a2" in scheduled.scheduled_batches[0].deferred_assay_ids

def test_schedule_with_family_capacity_uses_per_assay_mapping() -> None:
    plan = ExperimentPlan(
        program_id="prog-5",
        batches=[
            ExperimentBatch(
                batch_id="batch-1",
                objective="family mapped scheduling",
                assay_ids=["a1", "a2", "a3"],
                sample_requirements=["biophysical"],
                assay_sample_kinds={
                    "a1": "biophysical",
                    "a2": "biophysical",
                    "a3": "expression",
                },
                priority=1,
            )
        ],
    )

    scheduled = schedule_with_family_capacity(
        plan,
        LabCapacity(cycle_id="cycle-2", max_batches=1, max_assays_per_batch=3),
        family_capacities=[
            FamilyCapacity(family=AssayFamily.BIOPHYSICAL, max_assays=1),
            FamilyCapacity(family=AssayFamily.EXPRESSION, max_assays=1),
        ],
    )

    assert scheduled.scheduled_batches[0].assay_ids == ["a1", "a3"]
    assert scheduled.scheduled_batches[0].deferred_assay_ids == ["a2"]
