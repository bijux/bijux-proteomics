# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.assays import AssayRequirement
from bijux_proteomics.context import (
    ProgramContext,
    ProgramDeliveryContext,
    ProgramPortfolioContext,
)
from bijux_proteomics.constraints import ScientificConstraint
from bijux_proteomics.criteria import MeasurementDirection, SuccessCriterion
import pytest

from bijux_proteomics.exceptions import InvalidLifecycleTransitionError
from bijux_proteomics.lifecycle import ProgramLifecycle, advance_stage, allowed_next_stages
from bijux_proteomics.liabilities import LiabilityCategory, ProgramLiability
from bijux_proteomics.operating_model import DecisionOwnerRole, OperatingModel, ReviewCadence
from bijux_proteomics.program_spec import ProgramSpec, ProgramStage
from bijux_proteomics.reviews import ReviewGate
from bijux_proteomics.sequences import ProteinSequence, sequence_length
from bijux_proteomics.targets import (
    OutcomeSeverity,
    ProteinTarget,
    TargetAnnotation,
    TargetOutcome,
    target_summary,
)


def test_domain_modules_define_program_components() -> None:
    target = ProteinTarget(
        target_id="target-1",
        name="Target 1",
        sequence=ProteinSequence(
            target_id="target-1",
            residues="ACDEFGHIKLMNPQRSTVWY",
        ),
        organism="human",
        mechanism="stabilize productive packing",
    )
    program = ProgramSpec(
        program_id="prog-1",
        name="binder rescue",
        objective="recover binding while preserving folding",
        stage=ProgramStage.DESIGN,
        target=target,
        constraints=[
            ScientificConstraint(
                constraint_id="surface-hydrophobics",
                category="developability",
                statement="avoid broad hydrophobic surface patches",
                rationale="reduce aggregation risk",
            )
        ],
        liabilities=[
            ProgramLiability(
                liability_id="liability-1",
                category=LiabilityCategory.DEVELOPABILITY,
                summary="Aggregation hotspot",
                impact="Could limit expression yield.",
                mitigation="Screen stabilizing substitutions.",
            )
        ],
        success_criteria=[
            SuccessCriterion(
                criterion_id="binding",
                metric="binding_score",
                direction=MeasurementDirection.MAXIMIZE,
                threshold=0.8,
            )
        ],
        assay_panel=[
            AssayRequirement(
                assay_id="primary-binding",
                purpose="confirm target engagement",
                readout="binding_score",
                sample_kind="biophysical",
                blocking=True,
            )
        ],
        review_gates=[
            ReviewGate(
                gate_id="pre-synthesis",
                name="Pre-synthesis review",
                required_roles=["scientist"],
                decision_inputs=["evidence_bundle"],
            )
        ],
        context=ProgramContext(
            portfolio=ProgramPortfolioContext(
                therapeutic_area="oncology",
                disease_area="solid tumors",
                modality="protein degrader",
            ),
            delivery=ProgramDeliveryContext(
                sponsor="translational biology",
                decision_horizon="quarterly",
                intended_output="review packet",
            ),
            tags=["solid-tumor", "discovery"],
        ),
        operating_model=OperatingModel(
            review_cadence=ReviewCadence.WEEKLY,
            decision_owner_roles=[
                DecisionOwnerRole.SCIENTIST,
                DecisionOwnerRole.PROGRAM_LEAD,
            ],
        ),
    )

    assert program.stage is ProgramStage.DESIGN
    assert program.assay_panel[0].blocking is True
    assert program.operating_model.review_cadence is ReviewCadence.WEEKLY
    assert program.operating_model.decision_owner_roles == [
        DecisionOwnerRole.SCIENTIST,
        DecisionOwnerRole.PROGRAM_LEAD,
    ]
    assert program.context.portfolio.therapeutic_area == "oncology"
    assert sequence_length(program.target.sequence) == 20


def test_target_summary_includes_structured_annotations_and_risk_codes() -> None:
    target = ProteinTarget(
        target_id="target-2",
        name="Target 2",
        sequence=ProteinSequence(target_id="target-2", residues="ACDEFGHIKLMNPQRSTVWY"),
        organism="human",
        mechanism="stabilize fold",
        blocked_outcome_records=[
            TargetOutcome(
                code="agg-hotspot",
                summary="Aggregation hotspot near loop",
                severity=OutcomeSeverity.HIGH,
            )
        ],
        annotations=[
            TargetAnnotation(
                annotation_id="annot-1",
                statement="conserved active site geometry",
                evidence_ids=["ev-1", "ev-2"],
            )
        ],
    )

    summary = target_summary(target)

    assert summary["high_risk_block_codes"] == ["agg-hotspot"]
    assert summary["annotation_evidence_ids"] == ["ev-1", "ev-2"]


def test_program_lifecycle_advances_between_stages() -> None:
    lifecycle = ProgramLifecycle(
        program_id="prog-1",
        current_stage=ProgramStage.SCOPING,
    )

    advanced = advance_stage(
        lifecycle,
        ProgramStage.DESIGN,
        reason="design kickoff approved",
        actor="scientist",
    )

    assert advanced.current_stage is ProgramStage.DESIGN
    assert advanced.visited_stages == [ProgramStage.SCOPING, ProgramStage.DESIGN]
    assert advanced.transitions[0].reason == "design kickoff approved"
    assert advanced.transitions[0].actor == "scientist"


def test_program_lifecycle_rejects_invalid_transition() -> None:
    lifecycle = ProgramLifecycle(
        program_id="prog-1",
        current_stage=ProgramStage.SCOPING,
    )

    with pytest.raises(InvalidLifecycleTransitionError):
        advance_stage(lifecycle, ProgramStage.LAB_READY)


def test_allowed_next_stages_exposes_transition_map() -> None:
    assert allowed_next_stages(ProgramStage.REVIEW) == {
        ProgramStage.DESIGN,
        ProgramStage.LAB_READY,
    }
