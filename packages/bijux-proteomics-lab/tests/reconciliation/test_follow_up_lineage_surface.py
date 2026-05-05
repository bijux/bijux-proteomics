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


def _reconciliation_fixture(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "fixtures"
                / "reconciliation"
                / name
            ).read_text(encoding="utf-8")
        ),
    )

def test_degraded_provenance_fixture_keeps_follow_up_non_executable_until_lineage_is_restored() -> (
    None
):
    fixture = _reconciliation_fixture("degraded_provenance_follow_up.json")
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

    assert practicality_report.practical_candidate_ids == ["cand-provenance-gap"]
    assert practicality_report.impractical_candidate_ids == []
    assert readiness_report.ready_for_execution is False
    assert readiness_report.provenance_gap_ids == ["targeted-bundle-provenance-gap"]
    assert any(
        "incomplete" in note or "lineage" in note
        for note in readiness_report.risk_notes
    )
