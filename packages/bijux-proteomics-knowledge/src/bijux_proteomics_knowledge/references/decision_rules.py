# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated intelligence decision rules grounded in knowledge-owned references."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.references.briefings import (
    build_workflow_reference_briefing,
)
from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily


class GroundedDecisionRule(JsonModel):
    """One intelligence rule tied to knowledge-owned reference provenance."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    title: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    citation_ids: tuple[str, ...] = Field(default_factory=tuple)
    benchmark_ids: tuple[str, ...] = Field(default_factory=tuple)
    context_ids: tuple[str, ...] = Field(default_factory=tuple)
    known_problem_ids: tuple[str, ...] = Field(default_factory=tuple)
    literature_group_ids: tuple[str, ...] = Field(default_factory=tuple)
    scientific_rule_ids: tuple[str, ...] = Field(default_factory=tuple)


class RankingRuleGroundingLedger(JsonModel):
    """Grounding ledger for ranking and recommendation rules in one workflow."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    rules: tuple[GroundedDecisionRule, ...] = Field(default_factory=tuple)


def build_ranking_rule_grounding_ledger(
    workflow_family: KnowledgeWorkflowFamily,
) -> RankingRuleGroundingLedger:
    """Build knowledge-backed rule grounding for one workflow family."""
    briefing = build_workflow_reference_briefing(workflow_family)
    citation_ids = (
        briefing.evidence_claim.citation_ids + briefing.limitation.citation_ids
    )
    benchmark_ids = (briefing.benchmark_manifest.benchmark_id,)
    context_ids = tuple(entry.context_id for entry in briefing.scientific_context)
    known_problem_ids = tuple(entry.problem_id for entry in briefing.known_problems)
    literature_group_ids = tuple(group.group_id for group in briefing.literature_groups)
    scientific_rule_ids = tuple(rule.rule_id for rule in briefing.scientific_rules)

    return RankingRuleGroundingLedger(
        workflow_family=workflow_family,
        rules=(
            GroundedDecisionRule(
                rule_id="rule:evidence_strength_priority",
                workflow_family=workflow_family,
                title="Evidence strength should dominate recommendation confidence",
                rationale=(
                    "Strong recommendation pressure is only defensible when the "
                    "workflow-specific evidence claim remains within the benchmarked "
                    "scope and the limitation narrative remains attached."
                ),
                citation_ids=citation_ids,
                benchmark_ids=benchmark_ids,
                context_ids=context_ids,
                known_problem_ids=known_problem_ids,
                literature_group_ids=literature_group_ids,
                scientific_rule_ids=scientific_rule_ids,
            ),
            GroundedDecisionRule(
                rule_id="rule:reproducibility_priority",
                workflow_family=workflow_family,
                title="Reproducibility should outrank novelty when support is weak",
                rationale=(
                    "The benchmark manifest and linked literature groups justify "
                    "rewarding repeatable evidence before novelty-heavy signals that "
                    "can look cleaner than production-scale data."
                ),
                citation_ids=citation_ids,
                benchmark_ids=benchmark_ids,
                context_ids=context_ids,
                known_problem_ids=known_problem_ids,
                literature_group_ids=literature_group_ids,
                scientific_rule_ids=scientific_rule_ids,
            ),
            GroundedDecisionRule(
                rule_id="rule:freshness_penalty",
                workflow_family=workflow_family,
                title="Stale evidence should suppress recommendation confidence",
                rationale=(
                    "Benchmark and known-problem registries make it unsafe to treat "
                    "aging evidence as equally decision-ready, especially when fixture "
                    "corpora can hide production drift."
                ),
                citation_ids=citation_ids,
                benchmark_ids=benchmark_ids,
                context_ids=context_ids,
                known_problem_ids=known_problem_ids,
                literature_group_ids=literature_group_ids,
                scientific_rule_ids=scientific_rule_ids,
            ),
            GroundedDecisionRule(
                rule_id="rule:contradiction_penalty",
                workflow_family=workflow_family,
                title="Contradictory evidence must stay explicit in ranking outputs",
                rationale=(
                    "Workflow limitations and curated scientific rules require the "
                    "package to preserve contradiction pressure instead of flattening it "
                    "into one opaque score."
                ),
                citation_ids=citation_ids,
                benchmark_ids=benchmark_ids,
                context_ids=context_ids,
                known_problem_ids=known_problem_ids,
                literature_group_ids=literature_group_ids,
                scientific_rule_ids=scientific_rule_ids,
            ),
            GroundedDecisionRule(
                rule_id="rule:assay_feasibility_and_operational_risk_balance",
                workflow_family=workflow_family,
                title="Assay feasibility and operational risk must remain visible",
                rationale=(
                    "Workflow limits and known problems justify keeping assay "
                    "feasibility, cost, and operational pressure explicit so the "
                    "package does not over-promote scientifically interesting but "
                    "operationally fragile follow-up work."
                ),
                citation_ids=citation_ids,
                benchmark_ids=benchmark_ids,
                context_ids=context_ids,
                known_problem_ids=known_problem_ids,
                literature_group_ids=literature_group_ids,
                scientific_rule_ids=scientific_rule_ids,
            ),
        ),
    )


def rule_grounding_map(
    workflow_family: KnowledgeWorkflowFamily,
) -> dict[str, GroundedDecisionRule]:
    """Return grounded rules keyed by stable rule identifier."""
    ledger = build_ranking_rule_grounding_ledger(workflow_family)
    return {rule.rule_id: rule for rule in ledger.rules}


__all__ = [
    "GroundedDecisionRule",
    "RankingRuleGroundingLedger",
    "build_ranking_rule_grounding_ledger",
    "rule_grounding_map",
]
