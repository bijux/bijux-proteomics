# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable on-disk layout for workflow-owned result directories."""

from __future__ import annotations

import shutil
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

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


class WorkflowArtifactLayoutEntry(JsonModel):
    """One canonical artifact placement inside a workflow output directory."""

    model_config = ConfigDict(extra="forbid")

    legacy_relative_path: str = Field(..., min_length=1)
    canonical_relative_path: str = Field(..., min_length=1)
    folder: WorkflowArtifactFolder


class WorkflowArtifactLayoutManifest(JsonModel):
    """Stable machine-readable layout description over one workflow directory."""

    model_config = ConfigDict(extra="forbid")

    layout_name: str = "workflow_artifact_layout"
    folder_names: tuple[str, ...] = Field(
        default_factory=lambda: tuple(folder.value for folder in WorkflowArtifactFolder)
    )
    artifacts: tuple[WorkflowArtifactLayoutEntry, ...] = Field(default_factory=tuple)


def synchronize_workflow_artifact_layout(
    output_dir: Path,
) -> WorkflowArtifactLayoutManifest:
    """Populate canonical workflow folders from flat compatibility artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    _prepare_managed_directories(output_dir)
    entries: list[WorkflowArtifactLayoutEntry] = []
    for path in sorted(output_dir.iterdir(), key=lambda entry: entry.name):
        if not path.is_file() or path.name == "manifest.json":
            continue
        folder = classify_workflow_artifact_name(path.name)
        canonical_relative_path = f"{folder.value}/{path.name}"
        shutil.copyfile(path, output_dir / canonical_relative_path)
        entries.append(
            WorkflowArtifactLayoutEntry(
                legacy_relative_path=path.name,
                canonical_relative_path=canonical_relative_path,
                folder=folder,
            )
        )
    manifest = WorkflowArtifactLayoutManifest(artifacts=tuple(entries))
    (output_dir / "manifest.json").write_text(
        manifest.to_stable_json() + "\n",
        encoding="utf-8",
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


__all__ = [
    "WorkflowArtifactFolder",
    "WorkflowArtifactLayoutEntry",
    "WorkflowArtifactLayoutManifest",
    "classify_workflow_artifact_name",
    "synchronize_workflow_artifact_layout",
]
