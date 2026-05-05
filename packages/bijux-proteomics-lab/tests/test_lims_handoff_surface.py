# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_lab import (
    AlternativeAssayPlanOption,
    HandoffExplanation,
    HandoffSupportLevel,
    HandoffSupportStatement,
    LabExecutionRequest,
    ProtocolControlRequirement,
    ProtocolFailureCaveat,
    SamplePreparationMetadata,
    InstrumentMethodMetadata,
    build_lims_export_bundle,
    build_protocol_attachment,
    compare_alternative_assay_plans,
)


def _protocol_attachment():
    return build_protocol_attachment(
        sample_preparation=SamplePreparationMetadata(
            protocol_id="prep-targeted",
            digestion_protocol="trypsin overnight",
            cleanup_method="solid-phase extraction",
        ),
        instrument_method=InstrumentMethodMetadata(
            method_id="prm-method",
            instrument="orbitrap",
            acquisition_mode="PRM",
            gradient_minutes=60.0,
            ms1_resolution=60000,
            ms2_resolution=30000,
            collision_energy=28.0,
        ),
        protocol_version="2.3",
        required_controls=(
            ProtocolControlRequirement(
                control_id="pooled-reference",
                summary="shared pooled reference",
                failure_if_missing="transition timing cannot be normalized safely",
            ),
        ),
        failure_caveats=(
            ProtocolFailureCaveat(
                caveat_id="carryover-watch",
                triggering_condition="high-abundance precursor precedes low-abundance sample",
                operational_effect="transition ratios may be inflated by carryover",
                mitigation="insert wash and bridge controls",
            ),
        ),
    )


def test_build_lims_export_bundle_reports_field_mapping_and_loss() -> None:
    bundle = build_lims_export_bundle(
        bundle_id="lims-export-1",
        system_name="benchling-lims",
        candidate_id="cand-1",
        execution_request=LabExecutionRequest(
            program_id="prog-1",
            batch_id="batch-1",
            evidence_ids=["ev-1"],
            requested_instruction_ids=["batch-1:assay-a"],
            requested_assay_ids=["assay-a"],
            scientific_rationale=[
                "follow-up is supported by orthogonal assay evidence",
                "review contradiction pressure before irreversible spend",
            ],
            unresolved_risks=["review gate pending: gate-a"],
            ready_for_lab_review=False,
        ),
        protocol_attachment=_protocol_attachment(),
        explanation=HandoffExplanation(
            candidate_id="cand-1",
            supported=(
                HandoffSupportStatement(
                    level=HandoffSupportLevel.SUPPORTED,
                    summary="review packet contains linked evidence",
                    evidence_refs=("ev-1",),
                ),
            ),
            blocked=(
                HandoffSupportStatement(
                    level=HandoffSupportLevel.BLOCKED,
                    summary="review gate pending: gate-a",
                ),
            ),
            summary="handoff remains blocked until weak science or operational blockers are resolved",
        ),
    )

    assert bundle.records[0].protocol_version == "2.3"
    assert bundle.lossy_fields == ("scientific_rationale",)
    assert any(mapping.destination_field == "lims_operator_notes" for mapping in bundle.field_mappings)
    assert bundle.notes[0].startswith("handoff remains blocked")


def test_compare_alternative_assay_plans_balances_evidence_cost_and_turnaround() -> (
    None
):
    comparison = compare_alternative_assay_plans(
        (
            AlternativeAssayPlanOption(
                plan_id="orthogonal-first",
                prioritized_assay_ids=("assay-a", "assay-b"),
                evidence_gain_score=0.88,
                estimated_cost=2.4,
                turnaround_days=6.0,
                supporting_rationale=("maximizes contradiction resolution",),
            ),
            AlternativeAssayPlanOption(
                plan_id="cheap-but-weak",
                prioritized_assay_ids=("assay-c",),
                evidence_gain_score=0.42,
                estimated_cost=0.9,
                turnaround_days=3.0,
                supporting_rationale=("fast but limited evidence gain",),
            ),
        )
    )

    assert comparison.recommended_plan_id == "orthogonal-first"
    assert comparison.scores[0][0] == "orthogonal-first"
