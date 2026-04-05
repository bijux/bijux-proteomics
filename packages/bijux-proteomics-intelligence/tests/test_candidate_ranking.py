# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import ReviewGate, ScientificConstraint, SuccessCriterion, create_program_spec
from bijux_proteomics.programs import AssayRequirement, MeasurementDirection
from bijux_proteomics_intelligence import (
    CandidateAssessment,
    LiabilityFlag,
    OptimizationAxis,
    build_design_brief,
    prioritize_candidates,
)
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
)


def test_build_design_brief_surfaces_blockers_and_evidence_gaps() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="kinase rescue",
        objective="recover activity without raising aggregation risk",
        target_id="kinase-x",
        target_name="Kinase X",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize active-state packing",
    )
    program.target.blocked_outcomes.append("aggregation hotspot around the active-site loop")
    program.constraints.append(
        ScientificConstraint(
            constraint_id="surface-hydrophobics",
            category="developability",
            statement="avoid broad hydrophobic surface patches",
            rationale="reduce aggregation risk",
            threshold=0.3,
        )
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="pre-synthesis",
            name="Pre-synthesis review",
            required_roles=["scientist", "safety"],
            decision_inputs=["evidence-bundle", "candidate-ranking"],
        )
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
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.8,
        )
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="kinase-x",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Disease mechanism paper",
                source="PMID:1",
                claim="Kinase X signaling is disease-relevant.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    brief = build_design_brief(program, bundle)

    assert brief.optimization_axes == [OptimizationAxis.AFFINITY]
    assert brief.blocking_assays == ["primary-binding"]
    assert brief.review_gate_ids == ["pre-synthesis"]
    assert "structure" in brief.evidence_gaps
    assert [flag.code for flag in brief.liabilities] == [
        "surface-hydrophobics",
        "blocked-outcome-1",
    ]


def test_prioritize_candidates_rewards_support_and_penalizes_liabilities() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="binder rescue",
        objective="recover binding while preserving folding",
        target_id="target-1",
        target_name="Target 1",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a binding-competent state",
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.75,
        )
    )

    ranking = prioritize_candidates(
        program,
        [
            CandidateAssessment(
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.82},
                evidence_support=0.8,
            ),
            CandidateAssessment(
                candidate_id="candidate-b",
                sequence="ACDEFGHIKLMNPQRSTVWYA",
                metric_scores={"binding_score": 0.88},
                evidence_support=0.4,
                liabilities=[
                    LiabilityFlag(
                        code="aggregation-risk",
                        summary="Predicted aggregation hotspot",
                        severity=4,
                        source="model",
                    )
                ],
            ),
            CandidateAssessment(
                candidate_id="candidate-c",
                sequence="ACDEFGHIKLMNPQRSTV",
                metric_scores={},
                evidence_support=0.2,
            ),
        ],
    )

    assert [item.candidate_id for item in ranking.ranked_candidates] == [
        "candidate-a",
        "candidate-b",
    ]
    assert ranking.rejected_candidates == ["candidate-c"]
