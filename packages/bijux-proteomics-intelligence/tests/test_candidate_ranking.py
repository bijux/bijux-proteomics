# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.constraints import (
    ConstraintCategory,
    ScientificConstraint,
)
from bijux_proteomics.domain.criteria import MeasurementDirection, SuccessCriterion
from bijux_proteomics.domain.program_spec import create_program_spec
from bijux_proteomics.domain.reviews import ReviewGate
from bijux_proteomics_intelligence.briefs import (
    CandidateAssessment,
    CandidateRejection,
    CandidateExplainabilitySummary,
    CandidateRanking,
    CandidateRankingProvenanceReport,
    CandidateScoreBreakdown,
    LiabilityFlag,
    LiabilityFocusSummary,
    OptimizationAxis,
    RejectionReasonCode,
    RankedCandidate,
    RankingAssumptionScenario,
    RankingStabilityReport,
    analyze_ranking_stability,
    build_design_brief,
    build_rejection_action_plan,
    build_ranking_diagnostics,
    build_ranking_provenance_report,
    build_ranking_robustness_report,
    candidate_score_breakdown,
    criterion_satisfaction_vector,
    prioritize_candidates,
    summarize_candidate_explainability,
    summarize_liability_focus,
    summarize_metric_coverage,
    summarize_novelty_diversity,
    summarize_rejections,
    summarize_ranking_drift,
    summarize_uncertainty_pressure,
)
from bijux_proteomics_intelligence.candidates import (
    PortfolioSelectionPolicy,
    build_risk_profile,
    select_portfolio_shortlist,
)
from bijux_proteomics_intelligence.policies import (
    MetricDefinition,
    MetricDirection,
    RankingFactor,
    RankingPolicy,
    RankingPolicyLineage,
    ScientificMetricClass,
    audit_metric_catalog,
    classify_metric_name,
    ranking_policy_lineage,
    validate_factor_weights,
    validate_metric_catalog,
)
from bijux_proteomics_knowledge.memory.evidence import (
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
    program.target.blocked_outcomes.append(
        "aggregation hotspot around the active-site loop"
    )
    program.constraints.append(
        ScientificConstraint(
            constraint_id="surface-hydrophobics",
            category=ConstraintCategory.DEVELOPABILITY,
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
    assert ranking.rejections[0].recommended_experiments
    assert ranking.ranked_candidates[0].explainability["confidence"] == 0.9
    assert ranking.ranked_candidates[0].explainability["factor_scores"] == {
        RankingFactor.CRITERIA.value: 0.6322,
        RankingFactor.EVIDENCE.value: 0.7667,
        RankingFactor.MANUFACTURABILITY.value: 0.575,
        RankingFactor.LIABILITY.value: 1.0,
        RankingFactor.UNCERTAINTY.value: 0.95,
    }
    assert ranking.ranked_candidates[0].explainability["multi_objective_profile"] == {
        "scientific_value": 0.6322,
        "assay_feasibility": 0.65,
        "novelty": 0.5,
        "lab_cost_efficiency": 1.0,
        "operational_reliability": 1.0,
    }
    assert ranking.policy_lineage is not None
    assert ranking.policy_lineage.policy_version == 1
    assert ranking.provenance_entries[0].candidate_id == "candidate-a"
    assert ranking.provenance_entries[0].accepted is True


def test_build_ranking_provenance_report_tracks_ranked_and_rejected_candidates() -> (
    None
):
    program = create_program_spec(
        program_id="prog-provenance",
        name="provenance profile",
        objective="prefer supported candidates with measurable binding",
        target_id="target-provenance",
        target_name="Target Provenance",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize productive binding",
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.75,
        )
    )
    policy = RankingPolicy(policy_id="provenance-policy")

    ranking = prioritize_candidates(
        program,
        [
            CandidateAssessment(
                candidate_id="candidate-accepted",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.84},
                manufacturability_score=0.8,
                uncertainty=0.1,
                evidence_support=0.9,
            ),
            CandidateAssessment(
                candidate_id="candidate-rejected",
                sequence="ACDEFGHIKLMNPQRSTV",
                metric_scores={},
                manufacturability_score=0.5,
                uncertainty=0.5,
                evidence_support=0.3,
            ),
        ],
        policy=policy,
    )

    provenance = build_ranking_provenance_report(ranking, policy)

    assert isinstance(provenance, CandidateRankingProvenanceReport)
    assert provenance.policy_id == "provenance-policy"
    assert isinstance(provenance.policy_lineage, RankingPolicyLineage)
    assert provenance.policy_lineage.policy_id == "provenance-policy"
    assert provenance.policy_lineage.policy_fingerprint
    assert provenance.entries[0].weighted_contributions
    assert any(entry.accepted is False for entry in provenance.entries)


def test_analyze_ranking_stability_reports_sensitivity_to_policy_weights() -> None:
    program = create_program_spec(
        program_id="prog-stability",
        name="ranking stability",
        objective="test ranking sensitivity",
        target_id="target-stability",
        target_name="Target Stability",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="compare candidate ordering under alternative priorities",
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.75,
        )
    )
    candidates = [
        CandidateAssessment(
            candidate_id="candidate-a",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            metric_scores={"binding_score": 0.8},
            manufacturability_score=0.55,
            uncertainty=0.15,
            evidence_support=0.92,
            reproducibility_score=0.94,
            effect_size_score=0.72,
            assay_feasibility_score=0.35,
        ),
        CandidateAssessment(
            candidate_id="candidate-b",
            sequence="ACDEFGHIKLMNPQRSTVWYA",
            metric_scores={"binding_score": 0.84},
            manufacturability_score=0.9,
            uncertainty=0.2,
            evidence_support=0.58,
            reproducibility_score=0.58,
            effect_size_score=0.68,
            assay_feasibility_score=0.94,
        ),
    ]

    report = analyze_ranking_stability(
        program,
        candidates,
        policies=[
            RankingPolicy(policy_id="baseline-stability"),
            RankingPolicy(
                policy_id="manufacturability-heavy",
                factor_weights={
                    RankingFactor.CRITERIA: 0.3,
                    RankingFactor.EVIDENCE: 0.1,
                    RankingFactor.MANUFACTURABILITY: 0.4,
                    RankingFactor.LIABILITY: 0.1,
                    RankingFactor.UNCERTAINTY: 0.1,
                },
            ),
        ],
    )

    assert isinstance(report, RankingStabilityReport)
    assert report.baseline_policy_id == "baseline-stability"
    assert report.baseline_policy_lineage.policy_id == "baseline-stability"
    assert report.baseline_policy_lineage.policy_fingerprint
    assert report.stable_top_candidate is False
    assert report.top_candidate_frequencies == {"candidate-a": 1, "candidate-b": 1}
    assert isinstance(report.scenarios[0], RankingAssumptionScenario)
    assert report.scenarios[0].policy_lineage.policy_id == "baseline-stability"
    assert any("changes across scoring assumptions" in note for note in report.notes)


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

    assert [item.candidate_id for item in ranking.ranked_candidates] == [
        "candidate-keep"
    ]
    assert ranking.rejected_candidates == ["candidate-hard-filter"]


def test_prioritize_candidates_rejects_low_metric_coverage() -> None:
    program = create_program_spec(
        program_id="prog-coverage-filter",
        name="coverage filter",
        objective="reject candidates with missing criterion metrics",
        target_id="target-coverage-filter",
        target_name="Target Coverage Filter",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="enforce criterion metric coverage",
    )
    program.success_criteria.extend(
        [
            SuccessCriterion(
                criterion_id="binding",
                metric="binding_score",
                direction=MeasurementDirection.MAXIMIZE,
                threshold=0.8,
            ),
            SuccessCriterion(
                criterion_id="stability",
                metric="delta_tm",
                direction=MeasurementDirection.MAXIMIZE,
                threshold=1.5,
            ),
        ]
    )
    ranking = prioritize_candidates(
        program,
        [
            CandidateAssessment(
                candidate_id="candidate-missing-metric",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.9},
                manufacturability_score=0.8,
                uncertainty=0.1,
                evidence_support=0.8,
            )
        ],
        policy=RankingPolicy(policy_id="coverage-policy", minimum_metric_coverage=1.0),
    )

    assert ranking.rejected_candidates == ["candidate-missing-metric"]
    assert ranking.rejections[0].reason_codes == [
        RejectionReasonCode.LOW_METRIC_COVERAGE
    ]


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
                "scientific_value=0.62",
                "reproducibility=0.50",
                "assay_feasibility=0.66",
                "assessment confidence remains high enough for active consideration",
            ],
            open_risks=["Predicted aggregation hotspot"],
            evidence_gaps=["literature", "structure", "assay"],
        )
    ]


def test_summarize_uncertainty_pressure_identifies_low_confidence_cluster() -> None:
    program = create_program_spec(
        program_id="prog-uncertainty",
        name="uncertainty pressure",
        objective="surface uncertainty pressure in ranking outputs",
        target_id="target-uncertainty",
        target_name="Target Uncertainty",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="rank candidates with confidence-aware summaries",
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
                candidate_id="candidate-high",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.9},
                manufacturability_score=0.8,
                uncertainty=0.1,
                evidence_support=0.8,
            ),
            CandidateAssessment(
                candidate_id="candidate-low",
                sequence="ACDEFGHIKLMNPQRSTVWA",
                metric_scores={"binding_score": 0.85},
                manufacturability_score=0.75,
                uncertainty=0.45,
                evidence_support=0.6,
            ),
        ],
    )

    summary = summarize_uncertainty_pressure(ranking, confidence_floor=0.65)

    assert summary.candidate_count == 2
    assert "candidate-low" in summary.low_confidence_candidate_ids


def test_summarize_novelty_diversity_reports_liability_diversity() -> None:
    program = create_program_spec(
        program_id="prog-diversity",
        name="diversity summary",
        objective="summarize novelty and liability diversity in ranking",
        target_id="target-diversity",
        target_name="Target Diversity",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="capture diversity pressure in ranked outputs",
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
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.87},
                manufacturability_score=0.8,
                uncertainty=0.1,
                evidence_support=0.8,
                liabilities=[
                    LiabilityFlag(
                        code="aggregation", summary="agg", severity=3, source="model"
                    )
                ],
            ),
            CandidateAssessment(
                candidate_id="candidate-b",
                sequence="ACDEFGHIKLMNPQRSTVWA",
                metric_scores={"binding_score": 0.86},
                manufacturability_score=0.79,
                uncertainty=0.1,
                evidence_support=0.8,
                liabilities=[
                    LiabilityFlag(
                        code="safety", summary="safety", severity=3, source="model"
                    )
                ],
            ),
        ],
    )

    summary = summarize_novelty_diversity(ranking)

    assert summary.candidate_count == 2
    assert summary.unique_liability_codes >= 2


def test_build_ranking_robustness_report_combines_confidence_and_diversity() -> None:
    program = create_program_spec(
        program_id="prog-robustness",
        name="robustness report",
        objective="combine confidence pressure and diversity in one report",
        target_id="target-robustness",
        target_name="Target Robustness",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="evaluate ranking robustness",
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
                candidate_id="candidate-a",
                sequence="ACDEFGHIKLMNPQRSTVWY",
                metric_scores={"binding_score": 0.9},
                manufacturability_score=0.85,
                uncertainty=0.1,
                evidence_support=0.85,
            ),
            CandidateAssessment(
                candidate_id="candidate-b",
                sequence="ACDEFGHIKLMNPQRSTVWA",
                metric_scores={"binding_score": 0.88},
                manufacturability_score=0.8,
                uncertainty=0.2,
                evidence_support=0.8,
            ),
        ],
    )

    report = build_ranking_robustness_report(ranking)

    assert report.robustness_score > 0.5
    assert report.uncertainty_summary.candidate_count == 2


def test_summarize_metric_coverage_reports_missing_required_metrics() -> None:
    program = create_program_spec(
        program_id="prog-metric-coverage",
        name="metric coverage",
        objective="make missing candidate metrics explicit",
        target_id="target-metric-coverage",
        target_name="Target Metric Coverage",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="surface missing criteria metrics",
    )
    program.success_criteria.extend(
        [
            SuccessCriterion(
                criterion_id="binding",
                metric="binding_score",
                direction=MeasurementDirection.MAXIMIZE,
                threshold=0.8,
            ),
            SuccessCriterion(
                criterion_id="stability",
                metric="delta_tm",
                direction=MeasurementDirection.MAXIMIZE,
                threshold=1.5,
            ),
        ]
    )
    summary = summarize_metric_coverage(
        CandidateAssessment(
            candidate_id="candidate-metric-gap",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            metric_scores={"binding_score": 0.87},
        ),
        program,
    )

    assert summary.coverage_fraction == 0.5
    assert summary.missing_metrics == ["delta_tm"]


def test_criterion_satisfaction_vector_tracks_per_criterion_pass_fail() -> None:
    program = create_program_spec(
        program_id="prog-criterion-vector",
        name="criterion vector",
        objective="show criterion-level satisfaction for candidates",
        target_id="target-criterion-vector",
        target_name="Target Criterion Vector",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="map pass fail by criterion",
    )
    program.success_criteria.extend(
        [
            SuccessCriterion(
                criterion_id="binding",
                metric="binding_score",
                direction=MeasurementDirection.MAXIMIZE,
                threshold=0.8,
            ),
            SuccessCriterion(
                criterion_id="stability",
                metric="delta_tm",
                direction=MeasurementDirection.MAXIMIZE,
                threshold=1.5,
            ),
        ]
    )
    vector = criterion_satisfaction_vector(
        CandidateAssessment(
            candidate_id="candidate-criterion-vector",
            sequence="ACDEFGHIKLMNPQRSTVWY",
            metric_scores={"binding_score": 0.85, "delta_tm": 1.2},
        ),
        program,
    )

    assert vector.satisfied_fraction == 0.5
    assert [item.satisfied for item in vector.items] == [True, False]


def test_summarize_ranking_drift_reports_movements_and_entry_exit() -> None:
    previous = CandidateRanking(
        program_id="prog-drift",
        ranked_candidates=[
            RankedCandidate(candidate_id="c1", score=1.2, rank=1),
            RankedCandidate(candidate_id="c2", score=1.1, rank=2),
        ],
    )
    current = CandidateRanking(
        program_id="prog-drift",
        ranked_candidates=[
            RankedCandidate(candidate_id="c2", score=1.2, rank=1),
            RankedCandidate(candidate_id="c3", score=1.0, rank=2),
        ],
    )

    report = summarize_ranking_drift(previous, current)

    assert report.newly_ranked_candidate_ids == ["c3"]
    assert report.dropped_candidate_ids == ["c1"]
    assert report.moved_candidates[0].candidate_id == "c2"


def test_build_ranking_diagnostics_combines_robustness_and_rejections() -> None:
    ranking = CandidateRanking(
        program_id="prog-diagnostics",
        ranked_candidates=[RankedCandidate(candidate_id="c1", score=0.9, rank=1)],
        rejections=[
            CandidateRejection(
                candidate_id="c2",
                reason_codes=[RejectionReasonCode.LOW_EVIDENCE_SUPPORT],
            )
        ],
    )

    diagnostics = build_ranking_diagnostics(ranking)

    assert diagnostics.robustness.robustness_score >= 0.0
    assert diagnostics.rejection_summary.rejection_count == 1


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
    assert (
        classify_metric_name("target_engagement_ratio")
        is ScientificMetricClass.TARGET_ENGAGEMENT
    )
    assert (
        classify_metric_name("pathway_phospho_response")
        is ScientificMetricClass.PATHWAY_EFFECT
    )
    assert (
        classify_metric_name("proteomics_fold_change")
        is ScientificMetricClass.ABUNDANCE_MODULATION
    )


def test_candidate_rejection_supports_reopen_action_guidance() -> None:
    rejection = prioritize_candidates(
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

    assert (
        "collect orthogonal evidence across at least two modalities" in plan.experiments
    )


def test_build_rejection_action_plan_handles_low_metric_coverage_reason() -> None:
    plan = build_rejection_action_plan(
        CandidateRejection(
            candidate_id="candidate-coverage",
            reasons=["missing required metrics"],
            reason_codes=[RejectionReasonCode.LOW_METRIC_COVERAGE],
        )
    )

    assert (
        "collect missing criterion-linked assay metrics before reranking"
        in plan.experiments
    )


def test_summarize_rejections_counts_reason_codes() -> None:
    summary = summarize_rejections(
        [
            CandidateRejection(
                candidate_id="c1",
                reason_codes=[RejectionReasonCode.LOW_EVIDENCE_SUPPORT],
                blocking=True,
            ),
            CandidateRejection(
                candidate_id="c2",
                reason_codes=[
                    RejectionReasonCode.LOW_EVIDENCE_SUPPORT,
                    RejectionReasonCode.LOW_METRIC_COVERAGE,
                ],
                blocking=False,
            ),
        ]
    )

    assert summary.rejection_count == 2
    assert summary.by_reason_code["low_evidence_support"] == 2
    assert summary.by_reason_code["low_metric_coverage"] == 1
    assert summary.blocking_rejection_count == 1


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


def test_validate_metric_catalog_reports_missing_definitions() -> None:
    policy = RankingPolicy(
        policy_id="catalog-policy",
        metric_catalog=[
            MetricDefinition(
                metric_key="binding_kd",
                metric_class=ScientificMetricClass.AFFINITY,
                unit="nM",
                direction=MetricDirection.LOWER_IS_BETTER,
            )
        ],
    )

    missing = validate_metric_catalog(policy, ["binding_kd", "delta_tm"])

    assert missing == ["delta_tm"]


def test_audit_metric_catalog_reports_duplicates_and_missing_classes() -> None:
    policy = RankingPolicy(
        policy_id="audit-policy",
        metric_catalog=[
            MetricDefinition(
                metric_key="binding_kd",
                metric_class=ScientificMetricClass.AFFINITY,
                unit="nM",
                direction=MetricDirection.LOWER_IS_BETTER,
            ),
            MetricDefinition(
                metric_key="binding_kd",
                metric_class=ScientificMetricClass.AFFINITY,
                unit="nM",
                direction=MetricDirection.LOWER_IS_BETTER,
            ),
        ],
    )

    report = audit_metric_catalog(policy, ["binding_kd", "delta_tm"])

    assert report.missing_metric_keys == ["delta_tm"]
    assert report.duplicate_metric_keys == ["binding_kd"]
    assert "stability" in report.missing_metric_classes


def test_validate_factor_weights_reports_normalization_and_missing_factors() -> None:
    report = validate_factor_weights(
        RankingPolicy(
            policy_id="weights",
            factor_weights={
                RankingFactor.CRITERIA: 0.6,
                RankingFactor.EVIDENCE: 0.3,
            },
        )
    )

    assert "manufacturability" in report.missing_factors
    assert report.normalized is False


def test_ranking_policy_lineage_changes_when_policy_revision_changes() -> None:
    baseline_policy = RankingPolicy(
        policy_id="lineage-policy",
        policy_family="candidate_prioritization",
        policy_version=1,
    )
    revised_policy = RankingPolicy(
        policy_id="lineage-policy",
        policy_family="candidate_prioritization",
        policy_version=2,
        diversity_bonus_weight=0.2,
    )

    baseline_lineage = ranking_policy_lineage(baseline_policy)
    revised_lineage = ranking_policy_lineage(revised_policy)

    assert baseline_lineage.policy_id == revised_lineage.policy_id
    assert baseline_lineage.policy_version == 1
    assert revised_lineage.policy_version == 2
    assert baseline_lineage.policy_fingerprint != revised_lineage.policy_fingerprint


def test_summarize_liability_focus_counts_top_blockers() -> None:
    ranking = CandidateRanking(
        program_id="prog-liability-focus",
        ranked_candidates=[
            RankedCandidate(
                candidate_id="candidate-a",
                score=0.9,
                rank=1,
                explainability={"blockers": ["aggregation-risk", "expression-risk"]},
            ),
            RankedCandidate(
                candidate_id="candidate-b",
                score=0.8,
                rank=2,
                explainability={"blockers": ["aggregation-risk"]},
            ),
        ],
    )

    summary = summarize_liability_focus(ranking)

    assert isinstance(summary, LiabilityFocusSummary)
    assert summary.liability_counts["aggregation-risk"] == 2
    assert summary.top_liabilities[0] == "aggregation-risk"
