# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics_intelligence


def test_interpretation_public_api_contains_expected_exports() -> None:
    assert "build_run_interpretation_summary" in bijux_proteomics_intelligence.__all__
    assert "interpret_differential_abundance" in bijux_proteomics_intelligence.__all__
    assert "interpret_ptm_sites" in bijux_proteomics_intelligence.__all__
    assert "interpret_contaminant_artifacts" in bijux_proteomics_intelligence.__all__
    assert "recommend_experimental_contrasts" in bijux_proteomics_intelligence.__all__
    assert "analyze_missingness_patterns" in bijux_proteomics_intelligence.__all__
    assert "explain_outlier_samples" in bijux_proteomics_intelligence.__all__
    assert "extract_biological_themes" in bijux_proteomics_intelligence.__all__
    assert "compute_protein_set_enrichment" in bijux_proteomics_intelligence.__all__
    assert "compute_ranked_enrichment" in bijux_proteomics_intelligence.__all__
    assert "AnalyticalContrastRejectionReason" in bijux_proteomics_intelligence.__all__
    assert "RunInterpretationSummary" in bijux_proteomics_intelligence.__all__
    assert (
        "DifferentialAbundanceInterpretation" in bijux_proteomics_intelligence.__all__
    )
    assert "PtmInterpretationReport" in bijux_proteomics_intelligence.__all__
    assert "ContaminantArtifactIntelligence" in bijux_proteomics_intelligence.__all__
    assert (
        "AnalyticalContrastRecommendationReport"
        in bijux_proteomics_intelligence.__all__
    )
    assert "MissingnessPatternAnalysis" in bijux_proteomics_intelligence.__all__
    assert "PathwayInterpretationCautionReport" in bijux_proteomics_intelligence.__all__
    assert "PathwayInterpretationCautionCode" in bijux_proteomics_intelligence.__all__
    assert "OutlierInterpretationClass" in bijux_proteomics_intelligence.__all__
    assert "OutlierSampleExplanation" in bijux_proteomics_intelligence.__all__
    assert "BiologicalThemeExtraction" in bijux_proteomics_intelligence.__all__
    assert "ProteinSetEnrichmentReport" in bijux_proteomics_intelligence.__all__
    assert "RankedEnrichmentReport" in bijux_proteomics_intelligence.__all__


def test_judgment_public_api_contains_expected_exports() -> None:
    assert "DEFAULT_INTELLIGENCE_CHARTER" in bijux_proteomics_intelligence.__all__
    assert (
        "DEFAULT_INTELLIGENCE_CHARTER_ENTRIES" in bijux_proteomics_intelligence.__all__
    )
    assert "DEFAULT_INTELLIGENCE_MODULE_AUDIT" in bijux_proteomics_intelligence.__all__
    assert "IntelligenceCharterCapability" in bijux_proteomics_intelligence.__all__
    assert "IntelligenceModuleClassification" in bijux_proteomics_intelligence.__all__
    assert "GroundedDecisionRule" in bijux_proteomics_intelligence.__all__
    assert "RankingRuleGroundingLedger" in bijux_proteomics_intelligence.__all__
    assert "EvidenceContradictionSummary" in bijux_proteomics_intelligence.__all__
    assert "EvidenceFreshnessSummary" in bijux_proteomics_intelligence.__all__
    assert "CandidateRankingSensitivityReport" in bijux_proteomics_intelligence.__all__
    assert "RankingPolicyLineage" in bijux_proteomics_intelligence.__all__
    assert "ReviewBoardPacket" in bijux_proteomics_intelligence.__all__
    assert "SkepticalReviewReport" in bijux_proteomics_intelligence.__all__
    assert "WorkflowBenchmarkReview" in bijux_proteomics_intelligence.__all__
    assert "ReviewChallenge" in bijux_proteomics_intelligence.__all__
    assert "BenchmarkReviewClaim" in bijux_proteomics_intelligence.__all__
    assert "build_ranking_sensitivity_report" in bijux_proteomics_intelligence.__all__
    assert (
        "build_ranking_rule_grounding_ledger" in bijux_proteomics_intelligence.__all__
    )
    assert "build_review_board_packet" in bijux_proteomics_intelligence.__all__
    assert "build_skeptical_review_report" in bijux_proteomics_intelligence.__all__
    assert "build_dda_benchmark_review" in bijux_proteomics_intelligence.__all__
    assert "build_dia_benchmark_review" in bijux_proteomics_intelligence.__all__
    assert "build_ptm_benchmark_review" in bijux_proteomics_intelligence.__all__
    assert "build_lfq_benchmark_review" in bijux_proteomics_intelligence.__all__
    assert "build_multiplex_benchmark_review" in bijux_proteomics_intelligence.__all__
    assert "ranking_policy_lineage" in bijux_proteomics_intelligence.__all__
    assert "rule_grounding_map" in bijux_proteomics_intelligence.__all__
    assert "assess_recommendation_readiness" in bijux_proteomics_intelligence.__all__
    assert "summarize_evidence_contradictions" in bijux_proteomics_intelligence.__all__
    assert "summarize_evidence_freshness" in bijux_proteomics_intelligence.__all__
