# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned import provenance for external proteomics outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runtime.context import RunContextContract
from bijux_proteomics_runtime.runtime.control.integrity import (
    require_reusable_artifact_bundle,
)
from bijux_proteomics_runtime.runtime.control.ledger import RuntimeArtifactLedger
from bijux_proteomics_runtime.runtime.control.replay import ReplayContract
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace, write_json_atomic


class ImportedArtifactRecord(JsonModel):
    """Artifact brought into runtime from an external engine."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=1)
    provenance_role: str = Field(default="imported_evidence", min_length=1)


class DerivedArtifactRecord(JsonModel):
    """Artifact produced by runtime from imported evidence."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=1)
    derivation_role: str = Field(..., min_length=1)


class RuntimeImportTrace(JsonModel):
    """Explicit trace that separates imported and derived runtime outputs."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    external_engine_name: str = Field(..., min_length=1)
    external_engine_version: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    imported_artifacts: tuple[ImportedArtifactRecord, ...] = Field(default_factory=tuple)
    derived_artifacts: tuple[DerivedArtifactRecord, ...] = Field(default_factory=tuple)


class ImportRunBundle(JsonModel):
    """Reviewable runtime bundle for one import-only run."""

    model_config = ConfigDict(extra="forbid")

    run_context: RunContextContract
    replay_contract: ReplayContract
    import_trace: RuntimeImportTrace
    artifact_ledger: RuntimeArtifactLedger
    run_summary: dict[str, Any] = Field(default_factory=dict)
    failure_report: dict[str, Any] | None = Field(default=None)


def write_import_documents(
    workspace: RunWorkspace,
    *,
    engine_name: str,
    engine_version: str,
    source_path: Path,
    imported_payload: dict[str, Any],
) -> tuple[Path, Path, Path]:
    """Write imported evidence and review-facing documents for one run."""
    imported_path = workspace.artifact_items_dir / "imported_evidence.json"
    evidence_bundle_path = workspace.artifact_items_dir / "evidence_bundle.json"
    review_packet_path = workspace.artifact_items_dir / "review_packet.json"
    write_json_atomic(
        imported_path,
        {
            "kind": "runtime-imported-evidence",
            "engine_name": engine_name,
            "engine_version": engine_version,
            "source_path": str(source_path),
            "payload": imported_payload,
        },
    )
    write_json_atomic(
        evidence_bundle_path,
        {
            "kind": "runtime-evidence-bundle",
            "engine_name": engine_name,
            "engine_version": engine_version,
            "source_path": str(source_path),
            "imported_artifact_kind": "runtime-imported-evidence",
            "summary": "runtime imported external evidence without claiming new scientific derivation",
        },
    )
    write_json_atomic(
        review_packet_path,
        {
            "kind": "runtime-review-packet",
            "engine_name": engine_name,
            "engine_version": engine_version,
            "source_path": str(source_path),
            "recommendation": "review_imported_evidence",
            "note": "runtime preserved external-engine provenance and separated imported evidence from runtime-derived review outputs",
        },
    )
    return imported_path, evidence_bundle_path, review_packet_path


def build_import_trace(
    *,
    workspace: RunWorkspace,
    run_id: str,
    engine_name: str,
    engine_version: str,
    source_path: Path,
    imported_artifact_path: Path,
    derived_paths: tuple[Path, ...],
) -> RuntimeImportTrace:
    """Build an explicit import trace for one import-only run."""
    return RuntimeImportTrace(
        run_id=run_id,
        external_engine_name=engine_name,
        external_engine_version=engine_version,
        source_path=str(source_path),
        imported_artifacts=(
            ImportedArtifactRecord(
                artifact_kind="runtime-imported-evidence",
                path=str(imported_artifact_path),
                sha256=_sha256(imported_artifact_path),
            ),
        ),
        derived_artifacts=tuple(
            DerivedArtifactRecord(
                artifact_kind=_artifact_kind_for_path(path, workspace),
                path=str(path),
                sha256=_sha256(path),
                derivation_role="runtime_review_output",
            )
            for path in derived_paths
        ),
    )


def build_import_run_bundle(
    *,
    run_context: RunContextContract,
    replay_contract: ReplayContract,
    import_trace: RuntimeImportTrace,
    artifact_ledger: RuntimeArtifactLedger,
    run_summary: dict[str, Any],
    failure_report: dict[str, Any] | None = None,
) -> ImportRunBundle:
    """Build a runtime bundle for one import-only run."""
    return ImportRunBundle(
        run_context=run_context,
        replay_contract=replay_contract,
        import_trace=import_trace,
        artifact_ledger=artifact_ledger,
        run_summary=run_summary,
        failure_report=failure_report,
    )


def write_import_trace(workspace: RunWorkspace, trace: RuntimeImportTrace) -> None:
    """Persist one import trace."""
    write_json_atomic(workspace.import_trace_path, trace.to_dict())


def write_import_run_bundle(workspace: RunWorkspace, bundle: ImportRunBundle) -> None:
    """Persist one import-only run bundle."""
    write_json_atomic(workspace.import_run_bundle_path, bundle.to_dict())


def load_import_trace(workspace: RunWorkspace) -> RuntimeImportTrace:
    """Load one persisted import trace."""
    return RuntimeImportTrace.load_json(workspace.import_trace_path)


def load_import_run_bundle(workspace: RunWorkspace) -> ImportRunBundle:
    """Load one persisted import-only run bundle."""
    require_reusable_artifact_bundle(
        workspace,
        run_id=workspace.run_id,
        max_artifact_bytes=1_000_000,
        required_artifact_kinds=(
            "runtime-import-run-bundle",
            "runtime-import-trace",
            "runtime-replay-contract",
        ),
    )
    return ImportRunBundle.load_json(workspace.import_run_bundle_path)


def _artifact_kind_for_path(path: Path, workspace: RunWorkspace) -> str:
    if path == workspace.run_summary_path:
        return "runtime-status"
    if path == workspace.run_context_path:
        return "runtime-run-context"
    if path == workspace.replay_contract_path:
        return "runtime-replay-contract"
    if path == workspace.import_run_bundle_path:
        return "runtime-import-run-bundle"
    if path == workspace.artifact_items_dir / "evidence_bundle.json":
        return "runtime-evidence-bundle"
    if path == workspace.artifact_items_dir / "review_packet.json":
        return "runtime-review-packet"
    return "runtime-derived-artifact"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


__all__ = [
    "DerivedArtifactRecord",
    "ImportRunBundle",
    "ImportedArtifactRecord",
    "RuntimeImportTrace",
    "build_import_run_bundle",
    "build_import_trace",
    "load_import_run_bundle",
    "load_import_trace",
    "write_import_documents",
    "write_import_run_bundle",
    "write_import_trace",
]
