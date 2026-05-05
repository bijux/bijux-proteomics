# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated scientific context entries for shared proteomics interpretation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.json_models import JsonModel


class KnowledgeContextDomain(StrEnum):
    """Scientific context families curated by the knowledge package."""

    DIGESTION_CLEAVAGE = "digestion_cleavage"
    PTM_LOCALIZATION = "ptm_localization"
    DIA_SPECTRAL_LIBRARY = "dia_spectral_library"
    QUANTIFICATION_INTERPRETATION = "quantification_interpretation"


class ScientificContextEntry(JsonModel):
    """One curated scientific context entry with explicit provenance."""

    model_config = ConfigDict(extra="forbid")

    context_id: str = Field(..., min_length=1)
    domain: KnowledgeContextDomain
    title: str = Field(..., min_length=1)
    scientific_assertion: str = Field(..., min_length=1)
    interpretation_caveat: str = Field(..., min_length=1)
    citation_ids: tuple[str, ...] = Field(..., min_length=1)
    benchmark_ids: tuple[str, ...] = Field(..., min_length=1)
    related_rule_ids: tuple[str, ...] = Field(default_factory=tuple)
    related_term_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator(
        "citation_ids",
        "benchmark_ids",
        "related_rule_ids",
        "related_term_ids",
    )
    @classmethod
    def _strip_blank_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if value and not cleaned:
            raise ValueError("tuple fields must not contain only blank values")
        return cleaned


DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES: tuple[ScientificContextEntry, ...] = (
    ScientificContextEntry(
        context_id="context:digestion_tryptic_specificity",
        domain=KnowledgeContextDomain.DIGESTION_CLEAVAGE,
        title="Tryptic specificity expectation",
        scientific_assertion="Search, peptide rollup, and benchmark claims that assume tryptic digestion should preserve the expected lysine and arginine cleavage frame rather than treating all peptide evidence as digestion-agnostic.",
        interpretation_caveat="Missed cleavages, semi-tryptic evidence, and alternative proteases can be real, but they must remain explicit because they change how confidently peptide-level evidence maps back to the benchmark contract.",
        citation_ids=("citation:uniprot_2025",),
        benchmark_ids=(
            "benchmark:dda_search_reproducibility",
            "benchmark:lfq_quantification_repeatability",
        ),
        related_rule_ids=("rule:trypsin_specificity",),
        related_term_ids=("enzyme:trypsin", "enzyme:lysc"),
    ),
    ScientificContextEntry(
        context_id="context:digestion_protease_comparability",
        domain=KnowledgeContextDomain.DIGESTION_CLEAVAGE,
        title="Protease comparability caveat",
        scientific_assertion="Benchmark comparisons across proteases remain interpretable only when cleavage expectations and peptide detectability differences are kept visible instead of being collapsed into one merged identification claim.",
        interpretation_caveat="A LysC-supported peptide panel is not automatically interchangeable with a tryptic panel, so workflow summaries should avoid claiming cross-protease equivalence without explicit comparability evidence.",
        citation_ids=("citation:uniprot_2025",),
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        related_rule_ids=("rule:trypsin_specificity",),
        related_term_ids=("enzyme:trypsin", "enzyme:lysc"),
    ),
    ScientificContextEntry(
        context_id="context:ptm_localization_confidence",
        domain=KnowledgeContextDomain.PTM_LOCALIZATION,
        title="PTM localization confidence must stay explicit",
        scientific_assertion="Phosphorylation evidence should carry localization-confidence semantics alongside the PTM concept so that the suite can distinguish confidently localized sites from merely modified peptides.",
        interpretation_caveat="A peptide can support the presence of phosphorylation while still failing to support one exact residue assignment, and benchmark-backed outputs should preserve that distinction.",
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        related_rule_ids=("rule:phosphorylation_localization",),
        related_term_ids=("ptm:phosphorylation",),
    ),
    ScientificContextEntry(
        context_id="context:ptm_occupancy_scope",
        domain=KnowledgeContextDomain.PTM_LOCALIZATION,
        title="PTM occupancy is not implied by localization alone",
        scientific_assertion="Site localization evidence and occupancy-style abundance interpretation are related but not interchangeable, so PTM outputs should not imply stoichiometric occupancy when the benchmark only establishes localization confidence.",
        interpretation_caveat="A localized phosphosite can still have weak quantitative support for occupancy or condition-specific change, and that uncertainty should survive downstream interpretation.",
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        related_rule_ids=("rule:phosphorylation_localization",),
        related_term_ids=("ptm:phosphorylation",),
    ),
    ScientificContextEntry(
        context_id="context:dia_transition_grounding",
        domain=KnowledgeContextDomain.DIA_SPECTRAL_LIBRARY,
        title="DIA transition evidence stays peptide-centric",
        scientific_assertion="DIA and SWATH-style extraction claims are most defensible when transition-level and peptide-centric evidence remain visible instead of being treated as direct protein confirmation.",
        interpretation_caveat="Transition alignment and extracted-ion consistency are useful, but they are not a substitute for making the peptide-to-protein inference step explicit.",
        citation_ids=("citation:swath_2012", "citation:psi_ms_cv_2012"),
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        related_rule_ids=("rule:protein_inference_rollup",),
        related_term_ids=("acquisition_mode:dia",),
    ),
    ScientificContextEntry(
        context_id="context:dia_library_scope",
        domain=KnowledgeContextDomain.DIA_SPECTRAL_LIBRARY,
        title="Spectral-library scope constrains DIA claims",
        scientific_assertion="DIA benchmark outputs should keep library scope explicit because identifications and quantities are conditioned on the peptides and transitions represented in the library-backed extraction surface.",
        interpretation_caveat="A narrow or mismatched library can make a workflow look cleaner than it really is, so absence of evidence in DIA should not be treated as broad biological absence without scope context.",
        citation_ids=("citation:swath_2012", "citation:psi_ms_cv_2012"),
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        related_rule_ids=("rule:protein_inference_rollup",),
        related_term_ids=("acquisition_mode:dia",),
    ),
    ScientificContextEntry(
        context_id="context:quant_missingness_is_informative",
        domain=KnowledgeContextDomain.QUANTIFICATION_INTERPRETATION,
        title="Quantitative missingness is informative",
        scientific_assertion="Missing values in LFQ and multiplex-style quantification are not just formatting gaps; they often reflect sampling, detection, or interference constraints that matter to the benchmark claim.",
        interpretation_caveat="Naive imputation or silent dropping of missing values can overstate stability, so workflow summaries should keep the missingness story attached to the quantitative result.",
        citation_ids=("citation:uniprot_2025", "citation:tmtpro_2020"),
        benchmark_ids=(
            "benchmark:lfq_quantification_repeatability",
            "benchmark:multiplex_tmtpro_quantification",
        ),
        related_rule_ids=(),
        related_term_ids=(),
    ),
    ScientificContextEntry(
        context_id="context:quant_rollup_changes_claim_scope",
        domain=KnowledgeContextDomain.QUANTIFICATION_INTERPRETATION,
        title="Quantitative rollup changes the claim scope",
        scientific_assertion="Peptide-level, precursor-level, and protein-level quantitative summaries do not carry identical meaning, so the suite should preserve which rollup level each benchmark-backed claim actually supports.",
        interpretation_caveat="Protein-level summaries can hide conflicting peptide behavior or missingness patterns, and that tradeoff should remain explicit when other packages consume the result.",
        citation_ids=("citation:protein_inference_2012", "citation:tmtpro_2020"),
        benchmark_ids=(
            "benchmark:lfq_quantification_repeatability",
            "benchmark:multiplex_tmtpro_quantification",
            "benchmark:targeted_transition_quality_control",
        ),
        related_rule_ids=("rule:protein_inference_rollup",),
        related_term_ids=(),
    ),
)


__all__ = [
    "DEFAULT_SCIENTIFIC_CONTEXT_ENTRIES",
    "KnowledgeContextDomain",
    "ScientificContextEntry",
]
