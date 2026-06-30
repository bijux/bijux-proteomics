# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-package benchmark generalization surfaces for flagship workflow families."""

from __future__ import annotations

import csv
from datetime import date
from enum import StrEnum
import hashlib
import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.flagship.asset_roots import (
    FlagshipAssetBoundaryKind,
    FlagshipAssetRootEntry,
    FlagshipCitationReference,
    FlagshipGeneratedBoundaryRecord,
    FlagshipRemoteSource,
)
from bijux_proteomics.benchmarks.flagship.public_packages import (
    FlagshipPublicBenchmarkAsset,
    FlagshipPublicBenchmarkPackage,
    FlagshipPublicEvidenceKind,
    FlagshipPublicPackageArtifactInventory,
    FlagshipPublicPackageArtifactRecord,
    FlagshipPublicPackageLifecycleRecord,
    FlagshipPublicPackageQualitySheet,
    build_flagship_dda_public_benchmark_package,
    build_flagship_dia_public_benchmark_package,
    build_flagship_lfq_public_benchmark_package,
    build_flagship_multiplex_public_benchmark_package,
    build_flagship_ptm_public_benchmark_package,
    build_flagship_targeted_public_benchmark_package,
)
from bijux_proteomics_foundation import JsonModel

_GENERALIZATION_ROOT = (
    "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages"
)
_GENERALIZATION_REGISTRY_PATH = (
    f"{_GENERALIZATION_ROOT}/generalization_asset_registry.json"
)
_FAMILY_STABILITY_SCORECARD_PATH = (
    f"{_GENERALIZATION_ROOT}/family_stability_scorecard.json"
)
_REFRESH_COMMAND = (
    "uv run --group dev python -m "
    "bijux_proteomics.benchmarks.workflow_generalization_assets refresh"
)


class WorkflowGeneralizationFindingState(StrEnum):
    """How a claim behaves when moving from the primary to the companion package."""

    SURVIVES = "survives"
    WEAKENS = "weakens"
    COLLAPSES = "collapses"


class WorkflowGeneralizationMetricDelta(JsonModel):
    """One measured difference between the primary and companion package."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str = Field(..., min_length=1)
    primary_value: float = Field(..., ge=0.0)
    secondary_value: float = Field(..., ge=0.0)
    delta: float
    interpretation: str = Field(..., min_length=1)


class WorkflowGeneralizationFinding(JsonModel):
    """One exact claim that survives, weakens, or collapses across packages."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    state: WorkflowGeneralizationFindingState
    evidence_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowGeneralizationReport(JsonModel):
    """Cross-package generalization report for one workflow family."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    primary_package_id: str = Field(..., min_length=1)
    secondary_package_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    package_manifest_paths: tuple[str, ...] = Field(default_factory=tuple)
    runtime_package_ids: tuple[str, ...] = Field(default_factory=tuple)
    metric_deltas: tuple[WorkflowGeneralizationMetricDelta, ...] = Field(
        default_factory=tuple
    )
    findings: tuple[WorkflowGeneralizationFinding, ...] = Field(default_factory=tuple)
    family_stability_score: float = Field(..., ge=0.0, le=1.0)
    family_stability_label: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class WorkflowFamilyStabilityRecord(JsonModel):
    """One per-family stability summary derived from the generalization report."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    primary_package_id: str = Field(..., min_length=1)
    secondary_package_id: str = Field(..., min_length=1)
    report_path: str = Field(..., min_length=1)
    stability_score: float = Field(..., ge=0.0, le=1.0)
    surviving_claim_count: int = Field(..., ge=0)
    weakened_claim_count: int = Field(..., ge=0)
    collapsed_claim_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class WorkflowFamilyStabilityScorecard(JsonModel):
    """Cross-family scorecard that keeps generalization drift visible."""

    model_config = ConfigDict(extra="forbid")

    scorecard_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[WorkflowFamilyStabilityRecord, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class SecondaryPublicPackageAssetRegistry(JsonModel):
    """Registry of non-primary public packages used for cross-package proof."""

    model_config = ConfigDict(extra="forbid")

    registry_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[FlagshipAssetRootEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _repo_path(repo_relative_path: str) -> Path:
    return _repo_root() / repo_relative_path


def _package_root(dir_name: str) -> str:
    return f"{_GENERALIZATION_ROOT}/{dir_name}"


def _package_manifest_path(package_root: str) -> str:
    return f"{package_root}/package_manifest.json"


def _artifact_inventory_path(package_root: str) -> str:
    return f"{package_root}/artifact_inventory.json"


def _quality_path(package_root: str) -> str:
    return f"{package_root}/quality_sheet.json"


def _lifecycle_path(package_root: str) -> str:
    return f"{package_root}/lifecycle.json"


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


def _report_path(dir_name: str) -> str:
    return f"{_package_root(dir_name)}/cross_package_generalization.json"


def _sha256(repo_relative_path: str) -> str:
    return hashlib.sha256(_repo_path(repo_relative_path).read_bytes()).hexdigest()


def _tsv_row_count(repo_relative_path: str) -> int:
    with _repo_path(repo_relative_path).open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter="\t"))


def _json_size_measure(repo_relative_path: str) -> int:
    payload = json.loads(_repo_path(repo_relative_path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return len(payload)
    if isinstance(payload, list):
        return len(payload)
    return 1


def _mgf_spectrum_count(repo_relative_path: str) -> int:
    return (
        _repo_path(repo_relative_path).read_text(encoding="utf-8").count("BEGIN IONS")
    )


def _optional_row_count(asset: FlagshipPublicBenchmarkAsset) -> int | None:
    if asset.path.endswith(".tsv"):
        return _tsv_row_count(asset.path)
    if asset.path.endswith(".json"):
        return _json_size_measure(asset.path)
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
        if asset.evidence_kind is not FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY
        and _repo_path(asset.path).exists()
    )


def _asset(
    *,
    asset_role: str,
    path: str,
    evidence_kind: FlagshipPublicEvidenceKind,
    public_identity_note: str,
) -> FlagshipPublicBenchmarkAsset:
    return FlagshipPublicBenchmarkAsset(
        asset_role=asset_role,
        path=path,
        evidence_kind=evidence_kind,
        public_identity_note=public_identity_note,
    )


def _remote_source(
    *,
    source_id: str,
    public_source_name: str,
    package_root: str,
    local_relative: str,
    upstream_repo_source_path: str,
    public_reference_url: str,
    why_it_matters: str,
    availability_expectation: str,
    license_note: str,
) -> FlagshipRemoteSource:
    return FlagshipRemoteSource(
        source_id=source_id,
        public_source_name=public_source_name,
        local_artifact_path=f"{package_root}/{local_relative}",
        upstream_repo_source_path=upstream_repo_source_path,
        public_reference_url=public_reference_url,
        why_it_matters=why_it_matters,
        availability_expectation=availability_expectation,
        license_note=license_note,
    )


def _citation(
    *,
    citation_id: str,
    title: str,
    url: str,
    why_it_matters: str,
    doi: str | None = None,
) -> FlagshipCitationReference:
    return FlagshipCitationReference(
        citation_id=citation_id,
        title=title,
        doi=doi,
        url=url,
        why_it_matters=why_it_matters,
    )


def _boundary(
    *,
    package_root: str,
    artifact_relative: str,
    boundary_kind: FlagshipAssetBoundaryKind,
    note: str,
) -> FlagshipGeneratedBoundaryRecord:
    return FlagshipGeneratedBoundaryRecord(
        artifact_path=f"{package_root}/{artifact_relative}",
        boundary_kind=boundary_kind,
        regeneration_command=_REFRESH_COMMAND,
        note=note,
    )


def _dda_secondary_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("dda_cross_engine_review_package")
    return (
        _asset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note="The DDA companion package starts outsider review from a different engine pairing and slightly busier sample context.",
        ),
        _asset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note="The machine-readable manifest states how this DDA companion package differs from the flagship primary package.",
        ),
        _asset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note="The artifact inventory keeps digests and simple row counts visible for the DDA companion package.",
        ),
        _asset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note="The DDA companion quality sheet keeps its weaker and stronger boundaries public.",
        ),
        _asset(
            asset_role="lifecycle",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note="The DDA companion lifecycle record explains why the package exists as a generalization challenge rather than a replacement flagship.",
        ),
        _asset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note="The source locator manifest shows where every copied or derived DDA companion artifact came from.",
        ),
        _asset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note="The citation manifest ties the DDA companion package to search-engine and protein-inference references.",
        ),
        _asset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note="The generated boundary manifest keeps copied snapshots distinct from generated metadata.",
        ),
        _asset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note="The rebuild instructions tell maintainers how to refresh the DDA companion package surfaces.",
        ),
        _asset(
            asset_role="spectra",
            path=f"{package_root}/evidence/spectra.mgf",
            evidence_kind=FlagshipPublicEvidenceKind.RAW_SPECTRA,
            public_identity_note="A raw-like spectrum keeps the DDA companion package tied to inspectable fragment evidence rather than export-only prose.",
        ),
        _asset(
            asset_role="design",
            path=f"{package_root}/evidence/design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note="The design table preserves the sample and instrument context for the DDA companion package.",
        ),
        _asset(
            asset_role="expectation_ledger",
            path=f"{package_root}/evidence/workflow_end_to_end_expectations.json",
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note="The expectation ledger keeps the runtime and review outputs explicit for the DDA companion package.",
        ),
        _asset(
            asset_role="primary_import",
            path=f"{package_root}/primary/comet_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note="The Comet export gives the DDA companion package a different primary import dialect from the flagship package.",
        ),
        _asset(
            asset_role="primary_settings",
            path=f"{package_root}/primary/comet.params",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note="The Comet settings snapshot keeps the companion DDA import assumptions inspectable.",
        ),
        _asset(
            asset_role="comparator_import",
            path=f"{package_root}/comparator/sage_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note="The Sage export provides a different comparator pressure shape from the flagship DDA package.",
        ),
        _asset(
            asset_role="comparator_settings",
            path=f"{package_root}/comparator/sage_config.json",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note="The Sage config snapshot keeps the DDA companion comparator assumptions reviewable.",
        ),
    )


def _dia_secondary_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("dia_matrix_shift_review_package")
    return (
        _asset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note="The DIA companion package starts from a different report shape and matrix pressure than the flagship package.",
        ),
        _asset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note="The DIA companion manifest explains how the shifted library and matrix pressure differs from the flagship package.",
        ),
        _asset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note="The DIA companion inventory keeps digests and row counts visible.",
        ),
        _asset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note="The DIA companion quality sheet makes its weaker matrix-transfer posture explicit.",
        ),
        _asset(
            asset_role="lifecycle",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note="The DIA companion lifecycle record explains that this package exists to stress family transfer, not to replace the flagship package.",
        ),
        _asset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note="The source locator manifest shows where the DIA companion exports came from.",
        ),
        _asset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note="The citation manifest ties the DIA companion package to DIA method and library-dependence references.",
        ),
        _asset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note="The generated boundary manifest distinguishes copied DIA exports from generated metadata.",
        ),
        _asset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note="The rebuild instructions tell maintainers how to refresh the DIA companion package surfaces.",
        ),
        _asset(
            asset_role="primary_report",
            path=f"{package_root}/primary/diann_report.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note="The DIA-NN report drives the companion raw-executable DIA review lane.",
        ),
        _asset(
            asset_role="primary_pipeline_export",
            path=f"{package_root}/primary/diann_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note="The DIA-NN pipeline export keeps the companion package tied to a different extracted-result surface from the flagship package.",
        ),
        _asset(
            asset_role="comparator_pipeline_export",
            path=f"{package_root}/comparator/spectronaut_pipeline_export.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note="The Spectronaut export provides the companion comparator surface.",
        ),
        _asset(
            asset_role="comparator_settings",
            path=f"{package_root}/comparator/spectronaut_settings.txt",
            evidence_kind=FlagshipPublicEvidenceKind.IMPORTED_SEARCH_RESULTS,
            public_identity_note="The Spectronaut settings snapshot keeps the companion comparator assumptions visible.",
        ),
    )


def _lfq_secondary_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("lfq_sparse_contrast_review_package")
    return (
        _asset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note="The LFQ companion package starts from a sparser and more imbalanced cohort contrast.",
        ),
        _asset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note="The LFQ companion manifest states how the cohort contrast differs from the flagship package.",
        ),
        _asset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note="The LFQ companion inventory keeps feature, design, and reproducibility evidence auditable.",
        ),
        _asset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note="The LFQ companion quality sheet makes sparse-cohort transfer limits public.",
        ),
        _asset(
            asset_role="lifecycle",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note="The LFQ companion lifecycle record explains that this package exists to pressure generalization beyond the flagship cohort.",
        ),
        _asset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note="The source locator manifest shows where the LFQ companion evidence came from.",
        ),
        _asset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note="The citation manifest ties the LFQ companion package to missingness and differential quant references.",
        ),
        _asset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note="The generated boundary manifest distinguishes copied LFQ evidence from generated metadata.",
        ),
        _asset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note="The rebuild instructions tell maintainers how to refresh the LFQ companion package surfaces.",
        ),
        _asset(
            asset_role="feature_table",
            path=f"{package_root}/evidence/edge_case_ms1_features.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note="The LFQ companion feature table increases sparsity and sample imbalance pressure relative to the flagship package.",
        ),
        _asset(
            asset_role="design_table",
            path=f"{package_root}/evidence/edge_case.design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note="The LFQ companion design table introduces a different replicate structure than the flagship package.",
        ),
        _asset(
            asset_role="reproducibility_manifest",
            path=f"{package_root}/evidence/sparse_reproducibility_manifest.json",
            evidence_kind=FlagshipPublicEvidenceKind.EXPECTATION_MANIFEST,
            public_identity_note="The LFQ companion reproducibility manifest keeps sparse-cohort repeatability assumptions explicit.",
        ),
    )


def _multiplex_secondary_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("multiplex_channel_stress_review_package")
    return (
        _asset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note="The multiplex companion package starts from stronger channel imbalance and dropout stress.",
        ),
        _asset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note="The multiplex companion manifest states how the stress design differs from the flagship package.",
        ),
        _asset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note="The multiplex companion inventory keeps stress-package evidence auditable.",
        ),
        _asset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note="The multiplex companion quality sheet makes channel-stress boundaries visible.",
        ),
        _asset(
            asset_role="lifecycle",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note="The multiplex companion lifecycle record explains that this package exists to stress reporter imbalance rather than to change public release posture.",
        ),
        _asset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note="The source locator manifest shows where the multiplex stress-package evidence came from.",
        ),
        _asset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note="The citation manifest ties the multiplex companion package to interference and ratio-compression references.",
        ),
        _asset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note="The generated boundary manifest distinguishes the derived stress feature table from copied support metadata.",
        ),
        _asset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note="The rebuild instructions tell maintainers how to refresh the multiplex stress package surfaces.",
        ),
        _asset(
            asset_role="feature_table",
            path=f"{package_root}/evidence/multiplex_channel_stress_ms1_features.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note="The multiplex companion feature table increases pooled-reference dominance and missing-channel pressure.",
        ),
        _asset(
            asset_role="design_table",
            path=f"{package_root}/evidence/multiplex_channel_stress.design.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.EXPERIMENTAL_DESIGN,
            public_identity_note="The multiplex companion design table preserves the stress-package channel layout and role assignments.",
        ),
    )


def _ptm_secondary_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("ptm_ambiguity_stress_review_package")
    return (
        _asset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note="The PTM companion package starts from materially stronger localization ambiguity.",
        ),
        _asset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note="The PTM companion manifest explains how ambiguity and targetability pressure shifts relative to the flagship package.",
        ),
        _asset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note="The PTM companion inventory keeps ambiguity stress evidence auditable.",
        ),
        _asset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note="The PTM companion quality sheet makes ambiguity-driven collapse visible.",
        ),
        _asset(
            asset_role="lifecycle",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note="The PTM companion lifecycle record explains why the package exists to pressure ambiguity-sensitive claims.",
        ),
        _asset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note="The source locator manifest shows where PTM ambiguity-stress evidence came from.",
        ),
        _asset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note="The citation manifest ties the PTM companion package to localization and occupancy references.",
        ),
        _asset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note="The generated boundary manifest distinguishes the ambiguity-stress localization table from copied support files.",
        ),
        _asset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note="The rebuild instructions tell maintainers how to refresh the PTM ambiguity package surfaces.",
        ),
        _asset(
            asset_role="localization_table",
            path=f"{package_root}/evidence/localization_results.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.PTM_LOCALIZATION_TABLE,
            public_identity_note="The PTM companion localization table explicitly worsens site ambiguity relative to the flagship package.",
        ),
        _asset(
            asset_role="feature_table",
            path=f"{package_root}/evidence/ptm_features.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.QUANT_FEATURE_TABLE,
            public_identity_note="The PTM companion feature table preserves the feature context used to interpret ambiguity.",
        ),
        _asset(
            asset_role="reference_fasta",
            path=f"{package_root}/evidence/ptm_sites.fasta",
            evidence_kind=FlagshipPublicEvidenceKind.REFERENCE_FASTA,
            public_identity_note="The PTM companion FASTA keeps the same peptide-to-protein context while ambiguity worsens.",
        ),
        _asset(
            asset_role="spectra",
            path=f"{package_root}/evidence/spectra.mgf",
            evidence_kind=FlagshipPublicEvidenceKind.RAW_SPECTRA,
            public_identity_note="The PTM companion raw-like spectra keep ambiguity review tied to inspectable fragment evidence.",
        ),
    )


def _targeted_secondary_assets() -> tuple[FlagshipPublicBenchmarkAsset, ...]:
    package_root = _package_root("targeted_carryover_review_package")
    return (
        _asset(
            asset_role="package_readme",
            path=_readme_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_README,
            public_identity_note="The targeted companion package starts from explicit carryover and calibration drift pressure.",
        ),
        _asset(
            asset_role="package_manifest",
            path=_package_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.BENCHMARK_PACKAGE_MANIFEST,
            public_identity_note="The targeted companion manifest explains how carryover pressure differs from the flagship package.",
        ),
        _asset(
            asset_role="artifact_inventory",
            path=_artifact_inventory_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.ARTIFACT_INVENTORY,
            public_identity_note="The targeted companion inventory keeps QC and follow-up evidence auditable.",
        ),
        _asset(
            asset_role="quality_sheet",
            path=_quality_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_QUALITY_SHEET,
            public_identity_note="The targeted companion quality sheet makes carryover-driven downgrade pressure public.",
        ),
        _asset(
            asset_role="lifecycle",
            path=_lifecycle_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.PACKAGE_LIFECYCLE_RECORD,
            public_identity_note="The targeted companion lifecycle record explains that this package exists to stress transition carryover and calibration claims.",
        ),
        _asset(
            asset_role="source_locator_manifest",
            path=_source_locator_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.SOURCE_LOCATOR_MANIFEST,
            public_identity_note="The source locator manifest shows where the targeted carryover evidence came from.",
        ),
        _asset(
            asset_role="citation_manifest",
            path=_citation_manifest_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.CITATION_MANIFEST,
            public_identity_note="The citation manifest ties the targeted companion package to calibration and carryover references.",
        ),
        _asset(
            asset_role="generated_boundary",
            path=_generated_boundary_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.GENERATED_BOUNDARY_MANIFEST,
            public_identity_note="The generated boundary manifest distinguishes the derived carryover stress QC table from copied follow-up support files.",
        ),
        _asset(
            asset_role="rebuild_instructions",
            path=_rebuild_instructions_path(package_root),
            evidence_kind=FlagshipPublicEvidenceKind.REBUILD_INSTRUCTIONS,
            public_identity_note="The rebuild instructions tell maintainers how to refresh the targeted carryover package surfaces.",
        ),
        _asset(
            asset_role="targeted_qc",
            path=f"{package_root}/evidence/targeted_benchmark_qc.tsv",
            evidence_kind=FlagshipPublicEvidenceKind.TARGETED_QC_TABLE,
            public_identity_note="The targeted companion QC table worsens TIC drift and carryover relative to the flagship package.",
        ),
        _asset(
            asset_role="supported_follow_up",
            path=f"{package_root}/follow_up/supported_targeted_follow_up.json",
            evidence_kind=FlagshipPublicEvidenceKind.FOLLOW_UP_PACKET,
            public_identity_note="The supported follow-up keeps the best-case carryover package outcome visible.",
        ),
        _asset(
            asset_role="failed_follow_up",
            path=f"{package_root}/follow_up/failed_targeted_transition_follow_up.json",
            evidence_kind=FlagshipPublicEvidenceKind.FOLLOW_UP_PACKET,
            public_identity_note="The failed follow-up keeps transition-fragility pressure explicit in the targeted companion package.",
        ),
        _asset(
            asset_role="refused_follow_up",
            path=f"{package_root}/follow_up/refused_targeted_follow_up.json",
            evidence_kind=FlagshipPublicEvidenceKind.FOLLOW_UP_PACKET,
            public_identity_note="The refused follow-up keeps weak calibration and carryover posture from looking operationally safe by omission.",
        ),
    )


def build_secondary_dda_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    package_root = _package_root("dda_cross_engine_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="public_companion_package:dda_cross_engine_review_package",
        workflow_family="dda",
        package_label="Companion public DDA cross-engine review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="secondary_fixture_bundle:dda_cross_engine_variation",
        public_dataset_identity="tracked Comet primary export plus Sage comparator export with production-run spectrum context and slightly higher sample-complexity pressure",
        runtime_availability="import_only runtime lane exists and is reviewable",
        comparator_availability="Comet-versus-Sage confrontation is shipped",
        source_assets=_dda_secondary_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/generalization-dda/runtime/review_packet.json",
            "artifacts/workflows/generalization-dda/runtime/evidence_bundle.json",
        ),
        scientific_pressures=(
            "cross-engine peptide acceptance drift",
            "protein-rollup instability under a different primary import dialect",
            "sample-complexity shift relative to the flagship package",
        ),
        claim_scope="This companion DDA package exists to test whether the main DDA claims survive a different primary import engine and a slightly busier sample context.",
        note="The companion DDA package supports family-level generalization checks, but it still does not grant live-engine rerun parity or broad cohort-grade DDA authority.",
    )


def build_secondary_dia_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    package_root = _package_root("dia_matrix_shift_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="public_companion_package:dia_matrix_shift_review_package",
        workflow_family="dia",
        package_label="Companion public DIA matrix-shift review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="secondary_fixture_bundle:dia_matrix_shift_variation",
        public_dataset_identity="tracked DIA-NN primary report and pipeline export paired against a Spectronaut comparator with visibly thinner matrix support",
        runtime_availability="raw-executable runtime lane exists and remains library-conditioned",
        comparator_availability="DIA-NN-versus-Spectronaut confrontation is shipped",
        source_assets=_dia_secondary_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/generalization-dia/runtime/review_packet.json",
            "artifacts/workflows/generalization-dia/runtime/evidence_bundle.json",
        ),
        scientific_pressures=(
            "matrix-conditioned precursor thinning",
            "library assumption transfer pressure",
            "protein evidence overreach under weaker extraction support",
        ),
        claim_scope="This companion DIA package exists to test whether library-conditioned claims survive a thinner matrix and a different primary exported-result surface.",
        note="The companion DIA package supports family-level generalization checks, but its authority remains library-conditioned and does not claim chromatogram-side vendor parity.",
    )


def build_secondary_lfq_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    package_root = _package_root("lfq_sparse_contrast_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="public_companion_package:lfq_sparse_contrast_review_package",
        workflow_family="lfq",
        package_label="Companion public LFQ sparse-contrast review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="secondary_fixture_bundle:lfq_sparse_contrast_variation",
        public_dataset_identity="tracked sparse-cohort feature and design snapshots with a different replicate shape and more fragile biological contrast",
        runtime_availability="raw-executable runtime lane exists and is reviewable",
        comparator_availability="bounded external comparator confrontation is shipped",
        source_assets=_lfq_secondary_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/generalization-lfq/runtime/quant_bundle.json",
            "artifacts/workflows/generalization-lfq/runtime/differential_report.json",
        ),
        scientific_pressures=(
            "sparser replicate structure",
            "higher missingness pressure",
            "effect-direction fragility under altered cohort contrast",
        ),
        claim_scope="This companion LFQ package exists to test whether the main LFQ repeatability and abundance-review claims survive a sparser cohort contrast.",
        note="The companion LFQ package supports family-level generalization checks, but it still does not grant decision-grade or broad cohort-transfer quant authority.",
    )


def build_secondary_multiplex_public_benchmark_package() -> (
    FlagshipPublicBenchmarkPackage
):
    package_root = _package_root("multiplex_channel_stress_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="public_companion_package:multiplex_channel_stress_review_package",
        workflow_family="multiplex",
        package_label="Companion public multiplex channel-stress review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="secondary_fixture_bundle:multiplex_channel_stress_variation",
        public_dataset_identity="tracked multiplex feature and design snapshots with stronger pooled-reference dominance and missing-channel pressure",
        runtime_availability="raw-executable runtime lane exists and is reviewable",
        comparator_availability="external confrontation exists, but public authority remains intentionally internal-support only",
        source_assets=_multiplex_secondary_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/generalization-multiplex/runtime/quant_bundle.json",
            "artifacts/workflows/generalization-multiplex/runtime/review_packet.json",
        ),
        scientific_pressures=(
            "pooled-reference dominance",
            "missing-channel pressure",
            "ratio-compression drift under stronger imbalance",
        ),
        claim_scope="This companion multiplex package exists to test whether the current internal-support-only multiplex posture stays honest under a harsher channel design.",
        note="The companion multiplex package supports family-level stress checks, but multiplex remains outside the outsider-facing flagship trust set.",
    )


def build_secondary_ptm_public_benchmark_package() -> FlagshipPublicBenchmarkPackage:
    package_root = _package_root("ptm_ambiguity_stress_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="public_companion_package:ptm_ambiguity_stress_review_package",
        workflow_family="ptm",
        package_label="Companion public PTM ambiguity-stress review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="secondary_fixture_bundle:ptm_ambiguity_stress_variation",
        public_dataset_identity="tracked PTM localization evidence with materially worse ambiguity and lower localization confidence than the flagship package",
        runtime_availability="raw-executable runtime lane exists and is reviewable",
        comparator_availability="bounded external confrontation is shipped",
        source_assets=_ptm_secondary_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/generalization-ptm/runtime/review_packet.json",
            "artifacts/workflows/generalization-ptm/runtime/evidence_bundle.json",
        ),
        scientific_pressures=(
            "stronger localization ambiguity",
            "lower-confidence motif support",
            "targetability collapse under ambiguity stress",
        ),
        claim_scope="This companion PTM package exists to test whether localization-facing claims survive while targetability claims collapse under stronger ambiguity.",
        note="The companion PTM package supports family-level generalization checks, but it still does not grant decision-grade PTM promotion under ambiguity-heavy conditions.",
    )


def build_secondary_targeted_public_benchmark_package() -> (
    FlagshipPublicBenchmarkPackage
):
    package_root = _package_root("targeted_carryover_review_package")
    return FlagshipPublicBenchmarkPackage(
        package_id="public_companion_package:targeted_carryover_review_package",
        workflow_family="targeted",
        package_label="Companion public targeted carryover review package",
        package_root=package_root,
        benchmark_manifest_path=_package_manifest_path(package_root),
        artifact_inventory_path=_artifact_inventory_path(package_root),
        quality_sheet_path=_quality_path(package_root),
        lifecycle_record_path=_lifecycle_path(package_root),
        source_locator_manifest_path=_source_locator_manifest_path(package_root),
        citation_manifest_path=_citation_manifest_path(package_root),
        generated_boundary_path=_generated_boundary_path(package_root),
        rebuild_instructions_path=_rebuild_instructions_path(package_root),
        replaced_proof_surface="secondary_fixture_bundle:targeted_carryover_variation",
        public_dataset_identity="tracked targeted QC and follow-up evidence with stronger carryover drift and heavier refusal pressure than the flagship package",
        runtime_availability="raw-executable runtime lane exists and is reviewable",
        comparator_availability="bounded Skyline-class comparator confrontation is shipped",
        source_assets=_targeted_secondary_assets(),
        expected_review_artifacts=(
            "artifacts/workflows/generalization-targeted/runtime/review_packet.json",
            "artifacts/workflows/generalization-targeted/runtime/evidence_bundle.json",
        ),
        scientific_pressures=(
            "carryover drift",
            "calibration fragility",
            "follow-up refusal pressure under weaker transition behavior",
        ),
        claim_scope="This companion targeted package exists to test whether the main targeted claims survive under stronger carryover and calibration stress.",
        note="The companion targeted package supports family-level generalization checks, but calibration-clean and vendor-parity authority remain outside the current proof boundary.",
    )


def list_secondary_public_benchmark_packages() -> tuple[
    FlagshipPublicBenchmarkPackage, ...
]:
    """Return all companion public packages used for family generalization."""

    return (
        build_secondary_dda_public_benchmark_package(),
        build_secondary_dia_public_benchmark_package(),
        build_secondary_lfq_public_benchmark_package(),
        build_secondary_multiplex_public_benchmark_package(),
        build_secondary_ptm_public_benchmark_package(),
        build_secondary_targeted_public_benchmark_package(),
    )


def build_secondary_public_package_artifact_inventories() -> tuple[
    FlagshipPublicPackageArtifactInventory, ...
]:
    return tuple(
        FlagshipPublicPackageArtifactInventory(
            package_id=package.package_id,
            inventory_path=package.artifact_inventory_path,
            artifacts=_inventory_records(package),
            note="The companion package inventory keeps digests and simple counts visible so cross-package review can start from files instead of prose.",
        )
        for package in list_secondary_public_benchmark_packages()
    )


def build_secondary_public_package_quality_sheets() -> tuple[
    FlagshipPublicPackageQualitySheet, ...
]:
    return (
        FlagshipPublicPackageQualitySheet(
            package_id="public_companion_package:dda_cross_engine_review_package",
            workflow_family="dda",
            quality_path=_quality_path(
                _package_root("dda_cross_engine_review_package")
            ),
            raw_identity_state="raw-like spectrum plus Comet and Sage exported-result snapshots are tracked",
            runtime_state="reviewable import-only runtime lane exists",
            comparator_state="Comet-versus-Sage confrontation is shipped",
            lab_consequence_state="lab packet remains the flagship DDA packet and still stays exploratory-only",
            current_readiness="companion_package_for_family_generalization",
            exact_strengths=(
                "a different primary import engine keeps family trust from depending on one convenient DDA export",
                "cross-engine comparison pressure is still public instead of hidden",
            ),
            exact_blockers=(
                "no live-engine rerun parity",
                "generalization remains bounded to two small exported-result packages",
            ),
            note="This DDA companion package exists to make family-level trust less package-specific, not to overstate DDA authority.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="public_companion_package:dia_matrix_shift_review_package",
            workflow_family="dia",
            quality_path=_quality_path(
                _package_root("dia_matrix_shift_review_package")
            ),
            raw_identity_state="DIA-NN report and export snapshots are tracked with explicit matrix-shift pressure",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="DIA-NN-versus-Spectronaut confrontation is shipped",
            lab_consequence_state="lab packet remains the flagship DIA packet and still stays exploratory-only",
            current_readiness="companion_package_for_family_generalization",
            exact_strengths=(
                "a thinner matrix and different primary exported-result surface keep DIA family claims from depending on one comfortable package",
                "runtime can execute the companion package directly",
            ),
            exact_blockers=(
                "protein-evidence transfer remains weaker than precursor-level review transfer",
                "library-conditioned authority still caps the family posture",
            ),
            note="This DIA companion package exists to measure family transfer, not to flatten matrix-conditioned weaknesses.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="public_companion_package:lfq_sparse_contrast_review_package",
            workflow_family="lfq",
            quality_path=_quality_path(
                _package_root("lfq_sparse_contrast_review_package")
            ),
            raw_identity_state="sparser cohort-like feature and design snapshots are tracked",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="bounded external comparator confrontation is shipped",
            lab_consequence_state="lab packet remains the flagship LFQ packet and still stays exploratory-only",
            current_readiness="companion_package_for_family_generalization",
            exact_strengths=(
                "a different replicate structure keeps LFQ trust from resting on one cohort shape",
                "runtime executes the companion cohort package directly",
            ),
            exact_blockers=(
                "effect-direction confidence weakens under sparser contrast",
                "family authority remains bounded rather than decision-grade",
            ),
            note="This LFQ companion package exists to make generalization visible instead of implied.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="public_companion_package:multiplex_channel_stress_review_package",
            workflow_family="multiplex",
            quality_path=_quality_path(
                _package_root("multiplex_channel_stress_review_package")
            ),
            raw_identity_state="derived channel-stress feature and design snapshots are tracked",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="external confrontation exists, but public authority remains internal-support only",
            lab_consequence_state="no multiplex lab consequence packet is shipped",
            current_readiness="companion_package_for_internal_support_stress",
            exact_strengths=(
                "stronger imbalance and missing-channel pressure make multiplex weakness visible",
                "runtime executes the stress package directly",
            ),
            exact_blockers=(
                "multiplex still lacks outsider review and lab consequence posture",
                "public release language remains internal-support only even with a second package",
            ),
            note="This multiplex companion package exists to keep the internal-support boundary honest under stronger channel stress.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="public_companion_package:ptm_ambiguity_stress_review_package",
            workflow_family="ptm",
            quality_path=_quality_path(
                _package_root("ptm_ambiguity_stress_review_package")
            ),
            raw_identity_state="ambiguity-stress localization evidence is tracked with feature, FASTA, and spectra context",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="bounded external confrontation is shipped",
            lab_consequence_state="lab packet remains the flagship PTM packet and still stays exploratory-only",
            current_readiness="companion_package_for_family_generalization",
            exact_strengths=(
                "stronger ambiguity stress keeps PTM trust from resting on one well-behaved localization package",
                "runtime executes the ambiguity package directly",
            ),
            exact_blockers=(
                "targetability weakens materially under ambiguity stress",
                "family authority remains bounded rather than decision-grade",
            ),
            note="This PTM companion package exists to show exactly which PTM claims survive stronger ambiguity and which collapse.",
        ),
        FlagshipPublicPackageQualitySheet(
            package_id="public_companion_package:targeted_carryover_review_package",
            workflow_family="targeted",
            quality_path=_quality_path(
                _package_root("targeted_carryover_review_package")
            ),
            raw_identity_state="carryover-stress targeted QC and follow-up evidence are tracked",
            runtime_state="reviewable raw-executable runtime lane exists",
            comparator_state="bounded Skyline-class comparator confrontation is shipped",
            lab_consequence_state="lab packet remains the flagship targeted packet and still stays exploratory-only",
            current_readiness="companion_package_for_family_generalization",
            exact_strengths=(
                "carryover and calibration stress keep targeted trust from depending on one cleaner QC table",
                "runtime executes the carryover package directly",
            ),
            exact_blockers=(
                "stronger carryover pressure weakens promotion confidence",
                "family authority remains bounded by calibration and vendor-parity limits",
            ),
            note="This targeted companion package exists to make carryover and follow-up fragility public at the family level.",
        ),
    )


def build_secondary_public_package_lifecycle_records() -> tuple[
    FlagshipPublicPackageLifecycleRecord, ...
]:
    refreshed_on = date(2026, 5, 7)
    return tuple(
        FlagshipPublicPackageLifecycleRecord(
            package_id=package.package_id,
            workflow_family=package.workflow_family,
            lifecycle_path=package.lifecycle_record_path,
            created_on=refreshed_on,
            last_refreshed_on=refreshed_on,
            obsolescence_triggers=(
                "Retire or replace this companion package if a materially harder public variation for the same workflow family is added.",
                "Retire this companion package if its stress profile no longer adds meaningful drift relative to the primary package.",
            ),
            retirement_conditions=(
                "Retire only after a stronger cross-package generalization pair and a refreshed family report are both shipped.",
            ),
            successor_package_id=None,
            note="Companion package lifecycle is governed by whether it still adds real generalization pressure beyond the flagship primary package.",
        )
        for package in list_secondary_public_benchmark_packages()
    )


def build_secondary_public_package_asset_registry() -> (
    SecondaryPublicPackageAssetRegistry
):
    """Return the asset registry for all companion public packages."""

    entries = (
        FlagshipAssetRootEntry(
            package_id="public_companion_package:dda_cross_engine_review_package",
            workflow_family="dda",
            asset_root=_package_root("dda_cross_engine_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                _package_root("dda_cross_engine_review_package")
            ),
            citation_manifest_path=_citation_manifest_path(
                _package_root("dda_cross_engine_review_package")
            ),
            generated_boundary_path=_generated_boundary_path(
                _package_root("dda_cross_engine_review_package")
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                _package_root("dda_cross_engine_review_package")
            ),
            expected_wall_time_minutes=4,
            expected_disk_footprint_mb=8,
            known_license_limits=(
                "The DDA companion package ships checked exported-result and raw-like snapshots, not live Comet or Sage executables.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="dda-companion:comet",
                    public_source_name="Comet DDA companion export snapshot",
                    package_root=_package_root("dda_cross_engine_review_package"),
                    local_relative="primary/comet_pipeline_export.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/search_adapters/comet_pipeline_export.tsv",
                    public_reference_url="https://uwpr.github.io/Comet/",
                    why_it_matters="Comet supplies a different primary import dialect for DDA family generalization.",
                    availability_expectation="The Comet project page should remain reachable while this companion package remains active.",
                    license_note="The local file is a tracked snapshot; the public check targets the project page rather than a binary download.",
                ),
                _remote_source(
                    source_id="dda-companion:sage",
                    public_source_name="Sage DDA companion comparator snapshot",
                    package_root=_package_root("dda_cross_engine_review_package"),
                    local_relative="comparator/sage_pipeline_export.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/search_adapters/sage_pipeline_export.tsv",
                    public_reference_url="https://sage-docs.vercel.app/",
                    why_it_matters="Sage supplies the comparator dialect for the DDA family generalization pair.",
                    availability_expectation="The Sage documentation site should remain reachable while this companion package remains active.",
                    license_note="The local file is a tracked snapshot; the public check targets the documentation site.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:comet_project",
                    title="Comet project documentation",
                    url="https://uwpr.github.io/Comet/",
                    why_it_matters="Comet defines the primary imported-result dialect for the DDA companion package.",
                ),
                _citation(
                    citation_id="citation:sage_project",
                    title="Sage documentation",
                    url="https://sage-docs.vercel.app/",
                    why_it_matters="Sage defines the comparator dialect for the DDA companion package.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_root=_package_root("dda_cross_engine_review_package"),
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    note="README is human-authored to explain how the DDA companion package differs from the flagship primary package.",
                ),
                _boundary(
                    package_root=_package_root("dda_cross_engine_review_package"),
                    artifact_relative="primary/comet_pipeline_export.tsv",
                    boundary_kind=FlagshipAssetBoundaryKind.COPIED_SNAPSHOT,
                    note="Primary DDA companion export is a tracked copied snapshot from core fixtures.",
                ),
                _boundary(
                    package_root=_package_root("dda_cross_engine_review_package"),
                    artifact_relative="comparator/sage_pipeline_export.tsv",
                    boundary_kind=FlagshipAssetBoundaryKind.COPIED_SNAPSHOT,
                    note="Comparator DDA companion export is a tracked copied snapshot from core fixtures.",
                ),
                _boundary(
                    package_root=_package_root("dda_cross_engine_review_package"),
                    artifact_relative="package_manifest.json",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    note="The DDA companion manifest is generated from the repository model.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="public_companion_package:dia_matrix_shift_review_package",
            workflow_family="dia",
            asset_root=_package_root("dia_matrix_shift_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                _package_root("dia_matrix_shift_review_package")
            ),
            citation_manifest_path=_citation_manifest_path(
                _package_root("dia_matrix_shift_review_package")
            ),
            generated_boundary_path=_generated_boundary_path(
                _package_root("dia_matrix_shift_review_package")
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                _package_root("dia_matrix_shift_review_package")
            ),
            expected_wall_time_minutes=4,
            expected_disk_footprint_mb=8,
            known_license_limits=(
                "The DIA companion package ships checked exported-result snapshots and remains library-conditioned.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="dia-companion:diann",
                    public_source_name="DIA-NN companion report snapshot",
                    package_root=_package_root("dia_matrix_shift_review_package"),
                    local_relative="primary/diann_report.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/search_adapters/diann_report.tsv",
                    public_reference_url="https://github.com/vdemichev/DiaNN",
                    why_it_matters="DIA-NN supplies the primary exported-result surface for the DIA companion package.",
                    availability_expectation="The DIA-NN project repository should remain reachable while this companion package remains active.",
                    license_note="The local file is a tracked snapshot; the public check targets the project repository.",
                ),
                _remote_source(
                    source_id="dia-companion:spectronaut",
                    public_source_name="Spectronaut companion comparator snapshot",
                    package_root=_package_root("dia_matrix_shift_review_package"),
                    local_relative="comparator/spectronaut_pipeline_export.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/search_adapters/spectronaut_pipeline_export.tsv",
                    public_reference_url="https://biognosys.com/software/spectronaut/",
                    why_it_matters="Spectronaut supplies the comparator exported-result surface for the DIA companion package.",
                    availability_expectation="The Spectronaut product page should remain reachable while this companion package remains active.",
                    license_note="The local file is a tracked snapshot; the public check targets the product page.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:diann_project",
                    title="DIA-NN project repository",
                    url="https://github.com/vdemichev/DiaNN",
                    why_it_matters="DIA-NN defines the primary exported-result dialect for the DIA companion package.",
                ),
                _citation(
                    citation_id="citation:spectronaut_product",
                    title="Spectronaut product page",
                    url="https://biognosys.com/software/spectronaut/",
                    why_it_matters="Spectronaut defines the comparator surface for the DIA companion package.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_root=_package_root("dia_matrix_shift_review_package"),
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    note="README is human-authored to explain matrix-shift pressure in the DIA companion package.",
                ),
                _boundary(
                    package_root=_package_root("dia_matrix_shift_review_package"),
                    artifact_relative="primary/diann_report.tsv",
                    boundary_kind=FlagshipAssetBoundaryKind.COPIED_SNAPSHOT,
                    note="Primary DIA companion report is a copied snapshot from core fixtures.",
                ),
                _boundary(
                    package_root=_package_root("dia_matrix_shift_review_package"),
                    artifact_relative="package_manifest.json",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    note="The DIA companion manifest is generated from the repository model.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="public_companion_package:lfq_sparse_contrast_review_package",
            workflow_family="lfq",
            asset_root=_package_root("lfq_sparse_contrast_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                _package_root("lfq_sparse_contrast_review_package")
            ),
            citation_manifest_path=_citation_manifest_path(
                _package_root("lfq_sparse_contrast_review_package")
            ),
            generated_boundary_path=_generated_boundary_path(
                _package_root("lfq_sparse_contrast_review_package")
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                _package_root("lfq_sparse_contrast_review_package")
            ),
            expected_wall_time_minutes=3,
            expected_disk_footprint_mb=6,
            known_license_limits=(
                "The LFQ companion package ships tracked feature and design snapshots rather than raw vendor data.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="lfq-companion:edge-case-features",
                    public_source_name="Sparse-cohort LFQ feature snapshot",
                    package_root=_package_root("lfq_sparse_contrast_review_package"),
                    local_relative="evidence/edge_case_ms1_features.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/quant/edge_case_ms1_features.tsv",
                    public_reference_url="https://github.com/bijux/bijux-proteomics",
                    why_it_matters="The edge-case feature table supplies a sparser LFQ cohort shape for generalization pressure.",
                    availability_expectation="The repository source should remain reachable while this companion package remains active.",
                    license_note="This tracked file is a repository-owned snapshot.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:lfq_missingness_review",
                    title="LFQ missingness and reproducibility review",
                    url="https://pubmed.ncbi.nlm.nih.gov/33522158/",
                    why_it_matters="The LFQ companion package exists to stress missingness-aware transfer beyond one cohort shape.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_root=_package_root("lfq_sparse_contrast_review_package"),
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    note="README is human-authored to explain sparse-cohort pressure in the LFQ companion package.",
                ),
                _boundary(
                    package_root=_package_root("lfq_sparse_contrast_review_package"),
                    artifact_relative="evidence/edge_case_ms1_features.tsv",
                    boundary_kind=FlagshipAssetBoundaryKind.COPIED_SNAPSHOT,
                    note="LFQ companion feature table is a copied snapshot from core fixtures.",
                ),
                _boundary(
                    package_root=_package_root("lfq_sparse_contrast_review_package"),
                    artifact_relative="evidence/sparse_reproducibility_manifest.json",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    note="LFQ companion reproducibility manifest is a generated report.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="public_companion_package:multiplex_channel_stress_review_package",
            workflow_family="multiplex",
            asset_root=_package_root("multiplex_channel_stress_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                _package_root("multiplex_channel_stress_review_package")
            ),
            citation_manifest_path=_citation_manifest_path(
                _package_root("multiplex_channel_stress_review_package")
            ),
            generated_boundary_path=_generated_boundary_path(
                _package_root("multiplex_channel_stress_review_package")
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                _package_root("multiplex_channel_stress_review_package")
            ),
            expected_wall_time_minutes=3,
            expected_disk_footprint_mb=6,
            known_license_limits=(
                "The multiplex companion package ships a derived stress table rather than raw reporter-ion vendor data.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="multiplex-companion:stress-features",
                    public_source_name="Channel-stress multiplex feature snapshot",
                    package_root=_package_root(
                        "multiplex_channel_stress_review_package"
                    ),
                    local_relative="evidence/multiplex_channel_stress_ms1_features.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/quant/multiplex_ms1_features.tsv",
                    public_reference_url="https://github.com/bijux/bijux-proteomics",
                    why_it_matters="The stress feature table is derived from the tracked multiplex fixture to expose stronger imbalance.",
                    availability_expectation="The repository source should remain reachable while this companion package remains active.",
                    license_note="This tracked file is a repository-owned derived snapshot.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:multiplex_ratio_compression_review",
                    title="Multiplex ratio-compression review",
                    url="https://pubmed.ncbi.nlm.nih.gov/32883483/",
                    why_it_matters="The multiplex companion package exists to stress ratio compression and channel dropout limits.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_root=_package_root(
                        "multiplex_channel_stress_review_package"
                    ),
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    note="README is human-authored to explain channel-stress pressure in the multiplex companion package.",
                ),
                _boundary(
                    package_root=_package_root(
                        "multiplex_channel_stress_review_package"
                    ),
                    artifact_relative="evidence/multiplex_channel_stress_ms1_features.tsv",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    note="The stress feature table is derived from the flagship multiplex features with stronger imbalance and dropout pressure.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="public_companion_package:ptm_ambiguity_stress_review_package",
            workflow_family="ptm",
            asset_root=_package_root("ptm_ambiguity_stress_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                _package_root("ptm_ambiguity_stress_review_package")
            ),
            citation_manifest_path=_citation_manifest_path(
                _package_root("ptm_ambiguity_stress_review_package")
            ),
            generated_boundary_path=_generated_boundary_path(
                _package_root("ptm_ambiguity_stress_review_package")
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                _package_root("ptm_ambiguity_stress_review_package")
            ),
            expected_wall_time_minutes=4,
            expected_disk_footprint_mb=7,
            known_license_limits=(
                "The PTM companion package ships tracked ambiguity-stress snapshots rather than vendor-native raw files.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="ptm-companion:localization",
                    public_source_name="PTM ambiguity-stress localization snapshot",
                    package_root=_package_root("ptm_ambiguity_stress_review_package"),
                    local_relative="evidence/localization_results.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/ptm/localization_results.tsv",
                    public_reference_url="https://github.com/bijux/bijux-proteomics",
                    why_it_matters="The PTM ambiguity stress table is derived from the tracked localization fixture.",
                    availability_expectation="The repository source should remain reachable while this companion package remains active.",
                    license_note="This tracked file is a repository-owned derived snapshot.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:ptm_localization_review",
                    title="PTM localization confidence review",
                    url="https://pubmed.ncbi.nlm.nih.gov/28104535/",
                    why_it_matters="The PTM companion package exists to stress ambiguity-sensitive transfer.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_root=_package_root("ptm_ambiguity_stress_review_package"),
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    note="README is human-authored to explain ambiguity-stress pressure in the PTM companion package.",
                ),
                _boundary(
                    package_root=_package_root("ptm_ambiguity_stress_review_package"),
                    artifact_relative="evidence/localization_results.tsv",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    note="The localization table is derived from the flagship PTM localization table with stronger ambiguity pressure.",
                ),
            ),
        ),
        FlagshipAssetRootEntry(
            package_id="public_companion_package:targeted_carryover_review_package",
            workflow_family="targeted",
            asset_root=_package_root("targeted_carryover_review_package"),
            source_locator_manifest_path=_source_locator_manifest_path(
                _package_root("targeted_carryover_review_package")
            ),
            citation_manifest_path=_citation_manifest_path(
                _package_root("targeted_carryover_review_package")
            ),
            generated_boundary_path=_generated_boundary_path(
                _package_root("targeted_carryover_review_package")
            ),
            rebuild_instructions_path=_rebuild_instructions_path(
                _package_root("targeted_carryover_review_package")
            ),
            expected_wall_time_minutes=4,
            expected_disk_footprint_mb=7,
            known_license_limits=(
                "The targeted companion package ships a derived QC table and copied follow-up packets rather than vendor-native chromatograms.",
            ),
            remote_sources=(
                _remote_source(
                    source_id="targeted-companion:qc",
                    public_source_name="Targeted carryover QC snapshot",
                    package_root=_package_root("targeted_carryover_review_package"),
                    local_relative="evidence/targeted_benchmark_qc.tsv",
                    upstream_repo_source_path="packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv",
                    public_reference_url="https://github.com/bijux/bijux-proteomics",
                    why_it_matters="The carryover stress QC table is derived from the tracked targeted QC fixture.",
                    availability_expectation="The repository source should remain reachable while this companion package remains active.",
                    license_note="This tracked file is a repository-owned derived snapshot.",
                ),
            ),
            citations=(
                _citation(
                    citation_id="citation:targeted_carryover_review",
                    title="Targeted assay carryover and calibration review",
                    url="https://pubmed.ncbi.nlm.nih.gov/27556322/",
                    why_it_matters="The targeted companion package exists to stress carryover and calibration-sensitive transfer.",
                ),
            ),
            generated_boundaries=(
                _boundary(
                    package_root=_package_root("targeted_carryover_review_package"),
                    artifact_relative="README.md",
                    boundary_kind=FlagshipAssetBoundaryKind.CURATED_README,
                    note="README is human-authored to explain carryover stress in the targeted companion package.",
                ),
                _boundary(
                    package_root=_package_root("targeted_carryover_review_package"),
                    artifact_relative="evidence/targeted_benchmark_qc.tsv",
                    boundary_kind=FlagshipAssetBoundaryKind.GENERATED_REPORT,
                    note="The targeted QC table is derived from the flagship QC table with stronger carryover drift.",
                ),
            ),
        ),
    )
    return SecondaryPublicPackageAssetRegistry(
        registry_id="secondary-public-package-asset-registry",
        artifact_path=_GENERALIZATION_REGISTRY_PATH,
        entries=entries,
        note="These companion public packages exist to pressure family transfer beyond the single primary flagship package for each workflow family.",
    )


def _primary_package_for_family(
    workflow_family: str,
) -> FlagshipPublicBenchmarkPackage:
    return {
        "dda": build_flagship_dda_public_benchmark_package(),
        "dia": build_flagship_dia_public_benchmark_package(),
        "lfq": build_flagship_lfq_public_benchmark_package(),
        "multiplex": build_flagship_multiplex_public_benchmark_package(),
        "ptm": build_flagship_ptm_public_benchmark_package(),
        "targeted": build_flagship_targeted_public_benchmark_package(),
    }[workflow_family]


def _secondary_package_for_family(
    workflow_family: str,
) -> FlagshipPublicBenchmarkPackage:
    return {
        "dda": build_secondary_dda_public_benchmark_package(),
        "dia": build_secondary_dia_public_benchmark_package(),
        "lfq": build_secondary_lfq_public_benchmark_package(),
        "multiplex": build_secondary_multiplex_public_benchmark_package(),
        "ptm": build_secondary_ptm_public_benchmark_package(),
        "targeted": build_secondary_targeted_public_benchmark_package(),
    }[workflow_family]


def _metric_delta(
    metric_id: str,
    primary_value: float,
    secondary_value: float,
    interpretation: str,
) -> WorkflowGeneralizationMetricDelta:
    return WorkflowGeneralizationMetricDelta(
        metric_id=metric_id,
        primary_value=primary_value,
        secondary_value=secondary_value,
        delta=secondary_value - primary_value,
        interpretation=interpretation,
    )


def _finding(
    claim_id: str,
    summary: str,
    state: WorkflowGeneralizationFindingState,
    evidence_paths: tuple[str, ...],
    note: str,
) -> WorkflowGeneralizationFinding:
    return WorkflowGeneralizationFinding(
        claim_id=claim_id,
        summary=summary,
        state=state,
        evidence_paths=evidence_paths,
        note=note,
    )


def _stability_score(
    *,
    metric_deltas: tuple[WorkflowGeneralizationMetricDelta, ...],
    findings: tuple[WorkflowGeneralizationFinding, ...],
) -> float:
    weakened = sum(
        1
        for finding in findings
        if finding.state is WorkflowGeneralizationFindingState.WEAKENS
    )
    collapsed = sum(
        1
        for finding in findings
        if finding.state is WorkflowGeneralizationFindingState.COLLAPSES
    )
    metric_pressure = sum(
        min(abs(delta.delta) / max(delta.primary_value, 1.0), 1.0)
        for delta in metric_deltas
    )
    raw_score = 1.0 - (0.12 * weakened) - (0.22 * collapsed) - (0.08 * metric_pressure)
    return round(max(0.0, min(raw_score, 1.0)), 2)


def _stability_label(
    score: float,
    findings: tuple[WorkflowGeneralizationFinding, ...],
) -> str:
    if any(
        finding.state is WorkflowGeneralizationFindingState.COLLAPSES
        for finding in findings
    ):
        return "fragile_transfer" if score >= 0.4 else "package_specific"
    if score >= 0.8:
        return "highly_stable"
    if score >= 0.6:
        return "bounded_but_stable"
    if score >= 0.4:
        return "fragile_transfer"
    return "package_specific"


def _sample_count(path: str) -> int:
    return _tsv_row_count(path)


def _high_confidence_ptm_sites(path: str) -> int:
    with _repo_path(path).open(newline="", encoding="utf-8") as handle:
        return sum(
            1
            for row in csv.DictReader(handle, delimiter="\t")
            if float(row["localization_score"]) >= 0.99
        )


def _targeted_tic_median(path: str) -> float:
    values: list[float] = []
    with _repo_path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            values.append(float(row["tic"]))
    values.sort()
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2.0


def build_workflow_generalization_reports() -> tuple[WorkflowGeneralizationReport, ...]:
    """Build cross-package generalization reports for every workflow family."""

    reports: list[WorkflowGeneralizationReport] = []
    for workflow_family in ("dda", "dia", "lfq", "multiplex", "ptm", "targeted"):
        primary = _primary_package_for_family(workflow_family)
        secondary = _secondary_package_for_family(workflow_family)
        report_path = _report_path(Path(secondary.package_root).name)
        if workflow_family == "dda":
            metrics = (
                _metric_delta(
                    "primary_import_rows",
                    _tsv_row_count(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/primary/maxquant_pipeline_export.tsv"
                    ),
                    _tsv_row_count(
                        f"{secondary.package_root}/primary/comet_pipeline_export.tsv"
                    ),
                    "The companion DDA package has fewer accepted imported rows, so family trust cannot assume primary-import density transfers unchanged.",
                ),
                _metric_delta(
                    "comparator_rows",
                    _tsv_row_count(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/comparator/msfragger_pipeline_export.tsv"
                    ),
                    _tsv_row_count(
                        f"{secondary.package_root}/comparator/sage_pipeline_export.tsv"
                    ),
                    "Comparator density shifts under the companion engine pairing.",
                ),
            )
            findings = (
                _finding(
                    "target-decoy-semantics",
                    "Target-decoy-facing import normalization still survives the second DDA package.",
                    WorkflowGeneralizationFindingState.SURVIVES,
                    (
                        primary.benchmark_manifest_path,
                        secondary.benchmark_manifest_path,
                    ),
                    "The second package still keeps target and decoy records visible and reviewable.",
                ),
                _finding(
                    "protein-rollup-stability",
                    "Protein-rollup caution remains necessary and becomes slightly harsher under the companion engine pairing.",
                    WorkflowGeneralizationFindingState.WEAKENS,
                    (
                        primary.quality_sheet_path,
                        secondary.quality_sheet_path,
                    ),
                    "Cross-engine protein-facing confidence is still not strong enough to remove the downgrade-heavy DDA stance.",
                ),
            )
            runtime_package_ids = (
                "dda-maxquant-pipeline-corpus",
                "dda-comet-cross-engine-corpus",
            )
        elif workflow_family == "dia":
            metrics = (
                _metric_delta(
                    "primary_precursor_rows",
                    _tsv_row_count(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_report.tsv"
                    ),
                    _tsv_row_count(
                        f"{secondary.package_root}/primary/diann_report.tsv"
                    ),
                    "The companion DIA package is visibly thinner at the precursor-report layer.",
                ),
                _metric_delta(
                    "primary_pipeline_rows",
                    _tsv_row_count(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/primary/spectronaut_pipeline_export.tsv"
                    ),
                    _tsv_row_count(
                        f"{secondary.package_root}/primary/diann_pipeline_export.tsv"
                    ),
                    "The exported-result density shifts materially across the DIA family pair.",
                ),
            )
            findings = (
                _finding(
                    "library-conditioned-precursor-review",
                    "Library-conditioned precursor review survives across both DIA public packages.",
                    WorkflowGeneralizationFindingState.SURVIVES,
                    (
                        primary.benchmark_manifest_path,
                        secondary.benchmark_manifest_path,
                    ),
                    "Both packages still support bounded precursor-facing review under explicit library conditions.",
                ),
                _finding(
                    "protein-absence-overreach",
                    "Protein-level absence language becomes weaker on the companion package and must stay downgrade-heavy.",
                    WorkflowGeneralizationFindingState.WEAKENS,
                    (
                        primary.quality_sheet_path,
                        secondary.quality_sheet_path,
                    ),
                    "The thinner companion package keeps protein-level overreach pressure visible.",
                ),
            )
            runtime_package_ids = (
                "dia-diann-pipeline-corpus",
                "dia-matrix-shift-review-corpus",
            )
        elif workflow_family == "lfq":
            metrics = (
                _metric_delta(
                    "feature_rows",
                    _tsv_row_count(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv"
                    ),
                    _tsv_row_count(
                        f"{secondary.package_root}/evidence/edge_case_ms1_features.tsv"
                    ),
                    "The LFQ companion package has a smaller feature table and therefore a different missingness burden.",
                ),
                _metric_delta(
                    "design_rows",
                    _sample_count(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale.design.tsv"
                    ),
                    _sample_count(
                        f"{secondary.package_root}/evidence/edge_case.design.tsv"
                    ),
                    "The LFQ companion package uses a different replicate and batch structure.",
                ),
            )
            findings = (
                _finding(
                    "missingness-visibility",
                    "The repository still keeps missingness and QC visibility explicit across both LFQ packages.",
                    WorkflowGeneralizationFindingState.SURVIVES,
                    (
                        primary.package_root,
                        secondary.package_root,
                    ),
                    "The second package does not flatten missingness into smooth summary prose.",
                ),
                _finding(
                    "effect-direction-stability",
                    "Effect-direction confidence weakens under the sparse companion cohort and remains bounded.",
                    WorkflowGeneralizationFindingState.WEAKENS,
                    (
                        primary.quality_sheet_path,
                        secondary.quality_sheet_path,
                    ),
                    "The family claim survives only as bounded review-grade quant interpretation, not broad transfer.",
                ),
            )
            runtime_package_ids = (
                "lfq-cohort-review-corpus",
                "lfq-sparse-contrast-review-corpus",
            )
        elif workflow_family == "multiplex":
            metrics = (
                _metric_delta(
                    "feature_rows",
                    _tsv_row_count(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/evidence/multiplex_ms1_features.tsv"
                    ),
                    _tsv_row_count(
                        f"{secondary.package_root}/evidence/multiplex_channel_stress_ms1_features.tsv"
                    ),
                    "The multiplex companion package keeps a similar feature count while changing channel imbalance and dropout pressure.",
                ),
                _metric_delta(
                    "missing_channel_rows",
                    0.0,
                    sum(
                        1
                        for row in csv.DictReader(
                            _repo_path(
                                f"{secondary.package_root}/evidence/multiplex_channel_stress_ms1_features.tsv"
                            ).open(newline="", encoding="utf-8"),
                            delimiter="\t",
                        )
                        if row["missing_reason"].strip()
                    ),
                    "The companion multiplex package introduces explicit missing-channel rows that the flagship package does not carry.",
                ),
            )
            findings = (
                _finding(
                    "channel-imbalance-visibility",
                    "Channel imbalance and dropout pressure are still visible across both multiplex packages.",
                    WorkflowGeneralizationFindingState.SURVIVES,
                    (
                        primary.package_root,
                        secondary.package_root,
                    ),
                    "The second package keeps the internal-support boundary honest under stronger stress.",
                ),
                _finding(
                    "outsider-auditable-authority",
                    "Multiplex still does not earn outsider-facing trust language even with a second package.",
                    WorkflowGeneralizationFindingState.COLLAPSES,
                    (
                        secondary.quality_sheet_path,
                        secondary.benchmark_manifest_path,
                    ),
                    "The second package strengthens the stress surface, but it does not add outsider review or lab consequence authority.",
                ),
            )
            runtime_package_ids = (
                "multiplex-tmtpro-review-corpus",
                "multiplex-channel-stress-review-corpus",
            )
        elif workflow_family == "ptm":
            metrics = (
                _metric_delta(
                    "high_confidence_localizations",
                    _high_confidence_ptm_sites(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv"
                    ),
                    _high_confidence_ptm_sites(
                        f"{secondary.package_root}/evidence/localization_results.tsv"
                    ),
                    "The companion PTM package sharply reduces high-confidence localization count.",
                ),
                _metric_delta(
                    "localization_rows",
                    _tsv_row_count(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/evidence/localization_results.tsv"
                    ),
                    _tsv_row_count(
                        f"{secondary.package_root}/evidence/localization_results.tsv"
                    ),
                    "The companion PTM package keeps row volume similar while confidence shifts downward.",
                ),
            )
            findings = (
                _finding(
                    "localization-visibility",
                    "Localization-facing review still survives across both PTM public packages.",
                    WorkflowGeneralizationFindingState.SURVIVES,
                    (
                        primary.package_root,
                        secondary.package_root,
                    ),
                    "Both packages still make ambiguity and site-level evidence inspectable.",
                ),
                _finding(
                    "targetability-promotion",
                    "Targetability confidence weakens materially on the ambiguity-stress package.",
                    WorkflowGeneralizationFindingState.WEAKENS,
                    (
                        primary.quality_sheet_path,
                        secondary.quality_sheet_path,
                    ),
                    "The second package keeps PTM targetability bounded by ambiguity-aware consequence planning.",
                ),
            )
            runtime_package_ids = (
                "ptm-localization-review-corpus",
                "ptm-ambiguity-stress-review-corpus",
            )
        else:
            metrics = (
                _metric_delta(
                    "qc_rows",
                    _tsv_row_count(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv"
                    ),
                    _tsv_row_count(
                        f"{secondary.package_root}/evidence/targeted_benchmark_qc.tsv"
                    ),
                    "The targeted companion package keeps similar QC density while shifting the intensity profile downward.",
                ),
                _metric_delta(
                    "median_tic",
                    _targeted_tic_median(
                        "packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/evidence/targeted_benchmark_qc.tsv"
                    ),
                    _targeted_tic_median(
                        f"{secondary.package_root}/evidence/targeted_benchmark_qc.tsv"
                    ),
                    "Median TIC drops on the carryover-stress targeted package.",
                ),
            )
            findings = (
                _finding(
                    "calibration-and-transition-visibility",
                    "Calibration and transition QC visibility still survive across both targeted public packages.",
                    WorkflowGeneralizationFindingState.SURVIVES,
                    (
                        primary.package_root,
                        secondary.package_root,
                    ),
                    "The second package still keeps approved, failed, and refused targeted consequence states visible.",
                ),
                _finding(
                    "promotion-confidence",
                    "Promotion confidence weakens on the carryover-stress targeted package and remains bounded.",
                    WorkflowGeneralizationFindingState.WEAKENS,
                    (
                        primary.quality_sheet_path,
                        secondary.quality_sheet_path,
                    ),
                    "The second package makes it explicit that targeted authority is not tied to one cleaner QC table.",
                ),
            )
            runtime_package_ids = (
                "targeted-transition-review-corpus",
                "targeted-carryover-review-corpus",
            )
        score = _stability_score(metric_deltas=metrics, findings=findings)
        reports.append(
            WorkflowGeneralizationReport(
                report_id=f"{workflow_family}-cross-package-generalization",
                workflow_family=workflow_family,
                primary_package_id=primary.package_id,
                secondary_package_id=secondary.package_id,
                artifact_path=report_path,
                package_manifest_paths=(
                    primary.benchmark_manifest_path,
                    secondary.benchmark_manifest_path,
                ),
                runtime_package_ids=runtime_package_ids,
                metric_deltas=metrics,
                findings=findings,
                family_stability_score=score,
                family_stability_label=_stability_label(score, findings),
                note=(
                    "This report is the public family-transfer surface. It records what still survives when the workflow moves from the flagship primary package to a second package with a materially different pressure profile."
                ),
            )
        )
    return tuple(reports)


def build_workflow_family_stability_scorecard() -> WorkflowFamilyStabilityScorecard:
    """Return the per-family stability scorecard derived from generalization reports."""

    entries: list[WorkflowFamilyStabilityRecord] = []
    for report in build_workflow_generalization_reports():
        surviving = sum(
            1
            for finding in report.findings
            if finding.state is WorkflowGeneralizationFindingState.SURVIVES
        )
        weakened = sum(
            1
            for finding in report.findings
            if finding.state is WorkflowGeneralizationFindingState.WEAKENS
        )
        collapsed = sum(
            1
            for finding in report.findings
            if finding.state is WorkflowGeneralizationFindingState.COLLAPSES
        )
        entries.append(
            WorkflowFamilyStabilityRecord(
                workflow_family=report.workflow_family,
                primary_package_id=report.primary_package_id,
                secondary_package_id=report.secondary_package_id,
                report_path=report.artifact_path,
                stability_score=report.family_stability_score,
                surviving_claim_count=surviving,
                weakened_claim_count=weakened,
                collapsed_claim_count=collapsed,
                note=(
                    "The stability score is driven by measured package deltas plus claim outcomes from the cross-package report."
                ),
            )
        )
    return WorkflowFamilyStabilityScorecard(
        scorecard_id="workflow-family-stability-scorecard",
        artifact_path=_FAMILY_STABILITY_SCORECARD_PATH,
        entries=tuple(entries),
        note=(
            "Family stability stays visible as a measured public score instead of disappearing behind one unusually convenient flagship package."
        ),
    )


def count_public_packages_for_family(workflow_family: str) -> int:
    """Return how many tracked public packages currently back one workflow family."""

    return (
        2
        if workflow_family in {"dda", "dia", "lfq", "multiplex", "ptm", "targeted"}
        else 0
    )


__all__ = [
    "SecondaryPublicPackageAssetRegistry",
    "WorkflowFamilyStabilityRecord",
    "WorkflowFamilyStabilityScorecard",
    "WorkflowGeneralizationFinding",
    "WorkflowGeneralizationFindingState",
    "WorkflowGeneralizationMetricDelta",
    "WorkflowGeneralizationReport",
    "build_secondary_dda_public_benchmark_package",
    "build_secondary_dia_public_benchmark_package",
    "build_secondary_lfq_public_benchmark_package",
    "build_secondary_multiplex_public_benchmark_package",
    "build_secondary_ptm_public_benchmark_package",
    "build_secondary_public_package_artifact_inventories",
    "build_secondary_public_package_asset_registry",
    "build_secondary_public_package_lifecycle_records",
    "build_secondary_public_package_quality_sheets",
    "build_secondary_targeted_public_benchmark_package",
    "build_workflow_family_stability_scorecard",
    "build_workflow_generalization_reports",
    "count_public_packages_for_family",
    "list_secondary_public_benchmark_packages",
]
