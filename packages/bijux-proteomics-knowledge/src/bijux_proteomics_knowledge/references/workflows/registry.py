# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark registry and authority surfaces for scientific release claims."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    BenchmarkCrossCheckStatus,
    BenchmarkEvidenceTier,
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.briefings import (
    build_workflow_reference_briefing,
)


class BenchmarkAuthorityStatus(StrEnum):
    """Authority state for deciding whether a benchmark may back current claims."""

    ACTIVE = "active"
    REVIEW_DUE = "review_due"
    RETIRED = "retired"


class BenchmarkAuthorityAssessment(JsonModel):
    """Authority posture for one benchmark under the current review window."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    evidence_tier: BenchmarkEvidenceTier
    authority_status: BenchmarkAuthorityStatus
    age_days: int = Field(..., ge=0)
    freshness_window_days: int = Field(..., ge=1)
    authorized_claim_scope: tuple[str, ...] = Field(default_factory=tuple)
    blocking_reasons: tuple[str, ...] = Field(default_factory=tuple)
    realism_limits: tuple[str, ...] = Field(default_factory=tuple)
    interpretation_context_lines: tuple[str, ...] = Field(default_factory=tuple)
    decision_grade_definition: str = Field(..., min_length=1)
    decision_grade_criteria: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkRegistryEntry(JsonModel):
    """Public registry entry that states exactly what one benchmark can support."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    evidence_tier: BenchmarkEvidenceTier
    authority_status: BenchmarkAuthorityStatus
    dataset_id: str = Field(..., min_length=1)
    dataset_locator: str = Field(..., min_length=1)
    acquisition_mode: str = Field(..., min_length=1)
    instrument_profiles: tuple[str, ...] = Field(default_factory=tuple)
    sample_complexity: str = Field(..., min_length=1)
    organism: str = Field(..., min_length=1)
    label_strategy: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=1)
    replicate_count: int = Field(..., ge=1)
    cross_check_status: BenchmarkCrossCheckStatus
    benchmark_package_id: str | None = None
    benchmark_package_summary: str | None = None
    comparator_path_ids: tuple[str, ...] = Field(default_factory=tuple)
    supported_repo_claims: tuple[str, ...] = Field(default_factory=tuple)
    authorized_claim_scope: tuple[str, ...] = Field(default_factory=tuple)
    realism_limits: tuple[str, ...] = Field(default_factory=tuple)
    blocking_reasons: tuple[str, ...] = Field(default_factory=tuple)
    interpretation_context_lines: tuple[str, ...] = Field(default_factory=tuple)
    decision_grade_definition: str = Field(..., min_length=1)
    decision_grade_criteria: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkRegistryReport(JsonModel):
    """Full benchmark registry across curated workflow families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[BenchmarkRegistryEntry, ...] = Field(default_factory=tuple)


def _authorized_scope_for_tier(
    evidence_tier: BenchmarkEvidenceTier,
) -> tuple[str, ...]:
    if evidence_tier is BenchmarkEvidenceTier.SMOKE_FIXTURE:
        return (
            "fixture-shaped contract compatibility and parser stability only",
            "no release-facing scientific accuracy or decision-grade authority",
        )
    if evidence_tier is BenchmarkEvidenceTier.CURATED_MINI_STUDY:
        return (
            "bounded workflow semantics and review-packet behavior within the curated fixture scope",
            "no broad cohort, vendor-parity, or decision-grade scientific authority without stronger truth evidence",
        )
    if evidence_tier is BenchmarkEvidenceTier.PUBLIC_TRUTH_SET:
        return (
            "benchmark-backed scientific behavior within the documented dataset and truth surface",
            "release-facing claims remain limited to the named acquisition mode, sample complexity, and transfer boundaries",
        )
    return (
        "externally reproduced scientific behavior within the documented reproduction package",
        "release-facing claims remain limited to the named comparator and transfer boundaries",
    )


def assess_benchmark_authority(
    manifest: BenchmarkManifest,
    *,
    reviewed_on: date | None = None,
    triggered_retirement_conditions: tuple[str, ...] = (),
) -> BenchmarkAuthorityAssessment:
    """Assess whether a benchmark may still back scientific release claims."""

    today = reviewed_on or date.today()
    briefing = build_workflow_reference_briefing(manifest.workflow_family)
    age_days = max(0, (today - manifest.last_reviewed_on).days)
    blocking_reasons: list[str] = []
    authority_status = BenchmarkAuthorityStatus.ACTIVE
    if age_days > manifest.freshness_window_days:
        authority_status = BenchmarkAuthorityStatus.REVIEW_DUE
        blocking_reasons.append(
            "benchmark review window expired and the dataset must be re-verified"
        )
    if age_days > (manifest.freshness_window_days * 2):
        authority_status = BenchmarkAuthorityStatus.RETIRED
        blocking_reasons.append(
            "benchmark remained stale beyond two review windows and can no longer authorize current claims"
        )
    if triggered_retirement_conditions:
        authority_status = BenchmarkAuthorityStatus.RETIRED
        blocking_reasons.extend(
            condition.strip()
            for condition in triggered_retirement_conditions
            if condition.strip()
        )
    return BenchmarkAuthorityAssessment(
        benchmark_id=manifest.benchmark_id,
        workflow_family=manifest.workflow_family,
        evidence_tier=manifest.evidence_tier,
        authority_status=authority_status,
        age_days=age_days,
        freshness_window_days=manifest.freshness_window_days,
        authorized_claim_scope=_authorized_scope_for_tier(manifest.evidence_tier),
        blocking_reasons=tuple(dict.fromkeys(blocking_reasons)),
        realism_limits=manifest.fixture_realism_limits,
        interpretation_context_lines=briefing.interpretation_context_lines,
        decision_grade_definition=(
            briefing.decision_grade_framework.decision_grade_definition
        ),
        decision_grade_criteria=tuple(
            criterion.summary
            for criterion in briefing.decision_grade_framework.criteria
        ),
    )


def build_benchmark_registry_entry(
    manifest: BenchmarkManifest,
    *,
    reviewed_on: date | None = None,
) -> BenchmarkRegistryEntry:
    """Build one public registry entry from a curated benchmark manifest."""

    authority = assess_benchmark_authority(manifest, reviewed_on=reviewed_on)
    return BenchmarkRegistryEntry(
        benchmark_id=manifest.benchmark_id,
        title=manifest.title,
        workflow_family=manifest.workflow_family,
        evidence_tier=manifest.evidence_tier,
        authority_status=authority.authority_status,
        dataset_id=manifest.dataset_id,
        dataset_locator=manifest.dataset_locator,
        acquisition_mode=manifest.acquisition_mode,
        instrument_profiles=manifest.instrument_profiles,
        sample_complexity=manifest.sample_complexity,
        organism=manifest.organism,
        label_strategy=manifest.label_strategy,
        sample_count=manifest.sample_count,
        replicate_count=manifest.replicate_count,
        cross_check_status=manifest.cross_check_status,
        benchmark_package_id=(
            manifest.benchmark_package.package_id
            if manifest.benchmark_package is not None
            else None
        ),
        benchmark_package_summary=(
            manifest.benchmark_package.package_summary
            if manifest.benchmark_package is not None
            else None
        ),
        comparator_path_ids=manifest.comparator_path_ids,
        supported_repo_claims=manifest.supported_repo_claims,
        authorized_claim_scope=authority.authorized_claim_scope,
        realism_limits=authority.realism_limits,
        blocking_reasons=authority.blocking_reasons,
        interpretation_context_lines=authority.interpretation_context_lines,
        decision_grade_definition=authority.decision_grade_definition,
        decision_grade_criteria=authority.decision_grade_criteria,
    )


def build_benchmark_registry(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
    reviewed_on: date | None = None,
) -> BenchmarkRegistryReport:
    """Build the public benchmark registry across curated workflow families."""

    manifests = (
        DEFAULT_BENCHMARK_MANIFESTS
        if workflow_family is None
        else tuple(
            manifest
            for manifest in DEFAULT_BENCHMARK_MANIFESTS
            if manifest.workflow_family is workflow_family
        )
    )
    entries = tuple(
        build_benchmark_registry_entry(manifest, reviewed_on=reviewed_on)
        for manifest in manifests
    )
    return BenchmarkRegistryReport(entries=entries)


__all__ = [
    "BenchmarkAuthorityAssessment",
    "BenchmarkAuthorityStatus",
    "BenchmarkRegistryEntry",
    "BenchmarkRegistryReport",
    "assess_benchmark_authority",
    "build_benchmark_registry",
    "build_benchmark_registry_entry",
]
