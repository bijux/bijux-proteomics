# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Downstream-consumable workflow reference briefings with explicit provenance."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_models import JsonModel

from bijux_proteomics_knowledge.references.benchmarks import (
    BenchmarkManifest,
    DEFAULT_BENCHMARK_MANIFESTS,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.contexts import (
    DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES,
    ScientificContextEntry,
)
from bijux_proteomics_knowledge.references.literature import (
    DEFAULT_LITERATURE_GROUPS,
    LiteratureGroup,
)
from bijux_proteomics_knowledge.references.narratives import (
    DEFAULT_WORKFLOW_NARRATIVES,
    WorkflowNarrative,
    WorkflowNarrativeKind,
)
from bijux_proteomics_knowledge.references.problems import (
    DEFAULT_KNOWN_PROBLEM_REGISTRY,
    KnownProblemRegistryEntry,
)
from bijux_proteomics_knowledge.references.rules import (
    DEFAULT_SCIENTIFIC_RULE_REFERENCES,
    ScientificRuleReference,
)


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
