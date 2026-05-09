# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.constraints import (
    ConstraintCategory,
    ScientificConstraint,
    assess_constraint_risk,
    build_protein_native_constraints,
)
from bijux_proteomics.domain.context import (
    ProgramContext,
    ProgramDeliveryContext,
    ProgramPortfolioContext,
)
from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.lifecycle import (
    ProgramLifecycle,
    advance_stage,
    allowed_next_stages,
)
from bijux_proteomics.domain.operating_model import (
    DecisionOwnerRole,
    OperatingModel,
    ReviewCadence,
)
from bijux_proteomics.domain.program_spec import ProgramSpec, ProgramStage
from bijux_proteomics.domain.reviews import ReviewGate
from bijux_proteomics.domain.targets import (
    ComplexMembership,
    MechanismLiability,
    OutcomeSeverity,
    ProteinDomain,
    ProteinMotif,
    ProteinTarget,
    PtmHotspot,
    TargetAnnotation,
    TargetOutcome,
    TractabilityFlag,
    summarize_tractability,
    target_summary,
)
from bijux_proteomics.domain.errors import InvalidLifecycleTransitionError
from bijux_proteomics.domain.liabilities import LiabilityCategory, ProgramLiability
from bijux_proteomics.sequences import ProteinSequence, sequence_length


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
                category=ConstraintCategory.DEVELOPABILITY,
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
                intended_output="decision brief",
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
    assert program.liabilities[0].severity == 3
    assert program.operating_model.review_cadence is ReviewCadence.WEEKLY
    assert program.operating_model.decision_owner_roles == [
        DecisionOwnerRole.SCIENTIST,
        DecisionOwnerRole.PROGRAM_LEAD,
    ]
    assert program.constraints[0].category is ConstraintCategory.DEVELOPABILITY
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


def test_target_summary_includes_target_class_and_isoform_context() -> None:
    target = ProteinTarget(
        target_id="target-3",
        name="Target 3",
        sequence=ProteinSequence(target_id="target-3", residues="ACDEFGHIKLMNPQRSTVWY"),
        organism="human",
        mechanism="modulate pathway signaling",
        target_class="enzyme",
        subcellular_localization="cytosol",
        isoforms=["iso-1", "iso-2"],
        pathway_roles=["MAPK signaling"],
        domains=[ProteinDomain(domain_id="d1", name="Kinase", start=1, end=100)],
        motifs=[ProteinMotif(motif_id="m1", name="H-loop", pattern="HRD", start=50)],
        ptm_hotspots=[PtmHotspot(site="S42", modification="phosphorylation")],
        complex_memberships=[
            ComplexMembership(complex_id="cx-1", role="catalytic core")
        ],
        tractability_flags=[
            TractabilityFlag(code="tractable", summary="known binders")
        ],
        mechanism_liabilities=[
            MechanismLiability(
                liability_id="liab-1",
                summary="allosteric risk",
                severity=OutcomeSeverity.HIGH,
            )
        ],
    )

    summary = target_summary(target)

    assert summary["target_class"] == "enzyme"
    assert summary["isoform_count"] == 2
    assert summary["domain_count"] == 1
    assert summary["tractability_flag_count"] == 1


def test_assess_constraint_risk_flags_blockers_without_mitigation() -> None:
    report = assess_constraint_risk(
        [
            ScientificConstraint(
                constraint_id="constraint-1",
                category=ConstraintCategory.DEVELOPABILITY,
                statement="avoid aggregation",
                rationale="aggregation risk",
                blocker=True,
            )
        ]
    )

    assert report.blocker_count == 1
    assert report.high_risk_constraints == ["constraint-1"]


def test_summarize_tractability_flags_high_severity() -> None:
    target = ProteinTarget(
        target_id="target-tract",
        name="Target",
        sequence=ProteinSequence(
            target_id="target-tract", residues="ACDEFGHIKLMNPQRSTVWY"
        ),
        organism="human",
        mechanism="stabilize fold",
        tractability_flags=[
            TractabilityFlag(
                code="risk-1", summary="hard to express", severity=OutcomeSeverity.HIGH
            )
        ],
        mechanism_liabilities=[
            MechanismLiability(
                liability_id="liab-1",
                summary="allosteric risk",
                severity=OutcomeSeverity.HIGH,
            )
        ],
    )

    summary = summarize_tractability(target)

    assert summary["high_severity_flags"] == ["risk-1"]
    assert summary["high_severity_liabilities"] == ["liab-1"]


def test_program_liability_supports_blocker_fields() -> None:
    liability = ProgramLiability(
        liability_id="liability-2",
        category=LiabilityCategory.SAFETY,
        summary="immunogenicity risk",
        impact="could block clinical progression",
        mitigation="run immunogenicity panel",
        severity=5,
        blocker=True,
        owner_role="safety",
        evidence_ids=["ev-1"],
    )

    assert liability.blocker is True
    assert liability.owner_role == "safety"


def test_program_spec_supports_modality_unknowns_and_failure_modes() -> None:
    program = ProgramSpec(
        program_id="prog-rich-context",
        name="rich context",
        objective="capture scientific unknowns and failure modes",
        mechanism_hypothesis="stabilize target conformation",
        intervention_goal="stability rescue",
        modality_context="engineered binder",
        key_unknowns=["does cell context preserve selectivity"],
        critical_failure_modes=["aggregation under expression stress"],
        target=ProteinTarget(
            target_id="target-rich-context",
            name="Target Rich Context",
            sequence=ProteinSequence(
                target_id="target-rich-context", residues="ACDEFGHIKLMNPQRSTVWY"
            ),
            organism="human",
            mechanism="stabilize target conformation",
        ),
    )

    assert program.modality_context == "engineered binder"
    assert program.key_unknowns == ["does cell context preserve selectivity"]
    assert program.critical_failure_modes == ["aggregation under expression stress"]


def test_build_protein_native_constraints_returns_blocking_scientific_set() -> None:
    constraints = build_protein_native_constraints(
        target_id="target-native",
        catalytic_region="active-site-loop",
        interface_region="partner-interface",
    )

    categories = {constraint.category for constraint in constraints}
    assert ConstraintCategory.STABILITY_FLOOR in categories
    assert ConstraintCategory.AGGREGATION_CEILING in categories
    assert ConstraintCategory.CATALYTIC_RESIDUE in categories
    assert ConstraintCategory.DOMAIN_MUTABILITY in categories
    assert all(constraint.blocker for constraint in constraints)


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
