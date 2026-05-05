# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated scientific rule mappings backed by references and benchmark context."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.json_models import JsonModel


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
    citation_ids: tuple[str, ...] = Field(..., min_length=1)
    benchmark_ids: tuple[str, ...] = Field(..., min_length=1)
    benchmark_rationale: str = Field(..., min_length=1)
    related_term_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("citation_ids", "benchmark_ids", "related_term_ids")
    @classmethod
    def _strip_blank_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if value and not cleaned:
            raise ValueError("tuple fields must not contain only blank values")
        return cleaned


DEFAULT_SCIENTIFIC_RULE_REFERENCES: tuple[ScientificRuleReference, ...] = (
    ScientificRuleReference(
        rule_id="rule:trypsin_specificity",
        domain=KnowledgeRuleDomain.ENZYME,
        title="Trypsin specificity rule",
        rule_statement="Benchmark claims that assume tryptic digestion must state trypsin or LysC-style cleavage expectations explicitly before peptide-level evidence is interpreted.",
        citation_ids=("citation:uniprot_2025",),
        benchmark_ids=(
            "benchmark:dda_search_reproducibility",
            "benchmark:lfq_quantification_repeatability",
        ),
        benchmark_rationale="The bundled digestion and quantification fixtures are only interpretable when cleavage-specific search and quantification assumptions stay explicit.",
        related_term_ids=("enzyme:trypsin", "enzyme:lysc"),
    ),
    ScientificRuleReference(
        rule_id="rule:phosphorylation_localization",
        domain=KnowledgeRuleDomain.PTM_ASSUMPTION,
        title="Phosphorylation localization rule",
        rule_statement="Any phosphorylation claim must preserve localization-confidence evidence and PSI-MOD grounded PTM labels instead of collapsing ambiguous sites into unqualified protein conclusions.",
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        benchmark_rationale="The PTM fixture suite is only useful if ambiguous localization remains distinguishable from confidently localized phosphorylation sites.",
        related_term_ids=("ptm:phosphorylation",),
    ),
    ScientificRuleReference(
        rule_id="rule:tmtpro_channel_interpretation",
        domain=KnowledgeRuleDomain.LABEL_CHEMISTRY,
        title="TMTpro channel interpretation rule",
        rule_statement="Multiplex claims must retain TMTpro reporter-channel assumptions and avoid treating channel-level summaries as label-free abundance evidence.",
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
        citation_ids=("citation:target_decoy_2007", "citation:protein_inference_2012"),
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        benchmark_rationale="Adapter-normalized search outputs can only support reliable FDR claims when the asserted scope remains explicit across evidence rollups.",
        related_term_ids=(),
    ),
    ScientificRuleReference(
        rule_id="rule:protein_inference_rollup",
        domain=KnowledgeRuleDomain.INFERENCE_CAUTION,
        title="Protein inference rollup caution",
        rule_statement="Protein-level summaries must remain explicitly qualified when peptide evidence is shared, sparse, or transition-derived rather than directly protein-specific.",
        citation_ids=("citation:protein_inference_2012", "citation:swath_2012"),
        benchmark_ids=(
            "benchmark:targeted_transition_quality_control",
            "benchmark:dia_library_extraction_consistency",
        ),
        benchmark_rationale="Targeted and DIA evidence both encourage early rollup, so the benchmark layer needs an explicit caution mapping for shared-peptide and transition-derived ambiguity.",
        related_term_ids=("acquisition_mode:dia",),
    ),
)


__all__ = [
    "DEFAULT_SCIENTIFIC_RULE_REFERENCES",
    "KnowledgeRuleDomain",
    "ScientificRuleReference",
]
