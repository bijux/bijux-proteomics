# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Interpretation owners for runs, pathways, PTM, contaminants, and quantitative readouts."""

from __future__ import annotations

from bijux_proteomics_intelligence.interpretation.contaminants import (
    ContaminantArtifactFinding,
    ContaminantArtifactIntelligence,
    extract_contaminant_theme,
    interpret_contaminant_artifacts,
)
from bijux_proteomics_intelligence.interpretation.contrasts import (
    AnalyticalContrastRecommendation,
    AnalyticalContrastRecommendationReport,
    AnalyticalContrastRejectionReason,
    recommend_experimental_contrasts,
)
from bijux_proteomics_intelligence.interpretation.pathways import (
    AnnotationCategory,
    BiologicalTheme,
    BiologicalThemeExtraction,
    DifferentialAbundanceInterpretation,
    DifferentialConditionSignal,
    DifferentialStatisticalProvenance,
    EnrichmentProvenance,
    InterpretationClaimScope,
    PathwayInterpretationCaution,
    PathwayInterpretationCautionCode,
    PathwayInterpretationCautionReport,
    ProteinAnnotationAssignment,
    ProteinSetEnrichmentEntry,
    ProteinSetEnrichmentReport,
    RankedEnrichmentEntry,
    RankedEnrichmentReport,
    RankedEntityScore,
    SignalDirection,
    compute_protein_set_enrichment,
    compute_ranked_enrichment,
    extract_biological_themes,
    interpret_differential_abundance,
)
from bijux_proteomics_intelligence.interpretation.ptm import (
    PtmInterpretationReport,
    PtmInterpretationSite,
    interpret_ptm_sites,
)
from bijux_proteomics_intelligence.interpretation.quantitative import (
    MissingnessPatternAnalysis,
    MissingnessPatternEntry,
    MissingnessPatternLabel,
    OutlierInterpretationClass,
    OutlierSampleExplanation,
    QuantQcEvidenceIntegrationReport,
    analyze_missingness_patterns,
    explain_outlier_samples,
    integrate_quant_qc_evidence,
)
from bijux_proteomics_intelligence.interpretation.runs import (
    RunInterpretationSignal,
    RunInterpretationSummary,
    build_run_interpretation_summary,
)
from bijux_proteomics_intelligence.interpretation.structures import (
    compute_metrics,
    low_confidence_segments,
)

__all__ = [
    "AnalyticalContrastRecommendation",
    "AnalyticalContrastRecommendationReport",
    "AnalyticalContrastRejectionReason",
    "AnnotationCategory",
    "BiologicalTheme",
    "BiologicalThemeExtraction",
    "ContaminantArtifactFinding",
    "ContaminantArtifactIntelligence",
    "DifferentialAbundanceInterpretation",
    "DifferentialConditionSignal",
    "DifferentialStatisticalProvenance",
    "EnrichmentProvenance",
    "InterpretationClaimScope",
    "MissingnessPatternAnalysis",
    "MissingnessPatternEntry",
    "MissingnessPatternLabel",
    "OutlierInterpretationClass",
    "OutlierSampleExplanation",
    "PathwayInterpretationCaution",
    "PathwayInterpretationCautionCode",
    "PathwayInterpretationCautionReport",
    "ProteinAnnotationAssignment",
    "ProteinSetEnrichmentEntry",
    "ProteinSetEnrichmentReport",
    "PtmInterpretationReport",
    "PtmInterpretationSite",
    "QuantQcEvidenceIntegrationReport",
    "RankedEnrichmentEntry",
    "RankedEnrichmentReport",
    "RankedEntityScore",
    "RunInterpretationSignal",
    "RunInterpretationSummary",
    "SignalDirection",
    "build_run_interpretation_summary",
    "compute_metrics",
    "compute_protein_set_enrichment",
    "compute_ranked_enrichment",
    "explain_outlier_samples",
    "extract_biological_themes",
    "extract_contaminant_theme",
    "integrate_quant_qc_evidence",
    "interpret_contaminant_artifacts",
    "interpret_differential_abundance",
    "interpret_ptm_sites",
    "low_confidence_segments",
    "recommend_experimental_contrasts",
    "analyze_missingness_patterns",
]
