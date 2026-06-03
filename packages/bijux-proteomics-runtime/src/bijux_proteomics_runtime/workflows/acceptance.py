# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Acceptance, failure, and proof-bar surfaces for the flagship workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WorkflowFailureCategory(StrEnum):
    """Why a workflow stage fails in a reviewer-relevant way."""

    ENGINEERING_BREAKAGE = "engineering_breakage"
    SCIENTIFIC_INCOMPLETENESS = "scientific_incompleteness"
    EXTERNAL_CAPABILITY_GAP = "external_capability_gap"
    REVIEW_AUTHORITY_BOUNDARY = "review_authority_boundary"
    OPERATIONAL_EXECUTION_CONFLICT = "operational_execution_conflict"


@dataclass(frozen=True)
class WorkflowStageAcceptance:
    """Acceptance posture for one stage in the flagship workflow."""

    stage_id: str
    typed_only: bool
    executable: bool
    replayable: bool
    benchmarked: bool
    lab_reviewed: bool
    validating_test_paths: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowAcceptanceDossier:
    """Machine-readable stage acceptance status for the flagship workflow."""

    workflow_family: str
    stages: tuple[WorkflowStageAcceptance, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowFailureTaxonomyEntry:
    """One explicit workflow failure mode with reviewer-facing meaning."""

    failure_id: str
    stage_id: str
    category: WorkflowFailureCategory
    reviewer_question: str
    consequence: str
    blocks_decision_grade: bool


@dataclass(frozen=True)
class WorkflowFailureTaxonomy:
    """Stable set of failure modes for the flagship workflow."""

    workflow_family: str
    entries: tuple[WorkflowFailureTaxonomyEntry, ...]


@dataclass(frozen=True)
class WorkflowProofRequirement:
    """One non-negotiable requirement before a workflow can be called real."""

    requirement_id: str
    requirement_label: str
    validating_surface_refs: tuple[str, ...]
    validating_test_paths: tuple[str, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowProofBar:
    """Minimum proof bar for a workflow that deserves a real-support claim."""

    workflow_family: str
    requirements: tuple[WorkflowProofRequirement, ...]
    notes: tuple[str, ...] = ()


def build_flagship_workflow_acceptance_dossier() -> WorkflowAcceptanceDossier:
    """Return the current acceptance posture for the flagship workflow stages."""

    return WorkflowAcceptanceDossier(
        workflow_family="flagship-workflows",
        stages=(
            WorkflowStageAcceptance(
                stage_id="runtime-workflow-manifest",
                typed_only=True,
                executable=False,
                replayable=False,
                benchmarked=False,
                lab_reviewed=False,
                validating_test_paths=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_workflow_plans_surface.py",
                ),
                notes=(
                    "The manifest is a typed root contract, not an execution artifact by itself.",
                ),
            ),
            WorkflowStageAcceptance(
                stage_id="core-identification-review",
                typed_only=False,
                executable=True,
                replayable=True,
                benchmarked=True,
                lab_reviewed=False,
                validating_test_paths=(
                    "packages/bijux-proteomics-core/tests/identification/test_identification_surface.py",
                    "packages/bijux-proteomics-core/tests/identification/test_protein_inference_benchmark_surface.py",
                ),
            ),
            WorkflowStageAcceptance(
                stage_id="core-quantification-review",
                typed_only=False,
                executable=True,
                replayable=True,
                benchmarked=True,
                lab_reviewed=False,
                validating_test_paths=(
                    "packages/bijux-proteomics-core/tests/quantification/test_quant_review_bundle_surface.py",
                    "packages/bijux-proteomics-core/tests/quantification/test_quantification_scientific_benchmark_surface.py",
                ),
            ),
            WorkflowStageAcceptance(
                stage_id="core-ptm-review",
                typed_only=False,
                executable=True,
                replayable=True,
                benchmarked=True,
                lab_reviewed=True,
                validating_test_paths=(
                    "packages/bijux-proteomics-core/tests/ptm/test_lab_validation_packet_surface.py",
                    "packages/bijux-proteomics-core/tests/ptm/test_ptm_scientific_benchmark_surface.py",
                ),
            ),
            WorkflowStageAcceptance(
                stage_id="knowledge-evidence-review",
                typed_only=False,
                executable=True,
                replayable=True,
                benchmarked=True,
                lab_reviewed=False,
                validating_test_paths=(
                    "packages/bijux-proteomics-knowledge/tests/reviews/test_decision_briefs.py",
                    "packages/bijux-proteomics-knowledge/tests/reviews/test_provenance_surface.py",
                ),
            ),
            WorkflowStageAcceptance(
                stage_id="intelligence-decision-review",
                typed_only=False,
                executable=True,
                replayable=True,
                benchmarked=True,
                lab_reviewed=False,
                validating_test_paths=(
                    "packages/bijux-proteomics-intelligence/tests/judgment/test_scenarios_surface.py",
                    "packages/bijux-proteomics-intelligence/tests/reviews/test_benchmarks_surface.py",
                ),
            ),
            WorkflowStageAcceptance(
                stage_id="lab-review-packet",
                typed_only=False,
                executable=True,
                replayable=True,
                benchmarked=True,
                lab_reviewed=True,
                validating_test_paths=(
                    "packages/bijux-proteomics-lab/tests/planning/test_plan_construction_surface.py",
                ),
            ),
            WorkflowStageAcceptance(
                stage_id="lab-operational-follow-up",
                typed_only=False,
                executable=True,
                replayable=True,
                benchmarked=True,
                lab_reviewed=True,
                validating_test_paths=(
                    "packages/bijux-proteomics-lab/tests/reconciliation/test_operational_follow_up_path.py",
                ),
            ),
        ),
        notes=(
            "Typed-only stages are allowed only at the root manifest boundary.",
            "Decision-grade promotion depends on replayable, benchmarked, and review-preserving downstream stages.",
        ),
    )


def build_flagship_workflow_failure_taxonomy() -> WorkflowFailureTaxonomy:
    """Return explicit workflow failure modes with reviewer-facing meaning."""

    entries = (
        WorkflowFailureTaxonomyEntry(
            failure_id="manifest-missing-required-inputs",
            stage_id="runtime-workflow-manifest",
            category=WorkflowFailureCategory.ENGINEERING_BREAKAGE,
            reviewer_question="Did the run even declare the assets required for reproducibility?",
            consequence="Stop before any scientific interpretation because the workflow root is incomplete.",
            blocks_decision_grade=True,
        ),
        WorkflowFailureTaxonomyEntry(
            failure_id="identification-weak-calibration",
            stage_id="core-identification-review",
            category=WorkflowFailureCategory.SCIENTIFIC_INCOMPLETENESS,
            reviewer_question="Are accepted identifications still trustworthy under calibration pressure?",
            consequence="Protein, peptide, and downstream PTM or quantification claims must downgrade.",
            blocks_decision_grade=True,
        ),
        WorkflowFailureTaxonomyEntry(
            failure_id="quantification-batch-or-missingness-block",
            stage_id="core-quantification-review",
            category=WorkflowFailureCategory.SCIENTIFIC_INCOMPLETENESS,
            reviewer_question="Are quantitative shifts interpretable or mostly design and missingness artifacts?",
            consequence="Differential abundance may remain review-grade only.",
            blocks_decision_grade=True,
        ),
        WorkflowFailureTaxonomyEntry(
            failure_id="ptm-ambiguous-localization",
            stage_id="core-ptm-review",
            category=WorkflowFailureCategory.SCIENTIFIC_INCOMPLETENESS,
            reviewer_question="Is the site-level PTM evidence strong enough for lab targeting?",
            consequence="Site claims stay interpretive and cannot drive focused assay handoff.",
            blocks_decision_grade=True,
        ),
        WorkflowFailureTaxonomyEntry(
            failure_id="knowledge-contradictory-grounding",
            stage_id="knowledge-evidence-review",
            category=WorkflowFailureCategory.REVIEW_AUTHORITY_BOUNDARY,
            reviewer_question="Do literature and benchmark grounding still agree on the same story?",
            consequence="Recommendation strength must downgrade until the contradiction is resolved.",
            blocks_decision_grade=True,
        ),
        WorkflowFailureTaxonomyEntry(
            failure_id="intelligence-unsupported-promotion",
            stage_id="intelligence-decision-review",
            category=WorkflowFailureCategory.REVIEW_AUTHORITY_BOUNDARY,
            reviewer_question="Is the recommendation trying to outrun the available evidence and benchmark scope?",
            consequence="The system must refuse advancement rather than smoothing over thin grounding.",
            blocks_decision_grade=True,
        ),
        WorkflowFailureTaxonomyEntry(
            failure_id="lab-missing-minimum-controls",
            stage_id="lab-review-packet",
            category=WorkflowFailureCategory.OPERATIONAL_EXECUTION_CONFLICT,
            reviewer_question="Are the control needs explicit before instrument time is spent?",
            consequence="The lab plan stays blocked because execution honesty is missing.",
            blocks_decision_grade=True,
        ),
        WorkflowFailureTaxonomyEntry(
            failure_id="follow-up-observed-outcome-conflict",
            stage_id="lab-operational-follow-up",
            category=WorkflowFailureCategory.OPERATIONAL_EXECUTION_CONFLICT,
            reviewer_question="Did the observed assay outcome contradict the promoted decision path?",
            consequence="A next-cycle packet and operator actions are mandatory before further promotion.",
            blocks_decision_grade=False,
        ),
        WorkflowFailureTaxonomyEntry(
            failure_id="external-adapter-not-launchable",
            stage_id="runtime-workflow-manifest",
            category=WorkflowFailureCategory.EXTERNAL_CAPABILITY_GAP,
            reviewer_question="Is the declared external engine path executable or only normalization-compatible?",
            consequence="The workflow may remain import-reviewable but cannot be claimed as end-to-end executable.",
            blocks_decision_grade=False,
        ),
    )
    return WorkflowFailureTaxonomy(
        workflow_family="flagship-workflows",
        entries=entries,
    )


def build_minimum_real_workflow_proof_bar() -> WorkflowProofBar:
    """Return the minimum proof bar for a workflow that deserves a real claim."""

    return WorkflowProofBar(
        workflow_family="flagship-workflows",
        requirements=(
            WorkflowProofRequirement(
                requirement_id="reproducible-run",
                requirement_label="one reproducible run path exists and stays replay-auditable",
                validating_surface_refs=(
                    "bijux_proteomics_runtime.workflows.assurance.build_flagship_operator_path",
                    "bijux_proteomics_runtime.workflows.plans.build_workflow_replay_proof_report",
                ),
                validating_test_paths=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_operator_path_surface.py",
                    "packages/bijux-proteomics-runtime/tests/workflows/test_workflow_plans_surface.py",
                ),
            ),
            WorkflowProofRequirement(
                requirement_id="reviewed-artifacts",
                requirement_label="every downstream stage emits a stable decision brief or report",
                validating_surface_refs=(
                    "bijux_proteomics.identification.contracts.build_review_ready_evidence_bundle",
                    "bijux_proteomics.quantification.review.build_quant_review_bundle",
                    "bijux_proteomics.ptm.review.build_ptm_lab_validation_packet",
                    "bijux_proteomics_knowledge.reviews.decision_briefs.build_knowledge_decision_brief",
                    "bijux_proteomics_intelligence.reviews.decision_briefs.build_intelligence_review_packet",
                    "bijux_proteomics_lab.planning.assays.build_lab_review_packet_bundle",
                    "bijux_proteomics_lab.reconciliation.follow_up.build_operational_follow_up_path",
                ),
                validating_test_paths=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_workflow_acceptance_surface.py",
                ),
            ),
            WorkflowProofRequirement(
                requirement_id="known-limits",
                requirement_label="failure modes and known limits stay explicit and machine-readable",
                validating_surface_refs=(
                    "bijux_proteomics_runtime.workflows.acceptance.build_flagship_workflow_failure_taxonomy",
                    "bijux_proteomics_runtime.workflows.plans.build_external_tool_capability_report",
                ),
                validating_test_paths=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_workflow_acceptance_surface.py",
                ),
            ),
            WorkflowProofRequirement(
                requirement_id="serious-benchmark-corpus",
                requirement_label="at least one serious tracked benchmark lane backs the workflow family",
                validating_surface_refs=(
                    "bijux_proteomics_runtime.workflows.assurance.build_workflow_assurance_matrix",
                ),
                validating_test_paths=(
                    "packages/bijux-proteomics-runtime/tests/workflows/test_workflow_assurance_surface.py",
                    "packages/bijux-proteomics-runtime/tests/workflows/test_workflow_acceptance_surface.py",
                ),
                notes=(
                    "Synthetic-only or typed-only surfaces do not satisfy this requirement.",
                ),
            ),
        ),
        notes=(
            "A workflow does not become real because its contracts exist; it becomes real when these proof requirements stay simultaneously true.",
        ),
    )
