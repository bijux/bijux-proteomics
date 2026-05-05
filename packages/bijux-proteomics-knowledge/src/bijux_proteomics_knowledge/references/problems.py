# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated known-problem registries for misleading corpora and shortcuts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.json_models import JsonModel

from bijux_proteomics_knowledge.references.benchmarks import KnowledgeWorkflowFamily


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
        version_trace=("Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",),
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
        problem_id="problem:quant_fixture_missingness_shortcut",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="Quantification fixtures can hide missingness pain",
        problem_summary="Study-scale LFQ and multiplex fixtures are useful for repeatability checks, but they can make quantitative missingness and interference look easier to manage than in broader experimental cohorts.",
        mitigation_guidance="Keep missingness, interference, and rollup caveats attached to any benchmark-backed quantification claim rather than treating repeatable fixture behavior as universal.",
        version_trace=("Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",),
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
        problem_id="problem:targeted_rollup_shortcut",
        problem_kind=KnowledgeProblemKind.WEAK_BENCHMARK_SHORTCUT,
        title="Transition-level evidence can be over-rolled into protein certainty",
        problem_summary="Targeted and DIA-style evidence often encourages fast protein-level summaries even when the underlying support remains transition-level, peptide-level, or library-conditioned.",
        mitigation_guidance="Require explicit protein-inference caution whenever transition-level or peptide-centric evidence is rolled up into protein-facing operational recommendations.",
        version_trace=("Problem wording was reviewed against the linked corpora, benchmarks, and citations on 2026-05-05.",),
        retrieval_trace=("The linked benchmark ids, corpus ids, and citation ids were re-verified on 2026-05-05.",),
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
)


__all__ = [
    "DEFAULT_KNOWN_PROBLEM_REGISTRY",
    "KnowledgeProblemKind",
    "KnownProblemRegistryEntry",
]
