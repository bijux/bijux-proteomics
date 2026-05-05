# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from bijux_proteomics_lab.planning import (
    CandidatePrioritySignal,
    ExperimentPlan,
    InstrumentAvailability,
    LabCapacity,
    MaterialInventory,
    MaterialRequirement,
    build_follow_up_practicality_report,
)
from bijux_proteomics_lab.readiness import (
    ControlReadinessSignal,
    EvidenceReadinessSignal,
    ProvenanceReadinessSignal,
    ReagentAvailability,
    ReviewBacklogSnapshot,
    StaffingAvailability,
    build_operational_readiness_report,
)


def _readiness_fixture(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "fixtures"
                / "readiness"
                / name
            ).read_text(encoding="utf-8")
        ),
    )

def test_insufficient_material_fixture_blocks_readiness_and_follow_up_spend() -> None:
    fixture = _readiness_fixture("insufficient_material_follow_up.json")
    plan = ExperimentPlan.model_validate(fixture["plan"])
    capacity = LabCapacity.model_validate(fixture["capacity"])

    practicality_report = build_follow_up_practicality_report(
        plan,
        capacity,
        [
            InstrumentAvailability.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["instrument_availability"])
        ],
        [
            CandidatePrioritySignal.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["candidate_signals"])
        ],
        budget_limit=cast(float, fixture["budget_limit"]),
        estimated_batch_cost=cast(float, fixture["estimated_batch_cost"]),
        material_requirements=[
            MaterialRequirement.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["material_requirements"])
        ],
        inventory=[
            MaterialInventory.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["inventory"])
        ],
    )
    readiness_report = build_operational_readiness_report(
        plan,
        capacity=capacity,
        instrument_availability=[
            InstrumentAvailability.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["instrument_availability"])
        ],
        reagent_inventory=[
            ReagentAvailability.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["reagent_inventory"])
        ],
        staffing=[
            StaffingAvailability.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["staffing"])
        ],
        backlog=ReviewBacklogSnapshot.model_validate(fixture["backlog"]),
        budget_limit=cast(float, fixture["budget_limit"]),
        estimated_batch_cost=cast(float, fixture["estimated_batch_cost"]),
        control_readiness=[
            ControlReadinessSignal.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["control_readiness"])
        ],
        provenance_readiness=[
            ProvenanceReadinessSignal.model_validate(item)
            for item in cast(
                list[dict[str, object]], fixture["provenance_readiness"]
            )
        ],
        evidence_readiness=[
            EvidenceReadinessSignal.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["evidence_readiness"])
        ],
    )

    assert practicality_report.practical_candidate_ids == []
    assert practicality_report.impractical_candidate_ids == ["cand-material"]
    assert practicality_report.material_blocked_candidate_ids == ["cand-material"]
    assert readiness_report.ready_for_execution is False
    assert readiness_report.blocking_material_ids == ["cell-pellet"]
    assert readiness_report.missing_control_ids == ["pooled-reference"]
    assert readiness_report.provenance_gap_ids == ["evidence-bundle-1"]
    assert readiness_report.weak_evidence_ids == ["ev-weak-1"]
    assert any(
        "orthogonal confirmation is still missing" in note
        for note in readiness_report.risk_notes
    )

def test_contradictory_readiness_fixture_keeps_analytical_enthusiasm_non_executable() -> (
    None
):
    fixture = _readiness_fixture("contradictory_readiness_follow_up.json")
    plan = ExperimentPlan.model_validate(fixture["plan"])
    capacity = LabCapacity.model_validate(fixture["capacity"])

    practicality_report = build_follow_up_practicality_report(
        plan,
        capacity,
        [
            InstrumentAvailability.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["instrument_availability"])
        ],
        [
            CandidatePrioritySignal.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["candidate_signals"])
        ],
        budget_limit=cast(float, fixture["budget_limit"]),
        estimated_batch_cost=cast(float, fixture["estimated_batch_cost"]),
        material_requirements=[
            MaterialRequirement.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["material_requirements"])
        ],
        inventory=[
            MaterialInventory.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["inventory"])
        ],
    )
    readiness_report = build_operational_readiness_report(
        plan,
        capacity=capacity,
        instrument_availability=[
            InstrumentAvailability.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["instrument_availability"])
        ],
        reagent_inventory=[
            ReagentAvailability.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["reagent_inventory"])
        ],
        staffing=[
            StaffingAvailability.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["staffing"])
        ],
        backlog=ReviewBacklogSnapshot.model_validate(fixture["backlog"]),
        budget_limit=cast(float, fixture["budget_limit"]),
        estimated_batch_cost=cast(float, fixture["estimated_batch_cost"]),
        control_readiness=[
            ControlReadinessSignal.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["control_readiness"])
        ],
        provenance_readiness=[
            ProvenanceReadinessSignal.model_validate(item)
            for item in cast(
                list[dict[str, object]], fixture["provenance_readiness"]
            )
        ],
        evidence_readiness=[
            EvidenceReadinessSignal.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["evidence_readiness"])
        ],
    )

    assert practicality_report.practical_candidate_ids == ["cand-enthusiastic"]
    assert practicality_report.impractical_candidate_ids == []
    assert readiness_report.ready_for_execution is False
    assert readiness_report.missing_control_ids == ["pooled-reference"]
    assert readiness_report.provenance_gap_ids == ["targeted-bundle-enthusiastic"]
    assert readiness_report.weak_evidence_ids == ["ev-enthusiastic-but-thin"]
    assert any(
        "too thin" in note or "incomplete" in note for note in readiness_report.risk_notes
    )
