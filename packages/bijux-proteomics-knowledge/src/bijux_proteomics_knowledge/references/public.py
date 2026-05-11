# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated public entrypoints for grounded knowledge references."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.grounding.contexts import (
    ScientificContextEntry,
)
from bijux_proteomics_knowledge.references.grounding.ontologies import (
    KnowledgeOntologyDomain,
    KnowledgeOntologyMapping,
    resolve_ontology_mapping,
)
from bijux_proteomics_knowledge.references.grounding.rules import (
    ScientificRuleReference,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkEvidenceTier,
    BenchmarkManifest,
    BenchmarkPackageArtifact,
    BenchmarkPackageArtifactKind,
    BenchmarkReproductionStep,
    KnowledgeWorkflowFamily,
    WorkflowBenchmarkPackage,
)
from bijux_proteomics_knowledge.references.workflows.briefings import (
    WorkflowReferenceBriefing,
    build_workflow_reference_briefing,
)
from bijux_proteomics_knowledge.references.workflows.claim_grounding import (
    WorkflowClaimCitationTable,
    WorkflowUnsupportedClaimLedger,
)
from bijux_proteomics_knowledge.references.workflows.comparator_confrontations import (
    WorkflowComparatorConfrontation,
    WorkflowComparatorConfrontationReport,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    BenchmarkComparatorFailureEntry,
    BenchmarkComparatorFailureReport,
    ComparatorClaimSupportState,
    ComparatorFailureSeverity,
    build_benchmark_comparator_failure_report,
)
from bijux_proteomics_knowledge.references.workflows.comparator_positions import (
    ComparatorPositionEntry,
    ComparatorPositionKind,
    ComparatorPositionReport,
)
from bijux_proteomics_knowledge.references.workflows.comparator_regressions import (
    ComparatorRegressionStatus,
    WorkflowComparatorRegressionEntry,
    WorkflowComparatorRegressionReport,
)
from bijux_proteomics_knowledge.references.workflows.comparator_scorecards import (
    WorkflowComparatorScorecard,
    WorkflowComparatorScorecardReport,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    ProteomicsComparatorTool,
    WorkflowComparatorMatrixEntry,
    WorkflowComparatorMatrixReport,
    WorkflowComparatorPath,
    WorkflowComparatorToolStatus,
    build_workflow_comparator_matrix,
    get_workflow_comparator_path,
    list_workflow_comparator_paths,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_dossiers import (
    WorkflowContradictionDossier,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_triage import (
    WorkflowContradictionTriageReport,
)
from bijux_proteomics_knowledge.references.workflows.evidence_sufficiency import (
    WorkflowEvidenceSufficiencyRubric,
    WorkflowEvidenceTrustTier,
)
from bijux_proteomics_knowledge.references.workflows.knowledge_deficits import (
    KnowledgeDeficitSeverity,
    WorkflowKnowledgeDeficitReport,
)
from bijux_proteomics_knowledge.references.workflows.literature_audits import (
    BenchmarkLiteratureGapMatrix,
    ComparatorLiteratureGapMatrix,
    WorkflowBibliographyExport,
    WorkflowLiteratureFreshnessAudit,
)
from bijux_proteomics_knowledge.references.workflows.literature_matrices import (
    WorkflowLiteratureMatrix,
    WorkflowLiteratureMatrixEntry,
)
from bijux_proteomics_knowledge.references.workflows.lookups import (
    get_benchmark_comparator_failure,
    get_benchmark_literature_gap_matrix,
    get_benchmark_manifest,
    get_benchmark_package,
    get_benchmark_registry_entry,
    get_comparator_literature_gap_matrix,
    get_comparator_position_report,
    get_workflow_bibliography_export,
    get_workflow_claim_citation_table,
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
    list_benchmark_comparator_failures,
    list_benchmark_registry_entries,
    list_comparator_positions,
    list_workflow_bibliography_exports_lookup,
    list_workflow_claim_citation_tables_lookup,
    list_workflow_comparator_confrontations,
    list_workflow_comparator_scorecards,
    list_workflow_contradiction_dossiers_lookup,
    list_workflow_contradiction_triage_reports_lookup,
    list_workflow_evidence_sufficiency_rubrics_lookup,
    list_workflow_knowledge_deficit_reports_lookup,
    list_workflow_literature_freshness_audits_lookup,
    list_workflow_literature_matrices_lookup,
    list_workflow_scientific_reading_packs_lookup,
    list_workflow_unsupported_claim_ledgers_lookup,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkAuthorityAssessment,
    BenchmarkAuthorityStatus,
    BenchmarkRegistryEntry,
    BenchmarkRegistryReport,
    assess_benchmark_authority,
    build_benchmark_registry,
)
from bijux_proteomics_knowledge.references.workflows.scientific_reading_packs import (
    WorkflowScientificReadingPack,
)

__all__ = [
    "BenchmarkAuthorityAssessment",
    "BenchmarkAuthorityStatus",
    "BenchmarkComparatorFailureEntry",
    "BenchmarkComparatorFailureReport",
    "BenchmarkEvidenceTier",
    "BenchmarkLiteratureGapMatrix",
    "BenchmarkManifest",
    "BenchmarkPackageArtifact",
    "BenchmarkPackageArtifactKind",
    "BenchmarkReproductionStep",
    "BenchmarkRegistryEntry",
    "BenchmarkRegistryReport",
    "ComparatorClaimSupportState",
    "ComparatorLiteratureGapMatrix",
    "ComparatorFailureSeverity",
    "ComparatorPositionEntry",
    "ComparatorPositionKind",
    "ComparatorPositionReport",
    "ComparatorRegressionStatus",
    "WorkflowBibliographyExport",
    "WorkflowClaimCitationTable",
    "KnowledgeOntologyDomain",
    "KnowledgeOntologyMapping",
    "KnowledgeDeficitSeverity",
    "KnowledgeWorkflowFamily",
    "ProteomicsComparatorTool",
    "ScientificContextEntry",
    "ScientificRuleReference",
    "WorkflowBenchmarkPackage",
    "WorkflowComparatorConfrontation",
    "WorkflowComparatorConfrontationReport",
    "WorkflowContradictionDossier",
    "WorkflowContradictionTriageReport",
    "WorkflowComparatorMatrixEntry",
    "WorkflowComparatorMatrixReport",
    "WorkflowComparatorPath",
    "WorkflowComparatorRegressionEntry",
    "WorkflowComparatorRegressionReport",
    "WorkflowComparatorScorecard",
    "WorkflowComparatorScorecardReport",
    "WorkflowComparatorToolStatus",
    "WorkflowEvidenceSufficiencyRubric",
    "WorkflowEvidenceTrustTier",
    "WorkflowKnowledgeDeficitReport",
    "WorkflowLiteratureFreshnessAudit",
    "WorkflowLiteratureMatrix",
    "WorkflowLiteratureMatrixEntry",
    "WorkflowReferenceBriefing",
    "WorkflowScientificReadingPack",
    "WorkflowUnsupportedClaimLedger",
    "assess_benchmark_authority",
    "build_benchmark_registry",
    "build_benchmark_comparator_failure_report",
    "build_workflow_comparator_matrix",
    "build_workflow_reference_briefing",
    "get_benchmark_literature_gap_matrix",
    "get_benchmark_comparator_failure",
    "get_benchmark_manifest",
    "get_benchmark_package",
    "get_benchmark_registry_entry",
    "get_comparator_literature_gap_matrix",
    "get_comparator_position_report",
    "get_workflow_bibliography_export",
    "get_workflow_claim_citation_table",
    "get_workflow_comparator_confrontation",
    "get_workflow_contradiction_dossier",
    "get_workflow_contradiction_triage_report",
    "get_workflow_comparator_path",
    "get_workflow_comparator_regression_report",
    "get_workflow_comparator_scorecard",
    "get_workflow_evidence_sufficiency_rubric",
    "get_workflow_knowledge_deficit_report",
    "get_workflow_literature_freshness_audit",
    "get_workflow_literature_matrix",
    "get_workflow_scientific_reading_pack",
    "get_workflow_unsupported_claim_ledger",
    "list_benchmark_comparator_failures",
    "list_benchmark_registry_entries",
    "list_comparator_positions",
    "list_workflow_bibliography_exports_lookup",
    "list_workflow_claim_citation_tables_lookup",
    "list_workflow_comparator_confrontations",
    "list_workflow_comparator_scorecards",
    "list_workflow_contradiction_dossiers_lookup",
    "list_workflow_contradiction_triage_reports_lookup",
    "list_workflow_evidence_sufficiency_rubrics_lookup",
    "list_workflow_knowledge_deficit_reports_lookup",
    "list_workflow_literature_freshness_audits_lookup",
    "list_workflow_literature_matrices_lookup",
    "list_workflow_scientific_reading_packs_lookup",
    "list_workflow_unsupported_claim_ledgers_lookup",
    "list_workflow_comparator_paths",
    "resolve_ontology_mapping",
]
