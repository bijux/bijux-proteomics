# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared helpers for workflow-family benchmark reviews."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.dia.benchmarks import WorkflowScientificSupportTier
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.identification.search_adapters import SearchAdapterKind
from bijux_proteomics.lab.qc_benchmarks import build_workflow_minimum_control_report
from bijux_proteomics.review.collaboration import (
    ExternalReviewerBundle,
    ExternalReviewerBundleInput,
    build_external_reviewer_bundle,
)
from bijux_proteomics_foundation.support.states import SupportState
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    BenchmarkPackageArtifactKind,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.briefings import (
    build_workflow_reference_briefing,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
    build_benchmark_comparator_failure_report,
)
from bijux_proteomics_knowledge.references.workflows.comparators import (
    build_workflow_comparator_matrix,
)
from bijux_proteomics_knowledge.references.workflows.lookups import (
    get_benchmark_manifest,
    get_benchmark_package,
    get_benchmark_registry_entry,
)
from bijux_proteomics_knowledge.references.workflows.registry import (
    BenchmarkRegistryEntry,
)

from .models import (
    BenchmarkComparatorPosition,
    ReviewerGroundingState,
    WorkflowVendorCaveatEntry,
    WorkflowVendorCaveatLedger,
)


def repo_root() -> Path:
    """Resolve the repository root for checked-in benchmark assets."""

    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for benchmark reviews")


def require_manifest(benchmark_id: str) -> BenchmarkManifest:
    """Load one benchmark manifest or fail with a precise message."""

    manifest = get_benchmark_manifest(benchmark_id)
    if manifest is None:
        raise ValueError(f"unknown benchmark manifest: {benchmark_id}")
    return manifest


def require_registry_entry(benchmark_id: str) -> BenchmarkRegistryEntry:
    """Load one benchmark registry entry or fail with a precise message."""

    entry = get_benchmark_registry_entry(benchmark_id)
    if entry is None:
        raise ValueError(f"unknown benchmark registry entry: {benchmark_id}")
    return entry


def benchmark_package_artifact_ids(benchmark_id: str) -> tuple[str, ...]:
    """Return the checked-in artifact ids for one benchmark package."""

    package = get_benchmark_package(benchmark_id)
    if package is None:
        return ()
    return tuple(artifact.artifact_id for artifact in package.package_artifacts)


def build_comparator_positions(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[BenchmarkComparatorPosition, ...]:
    """Project comparator status into release-review posture entries."""

    matrix = build_workflow_comparator_matrix(workflow_family=workflow_family)
    if not matrix.entries:
        return ()
    return tuple(
        BenchmarkComparatorPosition(
            comparator_tool=status.comparator_tool,
            comparator_path_ids=status.comparator_path_ids,
            matched_behaviors=status.matched_behaviors,
            partial_behaviors=status.partial_behaviors,
            refused_behaviors=status.refused_behaviors,
            not_attempted_behaviors=status.not_attempted_behaviors,
        )
        for status in matrix.entries[0].tool_statuses
    )


def build_public_claim_posture(
    benchmark_id: str,
) -> tuple[
    ComparatorClaimSupportState,
    tuple[str, ...],
    tuple[str, ...],
    bool,
]:
    """Summarize public-claim support posture from comparator failures."""

    failure_report = build_benchmark_comparator_failure_report(
        benchmark_id=benchmark_id
    )
    if not failure_report.entries:
        return (ComparatorClaimSupportState.SUPPORTED, (), (), False)
    if any(
        entry.public_claim_support_state is ComparatorClaimSupportState.REFUSED
        for entry in failure_report.entries
    ):
        claim_state = ComparatorClaimSupportState.REFUSED
    else:
        claim_state = ComparatorClaimSupportState.ADVISORY
    summaries = tuple(entry.failure_summary for entry in failure_report.entries)
    improvement_targets = tuple(
        dict.fromkeys(entry.improvement_target for entry in failure_report.entries)
    )
    known_loss = any(
        entry.known_loss_to_established_tool for entry in failure_report.entries
    )
    return (claim_state, summaries, improvement_targets, known_loss)


def build_external_bundle(
    *,
    bundle_id: str,
    workflow_family: KnowledgeWorkflowFamily,
    artifact_ids: tuple[str, ...],
    summary_lines: tuple[str, ...],
    scientific_limits: tuple[str, ...],
    hash_entries: tuple[str, ...],
) -> ExternalReviewerBundle:
    """Build an external-review packet from benchmark-backed summary elements."""

    return build_external_reviewer_bundle(
        ExternalReviewerBundleInput(
            bundle_id=bundle_id,
            schema_refs=(
                "schema.benchmark_manifest.v1",
                f"schema.{workflow_family.value}.review.v1",
            ),
            evidence_pointer_ids=artifact_ids,
            summary_lines=summary_lines,
            hash_ledger_entries=hash_entries,
            reviewer_instructions=(
                "Review owner surfaces, benchmark evidence pointers, and explicit "
                "scientific limits before treating this workflow as release-ready."
            ),
        )
    )


def build_vendor_caveat_ledger(
    entries: tuple[WorkflowVendorCaveatEntry, ...],
) -> WorkflowVendorCaveatLedger:
    """Build a vendor caveat ledger with the derived support state."""

    vendor_support_state = (
        SupportState.SUPPORTED if not entries else SupportState.ADVISORY
    )
    return WorkflowVendorCaveatLedger(
        entries=entries,
        vendor_support_state=vendor_support_state,
    )


def workflow_minimum_controls(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[str, ...]:
    """Return the governed minimum controls for one workflow family."""

    report = build_workflow_minimum_control_report()
    entry = next(
        item for item in report.entries if item.workflow_family == workflow_family.value
    )
    return entry.minimum_controls


def infer_search_adapter_kind(source_path: Path) -> SearchAdapterKind:
    """Infer the adapter kind for one checked-in benchmark result artifact."""

    artifact_name = source_path.name.lower()
    if "msfragger" in artifact_name:
        return SearchAdapterKind.MSFRAGGER
    if "maxquant" in artifact_name:
        return SearchAdapterKind.MAXQUANT_EVIDENCE
    if "spectronaut" in artifact_name:
        return SearchAdapterKind.SPECTRONAUT
    raise ValueError(f"cannot infer search adapter kind from {source_path.name!r}")


def infer_search_adapter_dialect_id(source_path: Path) -> str | None:
    """Infer the checked-in result dialect when one benchmark path needs it."""

    artifact_name = source_path.name.lower()
    if "pipeline_export" in artifact_name:
        return "pipeline-export"
    return None


def build_dia_sample_resolved_support_counts(
    *,
    psm_records: tuple[PsmRecord, ...],
    protein_group_count: int,
) -> tuple[int, int, int, int]:
    """Build sample-resolved DIA counts from normalized evidence when run ids exist."""

    if not psm_records or not all(record.run_id for record in psm_records):
        return (
            len(psm_records),
            len(psm_records),
            protein_group_count,
            protein_group_count,
        )

    sample_resolved_precursor_count = len(
        {
            (record.run_id, record.canonical_peptide, record.charge)
            for record in psm_records
        }
    )
    sample_resolved_protein_count = len(
        {
            (record.run_id, protein_ref)
            for record in psm_records
            for protein_ref in record.protein_refs
        }
    )
    return (
        sample_resolved_precursor_count,
        sample_resolved_precursor_count,
        sample_resolved_protein_count,
        sample_resolved_protein_count,
    )


def resolve_primary_pipeline_export(manifest: BenchmarkManifest) -> Path:
    """Resolve the primary checked-in external export for one benchmark package."""

    package = manifest.benchmark_package
    if package is None:
        return repo_root() / manifest.dataset_locator
    primary_artifact = next(
        (
            artifact
            for artifact in package.package_artifacts
            if artifact.artifact_id.endswith("maxquant_export")
            and artifact.artifact_kind
            is BenchmarkPackageArtifactKind.EXTERNAL_PIPELINE_EXPORT
        ),
        None,
    )
    if primary_artifact is None:
        primary_artifact = next(
            (
                artifact
                for artifact in package.package_artifacts
                if artifact.artifact_kind
                is BenchmarkPackageArtifactKind.EXTERNAL_PIPELINE_EXPORT
            ),
            None,
        )
    if primary_artifact is None:
        return repo_root() / manifest.dataset_locator
    return repo_root() / primary_artifact.repo_relative_path


def resolve_package_artifact_path(
    manifest: BenchmarkManifest,
    *artifact_kinds: BenchmarkPackageArtifactKind,
) -> Path:
    """Resolve the first tracked benchmark package artifact for one kind set."""

    package = manifest.benchmark_package
    if package is None:
        return repo_root() / manifest.dataset_locator
    artifact = next(
        (
            item
            for item in package.package_artifacts
            if item.artifact_kind in artifact_kinds
        ),
        None,
    )
    if artifact is None:
        return repo_root() / manifest.dataset_locator
    return repo_root() / artifact.repo_relative_path


def build_grounding_payload(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    benchmark_manifest: BenchmarkManifest,
    public_claim_support_state: ComparatorClaimSupportState,
) -> tuple[
    ReviewerGroundingState,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    """Build the shared reviewer grounding payload for one family review."""

    briefing = build_workflow_reference_briefing(workflow_family)
    criteria = tuple(
        criterion.summary for criterion in briefing.decision_grade_framework.criteria
    )
    limits = tuple(
        dict.fromkeys(
            (
                *briefing.scope_limit_notes[:2],
                briefing.decision_grade_framework.decision_grade_definition,
            )
        )
    )
    if (
        public_claim_support_state is ComparatorClaimSupportState.SUPPORTED
        and benchmark_manifest.evidence_tier.value
        in {"public_truth_set", "external_reproduction_package"}
    ):
        grounding_state = ReviewerGroundingState.DECISION_GRADE
    elif public_claim_support_state is ComparatorClaimSupportState.REFUSED:
        grounding_state = ReviewerGroundingState.THIN
    else:
        grounding_state = ReviewerGroundingState.REVIEW_GRADE
    return (
        grounding_state,
        limits,
        briefing.interpretation_context_lines,
        criteria,
    )


def grounding_summary_phrase(grounding_state: ReviewerGroundingState) -> str:
    """Return the durable summary phrase for one grounding posture."""

    if grounding_state is ReviewerGroundingState.DECISION_GRADE:
        return "biological grounding is strong enough to defend decision-grade review scope."
    if grounding_state is ReviewerGroundingState.REVIEW_GRADE:
        return "biological grounding stays review-grade and explicitly bounded by benchmark and literature scope."
    return "biological grounding remains thin and cannot be hidden behind tidy benchmark prose."


def dia_claim_support_state(
    support_tier: WorkflowScientificSupportTier,
) -> SupportState:
    """Translate DIA scientific support tiers into release-review support states."""

    return (
        SupportState.SUPPORTED
        if support_tier is WorkflowScientificSupportTier.SUPPORTED
        else SupportState.ADVISORY
    )
