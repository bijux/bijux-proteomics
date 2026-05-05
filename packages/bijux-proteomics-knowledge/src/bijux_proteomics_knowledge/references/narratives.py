# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark-backed workflow narratives for claims and limitations."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.json_models import JsonModel

from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily


class WorkflowNarrativeKind(StrEnum):
    """Narrative modes curated by the knowledge package."""

    EVIDENCE_CLAIM = "evidence_claim"
    LIMITATION = "limitation"


class WorkflowNarrative(JsonModel):
    """One benchmark-backed workflow narrative with explicit provenance."""

    model_config = ConfigDict(extra="forbid")

    narrative_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    narrative_kind: WorkflowNarrativeKind
    title: str = Field(..., min_length=1)
    narrative_text: str = Field(..., min_length=1)
    benchmark_ids: tuple[str, ...] = Field(..., min_length=1)
    citation_ids: tuple[str, ...] = Field(..., min_length=1)
    context_ids: tuple[str, ...] = Field(default_factory=tuple)
    problem_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("benchmark_ids", "citation_ids", "context_ids", "problem_ids")
    @classmethod
    def _strip_blank_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if value and not cleaned:
            raise ValueError("tuple fields must not contain only blank values")
        return cleaned


DEFAULT_WORKFLOW_NARRATIVES: tuple[WorkflowNarrative, ...] = (
    WorkflowNarrative(
        narrative_id="narrative:dda_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.DDA,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from DDA adapter benchmarks",
        narrative_text="The suite can claim that adapter-normalized DDA search outputs preserve peptide-spectrum match confidence framing, reviewed-proteome grounding, and cleavage-aware interpretation across the supported fixture corpus.",
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        citation_ids=("citation:target_decoy_2007", "citation:uniprot_2025"),
        context_ids=(
            "context:digestion_tryptic_specificity",
            "context:digestion_protease_comparability",
        ),
        problem_ids=("problem:search_adapter_fixture_overconfidence",),
    ),
    WorkflowNarrative(
        narrative_id="narrative:dda_limitation",
        workflow_family=KnowledgeWorkflowFamily.DDA,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from DDA adapter benchmarks",
        narrative_text="The suite cannot claim that clean fixture-level DDA normalization proves production-scale search exports are equally complete, equally comparable across proteases, or equally safe to roll up into protein certainty without additional review.",
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        citation_ids=("citation:target_decoy_2007", "citation:protein_inference_2012"),
        context_ids=("context:digestion_protease_comparability",),
        problem_ids=("problem:search_adapter_fixture_overconfidence",),
    ),
    WorkflowNarrative(
        narrative_id="narrative:dia_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.DIA,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from DIA extraction benchmarks",
        narrative_text="The suite can claim that supported DIA adapter outputs preserve acquisition semantics, library-conditioned transition evidence, and peptide-centric extraction framing across the shared benchmark corpus.",
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        citation_ids=("citation:swath_2012", "citation:psi_ms_cv_2012"),
        context_ids=(
            "context:dia_transition_grounding",
            "context:dia_library_scope",
        ),
        problem_ids=(
            "problem:search_adapter_fixture_overconfidence",
            "problem:targeted_rollup_shortcut",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:dia_limitation",
        workflow_family=KnowledgeWorkflowFamily.DIA,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from DIA extraction benchmarks",
        narrative_text="The suite cannot claim that DIA transition evidence is direct protein confirmation, nor that absence from a library-conditioned extraction surface proves biological absence beyond the scope of the benchmarked library context.",
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        citation_ids=("citation:swath_2012", "citation:protein_inference_2012"),
        context_ids=(
            "context:dia_transition_grounding",
            "context:dia_library_scope",
        ),
        problem_ids=("problem:targeted_rollup_shortcut",),
    ),
    WorkflowNarrative(
        narrative_id="narrative:ptm_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.PTM,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from PTM localization benchmarks",
        narrative_text="The suite can claim that supported PTM outputs preserve phosphorylation concept grounding and site-localization confidence semantics strongly enough to distinguish localized evidence from merely modified peptide evidence.",
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
        context_ids=(
            "context:ptm_localization_confidence",
            "context:ptm_occupancy_scope",
        ),
        problem_ids=(),
    ),
    WorkflowNarrative(
        narrative_id="narrative:ptm_limitation",
        workflow_family=KnowledgeWorkflowFamily.PTM,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from PTM localization benchmarks",
        narrative_text="The suite cannot claim stoichiometric PTM occupancy, broad condition-specific regulation, or fully resolved site certainty when the benchmark only establishes localization confidence over a bundled fixture surface.",
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
        context_ids=("context:ptm_occupancy_scope",),
        problem_ids=(),
    ),
    WorkflowNarrative(
        narrative_id="narrative:lfq_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.LFQ,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from LFQ repeatability benchmarks",
        narrative_text="The suite can claim that supported LFQ workflows preserve study-design semantics and repeatable protein-quantity summaries across the bundled quantification corpus when missingness and rollup level remain explicit.",
        benchmark_ids=("benchmark:lfq_quantification_repeatability",),
        citation_ids=("citation:uniprot_2025", "citation:protein_inference_2012"),
        context_ids=(
            "context:quant_missingness_is_informative",
            "context:quant_rollup_changes_claim_scope",
        ),
        problem_ids=("problem:quant_fixture_missingness_shortcut",),
    ),
    WorkflowNarrative(
        narrative_id="narrative:lfq_limitation",
        workflow_family=KnowledgeWorkflowFamily.LFQ,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from LFQ repeatability benchmarks",
        narrative_text="The suite cannot claim that repeatable LFQ fixture behavior removes missingness, interference, or peptide-to-protein rollup ambiguity in broader experimental cohorts.",
        benchmark_ids=("benchmark:lfq_quantification_repeatability",),
        citation_ids=("citation:protein_inference_2012",),
        context_ids=("context:quant_missingness_is_informative",),
        problem_ids=("problem:quant_fixture_missingness_shortcut",),
    ),
    WorkflowNarrative(
        narrative_id="narrative:multiplex_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from multiplex quantification benchmarks",
        narrative_text="The suite can claim that supported multiplex outputs preserve reporter-channel semantics and explicit TMTpro label-chemistry assumptions across the bundled benchmark fixtures.",
        benchmark_ids=("benchmark:multiplex_tmtpro_quantification",),
        citation_ids=("citation:tmtpro_2020",),
        context_ids=(
            "context:quant_missingness_is_informative",
            "context:quant_rollup_changes_claim_scope",
        ),
        problem_ids=("problem:quant_fixture_missingness_shortcut",),
    ),
    WorkflowNarrative(
        narrative_id="narrative:multiplex_limitation",
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from multiplex quantification benchmarks",
        narrative_text="The suite cannot claim that reporter-channel summaries are interchangeable with label-free abundance evidence, nor that fixture-level multiplex stability erases interference and rollup caveats.",
        benchmark_ids=("benchmark:multiplex_tmtpro_quantification",),
        citation_ids=("citation:tmtpro_2020", "citation:protein_inference_2012"),
        context_ids=("context:quant_rollup_changes_claim_scope",),
        problem_ids=("problem:quant_fixture_missingness_shortcut",),
    ),
    WorkflowNarrative(
        narrative_id="narrative:targeted_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from targeted transition benchmarks",
        narrative_text="The suite can claim that supported targeted-style summaries preserve transition-level evidence and keep protein-level rollup caution visible during QC-oriented operational interpretation.",
        benchmark_ids=("benchmark:targeted_transition_quality_control",),
        citation_ids=("citation:protein_inference_2012", "citation:swath_2012"),
        context_ids=("context:quant_rollup_changes_claim_scope",),
        problem_ids=("problem:targeted_rollup_shortcut",),
    ),
    WorkflowNarrative(
        narrative_id="narrative:targeted_limitation",
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from targeted transition benchmarks",
        narrative_text="The suite cannot claim that transition-level targeted evidence alone resolves shared-peptide ambiguity or justifies unqualified protein certainty without explicit inference caution.",
        benchmark_ids=("benchmark:targeted_transition_quality_control",),
        citation_ids=("citation:protein_inference_2012",),
        context_ids=("context:quant_rollup_changes_claim_scope",),
        problem_ids=("problem:targeted_rollup_shortcut",),
    ),
)


__all__ = [
    "DEFAULT_WORKFLOW_NARRATIVES",
    "WorkflowNarrative",
    "WorkflowNarrativeKind",
]
