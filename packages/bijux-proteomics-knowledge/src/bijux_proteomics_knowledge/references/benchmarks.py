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
    dataset_id: str = Field(..., min_length=1)
    dataset_locator: str = Field(..., min_length=1)
    acquisition_mode: str = Field(..., min_length=1)
    success_metric: str = Field(..., min_length=1)
    result_claim: str = Field(..., min_length=1)
    primary_citation_ids: tuple[str, ...] = Field(..., min_length=1)
    corpus_ids: tuple[str, ...] = Field(..., min_length=1)
    benchmark_rationale: str = Field(..., min_length=1)
    version_trace: tuple[str, ...] = Field(..., min_length=1)
    retrieval_trace: tuple[str, ...] = Field(..., min_length=1)
    dataset_license_and_reuse_note: str = Field(..., min_length=1)
    instrument_profiles: tuple[str, ...] = Field(..., min_length=1)
    reproduction_requirements: tuple[str, ...] = Field(..., min_length=1)
    comparison_notes: tuple[str, ...] = Field(..., min_length=1)
    exclusion_notes: tuple[str, ...] = Field(..., min_length=1)
    weakness_notes: tuple[str, ...] = Field(..., min_length=1)
    failure_mode_notes: tuple[str, ...] = Field(..., min_length=1)

    @field_validator(
        "primary_citation_ids",
        "corpus_ids",
        "version_trace",
        "retrieval_trace",
        "instrument_profiles",
        "reproduction_requirements",
        "comparison_notes",
        "exclusion_notes",
        "weakness_notes",
        "failure_mode_notes",
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
        dataset_id="dataset:msfragger_search_adapter_fixture",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_results.tsv",
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
        version_trace=(
            "The benchmark is pinned to the checked-in MSFragger export and the current reference-corpus links reviewed on 2026-05-05.",
        ),
        retrieval_trace=(
            "Dataset paths and linked reference corpora were re-verified on 2026-05-05 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in adapter fixture is reused as internal benchmark evidence inside this repository and does not imply redistribution rights for external search-engine outputs beyond the test fixture snapshot.",
        instrument_profiles=("Orbitrap", "Q Exactive-class DDA"),
        reproduction_requirements=(
            "Normalize search-engine exports through the core adapter fixture corpus.",
            "Validate peptide-spectrum match confidence with target-decoy-oriented outputs.",
            "Map identified proteins against curated UniProt-reviewed records.",
        ),
        comparison_notes=(
            "Compare normalized outputs against the checked-in MSFragger export rather than rerunning external engines in-repo.",
            "Preserve target-decoy and reviewed-proteome expectations from the published identification framing.",
        ),
        exclusion_notes=(
            "Excludes direct search-engine reruns and any claim about raw-spectrum scoring parity outside the checked-in adapter fixture corpus.",
            "Excludes non-tryptic and protease-mixed export behavior that is not represented in the benchmark fixture suite.",
        ),
        weakness_notes=(
            "The checked-in export is cleaner and narrower than many production search result bundles.",
            "Protein rollup caution remains indirect because the benchmark surface is adapter-shaped rather than cohort-scale.",
        ),
        failure_mode_notes=(
            "Target-decoy columns can be normalized while semantic scope is still misread at peptide versus protein levels.",
            "Reviewed-proteome identifiers can appear stable even when protease comparability quietly drifts.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:dia_library_extraction_consistency",
        workflow_family=KnowledgeWorkflowFamily.DIA,
        title="DIA extraction consistency benchmark",
        scientific_focus="Consistency of peptide-centric extraction across DIA-style reports.",
        dataset_id="dataset:spectronaut_dia_fixture_export",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv",
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
        version_trace=(
            "The benchmark is pinned to the checked-in Spectronaut-style export and the current DIA reference corpus links reviewed on 2026-05-05.",
        ),
        retrieval_trace=(
            "Dataset paths and linked DIA reference corpora were re-verified on 2026-05-05 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in DIA fixture is reused as internal benchmark evidence and does not widen redistribution rights for vendor DIA outputs beyond the repository snapshot.",
        instrument_profiles=("Orbitrap", "timsTOF"),
        reproduction_requirements=(
            "Replay DIA-shaped adapter exports from the shared search-adapter fixture suite.",
            "Preserve DIA acquisition labels and transition-aligned peptide extraction semantics.",
            "Confirm vocabulary normalization against the PSI-MS controlled vocabulary.",
        ),
        comparison_notes=(
            "Compare adapter-normalized outputs against the checked-in Spectronaut-style export because direct DIA-NN or Spectronaut execution is outside repo scope.",
            "Keep SWATH-style transition semantics aligned with the published DIA method reference.",
        ),
        exclusion_notes=(
            "Excludes claims about vendor-library parity or de novo discovery beyond the benchmarked library-conditioned extraction surface.",
            "Excludes biological absence claims when a peptide is missing from the checked-in DIA extraction export.",
        ),
        weakness_notes=(
            "The fixture export does not capture the full instability of production library curation and chromatographic drift.",
            "Library-conditioned extraction can look more complete than the underlying protein-level support actually is.",
        ),
        failure_mode_notes=(
            "Transition evidence can be over-read as direct protein confirmation when library scope stays implicit.",
            "Vocabulary normalization can stay syntactically correct while transition alignment semantics still drift.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:ptm_site_localization_confidence",
        workflow_family=KnowledgeWorkflowFamily.PTM,
        title="PTM site-localization confidence benchmark",
        scientific_focus="Phosphorylation localization confidence and PTM term normalization.",
        dataset_id="dataset:ptm_localization_fixture",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv",
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
        version_trace=(
            "The benchmark is pinned to the checked-in PTM localization fixture and linked PTM reference corpora reviewed on 2026-05-05.",
        ),
        retrieval_trace=(
            "Dataset paths and linked PTM reference corpora were re-verified on 2026-05-05 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in PTM fixture is reused as internal benchmark evidence and does not imply redistribution rights beyond the repository’s reviewed test data.",
        instrument_profiles=("Orbitrap",),
        reproduction_requirements=(
            "Use the bundled PTM localization fixture corpus.",
            "Preserve phosphorylation-site localization scores and ambiguous-site handling.",
            "Map modification concepts to PSI-MOD-backed identifiers before emitting conclusions.",
        ),
        comparison_notes=(
            "Compare localization handling against the checked-in PTM localization fixture because direct rescoring engines are not executed in the repo test path.",
            "Retain Ascore-style ambiguity framing and PSI-MOD grounding in the resulting claims.",
        ),
        exclusion_notes=(
            "Excludes occupancy and condition-wide regulation claims that are outside the localized fixture scope.",
            "Excludes full rescoring-engine parity because the benchmark uses checked-in localization outputs rather than live rescoring.",
        ),
        weakness_notes=(
            "Localization confidence can still hide uncertainty about biological relevance and occupancy magnitude.",
            "The fixture surface is phosphorylation-oriented and does not generalize to every PTM family equally well.",
        ),
        failure_mode_notes=(
            "Ambiguous-site groups can be flattened into one confident-sounding label if the downstream consumer drops localization qualifiers.",
            "Ontology grounding can look complete while site-level ambiguity remains unresolved.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:lfq_quantification_repeatability",
        workflow_family=KnowledgeWorkflowFamily.LFQ,
        title="LFQ repeatability benchmark",
        scientific_focus="Label-free quantification repeatability on study-scale fixture inputs.",
        dataset_id="dataset:lfq_study_scale_fixture",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/quant/study_scale_ms1_features.tsv",
        acquisition_mode="data-dependent acquisition",
        success_metric="Consistent protein abundance summaries across repeated LFQ fixture runs.",
        result_claim="Label-free quantification outputs should preserve study design semantics and repeatable abundance rollups.",
        primary_citation_ids=("citation:uniprot_2025",),
        corpus_ids=(
            "corpus:quant_fixture_suite",
            "corpus:uniprot_reference_proteome",
        ),
        benchmark_rationale="The suite uses bundled LFQ fixtures to prove repeatability, but interpretation remains tied to stable reference-proteome identifiers.",
        version_trace=(
            "The benchmark is pinned to the checked-in study-scale quantification fixture and current proteome reference links reviewed on 2026-05-05.",
        ),
        retrieval_trace=(
            "Dataset paths and linked quantification reference corpora were re-verified on 2026-05-05 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in LFQ fixture is reused as internal benchmark evidence and does not widen redistribution rights for any external quantification pipelines beyond the repository snapshot.",
        instrument_profiles=("Orbitrap",),
        reproduction_requirements=(
            "Use the bundled quantification fixture corpus and study-scale design inputs.",
            "Preserve sample-design semantics during quantification aggregation.",
            "Map quantified proteins through curated UniProt-backed identifiers.",
        ),
        comparison_notes=(
            "Compare rollups against the checked-in study-scale LFQ fixture instead of claiming parity with unexecuted external quantification pipelines.",
            "Keep support claims scoped to repeatable abundance aggregation and design preservation.",
        ),
        exclusion_notes=(
            "Excludes universal cohort readiness claims and any promise that fixture repeatability removes missingness or interference.",
            "Excludes direct parity claims against external LFQ pipelines that are not executed inside the repository.",
        ),
        weakness_notes=(
            "Study-scale fixtures underrepresent the sample heterogeneity and dropout patterns seen in broader cohorts.",
            "Protein-level repeatability can obscure peptide-level ambiguity and design-sensitive missingness.",
        ),
        failure_mode_notes=(
            "Stable rollups can be mistaken for scope-free abundance truth even when missingness remains informative.",
            "Design labels can survive normalization while the downstream claim quietly widens past the benchmarked cohort shape.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:multiplex_tmtpro_quantification",
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX,
        title="Multiplex TMTpro quantification benchmark",
        scientific_focus="Isobaric multiplex assumptions and reporter-channel interpretation.",
        dataset_id="dataset:tmtpro_multiplex_fixture",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/quant/multiplex_ms1_features.tsv",
        acquisition_mode="data-dependent acquisition",
        success_metric="Stable multiplex abundance outputs with explicit TMTpro chemistry assumptions.",
        result_claim="Multiplex quantification should preserve TMTpro channel semantics and label-chemistry caveats.",
        primary_citation_ids=("citation:tmtpro_2020",),
        corpus_ids=(
            "corpus:quant_fixture_suite",
            "corpus:tmtpro_labeling_reference",
        ),
        benchmark_rationale="Multiplex quantification depends on durable label-chemistry assumptions that need a curated reference surface instead of ad hoc comments.",
        version_trace=(
            "The benchmark is pinned to the checked-in multiplex quantification fixture and current chemistry reference links reviewed on 2026-05-05.",
        ),
        retrieval_trace=(
            "Dataset paths and linked multiplex reference corpora were re-verified on 2026-05-05 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in multiplex fixture is reused as internal benchmark evidence and does not imply redistribution rights for any vendor multiplex outputs beyond the repository snapshot.",
        instrument_profiles=("Orbitrap",),
        reproduction_requirements=(
            "Use multiplex design and feature fixtures from the bundled quantification corpus.",
            "Preserve reporter-channel assignments for TMTpro-labeled samples.",
            "Keep label-chemistry assumptions explicit in any downstream interpretation.",
        ),
        comparison_notes=(
            "Compare reporter handling against the checked-in multiplex fixture because direct vendor-specific multiplex pipelines are not executed here.",
            "Limit support claims to channel semantics and chemistry caveats, not full external pipeline parity.",
        ),
        exclusion_notes=(
            "Excludes label-free abundance interpretation and any claim that reporter summaries erase multiplex interference.",
            "Excludes vendor-pipeline parity claims beyond the checked-in multiplex fixture and published chemistry framing.",
        ),
        weakness_notes=(
            "The fixture surface is narrower than production multiplex cohorts with more severe missing-channel and interference behavior.",
            "Channel stability can look stronger than the underlying protein-level certainty actually is.",
        ),
        failure_mode_notes=(
            "Reporter-channel summaries can be over-read as label-free abundance evidence when chemistry caveats are dropped.",
            "Rollup outputs can stay numerically stable while missing-channel pressure is hidden from reviewers.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:targeted_transition_quality_control",
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
        title="Targeted transition quality-control benchmark",
        scientific_focus="Transition-level quality checks over chromatogram-shaped targeted outputs.",
        dataset_id="dataset:chromatogram_qc_transition_fixture",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv",
        acquisition_mode="targeted acquisition",
        success_metric="Stable transition-level QC summaries for bundled chromatogram evidence.",
        result_claim="Targeted-style chromatogram summaries should preserve transition-level evidence and protein-inference caution when rolled up.",
        primary_citation_ids=("citation:protein_inference_2012",),
        corpus_ids=(
            "corpus:chromatogram_qc_fixture",
            "corpus:protein_inference_review_reference",
        ),
        benchmark_rationale="Targeted outputs often collapse transition evidence quickly, so the benchmark captures how much interpretation can safely happen before protein-level rollup.",
        version_trace=(
            "The benchmark is pinned to the checked-in chromatogram QC fixture and current protein-inference reference links reviewed on 2026-05-05.",
        ),
        retrieval_trace=(
            "Dataset paths and linked targeted reference corpora were re-verified on 2026-05-05 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in chromatogram fixture is reused as internal benchmark evidence and does not widen redistribution rights for vendor targeted outputs beyond the repository snapshot.",
        instrument_profiles=("Triple quadrupole", "Orbitrap"),
        reproduction_requirements=(
            "Use the bundled chromatogram QC fixture as the targeted evidence source.",
            "Keep transition-level measures intact before protein-level summary.",
            "Report any protein rollup with explicit inference caution.",
        ),
        comparison_notes=(
            "Compare targeted QC handling against the checked-in chromatogram fixture and published protein-inference caution rather than claiming direct vendor chromatogram parity.",
            "Keep support claims scoped to transition-level evidence retention and cautious rollup semantics.",
        ),
        exclusion_notes=(
            "Excludes direct vendor chromatogram parity and any claim that transition-level QC alone resolves shared-peptide ambiguity.",
            "Excludes unqualified protein certainty when the benchmark only proves cautious transition retention and rollup visibility.",
        ),
        weakness_notes=(
            "The QC fixture is operationally tidy compared with noisier targeted production runs and carryover scenarios.",
            "Transition retention is easier to prove than protein-specific interpretability in shared-peptide settings.",
        ),
        failure_mode_notes=(
            "Transition-level evidence can be collapsed into protein certainty too early if inference caution is not preserved.",
            "QC summaries can stay stable while chromatogram-specific edge cases remain outside the benchmarked fixture surface.",
        ),
    ),
)


__all__ = [
    "BenchmarkManifest",
    "DEFAULT_BENCHMARK_MANIFESTS",
    "KnowledgeWorkflowFamily",
]
