# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Downstream-consumable workflow reference briefings with explicit provenance."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.grounding.contexts import (
    DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
    ScientificContextEntry,
)
from bijux_proteomics_knowledge.references.grounding.literature import (
    DEFAULT_LITERATURE_GROUPS,
    LiteratureGroup,
)
from bijux_proteomics_knowledge.references.grounding.problems import (
    DEFAULT_KNOWN_PROBLEM_REGISTRY,
    KnownProblemRegistryEntry,
)
from bijux_proteomics_knowledge.references.grounding.rules import (
    DEFAULT_SCIENTIFIC_RULE_REFERENCES,
    ScientificRuleReference,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.narratives import (
    DEFAULT_WORKFLOW_NARRATIVES,
    WorkflowNarrative,
    WorkflowNarrativeKind,
)


class WorkflowDecisionGradeCriterion(JsonModel):
    """One exact criterion that must hold before a workflow is decision-grade."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    required_evidence_planes: tuple[str, ...] = Field(default_factory=tuple)
    blocking_if_missing: bool = True


class WorkflowDecisionGradeFramework(JsonModel):
    """Decision-grade acceptance criteria for one workflow family."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    decision_grade_definition: str = Field(..., min_length=1)
    criteria: tuple[WorkflowDecisionGradeCriterion, ...] = Field(default_factory=tuple)


class WorkflowReferenceBriefing(JsonModel):
    """One workflow-level briefing built from curated knowledge registries."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    benchmark_manifest: BenchmarkManifest
    evidence_claim: WorkflowNarrative
    limitation: WorkflowNarrative
    scientific_context: tuple[ScientificContextEntry, ...] = Field(
        default_factory=tuple
    )
    literature_groups: tuple[LiteratureGroup, ...] = Field(default_factory=tuple)
    known_problems: tuple[KnownProblemRegistryEntry, ...] = Field(default_factory=tuple)
    scientific_rules: tuple[ScientificRuleReference, ...] = Field(default_factory=tuple)
    scope_limit_notes: tuple[str, ...] = Field(default_factory=tuple)
    interpretation_context_lines: tuple[str, ...] = Field(default_factory=tuple)
    decision_grade_framework: WorkflowDecisionGradeFramework


def _benchmark_by_family(workflow_family: KnowledgeWorkflowFamily) -> BenchmarkManifest:
    return next(
        manifest
        for manifest in DEFAULT_BENCHMARK_MANIFESTS
        if manifest.workflow_family is workflow_family
    )


def _narrative_by_kind(
    workflow_family: KnowledgeWorkflowFamily,
    narrative_kind: WorkflowNarrativeKind,
) -> WorkflowNarrative:
    return next(
        narrative
        for narrative in DEFAULT_WORKFLOW_NARRATIVES
        if narrative.workflow_family is workflow_family
        and narrative.narrative_kind is narrative_kind
    )


def _interpretation_context_lines(
    workflow_family: KnowledgeWorkflowFamily,
) -> tuple[str, ...]:
    if workflow_family is KnowledgeWorkflowFamily.LFQ:
        return (
            "Quantitative shifts stay biologically bounded until replicate stability, batch posture, and missingness mechanism all remain explicit together.",
            "Benchmark interpretation must distinguish stable feature summaries from claims about robust effect size or cohort-transferable abundance biology.",
        )
    if workflow_family is KnowledgeWorkflowFamily.PTM:
        return (
            "PTM interpretation must keep localization ambiguity, motif fragility, and proteoform uncertainty visible before any pathway or site-centric takeaway is promoted.",
            "A site table is not yet a biological mechanism claim unless benchmark scope and literature grounding converge on the same bounded story.",
        )
    if workflow_family is KnowledgeWorkflowFamily.TARGETED:
        return (
            "Targeted interpretation must stay transition-first: calibration, heavy references, carryover, and interference remain part of the biology-facing reading, not only assay setup.",
            "Clean chromatogram summaries do not justify protein-level or outcome-level confidence unless control coverage and reconciliation evidence also survive review.",
        )
    if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
        return (
            "Multiplex interpretation must keep reporter chemistry, reference-channel posture, and ratio-compression risk visible before any biological comparison is treated as stable.",
        )
    if workflow_family is KnowledgeWorkflowFamily.DIA:
        return (
            "DIA interpretation depends on more than import success: library coverage, transition semantics, protein rollup, and absent-expected-peptide pressure remain biologically active limits.",
        )
    return (
        "DDA interpretation remains bounded by search-engine export scope, target-decoy posture, and adapter loss accounting rather than broad proteome truth authority.",
    )


def _decision_grade_framework(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowDecisionGradeFramework:
    definitions = {
        KnowledgeWorkflowFamily.DDA: (
            "Decision-grade DDA requires preserved target-decoy semantics, cross-engine accountability, and protein inference behavior that remains stable under contaminant and adapter pressure.",
            (
                WorkflowDecisionGradeCriterion(
                    criterion_id="dda_target_decoy_accountability",
                    summary="Target-decoy evidence remains visible and calibration stress does not collapse confidence framing.",
                    required_evidence_planes=(
                        "benchmark",
                        "confidence_calibration",
                        "review_bundle",
                    ),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="dda_cross_engine_accountability",
                    summary="Comparator evidence or known-loss dossiers keep search-adapter behavior honest against external engines.",
                    required_evidence_planes=("benchmark", "comparator", "references"),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="dda_protein_inference_stability",
                    summary="Protein-level conclusions remain stable under shared-peptide and contaminant pressure.",
                    required_evidence_planes=("benchmark", "protein_inference", "qc"),
                ),
            ),
        ),
        KnowledgeWorkflowFamily.DIA: (
            "Decision-grade DIA requires strong library-conditioned import, transition semantics, protein evidence, and biological-interpretation tiers with explicit comparator limits.",
            (
                WorkflowDecisionGradeCriterion(
                    criterion_id="dia_tier_alignment",
                    summary="Import, transition, protein, and biological interpretation tiers all remain above bounded scientific thresholds.",
                    required_evidence_planes=(
                        "benchmark",
                        "capability_matrix",
                        "review_bundle",
                    ),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="dia_library_and_mobility_coverage",
                    summary="Library coverage, ion-mobility coverage, and absent-expected-peptide pressure all remain inside documented interpretation limits.",
                    required_evidence_planes=("benchmark", "library_scope", "qc"),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="dia_external_accountability",
                    summary="External comparator posture keeps vendor and library parity caveats visible.",
                    required_evidence_planes=("benchmark", "comparator", "references"),
                ),
            ),
        ),
        KnowledgeWorkflowFamily.PTM: (
            "Decision-grade PTM requires localization confidence, ambiguity propagation control, family-specific credibility, and literature-bounded site interpretation.",
            (
                WorkflowDecisionGradeCriterion(
                    criterion_id="ptm_localization_confidence",
                    summary="Localization confidence remains high enough that ambiguous site groups do not dominate the claimed biology.",
                    required_evidence_planes=(
                        "benchmark",
                        "site_table",
                        "localization",
                    ),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="ptm_family_specific_scope",
                    summary="Only PTM families with explicit credibility tracks and scope limits can support decision-facing interpretation.",
                    required_evidence_planes=(
                        "benchmark",
                        "family_track",
                        "references",
                    ),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="ptm_literature_bounded_interpretation",
                    summary="Motif and pathway interpretations remain aligned with literature and are blocked when ambiguity or comparator pressure stays unresolved.",
                    required_evidence_planes=(
                        "benchmark",
                        "literature",
                        "review_packet",
                    ),
                ),
            ),
        ),
        KnowledgeWorkflowFamily.LFQ: (
            "Decision-grade LFQ requires stable replicate structure, controlled missingness, batch-aware normalization, and comparator-bounded abundance claims.",
            (
                WorkflowDecisionGradeCriterion(
                    criterion_id="lfq_missingness_accounted",
                    summary="Missingness mechanism and replicate structure stay explicit enough that abundance summaries do not overclaim robustness.",
                    required_evidence_planes=("benchmark", "readiness", "qc"),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="lfq_batch_and_normalization_stability",
                    summary="Batch posture and normalization drift remain inside bounded interpretation limits.",
                    required_evidence_planes=("benchmark", "normalization", "batch_qc"),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="lfq_external_quant_accountability",
                    summary="Comparator pressure and literature context both bound what quantitative biology the benchmark can authorize.",
                    required_evidence_planes=("benchmark", "comparator", "references"),
                ),
            ),
        ),
        KnowledgeWorkflowFamily.MULTIPLEX: (
            "Decision-grade multiplex requires channel chemistry stability, reference-channel integrity, and bounded interpretation under compression and imbalance pressure.",
            (
                WorkflowDecisionGradeCriterion(
                    criterion_id="multiplex_channel_integrity",
                    summary="Reference, bridge, and sample channels remain interpretable without hidden dropout or chemistry ambiguity.",
                    required_evidence_planes=("benchmark", "channel_policy", "qc"),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="multiplex_artifact_pressure",
                    summary="Ratio compression, overloaded carrier, and imbalance pressure remain explicit in the benchmark outcome.",
                    required_evidence_planes=(
                        "benchmark",
                        "chemistry",
                        "review_bundle",
                    ),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="multiplex_biological_scope",
                    summary="Biological interpretation remains bounded to the documented chemistry family and comparator scope.",
                    required_evidence_planes=("benchmark", "references", "comparator"),
                ),
            ),
        ),
        KnowledgeWorkflowFamily.TARGETED: (
            "Decision-grade targeted support requires chromatogram QC, calibration standards, heavy references, control coverage, honest handoff packets, and reconciled outcomes.",
            (
                WorkflowDecisionGradeCriterion(
                    criterion_id="targeted_qc_and_calibration",
                    summary="Chromatogram QC, calibration standards, and interference behavior all remain explicit before transition handoff.",
                    required_evidence_planes=(
                        "benchmark",
                        "chromatogram_qc",
                        "calibration",
                    ),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="targeted_control_coverage",
                    summary="Blank, heavy-reference, and calibration-standard controls all stay visible before claims leave advisory status.",
                    required_evidence_planes=("benchmark", "controls", "lab_handoff"),
                ),
                WorkflowDecisionGradeCriterion(
                    criterion_id="targeted_outcome_reconciliation",
                    summary="Observed failures are reconciled with corrective action instead of being hidden behind clean handoff prose.",
                    required_evidence_planes=(
                        "benchmark",
                        "reconciliation",
                        "reporting",
                    ),
                ),
            ),
        ),
    }
    definition, criteria = definitions[workflow_family]
    return WorkflowDecisionGradeFramework(
        workflow_family=workflow_family,
        decision_grade_definition=definition,
        criteria=criteria,
    )


def build_workflow_reference_briefing(
    workflow_family: KnowledgeWorkflowFamily,
) -> WorkflowReferenceBriefing:
    """Build one downstream-consumable workflow briefing with explicit provenance."""
    benchmark_manifest = _benchmark_by_family(workflow_family)
    evidence_claim = _narrative_by_kind(
        workflow_family, WorkflowNarrativeKind.EVIDENCE_CLAIM
    )
    limitation = _narrative_by_kind(workflow_family, WorkflowNarrativeKind.LIMITATION)
    context_ids = {
        *evidence_claim.context_ids,
        *limitation.context_ids,
    }
    problem_ids = {
        *evidence_claim.problem_ids,
        *limitation.problem_ids,
    }
    scientific_context = tuple(
        entry
        for entry in DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES
        if entry.context_id in context_ids
    )
    literature_groups = tuple(
        group
        for group in DEFAULT_LITERATURE_GROUPS
        if benchmark_manifest.benchmark_id in group.benchmark_ids
        or any(
            context.context_id in group.context_ids for context in scientific_context
        )
    )
    known_problems = tuple(
        entry
        for entry in DEFAULT_KNOWN_PROBLEM_REGISTRY
        if entry.problem_id in problem_ids
    )
    related_rule_ids = {
        rule_id
        for context in scientific_context
        for rule_id in context.related_rule_ids
    }
    scientific_rules = tuple(
        rule
        for rule in DEFAULT_SCIENTIFIC_RULE_REFERENCES
        if rule.rule_id in related_rule_ids
        or benchmark_manifest.benchmark_id in rule.benchmark_ids
    )
    scope_limit_notes = tuple(
        dict.fromkeys(
            (
                *evidence_claim.scope_limit_notes,
                *limitation.scope_limit_notes,
                *benchmark_manifest.exclusion_notes,
                *benchmark_manifest.weakness_notes,
                *benchmark_manifest.failure_mode_notes,
            )
        )
    )
    interpretation_context_lines = _interpretation_context_lines(workflow_family)
    decision_grade_framework = _decision_grade_framework(workflow_family)
    return WorkflowReferenceBriefing(
        workflow_family=workflow_family,
        benchmark_manifest=benchmark_manifest,
        evidence_claim=evidence_claim,
        limitation=limitation,
        scientific_context=scientific_context,
        literature_groups=literature_groups,
        known_problems=known_problems,
        scientific_rules=scientific_rules,
        scope_limit_notes=scope_limit_notes,
        interpretation_context_lines=interpretation_context_lines,
        decision_grade_framework=decision_grade_framework,
    )


def list_workflow_reference_briefings() -> tuple[WorkflowReferenceBriefing, ...]:
    """Return workflow briefings for each curated workflow family."""
    return tuple(
        build_workflow_reference_briefing(workflow_family)
        for workflow_family in KnowledgeWorkflowFamily
    )


__all__ = [
    "WorkflowReferenceBriefing",
    "build_workflow_reference_briefing",
    "list_workflow_reference_briefings",
]
