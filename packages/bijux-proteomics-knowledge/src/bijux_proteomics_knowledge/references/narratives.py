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
    version_trace: tuple[str, ...] = Field(..., min_length=1)
    retrieval_trace: tuple[str, ...] = Field(..., min_length=1)
    benchmark_ids: tuple[str, ...] = Field(..., min_length=1)
    citation_ids: tuple[str, ...] = Field(..., min_length=1)
    context_ids: tuple[str, ...] = Field(default_factory=tuple)
    problem_ids: tuple[str, ...] = Field(default_factory=tuple)
    scope_limit_notes: tuple[str, ...] = Field(..., min_length=1)

    @field_validator(
        "benchmark_ids",
        "citation_ids",
        "version_trace",
        "retrieval_trace",
        "context_ids",
        "problem_ids",
        "scope_limit_notes",
    )
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
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        citation_ids=("citation:target_decoy_2007", "citation:uniprot_2025"),
        context_ids=(
            "context:digestion_tryptic_specificity",
            "context:digestion_protease_comparability",
            "context:digestion_panel_scope",
            "context:fdr_scope_boundary",
        ),
        problem_ids=(
            "problem:search_adapter_fixture_overconfidence",
            "problem:protease_panel_equivalence_shortcut",
            "problem:fdr_scope_overclaim",
        ),
        scope_limit_notes=(
            "Applies to adapter-normalized DDA search outputs in the bundled fixture corpus, not arbitrary production exports.",
            "Preserves peptide-spectrum confidence framing and reviewed-proteome grounding, but does not widen the claim to protein certainty by itself.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:dda_limitation",
        workflow_family=KnowledgeWorkflowFamily.DDA,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from DDA adapter benchmarks",
        narrative_text="The suite cannot claim that clean fixture-level DDA normalization proves production-scale search exports are equally complete, equally comparable across proteases, or equally safe to roll up into protein certainty without additional review.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:dda_search_reproducibility",),
        citation_ids=("citation:target_decoy_2007", "citation:protein_inference_2012"),
        context_ids=(
            "context:digestion_protease_comparability",
            "context:digestion_panel_scope",
            "context:fdr_scope_boundary",
        ),
        problem_ids=(
            "problem:search_adapter_fixture_overconfidence",
            "problem:protease_panel_equivalence_shortcut",
            "problem:fdr_scope_overclaim",
        ),
        scope_limit_notes=(
            "Does not cover protease-mixed production cohorts beyond the curated fixture suite.",
            "Does not justify unqualified protein certainty when peptide evidence remains shared or sparse.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:dia_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.DIA,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from DIA extraction benchmarks",
        narrative_text="The suite can claim that supported DIA adapter outputs preserve acquisition semantics, library-conditioned transition evidence, and peptide-centric extraction framing across the shared benchmark corpus.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        citation_ids=("citation:swath_2012", "citation:psi_ms_cv_2012"),
        context_ids=(
            "context:dia_transition_grounding",
            "context:dia_library_scope",
            "context:dia_library_transfer_boundary",
        ),
        problem_ids=(
            "problem:search_adapter_fixture_overconfidence",
            "problem:targeted_rollup_shortcut",
            "problem:dia_library_transfer_overclaim",
        ),
        scope_limit_notes=(
            "Applies to library-conditioned extraction semantics in the benchmarked fixture corpus, not open-ended biological absence claims.",
            "Keeps transition-aligned peptide evidence in scope without promoting it to direct protein confirmation.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:dia_limitation",
        workflow_family=KnowledgeWorkflowFamily.DIA,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from DIA extraction benchmarks",
        narrative_text="The suite cannot claim that DIA transition evidence is direct protein confirmation, nor that absence from a library-conditioned extraction surface proves biological absence beyond the scope of the benchmarked library context.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        citation_ids=("citation:swath_2012", "citation:protein_inference_2012"),
        context_ids=(
            "context:dia_transition_grounding",
            "context:dia_library_scope",
            "context:dia_library_transfer_boundary",
        ),
        problem_ids=(
            "problem:targeted_rollup_shortcut",
            "problem:dia_library_transfer_overclaim",
        ),
        scope_limit_notes=(
            "Does not claim that missing extraction proves biological absence outside the benchmarked library context.",
            "Does not widen transition evidence into unqualified protein-level certainty.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:ptm_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.PTM,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from PTM localization benchmarks",
        narrative_text="The suite can claim that supported PTM outputs preserve phosphorylation concept grounding and site-localization confidence semantics strongly enough to distinguish localized evidence from merely modified peptide evidence.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
        context_ids=(
            "context:ptm_localization_confidence",
            "context:ptm_occupancy_scope",
            "context:ptm_regulation_boundary",
        ),
        problem_ids=("problem:ptm_regulation_overclaim",),
        scope_limit_notes=(
            "Applies to phosphorylation concept grounding and localization confidence in the curated PTM fixtures.",
            "Distinguishes localized evidence from merely modified peptide evidence without claiming occupancy or regulation breadth.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:ptm_limitation",
        workflow_family=KnowledgeWorkflowFamily.PTM,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from PTM localization benchmarks",
        narrative_text="The suite cannot claim stoichiometric PTM occupancy, broad condition-specific regulation, or fully resolved site certainty when the benchmark only establishes localization confidence over a bundled fixture surface.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        citation_ids=("citation:psi_mod_2008", "citation:ascore_2006"),
        context_ids=(
            "context:ptm_occupancy_scope",
            "context:ptm_regulation_boundary",
        ),
        problem_ids=("problem:ptm_regulation_overclaim",),
        scope_limit_notes=(
            "Does not claim stoichiometric occupancy or broad condition-specific regulation from localization fixtures alone.",
            "Does not erase ambiguous-site handling when the benchmark only establishes localization confidence.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:lfq_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.LFQ,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from LFQ repeatability benchmarks",
        narrative_text="The suite can claim that supported LFQ workflows preserve study-design semantics and repeatable protein-quantity summaries across the bundled quantification corpus when missingness and rollup level remain explicit.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:lfq_quantification_repeatability",),
        citation_ids=("citation:uniprot_2025", "citation:protein_inference_2012"),
        context_ids=(
            "context:quant_missingness_is_informative",
            "context:quant_rollup_changes_claim_scope",
            "context:multiplex_reporter_interference",
            "context:study_design_contrast_scope",
        ),
        problem_ids=(
            "problem:quant_fixture_missingness_shortcut",
            "problem:multiplex_interference_shortcut",
            "problem:design_contrast_overclaim",
        ),
        scope_limit_notes=(
            "Applies to repeatable LFQ behavior in the bundled study-scale fixtures, not every broader cohort shape.",
            "Keeps missingness and rollup level explicit instead of treating protein summaries as scope-free abundance truth.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:lfq_limitation",
        workflow_family=KnowledgeWorkflowFamily.LFQ,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from LFQ repeatability benchmarks",
        narrative_text="The suite cannot claim that repeatable LFQ fixture behavior removes missingness, interference, or peptide-to-protein rollup ambiguity in broader experimental cohorts.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:lfq_quantification_repeatability",),
        citation_ids=("citation:protein_inference_2012",),
        context_ids=(
            "context:quant_missingness_is_informative",
            "context:study_design_contrast_scope",
        ),
        problem_ids=(
            "problem:quant_fixture_missingness_shortcut",
            "problem:design_contrast_overclaim",
        ),
        scope_limit_notes=(
            "Does not claim that repeatable fixture behavior removes missingness, interference, or peptide-to-protein ambiguity.",
            "Does not widen study-scale fixture stability into universal cohort readiness.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:multiplex_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from multiplex quantification benchmarks",
        narrative_text="The suite can claim that supported multiplex outputs preserve reporter-channel semantics and explicit TMTpro label-chemistry assumptions across the bundled benchmark fixtures.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:multiplex_tmtpro_quantification",),
        citation_ids=("citation:tmtpro_2020",),
        context_ids=(
            "context:quant_missingness_is_informative",
            "context:quant_rollup_changes_claim_scope",
            "context:multiplex_reporter_interference",
            "context:study_design_contrast_scope",
        ),
        problem_ids=(
            "problem:quant_fixture_missingness_shortcut",
            "problem:multiplex_interference_shortcut",
            "problem:design_contrast_overclaim",
        ),
        scope_limit_notes=(
            "Applies to bundled multiplex fixtures with explicit TMTpro channel semantics, not label-free abundance interpretation.",
            "Keeps reporter-channel meaning in scope without widening the claim to every multiplex interference pattern.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:multiplex_limitation",
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from multiplex quantification benchmarks",
        narrative_text="The suite cannot claim that reporter-channel summaries are interchangeable with label-free abundance evidence, nor that fixture-level multiplex stability erases interference and rollup caveats.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:multiplex_tmtpro_quantification",),
        citation_ids=("citation:tmtpro_2020", "citation:protein_inference_2012"),
        context_ids=(
            "context:quant_rollup_changes_claim_scope",
            "context:multiplex_reporter_interference",
            "context:study_design_contrast_scope",
        ),
        problem_ids=(
            "problem:quant_fixture_missingness_shortcut",
            "problem:multiplex_interference_shortcut",
            "problem:design_contrast_overclaim",
        ),
        scope_limit_notes=(
            "Does not claim that reporter summaries are interchangeable with label-free abundance evidence.",
            "Does not erase interference and rollup caveats just because the fixture outputs stay stable.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:targeted_evidence_claim",
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
        narrative_kind=WorkflowNarrativeKind.EVIDENCE_CLAIM,
        title="What the suite can claim from targeted transition benchmarks",
        narrative_text="The suite can claim that supported targeted-style summaries preserve transition-level evidence and keep protein-level rollup caution visible during QC-oriented operational interpretation.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:targeted_transition_quality_control",),
        citation_ids=("citation:protein_inference_2012", "citation:swath_2012"),
        context_ids=(
            "context:quant_rollup_changes_claim_scope",
            "context:targeted_assay_transfer_scope",
        ),
        problem_ids=(
            "problem:targeted_rollup_shortcut",
            "problem:targeted_assay_transfer_shortcut",
        ),
        scope_limit_notes=(
            "Applies to targeted-style QC interpretation of bundled chromatogram fixtures, not unrestricted protein confirmation.",
            "Keeps transition-level evidence visible before any cautious protein rollup happens downstream.",
        ),
    ),
    WorkflowNarrative(
        narrative_id="narrative:targeted_limitation",
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
        narrative_kind=WorkflowNarrativeKind.LIMITATION,
        title="What the suite cannot honestly claim from targeted transition benchmarks",
        narrative_text="The suite cannot claim that transition-level targeted evidence alone resolves shared-peptide ambiguity or justifies unqualified protein certainty without explicit inference caution.",
        version_trace=("Narrative wording was reviewed against the linked benchmark and reference surfaces on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, citation ids, context ids, and problem ids were re-verified on 2026-05-05.",),
        benchmark_ids=("benchmark:targeted_transition_quality_control",),
        citation_ids=("citation:protein_inference_2012",),
        context_ids=(
            "context:quant_rollup_changes_claim_scope",
            "context:targeted_assay_transfer_scope",
        ),
        problem_ids=(
            "problem:targeted_rollup_shortcut",
            "problem:targeted_assay_transfer_shortcut",
        ),
        scope_limit_notes=(
            "Does not claim that transition-level targeted evidence alone resolves shared-peptide ambiguity.",
            "Does not justify unqualified protein certainty without explicit inference caution.",
        ),
    ),
)


__all__ = [
    "DEFAULT_WORKFLOW_NARRATIVES",
    "WorkflowNarrative",
    "WorkflowNarrativeKind",
]
