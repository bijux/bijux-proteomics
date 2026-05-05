# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated benchmark manifests for shared proteomics workflow families."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.json_models import JsonModel


class KnowledgeWorkflowFamily(StrEnum):
    """Proteomics workflow families covered by curated benchmark manifests."""

    DDA = "dda"
    DIA = "dia"
    PTM = "ptm"
    LFQ = "lfq"
    MULTIPLEX = "multiplex"
    TARGETED = "targeted"


class BenchmarkManifest(JsonModel):
    """One reproducible benchmark contract for a workflow family."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    title: str = Field(..., min_length=1)
    scientific_focus: str = Field(..., min_length=1)
    acquisition_mode: str = Field(..., min_length=1)
    success_metric: str = Field(..., min_length=1)
    result_claim: str = Field(..., min_length=1)
    primary_citation_ids: tuple[str, ...] = Field(..., min_length=1)
    corpus_ids: tuple[str, ...] = Field(..., min_length=1)
    benchmark_rationale: str = Field(..., min_length=1)
    instrument_profiles: tuple[str, ...] = Field(..., min_length=1)
    reproduction_requirements: tuple[str, ...] = Field(..., min_length=1)

    @field_validator(
        "primary_citation_ids",
        "corpus_ids",
        "instrument_profiles",
        "reproduction_requirements",
    )
    @classmethod
    def _forbid_blank_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if not cleaned:
            raise ValueError("at least one non-blank value is required")
        return cleaned


DEFAULT_BENCHMARK_MANIFESTS: tuple[BenchmarkManifest, ...] = (
    BenchmarkManifest(
        benchmark_id="benchmark:dda_search_reproducibility",
        workflow_family=KnowledgeWorkflowFamily.DDA,
        title="DDA search reproducibility benchmark",
        scientific_focus="Peptide-spectrum match reproducibility across search adapter inputs.",
        acquisition_mode="data-dependent acquisition",
        success_metric="Stable peptide and protein identification counts after adapter normalization.",
        result_claim="Adapter-normalized DDA evidence should preserve target-decoy semantics and reviewed-proteome mapping.",
        primary_citation_ids=(
            "citation:target_decoy_2007",
            "citation:uniprot_2025",
        ),
        corpus_ids=(
            "corpus:search_adapter_fixture_suite",
            "corpus:target_decoy_method_reference",
        ),
        benchmark_rationale="The suite compares multiple DDA search outputs, so the manifest must preserve both identification confidence framing and reference-proteome mapping.",
        instrument_profiles=("Orbitrap", "Q Exactive-class DDA"),
        reproduction_requirements=(
            "Normalize search-engine exports through the core adapter fixture corpus.",
            "Validate peptide-spectrum match confidence with target-decoy-oriented outputs.",
            "Map identified proteins against curated UniProt-reviewed records.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:dia_library_extraction_consistency",
        workflow_family=KnowledgeWorkflowFamily.DIA,
        title="DIA extraction consistency benchmark",
        scientific_focus="Consistency of peptide-centric extraction across DIA-style reports.",
        acquisition_mode="data-independent acquisition",
        success_metric="Stable extracted peptide quantities and aligned DIA transition semantics.",
        result_claim="DIA adapters should preserve acquisition semantics, transition alignment, and SWATH-style extraction expectations.",
        primary_citation_ids=(
            "citation:swath_2012",
            "citation:psi_ms_cv_2012",
        ),
        corpus_ids=(
            "corpus:search_adapter_fixture_suite",
            "corpus:swath_method_reference",
        ),
        benchmark_rationale="The knowledge layer needs a curated record of the DIA assumptions that justify spectral-library and transition-based claims downstream.",
        instrument_profiles=("Orbitrap", "timsTOF"),
        reproduction_requirements=(
            "Replay DIA-shaped adapter exports from the shared search-adapter fixture suite.",
            "Preserve DIA acquisition labels and transition-aligned peptide extraction semantics.",
            "Confirm vocabulary normalization against the PSI-MS controlled vocabulary.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:ptm_site_localization_confidence",
        workflow_family=KnowledgeWorkflowFamily.PTM,
        title="PTM site-localization confidence benchmark",
        scientific_focus="Phosphorylation localization confidence and PTM term normalization.",
        acquisition_mode="data-dependent acquisition",
        success_metric="Stable localization confidence assignments with curated PTM term provenance.",
        result_claim="PTM localization outputs should retain both PSI-MOD concept mapping and Ascore-style evidence interpretation.",
        primary_citation_ids=(
            "citation:psi_mod_2008",
            "citation:ascore_2006",
        ),
        corpus_ids=(
            "corpus:ptm_fixture_suite",
            "corpus:ptm_localization_method_reference",
        ),
        benchmark_rationale="PTM features need both ontology grounding and a localization-confidence method reference to keep downstream rule interpretation defensible.",
        instrument_profiles=("Orbitrap",),
        reproduction_requirements=(
            "Use the bundled PTM localization fixture corpus.",
            "Preserve phosphorylation-site localization scores and ambiguous-site handling.",
            "Map modification concepts to PSI-MOD-backed identifiers before emitting conclusions.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:lfq_quantification_repeatability",
        workflow_family=KnowledgeWorkflowFamily.LFQ,
        title="LFQ repeatability benchmark",
        scientific_focus="Label-free quantification repeatability on study-scale fixture inputs.",
        acquisition_mode="data-dependent acquisition",
        success_metric="Consistent protein abundance summaries across repeated LFQ fixture runs.",
        result_claim="Label-free quantification outputs should preserve study design semantics and repeatable abundance rollups.",
        primary_citation_ids=("citation:uniprot_2025",),
        corpus_ids=(
            "corpus:quant_fixture_suite",
            "corpus:uniprot_reference_proteome",
        ),
        benchmark_rationale="The suite uses bundled LFQ fixtures to prove repeatability, but interpretation remains tied to stable reference-proteome identifiers.",
        instrument_profiles=("Orbitrap",),
        reproduction_requirements=(
            "Use the bundled quantification fixture corpus and study-scale design inputs.",
            "Preserve sample-design semantics during quantification aggregation.",
            "Map quantified proteins through curated UniProt-backed identifiers.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:multiplex_tmtpro_quantification",
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX,
        title="Multiplex TMTpro quantification benchmark",
        scientific_focus="Isobaric multiplex assumptions and reporter-channel interpretation.",
        acquisition_mode="data-dependent acquisition",
        success_metric="Stable multiplex abundance outputs with explicit TMTpro chemistry assumptions.",
        result_claim="Multiplex quantification should preserve TMTpro channel semantics and label-chemistry caveats.",
        primary_citation_ids=("citation:tmtpro_2020",),
        corpus_ids=(
            "corpus:quant_fixture_suite",
            "corpus:tmtpro_labeling_reference",
        ),
        benchmark_rationale="Multiplex quantification depends on durable label-chemistry assumptions that need a curated reference surface instead of ad hoc comments.",
        instrument_profiles=("Orbitrap",),
        reproduction_requirements=(
            "Use multiplex design and feature fixtures from the bundled quantification corpus.",
            "Preserve reporter-channel assignments for TMTpro-labeled samples.",
            "Keep label-chemistry assumptions explicit in any downstream interpretation.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:targeted_transition_quality_control",
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
        title="Targeted transition quality-control benchmark",
        scientific_focus="Transition-level quality checks over chromatogram-shaped targeted outputs.",
        acquisition_mode="targeted acquisition",
        success_metric="Stable transition-level QC summaries for bundled chromatogram evidence.",
        result_claim="Targeted-style chromatogram summaries should preserve transition-level evidence and protein-inference caution when rolled up.",
        primary_citation_ids=("citation:protein_inference_2012",),
        corpus_ids=(
            "corpus:chromatogram_qc_fixture",
            "corpus:protein_inference_review_reference",
        ),
        benchmark_rationale="Targeted outputs often collapse transition evidence quickly, so the benchmark captures how much interpretation can safely happen before protein-level rollup.",
        instrument_profiles=("Triple quadrupole", "Orbitrap"),
        reproduction_requirements=(
            "Use the bundled chromatogram QC fixture as the targeted evidence source.",
            "Keep transition-level measures intact before protein-level summary.",
            "Report any protein rollup with explicit inference caution.",
        ),
    ),
)


__all__ = [
    "BenchmarkManifest",
    "DEFAULT_BENCHMARK_MANIFESTS",
    "KnowledgeWorkflowFamily",
]
