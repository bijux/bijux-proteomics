# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Read-only query helpers over workflow benchmark and narrative surfaces."""

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    BenchmarkManifest,
    BenchmarkPackageArtifact,
    BenchmarkPackageArtifactKind,
    BenchmarkReproductionStep,
    KnowledgeWorkflowFamily,
    WorkflowBenchmarkPackage,
)
from bijux_proteomics_knowledge.references.workflows.claim_grounding import (
    WorkflowClaimCitationTable,
    WorkflowUnsupportedClaimLedger,
    build_workflow_claim_citation_table,
    build_workflow_unsupported_claim_ledger,
    list_workflow_claim_citation_tables,
    list_workflow_unsupported_claim_ledgers,
)
from bijux_proteomics_knowledge.references.workflows.comparator_confrontations import (
    WorkflowComparatorConfrontation,
    WorkflowComparatorConfrontationReport,
    build_workflow_comparator_confrontation,
    build_workflow_comparator_confrontation_report,
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
    build_comparator_position_report,
)
from bijux_proteomics_knowledge.references.workflows.comparator_regressions import (
    ComparatorRegressionStatus,
    WorkflowComparatorRegressionEntry,
    WorkflowComparatorRegressionReport,
    build_workflow_comparator_regression_report,
)
from bijux_proteomics_knowledge.references.workflows.comparator_scorecards import (
    WorkflowComparatorScorecard,
    WorkflowComparatorScorecardReport,
    build_workflow_comparator_scorecard,
    build_workflow_comparator_scorecard_report,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    WorkflowComparatorMatrixEntry,
    WorkflowComparatorMatrixReport,
    WorkflowComparatorPath,
    build_workflow_comparator_matrix,
    get_workflow_comparator_path,
    list_workflow_comparator_paths,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_dossiers import (
    WorkflowContradictionDossier,
    build_workflow_contradiction_dossier,
    list_workflow_contradiction_dossiers,
)
from bijux_proteomics_knowledge.references.workflows.contradiction_triage import (
    WorkflowContradictionTriageReport,
    build_workflow_contradiction_triage_report,
    list_workflow_contradiction_triage_reports,
)
from bijux_proteomics_knowledge.references.workflows.evidence_sufficiency import (
    WorkflowEvidenceSufficiencyRubric,
    build_workflow_evidence_sufficiency_rubric,
    list_workflow_evidence_sufficiency_rubrics,
)
from bijux_proteomics_knowledge.references.workflows.knowledge_deficits import (
    WorkflowKnowledgeDeficitReport,
    build_workflow_knowledge_deficit_report,
    list_workflow_knowledge_deficit_reports,
)
from bijux_proteomics_knowledge.references.workflows.literature_audits import (
    BenchmarkLiteratureGapMatrix,
    ComparatorLiteratureGapMatrix,
    WorkflowBibliographyExport,
    WorkflowLiteratureFreshnessAudit,
    build_benchmark_literature_gap_matrix,
    build_comparator_literature_gap_matrix,
    build_workflow_bibliography_export,
    build_workflow_literature_freshness_audit,
    list_workflow_bibliography_exports,
    list_workflow_literature_freshness_audits,
)
from bijux_proteomics_knowledge.references.workflows.literature_matrices import (
    WorkflowLiteratureMatrix,
    build_workflow_literature_matrix,
    list_workflow_literature_matrices,
)
from bijux_proteomics_knowledge.references.workflows.narratives import (
    DEFAULT_WORKFLOW_NARRATIVES,
    WorkflowNarrative,
    WorkflowNarrativeKind,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkRegistryEntry,
    BenchmarkRegistryReport,
    build_benchmark_registry,
    build_benchmark_registry_entry,
)
from bijux_proteomics_knowledge.references.workflows.scientific_reading_packs import (
    WorkflowScientificReadingPack,
    build_workflow_scientific_reading_pack,
    list_workflow_scientific_reading_packs,
)


def list_benchmark_manifests(
    *, workflow_family: KnowledgeWorkflowFamily | None = None
) -> tuple[BenchmarkManifest, ...]:
    """Return curated benchmark manifests, optionally filtered by workflow family."""

    if workflow_family is None:
        return DEFAULT_BENCHMARK_MANIFESTS
    return tuple(
        manifest
        for manifest in DEFAULT_BENCHMARK_MANIFESTS
        if manifest.workflow_family is workflow_family
    )


def get_benchmark_manifest(benchmark_id: str) -> BenchmarkManifest | None:
    """Return one benchmark manifest by stable identifier."""

    return next(
        (
            manifest
            for manifest in DEFAULT_BENCHMARK_MANIFESTS
            if manifest.benchmark_id == benchmark_id
        ),
        None,
    )


def get_benchmark_package(benchmark_id: str) -> WorkflowBenchmarkPackage | None:
    """Return the promoted benchmark package for one benchmark when available."""

    manifest = get_benchmark_manifest(benchmark_id)
    if manifest is None:
        return None
    return manifest.benchmark_package


def list_benchmark_comparator_failures(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[BenchmarkComparatorFailureEntry, ...]:
    """Return benchmark comparator failures filtered by workflow family."""

    return build_benchmark_comparator_failure_report(
        workflow_family=workflow_family
    ).entries


def get_benchmark_comparator_failure(
    benchmark_id: str,
) -> BenchmarkComparatorFailureEntry | None:
    """Return one benchmark comparator failure dossier by benchmark identifier."""

    report = build_benchmark_comparator_failure_report(benchmark_id=benchmark_id)
    return report.entries[0] if report.entries else None


def list_workflow_comparator_confrontations(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowComparatorConfrontation, ...]:
    """Return explicit workflow-family comparator confrontations."""

    return build_workflow_comparator_confrontation_report(
        workflow_family=workflow_family
    ).entries


def get_workflow_comparator_confrontation(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowComparatorConfrontation:
    """Return the comparator confrontation for one workflow family."""

    return build_workflow_comparator_confrontation(workflow_family)


def list_workflow_comparator_scorecards() -> tuple[WorkflowComparatorScorecard, ...]:
    """Return workflow-family comparator scorecards."""

    return build_workflow_comparator_scorecard_report().entries


def get_workflow_comparator_scorecard(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowComparatorScorecard:
    """Return the comparator scorecard for one workflow family."""

    return build_workflow_comparator_scorecard(workflow_family)


def list_comparator_positions(
    *,
    kind: ComparatorPositionKind | None = None,
) -> tuple[ComparatorPositionEntry, ...]:
    """Return known comparator wins and losses, optionally filtered by kind."""

    entries = build_comparator_position_report().entries
    if kind is None:
        return entries
    return tuple(entry for entry in entries if entry.kind is kind)


def get_comparator_position_report() -> ComparatorPositionReport:
    """Return the report of known comparator wins and losses."""

    return build_comparator_position_report()


def get_workflow_comparator_regression_report() -> WorkflowComparatorRegressionReport:
    """Return the workflow-family comparator regression baseline report."""

    return build_workflow_comparator_regression_report()


def list_benchmark_registry_entries(
    *, workflow_family: KnowledgeWorkflowFamily | None = None
) -> tuple[BenchmarkRegistryEntry, ...]:
    """Return public benchmark registry entries with authority posture."""

    return build_benchmark_registry(workflow_family=workflow_family).entries


def get_benchmark_registry_entry(benchmark_id: str) -> BenchmarkRegistryEntry | None:
    """Return one public benchmark registry entry by stable benchmark identifier."""

    manifest = get_benchmark_manifest(benchmark_id)
    if manifest is None:
        return None
    return build_benchmark_registry_entry(manifest)


def list_workflow_narratives(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
    narrative_kind: WorkflowNarrativeKind | None = None,
) -> tuple[WorkflowNarrative, ...]:
    """Return curated workflow narratives with optional workflow and kind filters."""

    return tuple(
        narrative
        for narrative in DEFAULT_WORKFLOW_NARRATIVES
        if (workflow_family is None or narrative.workflow_family is workflow_family)
        and (narrative_kind is None or narrative.narrative_kind is narrative_kind)
    )


def get_workflow_narrative(narrative_id: str) -> WorkflowNarrative | None:
    """Return one workflow narrative by stable identifier."""

    return next(
        (
            narrative
            for narrative in DEFAULT_WORKFLOW_NARRATIVES
            if narrative.narrative_id == narrative_id
        ),
        None,
    )


def list_workflow_literature_matrices_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowLiteratureMatrix, ...]:
    """Return curated literature matrices with optional family filtering."""

    if workflow_family is None:
        return list_workflow_literature_matrices()
    return (build_workflow_literature_matrix(workflow_family),)


def get_workflow_literature_matrix(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowLiteratureMatrix:
    """Return the curated literature matrix for one workflow family."""

    return build_workflow_literature_matrix(workflow_family)


def list_workflow_claim_citation_tables_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowClaimCitationTable, ...]:
    """Return workflow-family claim citation tables."""

    if workflow_family is None:
        return list_workflow_claim_citation_tables()
    return (build_workflow_claim_citation_table(workflow_family),)


def get_workflow_claim_citation_table(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowClaimCitationTable:
    """Return the workflow-family claim citation table."""

    return build_workflow_claim_citation_table(workflow_family)


def list_workflow_contradiction_dossiers_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowContradictionDossier, ...]:
    """Return contradiction dossiers with optional family filtering."""

    if workflow_family is None:
        return list_workflow_contradiction_dossiers()
    return (build_workflow_contradiction_dossier(workflow_family),)


def get_workflow_contradiction_dossier(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowContradictionDossier:
    """Return the contradiction dossier for one workflow family."""

    return build_workflow_contradiction_dossier(workflow_family)


def list_workflow_contradiction_triage_reports_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowContradictionTriageReport, ...]:
    """Return contradiction triage reports with optional family filtering."""

    if workflow_family is None:
        return list_workflow_contradiction_triage_reports()
    return (build_workflow_contradiction_triage_report(workflow_family),)


def get_workflow_contradiction_triage_report(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowContradictionTriageReport:
    """Return the contradiction triage report for one workflow family."""

    return build_workflow_contradiction_triage_report(workflow_family)


def list_workflow_evidence_sufficiency_rubrics_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowEvidenceSufficiencyRubric, ...]:
    """Return evidence sufficiency rubrics with optional family filtering."""

    if workflow_family is None:
        return list_workflow_evidence_sufficiency_rubrics()
    return (build_workflow_evidence_sufficiency_rubric(workflow_family),)


def get_workflow_evidence_sufficiency_rubric(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowEvidenceSufficiencyRubric:
    """Return the evidence sufficiency rubric for one workflow family."""

    return build_workflow_evidence_sufficiency_rubric(workflow_family)


def list_workflow_knowledge_deficit_reports_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowKnowledgeDeficitReport, ...]:
    """Return knowledge deficit reports with optional family filtering."""

    if workflow_family is None:
        return list_workflow_knowledge_deficit_reports()
    return (build_workflow_knowledge_deficit_report(workflow_family),)


def get_workflow_knowledge_deficit_report(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowKnowledgeDeficitReport:
    """Return the knowledge deficit report for one workflow family."""

    return build_workflow_knowledge_deficit_report(workflow_family)


def list_workflow_unsupported_claim_ledgers_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowUnsupportedClaimLedger, ...]:
    """Return unsupported-claim ledgers with optional family filtering."""

    if workflow_family is None:
        return list_workflow_unsupported_claim_ledgers()
    return (build_workflow_unsupported_claim_ledger(workflow_family),)


def get_workflow_unsupported_claim_ledger(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowUnsupportedClaimLedger:
    """Return the workflow-family unsupported-claim ledger."""

    return build_workflow_unsupported_claim_ledger(workflow_family)


def list_workflow_literature_freshness_audits_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowLiteratureFreshnessAudit, ...]:
    """Return literature freshness audits with optional family filtering."""

    if workflow_family is None:
        return list_workflow_literature_freshness_audits()
    return (build_workflow_literature_freshness_audit(workflow_family),)


def get_workflow_literature_freshness_audit(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowLiteratureFreshnessAudit:
    """Return the workflow-family literature freshness audit."""

    return build_workflow_literature_freshness_audit(workflow_family)


def list_workflow_bibliography_exports_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowBibliographyExport, ...]:
    """Return bibliography exports with optional family filtering."""

    if workflow_family is None:
        return list_workflow_bibliography_exports()
    return (build_workflow_bibliography_export(workflow_family),)


def get_workflow_bibliography_export(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowBibliographyExport:
    """Return the workflow-family bibliography export."""

    return build_workflow_bibliography_export(workflow_family)


def get_benchmark_literature_gap_matrix() -> BenchmarkLiteratureGapMatrix:
    """Return the cross-family benchmark-versus-literature gap matrix."""

    return build_benchmark_literature_gap_matrix()


def get_comparator_literature_gap_matrix() -> ComparatorLiteratureGapMatrix:
    """Return the cross-family comparator-versus-literature gap matrix."""

    return build_comparator_literature_gap_matrix()


def list_workflow_scientific_reading_packs_lookup(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> tuple[WorkflowScientificReadingPack, ...]:
    """Return scientific reading packs with optional family filtering."""

    if workflow_family is None:
        return list_workflow_scientific_reading_packs()
    return (build_workflow_scientific_reading_pack(workflow_family),)


def get_workflow_scientific_reading_pack(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowScientificReadingPack:
    """Return the scientific reading pack for one workflow family."""

    return build_workflow_scientific_reading_pack(workflow_family)


__all__ = [
    "BenchmarkPackageArtifact",
    "BenchmarkPackageArtifactKind",
    "BenchmarkReproductionStep",
    "BenchmarkComparatorFailureEntry",
    "BenchmarkComparatorFailureReport",
    "BenchmarkLiteratureGapMatrix",
    "ComparatorLiteratureGapMatrix",
    "ComparatorClaimSupportState",
    "ComparatorFailureSeverity",
    "ComparatorPositionEntry",
    "ComparatorPositionKind",
    "ComparatorPositionReport",
    "ComparatorRegressionStatus",
    "WorkflowBibliographyExport",
    "WorkflowClaimCitationTable",
    "build_benchmark_comparator_failure_report",
    "build_benchmark_literature_gap_matrix",
    "build_comparator_position_report",
    "build_comparator_literature_gap_matrix",
    "get_benchmark_comparator_failure",
    "get_benchmark_manifest",
    "get_benchmark_package",
    "get_benchmark_literature_gap_matrix",
    "get_benchmark_registry_entry",
    "get_comparator_position_report",
    "get_comparator_literature_gap_matrix",
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
    "get_workflow_narrative",
    "get_workflow_scientific_reading_pack",
    "get_workflow_unsupported_claim_ledger",
    "list_benchmark_comparator_failures",
    "list_comparator_positions",
    "list_workflow_bibliography_exports_lookup",
    "list_workflow_claim_citation_tables_lookup",
    "list_workflow_comparator_confrontations",
    "list_workflow_comparator_paths",
    "list_workflow_comparator_scorecards",
    "build_workflow_comparator_matrix",
    "list_benchmark_registry_entries",
    "list_benchmark_manifests",
    "list_workflow_contradiction_dossiers_lookup",
    "list_workflow_contradiction_triage_reports_lookup",
    "list_workflow_evidence_sufficiency_rubrics_lookup",
    "list_workflow_knowledge_deficit_reports_lookup",
    "list_workflow_literature_freshness_audits_lookup",
    "list_workflow_literature_matrices_lookup",
    "list_workflow_narratives",
    "list_workflow_scientific_reading_packs_lookup",
    "list_workflow_unsupported_claim_ledgers_lookup",
    "BenchmarkRegistryEntry",
    "BenchmarkRegistryReport",
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
    "WorkflowEvidenceSufficiencyRubric",
    "WorkflowKnowledgeDeficitReport",
    "WorkflowLiteratureFreshnessAudit",
    "WorkflowLiteratureMatrix",
    "WorkflowScientificReadingPack",
    "WorkflowUnsupportedClaimLedger",
]
