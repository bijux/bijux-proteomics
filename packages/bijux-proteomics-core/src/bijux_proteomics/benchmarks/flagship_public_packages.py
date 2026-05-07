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

from bijux_proteomics_foundation import JsonModel


class FlagshipPublicEvidenceKind(StrEnum):
    """Dominant evidence kind used to anchor one public benchmark asset."""

    ARTIFACT_INVENTORY = "artifact_inventory"
    BENCHMARK_PACKAGE_MANIFEST = "benchmark_package_manifest"
    BENCHMARK_README = "benchmark_readme"
    FOLLOW_UP_PACKET = "follow_up_packet"
    PACKAGE_LIFECYCLE_RECORD = "package_lifecycle_record"
    PACKAGE_QUALITY_SHEET = "package_quality_sheet"
    RAW_SPECTRA = "raw_spectra"
    IMPORTED_SEARCH_RESULTS = "imported_search_results"
    QUANT_FEATURE_TABLE = "quant_feature_table"
    PTM_LOCALIZATION_TABLE = "ptm_localization_table"
    REFERENCE_FASTA = "reference_fasta"
    SCIENTIFIC_INVARIANT_LEDGER = "scientific_invariant_ledger"
    EXPERIMENTAL_DESIGN = "experimental_design"
    EXPECTATION_MANIFEST = "expectation_manifest"
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
    return _repo_path(repo_relative_path).read_text(encoding="utf-8").count("BEGIN IONS")


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
    return (
        "packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/"
        f"{dir_name}"
    )


def _package_manifest_path(package_root: str) -> str:
    return f"{package_root}/package_manifest.json"


def _artifact_inventory_path(package_root: str) -> str:
    return f"{package_root}/artifact_inventory.json"


def _readme_path(package_root: str) -> str:
    return f"{package_root}/README.md"


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
            path="packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
            evidence_kind=FlagshipPublicEvidenceKind.RAW_SPECTRA,
            public_identity_note=(
                "Raw tandem spectra keep the flagship DDA package tied to inspectable evidence rather than a closed export alone."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="primary_search_results",
            path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The primary MaxQuant export anchors the reviewable runtime import lane in a governed checked-in result table."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="comparator_search_results",
            path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/msfragger/msfragger_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The paired MSFragger export keeps cross-engine DDA warning pressure public and reviewable."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="experimental_design",
            path="packages/bijux-proteomics-core/tests/fixtures/production_run/design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note=(
                "Design metadata keeps downstream review tied to the actual sample structure."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="expectation_manifest",
            path="packages/bijux-proteomics-core/tests/fixtures/production_run/workflow_end_to_end_expectations.json",
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
            asset_role="spectronaut_report",
            path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_report.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The Spectronaut-style report anchors one public DIA extraction view with explicit library-conditioned assumptions."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="spectronaut_pipeline_export",
            path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The Spectronaut-style pipeline export exposes adapter field coverage and DIA review drift risk."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="spectronaut_settings",
            path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/spectronaut/spectronaut_settings.txt",
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note=(
                "Pinned settings keep library and extraction assumptions inspectable instead of implied."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="diann_pipeline_export",
            path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note=(
                "The DIA-NN-style export is the current external confrontation partner for library-conditioned DIA review."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="diann_config",
            path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_config.json",
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
            asset_role="feature_table",
            path="packages/bijux-proteomics-core/tests/fixtures/quant/study_scale_ms1_features.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note=(
                "The study-scale MS1 table is the current public quantitative evidence bed for LFQ review."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="design_table",
            path="packages/bijux-proteomics-core/tests/fixtures/quant/study_scale.design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note=(
                "The cohort-shaped design table keeps replicate, batch, and instrument structure explicit."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="reproducibility_manifest",
            path="packages/bijux-proteomics-core/tests/fixtures/quant/quant_reproducibility_manifest.json",
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
            asset_role="feature_table",
            path="packages/bijux-proteomics-core/tests/fixtures/quant/multiplex_ms1_features.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note=(
                "Reporter-channel feature evidence keeps missing-channel and imbalance pressure tied to tracked files."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="design_table",
            path="packages/bijux-proteomics-core/tests/fixtures/quant/multiplex.design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note=(
                "The multiplex design table preserves pooled-reference roles and channel assignments."
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
            asset_role="localization_table",
            path="packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.PTM_LOCALIZATION_TABLE,
            public_identity_note=(
                "Localization results keep ambiguous-site handling tied to tracked PTM evidence."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="ptm_feature_table",
            path="packages/bijux-proteomics-core/tests/fixtures/ptm/ptm_features.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note=(
                "PTM feature intensities keep occupancy interpretation grounded in tracked quantitative evidence."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="reference_fasta",
            path="packages/bijux-proteomics-core/tests/fixtures/fasta/ptm_sites.fasta",
            evidence_kind=FlagshipPublicEvidenceKind.REFERENCE_FASTA,
            public_identity_note=(
                "Reference sequence context preserves site coordinates and residue identity."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="raw_spectra",
            path="packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
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
            asset_role="targeted_qc_table",
            path="packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.TARGETED_QC_TABLE,
            public_identity_note=(
                "Transition-level QC evidence is the tracked base layer for the targeted public package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="approved_follow_up",
            path="packages/bijux-proteomics-lab/tests/fixtures/handoffs/supported_targeted_follow_up.json",
            evidence_kind=FlagshipPublicEvidenceKind.FOLLOW_UP_PACKET,
            public_identity_note=(
                "The approved targeted follow-up packet shows the current strongest operator-facing consequence of the package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="failed_follow_up",
            path="packages/bijux-proteomics-lab/tests/fixtures/handoffs/failed_targeted_transition_follow_up.json",
            evidence_kind=FlagshipPublicEvidenceKind.FOLLOW_UP_PACKET,
            public_identity_note=(
                "The failed follow-up packet keeps control and transition failure pressure in the public package."
            ),
        ),
        FlagshipPublicBenchmarkAsset(
            asset_role="refused_follow_up",
            path="packages/bijux-proteomics-lab/tests/fixtures/handoffs/refused_targeted_follow_up.json",
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
        replaced_proof_surface="legacy_fixture_bundle:dda_mini_study",
        public_dataset_identity=(
            "tracked raw-like spectrum plus paired MaxQuant and MSFragger exported-result snapshots inside one outsider-readable DDA package"
        ),
        runtime_availability="import_only runtime lane exists and is reviewable",
        comparator_availability="MaxQuant-versus-MSFragger confrontation is shipped",
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
        replaced_proof_surface="curated_fixture_bundle:dia_library_extraction_bundle",
        public_dataset_identity=(
            "tracked Spectronaut-style and DIA-NN-style exported-result snapshots with explicit library-conditioned settings and confrontation scope"
        ),
        runtime_availability="import_only runtime lane exists and remains library-conditioned",
        comparator_availability="Spectronaut-versus-DIA-NN confrontation is shipped",
        source_assets=_dia_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/reviewable-proteomics/runtime/review_packet.json",
            "artifacts/workflows/reviewable-proteomics/runtime/evidence_bundle.json",
            "artifacts/workflows/reviewable-proteomics/core/scientific_kernel.json",
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
            "This package is real and inspectable, but it still stops at library-conditioned import review rather than chromatogram-level vendor parity."
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
        replaced_proof_surface="closed_fixture_bundle:lfq_tidy_matrix_only",
        public_dataset_identity=(
            "tracked study-scale feature and cohort-design snapshots with explicit missingness and repeatability boundaries"
        ),
        runtime_availability="no flagship runtime lane is wired yet",
        comparator_availability="external comparator confrontation exists but decision-grade claim support is still refused",
        source_assets=_lfq_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/reviewable-proteomics/runtime/quant_bundle.json",
            "artifacts/workflows/reviewable-proteomics/runtime/missingness_profile.json",
            "artifacts/workflows/reviewable-proteomics/runtime/differential_report.json",
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
            "This package makes LFQ evidence inspectable from tracked files, but runtime execution and stronger comparator closure are still missing."
        ),
    )


def build_flagship_multiplex_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
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
        replaced_proof_surface="closed_fixture_bundle:multiplex_channel_fixture",
        public_dataset_identity=(
            "tracked TMTpro feature and design snapshots with explicit reporter-channel, imbalance, and missing-channel pressure"
        ),
        runtime_availability="no flagship runtime lane is wired yet",
        comparator_availability="external confrontation exists, but runtime-linked outsider proof is absent",
        source_assets=_multiplex_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/reviewable-proteomics/runtime/quant_bundle.json",
            "artifacts/workflows/reviewable-proteomics/core/quant_review_packet.json",
        ),
        scientific_pressures=(
            "reference-channel dependence",
            "ratio compression",
            "missing-channel pressure",
            "channel imbalance",
        ),
        claim_scope=(
            "Multiplex credibility is now anchored in a public TMTpro package that exposes chemistry and channel pressure directly instead of relying on an internal fixture shape."
        ),
        note=(
            "This package makes multiplex chemistry and channel evidence public, but it does not yet have a flagship runtime lane or outsider release packet."
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
        replaced_proof_surface="closed_fixture_bundle:ptm_localization_only",
        public_dataset_identity=(
            "tracked localization, PTM feature, raw-spectrum, and sequence-context snapshots with explicit ambiguity limits"
        ),
        runtime_availability="no flagship runtime lane is wired yet",
        comparator_availability="public comparator-backed claim support is still refused",
        source_assets=_ptm_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/reviewable-proteomics/runtime/ptm_localization_report.json",
            "artifacts/workflows/reviewable-proteomics/runtime/ptm_occupancy_report.json",
            "artifacts/workflows/reviewable-proteomics/runtime/ptm_lab_targeting_packet.json",
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
            "This package makes PTM evidence inspectable from files, but runtime execution and comparator closure remain blocked."
        ),
    )


def build_flagship_targeted_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
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
        replaced_proof_surface="closed_fixture_bundle:targeted_transition_control_bundle",
        public_dataset_identity=(
            "tracked chromatogram-shaped QC table plus approved, failed, and refused follow-up packet snapshots"
        ),
        runtime_availability="no flagship runtime truth row is published yet",
        comparator_availability="public comparator-backed claim support is still refused",
        source_assets=_targeted_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/reviewable-proteomics/lab/follow_up_packet.json",
            "artifacts/workflows/reviewable-proteomics/core/targeted_qc_review.json",
        ),
        scientific_pressures=(
            "transition reproducibility",
            "calibration absence",
            "interference risk",
            "premature protein certainty",
        ),
        claim_scope=(
            "Targeted credibility is now anchored in a public transition-control package with explicit approved, failed, and refused consequence packets instead of a buried QC fixture."
        ),
        note=(
            "This package makes targeted transition evidence public, but runtime execution and comparator closure are still behind the package surface."
        ),
    )


def list_flagship_public_benchmark_packages() -> tuple[FlagshipPublicBenchmarkPackage, ...]:
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
            runtime_state="reviewable import-only runtime lane exists",
            comparator_state="Spectronaut-versus-DIA-NN confrontation is shipped",
            lab_consequence_state="lab packet exists but remains exploratory-only",
            current_readiness="public_package_ready_but_library_conditioned",
            exact_strengths=(
                "paired DIA exported-result surfaces make library assumptions inspectable",
                "runtime and comparator identity are both visible from tracked files",
            ),
            exact_blockers=(
                "no chromatogram-level vendor parity",
                "library incompleteness and absent-peptide consequences still block broader biological confidence",
            ),
            note="DIA now has a real public package, but it still stops at library-conditioned import review.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:lfq_cohort_review_package",
            workflow_family="lfq",
            quality_path=_quality_path(_package_root("lfq_cohort_review_package")),
            raw_identity_state="study-scale cohort-like feature and design snapshots are tracked",
            runtime_state="no flagship runtime lane is wired yet",
            comparator_state="confrontation exists but release-facing claim support remains refused",
            lab_consequence_state="current lab packet says not worth the assay",
            current_readiness="public_package_ready_runtime_blocked",
            exact_strengths=(
                "cohort design and missingness evidence are public and inspectable",
                "repeatability boundary is visible instead of implied",
            ),
            exact_blockers=(
                "no flagship runtime lane",
                "no stronger public truth package for accuracy beyond repeatability",
            ),
            note="LFQ package substance is now public, but runtime and decision-grade trust remain behind it.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:multiplex_tmtpro_review_package",
            workflow_family="multiplex",
            quality_path=_quality_path(_package_root("multiplex_tmtpro_review_package")),
            raw_identity_state="TMTpro feature and channel-design snapshots are tracked",
            runtime_state="no flagship runtime lane is wired yet",
            comparator_state="external confrontation exists but outsider release proof is still thinner than DDA",
            lab_consequence_state="no multiplex lab consequence packet is shipped",
            current_readiness="public_package_ready_runtime_and_lab_blocked",
            exact_strengths=(
                "reporter-channel and pooled-reference roles are explicit in tracked files",
                "ratio-compression and missing-channel pressure are public package concerns rather than hidden caveats",
            ),
            exact_blockers=(
                "no flagship runtime lane",
                "no multiplex lab packet or outsider review packet family",
            ),
            note="Multiplex now has a real public package, but runtime and downstream consequence layers still lag behind it.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:ptm_localization_review_package",
            workflow_family="ptm",
            quality_path=_quality_path(_package_root("ptm_localization_review_package")),
            raw_identity_state="localization, feature, raw-spectrum, and FASTA snapshots are tracked",
            runtime_state="no flagship runtime lane is wired yet",
            comparator_state="public comparator-backed claim support is refused",
            lab_consequence_state="current lab packet says not worth the assay",
            current_readiness="public_package_ready_runtime_and_comparator_blocked",
            exact_strengths=(
                "localization ambiguity and raw-spectrum context are public",
                "occupancy and targetability limits are inspectable from tracked files",
            ),
            exact_blockers=(
                "no flagship runtime lane",
                "no comparator-backed public claim support",
            ),
            note="PTM now has a real public package, but runtime and comparator closure remain blocking gaps.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="flagship_public_package:targeted_transition_review_package",
            workflow_family="targeted",
            quality_path=_quality_path(_package_root("targeted_transition_review_package")),
            raw_identity_state="transition QC and approved/failed/refused consequence packet snapshots are tracked",
            runtime_state="no flagship runtime truth row is published yet",
            comparator_state="public comparator-backed claim support is refused",
            lab_consequence_state="lab packet family exists but current posture remains not worth the assay",
            current_readiness="public_package_ready_runtime_and_comparator_blocked",
            exact_strengths=(
                "approved, failed, and refused targeted consequences are all public package artifacts",
                "transition-level QC remains the primary tracked evidence surface",
            ),
            exact_blockers=(
                "no flagship runtime truth row",
                "no comparator-backed targeted claim support",
            ),
            note="Targeted now has a real public package, but runtime execution and comparator closure still trail the package surface.",
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
            lifecycle_path=_lifecycle_path(_package_root("multiplex_tmtpro_review_package")),
            created_on=date(2026, 5, 7),
            last_refreshed_on=refreshed_on,
            obsolescence_triggers=(
                "TMTpro channel mappings or multiplex design assumptions change without package refresh.",
                "A runtime-backed multiplex package becomes available.",
            ),
            retirement_conditions=(
                "Retire this package when a stronger multiplex package adds runtime and lab consequence closure.",
                "Retire this package from flagship authority if chemistry claims widen beyond the current TMTpro evidence bed.",
            ),
            note="The multiplex package is public now, but it still needs runtime and consequence-bearing layers before it can lead broader trust language.",
        ),
        FlagshipPublicPackageLifecycleRecord(
            package_id="flagship_public_package:ptm_localization_review_package",
            workflow_family="ptm",
            lifecycle_path=_lifecycle_path(_package_root("ptm_localization_review_package")),
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
            lifecycle_path=_lifecycle_path(_package_root("targeted_transition_review_package")),
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
