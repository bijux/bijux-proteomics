# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship public benchmark packages that anchor scientific trust claims."""

from __future__ import annotations

import csv
from datetime import date
from enum import StrEnum
import hashlib
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.flagship_asset_roots import (
    flagship_asset_root,
)
from bijux_proteomics_foundation import JsonModel


class FlagshipPublicEvidenceKind(StrEnum):
    """Dominant evidence kind used to anchor one public benchmark asset."""

    ARTIFACT_INVENTORY = "artifact_inventory"
    BENCHMARK_PACKAGE_MANIFEST = "benchmark_package_manifest"
    BENCHMARK_README = "benchmark_readme"
    CITATION_MANIFEST = "citation_manifest"
    FOLLOW_UP_PACKET = "follow_up_packet"
    GENERATED_BOUNDARY_MANIFEST = "generated_boundary_manifest"
    PACKAGE_LIFECYCLE_RECORD = "package_lifecycle_record"
    PACKAGE_QUALITY_SHEET = "package_quality_sheet"
    RAW_SPECTRA = "raw_spectra"
    REBUILD_INSTRUCTIONS = "rebuild_instructions"
    SOURCE_LOCATOR_MANIFEST = "source_locator_manifest"
    IMPORTED_SEARCH_RESULTS = "imported_search_results"
    QUANT_FEATURE_TABLE = "quant_feature_table"
    PTM_LOCALIZATION_TABLE = "ptm_localization_table"
    REFERENCE_FASTA = "reference_fasta"
    SCIENTIFIC_INVARIANT_LEDGER = "scientific_invariant_ledger"
    EXPERIMENTAL_DESIGN = "experimental_design"
    EXPECTATION_MANIFEST = "expectation_manifest"
    TARGETED_RESULT_TABLE = "targeted_result_table"
    TARGETED_QC_TABLE = "targeted_qc_table"
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
    package_root: str = Field(..., min_length=1)
    benchmark_manifest_path: str = Field(..., min_length=1)
    artifact_inventory_path: str = Field(..., min_length=1)
    quality_sheet_path: str = Field(..., min_length=1)
    lifecycle_record_path: str = Field(..., min_length=1)
    source_locator_manifest_path: str = Field(..., min_length=1)
    citation_manifest_path: str = Field(..., min_length=1)
    generated_boundary_path: str = Field(..., min_length=1)
    rebuild_instructions_path: str = Field(..., min_length=1)
    replaced_proof_surface: str = Field(..., min_length=1)
    public_dataset_identity: str = Field(..., min_length=1)
    runtime_availability: str = Field(..., min_length=1)
    comparator_availability: str = Field(..., min_length=1)
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


class FlagshipPublicPackageArtifactRecord(JsonModel):
    """One concrete file tracked inside a flagship public package root."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    repo_relative_path: str = Field(..., min_length=1)
    evidence_kind: FlagshipPublicEvidenceKind
    sha256: str = Field(..., min_length=64, max_length=64)
    row_count: int | None = Field(default=None, ge=0)
    spectra_count: int | None = Field(default=None, ge=0)
    note: str = Field(..., min_length=1)


class FlagshipPublicPackageArtifactInventory(JsonModel):
    """Machine-readable inventory for one flagship public benchmark package."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    inventory_path: str = Field(..., min_length=1)
    artifacts: tuple[FlagshipPublicPackageArtifactRecord, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class FlagshipPublicPackageQualitySheet(JsonModel):
    """One outsider-readable quality sheet for a flagship public package."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    quality_path: str = Field(..., min_length=1)
    raw_identity_state: str = Field(..., min_length=1)
    runtime_state: str = Field(..., min_length=1)
    comparator_state: str = Field(..., min_length=1)
    lab_consequence_state: str = Field(..., min_length=1)
    current_readiness: str = Field(..., min_length=1)
    exact_strengths: tuple[str, ...] = Field(default_factory=tuple)
    exact_blockers: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class FlagshipPublicPackageLifecycleRecord(JsonModel):
    """Lifecycle, refresh, and retirement rules for one public package."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    lifecycle_path: str = Field(..., min_length=1)
    created_on: date
    last_refreshed_on: date
    obsolescence_triggers: tuple[str, ...] = Field(default_factory=tuple)
    retirement_conditions: tuple[str, ...] = Field(default_factory=tuple)
    successor_package_id: str | None = None
    note: str = Field(..., min_length=1)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _repo_path(repo_relative_path: str) -> Path:
    return _repo_root() / repo_relative_path


def _sha256(repo_relative_path: str) -> str:
    return hashlib.sha256(_repo_path(repo_relative_path).read_bytes()).hexdigest()


def _tsv_row_count(repo_relative_path: str) -> int:
    with _repo_path(repo_relative_path).open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter="\t"))


def _mgf_spectrum_count(repo_relative_path: str) -> int:
    return (
        _repo_path(repo_relative_path).read_text(encoding="utf-8").count("BEGIN IONS")
    )


def _optional_row_count(asset: FlagshipPublicBenchmarkAsset) -> int | None:
    if asset.path.endswith(".tsv"):
        return _tsv_row_count(asset.path)
    return None


def _optional_spectrum_count(asset: FlagshipPublicBenchmarkAsset) -> int | None:
    if asset.path.endswith(".mgf"):
        return _mgf_spectrum_count(asset.path)
    return None


def _inventory_records(
    package: FlagshipPublicBenchmarkPackage,
) -> tuple[FlagshipPublicPackageArtifactRecord, ...]:
    return tuple(
        FlagshipPublicPackageArtifactRecord(
            artifact_id=f"{package.workflow_family}:{asset.asset_role}",
            repo_relative_path=asset.path,
            evidence_kind=asset.evidence_kind,
            sha256=_sha256(asset.path),
            row_count=_optional_row_count(asset),
            spectra_count=_optional_spectrum_count(asset),
            note=asset.public_identity_note,
        )
        for asset in package.source_assets
    )


def _quality_path(package_root: str) -> str:
    return f"{package_root}/quality_sheet.json"


def _lifecycle_path(package_root: str) -> str:
    return f"{package_root}/lifecycle.json"


def _package_root(dir_name: str) -> str:
    return flagship_asset_root(dir_name)


def _package_manifest_path(package_root: str) -> str:
    return f"{package_root}/package_manifest.json"


def _artifact_inventory_path(package_root: str) -> str:
    return f"{package_root}/artifact_inventory.json"


def _readme_path(package_root: str) -> str:
    return f"{package_root}/README.md"


def _source_locator_manifest_path(package_root: str) -> str:
    return f"{package_root}/source_locator_manifest.json"


def _citation_manifest_path(package_root: str) -> str:
    return f"{package_root}/citation_manifest.json"


def _generated_boundary_path(package_root: str) -> str:
    return f"{package_root}/generated_boundary.json"


def _rebuild_instructions_path(package_root: str) -> str:
    return f"{package_root}/rebuild_instructions.md"


def _dda_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("dda_reviewable_run")
    return (
        FlagshipPublicBenchmarkAsset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note=(
                "The DDA package README is the first outsider-facing statement of what the tracked package can and cannot prove."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note=(
                "The tracked package manifest is the current machine-readable anchor for the public DDA benchmark center."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note=(
                "Artifact inventory keeps digests, row counts, and reviewer notes visible from files alone."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note=(
                "The quality sheet makes raw identity, runtime state, comparator state, and lab consequence state explicit without reading code."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="lifecycle_record",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note=(
                "The lifecycle record says when this package goes stale and what must replace it before authority widens."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note=(
                "The source locator manifest says exactly which copied snapshots and public reference pages make the DDA package rebuildable."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note=(
                "The citation manifest keeps the public scientific references explicit instead of burying them in prose."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note=(
                "The generated boundary file tells outsiders which DDA package files are copied snapshots, generated metadata, or hand-curated explanation."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note=(
                "The rebuild instructions turn the DDA package from a static tree into a governed asset root."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="scientific_invariants",
            path=f"{package_root}/scientific_invariants.json",
            evidence_kind=FlagshipPublicEvidenceKind.SCIENTIFIC_INVARIANT_LEDGER,
            public_identity_note=(
                "Numeric invariants stop the DDA flagship package from reading like structure-only packaging."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="warning_demonstrations",
            path=f"{package_root}/warning_demonstrations.json",
            evidence_kind=FlagshipPublicEvidenceKind.WARNING_DEMONSTRATION_LEDGER,
            public_identity_note=(
                "Warning demonstrations turn protein-rollup caution into concrete public evidence."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="spectra",
            path=f"{package_root}/evidence/spectra.mgf",
            evidence_kind=FlagshipPublicEvidenceKind.RAW_SPECTRA,
            public_identity_note=(
                "Raw tandem spectra keep the flagship DDA package tied to inspectable evidence rather than a closed export alone."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="primary_search_results",
            path=f"{package_root}/primary/maxquant_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The primary MaxQuant export anchors the reviewable runtime import lane in a governed checked-in result table."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="comparator_search_results",
            path=f"{package_root}/comparator/msfragger_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The paired MSFragger export keeps cross-engine DDA warning pressure public and reviewable."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="experimental_design",
            path=f"{package_root}/evidence/design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note=(
                "Design metadata keeps downstream review tied to the actual sample structure."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="expectation_manifest",
            path=f"{package_root}/evidence/workflow_end_to_end_expectations.json",
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note=(
                "Workflow expectations keep the flagship package linked to explicit review and runtime outputs."
            ),
        ),
    )


def _dia_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("dia_library_review_package")
    return (
        FlagshipPublicBenchmarkAsset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note=(
                "The DIA package README defines exactly where library-conditioned evidence stops and where vendor-execution parity is still absent."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note=(
                "The DIA manifest is the machine-readable entrypoint for the flagship library-conditioned review package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note=(
                "The DIA artifact inventory keeps digests, row counts, and dependency edges explicit."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note=(
                "The DIA quality sheet says plainly that the public package is import-backed and library-conditioned."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="lifecycle_record",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note=(
                "The DIA lifecycle record states which missing runtime and chromatogram pressures would obsolete this package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note=(
                "The source locator manifest keeps copied DIA snapshots and public tool pages tied together in one rebuildable surface."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note=(
                "The citation manifest keeps library-conditioned DIA references inspectable from files alone."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note=(
                "The generated boundary file says which DIA asset-root files are copied evidence versus generated metadata."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note=(
                "The rebuild instructions define how to refresh the DIA asset root without treating it like a hidden test bundle."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="spectronaut_report",
            path=f"{package_root}/primary/spectronaut_report.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The Spectronaut-style report anchors one public DIA extraction view with explicit library-conditioned assumptions."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="spectronaut_pipeline_export",
            path=f"{package_root}/primary/spectronaut_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The Spectronaut-style pipeline export exposes adapter field coverage and DIA review drift risk."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="spectronaut_settings",
            path=f"{package_root}/primary/spectronaut_settings.txt",
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note=(
                "Pinned settings keep library and extraction assumptions inspectable instead of implied."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="diann_pipeline_export",
            path=f"{package_root}/comparator/diann_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The DIA-NN-style export is the current external confrontation partner for library-conditioned DIA review."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="diann_config",
            path=f"{package_root}/comparator/diann_config.json",
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note=(
                "The DIA-NN-style config snapshot keeps classifier and library assumptions visible beside the export."
            ),
        ),
    )


def _lfq_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("lfq_cohort_review_package")
    return (
        FlagshipPublicBenchmarkAsset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note=(
                "The LFQ package README names the cohort-shaped evidence, missingness burden, and the current runtime gap."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note=(
                "The LFQ manifest is the machine-readable anchor for the study-scale public review package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note=(
                "The LFQ artifact inventory keeps feature, design, and reproducibility surfaces auditably tied together."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note=(
                "The LFQ quality sheet states clearly that package substance is ahead of runtime and comparator closure."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="lifecycle_record",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note=(
                "The LFQ lifecycle record names the missing runtime and truth-surface upgrades needed before stronger claims are allowed."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note=(
                "The source locator manifest makes the copied LFQ cohort snapshots and public method references rebuildable."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note=(
                "The citation manifest keeps LFQ missingness and normalization references explicit."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note=(
                "The generated boundary file distinguishes copied cohort evidence from generated LFQ package metadata."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note=(
                "The rebuild instructions define how to refresh the LFQ asset root as a product surface rather than a test helper."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="feature_table",
            path=f"{package_root}/evidence/study_scale_ms1_features.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note=(
                "The study-scale MS1 table is the current public quantitative evidence bed for LFQ review."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="design_table",
            path=f"{package_root}/evidence/study_scale.design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note=(
                "The cohort-shaped design table keeps replicate, batch, and instrument structure explicit."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="reproducibility_manifest",
            path=f"{package_root}/evidence/quant_reproducibility_manifest.json",
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note=(
                "The reproducibility manifest keeps bounded repeatability outputs pinned beside the study-scale evidence."
            ),
        ),
    )


def _multiplex_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("multiplex_tmtpro_review_package")
    return (
        FlagshipPublicBenchmarkAsset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note=(
                "The multiplex package README states exactly which TMTpro chemistry claims are earned and which production-scale claims stay blocked."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note=(
                "The multiplex manifest is the machine-readable entrypoint for the TMTpro stress package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note=(
                "The multiplex artifact inventory keeps channel evidence, design metadata, and digest checks visible."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note=(
                "The multiplex quality sheet makes the package’s chemistry strength and runtime weakness visible at a glance."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="lifecycle_record",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note=(
                "The multiplex lifecycle record names the channel and carrier pressures that would obsolete this package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note=(
                "The source locator manifest keeps copied multiplex evidence and chemistry references rebuildable."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note=(
                "The citation manifest keeps the multiplex chemistry and ratio-compression references explicit."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note=(
                "The generated boundary file distinguishes copied multiplex evidence from generated package metadata."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note=(
                "The rebuild instructions define how to refresh the multiplex asset root as a durable product surface."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="reporter_table",
            path=f"{package_root}/evidence/tmt_reporter_table.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note=(
                "Reporter-channel evidence keeps bridge-channel gaps, interference pressure, and imbalance tied to tracked files."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="feature_table",
            path=f"{package_root}/evidence/multiplex_ms1_features.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note=(
                "The retained channel-level feature snapshot keeps runtime and challenge surfaces tied to the original multiplex intensity view."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="design_table",
            path=f"{package_root}/evidence/multiplex.design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note=(
                "The multiplex design table preserves pooled-reference and bridge-channel assignments."
            ),
        ),
    )


def _ptm_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("ptm_localization_review_package")
    return (
        FlagshipPublicBenchmarkAsset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note=(
                "The PTM package README explains what ambiguity, localization, and targetability limits still stay in force."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note=(
                "The PTM manifest is the machine-readable boundary for the localization review package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note=(
                "The PTM artifact inventory keeps localization, occupancy, raw-spectrum, and FASTA context visible together."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note=(
                "The PTM quality sheet makes clear that the package is real and inspectable but still blocked by runtime and comparator gaps."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="lifecycle_record",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note=(
                "The PTM lifecycle record states which rescoring, runtime, and PTM-family breadth upgrades would obsolete this package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note=(
                "The source locator manifest keeps copied PTM evidence and public localization references rebuildable."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note=(
                "The citation manifest keeps PTM localization references explicit in the asset root itself."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note=(
                "The generated boundary file distinguishes copied PTM evidence from generated package metadata."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note=(
                "The rebuild instructions define how to refresh the PTM asset root without treating it like test collateral."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="localization_table",
            path=f"{package_root}/evidence/localization_results.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.PTM_LOCALIZATION_TABLE,
            public_identity_note=(
                "Localization results keep ambiguous-site handling tied to tracked PTM evidence."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="ptm_feature_table",
            path=f"{package_root}/evidence/ptm_features.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note=(
                "PTM feature intensities keep occupancy interpretation grounded in tracked quantitative evidence."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="reference_fasta",
            path=f"{package_root}/evidence/ptm_sites.fasta",
            evidence_kind=FlagshipPublicEvidenceKind.REFERENCE_FASTA,
            public_identity_note=(
                "Reference sequence context preserves site coordinates and residue identity."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="raw_spectra",
            path=f"{package_root}/evidence/spectra.mgf",
            evidence_kind=FlagshipPublicEvidenceKind.RAW_SPECTRA,
            public_identity_note=(
                "Raw spectra keep fragment-linked PTM validation tied to a concrete evidence surface."
            ),
        ),
    )


def _targeted_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("targeted_transition_review_package")
    return (
        FlagshipPublicBenchmarkAsset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note=(
                "The targeted package README makes transition-level value and vendor-parity gaps explicit."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note=(
                "The targeted manifest is the machine-readable anchor for the transition-control review package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note=(
                "The targeted artifact inventory keeps QC tables and approved/failed/refused follow-up packets together."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note=(
                "The targeted quality sheet says directly that package evidence is ahead of runtime execution and comparator closure."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="lifecycle_record",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note=(
                "The targeted lifecycle record names the calibration, interference, and runtime upgrades needed before stronger claims are allowed."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note=(
                "The source locator manifest keeps copied targeted QC evidence and public assay references rebuildable."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note=(
                "The citation manifest keeps targeted assay discipline references explicit inside the asset root."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note=(
                "The generated boundary file distinguishes copied targeted evidence from generated metadata."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note=(
                "The rebuild instructions define how to refresh the targeted asset root as a product evidence surface."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="targeted_result_table",
            path=f"{package_root}/evidence/skyline_targeted_qc_results.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.TARGETED_RESULT_TABLE,
            public_identity_note=(
                "The Skyline-style targeted result table is the runnable benchmark input for matrix and assay-QC regeneration."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="targeted_design",
            path=f"{package_root}/evidence/skyline_targeted_qc.design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note=(
                "The targeted design preserves the replicate and condition structure needed for replicate-CV and validation review."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="targeted_validation_discovery_claims",
            path=(
                f"{package_root}/evidence/targeted_validation_discovery_claims.json"
            ),
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note=(
                "Discovery-claim inputs keep the public targeted benchmark validation run anchored to explicit candidate expectations."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="targeted_validation_panel_assays",
            path=f"{package_root}/evidence/targeted_validation_panel_assays.json",
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note=(
                "Panel-assay inputs bind the targeted benchmark candidates back to concrete peptide assays before verdicts are emitted."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="targeted_qc_table",
            path=f"{package_root}/evidence/targeted_benchmark_qc.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.TARGETED_QC_TABLE,
            public_identity_note=(
                "Transition-level QC evidence remains a tracked supporting layer beside the runnable targeted benchmark input."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="approved_follow_up",
            path=f"{package_root}/follow_up/supported_targeted_follow_up.json",
            evidence_kind=FlagshipPublicEvidenceKind.FOLLOW_UP_PACKET,
            public_identity_note=(
                "The approved targeted follow-up packet shows the current strongest operator-facing consequence of the package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="failed_follow_up",
            path=f"{package_root}/follow_up/failed_targeted_transition_follow_up.json",
            evidence_kind=FlagshipPublicEvidenceKind.FOLLOW_UP_PACKET,
            public_identity_note=(
                "The failed follow-up packet keeps control and transition failure pressure in the public package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="refused_follow_up",
            path=f"{package_root}/follow_up/refused_targeted_follow_up.json",
            evidence_kind=FlagshipPublicEvidenceKind.FOLLOW_UP_PACKET,
            public_identity_note=(
                "The refused follow-up packet stops weak targeted science from looking executable by omission."
            ),
        ),
    )


def build_flagship_dda_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    """Build the flagship public DDA package that replaces a closed fixture center."""

    package_root = _package_root("dda_reviewable_run")
    return FlagshipPublicBenchmarkPackage(
        package_id="flagship_public_package:dda_reviewable_run",
        workflow_family="dda",
        package_label="Flagship public DDA reviewable run",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="legacy_fixture_bundle:dda_mini_study",
        public_dataset_identity=(
            "tracked raw-like spectrum plus paired MaxQuant and MSFragger exported-result snapshots inside one outsider-readable DDA package"
        ),
        runtime_availability="import_only runtime lane exists and is reviewable",
        comparator_availability="MaxQuant-versus-MSFragger confrontation is shipped",
        source_assets=_dda_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/flagship-workflows/runtime/sequence_intake.json",
            "artifacts/workflows/flagship-workflows/runtime/qc_report.json",
            "artifacts/workflows/flagship-workflows/runtime/review_packet.json",
            "artifacts/workflows/flagship-workflows/core/scientific_kernel.json",
        ),
        scientific_pressures=(
            "calibration drift",
            "protein inference ambiguity",
            "target-decoy collisions",
            "cross-engine protein rollup drift",
        ),
        claim_scope=(
            "Primary DDA credibility should now be described against the tracked public package with raw spectra, paired imported results, invariant ledgers, and explicit warning demonstrations."
        ),
        note=(
            "This package is outsider-auditable and materially stronger than the old DDA mini-study center, but it still does not claim in-repo live-engine rerun parity."
        ),
    )


def build_flagship_dia_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    """Build the flagship public DIA package."""

    package_root = _package_root("dia_library_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="flagship_public_package:dia_library_review_package",
        workflow_family="dia",
        package_label="Flagship public DIA library review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="curated_fixture_bundle:dia_library_extraction_bundle",
        public_dataset_identity=(
            "tracked Spectronaut-style and DIA-NN-style exported-result snapshots with explicit library-conditioned settings and confrontation scope"
        ),
        runtime_availability="raw-executable runtime lane exists and remains library-conditioned",
        comparator_availability="Spectronaut-versus-DIA-NN confrontation is shipped",
        source_assets=_dia_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/flagship-workflows/runtime/review_packet.json",
            "artifacts/workflows/flagship-workflows/runtime/evidence_bundle.json",
            "artifacts/workflows/flagship-workflows/core/scientific_kernel.json",
        ),
        scientific_pressures=(
            "library incompleteness",
            "transition semantics drift",
            "protein-level absence overreach",
            "vendor extraction mismatch",
        ),
        claim_scope=(
            "DIA credibility is now anchored in a public package with paired exported-result surfaces, explicit library assumptions, and confrontation context instead of a hidden mini-study contract."
        ),
        note=(
            "This package is real and inspectable, and the runtime lane now executes it directly, but its authority still stops at library-conditioned review rather than chromatogram-level vendor parity."
        ),
    )


def build_flagship_lfq_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    """Build the flagship public LFQ package for quantification proof."""

    package_root = _package_root("lfq_cohort_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="flagship_public_package:lfq_cohort_review_package",
        workflow_family="lfq",
        package_label="Flagship public LFQ cohort review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="closed_fixture_bundle:lfq_tidy_matrix_only",
        public_dataset_identity=(
            "tracked study-scale feature and cohort-design snapshots with explicit missingness and repeatability boundaries"
        ),
        runtime_availability="raw-executable runtime lane exists and is reviewable",
        comparator_availability="bounded external comparator confrontation is shipped",
        source_assets=_lfq_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/flagship-workflows/runtime/quant_bundle.json",
            "artifacts/workflows/flagship-workflows/runtime/missingness_profile.json",
            "artifacts/workflows/flagship-workflows/runtime/differential_report.json",
        ),
        scientific_pressures=(
            "realistic missingness",
            "batch drift",
            "effect-size instability",
            "multiple-testing pressure",
        ),
        claim_scope=(
            "LFQ credibility is now anchored in a public cohort-style package with feature, design, and reproducibility surfaces instead of a tidy closed matrix story."
        ),
        note=(
            "This package now has a product-owned asset root, a raw-executable runtime lane, and bounded outsider-auditable authority, but generalization beyond the current cohort package remains explicitly limited."
        ),
    )


def build_flagship_multiplex_public_benchmark_package() -> (
    FlagshipPublicBenchmarkPackage
):
    """Build the flagship public multiplex package."""

    package_root = _package_root("multiplex_tmtpro_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="flagship_public_package:multiplex_tmtpro_review_package",
        workflow_family="multiplex",
        package_label="Flagship public multiplex TMTpro review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="closed_fixture_bundle:multiplex_channel_fixture",
        public_dataset_identity=(
            "tracked TMTpro reporter-ion, feature, and design snapshots with explicit bridge-channel, interference, imbalance, and missing-channel pressure"
        ),
        runtime_availability="raw-executable runtime lane exists and is reviewable",
        comparator_availability="external confrontation exists, but public authority is intentionally limited to internal support",
        source_assets=_multiplex_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/flagship-workflows/runtime/quant_bundle.json",
            "artifacts/workflows/flagship-workflows/core/quant_review_packet.json",
        ),
        scientific_pressures=(
            "reference-channel dependence",
            "ratio compression",
            "isolation interference",
            "missing-channel pressure",
            "channel imbalance",
        ),
        claim_scope=(
            "Multiplex credibility is now anchored in a public TMTpro package that exposes reporter channels, bridge roles, and interference pressure directly instead of relying on an internal fixture shape."
        ),
        note=(
            "This package now has a product-owned asset root, a raw-executable benchmark lane, and explicit interference review, but it remains an internal-support family until lab consequence and outsider review surfaces exist."
        ),
    )


def build_flagship_ptm_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    """Build the flagship public PTM package for localization and occupancy proof."""

    package_root = _package_root("ptm_localization_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="flagship_public_package:ptm_localization_review_package",
        workflow_family="ptm",
        package_label="Flagship public PTM localization review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="closed_fixture_bundle:ptm_localization_only",
        public_dataset_identity=(
            "tracked localization, PTM feature, raw-spectrum, and sequence-context snapshots with explicit ambiguity limits"
        ),
        runtime_availability="raw-executable runtime lane exists and is reviewable",
        comparator_availability="bounded external comparator confrontation is shipped",
        source_assets=_ptm_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/flagship-workflows/runtime/ptm_localization_report.json",
            "artifacts/workflows/flagship-workflows/runtime/ptm_occupancy_report.json",
            "artifacts/workflows/flagship-workflows/runtime/ptm_lab_targeting_packet.json",
        ),
        scientific_pressures=(
            "site ambiguity",
            "occupancy uncertainty",
            "motif credibility stress",
            "lab-targeting burden",
        ),
        claim_scope=(
            "PTM credibility is now anchored in a public localization review package with raw-spectrum and feature context instead of a hidden fixture-only contract."
        ),
        note=(
            "This package now has a product-owned asset root, a raw-executable runtime lane, and bounded outsider-auditable authority, but ambiguity, occupancy, and lab-targeting limits remain in force."
        ),
    )


def build_flagship_targeted_public_benchmark_package() -> (
    FlagshipPublicBenchmarkPackage
):
    """Build the flagship public targeted package."""

    package_root = _package_root("targeted_transition_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="flagship_public_package:targeted_transition_review_package",
        workflow_family="targeted",
        package_label="Flagship public targeted transition review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="closed_fixture_bundle:targeted_transition_control_bundle",
        public_dataset_identity=(
            "tracked Skyline-style targeted result and design snapshots plus supporting QC, benchmark-ranked validation inputs, and approved, failed, and refused follow-up packet snapshots"
        ),
        runtime_availability="raw-executable runtime lane exists and is reviewable",
        comparator_availability="bounded Skyline-class comparator confrontation is shipped",
        source_assets=_targeted_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/flagship-workflows/lab/follow_up_packet.json",
            "artifacts/workflows/flagship-workflows/core/targeted_qc_review.json",
        ),
        scientific_pressures=(
            "transition reproducibility",
            "interference risk",
            "fragment-ratio drift",
            "coelution instability",
            "premature protein certainty",
        ),
        claim_scope=(
            "Targeted credibility is now anchored in a public transition-control package with runnable Skyline-style results, explicit QC review, benchmark-ranked validation inputs, and approved, failed, and refused consequence packets instead of a buried QC fixture."
        ),
        note=(
            "This package now has a product-owned asset root, a raw-executable runtime lane, and bounded outsider-auditable authority, but absolute calibration, interference, and vendor-parity limits remain explicit."
        ),
    )


def list_flagship_public_benchmark_packages() -> tuple[
    FlagshipPublicBenchmarkPackage, ...
]:
    """Return the flagship public packages that anchor core proof surfaces today."""

    return (
        build_flagship_dda_public_benchmark_package(),
        build_flagship_dia_public_benchmark_package(),
        build_flagship_lfq_public_benchmark_package(),
        build_flagship_multiplex_public_benchmark_package(),
        build_flagship_ptm_public_benchmark_package(),
        build_flagship_targeted_public_benchmark_package(),
    )


def build_flagship_public_benchmark_catalog() -> FlagshipPublicBenchmarkCatalog:
    """Build the catalog of flagship public benchmark packages."""

    return FlagshipPublicBenchmarkCatalog(
        entries=list_flagship_public_benchmark_packages()
    )


def build_flagship_public_package_artifact_inventories() -> tuple[
    FlagshipPublicPackageArtifactInventory, ...
]:
    """Build artifact inventories across the flagship public packages."""

    return tuple(
        FlagshipPublicPackageArtifactInventory(
            package_id=package.package_id,
            inventory_path=package.artifact_inventory_path,
            artifacts=_inventory_records(package),
            note=(
                "Each inventory keeps digests and simple row or spectrum counts visible so the package can be audited from files alone."
            ),
        )
        for package in list_flagship_public_benchmark_packages()
    )


def build_flagship_public_package_quality_sheets() -> tuple[
    FlagshipPublicPackageQualitySheet, ...
]:
    """Build outsider-readable quality sheets across flagship packages."""

    return (
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:dda_reviewable_run",
            workflow_family="dda",
            quality_path=_quality_path(_package_root("dda_reviewable_run")),
            raw_identity_state="raw-like spectrum and paired exported-result snapshots are tracked",
            runtime_state="reviewable import-only runtime lane exists",
            comparator_state="paired MSFragger confrontation is shipped",
            lab_consequence_state="lab packet exists but remains exploratory-only",
            current_readiness="outsider_auditable_but_not_live_rerun_parity",
            exact_strengths=(
                "raw-like spectra, imported results, and settings are all tracked together",
                "cross-engine protein-rollup drift is demonstrated in public files",
            ),
            exact_blockers=(
                "no in-repo live-engine rerun parity",
                "one-run package cannot authorize broad production-cohort DDA claims",
            ),
            note="DDA is the strongest current public package, but its authority still stops before live-engine rerun parity.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:dia_library_review_package",
            workflow_family="dia",
            quality_path=_quality_path(_package_root("dia_library_review_package")),
            raw_identity_state="library-conditioned exported-result snapshots are tracked",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="Spectronaut-versus-DIA-NN confrontation is shipped",
            lab_consequence_state="lab packet exists but remains exploratory-only",
            current_readiness="outsider_auditable_library_conditioned_raw_execution",
            exact_strengths=(
                "paired DIA exported-result surfaces make library assumptions inspectable",
                "runtime and comparator identity are both visible from tracked files",
                "the flagship runtime lane now executes the tracked DIA package directly",
            ),
            exact_blockers=(
                "no chromatogram-level vendor parity",
                "library incompleteness and absent-peptide consequences still block broader biological confidence",
            ),
            note="DIA now has a real public package and a raw-executable runtime lane, but its authority still stops at library-conditioned review.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:lfq_cohort_review_package",
            workflow_family="lfq",
            quality_path=_quality_path(_package_root("lfq_cohort_review_package")),
            raw_identity_state="study-scale cohort-like feature and design snapshots are tracked",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="bounded external confrontation is shipped",
            lab_consequence_state="lab packet exists and remains exploratory-only",
            current_readiness="outsider_auditable_but_generalization_bounded",
            exact_strengths=(
                "cohort design and missingness evidence are public and inspectable",
                "repeatability boundary is visible instead of implied",
                "runtime now executes the tracked LFQ cohort review path",
                "outsider review now survives with explicit advisory rather than refused comparator posture",
            ),
            exact_blockers=(
                "no stronger public truth package for accuracy beyond repeatability",
                "generalization beyond the current cohort package remains explicitly bounded",
            ),
            note="LFQ package substance, runtime execution, and outsider review are all real now, but decision-grade and multi-cohort authority remain behind them.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:multiplex_tmtpro_review_package",
            workflow_family="multiplex",
            quality_path=_quality_path(
                _package_root("multiplex_tmtpro_review_package")
            ),
            raw_identity_state="TMTpro reporter-ion, feature, and channel-design snapshots are tracked",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="external confrontation exists but public authority stays internal-support only",
            lab_consequence_state="no multiplex lab consequence packet is shipped",
            current_readiness="internal_support_runnable_benchmark_not_outsider_auditable",
            exact_strengths=(
                "reporter-channel, pooled-reference, and bridge-channel roles are explicit in tracked files",
                "isolation-interference, ratio-compression, and missing-channel pressure are public package concerns rather than hidden caveats",
                "runtime now executes the tracked multiplex benchmark path",
            ),
            exact_blockers=(
                "no multiplex lab packet or outsider decision brief family",
                "multiplex authority is intentionally kept out of the outsider-facing flagship set",
            ),
            note="Multiplex now has a runnable benchmark package with explicit interference review, but it remains an internal-support family rather than an outsider-facing flagship family.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:ptm_localization_review_package",
            workflow_family="ptm",
            quality_path=_quality_path(
                _package_root("ptm_localization_review_package")
            ),
            raw_identity_state="localization, feature, raw-spectrum, and FASTA snapshots are tracked",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="bounded external confrontation is shipped",
            lab_consequence_state="lab packet exists and remains exploratory-only",
            current_readiness="outsider_auditable_ambiguity_bounded",
            exact_strengths=(
                "localization ambiguity and raw-spectrum context are public",
                "occupancy and targetability limits are inspectable from tracked files",
                "runtime now executes the tracked PTM localization review path",
                "outsider review now survives with advisory comparator posture and explicit ambiguity limits",
            ),
            exact_blockers=(
                "occupancy and regulatory interpretation still remain narrower than localization evidence",
                "PTM follow-up remains exploratory and bounded by ambiguity-aware consequence planning",
            ),
            note="PTM package substance, runtime execution, and outsider review are real now, but decision-grade PTM promotion remains blocked by ambiguity-aware consequence limits.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:targeted_transition_review_package",
            workflow_family="targeted",
            quality_path=_quality_path(
                _package_root("targeted_transition_review_package")
            ),
            raw_identity_state="transition QC and approved/failed/refused consequence packet snapshots are tracked",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="bounded Skyline-class comparator confrontation is shipped",
            lab_consequence_state="lab packet exists and remains exploratory-only",
            current_readiness="outsider_auditable_calibration_bounded",
            exact_strengths=(
                "approved, failed, and refused targeted consequences are all public package artifacts",
                "transition-level QC remains the primary tracked evidence surface",
                "the flagship runtime lane now executes the tracked targeted review package directly",
            ),
            exact_blockers=(
                "vendor-parity and calibration-clean authority are still outside the current proof boundary",
                "targeted follow-up remains exploratory and cannot authorize calibration-perfect biological certainty",
            ),
            note="Targeted package substance, runtime execution, and outsider review are real now, but calibration, interference, and vendor-parity limits still bound the authority it earns.",
        ),
    )


def build_flagship_public_package_lifecycle_records() -> tuple[
    FlagshipPublicPackageLifecycleRecord, ...
]:
    """Build lifecycle records across flagship public packages."""

    refreshed_on = date(2026, 5, 7)
    return (
        FlagshipPublicPackageLifecycleRecord(
            package_id="flagship_public_package:dda_reviewable_run",
            workflow_family="dda",
            lifecycle_path=_lifecycle_path(_package_root("dda_reviewable_run")),
            created_on=date(2026, 5, 7),
            last_refreshed_on=refreshed_on,
            obsolescence_triggers=(
                "DDA exported-result dialects change without refreshing the paired package artifacts.",
                "The package remains one-run only while broader DDA release claims expand.",
            ),
            retirement_conditions=(
                "Retire this package from flagship authority when a broader multi-run DDA package replaces it.",
                "Retire this package from outsider release leadership if the paired comparator export or warning ledger goes stale.",
            ),
            note="The DDA package stays current only while its raw-like and paired-export boundary remains the actual flagship proof center.",
        ),
        FlagshipPublicPackageLifecycleRecord(
            package_id="flagship_public_package:dia_library_review_package",
            workflow_family="dia",
            lifecycle_path=_lifecycle_path(_package_root("dia_library_review_package")),
            created_on=date(2026, 5, 7),
            last_refreshed_on=refreshed_on,
            obsolescence_triggers=(
                "Library-conditioned export dialects or settings change without package refresh.",
                "A chromatogram-level runtime or vendor-parity package becomes available.",
            ),
            retirement_conditions=(
                "Retire this package when a broader chromatogram-backed DIA package replaces it.",
                "Retire this package from flagship authority if the confrontation no longer covers the current DIA review story.",
            ),
            note="The DIA package is a serious current package, but it should be replaced once chromatogram-level public proof becomes feasible.",
        ),
        FlagshipPublicPackageLifecycleRecord(
            package_id="flagship_public_package:lfq_cohort_review_package",
            workflow_family="lfq",
            lifecycle_path=_lifecycle_path(_package_root("lfq_cohort_review_package")),
            created_on=date(2026, 5, 7),
            last_refreshed_on=refreshed_on,
            obsolescence_triggers=(
                "Cohort design or feature-schema changes without package refresh.",
                "A stronger accuracy- or truth-set-backed LFQ package replaces repeatability-only authority.",
            ),
            retirement_conditions=(
                "Retire this package from flagship authority when a raw-executable LFQ package exists.",
                "Retire this package from release-facing trust if runtime and comparator gaps remain open across two review windows.",
            ),
            note="The LFQ package is now real, but it should not be the final flagship package shape for quantification.",
        ),
        FlagshipPublicPackageLifecycleRecord(
            package_id="flagship_public_package:multiplex_tmtpro_review_package",
            workflow_family="multiplex",
            lifecycle_path=_lifecycle_path(
                _package_root("multiplex_tmtpro_review_package")
            ),
            created_on=date(2026, 5, 7),
            last_refreshed_on=refreshed_on,
            obsolescence_triggers=(
                "TMTpro reporter-ion schema, interference semantics, or multiplex design assumptions change without package refresh.",
                "A stronger multiplex package adds lab consequence closure or outsider-facing authority.",
            ),
            retirement_conditions=(
                "Retire this package when a stronger multiplex package adds consequence-bearing review and broader authority.",
                "Retire this package from flagship authority if chemistry claims widen beyond the current TMTpro evidence bed.",
            ),
            note="The multiplex package is now runnable, but it still needs consequence-bearing and outsider-facing review layers before it can lead broader trust language.",
        ),
        FlagshipPublicPackageLifecycleRecord(
            package_id="flagship_public_package:ptm_localization_review_package",
            workflow_family="ptm",
            lifecycle_path=_lifecycle_path(
                _package_root("ptm_localization_review_package")
            ),
            created_on=date(2026, 5, 7),
            last_refreshed_on=refreshed_on,
            obsolescence_triggers=(
                "PTM-family scope widens without refreshing the localization package.",
                "A runtime-backed or rescoring-backed PTM package becomes available.",
            ),
            retirement_conditions=(
                "Retire this package when a broader PTM package adds runtime and comparator closure.",
                "Retire this package from flagship authority if localization evidence no longer represents current PTM support claims.",
            ),
            note="The PTM package is now inspectable and public, but it is still a midpoint package rather than the end-state PTM flagship.",
        ),
        FlagshipPublicPackageLifecycleRecord(
            package_id="flagship_public_package:targeted_transition_review_package",
            workflow_family="targeted",
            lifecycle_path=_lifecycle_path(
                _package_root("targeted_transition_review_package")
            ),
            created_on=date(2026, 5, 7),
            last_refreshed_on=refreshed_on,
            obsolescence_triggers=(
                "Targeted QC schema, follow-up packet rules, or calibration expectations change without package refresh.",
                "A runtime-backed targeted package becomes available.",
            ),
            retirement_conditions=(
                "Retire this package when a stronger targeted package adds runtime and comparator closure.",
                "Retire this package from flagship authority if transition-control claims widen past the current QC and follow-up evidence bed.",
            ),
            note="The targeted package is real and public now, but it should be replaced by a runtime-backed targeted flagship package when one exists.",
        ),
    )


__all__ = [
    "FlagshipPublicBenchmarkAsset",
    "FlagshipPublicBenchmarkCatalog",
    "FlagshipPublicBenchmarkPackage",
    "FlagshipPublicEvidenceKind",
    "FlagshipPublicPackageArtifactInventory",
    "FlagshipPublicPackageArtifactRecord",
    "FlagshipPublicPackageLifecycleRecord",
    "FlagshipPublicPackageQualitySheet",
    "build_flagship_dda_public_benchmark_package",
    "build_flagship_dia_public_benchmark_package",
    "build_flagship_lfq_public_benchmark_package",
    "build_flagship_multiplex_public_benchmark_package",
    "build_flagship_ptm_public_benchmark_package",
    "build_flagship_public_benchmark_catalog",
    "build_flagship_public_package_artifact_inventories",
    "build_flagship_public_package_lifecycle_records",
    "build_flagship_public_package_quality_sheets",
    "build_flagship_targeted_public_benchmark_package",
    "list_flagship_public_benchmark_packages",
]
