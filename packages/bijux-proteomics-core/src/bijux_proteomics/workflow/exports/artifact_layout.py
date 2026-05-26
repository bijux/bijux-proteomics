# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable on-disk layout for workflow-owned result directories."""

from __future__ import annotations

import csv
import hashlib
import json
from io import StringIO
import shutil
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._atomic_files import atomic_copy_file, atomic_write_text
from bijux_proteomics._output_tables import (
    OutputTableSchema,
    infer_output_table_schema,
    validate_output_table_text,
)
from bijux_proteomics.domain.errors import InvalidWorkflowError, ScientificEvidenceError
from bijux_proteomics.domain.semantic_ids import build_artifact_id
from bijux_proteomics_foundation import JsonModel


class WorkflowArtifactFolder(StrEnum):
    """Canonical top-level folders used by workflow-owned output directories."""

    INPUTS = "inputs"
    QC = "qc"
    EVIDENCE = "evidence"
    MATRICES = "matrices"
    STATS = "stats"
    BIOLOGY = "biology"
    CARDS = "cards"
    REPORTS = "reports"


class WorkflowArtifactKind(StrEnum):
    """Stable file-format kinds tracked in workflow artifact manifests."""

    TSV_TABLE = "tsv_table"
    JSON_DOCUMENT = "json_document"
    TEXT_DOCUMENT = "text_document"


class WorkflowArtifactLayoutEntry(JsonModel):
    """One canonical artifact placement inside a workflow output directory."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    legacy_relative_path: str = Field(..., min_length=1)
    relative_path: str = Field(..., min_length=1)
    canonical_relative_path: str = Field(..., min_length=1)
    folder: WorkflowArtifactFolder
    artifact_kind: WorkflowArtifactKind
    artifact_schema: str = Field(..., min_length=1)
    artifact_schema_version: str = Field(..., min_length=1)
    output_table_schema: OutputTableSchema | None = None
    output_table_schema_sidecar_relative_path: str | None = None
    row_count: int = Field(..., ge=0)
    checksum_sha256: str = Field(..., min_length=64, max_length=64)
    producer_function: str = Field(..., min_length=1)


class WorkflowArtifactLayoutManifest(JsonModel):
    """Stable machine-readable layout description over one workflow directory."""

    model_config = ConfigDict(extra="forbid")

    layout_name: str = "workflow_artifact_layout"
    manifest_schema_version: str = "2026-05-25"
    producer_function: str = Field(..., min_length=1)
    folder_names: tuple[str, ...] = Field(
        default_factory=lambda: tuple(folder.value for folder in WorkflowArtifactFolder)
    )
    artifacts: tuple[WorkflowArtifactLayoutEntry, ...] = Field(default_factory=tuple)


class WorkflowArtifactLayoutIndex(JsonModel):
    """Indexed lookup surface over one workflow artifact layout manifest."""

    model_config = ConfigDict(extra="forbid")

    manifest: WorkflowArtifactLayoutManifest
    artifact_ids: dict[str, int] = Field(default_factory=dict)
    legacy_relative_paths: dict[str, int] = Field(default_factory=dict)
    relative_paths: dict[str, int] = Field(default_factory=dict)
    canonical_relative_paths: dict[str, int] = Field(default_factory=dict)


class WorkflowArtifactExpectation(JsonModel):
    """One workflow-owned artifact declared by a typed workflow manifest."""

    model_config = ConfigDict(extra="forbid")

    source_manifest_relative_path: str = Field(..., min_length=1)
    manifest_key_path: str = Field(..., min_length=1)
    legacy_relative_path: str = Field(..., min_length=1)
    canonical_relative_path: str = Field(..., min_length=1)


class WorkflowArtifactInventoryEntry(JsonModel):
    """One inventory row over a produced workflow artifact."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    legacy_relative_path: str = Field(..., min_length=1)
    canonical_relative_path: str = Field(..., min_length=1)
    folder: WorkflowArtifactFolder
    artifact_kind: WorkflowArtifactKind
    row_count: int = Field(..., ge=0)


class WorkflowArtifactInventorySummary(JsonModel):
    """Aggregate inventory counts over one workflow output directory."""

    model_config = ConfigDict(extra="forbid")

    artifact_count: int = Field(..., ge=0)
    tsv_artifact_count: int = Field(..., ge=0)
    total_tsv_row_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


WORKFLOW_ARTIFACT_INVENTORY_NAME = "artifact_inventory.tsv"
WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME = "artifact_inventory_summary.tsv"


def synchronize_workflow_artifact_layout(
    output_dir: Path,
    *,
    producer_function: str = "synchronize_workflow_artifact_layout",
) -> WorkflowArtifactLayoutManifest:
    """Populate canonical workflow folders from flat compatibility artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    _prepare_managed_directories(output_dir)
    entries: list[WorkflowArtifactLayoutEntry] = []
    for path in sorted(output_dir.iterdir(), key=lambda entry: entry.name):
        if not path.is_file() or path.name in {
            "manifest.json",
            WORKFLOW_ARTIFACT_INVENTORY_NAME,
            WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME,
        }:
            continue
        folder = classify_workflow_artifact_name(path.name)
        canonical_relative_path = f"{folder.value}/{path.name}"
        atomic_copy_file(path, output_dir / canonical_relative_path)
        canonical_path = output_dir / canonical_relative_path
        entries.append(
            _build_layout_entry(
                canonical_path=canonical_path,
                legacy_relative_path=path.name,
                canonical_relative_path=canonical_relative_path,
                folder=folder,
                producer_function=producer_function,
            )
        )
    inventory_entries = build_workflow_artifact_inventory_entries(tuple(entries))
    inventory_summary = build_workflow_artifact_inventory_summary(inventory_entries)
    entries.extend(
        _write_inventory_artifacts(
            output_dir=output_dir,
            inventory_entries=inventory_entries,
            inventory_summary=inventory_summary,
            producer_function=producer_function,
        )
    )
    manifest = WorkflowArtifactLayoutManifest(
        producer_function=producer_function,
        artifacts=tuple(entries),
    )
    atomic_write_text(output_dir / "manifest.json", manifest.to_stable_json() + "\n")
    validate_workflow_artifact_manifest(output_dir)
    return manifest


def load_workflow_artifact_manifest(output_dir: Path) -> WorkflowArtifactLayoutManifest:
    """Load the stable workflow artifact manifest from one output directory."""

    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        raise ScientificEvidenceError(
            f"workflow artifact manifest is missing from {output_dir}"
        )
    return WorkflowArtifactLayoutManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )


def index_workflow_artifact_manifest(
    output_dir: Path | None = None,
    *,
    manifest: WorkflowArtifactLayoutManifest | None = None,
) -> WorkflowArtifactLayoutIndex:
    """Index one workflow artifact manifest by stable ids and paths."""

    if manifest is None:
        if output_dir is None:
            raise ValueError("output_dir is required when manifest is not provided")
        manifest = load_workflow_artifact_manifest(output_dir)
    artifact_ids: dict[str, int] = {}
    legacy_relative_paths: dict[str, int] = {}
    relative_paths: dict[str, int] = {}
    canonical_relative_paths: dict[str, int] = {}
    for index, artifact in enumerate(manifest.artifacts):
        if artifact.artifact_id in artifact_ids:
            raise InvalidWorkflowError(
                "workflow artifact manifest contains duplicate artifact_id "
                f"{artifact.artifact_id!r}"
            )
        artifact_ids[artifact.artifact_id] = index
        legacy_relative_paths[artifact.legacy_relative_path] = index
        relative_paths[artifact.relative_path] = index
        canonical_relative_paths[artifact.canonical_relative_path] = index
    return WorkflowArtifactLayoutIndex(
        manifest=manifest,
        artifact_ids=artifact_ids,
        legacy_relative_paths=legacy_relative_paths,
        relative_paths=relative_paths,
        canonical_relative_paths=canonical_relative_paths,
    )


def find_workflow_artifact_by_legacy_path(
    artifact_index: WorkflowArtifactLayoutIndex,
    legacy_relative_path: str,
) -> WorkflowArtifactLayoutEntry | None:
    """Return the layout entry for one legacy root-level workflow artifact path."""

    row_index = artifact_index.legacy_relative_paths.get(legacy_relative_path)
    if row_index is None:
        return None
    return artifact_index.manifest.artifacts[row_index]


def find_workflow_artifact_by_id(
    artifact_index: WorkflowArtifactLayoutIndex,
    artifact_id: str,
) -> WorkflowArtifactLayoutEntry | None:
    """Return the layout entry for one stable workflow artifact id."""

    row_index = artifact_index.artifact_ids.get(artifact_id)
    if row_index is None:
        return None
    return artifact_index.manifest.artifacts[row_index]


def validate_workflow_artifact_manifest(output_dir: Path) -> WorkflowArtifactLayoutManifest:
    """Validate manifest-listed workflow artifacts against current on-disk content."""

    manifest = load_workflow_artifact_manifest(output_dir)
    artifact_index = index_workflow_artifact_manifest(manifest=manifest)
    for artifact in manifest.artifacts:
        artifact_path = output_dir / artifact.relative_path
        if not artifact_path.is_file():
            raise ScientificEvidenceError(
                f"workflow artifact manifest lists missing file {artifact.relative_path}"
            )
        actual_kind = _classify_artifact_kind(artifact_path)
        if actual_kind is not artifact.artifact_kind:
            raise InvalidWorkflowError(
                "workflow artifact manifest kind mismatch for "
                f"{artifact.relative_path}: expected {artifact.artifact_kind.value}, "
                f"found {actual_kind.value}"
            )
        if actual_kind is WorkflowArtifactKind.TSV_TABLE:
            _validate_tsv_artifact_schema(
                artifact=artifact,
                artifact_path=artifact_path,
                output_dir=output_dir,
            )
        actual_schema = _infer_artifact_schema(artifact_path, actual_kind)
        if actual_schema != artifact.artifact_schema:
            raise InvalidWorkflowError(
                "workflow artifact manifest schema mismatch for "
                f"{artifact.relative_path}: expected {artifact.artifact_schema!r}, "
                f"found {actual_schema!r}"
            )
        actual_row_count = _count_artifact_rows(artifact_path, actual_kind)
        if actual_row_count != artifact.row_count:
            raise InvalidWorkflowError(
                "workflow artifact manifest row-count mismatch for "
                f"{artifact.relative_path}: expected {artifact.row_count}, "
                f"found {actual_row_count}"
            )
        actual_checksum = _compute_sha256(artifact_path)
        if actual_checksum != artifact.checksum_sha256:
            raise InvalidWorkflowError(
                "workflow artifact manifest checksum mismatch for "
                f"{artifact.relative_path}: expected {artifact.checksum_sha256}, "
                f"found {actual_checksum}"
            )
    validate_workflow_artifact_completeness(
        output_dir=output_dir,
        manifest=manifest,
        artifact_index=artifact_index,
    )
    validate_workflow_artifact_inventory(
        output_dir=output_dir,
        manifest=manifest,
    )
    return manifest


def classify_workflow_artifact_name(filename: str) -> WorkflowArtifactFolder:
    """Resolve one workflow artifact filename into its canonical folder."""

    name = filename.lower()
    stem = name.rsplit(".", 1)[0]
    tokens = set(stem.replace("-", "_").split("_"))

    if "card" in tokens or "cards" in tokens:
        return WorkflowArtifactFolder.CARDS
    if tokens & {
        "matrix",
        "missingness",
        "ratio",
        "ratios",
        "totals",
        "distribution",
        "distributions",
        "transform",
        "transforms",
        "sample",
        "samples",
        "channel",
        "channels",
        "pca",
        "distance",
        "cluster",
        "mappings",
    }:
        return WorkflowArtifactFolder.MATRICES
    if tokens & {
        "qc",
        "validation",
        "interference",
        "coelution",
        "retention",
        "replicate",
        "unreliable",
        "belief",
        "audit",
        "confidence",
        "metadata",
        "assignment",
        "assignments",
        "duplicate",
    }:
        return WorkflowArtifactFolder.QC
    if tokens & {
        "differential",
        "volcano",
        "ranking",
        "enrichment",
        "effect",
        "effects",
        "balance",
    }:
        return WorkflowArtifactFolder.STATS
    if tokens & {
        "evidence",
        "claim",
        "claims",
        "graph",
        "localization",
        "peptide",
        "peptides",
        "site",
        "sites",
        "occupancy",
        "fragment",
        "fragments",
        "transition",
        "transitions",
        "protein",
        "proteins",
    }:
        return WorkflowArtifactFolder.EVIDENCE
    if tokens & {"import", "accepted", "rejected", "rows", "observations", "design"}:
        return WorkflowArtifactFolder.INPUTS
    if tokens & {"summary", "report", "reports", "manifest"}:
        return WorkflowArtifactFolder.REPORTS
    if tokens & {
        "pathway",
        "complex",
        "annotation",
        "context",
        "regulator",
        "mechanism",
        "cohort",
        "tissue",
        "compartment",
        "drug",
        "disease",
        "phenotype",
        "go",
        "ortholog",
        "biological",
    }:
        return WorkflowArtifactFolder.BIOLOGY
    return WorkflowArtifactFolder.REPORTS


def _prepare_managed_directories(output_dir: Path) -> None:
    for folder in WorkflowArtifactFolder:
        folder_path = output_dir / folder.value
        folder_path.mkdir(parents=True, exist_ok=True)
        for entry in folder_path.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()


def _build_layout_entry(
    *,
    canonical_path: Path,
    legacy_relative_path: str,
    canonical_relative_path: str,
    folder: WorkflowArtifactFolder,
    producer_function: str,
) -> WorkflowArtifactLayoutEntry:
    artifact_kind = _classify_artifact_kind(canonical_path)
    output_table_schema = None
    output_table_schema_sidecar_relative_path = None
    if artifact_kind is WorkflowArtifactKind.TSV_TABLE:
        output_table_schema = infer_output_table_schema(
            canonical_path.read_text(encoding="utf-8"),
            table_name=canonical_path.stem,
        )
        output_table_schema_sidecar_relative_path = _write_output_table_schema_sidecar(
            canonical_path=canonical_path,
            output_table_schema=output_table_schema,
        )
    return WorkflowArtifactLayoutEntry(
        artifact_id=build_artifact_id(
            canonical_relative_path,
            folder=folder.value,
            artifact_kind=artifact_kind.value,
        ),
        legacy_relative_path=legacy_relative_path,
        relative_path=canonical_relative_path,
        canonical_relative_path=canonical_relative_path,
        folder=folder,
        artifact_kind=artifact_kind,
        artifact_schema=_infer_artifact_schema(canonical_path, artifact_kind),
        artifact_schema_version=_infer_artifact_schema_version(
            artifact_kind=artifact_kind,
            output_table_schema=output_table_schema,
        ),
        output_table_schema=output_table_schema,
        output_table_schema_sidecar_relative_path=output_table_schema_sidecar_relative_path,
        row_count=_count_artifact_rows(canonical_path, artifact_kind),
        checksum_sha256=_compute_sha256(canonical_path),
        producer_function=producer_function,
    )


def validate_workflow_artifact_completeness(
    *,
    output_dir: Path,
    manifest: WorkflowArtifactLayoutManifest | None = None,
    artifact_index: WorkflowArtifactLayoutIndex | None = None,
) -> WorkflowArtifactLayoutManifest:
    """Validate manifest-declared workflow completeness against on-disk artifacts."""

    if manifest is None:
        manifest = load_workflow_artifact_manifest(output_dir)
    if artifact_index is None:
        artifact_index = index_workflow_artifact_manifest(manifest=manifest)
    for expectation in _collect_workflow_artifact_expectations(
        output_dir=output_dir,
        manifest=manifest,
    ):
        legacy_path = output_dir / expectation.legacy_relative_path
        if not legacy_path.is_file():
            raise ScientificEvidenceError(
                "workflow artifact completeness validation failed for "
                f"{expectation.source_manifest_relative_path}: missing "
                f"{expectation.legacy_relative_path} declared at "
                f"{expectation.manifest_key_path}"
            )
        layout_entry = find_workflow_artifact_by_legacy_path(
            artifact_index,
            expectation.legacy_relative_path,
        )
        if layout_entry is None:
            raise InvalidWorkflowError(
                "workflow artifact completeness validation failed for "
                f"{expectation.source_manifest_relative_path}: "
                f"{expectation.legacy_relative_path} declared at "
                f"{expectation.manifest_key_path} is missing from manifest.json"
            )
        if layout_entry.relative_path != expectation.canonical_relative_path:
            raise InvalidWorkflowError(
                "workflow artifact completeness validation failed for "
                f"{expectation.source_manifest_relative_path}: "
                f"{expectation.legacy_relative_path} declared at "
                f"{expectation.manifest_key_path} must map to "
                f"{expectation.canonical_relative_path}, found {layout_entry.relative_path}"
            )
    return manifest


def build_workflow_artifact_inventory_entries(
    artifacts: tuple[WorkflowArtifactLayoutEntry, ...],
) -> tuple[WorkflowArtifactInventoryEntry, ...]:
    """Build inventory rows over manifest-managed workflow artifacts."""

    return tuple(
        WorkflowArtifactInventoryEntry(
            artifact_id=artifact.artifact_id,
            legacy_relative_path=artifact.legacy_relative_path,
            canonical_relative_path=artifact.canonical_relative_path,
            folder=artifact.folder,
            artifact_kind=artifact.artifact_kind,
            row_count=artifact.row_count,
        )
        for artifact in artifacts
        if artifact.legacy_relative_path
        not in {
            WORKFLOW_ARTIFACT_INVENTORY_NAME,
            WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME,
        }
    )


def build_workflow_artifact_inventory_summary(
    inventory_entries: tuple[WorkflowArtifactInventoryEntry, ...],
) -> WorkflowArtifactInventorySummary:
    """Summarize artifact and TSV row-count coverage for one workflow run."""

    tsv_entries = tuple(
        entry
        for entry in inventory_entries
        if entry.artifact_kind is WorkflowArtifactKind.TSV_TABLE
    )
    return WorkflowArtifactInventorySummary(
        artifact_count=len(inventory_entries),
        tsv_artifact_count=len(tsv_entries),
        total_tsv_row_count=sum(entry.row_count for entry in tsv_entries),
        note=(
            "artifact inventory summarizes produced workflow artifacts together with "
            "their governed TSV row counts"
        ),
    )


def render_workflow_artifact_inventory_tsv(
    inventory_entries: tuple[WorkflowArtifactInventoryEntry, ...],
) -> str:
    """Render one workflow artifact inventory as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "artifact_id",
            "legacy_relative_path",
            "canonical_relative_path",
            "folder",
            "artifact_kind",
            "row_count",
        )
    )
    for entry in inventory_entries:
        writer.writerow(
            (
                entry.artifact_id,
                entry.legacy_relative_path,
                entry.canonical_relative_path,
                entry.folder.value,
                entry.artifact_kind.value,
                entry.row_count,
            )
        )
    return handle.getvalue()


def render_workflow_artifact_inventory_summary_tsv(
    summary: WorkflowArtifactInventorySummary,
) -> str:
    """Render aggregate workflow artifact inventory counts as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("artifact_count", summary.artifact_count),
        ("tsv_artifact_count", summary.tsv_artifact_count),
        ("total_tsv_row_count", summary.total_tsv_row_count),
        ("note", summary.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def validate_workflow_artifact_inventory(
    *,
    output_dir: Path,
    manifest: WorkflowArtifactLayoutManifest | None = None,
) -> None:
    """Validate emitted inventory rows and counts against managed artifacts."""

    if manifest is None:
        manifest = load_workflow_artifact_manifest(output_dir)
    inventory_path = output_dir / WORKFLOW_ARTIFACT_INVENTORY_NAME
    summary_path = output_dir / WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME
    canonical_inventory_path = output_dir / "reports" / WORKFLOW_ARTIFACT_INVENTORY_NAME
    canonical_summary_path = output_dir / "reports" / WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME
    for path in (
        inventory_path,
        summary_path,
        canonical_inventory_path,
        canonical_summary_path,
    ):
        if not path.is_file():
            raise ScientificEvidenceError(
                f"workflow artifact inventory is missing required file {path.name}"
            )
    expected_entries = build_workflow_artifact_inventory_entries(manifest.artifacts)
    expected_by_legacy_path = {
        entry.legacy_relative_path: entry for entry in expected_entries
    }
    observed_rows = tuple(
        csv.DictReader(
            inventory_path.read_text(encoding="utf-8").splitlines(),
            delimiter="\t",
        )
    )
    if len(observed_rows) != len(expected_entries):
        raise InvalidWorkflowError(
            "workflow artifact inventory row-count mismatch: expected "
            f"{len(expected_entries)} rows, found {len(observed_rows)}"
        )
    for row in observed_rows:
        legacy_relative_path = row["legacy_relative_path"]
        expected = expected_by_legacy_path.get(legacy_relative_path)
        if expected is None:
            raise InvalidWorkflowError(
                "workflow artifact inventory lists unexpected artifact "
                f"{legacy_relative_path!r}"
            )
        if row["artifact_id"] != expected.artifact_id:
            raise InvalidWorkflowError(
                "workflow artifact inventory artifact id mismatch for "
                f"{legacy_relative_path}: expected {expected.artifact_id!r}, "
                f"found {row['artifact_id']!r}"
            )
        if row["canonical_relative_path"] != expected.canonical_relative_path:
            raise InvalidWorkflowError(
                "workflow artifact inventory canonical path mismatch for "
                f"{legacy_relative_path}: expected "
                f"{expected.canonical_relative_path!r}, found "
                f"{row['canonical_relative_path']!r}"
            )
        if row["folder"] != expected.folder.value:
            raise InvalidWorkflowError(
                "workflow artifact inventory folder mismatch for "
                f"{legacy_relative_path}: expected {expected.folder.value!r}, "
                f"found {row['folder']!r}"
            )
        if row["artifact_kind"] != expected.artifact_kind.value:
            raise InvalidWorkflowError(
                "workflow artifact inventory kind mismatch for "
                f"{legacy_relative_path}: expected {expected.artifact_kind.value!r}, "
                f"found {row['artifact_kind']!r}"
            )
        observed_row_count = int(row["row_count"])
        if observed_row_count != expected.row_count:
            raise InvalidWorkflowError(
                "workflow artifact inventory row count mismatch for "
                f"{legacy_relative_path}: expected {expected.row_count}, found "
                f"{observed_row_count}"
            )
        if expected.artifact_kind is WorkflowArtifactKind.TSV_TABLE:
            actual_row_count = _count_artifact_rows(
                output_dir / expected.legacy_relative_path,
                WorkflowArtifactKind.TSV_TABLE,
            )
            if actual_row_count != observed_row_count:
                raise InvalidWorkflowError(
                    "workflow artifact inventory does not match actual TSV rows for "
                    f"{legacy_relative_path}: expected {actual_row_count}, found "
                    f"{observed_row_count}"
                )
    expected_summary = build_workflow_artifact_inventory_summary(expected_entries)
    observed_summary = {
        row["field"]: row["value"]
        for row in csv.DictReader(
            summary_path.read_text(encoding="utf-8").splitlines(),
            delimiter="\t",
        )
    }
    if int(observed_summary["artifact_count"]) != expected_summary.artifact_count:
        raise InvalidWorkflowError("workflow artifact inventory summary artifact_count mismatch")
    if int(observed_summary["tsv_artifact_count"]) != expected_summary.tsv_artifact_count:
        raise InvalidWorkflowError("workflow artifact inventory summary tsv_artifact_count mismatch")
    if int(observed_summary["total_tsv_row_count"]) != expected_summary.total_tsv_row_count:
        raise InvalidWorkflowError("workflow artifact inventory summary total_tsv_row_count mismatch")
    if observed_summary["note"] != expected_summary.note:
        raise InvalidWorkflowError("workflow artifact inventory summary note mismatch")
    if inventory_path.read_text(encoding="utf-8") != canonical_inventory_path.read_text(
        encoding="utf-8"
    ):
        raise InvalidWorkflowError(
            "workflow artifact inventory root and canonical copies differ"
        )
    if summary_path.read_text(encoding="utf-8") != canonical_summary_path.read_text(
        encoding="utf-8"
    ):
        raise InvalidWorkflowError(
            "workflow artifact inventory summary root and canonical copies differ"
        )


def _collect_workflow_artifact_expectations(
    *,
    output_dir: Path,
    manifest: WorkflowArtifactLayoutManifest,
) -> tuple[WorkflowArtifactExpectation, ...]:
    expectations: list[WorkflowArtifactExpectation] = []
    for artifact in manifest.artifacts:
        if (
            artifact.artifact_kind is not WorkflowArtifactKind.JSON_DOCUMENT
            or "manifest" not in Path(artifact.legacy_relative_path).stem
        ):
            continue
        payload = json.loads((output_dir / artifact.relative_path).read_text(encoding="utf-8"))
        expectations.extend(
            _collect_manifest_declared_artifacts(
                payload=payload,
                source_manifest_relative_path=artifact.relative_path,
            )
        )
    return tuple(expectations)


def _write_inventory_artifacts(
    *,
    output_dir: Path,
    inventory_entries: tuple[WorkflowArtifactInventoryEntry, ...],
    inventory_summary: WorkflowArtifactInventorySummary,
    producer_function: str,
) -> tuple[WorkflowArtifactLayoutEntry, ...]:
    inventory_text = render_workflow_artifact_inventory_tsv(inventory_entries)
    summary_text = render_workflow_artifact_inventory_summary_tsv(inventory_summary)
    inventory_root_path = output_dir / WORKFLOW_ARTIFACT_INVENTORY_NAME
    summary_root_path = output_dir / WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME
    atomic_write_text(inventory_root_path, inventory_text)
    atomic_write_text(summary_root_path, summary_text)
    inventory_canonical_relative_path = (
        f"{WorkflowArtifactFolder.REPORTS.value}/{WORKFLOW_ARTIFACT_INVENTORY_NAME}"
    )
    summary_canonical_relative_path = (
        f"{WorkflowArtifactFolder.REPORTS.value}/"
        f"{WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME}"
    )
    inventory_canonical_path = output_dir / inventory_canonical_relative_path
    summary_canonical_path = output_dir / summary_canonical_relative_path
    atomic_copy_file(inventory_root_path, inventory_canonical_path)
    atomic_copy_file(summary_root_path, summary_canonical_path)
    return (
        _build_layout_entry(
            canonical_path=inventory_canonical_path,
            legacy_relative_path=WORKFLOW_ARTIFACT_INVENTORY_NAME,
            canonical_relative_path=inventory_canonical_relative_path,
            folder=WorkflowArtifactFolder.REPORTS,
            producer_function=producer_function,
        ),
        _build_layout_entry(
            canonical_path=summary_canonical_path,
            legacy_relative_path=WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME,
            canonical_relative_path=summary_canonical_relative_path,
            folder=WorkflowArtifactFolder.REPORTS,
            producer_function=producer_function,
        ),
    )


def _collect_manifest_declared_artifacts(
    *,
    payload: object,
    source_manifest_relative_path: str,
) -> tuple[WorkflowArtifactExpectation, ...]:
    expectations: list[WorkflowArtifactExpectation] = []

    def visit(node: object, path: str, *, inside_artifacts: bool) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                next_path = f"{path}.{key}"
                visit(
                    value,
                    next_path,
                    inside_artifacts=inside_artifacts or key == "artifacts",
                )
            return
        if isinstance(node, list):
            for index, value in enumerate(node):
                visit(value, f"{path}[{index}]", inside_artifacts=inside_artifacts)
            return
        if not inside_artifacts or not _is_declared_artifact_path(node):
            return
        legacy_relative_path = str(node)
        expectations.append(
            WorkflowArtifactExpectation(
                source_manifest_relative_path=source_manifest_relative_path,
                manifest_key_path=path,
                legacy_relative_path=legacy_relative_path,
                canonical_relative_path=(
                    f"{classify_workflow_artifact_name(legacy_relative_path).value}/"
                    f"{legacy_relative_path}"
                ),
            )
        )

    visit(payload, "manifest", inside_artifacts=False)
    return tuple(expectations)


def _is_declared_artifact_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("/") or "://" in value or "/" in value:
        return False
    return value.endswith((".tsv", ".json", ".html", ".svg", ".txt"))


def _validate_tsv_artifact_schema(
    *,
    artifact: WorkflowArtifactLayoutEntry,
    artifact_path: Path,
    output_dir: Path,
) -> None:
    if artifact.output_table_schema is None:
        raise InvalidWorkflowError(
            "workflow artifact manifest is missing typed table schema for "
            f"{artifact.relative_path}"
        )
    if artifact.artifact_schema_version != artifact.output_table_schema.schema_version:
        raise InvalidWorkflowError(
            "workflow artifact manifest schema-version mismatch for "
            f"{artifact.relative_path}: expected "
            f"{artifact.output_table_schema.schema_version}, found "
            f"{artifact.artifact_schema_version}"
        )
    if artifact.output_table_schema_sidecar_relative_path is None:
        raise InvalidWorkflowError(
            "workflow artifact manifest is missing table-schema sidecar for "
            f"{artifact.relative_path}"
        )
    sidecar_path = output_dir / artifact.output_table_schema_sidecar_relative_path
    if not sidecar_path.is_file():
        raise ScientificEvidenceError(
            "workflow artifact manifest lists missing table-schema sidecar "
            f"{artifact.output_table_schema_sidecar_relative_path}"
        )
    sidecar_schema = OutputTableSchema.model_validate_json(
        sidecar_path.read_text(encoding="utf-8")
    )
    if sidecar_schema != artifact.output_table_schema:
        raise InvalidWorkflowError(
            "workflow artifact manifest table-schema sidecar mismatch for "
            f"{artifact.relative_path}"
        )
    validation_report = validate_output_table_text(
        artifact_path.read_text(encoding="utf-8"),
        schema=artifact.output_table_schema,
    )
    if validation_report.valid:
        return
    first_issue = validation_report.issues[0]
    raise InvalidWorkflowError(
        "workflow artifact manifest table-schema mismatch for "
        f"{artifact.relative_path}: {first_issue.message}"
    )


def _write_output_table_schema_sidecar(
    *,
    canonical_path: Path,
    output_table_schema: OutputTableSchema,
) -> str:
    sidecar_path = canonical_path.with_name(f"{canonical_path.name}.schema.json")
    atomic_write_text(sidecar_path, output_table_schema.to_stable_json() + "\n")
    return sidecar_path.relative_to(canonical_path.parents[1]).as_posix()


def _infer_artifact_schema_version(
    *,
    artifact_kind: WorkflowArtifactKind,
    output_table_schema: OutputTableSchema | None,
) -> str:
    if artifact_kind is WorkflowArtifactKind.TSV_TABLE and output_table_schema is not None:
        return output_table_schema.schema_version
    return WorkflowArtifactLayoutManifest.model_fields["manifest_schema_version"].default


def _classify_artifact_kind(path: Path) -> WorkflowArtifactKind:
    suffix = path.suffix.lower()
    if suffix == ".tsv":
        return WorkflowArtifactKind.TSV_TABLE
    if suffix == ".json":
        return WorkflowArtifactKind.JSON_DOCUMENT
    return WorkflowArtifactKind.TEXT_DOCUMENT


def _infer_artifact_schema(path: Path, artifact_kind: WorkflowArtifactKind) -> str:
    if artifact_kind is WorkflowArtifactKind.TSV_TABLE:
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines:
            return "tsv[]"
        columns = tuple(lines[0].split("\t"))
        return f"tsv[{','.join(columns)}]"
    if artifact_kind is WorkflowArtifactKind.JSON_DOCUMENT:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return "json[list]"
        if isinstance(payload, dict):
            return "json[object]"
        return "json[scalar]"
    suffix = path.suffix.lower().lstrip(".") or "text"
    return f"text[{suffix}]"


def _count_artifact_rows(path: Path, artifact_kind: WorkflowArtifactKind) -> int:
    if artifact_kind is WorkflowArtifactKind.TSV_TABLE:
        lines = path.read_text(encoding="utf-8").splitlines()
        return 0 if not lines else len(lines) - 1
    if artifact_kind is WorkflowArtifactKind.JSON_DOCUMENT:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return len(payload)
        return 1
    return len([line for line in path.read_text(encoding="utf-8").splitlines() if line])


def _compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "WorkflowArtifactFolder",
    "WorkflowArtifactInventoryEntry",
    "WorkflowArtifactInventorySummary",
    "WorkflowArtifactKind",
    "WorkflowArtifactExpectation",
    "WorkflowArtifactLayoutEntry",
    "WorkflowArtifactLayoutIndex",
    "WorkflowArtifactLayoutManifest",
    "WORKFLOW_ARTIFACT_INVENTORY_NAME",
    "WORKFLOW_ARTIFACT_INVENTORY_SUMMARY_NAME",
    "build_workflow_artifact_inventory_entries",
    "build_workflow_artifact_inventory_summary",
    "classify_workflow_artifact_name",
    "find_workflow_artifact_by_id",
    "find_workflow_artifact_by_legacy_path",
    "index_workflow_artifact_manifest",
    "load_workflow_artifact_manifest",
    "render_workflow_artifact_inventory_summary_tsv",
    "render_workflow_artifact_inventory_tsv",
    "synchronize_workflow_artifact_layout",
    "validate_workflow_artifact_inventory",
    "validate_workflow_artifact_completeness",
    "validate_workflow_artifact_manifest",
]
