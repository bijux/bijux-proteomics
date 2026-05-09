# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared support for benchmark-facing review and release surfaces."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path

from bijux_proteomics.benchmarks.flagship_asset_roots import (
    FlagshipAssetRootEntry,
    list_flagship_asset_root_entries,
)
from bijux_proteomics.benchmarks.flagship_public_packages import (
    FlagshipPublicBenchmarkAsset,
    FlagshipPublicPackageArtifactInventory,
    FlagshipPublicPackageArtifactRecord,
    FlagshipPublicPackageLifecycleRecord,
    FlagshipPublicPackageQualitySheet,
    build_flagship_public_package_artifact_inventories,
    build_flagship_public_package_lifecycle_records,
    build_flagship_public_package_quality_sheets,
    list_flagship_public_benchmark_packages,
)
from bijux_proteomics.benchmarks.workflow_generalization import (
    WorkflowGeneralizationReport,
    build_secondary_public_package_artifact_inventories,
    build_secondary_public_package_asset_registry,
    build_secondary_public_package_lifecycle_records,
    build_secondary_public_package_quality_sheets,
    build_workflow_generalization_reports,
    list_secondary_public_benchmark_packages,
)
from bijux_proteomics_intelligence.reviews.workflow_authority import (
    WorkflowAuthorityRow,
    build_workflow_authority_matrix,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
)
from bijux_proteomics_runtime.workflows.benchmark_runs import (
    BenchmarkRunSpec,
    BenchmarkRuntimeTruthRow,
    build_benchmark_run_specs,
    build_benchmark_runtime_truth_surface,
)

__all__ = [
    "CORE_FOUNDATION_DIR",
    "LAST_REVIEWED",
    "REPO_ROOT",
    "RUNTIME_DIR",
    "BenchmarkPackageBundle",
    "artifact_inventory_by_path",
    "build_generalization_report_map",
    "build_runtime_spec_map",
    "build_runtime_truth_map",
    "build_workflow_authority_row_map",
    "bundle_runtime_spec",
    "bundle_sort_key",
    "family_order",
    "iter_benchmark_package_bundles",
    "package_sha256",
]


REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "docs").is_dir()
)
CORE_FOUNDATION_DIR = REPO_ROOT / "docs" / "04-bijux-proteomics-core" / "foundation"
RUNTIME_DIR = REPO_ROOT / "docs" / "09-bijux-proteomics-runtime"
LAST_REVIEWED = "2026-05-09"

_PRIMARY_REFRESH_COMMAND = (
    "uv run --group dev python -m "
    "bijux_proteomics.benchmarks.flagship_asset_maintenance refresh"
)
_COMPANION_REFRESH_COMMAND = (
    "uv run --group dev python -m "
    "bijux_proteomics.benchmarks.workflow_generalization_assets refresh"
)
_FAMILY_ORDER = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.MULTIPLEX,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
)


@dataclass(frozen=True)
class BenchmarkPackageBundle:
    """One public benchmark package plus the review metadata around it."""

    workflow_family: KnowledgeWorkflowFamily
    package_role: str
    package_id: str
    package_label: str
    package_root: str
    benchmark_manifest_path: str
    artifact_inventory_path: str
    quality_sheet_path: str
    lifecycle_record_path: str
    source_locator_manifest_path: str
    citation_manifest_path: str
    generated_boundary_path: str
    rebuild_instructions_path: str
    rebuild_command: str
    public_dataset_identity: str
    claim_scope: str
    runtime_availability: str
    comparator_availability: str
    note: str
    source_assets: tuple[FlagshipPublicBenchmarkAsset, ...]
    inventory: FlagshipPublicPackageArtifactInventory
    quality_sheet: FlagshipPublicPackageQualitySheet
    lifecycle_record: FlagshipPublicPackageLifecycleRecord
    asset_root_entry: FlagshipAssetRootEntry
    benchmark_manifest: BenchmarkManifest


def family_order(workflow_family: KnowledgeWorkflowFamily) -> int:
    """Return the stable family sort order used by review pages."""

    return _FAMILY_ORDER.index(workflow_family)


def bundle_sort_key(bundle: BenchmarkPackageBundle) -> tuple[int, int]:
    """Sort primaries before companions inside the stable family order."""

    role_rank = 0 if bundle.package_role == "primary" else 1
    return family_order(bundle.workflow_family), role_rank


def package_sha256(repo_relative_path: str) -> str:
    """Return the repository-local digest for one tracked artifact."""

    return hashlib.sha256((REPO_ROOT / repo_relative_path).read_bytes()).hexdigest()


def artifact_inventory_by_path(
    bundle: BenchmarkPackageBundle,
) -> dict[str, FlagshipPublicPackageArtifactRecord]:
    """Return inventory rows keyed by repo-relative path."""

    return {
        artifact.repo_relative_path: artifact for artifact in bundle.inventory.artifacts
    }


def _benchmark_manifest(
    workflow_family: KnowledgeWorkflowFamily,
) -> BenchmarkManifest:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    if manifest is None:  # pragma: no cover - guarded by existing scientific tests
        raise ValueError(f"missing benchmark manifest for {workflow_family.value}")
    return manifest


def _primary_bundle_map() -> dict[str, BenchmarkPackageBundle]:
    packages = {
        package.package_id: package for package in list_flagship_public_benchmark_packages()
    }
    inventories = {
        inventory.package_id: inventory
        for inventory in build_flagship_public_package_artifact_inventories()
    }
    quality_sheets = {
        sheet.package_id: sheet
        for sheet in build_flagship_public_package_quality_sheets()
    }
    lifecycle_records = {
        record.package_id: record
        for record in build_flagship_public_package_lifecycle_records()
    }
    asset_roots = {
        entry.package_id: entry for entry in list_flagship_asset_root_entries()
    }
    bundles: dict[str, BenchmarkPackageBundle] = {}
    for package_id, package in packages.items():
        workflow_family = KnowledgeWorkflowFamily(package.workflow_family)
        bundles[package_id] = BenchmarkPackageBundle(
            workflow_family=workflow_family,
            package_role="primary",
            package_id=package.package_id,
            package_label=package.package_label,
            package_root=package.package_root,
            benchmark_manifest_path=package.benchmark_manifest_path,
            artifact_inventory_path=package.artifact_inventory_path,
            quality_sheet_path=package.quality_sheet_path,
            lifecycle_record_path=package.lifecycle_record_path,
            source_locator_manifest_path=package.source_locator_manifest_path,
            citation_manifest_path=package.citation_manifest_path,
            generated_boundary_path=package.generated_boundary_path,
            rebuild_instructions_path=package.rebuild_instructions_path,
            rebuild_command=_PRIMARY_REFRESH_COMMAND,
            public_dataset_identity=package.public_dataset_identity,
            claim_scope=package.claim_scope,
            runtime_availability=package.runtime_availability,
            comparator_availability=package.comparator_availability,
            note=package.note,
            source_assets=package.source_assets,
            inventory=inventories[package_id],
            quality_sheet=quality_sheets[package_id],
            lifecycle_record=lifecycle_records[package_id],
            asset_root_entry=asset_roots[package_id],
            benchmark_manifest=_benchmark_manifest(workflow_family),
        )
    return bundles


def _companion_bundle_map() -> dict[str, BenchmarkPackageBundle]:
    packages = {
        package.package_id: package
        for package in list_secondary_public_benchmark_packages()
    }
    inventories = {
        inventory.package_id: inventory
        for inventory in build_secondary_public_package_artifact_inventories()
    }
    quality_sheets = {
        sheet.package_id: sheet
        for sheet in build_secondary_public_package_quality_sheets()
    }
    lifecycle_records = {
        record.package_id: record
        for record in build_secondary_public_package_lifecycle_records()
    }
    asset_roots = {
        entry.package_id: entry
        for entry in build_secondary_public_package_asset_registry().entries
    }
    bundles: dict[str, BenchmarkPackageBundle] = {}
    for package_id, package in packages.items():
        workflow_family = KnowledgeWorkflowFamily(package.workflow_family)
        bundles[package_id] = BenchmarkPackageBundle(
            workflow_family=workflow_family,
            package_role="companion",
            package_id=package.package_id,
            package_label=package.package_label,
            package_root=package.package_root,
            benchmark_manifest_path=package.benchmark_manifest_path,
            artifact_inventory_path=package.artifact_inventory_path,
            quality_sheet_path=package.quality_sheet_path,
            lifecycle_record_path=package.lifecycle_record_path,
            source_locator_manifest_path=package.source_locator_manifest_path,
            citation_manifest_path=package.citation_manifest_path,
            generated_boundary_path=package.generated_boundary_path,
            rebuild_instructions_path=package.rebuild_instructions_path,
            rebuild_command=_COMPANION_REFRESH_COMMAND,
            public_dataset_identity=package.public_dataset_identity,
            claim_scope=package.claim_scope,
            runtime_availability=package.runtime_availability,
            comparator_availability=package.comparator_availability,
            note=package.note,
            source_assets=package.source_assets,
            inventory=inventories[package_id],
            quality_sheet=quality_sheets[package_id],
            lifecycle_record=lifecycle_records[package_id],
            asset_root_entry=asset_roots[package_id],
            benchmark_manifest=_benchmark_manifest(workflow_family),
        )
    return bundles


def iter_benchmark_package_bundles() -> tuple[BenchmarkPackageBundle, ...]:
    """Return all public primary and companion benchmark packages."""

    bundles = [
        *_primary_bundle_map().values(),
        *_companion_bundle_map().values(),
    ]
    return tuple(sorted(bundles, key=bundle_sort_key))


def build_generalization_report_map() -> dict[str, WorkflowGeneralizationReport]:
    """Return cross-package generalization reports keyed by family id."""

    return {
        report.workflow_family: report for report in build_workflow_generalization_reports()
    }


def build_runtime_spec_map() -> dict[str, BenchmarkRunSpec]:
    """Return runtime benchmark specs keyed by package id."""

    return {spec.package_id: spec for spec in build_benchmark_run_specs()}


def build_runtime_truth_map() -> dict[str, BenchmarkRuntimeTruthRow]:
    """Return runtime benchmark truth rows keyed by runtime workflow id."""

    return {
        row.workflow_family: row for row in build_benchmark_runtime_truth_surface()
    }


def build_workflow_authority_row_map() -> dict[str, WorkflowAuthorityRow]:
    """Return workflow authority rows keyed by scientific family id."""

    return {
        row.workflow_family.value: row for row in build_workflow_authority_matrix().rows
    }


def bundle_runtime_spec(bundle: BenchmarkPackageBundle) -> BenchmarkRunSpec | None:
    """Return the runtime spec that executes or imports one public package."""

    package_manifest_path = bundle.benchmark_manifest_path
    for spec in build_benchmark_run_specs():
        if package_manifest_path in spec.public_package_paths:
            return spec
    return None
