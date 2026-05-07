# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship public benchmark packages that anchor scientific trust claims."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class FlagshipPublicEvidenceKind(StrEnum):
    """Dominant evidence kind used to anchor one public benchmark asset."""

    ARTIFACT_INVENTORY = "artifact_inventory"
    BENCHMARK_PACKAGE_MANIFEST = "benchmark_package_manifest"
    RAW_SPECTRA = "raw_spectra"
    IMPORTED_SEARCH_RESULTS = "imported_search_results"
    QUANT_FEATURE_TABLE = "quant_feature_table"
    PTM_LOCALIZATION_TABLE = "ptm_localization_table"
    REFERENCE_FASTA = "reference_fasta"
    SCIENTIFIC_INVARIANT_LEDGER = "scientific_invariant_ledger"
    EXPERIMENTAL_DESIGN = "experimental_design"
    EXPECTATION_MANIFEST = "expectation_manifest"
    WARNING_DEMONSTRATION_LEDGER = "warning_demonstration_ledger"


class FlagshipPublicBenchmarkAsset(JsonModel):
    """One governed asset that makes a flagship benchmark package inspectable."""

    model_config = ConfigDict(extra="forbid")

    asset_role: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    evidence_kind: FlagshipPublicEvidenceKind
    public_identity_note: str = Field(..., min_length=1)


class FlagshipPublicBenchmarkPackage(JsonModel):
    """Public benchmark package that becomes a primary scientific proof surface."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    package_label: str = Field(..., min_length=1)
    replaced_proof_surface: str = Field(..., min_length=1)
    source_assets: tuple[FlagshipPublicBenchmarkAsset, ...] = Field(
        default_factory=tuple
    )
    expected_review_artifacts: tuple[str, ...] = Field(default_factory=tuple)
    scientific_pressures: tuple[str, ...] = Field(default_factory=tuple)
    claim_scope: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class FlagshipPublicBenchmarkCatalog(JsonModel):
    """Catalog of flagship public benchmark packages used by core proof surfaces."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[FlagshipPublicBenchmarkPackage, ...] = Field(default_factory=tuple)


def _dda_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    return (
        FlagshipPublicBenchmarkAsset(
            asset_role="package_manifest",
            path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/package_manifest.json",
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note=(
                "the tracked package manifest is the current machine-readable anchor for the public DDA benchmark center"
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="artifact_inventory",
            path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/artifact_inventory.json",
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note=(
                "artifact inventory keeps digests, row counts, and reviewer notes visible from files alone"
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="scientific_invariants",
            path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/scientific_invariants.json",
            evidence_kind=FlagshipPublicEvidenceKind.SCIENTIFIC_INVARIANT_LEDGER,
            public_identity_note=(
                "numeric invariants stop the DDA flagship package from reading like structure-only packaging"
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="warning_demonstrations",
            path="packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/warning_demonstrations.json",
            evidence_kind=FlagshipPublicEvidenceKind.WARNING_DEMONSTRATION_LEDGER,
            public_identity_note=(
                "warning demonstrations turn protein-rollup caution into concrete public evidence"
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="spectra",
            path="packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
            evidence_kind=FlagshipPublicEvidenceKind.RAW_SPECTRA,
            public_identity_note=(
                "raw tandem spectra keep the flagship DDA package tied to inspectable evidence rather than a closed export alone"
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="primary_search_results",
            path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "the primary MaxQuant export anchors the reviewable runtime import lane in a governed checked-in result table"
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="comparator_search_results",
            path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "the paired MSFragger export keeps cross-engine DDA warning pressure public and reviewable"
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="experimental_design",
            path="packages/bijux-proteomics-core/tests/fixtures/production_run/design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note=(
                "design metadata keeps downstream review tied to the actual sample structure"
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="expectation_manifest",
            path="packages/bijux-proteomics-core/tests/fixtures/production_run/workflow_end_to_end_expectations.json",
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note=(
                "workflow expectations keep the flagship package linked to explicit review and runtime outputs"
            ),
        ),
    )


def build_flagship_dda_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    """Build the flagship public DDA package that replaces a closed fixture center."""

    return FlagshipPublicBenchmarkPackage(
        package_id="flagship_public_package:dda_reviewable_run",
        workflow_family="dda",
        package_label="Flagship public DDA reviewable run",
        replaced_proof_surface="legacy_fixture_bundle:dda_mini_study",
        source_assets=_dda_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/reviewable-proteomics/runtime/sequence_intake.json",
            "artifacts/workflows/reviewable-proteomics/runtime/qc_report.json",
            "artifacts/workflows/reviewable-proteomics/runtime/review_packet.json",
            "artifacts/workflows/reviewable-proteomics/core/scientific_kernel.json",
        ),
        scientific_pressures=(
            "calibration drift",
            "protein inference ambiguity",
            "target-decoy collisions",
            "cross-engine protein rollup drift",
        ),
        claim_scope=(
            "primary DDA credibility should now be described against the tracked public package with raw spectra, paired imported results, invariant ledgers, and explicit warning demonstrations."
        ),
        note=(
            "This package becomes the main DDA proof center and demotes the earlier DDA mini-study surface to legacy regression support only."
        ),
    )


def build_flagship_lfq_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    """Build the flagship public LFQ package for quantification proof."""

    return FlagshipPublicBenchmarkPackage(
        package_id="flagship_public_package:lfq_study_scale",
        workflow_family="lfq",
        package_label="Flagship public LFQ study-scale matrix",
        replaced_proof_surface="closed_fixture_bundle:lfq_tidy_matrix_only",
        source_assets=(
            FlagshipPublicBenchmarkAsset(
                asset_role="feature_table",
                path="packages/bijux-proteomics-core/tests/fixtures/quant/study_scale_ms1_features.tsv",
                evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
                public_identity_note=(
                    "study-scale MS1 features provide the quantitative evidence bed instead of a tiny hand-made bundle"
                ),
            ),
            FlagshipPublicBenchmarkAsset(
                asset_role="experimental_design",
                path="packages/bijux-proteomics-core/tests/fixtures/quant/study_scale.design.tsv",
                evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
                public_identity_note=(
                    "study-scale design metadata preserves cohort structure, batches, and replicate shape"
                ),
            ),
            FlagshipPublicBenchmarkAsset(
                asset_role="reproducibility_manifest",
                path="packages/bijux-proteomics-core/tests/fixtures/quant/quant_reproducibility_manifest.json",
                evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
                public_identity_note=(
                    "reproducibility expectations keep quant outputs tied to explicit public benchmark consequences"
                ),
            ),
        ),
        expected_review_artifacts=(
            "artifacts/workflows/reviewable-proteomics/runtime/quant_bundle.json",
            "artifacts/workflows/reviewable-proteomics/runtime/missingness_profile.json",
            "artifacts/workflows/reviewable-proteomics/runtime/differential_report.json",
            "artifacts/workflows/reviewable-proteomics/core/quant_review_packet.json",
        ),
        scientific_pressures=(
            "realistic missingness",
            "batch drift",
            "effect-size instability",
            "multiple-testing pressure",
        ),
        claim_scope=(
            "LFQ credibility should now be anchored in study-scale public quant evidence rather than tidy closed matrices."
        ),
        note=(
            "This package makes public cohort shape, missingness burden, and reproducibility expectations the center of LFQ proof."
        ),
    )


def build_flagship_ptm_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    """Build the flagship public PTM package for localization and occupancy proof."""

    return FlagshipPublicBenchmarkPackage(
        package_id="flagship_public_package:ptm_localization_bundle",
        workflow_family="ptm",
        package_label="Flagship public PTM localization bundle",
        replaced_proof_surface="closed_fixture_bundle:ptm_localization_only",
        source_assets=(
            FlagshipPublicBenchmarkAsset(
                asset_role="localization_table",
                path="packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv",
                evidence_kind=FlagshipPublicEvidenceKind.PTM_LOCALIZATION_TABLE,
                public_identity_note=(
                    "site localization evidence keeps PTM review tied to inspectable spectrum-linked assignments"
                ),
            ),
            FlagshipPublicBenchmarkAsset(
                asset_role="quant_feature_table",
                path="packages/bijux-proteomics-core/tests/fixtures/ptm/ptm_features.tsv",
                evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
                public_identity_note=(
                    "PTM feature intensities anchor occupancy and ambiguity propagation in an inspectable feature surface"
                ),
            ),
            FlagshipPublicBenchmarkAsset(
                asset_role="reference_fasta",
                path="packages/bijux-proteomics-core/tests/fixtures/fasta/ptm_sites.fasta",
                evidence_kind=FlagshipPublicEvidenceKind.REFERENCE_FASTA,
                public_identity_note=(
                    "reference sequence context preserves exact site coordinates for flagship PTM review"
                ),
            ),
            FlagshipPublicBenchmarkAsset(
                asset_role="raw_spectra",
                path="packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
                evidence_kind=FlagshipPublicEvidenceKind.RAW_SPECTRA,
                public_identity_note=(
                    "raw spectra keep fragment-linked PTM validation and rescoring pressure tied to a concrete evidence surface"
                ),
            ),
        ),
        expected_review_artifacts=(
            "artifacts/workflows/reviewable-proteomics/runtime/ptm_localization_report.json",
            "artifacts/workflows/reviewable-proteomics/runtime/ptm_occupancy_report.json",
            "artifacts/workflows/reviewable-proteomics/runtime/ptm_lab_targeting_packet.json",
            "artifacts/workflows/reviewable-proteomics/core/ptm_scientific_review.json",
        ),
        scientific_pressures=(
            "site ambiguity",
            "occupancy uncertainty",
            "motif credibility stress",
            "lab-targeting burden",
        ),
        claim_scope=(
            "PTM credibility should now be described against public localization, occupancy, and raw-spectrum-linked evidence rather than a narrow closed PTM fixture."
        ),
        note=(
            "This package turns ambiguity, occupancy, and raw-spectrum validation into a public PTM proof center."
        ),
    )


def list_flagship_public_benchmark_packages() -> tuple[FlagshipPublicBenchmarkPackage, ...]:
    """Return the flagship public packages that anchor core proof surfaces today."""

    return (
        build_flagship_dda_public_benchmark_package(),
        build_flagship_lfq_public_benchmark_package(),
        build_flagship_ptm_public_benchmark_package(),
    )


def build_flagship_public_benchmark_catalog() -> FlagshipPublicBenchmarkCatalog:
    """Build the catalog of flagship public benchmark packages."""

    return FlagshipPublicBenchmarkCatalog(
        entries=list_flagship_public_benchmark_packages()
    )


__all__ = [
    "FlagshipPublicBenchmarkAsset",
    "FlagshipPublicBenchmarkCatalog",
    "FlagshipPublicBenchmarkPackage",
    "FlagshipPublicEvidenceKind",
    "build_flagship_dda_public_benchmark_package",
    "build_flagship_lfq_public_benchmark_package",
    "build_flagship_ptm_public_benchmark_package",
    "build_flagship_public_benchmark_catalog",
    "list_flagship_public_benchmark_packages",
]
