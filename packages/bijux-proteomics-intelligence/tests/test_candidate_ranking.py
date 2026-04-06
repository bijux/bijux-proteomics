# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics import ReviewGate, ScientificConstraint, SuccessCriterion, create_program_spec
from bijux_proteomics.programs import AssayRequirement, MeasurementDirection
from bijux_proteomics_intelligence import (
    CandidateAssessment,
    CandidateExplainabilitySummary,
    CandidateRejection,
    CandidateScoreBreakdown,
    MetricDefinition,
    MetricDirection,
    build_risk_profile,
    LiabilityFlag,
    OptimizationAxis,
    RankingFactor,
    PortfolioSelectionPolicy,
    RejectionReasonCode,
    RankingPolicy,
    ScientificMetricClass,
    build_design_brief,
    prioritize_candidates,
    select_portfolio_shortlist,
    summarize_candidate_explainability,
    candidate_score_breakdown,
    classify_metric_name,
    build_rejection_action_plan,
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
    assert brief.ranking_priorities == ["affinity"]
    assert brief.blocking_assays == ["primary-binding"]
    assert brief.review_gate_ids == ["pre-synthesis"]
    assert brief.downstream_lab_assumptions == ["confirm target engagement"]
    assert "structure" in brief.evidence_gaps
    assert brief.risk_appetite == "balanced"
    assert "avoid broad hydrophobic surface patches" in brief.prohibited_failure_modes
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
                manufacturability_score=0.8,
                uncertainty=0.1,
                evidence_support=0.8,
            ),
            CandidateAssessment(
                candidate_id="candidate-b",
                sequence="ACDEFGHIKLMNPQRSTVWYA",
                metric_scores={"binding_score": 0.88},
                manufacturability_score=0.4,
                uncertainty=0.2,
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
                manufacturability_score=0.2,
                uncertainty=0.7,
                evidence_support=0.2,
            ),
        ],
    )

    assert [item.candidate_id for item in ranking.ranked_candidates] == [
        "candidate-a",
        "candidate-b",
    ]
    assert ranking.rejected_candidates == ["candidate-c"]
    assert ranking.rejections[0].candidate_id == "candidate-c"
    assert ranking.rejections[0].reason_codes == [
        RejectionReasonCode.LOW_METRIC_FRACTION
    ]
    assert ranking.ranked_candidates[0].explainability["confidence"] == 0.9
    assert ranking.ranked_candidates[0].explainability["factor_scores"] == {
        RankingFactor.CRITERIA.value: 0.7289,
        RankingFactor.EVIDENCE.value: 0.8,
        RankingFactor.MANUFACTURABILITY.value: 0.8,
        RankingFactor.LIABILITY.value: 1.0,
        RankingFactor.UNCERTAINTY.value: 0.9,
    }


def test_prioritize_candidates_applies_profile_hard_filters() -> None:
    program = create_program_spec(
        program_id="prog-2",
        name="filter profile",
        objective="screen out weakly supported and hard-to-make candidates",
        target_id="target-2",
        target_name="Target 2",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize productive packing",
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.8,
        )
    )

    ranking = prioritize_candidates(
        program,
        [
            CandidateAssessment(
                candidate_id="candidate-hard-filter",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.85},
                manufacturability_score=0.2,
                uncertainty=0.1,
                evidence_support=0.7,
            ),
            CandidateAssessment(
                candidate_id="candidate-keep",
                sequence="ACDEFGHIKLMNPQRSTVWA",
                metric_scores={"binding_score": 0.82},
                manufacturability_score=0.7,
                uncertainty=0.1,
                evidence_support=0.8,
            ),
        ],
        policy=RankingPolicy(
            policy_id="manufacturability-gate",
            require_manufacturability_floor=True,
            manufacturability_floor=0.5,
        ),
    )

    assert [item.candidate_id for item in ranking.ranked_candidates] == ["candidate-keep"]
    assert ranking.rejected_candidates == ["candidate-hard-filter"]


def test_select_portfolio_shortlist_preserves_liability_diversity() -> None:
    candidates = [
        CandidateAssessment(
            candidate_id="candidate-a",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            metric_scores={"binding_score": 0.85},
            manufacturability_score=0.8,
            uncertainty=0.1,
            evidence_support=0.85,
            liabilities=[
                LiabilityFlag(
                    code="aggregation-risk",
                    summary="Aggregation hotspot",
                    severity=4,
                    source="model",
                )
            ],
        ),
        CandidateAssessment(
            candidate_id="candidate-b",
            sequence="ACDEFGHIKLMNPQRSTVWA",
            metric_scores={"binding_score": 0.83},
            manufacturability_score=0.78,
            uncertainty=0.12,
            evidence_support=0.82,
            liabilities=[
                LiabilityFlag(
                    code="aggregation-risk",
                    summary="Aggregation hotspot",
                    severity=3,
                    source="model",
                )
            ],
        ),
        CandidateAssessment(
            candidate_id="candidate-c",
            sequence="ACDEFGHIKLMNPQRSTVWF",
            metric_scores={"binding_score": 0.81},
            manufacturability_score=0.76,
            uncertainty=0.15,
            evidence_support=0.8,
            liabilities=[
                LiabilityFlag(
                    code="immunogenicity-risk",
                    summary="Potential immunogenicity signal",
                    severity=2,
                    source="model",
                )
            ],
        ),
    ]

    selection = select_portfolio_shortlist(
        candidates,
        [build_risk_profile(candidate) for candidate in candidates],
        policy=PortfolioSelectionPolicy(
            policy_id="diverse-shortlist",
            selection_size=2,
            max_candidates_per_liability_code=1,
        ),
    )

    assert selection.selected_candidate_ids == ["candidate-a", "candidate-c"]
    assert selection.deferred_candidate_ids == ["candidate-b"]


def test_summarize_candidate_explainability_carries_evidence_gaps() -> None:
    program = create_program_spec(
        program_id="prog-3",
        name="explainability brief",
        objective="surface evidence gaps alongside ranking drivers",
        target_id="target-3",
        target_name="Target 3",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a productive fold",
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.8,
        )
    )
    brief = build_design_brief(program)
    ranking = prioritize_candidates(
        program,
        [
            CandidateAssessment(
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.86},
                manufacturability_score=0.82,
                uncertainty=0.1,
                evidence_support=0.78,
                liabilities=[
                    LiabilityFlag(
                        code="aggregation-risk",
                        summary="Predicted aggregation hotspot",
                        severity=3,
                        source="model",
                    )
                ],
            )
        ],
    )

    summaries = summarize_candidate_explainability(ranking, brief)

    assert summaries == [
        CandidateExplainabilitySummary(
            candidate_id="candidate-a",
            strengths=[
                "criteria_factor=0.72",
                "evidence_factor=0.78",
                "manufacturability_factor=0.82",
                "assessment confidence remains high enough for active consideration",
            ],
            open_risks=["Predicted aggregation hotspot"],
            evidence_gaps=["literature", "structure", "assay"],
        )
    ]


def test_candidate_score_breakdown_reports_weighted_contributions() -> None:
    program = create_program_spec(
        program_id="prog-4",
        name="score decomposition",
        objective="explain weighted score composition",
        target_id="target-4",
        target_name="Target 4",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize active conformation",
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.8,
        )
    )
    policy = RankingPolicy(policy_id="score-breakdown")
    ranking = prioritize_candidates(
        program,
        [
            CandidateAssessment(
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.85},
                manufacturability_score=0.75,
                uncertainty=0.2,
                evidence_support=0.8,
            )
        ],
        policy=policy,
    )

    breakdown = candidate_score_breakdown(ranking.ranked_candidates[0], policy)

    assert isinstance(breakdown, CandidateScoreBreakdown)
    assert breakdown.base_score > 0
    assert breakdown.final_score <= breakdown.base_score


def test_classify_metric_name_uses_typed_metric_classes() -> None:
    assert classify_metric_name("binding_score") is ScientificMetricClass.AFFINITY
    assert classify_metric_name("delta_tm") is ScientificMetricClass.STABILITY
    assert classify_metric_name("tox_signal") is ScientificMetricClass.SAFETY


def test_candidate_rejection_supports_reopen_action_guidance() -> None:
    rejection = ranking = prioritize_candidates(
        create_program_spec(
            program_id="prog-reject",
            name="rejection details",
            objective="surface actionable rejection context",
            target_id="target-reject",
            target_name="Target Reject",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            organism="human",
            mechanism="rejection guidance",
        ),
        [
            CandidateAssessment(
                candidate_id="candidate-x",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={},
                manufacturability_score=0.1,
                uncertainty=0.5,
                evidence_support=0.1,
            )
        ],
    ).rejections[0]

    enriched = rejection.model_copy(
        update={
            "recommended_experiments": ["run orthogonal binding assay"],
            "reopen_conditions": ["evidence_support >= 0.4"],
        }
    )

    assert enriched.recommended_experiments == ["run orthogonal binding assay"]
    assert enriched.reopen_conditions == ["evidence_support >= 0.4"]


def test_build_rejection_action_plan_maps_reason_codes_to_experiments() -> None:
    plan = build_rejection_action_plan(
        CandidateRejection(
            candidate_id="candidate-plan",
            reasons=["insufficient evidence support"],
            reason_codes=[RejectionReasonCode.LOW_EVIDENCE_SUPPORT],
        )
    )

    assert "collect orthogonal evidence across at least two modalities" in plan.experiments


def test_metric_definition_encodes_typed_metric_contract() -> None:
    definition = MetricDefinition(
        metric_key="binding_kd",
        metric_class=ScientificMetricClass.AFFINITY,
        unit="nM",
        direction=MetricDirection.LOWER_IS_BETTER,
        normalization="log10",
    )

    assert definition.metric_key == "binding_kd"
    assert definition.direction is MetricDirection.LOWER_IS_BETTER
