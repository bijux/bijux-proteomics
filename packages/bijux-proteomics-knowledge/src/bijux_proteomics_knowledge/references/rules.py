# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated scientific rules and grounded judgment ledgers for references."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.json_models import JsonModel
from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily


class KnowledgeRuleDomain(StrEnum):
    """Scientific rule domains that need durable reference grounding."""

    ENZYME = "enzyme"
    PTM_ASSUMPTION = "ptm_assumption"
    LABEL_CHEMISTRY = "label_chemistry"
    FDR_CAVEAT = "fdr_caveat"
    INFERENCE_CAUTION = "inference_caution"


class ScientificRuleReference(JsonModel):
    """One curated scientific rule backed by references and benchmark rationale."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str = Field(..., min_length=1)
    domain: KnowledgeRuleDomain
    title: str = Field(..., min_length=1)
    rule_statement: str = Field(..., min_length=1)
    version_trace: tuple[str, ...] = Field(..., min_length=1)
    retrieval_trace: tuple[str, ...] = Field(..., min_length=1)
    citation_ids: tuple[str, ...] = Field(..., min_length=1)
    benchmark_ids: tuple[str, ...] = Field(..., min_length=1)
    benchmark_rationale: str = Field(..., min_length=1)
    related_term_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator(
        "citation_ids",
        "benchmark_ids",
        "related_term_ids",
        "version_trace",
        "retrieval_trace",
    )
    @classmethod
    def _strip_blank_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if value and not cleaned:
            raise ValueError("tuple fields must not contain only blank values")
        return cleaned


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


DEFAULT_SCIENTIFIC_RULE_REFERENCES: tuple[ScientificRuleReference, ...] = (
    ScientificRuleReference(
        rule_id="rule:trypsin_specificity",
        domain=KnowledgeRuleDomain.ENZYME,
        title="Trypsin specificity rule",
        rule_statement="Benchmark claims that assume tryptic digestion must state trypsin or LysC-style cleavage expectations explicitly before peptide-level evidence is interpreted.",
        version_trace=("Rule wording was reviewed against the linked references and benchmark surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citation ids, benchmark ids, and related term ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:uniprot_2025",),
        benchmark_ids=(
            "benchmark:dda_search_reproducibility",
            "benchmark:lfq_quantification_repeatability",
        ),
        benchmark_rationale="The bundled digestion and quantification fixtures are only interpretable when cleavage-specific search and quantification assumptions stay explicit.",
        related_term_ids=("enzyme:trypsin", "enzyme:lysc"),
    ),
    ScientificRuleReference(
        rule_id="rule:protease_panel_equivalence",
        domain=KnowledgeRuleDomain.ENZYME,
        title="Protease panel equivalence needs explicit evidence",
        rule_statement="Claims that compare tryptic and LysC-style peptide panels must keep protease-specific detectability limits explicit instead of treating one clean fixture panel as evidence of cross-protease interchangeability.",
        version_trace=("Rule wording was reviewed against the linked references and benchmark surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citation ids, benchmark ids, and related term ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:uniprot_2025", "citation:protein_inference_2012"),
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        benchmark_rationale="Adapter-normalized DDA fixture outputs can look consistent across protease-shaped exports even when peptide detectability and downstream rollup meaning are not equivalent.",
        related_term_ids=("enzyme:trypsin", "enzyme:lysc"),
    ),
    ScientificRuleReference(
        rule_id="rule:phosphorylation_localization",
        domain=KnowledgeRuleDomain.PTM_ASSUMPTION,
        title="Phosphorylation localization rule",
        rule_statement="Any phosphorylation claim must preserve localization-confidence evidence and PSI-MOD grounded PTM labels instead of collapsing ambiguous sites into unqualified protein conclusions.",
        version_trace=("Rule wording was reviewed against the linked references and benchmark surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citation ids, benchmark ids, and related term ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        benchmark_rationale="The PTM fixture suite is only useful if ambiguous localization remains distinguishable from confidently localized phosphorylation sites.",
        related_term_ids=("ptm:phosphorylation",),
    ),
    ScientificRuleReference(
        rule_id="rule:ptm_regulation_scope",
        domain=KnowledgeRuleDomain.PTM_ASSUMPTION,
        title="PTM regulation claims need evidence beyond localization",
        rule_statement="PTM narratives must keep localization evidence separate from regulation or occupancy claims unless the benchmarked evidence also carries the quantitative and design context needed to support that broader interpretation.",
        version_trace=("Rule wording was reviewed against the linked references and benchmark surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citation ids, benchmark ids, and related term ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006", "citation:protein_inference_2012"),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        benchmark_rationale="The PTM localization fixture proves concept grounding and site confidence, but it does not by itself justify regulation-scale biological claims.",
        related_term_ids=("ptm:phosphorylation",),
    ),
    ScientificRuleReference(
        rule_id="rule:tmtpro_channel_interpretation",
        domain=KnowledgeRuleDomain.LABEL_CHEMISTRY,
        title="TMTpro channel interpretation rule",
        rule_statement="Multiplex claims must retain TMTpro reporter-channel assumptions and avoid treating channel-level summaries as label-free abundance evidence.",
        version_trace=("Rule wording was reviewed against the linked references and benchmark surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citation ids, benchmark ids, and related term ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:tmtpro_2020",),
        benchmark_ids=("benchmark:multiplex_tmtpro_quantification",),
        benchmark_rationale="The multiplex quantification fixture suite exists to preserve label-chemistry semantics during reporter-channel interpretation.",
        related_term_ids=(),
    ),
    ScientificRuleReference(
        rule_id="rule:target_decoy_scope",
        domain=KnowledgeRuleDomain.FDR_CAVEAT,
        title="Target-decoy scope rule",
        rule_statement="False-discovery claims must state the scope they apply to, because peptide-spectrum, peptide, and protein rollups do not share identical error guarantees.",
        version_trace=("Rule wording was reviewed against the linked references and benchmark surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citation ids, benchmark ids, and related term ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:target_decoy_2007", "citation:protein_inference_2012"),
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        benchmark_rationale="Adapter-normalized search outputs can only support reliable FDR claims when the asserted scope remains explicit across evidence rollups.",
        related_term_ids=(),
    ),
    ScientificRuleReference(
        rule_id="rule:dia_library_transfer_scope",
        domain=KnowledgeRuleDomain.INFERENCE_CAUTION,
        title="DIA library transfer claims need explicit scope",
        rule_statement="DIA narratives must keep library composition, assay transfer limits, and peptide-centric evidence scope explicit instead of treating one stable extraction surface as proof of broad protein-level portability.",
        version_trace=("Rule wording was reviewed against the linked references and benchmark surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citation ids, benchmark ids, and related term ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:swath_2012", "citation:psi_ms_cv_2012", "citation:protein_inference_2012"),
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        benchmark_rationale="A library-conditioned DIA fixture can stay internally consistent while still overstating how safely the same extraction surface transfers to new libraries, cohorts, or protein-facing interpretations.",
        related_term_ids=("acquisition_mode:dia",),
    ),
    ScientificRuleReference(
        rule_id="rule:protein_inference_rollup",
        domain=KnowledgeRuleDomain.INFERENCE_CAUTION,
        title="Protein inference rollup caution",
        rule_statement="Protein-level summaries must remain explicitly qualified when peptide evidence is shared, sparse, or transition-derived rather than directly protein-specific.",
        version_trace=("Rule wording was reviewed against the linked references and benchmark surfaces on 2026-05-05.",),
        retrieval_trace=("The linked citation ids, benchmark ids, and related term ids were re-verified on 2026-05-05.",),
        citation_ids=("citation:protein_inference_2012", "citation:swath_2012"),
        benchmark_ids=(
            "benchmark:targeted_transition_quality_control",
            "benchmark:dia_library_extraction_consistency",
        ),
        benchmark_rationale="Targeted and DIA evidence both encourage early rollup, so the benchmark layer needs an explicit caution mapping for shared-peptide and transition-derived ambiguity.",
        related_term_ids=("acquisition_mode:dia",),
    ),
)


def build_ranking_rule_grounding_ledger(
    workflow_family: KnowledgeWorkflowFamily,
) -> RankingRuleGroundingLedger:
    """Build knowledge-backed rule grounding for one workflow family."""

    from bijux_proteomics_knowledge.references.briefings import (
        build_workflow_reference_briefing,
    )

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
    "DEFAULT_SCIENTIFIC_RULE_REFERENCES",
    "GroundedDecisionRule",
    "KnowledgeRuleDomain",
    "RankingRuleGroundingLedger",
    "ScientificRuleReference",
    "build_ranking_rule_grounding_ledger",
    "rule_grounding_map",
]
