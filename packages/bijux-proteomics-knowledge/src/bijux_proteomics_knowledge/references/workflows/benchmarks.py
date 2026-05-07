# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Curated benchmark manifests for shared proteomics workflow families."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel


class KnowledgeWorkflowFamily(StrEnum):
    """Proteomics workflow families covered by curated benchmark manifests."""

    DDA = "dda"
    DIA = "dia"
    PTM = "ptm"
    LFQ = "lfq"
    MULTIPLEX = "multiplex"
    TARGETED = "targeted"


class BenchmarkCrossCheckStatus(StrEnum):
    """How far a benchmark claim has been cross-checked beyond internal consistency."""

    INTERNAL_ONLY = "internal_only"
    EXTERNAL_OUTPUT_COMPARISON = "external_output_comparison"


class BenchmarkEvidenceTier(StrEnum):
    """Scientific evidence ladder for benchmark authority and release claims."""

    SMOKE_FIXTURE = "smoke_fixture"
    CURATED_MINI_STUDY = "curated_mini_study"
    PUBLIC_TRUTH_SET = "public_truth_set"
    EXTERNAL_REPRODUCTION_PACKAGE = "external_reproduction_package"


class BenchmarkPackageArtifactKind(StrEnum):
    """Artifact roles inside a reproducible benchmark package."""

    ARTIFACT_INVENTORY = "artifact_inventory"
    BENCHMARK_MANIFEST = "benchmark_manifest"
    BENCHMARK_README = "benchmark_readme"
    DESIGN_TABLE = "design_table"
    EXPECTATION_LEDGER = "expectation_ledger"
    EXTERNAL_PIPELINE_EXPORT = "external_pipeline_export"
    FEATURE_TABLE = "feature_table"
    FIXTURE_MANIFEST = "fixture_manifest"
    FOLLOW_UP_PACKET = "follow_up_packet"
    PROTEIN_FASTA = "protein_fasta"
    RAW_SPECTRA = "raw_spectra"
    RESULTS_TABLE = "results_table"
    RUNTIME_POLICY = "runtime_policy"
    SCIENTIFIC_INVARIANT_LEDGER = "scientific_invariant_ledger"
    SEARCH_SETTINGS = "search_settings"
    WARNING_DEMONSTRATION_LEDGER = "warning_demonstration_ledger"
    TARGETED_QC_TABLE = "targeted_qc_table"


class BenchmarkPackageArtifact(JsonModel):
    """One governed repo artifact that belongs to a benchmark package."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    artifact_kind: BenchmarkPackageArtifactKind
    repo_relative_path: str = Field(..., min_length=1)
    required_for_reproduction: bool = True
    note: str = Field(..., min_length=1)


class BenchmarkReproductionStep(JsonModel):
    """One reviewable step for replaying a benchmark package."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    artifact_ids: tuple[str, ...] = Field(..., min_length=1)
    outside_repo_execution: bool = False
    expected_outputs: tuple[str, ...] = Field(..., min_length=1)

    @field_validator("artifact_ids", "expected_outputs")
    @classmethod
    def _forbid_blank_step_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if not cleaned:
            raise ValueError("at least one non-blank value is required")
        return cleaned


class WorkflowBenchmarkPackage(JsonModel):
    """One benchmark package that promotes a fixture into a reviewable bundle."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    package_summary: str = Field(..., min_length=1)
    promotion_goal: str = Field(..., min_length=1)
    realism_pressures: tuple[str, ...] = Field(..., min_length=1)
    transparent_assumptions: tuple[str, ...] = Field(..., min_length=1)
    governed_output_surfaces: tuple[str, ...] = Field(..., min_length=1)
    package_artifacts: tuple[BenchmarkPackageArtifact, ...] = Field(..., min_length=1)
    reproduction_steps: tuple[BenchmarkReproductionStep, ...] = Field(
        ..., min_length=1
    )

    @field_validator(
        "realism_pressures",
        "transparent_assumptions",
        "governed_output_surfaces",
    )
    @classmethod
    def _forbid_blank_package_values(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(item.strip() for item in value if item.strip())
        if not cleaned:
            raise ValueError("at least one non-blank value is required")
        return cleaned


class BenchmarkManifest(JsonModel):
    """One reproducible benchmark contract for a workflow family."""

    model_config = ConfigDict(extra="forbid")

    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    title: str = Field(..., min_length=1)
    scientific_focus: str = Field(..., min_length=1)
    evidence_tier: BenchmarkEvidenceTier
    dataset_id: str = Field(..., min_length=1)
    dataset_locator: str = Field(..., min_length=1)
    organism: str = Field(..., min_length=1)
    sample_complexity: str = Field(..., min_length=1)
    label_strategy: str = Field(..., min_length=1)
    sample_count: int = Field(..., ge=1)
    replicate_count: int = Field(..., ge=1)
    acquisition_mode: str = Field(..., min_length=1)
    truth_surfaces: tuple[str, ...] = Field(..., min_length=1)
    success_metric: str = Field(..., min_length=1)
    result_claim: str = Field(..., min_length=1)
    cross_check_status: BenchmarkCrossCheckStatus
    cross_check_note: str = Field(..., min_length=1)
    primary_citation_ids: tuple[str, ...] = Field(..., min_length=1)
    corpus_ids: tuple[str, ...] = Field(..., min_length=1)
    benchmark_rationale: str = Field(..., min_length=1)
    version_trace: tuple[str, ...] = Field(..., min_length=1)
    retrieval_trace: tuple[str, ...] = Field(..., min_length=1)
    dataset_license_and_reuse_note: str = Field(..., min_length=1)
    instrument_profiles: tuple[str, ...] = Field(..., min_length=1)
    reproduction_requirements: tuple[str, ...] = Field(..., min_length=1)
    benchmark_package: WorkflowBenchmarkPackage | None = None
    comparator_path_ids: tuple[str, ...] = Field(default_factory=tuple)
    comparison_notes: tuple[str, ...] = Field(..., min_length=1)
    exclusion_notes: tuple[str, ...] = Field(..., min_length=1)
    weakness_notes: tuple[str, ...] = Field(..., min_length=1)
    fixture_realism_limits: tuple[str, ...] = Field(..., min_length=1)
    failure_mode_notes: tuple[str, ...] = Field(..., min_length=1)
    expected_failure_conditions: tuple[str, ...] = Field(..., min_length=1)
    non_transfer_zones: tuple[str, ...] = Field(..., min_length=1)
    supported_repo_claims: tuple[str, ...] = Field(..., min_length=1)
    last_reviewed_on: date
    freshness_window_days: int = Field(..., ge=1)
    obsolescence_conditions: tuple[str, ...] = Field(..., min_length=1)
    retirement_conditions: tuple[str, ...] = Field(..., min_length=1)

    @field_validator(
        "truth_surfaces",
        "primary_citation_ids",
        "corpus_ids",
        "version_trace",
        "retrieval_trace",
        "instrument_profiles",
        "reproduction_requirements",
        "comparator_path_ids",
        "comparison_notes",
        "exclusion_notes",
        "weakness_notes",
        "fixture_realism_limits",
        "failure_mode_notes",
        "expected_failure_conditions",
        "non_transfer_zones",
        "supported_repo_claims",
        "obsolescence_conditions",
        "retirement_conditions",
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
        title="DDA reviewable public benchmark package",
        scientific_focus="Bounded DDA review over a primary MaxQuant import path with explicit MSFragger comparator pressure.",
        evidence_tier=BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE,
        dataset_id="dataset:dda_reviewable_run_package",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/package_manifest.json",
        organism="human",
        sample_complexity="one raw-like spectrum, one primary MaxQuant pipeline export, one MSFragger comparator export, and explicit warning ledgers",
        label_strategy="label-free",
        sample_count=1,
        replicate_count=1,
        acquisition_mode="data-dependent acquisition",
        truth_surfaces=(
            "target-decoy confidence scope",
            "loss-free adapter normalization across the shipped DDA imports",
            "cross-engine protein-rollup warning pressure",
        ),
        success_metric="The primary MaxQuant export stays parity-acceptable while the MSFragger comparator keeps protein-rollup disagreement explicit.",
        result_claim="The public DDA package can support bounded peptide-facing review, explicit target-decoy visibility, and explicit cross-engine protein-rollup caution.",
        cross_check_status=BenchmarkCrossCheckStatus.EXTERNAL_OUTPUT_COMPARISON,
        cross_check_note="The package is cross-checked against both MaxQuant and MSFragger pipeline exports, but still does not claim in-repo live-engine rerun parity.",
        primary_citation_ids=(
            "citation:target_decoy_2007",
            "citation:protein_inference_2012",
            "citation:uniprot_2025",
        ),
        corpus_ids=(
            "corpus:search_adapter_fixture_suite",
            "corpus:target_decoy_method_reference",
        ),
        benchmark_rationale="The DDA family now has enough tracked substance to make the benchmark itself a public package instead of a structure-only fixture story, so the manifest centers on inspectable files and cross-engine drift.",
        version_trace=(
            "The benchmark was promoted onto the tracked DDA reviewable package and its paired comparator export on 2026-05-07.",
        ),
        retrieval_trace=(
            "The tracked DDA package files, comparator exports, and citation anchors were re-verified on 2026-05-07 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The tracked DDA package reuses checked-in raw-like and imported-result snapshots as governed benchmark evidence and does not imply redistribution rights for any broader external-engine dataset outside those snapshots.",
        instrument_profiles=("Orbitrap", "Q Exactive-class DDA"),
        reproduction_requirements=(
            "Inspect the tracked package manifest, artifact inventory, and README before relying on summary prose.",
            "Replay adapter normalization on the shipped MaxQuant and MSFragger pipeline exports.",
            "Check the warning demonstration ledger before promoting any protein-facing DDA claim.",
        ),
        benchmark_package=WorkflowBenchmarkPackage(
            package_id="benchmark_package:dda_reviewable_run",
            package_summary="The DDA benchmark package is now a tracked public package with a human README, machine manifest, artifact inventory, scientific invariants, warning demonstrations, raw-like spectra, and paired MaxQuant and MSFragger exports.",
            promotion_goal="Keep DDA authority anchored in outsider-readable files and concrete warning pressure instead of structure-only benchmark objects.",
            realism_pressures=(
                "paired primary-versus-comparator DDA export pressure at the protein rollup layer",
                "raw-like spectrum and explicit expectation-ledger pressure instead of export-only narration",
            ),
            transparent_assumptions=(
                "the package proves bounded imported-result review, not in-repo live-engine rerun parity",
                "the warning ledger is strong enough to demonstrate protein-rollup drift but not broad production-cohort transfer",
            ),
            governed_output_surfaces=(
                "identification.search_adapters",
                "identification.review_ready_evidence_bundle",
                "identification.search_adapter_loss",
            ),
            package_artifacts=(
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:package_readme",
                    artifact_kind=BenchmarkPackageArtifactKind.BENCHMARK_README,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/README.md",
                    note="Human-readable entrypoint that explains exactly what the DDA package can and cannot support.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:package_manifest",
                    artifact_kind=BenchmarkPackageArtifactKind.BENCHMARK_MANIFEST,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/package_manifest.json",
                    note="Machine-readable DDA package summary with citations, runtime linkage, and review artifact paths.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:artifact_inventory",
                    artifact_kind=BenchmarkPackageArtifactKind.ARTIFACT_INVENTORY,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/artifact_inventory.json",
                    note="Artifact inventory with digests and reviewer notes for every tracked DDA evidence file.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:scientific_invariants",
                    artifact_kind=BenchmarkPackageArtifactKind.SCIENTIFIC_INVARIANT_LEDGER,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/scientific_invariants.json",
                    note="Numeric DDA invariants earned by the public package rather than by benchmark shape alone.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:warning_demonstrations",
                    artifact_kind=BenchmarkPackageArtifactKind.WARNING_DEMONSTRATION_LEDGER,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/warning_demonstrations.json",
                    note="Concrete warning demonstrations that keep protein-facing DDA caution public and inspectable.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:raw_spectra",
                    artifact_kind=BenchmarkPackageArtifactKind.RAW_SPECTRA,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
                    note="Raw-like spectrum that keeps the benchmark anchored to inspectable fragment evidence.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:design_table",
                    artifact_kind=BenchmarkPackageArtifactKind.DESIGN_TABLE,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/production_run/design.tsv",
                    note="Design table that preserves batch, instrument, and engine context for the reviewable run.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:expectation_ledger",
                    artifact_kind=BenchmarkPackageArtifactKind.EXPECTATION_LEDGER,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/production_run/workflow_end_to_end_expectations.json",
                    note="Expectation ledger that keeps runtime and review outputs explicit.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:maxquant_export",
                    artifact_kind=BenchmarkPackageArtifactKind.EXTERNAL_PIPELINE_EXPORT,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv",
                    note="Primary imported DDA result set that anchors the runtime reviewable run.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:maxquant_settings",
                    artifact_kind=BenchmarkPackageArtifactKind.SEARCH_SETTINGS,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_settings.txt",
                    note="Primary search settings snapshot that exposes enzyme, tolerances, and decoy prefix assumptions.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:msfragger_export",
                    artifact_kind=BenchmarkPackageArtifactKind.EXTERNAL_PIPELINE_EXPORT,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv",
                    note="Comparator imported DDA result set that demonstrates protein-rollup drift in public files.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dda_reviewable_run:msfragger_settings",
                    artifact_kind=BenchmarkPackageArtifactKind.SEARCH_SETTINGS,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger.params",
                    note="Comparator search settings snapshot that keeps alternate engine assumptions inspectable.",
                ),
            ),
            reproduction_steps=(
                BenchmarkReproductionStep(
                    step_id="inspect_public_package",
                    summary="Open the public package README, manifest, and artifact inventory before relying on narrative summaries.",
                    artifact_ids=(
                        "dda_reviewable_run:package_readme",
                        "dda_reviewable_run:package_manifest",
                        "dda_reviewable_run:artifact_inventory",
                    ),
                    expected_outputs=(
                        "package scope and exact tracked evidence files stay explicit",
                        "artifact digests and reviewer notes are visible before any scientific claim is promoted",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="replay_primary_import_review",
                    summary="Replay the primary DDA import review against the tracked MaxQuant export, settings, raw-like spectrum, design table, and expectation ledger.",
                    artifact_ids=(
                        "dda_reviewable_run:raw_spectra",
                        "dda_reviewable_run:design_table",
                        "dda_reviewable_run:expectation_ledger",
                        "dda_reviewable_run:maxquant_export",
                        "dda_reviewable_run:maxquant_settings",
                    ),
                    expected_outputs=(
                        "target-decoy semantics remain visible after adapter normalization",
                        "the runtime-linked DDA review path stays bounded to the tracked import package",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="demonstrate_comparator_warning_pressure",
                    summary="Compare the primary and comparator DDA exports against the invariant and warning ledgers before making any protein-facing interpretation stronger.",
                    artifact_ids=(
                        "dda_reviewable_run:maxquant_export",
                        "dda_reviewable_run:msfragger_export",
                        "dda_reviewable_run:scientific_invariants",
                        "dda_reviewable_run:warning_demonstrations",
                    ),
                    expected_outputs=(
                        "adapter parity and loss-free import remain explicit for both DDA engines",
                        "protein-rollup disagreement stays demonstrated in public files rather than hidden inside review prose",
                    ),
                ),
            ),
        ),
        comparator_path_ids=(
            "comparator_path:msfragger_imported_dda_review",
            "comparator_path:maxquant_evidence_import_contracts",
        ),
        comparison_notes=(
            "Compare the primary MaxQuant import path against the paired MSFragger comparator export inside the tracked DDA package.",
            "Preserve target-decoy visibility and explicit protein-rollup caution rather than flattening DDA review into engine-agnostic certainty.",
        ),
        exclusion_notes=(
            "Excludes direct search-engine reruns and any claim about raw-spectrum scoring parity beyond the tracked imported-result package.",
            "Excludes broad production-cohort DDA behavior that is not represented in the one-run public package.",
        ),
        weakness_notes=(
            "The tracked DDA package is still smaller and cleaner than a production multi-run search corpus.",
            "The package demonstrates protein-rollup drift directly, but it still does not prove live-engine calibration parity.",
        ),
        fixture_realism_limits=(
            "The public package is still a one-run imported-result surface rather than a broader cohort-grade DDA benchmark.",
            "The package demonstrates cross-engine drift but does not yet replace live-engine rerun proof.",
        ),
        failure_mode_notes=(
            "Target-decoy visibility can stay intact while protein-facing interpretation still drifts across comparator engines.",
            "Imported-result parity can look strong even when live-engine calibration behavior remains unproven.",
        ),
        expected_failure_conditions=(
            "Adapter normalization drops or misreads decoy labels.",
            "Reviewed-proteome accessions drift during import or rollup.",
        ),
        non_transfer_zones=(
            "Unrepresented proteases or mixed-protease exports.",
            "Raw-spectrum scoring parity and engine-side calibration behavior.",
        ),
        supported_repo_claims=(
            "adapter-normalized DDA evidence preserves target-decoy semantics across the pinned fixture corpus",
            "review-ready DDA evidence retains reviewed-proteome grounding and explicit field-loss accounting",
        ),
        last_reviewed_on=date(2026, 5, 5),
        freshness_window_days=365,
        obsolescence_conditions=(
            "Search-engine export columns change in a way that the checked fixture no longer reflects current outputs.",
            "Reference-proteome mapping rules change without a corresponding fixture refresh.",
        ),
        retirement_conditions=(
            "Retire this benchmark from release-facing authority if it remains stale beyond two review windows.",
            "Retire this benchmark from scientific authority if adapter support widens beyond the fixture without a broader benchmark tier.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:dia_library_extraction_consistency",
        workflow_family=KnowledgeWorkflowFamily.DIA,
        title="DIA library review public benchmark package",
        scientific_focus="Library-conditioned DIA extraction over a tracked public package with explicit comparator and runtime-import boundaries.",
        evidence_tier=BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE,
        dataset_id="dataset:dia_library_review_package",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dia_library_review_package/package_manifest.json",
        organism="human",
        sample_complexity="library-conditioned DIA adapter export with bounded precursor diversity",
        label_strategy="label-free",
        sample_count=1,
        replicate_count=1,
        acquisition_mode="data-independent acquisition",
        truth_surfaces=(
            "transition-aligned peptide extraction",
            "library-conditioned DIA semantics",
            "controlled-vocabulary normalization",
        ),
        success_metric="Stable extracted peptide quantities and aligned DIA transition semantics.",
        result_claim="DIA adapters should preserve acquisition semantics, transition alignment, and SWATH-style extraction expectations.",
        cross_check_status=BenchmarkCrossCheckStatus.EXTERNAL_OUTPUT_COMPARISON,
        cross_check_note="The manifest is checked against a tracked DIA public package with Spectronaut-style and DIA-NN-style exports, but it still does not claim chromatogram-level vendor execution parity inside the repo.",
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
            "The benchmark is pinned to the checked-in DIA public package and the current DIA reference corpus links reviewed on 2026-05-07.",
        ),
        retrieval_trace=(
            "Dataset paths and linked DIA reference corpora were re-verified on 2026-05-07 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in DIA fixture is reused as internal benchmark evidence and does not widen redistribution rights for vendor DIA outputs beyond the repository snapshot.",
        instrument_profiles=("Orbitrap", "timsTOF"),
        reproduction_requirements=(
            "Replay DIA-shaped adapter exports from the shared search-adapter fixture suite.",
            "Preserve DIA acquisition labels and transition-aligned peptide extraction semantics.",
            "Confirm vocabulary normalization against the PSI-MS controlled vocabulary.",
        ),
        benchmark_package=WorkflowBenchmarkPackage(
            package_id="benchmark_package:dia_library_review_package",
            package_summary="DIA benchmark package ties a tracked public package to Spectronaut-style and DIA-NN-style exports so extraction-and-interpretation review stays outsider-readable with explicit library assumptions.",
            promotion_goal="Keep DIA authority anchored in the tracked public package instead of a thinner checked-in report review bundle.",
            realism_pressures=(
                "library-conditioned peptide extraction pressure through pinned report and pipeline exports",
                "method-scope pressure that keeps DIA interpretation bounded by visible library assumptions",
            ),
            transparent_assumptions=(
                "library generation and vendor execution remain outside repo scope even though settings and outputs are pinned",
                "comparison authority stops at checked-in extraction outputs rather than chromatogram-level vendor parity",
            ),
            governed_output_surfaces=(
                "identification.search_adapters",
                "dia.capability_matrix",
                "identification.review_ready_evidence_bundle",
            ),
            package_artifacts=(
                BenchmarkPackageArtifact(
                    artifact_id="dia_library_bundle:report",
                    artifact_kind=BenchmarkPackageArtifactKind.RESULTS_TABLE,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv",
                    note="Pinned Spectronaut-style report that anchors DIA extraction review.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dia_library_bundle:pipeline_export",
                    artifact_kind=BenchmarkPackageArtifactKind.EXTERNAL_PIPELINE_EXPORT,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_pipeline_export.tsv",
                    note="Pipeline-facing export snapshot that keeps adapter field coverage auditable.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="dia_library_bundle:settings",
                    artifact_kind=BenchmarkPackageArtifactKind.SEARCH_SETTINGS,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_settings.txt",
                    note="Pinned DIA settings snapshot that exposes spectral-library and extraction assumptions.",
                ),
            ),
            reproduction_steps=(
                BenchmarkReproductionStep(
                    step_id="inspect_library_conditioning",
                    summary="Review the pinned DIA settings before treating the checked-in extraction report as benchmark authority.",
                    artifact_ids=("dia_library_bundle:settings",),
                    outside_repo_execution=True,
                    expected_outputs=(
                        "library-conditioned assumptions stay explicit",
                        "DIA review remains bounded by the documented extraction posture",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="normalize_report_and_pipeline_export",
                    summary="Replay adapter normalization over both the report and pipeline export so field-level extraction semantics stay auditable.",
                    artifact_ids=(
                        "dia_library_bundle:report",
                        "dia_library_bundle:pipeline_export",
                    ),
                    expected_outputs=(
                        "transition-aligned peptide evidence remains reviewable",
                        "adapter field-loss accounting stays visible instead of hiding library-shaped columns",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="assemble_interpretation_review",
                    summary="Build DIA capability and review-ready evidence outputs from the pinned extraction surface.",
                    artifact_ids=("dia_library_bundle:report",),
                    expected_outputs=(
                        "DIA capability boundaries remain explicit",
                        "interpretation claims stop at library-conditioned review scope",
                    ),
                ),
            ),
        ),
        comparator_path_ids=(
            "comparator_path:spectronaut_dia_review_contracts",
            "comparator_path:diann_report_normalization_contracts",
        ),
        comparison_notes=(
            "Compare adapter-normalized outputs against the tracked DIA public package because direct DIA-NN or Spectronaut execution is outside repo scope.",
            "Keep SWATH-style transition semantics aligned with the published DIA method reference.",
        ),
        exclusion_notes=(
            "Excludes claims about vendor-library parity or de novo discovery beyond the benchmarked library-conditioned extraction surface.",
            "Excludes biological absence claims when a peptide is missing from the checked-in DIA extraction export.",
        ),
        weakness_notes=(
            "The public package still does not capture the full instability of production library curation and chromatographic drift.",
            "Library-conditioned extraction can look more complete than the underlying protein-level support actually is.",
        ),
        fixture_realism_limits=(
            "The checked-in DIA export does not pressure vendor-library churn, chromatography drift, or peptide absence ambiguity at production scale.",
            "The fixture is library-conditioned and cannot authorize open-ended protein-level absence claims.",
        ),
        failure_mode_notes=(
            "Transition evidence can be over-read as direct protein confirmation when library scope stays implicit.",
            "Vocabulary normalization can stay syntactically correct while transition alignment semantics still drift.",
        ),
        expected_failure_conditions=(
            "Transition semantics drift while column names still normalize cleanly.",
            "Library scope is dropped from the final review surface.",
        ),
        non_transfer_zones=(
            "Unseen library compositions, vendor-tuned extraction heuristics, and chromatographic drift outside the fixture.",
            "Protein-level absence claims inferred from library-conditioned missing peptides.",
        ),
        supported_repo_claims=(
            "DIA adapter normalization preserves library-conditioned transition semantics across the pinned export corpus",
            "DIA review surfaces keep capability limits explicit instead of implying vendor-pipeline parity",
        ),
        last_reviewed_on=date(2026, 5, 7),
        freshness_window_days=365,
        obsolescence_conditions=(
            "Supported DIA export dialects change without fixture refresh.",
            "Controlled-vocabulary mappings or library assumptions change materially.",
        ),
        retirement_conditions=(
            "Retire this benchmark from release-facing authority if it remains stale beyond two review windows.",
            "Retire this benchmark from scientific authority if DIA support expands into vendor parity without a broader reproduction package.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:ptm_site_localization_confidence",
        workflow_family=KnowledgeWorkflowFamily.PTM,
        title="PTM localization public benchmark package",
        scientific_focus="Localization, ambiguity, occupancy-facing feature context, and raw-spectrum context over a tracked PTM public package.",
        evidence_tier=BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE,
        dataset_id="dataset:ptm_localization_review_package",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/ptm_localization_review_package/package_manifest.json",
        organism="human",
        sample_complexity="phosphorylation-oriented localization fixture with bounded site ambiguity",
        label_strategy="label-free",
        sample_count=8,
        replicate_count=4,
        acquisition_mode="data-dependent acquisition",
        truth_surfaces=(
            "localized-site confidence",
            "ambiguous-site preservation",
            "PSI-MOD concept grounding",
        ),
        success_metric="Stable localization confidence assignments with curated PTM term provenance.",
        result_claim="PTM localization outputs should retain both PSI-MOD concept mapping and Ascore-style evidence interpretation.",
        cross_check_status=BenchmarkCrossCheckStatus.INTERNAL_ONLY,
        cross_check_note="The manifest is benchmarked against a tracked PTM public package with localization, feature, raw-spectrum, and sequence-context evidence, but comparator-backed claim support is still refused.",
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
            "The benchmark is pinned to the checked-in PTM public package and linked PTM reference corpora reviewed on 2026-05-07.",
        ),
        retrieval_trace=(
            "Dataset paths and linked PTM reference corpora were re-verified on 2026-05-07 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in PTM fixture is reused as internal benchmark evidence and does not imply redistribution rights beyond the repository’s reviewed test data.",
        instrument_profiles=("Orbitrap",),
        reproduction_requirements=(
            "Use the bundled PTM localization fixture corpus.",
            "Preserve phosphorylation-site localization scores and ambiguous-site handling.",
            "Map modification concepts to PSI-MOD-backed identifiers before emitting conclusions.",
        ),
        benchmark_package=WorkflowBenchmarkPackage(
            package_id="benchmark_package:ptm_localization_review_package",
            package_summary="PTM benchmark package ties a tracked public package to localization, PTM feature, raw-spectrum, and reference-sequence evidence so ambiguity and targetability stay outsider-readable.",
            promotion_goal="Keep PTM authority anchored in the tracked public package instead of a thinner localization fixture story.",
            realism_pressures=(
                "site-localization ambiguity and occupancy-facing feature pressure through tracked localization and PTM feature files",
                "raw-spectrum and sequence-context pressure that keeps PTM review tied to inspectable evidence",
            ),
            transparent_assumptions=(
                "the public package proves bounded localization review and explicit ambiguity handling, not comparator-backed PTM parity",
                "runtime and comparator closure still remain outside the current PTM flagship package",
            ),
            governed_output_surfaces=(
                "ptm.localization_review",
                "ptm.lab_targeting_packet",
                "ptm.occupancy_counterpart",
            ),
            package_artifacts=(
                BenchmarkPackageArtifact(
                    artifact_id="ptm_localization_review_package:package_readme",
                    artifact_kind=BenchmarkPackageArtifactKind.BENCHMARK_README,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/ptm_localization_review_package/README.md",
                    note="Human-readable entrypoint that states the exact PTM ambiguity boundary.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="ptm_localization_review_package:package_manifest",
                    artifact_kind=BenchmarkPackageArtifactKind.BENCHMARK_MANIFEST,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/ptm_localization_review_package/package_manifest.json",
                    note="Machine-readable PTM package summary with package scope and package files.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="ptm_localization_review_package:artifact_inventory",
                    artifact_kind=BenchmarkPackageArtifactKind.ARTIFACT_INVENTORY,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/ptm_localization_review_package/artifact_inventory.json",
                    note="Artifact inventory with digests and row counts for the tracked PTM package files.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="ptm_localization_review_package:quality_sheet",
                    artifact_kind=BenchmarkPackageArtifactKind.ARTIFACT_INVENTORY,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/ptm_localization_review_package/quality_sheet.json",
                    required_for_reproduction=False,
                    note="Quality sheet that keeps PTM runtime and comparator blockers explicit from the package root.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="ptm_localization_review_package:lifecycle_record",
                    artifact_kind=BenchmarkPackageArtifactKind.ARTIFACT_INVENTORY,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/ptm_localization_review_package/lifecycle.json",
                    required_for_reproduction=False,
                    note="Lifecycle record that states which stronger PTM package should replace the current one.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="ptm_localization_review_package:localization_table",
                    artifact_kind=BenchmarkPackageArtifactKind.RESULTS_TABLE,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv",
                    note="Tracked PTM localization evidence with explicit site ambiguity.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="ptm_localization_review_package:feature_table",
                    artifact_kind=BenchmarkPackageArtifactKind.FEATURE_TABLE,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/ptm/ptm_features.tsv",
                    note="Tracked PTM feature evidence that keeps occupancy-facing interpretation grounded in files.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="ptm_localization_review_package:reference_fasta",
                    artifact_kind=BenchmarkPackageArtifactKind.PROTEIN_FASTA,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/fasta/ptm_sites.fasta",
                    note="Reference sequence context for exact site coordinates and residue identity.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="ptm_localization_review_package:raw_spectra",
                    artifact_kind=BenchmarkPackageArtifactKind.RAW_SPECTRA,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
                    note="Raw-like spectrum that keeps fragment-linked PTM evidence inspectable.",
                ),
            ),
            reproduction_steps=(
                BenchmarkReproductionStep(
                    step_id="inspect_public_package",
                    summary="Open the PTM package README, manifest, quality sheet, and lifecycle record before relying on PTM summary prose.",
                    artifact_ids=(
                        "ptm_localization_review_package:package_readme",
                        "ptm_localization_review_package:package_manifest",
                        "ptm_localization_review_package:quality_sheet",
                        "ptm_localization_review_package:lifecycle_record",
                    ),
                    expected_outputs=(
                        "ambiguity and runtime gaps stay explicit",
                        "the current PTM public package boundary is visible from files alone",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="replay_localization_and_feature_review",
                    summary="Replay PTM localization and occupancy-facing review over the tracked localization and feature files.",
                    artifact_ids=(
                        "ptm_localization_review_package:localization_table",
                        "ptm_localization_review_package:feature_table",
                    ),
                    expected_outputs=(
                        "localized and ambiguous PTM evidence remain distinct",
                        "occupancy-facing interpretation remains tied to tracked PTM feature evidence",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="keep_raw_and_sequence_context_visible",
                    summary="Use the raw-like spectrum and reference FASTA before any PTM targetability claim is strengthened.",
                    artifact_ids=(
                        "ptm_localization_review_package:raw_spectra",
                        "ptm_localization_review_package:reference_fasta",
                    ),
                    expected_outputs=(
                        "fragment-linked PTM evidence stays inspectable",
                        "site coordinates remain tied to reference sequence context",
                    ),
                ),
            ),
        ),
        comparator_path_ids=("comparator_path:maxquant_evidence_import_contracts",),
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
            "The public package is still phosphorylation-oriented and does not generalize to every PTM family equally well under broader production PTM diversity.",
        ),
        fixture_realism_limits=(
            "The fixture emphasizes phosphorylation localization and does not represent full PTM family diversity.",
            "The dataset is too tidy to authorize occupancy or broad regulatory storytelling on its own.",
        ),
        failure_mode_notes=(
            "Ambiguous-site groups can be flattened into one confident-sounding label if the downstream consumer drops localization qualifiers.",
            "Ontology grounding can look complete while site-level ambiguity remains unresolved.",
        ),
        expected_failure_conditions=(
            "Localized and ambiguous site groups are collapsed into one accepted site claim.",
            "PTM concept identifiers resolve while localization confidence is discarded.",
        ),
        non_transfer_zones=(
            "Stoichiometric occupancy and broad regulatory claims.",
            "PTM families that are not represented by the phosphorylation-oriented fixture.",
        ),
        supported_repo_claims=(
            "PTM review preserves localization confidence, ambiguity, and PSI-MOD grounding across the pinned phospho-oriented fixture",
            "PTM benchmark outputs separate localized evidence from broader occupancy or regulatory claims",
        ),
        last_reviewed_on=date(2026, 5, 7),
        freshness_window_days=365,
        obsolescence_conditions=(
            "PTM localization conventions change without a fixture refresh.",
            "Supported PTM families broaden or narrow without updating the benchmark scope.",
        ),
        retirement_conditions=(
            "Retire this benchmark from release-facing authority if it remains stale beyond two review windows.",
            "Retire this benchmark from scientific authority if PTM support broadens beyond phosphorylation-oriented localization without a broader benchmark tier.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:lfq_quantification_repeatability",
        workflow_family=KnowledgeWorkflowFamily.LFQ,
        title="LFQ cohort review public benchmark package",
        scientific_focus="Label-free quantification repeatability and missingness review over a tracked cohort-shaped public package.",
        evidence_tier=BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE,
        dataset_id="dataset:lfq_cohort_review_package",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/lfq_cohort_review_package/package_manifest.json",
        organism="human",
        sample_complexity="study-scale cohort fixture with bounded missingness and two-condition replicate structure",
        label_strategy="label-free",
        sample_count=4,
        replicate_count=2,
        acquisition_mode="data-dependent acquisition",
        truth_surfaces=(
            "protein-level abundance rollup",
            "study-design preservation",
            "repeatability under bounded missingness",
        ),
        success_metric="Consistent protein abundance summaries across repeated LFQ fixture runs.",
        result_claim="Label-free quantification outputs should preserve study design semantics and repeatable abundance rollups.",
        cross_check_status=BenchmarkCrossCheckStatus.INTERNAL_ONLY,
        cross_check_note="The manifest proves repeatability over a tracked LFQ public package, but still does not claim runtime execution or broader cohort truth parity.",
        primary_citation_ids=("citation:uniprot_2025",),
        corpus_ids=(
            "corpus:quant_fixture_suite",
            "corpus:uniprot_reference_proteome",
        ),
        benchmark_rationale="The suite uses bundled LFQ fixtures to prove repeatability, but interpretation remains tied to stable reference-proteome identifiers.",
        version_trace=(
            "The benchmark is pinned to the checked-in LFQ public package and current proteome reference links reviewed on 2026-05-07.",
        ),
        retrieval_trace=(
            "Dataset paths and linked quantification reference corpora were re-verified on 2026-05-07 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in LFQ fixture is reused as internal benchmark evidence and does not widen redistribution rights for any external quantification pipelines beyond the repository snapshot.",
        instrument_profiles=("Orbitrap",),
        reproduction_requirements=(
            "Use the bundled quantification fixture corpus and study-scale design inputs.",
            "Preserve sample-design semantics during quantification aggregation.",
            "Map quantified proteins through curated UniProt-backed identifiers.",
        ),
        benchmark_package=WorkflowBenchmarkPackage(
            package_id="benchmark_package:lfq_cohort_review_package",
            package_summary="LFQ benchmark package ties a tracked public package to cohort-shaped design and study-scale feature evidence so missingness and replicate structure stay outsider-readable.",
            promotion_goal="Keep LFQ authority anchored in the tracked public package instead of a thinner study-scale fixture bundle.",
            realism_pressures=(
                "cohort-shaped replicate and batch pressure through an eight-sample design table",
                "missingness pressure that keeps quant review bounded by actual dropout and design semantics",
            ),
            transparent_assumptions=(
                "the study remains fixture-sized even though it carries cohort-style batch and instrument structure",
                "repeatability under this bundle does not imply spike-in accuracy or broad cohort transfer",
            ),
            governed_output_surfaces=(
                "quantification.feature_ingestion",
                "quantification.review",
            ),
            package_artifacts=(
                BenchmarkPackageArtifact(
                    artifact_id="lfq_cohort_bundle:feature_table",
                    artifact_kind=BenchmarkPackageArtifactKind.FEATURE_TABLE,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/quant/study_scale_ms1_features.tsv",
                    note="Study-scale LFQ feature evidence with visible missingness and replicate structure.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="lfq_cohort_bundle:design_table",
                    artifact_kind=BenchmarkPackageArtifactKind.DESIGN_TABLE,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/quant/study_scale.design.tsv",
                    note="Eight-sample cohort-shaped design with batches, instruments, and replicate labels.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="lfq_cohort_bundle:expectation_ledger",
                    artifact_kind=BenchmarkPackageArtifactKind.EXPECTATION_LEDGER,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/quant/quant_reproducibility_manifest.json",
                    required_for_reproduction=False,
                    note="Pinned quant reproducibility ledger that keeps review output hashes explicit even though it is narrower than the study-scale cohort table.",
                ),
            ),
            reproduction_steps=(
                BenchmarkReproductionStep(
                    step_id="inspect_cohort_design",
                    summary="Check that replicate, batch, condition, and instrument structure remain governed before reading the benchmark as cohort-like evidence.",
                    artifact_ids=("lfq_cohort_bundle:design_table",),
                    expected_outputs=(
                        "cohort-style replicate structure remains explicit",
                        "batch and instrument posture stays visible before quant rollup begins",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="assemble_quant_review_bundle",
                    summary="Replay LFQ feature ingestion and quant review assembly over the study-scale design and feature tables.",
                    artifact_ids=(
                        "lfq_cohort_bundle:feature_table",
                        "lfq_cohort_bundle:design_table",
                    ),
                    expected_outputs=(
                        "missingness and QC caveats remain first-class review signals",
                        "protein-level abundance rollups preserve design semantics instead of flattening them",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="cross_check_repeatability_scope",
                    summary="Use the pinned reproducibility ledger as a bounded cross-check rather than treating stable values as general LFQ truth.",
                    artifact_ids=("lfq_cohort_bundle:expectation_ledger",),
                    expected_outputs=(
                        "repeatability claims remain separate from accuracy claims",
                        "review outputs stay tied to the governed cohort-style fixture scope",
                    ),
                ),
            ),
        ),
        comparator_path_ids=("comparator_path:maxquant_evidence_import_contracts",),
        comparison_notes=(
            "Compare rollups against the tracked LFQ public package instead of claiming parity with unexecuted external quantification pipelines.",
            "Keep support claims scoped to repeatable abundance aggregation and design preservation.",
        ),
        exclusion_notes=(
            "Excludes universal cohort readiness claims and any promise that fixture repeatability removes missingness or interference.",
            "Excludes direct parity claims against external LFQ pipelines that are not executed inside the repository.",
        ),
        weakness_notes=(
            "The public package still underrepresents the sample heterogeneity and dropout patterns seen in broader production cohorts.",
            "Protein-level repeatability can obscure peptide-level ambiguity and design-sensitive missingness.",
        ),
        fixture_realism_limits=(
            "The LFQ fixture does not represent broader cohort heterogeneity or severe missing-not-at-random behavior.",
            "Repeatability under this study shape does not authorize decision-grade abundance claims by itself.",
        ),
        failure_mode_notes=(
            "Stable rollups can be mistaken for scope-free abundance truth even when missingness remains informative.",
            "Design labels can survive normalization while the downstream claim quietly widens past the benchmarked cohort shape.",
        ),
        expected_failure_conditions=(
            "Protein rollups remain numerically stable while missingness or contrast semantics drift.",
            "Design annotations survive import but no longer match the benchmarked comparison.",
        ),
        non_transfer_zones=(
            "Large heterogeneous cohorts with stronger missing-not-at-random behavior.",
            "Accuracy claims against external LFQ pipelines or spike-in truth sets.",
        ),
        supported_repo_claims=(
            "LFQ review preserves study-design semantics, missingness visibility, and repeatable rollup behavior across the bundled fixture",
            "LFQ benchmark outputs can support review-grade abundance interpretation when QC and replicate caveats remain explicit",
        ),
        last_reviewed_on=date(2026, 5, 7),
        freshness_window_days=365,
        obsolescence_conditions=(
            "LFQ design fixtures change in sample structure without metadata refresh.",
            "Quantification claims expand beyond repeatability into accuracy without new truth evidence.",
        ),
        retirement_conditions=(
            "Retire this benchmark from release-facing authority if it remains stale beyond two review windows.",
            "Retire this benchmark from scientific authority if quantification claims widen into accuracy or cohort-scale decision support without a stronger truth tier.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:multiplex_tmtpro_quantification",
        workflow_family=KnowledgeWorkflowFamily.MULTIPLEX,
        title="Multiplex TMTpro public benchmark package",
        scientific_focus="Isobaric multiplex channel and chemistry interpretation over a tracked TMTpro public package.",
        evidence_tier=BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE,
        dataset_id="dataset:multiplex_tmtpro_review_package",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/multiplex_tmtpro_review_package/package_manifest.json",
        organism="human",
        sample_complexity="paired-plex reporter-channel fixture with bounded interference and missing-channel pressure",
        label_strategy="TMTpro multiplex",
        sample_count=6,
        replicate_count=2,
        acquisition_mode="data-dependent acquisition",
        truth_surfaces=(
            "reporter-channel identity preservation",
            "label-chemistry scope retention",
            "bounded multiplex rollup interpretation",
        ),
        success_metric="Stable multiplex abundance outputs with explicit TMTpro chemistry assumptions.",
        result_claim="Multiplex quantification should preserve TMTpro channel semantics and label-chemistry caveats.",
        cross_check_status=BenchmarkCrossCheckStatus.INTERNAL_ONLY,
        cross_check_note="The manifest is bounded to a tracked multiplex public package and published chemistry framing rather than a live vendor multiplex pipeline.",
        primary_citation_ids=("citation:tmtpro_2020",),
        corpus_ids=(
            "corpus:quant_fixture_suite",
            "corpus:tmtpro_labeling_reference",
        ),
        benchmark_rationale="Multiplex quantification depends on durable label-chemistry assumptions that need a curated reference surface instead of ad hoc comments.",
        version_trace=(
            "The benchmark is pinned to the checked-in multiplex public package and current chemistry reference links reviewed on 2026-05-07.",
        ),
        retrieval_trace=(
            "Dataset paths and linked multiplex reference corpora were re-verified on 2026-05-07 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in multiplex fixture is reused as internal benchmark evidence and does not imply redistribution rights for any vendor multiplex outputs beyond the repository snapshot.",
        instrument_profiles=("Orbitrap",),
        reproduction_requirements=(
            "Use multiplex design and feature fixtures from the bundled quantification corpus.",
            "Preserve reporter-channel assignments for TMTpro-labeled samples.",
            "Keep label-chemistry assumptions explicit in any downstream interpretation.",
        ),
        benchmark_package=WorkflowBenchmarkPackage(
            package_id="benchmark_package:multiplex_tmtpro_review_package",
            package_summary="Multiplex benchmark package ties a tracked public package to reporter features and multiplex design so channel and chemistry pressure stay outsider-readable.",
            promotion_goal="Keep multiplex authority anchored in the tracked public package instead of a thinner TMTpro fixture bundle.",
            realism_pressures=(
                "reference-channel and pooled-reference dependence pressure across paired plexes",
                "missing-channel and imbalance pressure that keeps multiplex review from reading like label-free abundance truth",
            ),
            transparent_assumptions=(
                "the package models bounded TMTpro behavior rather than severe production-scale carrier overload",
                "channel-aware review remains the governed output, not vendor-specific TMT execution parity",
            ),
            governed_output_surfaces=(
                "quantification.label_based_quant_bundle",
                "quantification.multiplex_balance",
            ),
            package_artifacts=(
                BenchmarkPackageArtifact(
                    artifact_id="multiplex_stress_bundle:feature_table",
                    artifact_kind=BenchmarkPackageArtifactKind.FEATURE_TABLE,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/quant/multiplex_ms1_features.tsv",
                    note="Reporter-channel feature evidence that carries imbalance and carrier-shape pressure.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="multiplex_stress_bundle:design_table",
                    artifact_kind=BenchmarkPackageArtifactKind.DESIGN_TABLE,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/quant/multiplex.design.tsv",
                    note="Multiplex design table that keeps group, channel, and pooled-reference roles explicit.",
                ),
            ),
            reproduction_steps=(
                BenchmarkReproductionStep(
                    step_id="inspect_channel_roles",
                    summary="Review multiplex groups, channel identities, and pooled-reference roles before any label-based rollup is trusted.",
                    artifact_ids=("multiplex_stress_bundle:design_table",),
                    expected_outputs=(
                        "reference-channel dependence remains explicit",
                        "missing-channel pressure can be traced back to governed channel roles",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="assemble_label_based_quant_bundle",
                    summary="Replay reporter-aware quantification and preserve missing channels instead of forcing a falsely complete plex.",
                    artifact_ids=(
                        "multiplex_stress_bundle:feature_table",
                        "multiplex_stress_bundle:design_table",
                    ),
                    expected_outputs=(
                        "reporter-channel assignments remain stable",
                        "missing channels remain explicit review caveats",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="check_balance_and_interference_pressure",
                    summary="Use channel balance diagnostics to keep imbalance and chemistry caveats visible during interpretation.",
                    artifact_ids=("multiplex_stress_bundle:feature_table",),
                    expected_outputs=(
                        "imbalance and carrier-driven pressure stay review-visible",
                        "multiplex support remains bounded by chemistry-aware caveats",
                    ),
                ),
            ),
        ),
        comparison_notes=(
            "Compare reporter handling against the tracked multiplex public package because direct vendor-specific multiplex pipelines are not executed here.",
            "Limit support claims to channel semantics and chemistry caveats, not full external pipeline parity.",
        ),
        exclusion_notes=(
            "Excludes label-free abundance interpretation and any claim that reporter summaries erase multiplex interference.",
            "Excludes vendor-pipeline parity claims beyond the checked-in multiplex fixture and published chemistry framing.",
        ),
        weakness_notes=(
            "The public package surface is still narrower than production multiplex cohorts with more severe missing-channel and interference behavior.",
            "Channel stability can look stronger than the underlying protein-level certainty actually is.",
        ),
        fixture_realism_limits=(
            "The multiplex fixture does not exercise the strongest carrier overload, interference, or unbalanced cohort behavior seen in production.",
            "Reporter stability under this fixture does not authorize label-free-style decision claims.",
        ),
        failure_mode_notes=(
            "Reporter-channel summaries can be over-read as label-free abundance evidence when chemistry caveats are dropped.",
            "Rollup outputs can stay numerically stable while missing-channel pressure is hidden from reviewers.",
        ),
        expected_failure_conditions=(
            "Reporter-channel assignments drift or collapse during quantification rollup.",
            "Channel-level caveats disappear from the final interpretation surface.",
        ),
        non_transfer_zones=(
            "Severe interference, carrier overload, and vendor-specific multiplex tuning outside the bundled fixture.",
            "Claims that reporter summaries are interchangeable with label-free abundance truth.",
        ),
        supported_repo_claims=(
            "Multiplex review preserves TMTpro reporter semantics, missing-channel visibility, and balance caveats across the bundled fixture",
            "Multiplex benchmark outputs can support review-grade interpretation when channel chemistry limits remain explicit",
        ),
        last_reviewed_on=date(2026, 5, 7),
        freshness_window_days=365,
        obsolescence_conditions=(
            "Multiplex channel mappings or fixture design change without metadata refresh.",
            "Supported multiplex chemistry families change without benchmark scope review.",
        ),
        retirement_conditions=(
            "Retire this benchmark from release-facing authority if it remains stale beyond two review windows.",
            "Retire this benchmark from scientific authority if multiplex claims widen beyond TMTpro channel semantics without a stronger truth tier.",
        ),
    ),
    BenchmarkManifest(
        benchmark_id="benchmark:targeted_transition_quality_control",
        workflow_family=KnowledgeWorkflowFamily.TARGETED,
        title="Targeted transition public benchmark package",
        scientific_focus="Transition-level quality checks and operator consequence packets over a tracked targeted public package.",
        evidence_tier=BenchmarkEvidenceTier.EXTERNAL_REPRODUCTION_PACKAGE,
        dataset_id="dataset:targeted_transition_review_package",
        dataset_locator="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/targeted_transition_review_package/package_manifest.json",
        organism="human",
        sample_complexity="targeted chromatogram QC fixture with bounded transition diversity and shared-peptide caution",
        label_strategy="targeted transition monitoring",
        sample_count=2,
        replicate_count=2,
        acquisition_mode="targeted acquisition",
        truth_surfaces=(
            "transition-level QC retention",
            "bounded protein-rollup caution",
            "chromatogram-derived operator review signals",
        ),
        success_metric="Stable transition-level QC summaries for bundled chromatogram evidence.",
        result_claim="Targeted-style chromatogram summaries should preserve transition-level evidence and protein-inference caution when rolled up.",
        cross_check_status=BenchmarkCrossCheckStatus.INTERNAL_ONLY,
        cross_check_note="The manifest is grounded in a tracked targeted public package with QC and follow-up packets, not in a live vendor targeted workflow.",
        primary_citation_ids=("citation:protein_inference_2012",),
        corpus_ids=(
            "corpus:chromatogram_qc_fixture",
            "corpus:protein_inference_review_reference",
        ),
        benchmark_rationale="Targeted outputs often collapse transition evidence quickly, so the benchmark captures how much interpretation can safely happen before protein-level rollup.",
        version_trace=(
            "The benchmark is pinned to the checked-in targeted public package and current protein-inference reference links reviewed on 2026-05-07.",
        ),
        retrieval_trace=(
            "Dataset paths and linked targeted reference corpora were re-verified on 2026-05-07 before the benchmark contract was refreshed.",
        ),
        dataset_license_and_reuse_note="The checked-in chromatogram fixture is reused as internal benchmark evidence and does not widen redistribution rights for vendor targeted outputs beyond the repository snapshot.",
        instrument_profiles=("Triple quadrupole", "Orbitrap"),
        reproduction_requirements=(
            "Use the bundled chromatogram QC fixture as the targeted evidence source.",
            "Keep transition-level measures intact before protein-level summary.",
            "Report any protein rollup with explicit inference caution.",
        ),
        benchmark_package=WorkflowBenchmarkPackage(
            package_id="benchmark_package:targeted_transition_review_package",
            package_summary="Targeted benchmark package ties a tracked public package to transition QC evidence and approved, failed, and refused follow-up packets so operator risk stays outsider-readable.",
            promotion_goal="Keep targeted authority anchored in the tracked public package instead of a thinner chromatogram QC bundle.",
            realism_pressures=(
                "transition reproducibility pressure through supported, failed, and refused targeted follow-up packets",
                "control and interference pressure that keeps operator-facing targeted review honest about execution risk",
            ),
            transparent_assumptions=(
                "the bundle proves targeted review governance rather than live Skyline or vendor chromatogram parity",
                "calibration and control pressure are modeled through review packets and QC tables, not through raw vendor traces",
            ),
            governed_output_surfaces=(
                "formats.targeted_qc_ingestion",
                "lab.targeted_follow_up_handoff",
            ),
            package_artifacts=(
                BenchmarkPackageArtifact(
                    artifact_id="targeted_control_bundle:qc_table",
                    artifact_kind=BenchmarkPackageArtifactKind.TARGETED_QC_TABLE,
                    repo_relative_path="packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv",
                    note="Chromatogram-shaped QC table that anchors transition-level review.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="targeted_control_bundle:approved_follow_up",
                    artifact_kind=BenchmarkPackageArtifactKind.FOLLOW_UP_PACKET,
                    repo_relative_path="packages/bijux-proteomics-lab/tests/fixtures/handoffs/supported_targeted_follow_up.json",
                    note="Execution-ready targeted packet that keeps reproducible approval posture visible.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="targeted_control_bundle:failed_follow_up",
                    artifact_kind=BenchmarkPackageArtifactKind.FOLLOW_UP_PACKET,
                    repo_relative_path="packages/bijux-proteomics-lab/tests/fixtures/handoffs/failed_targeted_transition_follow_up.json",
                    note="Failed transition packet that carries control gaps and likely assay-failure pressure.",
                ),
                BenchmarkPackageArtifact(
                    artifact_id="targeted_control_bundle:refused_follow_up",
                    artifact_kind=BenchmarkPackageArtifactKind.FOLLOW_UP_PACKET,
                    repo_relative_path="packages/bijux-proteomics-lab/tests/fixtures/handoffs/refused_targeted_follow_up.json",
                    note="Refused targeted packet that keeps weak science and missing controls from being laundered into execution.",
                ),
            ),
            reproduction_steps=(
                BenchmarkReproductionStep(
                    step_id="inspect_transition_qc_surface",
                    summary="Review the chromatogram-shaped QC table before any targeted support claim is escalated.",
                    artifact_ids=("targeted_control_bundle:qc_table",),
                    expected_outputs=(
                        "transition-level evidence remains the primary review surface",
                        "protein-level certainty stays secondary to QC and inference caution",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="compare_approved_and_failed_follow_up_packets",
                    summary="Use approved and failed handoff packets to keep control coverage, heavy standards, and execution-safe transitions explicit.",
                    artifact_ids=(
                        "targeted_control_bundle:approved_follow_up",
                        "targeted_control_bundle:failed_follow_up",
                    ),
                    expected_outputs=(
                        "transition reproducibility pressure remains operator-visible",
                        "missing controls remain explicit blockers instead of hidden assumptions",
                    ),
                ),
                BenchmarkReproductionStep(
                    step_id="preserve_refusal_boundaries",
                    summary="Keep refused targeted packets in the package so weak science and high-risk transitions remain part of the benchmark truth surface.",
                    artifact_ids=("targeted_control_bundle:refused_follow_up",),
                    expected_outputs=(
                        "interference and control risk remain visible in review outputs",
                        "targeted support claims stop before weak science is turned into executable spend",
                    ),
                ),
            ),
        ),
        comparison_notes=(
            "Compare targeted QC handling against the tracked targeted public package and published protein-inference caution rather than claiming direct vendor chromatogram parity.",
            "Keep support claims scoped to transition-level evidence retention and cautious rollup semantics.",
        ),
        exclusion_notes=(
            "Excludes direct vendor chromatogram parity and any claim that transition-level QC alone resolves shared-peptide ambiguity.",
            "Excludes unqualified protein certainty when the benchmark only proves cautious transition retention and rollup visibility.",
        ),
        weakness_notes=(
            "The public package evidence is still operationally tidy compared with noisier targeted production runs and carryover scenarios.",
            "Transition retention is easier to prove than protein-specific interpretability in shared-peptide settings.",
        ),
        fixture_realism_limits=(
            "The targeted fixture does not cover vendor-specific chromatogram quirks, calibration standards, or messy carryover behavior.",
            "Transition retention under this fixture does not authorize direct protein certainty claims.",
        ),
        failure_mode_notes=(
            "Transition-level evidence can be collapsed into protein certainty too early if inference caution is not preserved.",
            "QC summaries can stay stable while chromatogram-specific edge cases remain outside the benchmarked fixture surface.",
        ),
        expected_failure_conditions=(
            "Transition QC stays numerically stable while rollup removes protein-inference caution.",
            "Chromatogram warnings are flattened into a clean targeted-support claim.",
        ),
        non_transfer_zones=(
            "Vendor-specific chromatogram behavior, calibration standards, and transition-interference edge cases outside the bundled fixture.",
            "Claims that targeted QC alone resolves shared-peptide ambiguity or confirms protein truth.",
        ),
        supported_repo_claims=(
            "Targeted benchmark outputs preserve transition-level QC evidence and explicit protein-inference caution across the bundled chromatogram fixture",
            "Targeted review can support operator-facing QC interpretation without pretending to prove vendor-parity targeted biology",
        ),
        last_reviewed_on=date(2026, 5, 7),
        freshness_window_days=365,
        obsolescence_conditions=(
            "Targeted fixture schema changes without updated transition-level metadata.",
            "Targeted support claims expand into vendor or calibration parity without new benchmark evidence.",
        ),
        retirement_conditions=(
            "Retire this benchmark from release-facing authority if it remains stale beyond two review windows.",
            "Retire this benchmark from scientific authority if targeted claims widen into vendor or calibration parity without a stronger benchmark tier.",
        ),
    ),
)


__all__ = [
    "BenchmarkEvidenceTier",
    "BenchmarkManifest",
    "BenchmarkCrossCheckStatus",
    "BenchmarkPackageArtifact",
    "BenchmarkPackageArtifactKind",
    "BenchmarkReproductionStep",
    "DEFAULT_BENCHMARK_MANIFESTS",
    "KnowledgeWorkflowFamily",
    "WorkflowBenchmarkPackage",
]
