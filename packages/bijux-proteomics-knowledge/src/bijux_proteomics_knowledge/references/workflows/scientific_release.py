# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific release packets that outsiders can inspect without generosity."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkEvidenceTier,
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.scientific_risk import (
    RecommendationFailureTrapReport,
    WorkflowScientificErrorBudget,
    build_recommendation_failure_trap_report,
    build_workflow_scientific_error_budget,
)
from bijux_proteomics_knowledge.references.workflows.scientific_thresholds import (
    DecisionOutcomeAuditReport,
    WorkflowThresholdEvidenceReport,
    build_decision_outcome_audit_report,
    build_workflow_threshold_evidence_report,
)


class ScientificMetricPriorityCategory(StrEnum):
    """Priority categories for benchmark artifacts."""

    SCIENTIFIC_ACCURACY = "scientific_accuracy"
    CALIBRATION = "calibration"
    TRUST = "trust"
    THROUGHPUT = "throughput"
    LATENCY = "latency"


class HostileReviewerCheckItem(JsonModel):
    """One outsider-facing question that release claims must answer."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)


class HostileReviewerChecklist(JsonModel):
    """Package-agnostic checklist for adversarial domain review."""

    model_config = ConfigDict(extra="forbid")

    items: tuple[HostileReviewerCheckItem, ...] = Field(default_factory=tuple)
    ready_for_hostile_review: bool


class PackageScienceTable(JsonModel):
    """Machine-readable supported, bounded, and future science table for one package."""

    model_config = ConfigDict(extra="forbid")

    package_name: str = Field(..., min_length=1)
    supported_science: tuple[str, ...] = Field(default_factory=tuple)
    bounded_science: tuple[str, ...] = Field(default_factory=tuple)
    future_science: tuple[str, ...] = Field(default_factory=tuple)


class RepositoryScienceTableReport(JsonModel):
    """Machine-readable science tables across the proteomics packages."""

    model_config = ConfigDict(extra="forbid")

    tables: tuple[PackageScienceTable, ...] = Field(default_factory=tuple)


class BenchmarkMetricPriorityEntry(JsonModel):
    """One priority weight for benchmark artifact consumers."""

    model_config = ConfigDict(extra="forbid")

    category: ScientificMetricPriorityCategory
    weight: int = Field(..., ge=1)
    rationale: str = Field(..., min_length=1)


class BenchmarkMetricPriorityLedger(JsonModel):
    """Scientific metric priorities that outweigh convenience metrics."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    entries: tuple[BenchmarkMetricPriorityEntry, ...] = Field(default_factory=tuple)


class FlagshipReproducibilityPack(JsonModel):
    """Third-party-facing reproducibility pack for one flagship workflow path."""

    model_config = ConfigDict(extra="forbid")

    pack_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    reviewer_entrypoints: tuple[str, ...] = Field(default_factory=tuple)
    third_party_review_steps: tuple[str, ...] = Field(default_factory=tuple)


class ScientificGraduationState(StrEnum):
    """Whether the repository can be presented as a real proteomics product."""

    BLOCKED = "blocked"
    PROMISING_INFRASTRUCTURE = "promising_infrastructure"
    OUTSIDER_TRUST_READY = "outsider_trust_ready"


class ScientificReleasePacket(JsonModel):
    """Combined scientific release packet for one workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    threshold_evidence: WorkflowThresholdEvidenceReport
    decision_outcome_audit: DecisionOutcomeAuditReport
    failure_trap_report: RecommendationFailureTrapReport
    scientific_error_budget: WorkflowScientificErrorBudget
    hostile_reviewer_checklist: HostileReviewerChecklist
    science_tables: RepositoryScienceTableReport
    benchmark_metric_priorities: BenchmarkMetricPriorityLedger
    flagship_reproducibility_pack: FlagshipReproducibilityPack
    evidence_quality_gate_passed: bool
    graduation_state: ScientificGraduationState
    note: str = Field(..., min_length=1)


def build_hostile_reviewer_checklist(
    manifest: BenchmarkManifest,
    *,
    evidence_quality_gate_passed: bool,
) -> HostileReviewerChecklist:
    """Build the package-agnostic hostile-review checklist."""

    items = (
        HostileReviewerCheckItem(
            question="Can we show what this workflow actually proves without hiding transfer limits?",
            status="yes",
            evidence_refs=(manifest.benchmark_id, *manifest.non_transfer_zones[:1]),
        ),
        HostileReviewerCheckItem(
            question="Are the main thresholds defended by benchmark or citation anchors rather than convenience defaults?",
            status="yes",
            evidence_refs=(manifest.benchmark_id, *manifest.primary_citation_ids[:1]),
        ),
        HostileReviewerCheckItem(
            question="Would an external reviewer see why a strong claim is still blocked?",
            status="yes" if not evidence_quality_gate_passed else "partially",
            evidence_refs=(*manifest.expected_failure_conditions[:1],),
        ),
    )
    return HostileReviewerChecklist(
        items=items,
        ready_for_hostile_review=evidence_quality_gate_passed,
    )


def build_repository_science_table_report() -> RepositoryScienceTableReport:
    """Publish supported, bounded, and future science tables for each package."""

    return RepositoryScienceTableReport(
        tables=(
            PackageScienceTable(
                package_name="agentic-proteins",
                supported_science=("compatibility routing and owned-wrapper disclosure",),
                bounded_science=("not a scientific authority package",),
                future_science=("continued compatibility retirement",),
            ),
            PackageScienceTable(
                package_name="bijux-proteomics-core",
                supported_science=("typed scientific kernels for identification, quantification, PTM, DIA, sequences, and QC",),
                bounded_science=("broad vendor parity and universal workflow authority remain bounded by benchmark scope",),
                future_science=("stronger cross-engine and sample-realism proof",),
            ),
            PackageScienceTable(
                package_name="bijux-proteomics-foundation",
                supported_science=("hashing, serialization, support-state, and contract mechanics",),
                bounded_science=("no direct scientific interpretation authority",),
                future_science=("release-kernel support for scientific trust packets",),
            ),
            PackageScienceTable(
                package_name="bijux-proteomics-intelligence",
                supported_science=("benchmark-backed release reviews and bounded recommendation logic",),
                bounded_science=("ranking and interpretation remain blocked from overclaiming beyond benchmark and literature support",),
                future_science=("decision-outcome learning under stronger real workflow proof",),
            ),
            PackageScienceTable(
                package_name="bijux-proteomics-knowledge",
                supported_science=("workflow references, provenance, disagreement, and scientific release packets",),
                bounded_science=("knowledge replay and literature breadth remain bounded by current curated corpora",),
                future_science=("richer replay and corpus freshness proof",),
            ),
            PackageScienceTable(
                package_name="bijux-proteomics-lab",
                supported_science=("operational planning and reconciliation boundaries",),
                bounded_science=("lab readiness is still constrained by current benchmark and workflow proof",),
                future_science=("stronger observed-outcome and operator-trust closure",),
            ),
            PackageScienceTable(
                package_name="bijux-proteomics-runtime",
                supported_science=("workflow planning, reproducibility, and execution-artifact contracts",),
                bounded_science=("real-tool execution parity remains narrower than the typed runtime surface",),
                future_science=("harder execution proof and reproducibility packs",),
            ),
            PackageScienceTable(
                package_name="bijux-proteomics-dev",
                supported_science=("governance, reports, and contract validation",),
                bounded_science=("does not create scientific authority by itself",),
                future_science=("freshness and integrity gating for generated governance reports",),
            ),
        )
    )


def build_benchmark_metric_priority_ledger(
    manifest: BenchmarkManifest,
) -> BenchmarkMetricPriorityLedger:
    """Make scientific trust metrics outrank convenience metrics."""

    return BenchmarkMetricPriorityLedger(
        workflow_family=manifest.workflow_family,
        entries=(
            BenchmarkMetricPriorityEntry(
                category=ScientificMetricPriorityCategory.SCIENTIFIC_ACCURACY,
                weight=5,
                rationale="Scientific accuracy is the first release question because a fast wrong answer is still wrong.",
            ),
            BenchmarkMetricPriorityEntry(
                category=ScientificMetricPriorityCategory.CALIBRATION,
                weight=5,
                rationale="Calibration stability keeps confidence and threshold behavior scientifically interpretable.",
            ),
            BenchmarkMetricPriorityEntry(
                category=ScientificMetricPriorityCategory.TRUST,
                weight=5,
                rationale="Trust metrics decide whether the benchmark can defend an external scientific claim.",
            ),
            BenchmarkMetricPriorityEntry(
                category=ScientificMetricPriorityCategory.THROUGHPUT,
                weight=2,
                rationale="Throughput matters only after trust and scientific accuracy remain explicit.",
            ),
            BenchmarkMetricPriorityEntry(
                category=ScientificMetricPriorityCategory.LATENCY,
                weight=1,
                rationale="Latency is useful but never substitutes for scientific reliability.",
            ),
        ),
    )


def build_flagship_reproducibility_pack(
    manifest: BenchmarkManifest,
) -> FlagshipReproducibilityPack:
    """Build a third-party-oriented reproducibility pack for one workflow family."""

    artifact_ids = tuple(
        artifact.artifact_id
        for artifact in manifest.benchmark_package.package_artifacts
    ) if manifest.benchmark_package is not None else ()
    return FlagshipReproducibilityPack(
        pack_id=f"{manifest.benchmark_id}:flagship_reproducibility_pack",
        workflow_family=manifest.workflow_family,
        artifact_ids=artifact_ids,
        reviewer_entrypoints=(
            manifest.dataset_locator,
            *(artifact.repo_relative_path for artifact in manifest.benchmark_package.package_artifacts[:2]),
        ) if manifest.benchmark_package is not None else (manifest.dataset_locator,),
        third_party_review_steps=(
            "Inspect the benchmark manifest and supported claim scope before reading summary language.",
            "Open the governed artifact set and compare the named realism limits against the current claim.",
            "Check the decision-grade criteria and hostile-review checklist before treating the workflow as product-grade science.",
        ),
    )


def build_scientific_release_packet(
    manifest: BenchmarkManifest,
) -> ScientificReleasePacket:
    """Build one scientific release packet that blocks premature graduation."""

    threshold_evidence = build_workflow_threshold_evidence_report(manifest)
    decision_outcome_audit = build_decision_outcome_audit_report(manifest)
    failure_trap_report = build_recommendation_failure_trap_report(manifest)
    scientific_error_budget = build_workflow_scientific_error_budget(manifest)
    metric_priorities = build_benchmark_metric_priority_ledger(manifest)
    evidence_quality_gate_passed = (
        manifest.evidence_tier
        in {
            BenchmarkEvidenceTier.PUBLIC_TRUTH_SET,
            BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE,
        }
        and manifest.cross_check_status.value != "internal_only"
        and decision_outcome_audit.trustworthy_decision_ratio >= 0.75
    )
    hostile_checklist = build_hostile_reviewer_checklist(
        manifest,
        evidence_quality_gate_passed=evidence_quality_gate_passed,
    )
    reproducibility_pack = build_flagship_reproducibility_pack(manifest)
    science_tables = build_repository_science_table_report()
    graduation_state = (
        ScientificGraduationState.OUTSIDER_TRUST_READY
        if evidence_quality_gate_passed and hostile_checklist.ready_for_hostile_review
        else ScientificGraduationState.BLOCKED
        if manifest.evidence_tier is BenchmarkEvidenceTier.CURATED_MINI_STUDY
        else ScientificGraduationState.PROMISING_INFRASTRUCTURE
    )
    return ScientificReleasePacket(
        workflow_family=manifest.workflow_family,
        threshold_evidence=threshold_evidence,
        decision_outcome_audit=decision_outcome_audit,
        failure_trap_report=failure_trap_report,
        scientific_error_budget=scientific_error_budget,
        hostile_reviewer_checklist=hostile_checklist,
        science_tables=science_tables,
        benchmark_metric_priorities=metric_priorities,
        flagship_reproducibility_pack=reproducibility_pack,
        evidence_quality_gate_passed=evidence_quality_gate_passed,
        graduation_state=graduation_state,
        note=(
            "Scientific release readiness remains blocked until evidence quality, adversarial review posture, and outsider-readable reproducibility artifacts are strong enough."
            if graduation_state is not ScientificGraduationState.OUTSIDER_TRUST_READY
            else "Scientific release packet clears the current outsider-trust gate."
        ),
    )


__all__ = [
    "BenchmarkMetricPriorityEntry",
    "BenchmarkMetricPriorityLedger",
    "FlagshipReproducibilityPack",
    "HostileReviewerChecklist",
    "HostileReviewerCheckItem",
    "PackageScienceTable",
    "RepositoryScienceTableReport",
    "ScientificGraduationState",
    "ScientificMetricPriorityCategory",
    "ScientificReleasePacket",
    "build_benchmark_metric_priority_ledger",
    "build_flagship_reproducibility_pack",
    "build_hostile_reviewer_checklist",
    "build_repository_science_table_report",
    "build_scientific_release_packet",
]
