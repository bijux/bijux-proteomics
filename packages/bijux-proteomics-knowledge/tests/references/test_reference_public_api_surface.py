# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references import (
    BenchmarkComparatorFailureReport,
    BenchmarkLiteratureGapMatrix,
    BenchmarkManifest,
    BenchmarkRegistryEntry,
    ComparatorLiteratureGapMatrix,
    ComparatorPositionReport,
    KnowledgeDeficitSeverity,
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    KnowledgeWorkflowFamily,
    WorkflowBenchmarkPackage,
    WorkflowBibliographyExport,
    WorkflowClaimCitationTable,
    WorkflowComparatorConfrontation,
    WorkflowComparatorMatrixReport,
    WorkflowComparatorRegressionReport,
    WorkflowComparatorScorecard,
    WorkflowContradictionDossier,
    WorkflowContradictionTriageReport,
    WorkflowEvidenceSufficiencyRubric,
    WorkflowLiteratureFreshnessAudit,
    WorkflowLiteratureMatrix,
    WorkflowReferenceBriefing,
    WorkflowScientificReadingPack,
    WorkflowUnsupportedClaimLedger,
    get_benchmark_literature_gap_matrix,
    build_benchmark_comparator_failure_report,
    get_comparator_literature_gap_matrix,
    get_workflow_bibliography_export,
    get_workflow_claim_citation_table,
    build_workflow_comparator_matrix,
    build_workflow_reference_briefing,
    get_benchmark_manifest,
    get_benchmark_package,
    get_benchmark_registry_entry,
    get_comparator_position_report,
    get_workflow_comparator_confrontation,
    get_workflow_comparator_regression_report,
    get_workflow_comparator_scorecard,
    get_workflow_contradiction_dossier,
    get_workflow_contradiction_triage_report,
    get_workflow_evidence_sufficiency_rubric,
    get_workflow_knowledge_deficit_report,
    get_workflow_literature_freshness_audit,
    get_workflow_literature_matrix,
    get_workflow_scientific_reading_pack,
    get_workflow_unsupported_claim_ledger,
    resolve_ontology_mapping,
)


def test_knowledge_references_root_exposes_curated_reference_anchors() -> None:
    briefing = build_workflow_reference_briefing(KnowledgeWorkflowFamily.DIA)
    manifest = get_benchmark_manifest("benchmark:dia_library_extraction_consistency")
    package = get_benchmark_package("benchmark:dia_library_extraction_consistency")
    registry_entry = get_benchmark_registry_entry(
        "benchmark:dia_library_extraction_consistency"
    )
    comparator_failures = build_benchmark_comparator_failure_report(
        workflow_family=KnowledgeWorkflowFamily.DIA
    )
    comparator_confrontation = get_workflow_comparator_confrontation(
        KnowledgeWorkflowFamily.DIA
    )
    comparator_matrix = build_workflow_comparator_matrix(
        workflow_family=KnowledgeWorkflowFamily.DIA
    )
    comparator_scorecard = get_workflow_comparator_scorecard(
        KnowledgeWorkflowFamily.DIA
    )
    comparator_positions = get_comparator_position_report()
    comparator_regressions = get_workflow_comparator_regression_report()
    claim_citation_table = get_workflow_claim_citation_table(KnowledgeWorkflowFamily.DIA)
    literature_matrix = get_workflow_literature_matrix(KnowledgeWorkflowFamily.DIA)
    literature_freshness_audit = get_workflow_literature_freshness_audit(
        KnowledgeWorkflowFamily.DIA
    )
    bibliography_export = get_workflow_bibliography_export(
        KnowledgeWorkflowFamily.DIA
    )
    contradiction_dossier = get_workflow_contradiction_dossier(
        KnowledgeWorkflowFamily.DIA
    )
    contradiction_triage = get_workflow_contradiction_triage_report(
        KnowledgeWorkflowFamily.DIA
    )
    sufficiency_rubric = get_workflow_evidence_sufficiency_rubric(
        KnowledgeWorkflowFamily.DIA
    )
    deficit_report = get_workflow_knowledge_deficit_report(
        KnowledgeWorkflowFamily.DIA
    )
    unsupported_claim_ledger = get_workflow_unsupported_claim_ledger(
        KnowledgeWorkflowFamily.DIA
    )
    reading_pack = get_workflow_scientific_reading_pack(KnowledgeWorkflowFamily.DIA)
    benchmark_gap_matrix = get_benchmark_literature_gap_matrix()
    comparator_gap_matrix = get_comparator_literature_gap_matrix()
    mapping = resolve_ontology_mapping(KnowledgeOntologyDomain.PTM, "phospho")

    assert isinstance(briefing, WorkflowReferenceBriefing)
    assert isinstance(manifest, BenchmarkManifest)
    assert isinstance(package, WorkflowBenchmarkPackage)
    assert isinstance(registry_entry, BenchmarkRegistryEntry)
    assert isinstance(comparator_failures, BenchmarkComparatorFailureReport)
    assert isinstance(comparator_confrontation, WorkflowComparatorConfrontation)
    assert isinstance(comparator_matrix, WorkflowComparatorMatrixReport)
    assert isinstance(comparator_scorecard, WorkflowComparatorScorecard)
    assert isinstance(comparator_positions, ComparatorPositionReport)
    assert isinstance(comparator_regressions, WorkflowComparatorRegressionReport)
    assert isinstance(claim_citation_table, WorkflowClaimCitationTable)
    assert isinstance(literature_matrix, WorkflowLiteratureMatrix)
    assert isinstance(literature_freshness_audit, WorkflowLiteratureFreshnessAudit)
    assert isinstance(bibliography_export, WorkflowBibliographyExport)
    assert isinstance(contradiction_dossier, WorkflowContradictionDossier)
    assert isinstance(contradiction_triage, WorkflowContradictionTriageReport)
    assert isinstance(sufficiency_rubric, WorkflowEvidenceSufficiencyRubric)
    assert deficit_report.highest_severity in set(KnowledgeDeficitSeverity)
    assert isinstance(unsupported_claim_ledger, WorkflowUnsupportedClaimLedger)
    assert isinstance(reading_pack, WorkflowScientificReadingPack)
    assert isinstance(benchmark_gap_matrix, BenchmarkLiteratureGapMatrix)
    assert isinstance(comparator_gap_matrix, ComparatorLiteratureGapMatrix)
    assert isinstance(mapping, KnowledgeOntologyMapping)
