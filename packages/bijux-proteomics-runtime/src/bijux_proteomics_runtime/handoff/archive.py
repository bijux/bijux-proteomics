# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Portable collaborator handoff archives over completed runtime runs."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.review import (
    BeliefAuditReport,
    build_belief_audit_report_from_artifacts,
)
from bijux_proteomics.workflow import (
    InteractiveResultCard,
    InteractiveResultQcEntry,
    ProteomicsEvidenceGraph,
    ProteomicsStudyConclusionEntry,
    ProteomicsStudyMatrixSurface,
    ProteomicsStudyResult,
    ResultManifestInputKind,
    ResultManifestReport,
    ResultManifestSourceKind,
)
from bijux_proteomics_foundation import JsonModel, hash_payload
from bijux_proteomics_runtime.rehydrate import load_completed_run


class CollaboratorHandoffArchiveSummary(JsonModel):
    """Compact counts and integrity posture for one collaborator handoff archive."""

    model_config = ConfigDict(extra="forbid")

    matrix_surface_count: int = Field(..., ge=0)
    card_count: int = Field(..., ge=0)
    qc_packet_count: int = Field(..., ge=0)
    claim_count: int = Field(..., ge=0)
    belief_audit_entry_count: int = Field(..., ge=0)
    archive_sha256: str = Field(..., min_length=64, max_length=64)


class CollaboratorHandoffArchive(JsonModel):
    """Self-contained collaborator handoff archive that stays queryable offline."""

    model_config = ConfigDict(extra="forbid")

    source_run_dir: str = Field(..., min_length=1)
    result: ProteomicsStudyResult
    graph: ProteomicsEvidenceGraph
    matrices: tuple[ProteomicsStudyMatrixSurface, ...] = Field(default_factory=tuple)
    cards: tuple[InteractiveResultCard, ...] = Field(default_factory=tuple)
    qc_packets: tuple[InteractiveResultQcEntry, ...] = Field(default_factory=tuple)
    claims: tuple[ProteomicsStudyConclusionEntry, ...] = Field(default_factory=tuple)
    belief_audit: BeliefAuditReport
    manifest: ResultManifestReport
    summary: CollaboratorHandoffArchiveSummary
    note: str = Field(..., min_length=1)

    def query_archived_protein(
        self,
        *,
        object_id: str | None = None,
        representative_protein_ref: str | None = None,
    ):
        """Query one archived protein from the embedded result object."""

        return self.result.query_archived_protein(
            object_id=object_id,
            representative_protein_ref=representative_protein_ref,
        )

    def query_archived_pathway(self, *, pathway_id: str):
        """Query one archived pathway from the embedded result object."""

        return self.result.query_archived_pathway(pathway_id=pathway_id)


def build_handoff_archive(
    run_dir: Path, out_archive: Path
) -> CollaboratorHandoffArchive:
    """Persist a self-contained collaborator handoff archive for one completed run."""

    result = load_completed_run(run_dir)
    if result.archive_manifest is None:
        raise ValueError("completed run is missing an archived result manifest")
    if result.archived_evidence_graph is None:
        raise ValueError("completed run is missing an archived evidence graph")
    if result.interactive_result_bundle is None:
        raise ValueError("completed run is missing an interactive result bundle")

    manifest = result.archive_manifest
    manifest_path = _resolve_completed_run_manifest(run_dir)
    belief_audit = build_belief_audit_report_from_artifacts(
        biological_report_dir=_resolve_source_report_dir(
            manifest=manifest,
            manifest_path=manifest_path,
            source_kind=ResultManifestSourceKind.BIOLOGICAL_REPORT,
        ),
        ptm_report_dir=_resolve_source_report_dir(
            manifest=manifest,
            manifest_path=manifest_path,
            source_kind=ResultManifestSourceKind.PTM_REPORT,
        ),
        run_qc_assessment_tsv_paths=_resolve_run_qc_paths(
            manifest=manifest,
            manifest_path=manifest_path,
        ),
    )

    archive = CollaboratorHandoffArchive(
        source_run_dir=str(run_dir),
        result=result,
        graph=result.archived_evidence_graph,
        matrices=result.matrix_surfaces,
        cards=result.interactive_result_bundle.cards,
        qc_packets=result.interactive_result_bundle.qc_entries,
        claims=result.biological_conclusions,
        belief_audit=belief_audit,
        manifest=manifest,
        summary=CollaboratorHandoffArchiveSummary(
            matrix_surface_count=len(result.matrix_surfaces),
            card_count=len(result.interactive_result_bundle.cards),
            qc_packet_count=len(result.interactive_result_bundle.qc_entries),
            claim_count=len(result.biological_conclusions),
            belief_audit_entry_count=len(belief_audit.entries),
            archive_sha256="0" * 64,
        ),
        note=(
            "collaborator handoff archives preserve the rehydrated result object, "
            "graph, matrices, cards, QC packets, claims, belief audit, and "
            "manifest in one self-contained portable review surface"
        ),
    )
    archive_sha256 = _archive_sha256(archive)
    archive = archive.model_copy(
        update={
            "summary": archive.summary.model_copy(
                update={"archive_sha256": archive_sha256}
            )
        }
    )
    out_archive.parent.mkdir(parents=True, exist_ok=True)
    out_archive.write_text(archive.to_stable_json() + "\n", encoding="utf-8")
    return archive


def load_handoff_archive(path: Path) -> CollaboratorHandoffArchive:
    """Load and verify one collaborator handoff archive from disk."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    archive = CollaboratorHandoffArchive.from_dict(payload)
    expected_sha256 = _archive_sha256(archive)
    if archive.summary.archive_sha256 != expected_sha256:
        raise ValueError("handoff archive sha256 does not match embedded content")
    return archive


def _resolve_completed_run_manifest(run_dir: Path) -> Path:
    candidates = (
        run_dir / "result_manifest.json",
        run_dir / "archive" / "result_manifest.json",
        run_dir / "artifacts" / "result_manifest.json",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise ValueError(
        "completed run handoff archiving requires result_manifest.json in the run "
        "directory root, archive/, or artifacts/"
    )


def _resolve_source_report_dir(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
    source_kind: ResultManifestSourceKind,
) -> Path | None:
    for entry in manifest.source_reports:
        if entry.source_kind is source_kind:
            return _resolve_archived_path(manifest_path.parent, entry.report_dir)
    return None


def _resolve_run_qc_paths(
    *,
    manifest: ResultManifestReport,
    manifest_path: Path,
) -> tuple[Path, ...]:
    return tuple(
        _resolve_archived_path(manifest_path.parent, entry.path)
        for entry in manifest.inputs
        if entry.input_kind is ResultManifestInputKind.RUN_QC_ASSESSMENT
    )


def _resolve_archived_path(base_dir: Path, archived_path: str) -> Path:
    candidate = Path(archived_path)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def _archive_sha256(archive: CollaboratorHandoffArchive) -> str:
    payload = archive.to_dict()
    payload["summary"]["archive_sha256"] = ""
    return hash_payload(payload)


__all__ = [
    "CollaboratorHandoffArchive",
    "CollaboratorHandoffArchiveSummary",
    "build_handoff_archive",
    "load_handoff_archive",
]
