# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated known-problem registries for misleading corpora and shortcuts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


class KnowledgeProblemKind(StrEnum):
    """Problem categories tracked by the knowledge package."""

    MISLEADING_TOY_CORPUS = "misleading_toy_corpus"
    WEAK_BENCHMARK_SHORTCUT = "weak_benchmark_shortcut"


class KnownProblemRegistryEntry(JsonModel):
    """One curated problem entry with explicit mitigation guidance."""

    model_config = ConfigDict(extra="forbid")

    problem_id: str = Field(..., min_length=1)
    problem_kind: KnowledgeProblemKind
    title: str = Field(..., min_length=1)
    problem_summary: str = Field(..., min_length=1)
    mitigation_guidance: str = Field(..., min_length=1)
    version_trace: tuple[str, ...] = Field(..., min_length=1)
    retrieval_trace: tuple[str, ...] = Field(..., min_length=1)
    affected_workflow_families: tuple[KnowledgeWorkflowFamily, ...] = Field(
        ..., min_length=1
    )
    affected_corpus_ids: tuple[str, ...] = Field(default_factory=tuple)
    affected_benchmark_ids: tuple[str, ...] = Field(default_factory=tuple)
    citation_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator(
        "affected_corpus_ids",
        "affected_benchmark_ids",
        "citation_ids",
        "version_trace",
        "retrieval_trace",
    )
    @classmethod
    def _strip_blank_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if value and not cleaned:
            raise ValueError("tuple fields must not contain only blank values")
        return cleaned


DEFAULT_KNOWN_PROBLEM_REGISTRY: tuple[KnownProblemRegistryEntry, ...] = (
    KnownProblemRegistryEntry(
        problem_id="problem:search_adapter_fixture_overconfidence",
        problem_kind=KnowledgeProblemKind.MISLEADING_TOY_CORPUS,
        title="Search-adapter fixtures can look cleaner than production exports",
        problem_summary="Bundled adapter fixtures are intentionally reviewable and can under-represent messy missing metadata, inconsistent scoring, and mixed search-space assumptions found in production DDA or DIA exports.",
        mitigation_guidance="Treat the fixture suite as a normalization proof, not as evidence that production-scale adapter inputs are equally complete or equally well-behaved.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(
            KnowledgeWorkflowFamily.DDA,
            KnowledgeWorkflowFamily.DIA,
        ),
        affected_corpus_ids=("corpus:search_adapter_fixture_suite",),
        affected_benchmark_ids=(
            "benchmark:dda_search_reproducibility",
            "benchmark:dia_library_extraction_consistency",
        ),
        citation_ids=("citation:target_decoy_2007", "citation:swath_2012"),
    ),
    KnownProblemRegistryEntry(
        problem_id="problem:protease_panel_equivalence_shortcut",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="Clean protease panels can be mistaken for cross-protease equivalence",
        problem_summary="A benchmark that normalizes more than one protease-shaped export can still leave peptide detectability and downstream rollup meaning protease-dependent.",
        mitigation_guidance="Keep protease-specific detectability and rollup caveats attached whenever DDA summaries compare tryptic and LysC-style evidence.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(KnowledgeWorkflowFamily.DDA,),
        affected_corpus_ids=("corpus:search_adapter_fixture_suite",),
        affected_benchmark_ids=("benchmark:dda_search_reproducibility",),
        citation_ids=("citation:uniprot_2025", "citation:protein_inference_2012"),
    ),
    KnownProblemRegistryEntry(
        problem_id="problem:ptm_regulation_overclaim",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="Localized PTM evidence can be over-read as regulation",
        problem_summary="A localized phosphosite can sound biologically decisive even when the benchmark only establishes concept grounding and localization confidence rather than occupancy or regulation.",
        mitigation_guidance="Require explicit regulation or occupancy support before turning localized PTM evidence into broader biological claims.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(KnowledgeWorkflowFamily.PTM,),
        affected_corpus_ids=("corpus:ptm_fixture_suite",),
        affected_benchmark_ids=("benchmark:ptm_site_localization_confidence",),
        citation_ids=(
            "citation:psi_mod_2008",
            "citation:ascore_2006",
            "citation:protein_inference_2012",
        ),
    ),
    KnownProblemRegistryEntry(
        problem_id="problem:fdr_scope_overclaim",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="Target-decoy confidence can be over-read across evidence levels",
        problem_summary="A stable target-decoy surface at the peptide-spectrum or peptide level can still be over-interpreted as protein-level certainty when rollup scope is left implicit.",
        mitigation_guidance="Keep peptide-spectrum, peptide, and protein confidence scopes explicit whenever DDA summaries move beyond the exact evidence level benchmarked.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(KnowledgeWorkflowFamily.DDA,),
        affected_corpus_ids=(
            "corpus:search_adapter_fixture_suite",
            "corpus:target_decoy_method_reference",
        ),
        affected_benchmark_ids=("benchmark:dda_search_reproducibility",),
        citation_ids=("citation:target_decoy_2007", "citation:protein_inference_2012"),
    ),
    KnownProblemRegistryEntry(
        problem_id="problem:quant_fixture_missingness_shortcut",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="Quantification fixtures can hide missingness pain",
        problem_summary="Study-scale LFQ and multiplex fixtures are useful for repeatability checks, but they can make quantitative missingness and interference look easier to manage than in broader experimental cohorts.",
        mitigation_guidance="Keep missingness, interference, and rollup caveats attached to any benchmark-backed quantification claim rather than treating repeatable fixture behavior as universal.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(
            KnowledgeWorkflowFamily.LFQ,
            KnowledgeWorkflowFamily.MULTIPLEX,
        ),
        affected_corpus_ids=("corpus:quant_fixture_suite",),
        affected_benchmark_ids=(
            "benchmark:lfq_quantification_repeatability",
            "benchmark:multiplex_tmtpro_quantification",
        ),
        citation_ids=("citation:tmtpro_2020", "citation:protein_inference_2012"),
    ),
    KnownProblemRegistryEntry(
        problem_id="problem:multiplex_interference_shortcut",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="Stable reporter ratios can hide multiplex interference",
        problem_summary="A clean multiplex fixture can make reporter-channel summaries look more portable than they really are when co-isolation, ratio compression, or channel imbalance are muted by the fixture shape.",
        mitigation_guidance="Keep reporter interference, channel imbalance, and rollup caveats attached whenever multiplex outputs are summarized beyond the exact benchmarked fixture scope.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(KnowledgeWorkflowFamily.MULTIPLEX,),
        affected_corpus_ids=(
            "corpus:quant_fixture_suite",
            "corpus:tmtpro_labeling_reference",
        ),
        affected_benchmark_ids=("benchmark:multiplex_tmtpro_quantification",),
        citation_ids=("citation:tmtpro_2020", "citation:protein_inference_2012"),
    ),
    KnownProblemRegistryEntry(
        problem_id="problem:targeted_rollup_shortcut",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="Transition-level evidence can be over-rolled into protein certainty",
        problem_summary="Targeted and DIA-style evidence often encourages fast protein-level summaries even when the underlying support remains transition-level, peptide-level, or library-conditioned.",
        mitigation_guidance="Require explicit protein-inference caution whenever transition-level or peptide-centric evidence is rolled up into protein-facing operational recommendations.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(
            KnowledgeWorkflowFamily.DIA,
            KnowledgeWorkflowFamily.TARGETED,
        ),
        affected_corpus_ids=(
            "corpus:chromatogram_qc_fixture",
            "corpus:swath_method_reference",
        ),
        affected_benchmark_ids=(
            "benchmark:dia_library_extraction_consistency",
            "benchmark:targeted_transition_quality_control",
        ),
        citation_ids=("citation:protein_inference_2012", "citation:swath_2012"),
    ),
    KnownProblemRegistryEntry(
        problem_id="problem:dia_library_transfer_overclaim",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="Library-conditioned DIA consistency can be over-generalized",
        problem_summary="A reproducible DIA extraction surface can still depend on one library shape and one transfer pattern more heavily than a downstream review packet makes obvious.",
        mitigation_guidance="Keep library composition, transition compatibility, and peptide-centric scope explicit before turning one stable DIA extraction benchmark into broader protein-facing portability claims.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(KnowledgeWorkflowFamily.DIA,),
        affected_corpus_ids=(
            "corpus:search_adapter_fixture_suite",
            "corpus:swath_method_reference",
        ),
        affected_benchmark_ids=("benchmark:dia_library_extraction_consistency",),
        citation_ids=(
            "citation:swath_2012",
            "citation:psi_ms_cv_2012",
            "citation:protein_inference_2012",
        ),
    ),
    KnownProblemRegistryEntry(
        problem_id="problem:design_contrast_overclaim",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="One benchmarked design contrast can be over-generalized",
        problem_summary="Repeatable quantitative behavior in one study design can be mistaken for broad cohort readiness even when the benchmark only represents one contrast structure and one balance pattern.",
        mitigation_guidance="Keep study-design scope and contrast structure explicit before carrying LFQ or multiplex summaries into broader cohort-facing claims.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(
            KnowledgeWorkflowFamily.LFQ,
            KnowledgeWorkflowFamily.MULTIPLEX,
        ),
        affected_corpus_ids=("corpus:quant_fixture_suite",),
        affected_benchmark_ids=(
            "benchmark:lfq_quantification_repeatability",
            "benchmark:multiplex_tmtpro_quantification",
        ),
        citation_ids=(
            "citation:uniprot_2025",
            "citation:protein_inference_2012",
            "citation:tmtpro_2020",
        ),
    ),
    KnownProblemRegistryEntry(
        problem_id="problem:targeted_assay_transfer_shortcut",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="One stable targeted panel can be mistaken for broad assay portability",
        problem_summary="A clean targeted QC panel can look universally trustworthy even when the benchmark only demonstrates one transition set, one assay design, and one matrix-facing behavior.",
        mitigation_guidance="Keep assay-panel scope, transition coverage, and protein-rollup caution explicit before carrying targeted QC stability into broader assay-readiness claims.",
        version_trace=(
            "Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",
        ),
        retrieval_trace=(
            "The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",
        ),
        affected_workflow_families=(KnowledgeWorkflowFamily.TARGETED,),
        affected_corpus_ids=(
            "corpus:chromatogram_qc_fixture",
            "corpus:protein_inference_review_reference",
        ),
        affected_benchmark_ids=("benchmark:targeted_transition_quality_control",),
        citation_ids=("citation:protein_inference_2012", "citation:swath_2012"),
    ),
)


__all__ = [
    "DEFAULT_KNOWN_PROBLEM_REGISTRY",
    "KnowledgeProblemKind",
    "KnownProblemRegistryEntry",
]
