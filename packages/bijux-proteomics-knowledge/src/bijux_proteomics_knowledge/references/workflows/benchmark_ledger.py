# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark evidence ledger for reviewable scientific workflow claims."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    BenchmarkCrossCheckStatus,
    BenchmarkEvidenceTier,
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)


class WorkflowBenchmarkLedgerEntry(JsonModel):
    """One benchmark entry with the provenance and trust boundaries reviewers need."""

    model_config = ConfigDict(extra="forbid")

    ledger_entry_id: str = Field(..., min_length=1)
    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    title: str = Field(..., min_length=1)
    evidence_tier: BenchmarkEvidenceTier
    dataset_id: str = Field(..., min_length=1)
    dataset_locator: str = Field(..., min_length=1)
    cross_check_status: BenchmarkCrossCheckStatus
    scientific_focus: str = Field(..., min_length=1)
    truth_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    truth_assumptions: tuple[str, ...] = Field(default_factory=tuple)
    provenance_trace: tuple[str, ...] = Field(default_factory=tuple)
    caveat_lines: tuple[str, ...] = Field(default_factory=tuple)
    consumer_facing_limits: tuple[str, ...] = Field(default_factory=tuple)
    supported_repo_claims: tuple[str, ...] = Field(default_factory=tuple)
    primary_citation_ids: tuple[str, ...] = Field(default_factory=tuple)
    corpus_ids: tuple[str, ...] = Field(default_factory=tuple)


class WorkflowBenchmarkLedger(JsonModel):
    """Benchmark ledger across curated workflow families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[WorkflowBenchmarkLedgerEntry, ...] = Field(default_factory=tuple)


def build_workflow_benchmark_ledger_entry(
    manifest: BenchmarkManifest,
) -> WorkflowBenchmarkLedgerEntry:
    """Build one evidence ledger entry from a benchmark manifest."""

    return WorkflowBenchmarkLedgerEntry(
        ledger_entry_id=f"benchmark_ledger:{manifest.workflow_family.value}",
        benchmark_id=manifest.benchmark_id,
        workflow_family=manifest.workflow_family,
        title=manifest.title,
        evidence_tier=manifest.evidence_tier,
        dataset_id=manifest.dataset_id,
        dataset_locator=manifest.dataset_locator,
        cross_check_status=manifest.cross_check_status,
        scientific_focus=manifest.scientific_focus,
        truth_surfaces=manifest.truth_surfaces,
        truth_assumptions=manifest.reproduction_requirements,
        provenance_trace=(
            *manifest.version_trace,
            *manifest.retrieval_trace,
            manifest.dataset_license_and_reuse_note,
        ),
        caveat_lines=(
            *manifest.comparison_notes,
            *manifest.exclusion_notes,
            *manifest.weakness_notes,
            *manifest.failure_mode_notes,
        ),
        consumer_facing_limits=(
            *manifest.fixture_realism_limits,
            *manifest.expected_failure_conditions,
            *manifest.non_transfer_zones,
        ),
        supported_repo_claims=manifest.supported_repo_claims,
        primary_citation_ids=manifest.primary_citation_ids,
        corpus_ids=manifest.corpus_ids,
    )


def build_workflow_benchmark_ledger(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> WorkflowBenchmarkLedger:
    """Build the benchmark evidence ledger across curated workflow families."""

    manifests = (
        DEFAULT_BENCHMARK_MANIFESTS
        if workflow_family is None
        else tuple(
            manifest
            for manifest in DEFAULT_BENCHMARK_MANIFESTS
            if manifest.workflow_family is workflow_family
        )
    )
    return WorkflowBenchmarkLedger(
        entries=tuple(
            build_workflow_benchmark_ledger_entry(manifest) for manifest in manifests
        )
    )
