# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific failure traps and error budgets for workflow release claims."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)


class RecommendationFailureTrapEntry(JsonModel):
    """One intentionally bad recommendation that the system must catch."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    injected_failure_mode: str = Field(..., min_length=1)
    expected_guard: str = Field(..., min_length=1)
    failure_if_missed: str = Field(..., min_length=1)


class RecommendationFailureTrapReport(JsonModel):
    """Failure-trap suite for recommendation downgrade or refusal behavior."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    entries: tuple[RecommendationFailureTrapEntry, ...] = Field(default_factory=tuple)


class WorkflowScientificErrorBudget(JsonModel):
    """Workflow-specific scientific error budget with release blockers."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    acceptable_errors: tuple[str, ...] = Field(default_factory=tuple)
    release_blocking_errors: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_recommendation_failure_trap_report(
    manifest: BenchmarkManifest,
) -> RecommendationFailureTrapReport:
    """State which intentionally wrong recommendations must be caught."""

    entries_by_family: dict[
        KnowledgeWorkflowFamily, tuple[RecommendationFailureTrapEntry, ...]
    ] = {
        KnowledgeWorkflowFamily.DDA: (
            RecommendationFailureTrapEntry(
                scenario_id="dda_decoy_hidden",
                injected_failure_mode="decoy evidence disappears while confidence language remains strong",
                expected_guard="downgrade target-decoy semantics and block stronger interpretation",
                failure_if_missed="review-ready evidence would falsely sound protein-certain",
            ),
        ),
        KnowledgeWorkflowFamily.DIA: (
            RecommendationFailureTrapEntry(
                scenario_id="dia_library_gap_promoted",
                injected_failure_mode="low library coverage is treated as strong biological support",
                expected_guard="biological interpretation tier stays advisory or refused",
                failure_if_missed="benchmark would overclaim cohort-transferable DIA biology",
            ),
        ),
        KnowledgeWorkflowFamily.PTM: (
            RecommendationFailureTrapEntry(
                scenario_id="ptm_ambiguity_mechanism_jump",
                injected_failure_mode="ambiguous localization is promoted into motif or pathway certainty",
                expected_guard="site ambiguity and family-track limits trigger downgrade",
                failure_if_missed="PTM review would convert ambiguous evidence into mechanistic language",
            ),
        ),
        KnowledgeWorkflowFamily.LFQ: (
            RecommendationFailureTrapEntry(
                scenario_id="lfq_batch_shift_ignored",
                injected_failure_mode="batch shift is ignored while abundance ranking stays attractive",
                expected_guard="decision-grade boundary blocks stronger quantitative conclusion",
                failure_if_missed="quant review would mistake implementation stability for biological robustness",
            ),
        ),
        KnowledgeWorkflowFamily.MULTIPLEX: (
            RecommendationFailureTrapEntry(
                scenario_id="multiplex_reference_dropout_ignored",
                injected_failure_mode="reference-channel dropout is treated as cosmetic",
                expected_guard="channel-balance and chemistry caveats keep the review advisory",
                failure_if_missed="multiplex comparison would look biologically stronger than the chemistry allows",
            ),
        ),
        KnowledgeWorkflowFamily.TARGETED: (
            RecommendationFailureTrapEntry(
                scenario_id="targeted_inflated_handoff",
                injected_failure_mode="transition handoff sounds execution-ready despite calibration or control gaps",
                expected_guard="raw-to-reviewed bundle and minimum-control policy block promotion",
                failure_if_missed="follow-up spend would be authorized on review-grade assay evidence",
            ),
            RecommendationFailureTrapEntry(
                scenario_id="targeted_carryover_laundered",
                injected_failure_mode="carryover is reduced to a warning instead of a follow-up blocker",
                expected_guard="carryover benchmark and reconciliation posture prevent clean readiness claims",
                failure_if_missed="contaminated targeted follow-up would be framed as trustworthy biology",
            ),
        ),
    }
    return RecommendationFailureTrapReport(
        workflow_family=manifest.workflow_family,
        entries=entries_by_family[manifest.workflow_family],
    )


def build_workflow_scientific_error_budget(
    manifest: BenchmarkManifest,
) -> WorkflowScientificErrorBudget:
    """Define acceptable and release-blocking scientific errors per workflow."""

    workflow_family = manifest.workflow_family
    acceptable_errors: dict[KnowledgeWorkflowFamily, tuple[str, ...]] = {
        KnowledgeWorkflowFamily.DDA: (
            "bounded review-only loss of engine-native columns when loss accounting remains explicit",
        ),
        KnowledgeWorkflowFamily.DIA: (
            "review-grade support under explicit library or ion-mobility limits without stronger biological promotion",
        ),
        KnowledgeWorkflowFamily.PTM: (
            "interpretive-only PTM family coverage when unsupported families remain explicitly refused",
        ),
        KnowledgeWorkflowFamily.LFQ: (
            "review-grade abundance summaries under explicit batch and missingness caveats",
        ),
        KnowledgeWorkflowFamily.MULTIPLEX: (
            "review-grade reporter summaries when chemistry caveats remain visible",
        ),
        KnowledgeWorkflowFamily.TARGETED: (
            "operator-facing targeted QC guidance when vendor parity stays explicitly out of scope",
        ),
    }
    blocking_errors: dict[KnowledgeWorkflowFamily, tuple[str, ...]] = {
        KnowledgeWorkflowFamily.DDA: (
            "hidden loss of target-decoy semantics",
            "protein-level confidence that survives neither adapter-loss nor contaminant pressure",
        ),
        KnowledgeWorkflowFamily.DIA: (
            "strong biological interpretation under weak library coverage or absent expected peptide pressure",
            "vendor-facing parity claims without external execution evidence",
        ),
        KnowledgeWorkflowFamily.PTM: (
            "mechanistic PTM language under unresolved localization ambiguity",
            "family-wide release claims for unsupported PTM families",
        ),
        KnowledgeWorkflowFamily.LFQ: (
            "decision-grade abundance language under unstable replicates or unresolved batch shift",
            "threshold defaults presented as evidence-backed when they are convenience-only",
        ),
        KnowledgeWorkflowFamily.MULTIPLEX: (
            "biological comparisons that ignore reference-channel failure or ratio-compression risk",
        ),
        KnowledgeWorkflowFamily.TARGETED: (
            "execution-ready handoff under failed calibration, carryover, or missing controls",
            "transition-level QC promoted into vendor-parity targeted biology",
        ),
    }
    return WorkflowScientificErrorBudget(
        workflow_family=workflow_family,
        acceptable_errors=acceptable_errors[workflow_family],
        release_blocking_errors=blocking_errors[workflow_family],
        note="The release bar is set by scientific error containment, not only by parser or manifest completeness.",
    )


__all__ = [
    "RecommendationFailureTrapEntry",
    "RecommendationFailureTrapReport",
    "WorkflowScientificErrorBudget",
    "build_recommendation_failure_trap_report",
    "build_workflow_scientific_error_budget",
]
