# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Runtime API catalog helpers for stable review-facing contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_proteomics_runtime.api.v1.schema import (
    ArtifactLookupResponse,
    EvidenceLookupResponse,
    RunArtifactsResponse,
    RunEvidenceResponse,
    RunHistoryResponse,
    RunReviewResponse,
    RuntimeHealthComponent,
    RuntimeHealthComponentState,
    RuntimeHealthResponse,
    RuntimeArtifactRecord,
    RuntimeDocumentAvailability,
    RuntimeDocumentReference,
    RuntimeStatusResponse,
    RunResponse,
)
from bijux_proteomics_runtime.providers import provider_metadata
from bijux_proteomics_runtime.providers.factory import provider_requirements
from bijux_proteomics_runtime.runtime_identity import runtime_banner
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace

_DOCUMENT_MAX_INLINE_BYTES = 256_000
_MAX_ARTIFACT_LOAD_BYTES = 1_000_000

_TOP_LEVEL_ARTIFACTS: tuple[tuple[str, str, str], ...] = (
    ("config", "runtime-config", "runtime configuration"),
    ("plan", "runtime-plan", "runtime execution plan"),
    ("state", "runtime-state", "runtime state snapshot"),
    ("report", "runtime-report", "runtime report bundle"),
    ("telemetry", "runtime-telemetry", "runtime telemetry summary"),
    ("analysis", "runtime-analysis", "runtime analysis summary"),
    ("execution", "runtime-execution", "runtime execution summary"),
    ("timings", "runtime-timings", "runtime timing summary"),
    ("run_summary", "runtime-status", "runtime run summary"),
    ("run_output", "runtime-output", "runtime raw run output"),
    ("error", "runtime-error", "runtime failure payload"),
    ("lifecycle", "runtime-lifecycle", "runtime lifecycle transitions"),
    (
        "execution_snapshots",
        "runtime-execution-snapshots",
        "runtime execution snapshots",
    ),
    (
        "telemetry_snapshots",
        "runtime-telemetry-snapshots",
        "runtime telemetry snapshots",
    ),
    ("human_decision", "runtime-human-decision", "human decision payload"),
    (
        "candidate_selection",
        "runtime-candidate-selection",
        "candidate selection payload",
    ),
)

_RUNTIME_API_CONTRACT_FILES: tuple[str, ...] = (
    "apis/bijux-proteomics-runtime/v1/schema.yaml",
    "apis/bijux-proteomics-runtime/v1/pinned_openapi.json",
    "apis/bijux-proteomics-runtime/v1/schema.hash",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _component(
    name: str,
    state: RuntimeHealthComponentState,
    detail: str,
    remediation_hint: str,
) -> RuntimeHealthComponent:
    return RuntimeHealthComponent(
        component=name,
        state=state,
        detail=detail,
        remediation_hint=remediation_hint,
    )


def _bounded_inline_limit(max_inline_bytes: int) -> int:
    if max_inline_bytes < 1:
        raise ValueError("max_inline_bytes must be >= 1")
    if max_inline_bytes > _MAX_ARTIFACT_LOAD_BYTES:
        raise ValueError(
            f"max_inline_bytes exceeds the guarded limit of {_MAX_ARTIFACT_LOAD_BYTES}"
        )
    return max_inline_bytes


def _load_run_summary_payload(
    base_dir: Path,
    run_id: str,
    artifacts_dir: Path | None,
) -> dict[str, Any]:
    workspace = RunWorkspace.for_run(
        base_dir,
        run_id,
        artifacts_root_override=artifacts_dir,
    )
    payload = json.loads(workspace.run_summary_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _iter_run_ids(base_dir: Path) -> list[str]:
    artifacts_root = base_dir / "artifacts"
    if not artifacts_root.exists():
        return []
    run_ids: list[str] = []
    for path in sorted(artifacts_root.iterdir()):
        if not path.is_dir():
            continue
        if (path / "run_summary.json").exists():
            run_ids.append(path.name)
    return run_ids


def _artifact_record(
    *,
    run_id: str,
    artifact_key: str,
    artifact_kind: str,
    path: Path,
    tags: list[str] | None = None,
    description: str,
) -> RuntimeArtifactRecord:
    return RuntimeArtifactRecord(
        run_id=run_id,
        artifact_key=artifact_key,
        artifact_kind=artifact_kind,
        path=str(path),
        size_bytes=path.stat().st_size,
        sha256=_sha256(path),
        tags=sorted(tags or []),
        description=description,
    )


def _document_reference(
    *,
    run_id: str,
    document_kind: str,
    path: Path,
    requested: bool,
    supported: bool,
    max_inline_bytes: int = _DOCUMENT_MAX_INLINE_BYTES,
) -> RuntimeDocumentReference:
    max_inline_bytes = _bounded_inline_limit(max_inline_bytes)
    if not supported:
        return RuntimeDocumentReference(
            run_id=run_id,
            document_kind=document_kind,
            availability=RuntimeDocumentAvailability.UNSUPPORTED,
            path=str(path),
            guard_limit_bytes=max_inline_bytes,
            note="runtime does not currently generate this document kind for the run",
        )
    if not path.exists():
        return RuntimeDocumentReference(
            run_id=run_id,
            document_kind=document_kind,
            availability=RuntimeDocumentAvailability.MISSING,
            path=str(path),
            guard_limit_bytes=max_inline_bytes,
            note="document path is defined but no file is present for this run",
        )
    size_bytes = path.stat().st_size
    sha256 = _sha256(path)
    if size_bytes > max_inline_bytes:
        return RuntimeDocumentReference(
            run_id=run_id,
            document_kind=document_kind,
            availability=RuntimeDocumentAvailability.TOO_LARGE,
            path=str(path),
            size_bytes=size_bytes,
            guard_limit_bytes=max_inline_bytes,
            sha256=sha256,
            note="document exists but exceeds the inline-load guard",
        )
    content: dict[str, Any] | None = None
    if requested:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        content = loaded if isinstance(loaded, dict) else {"items": loaded}
    return RuntimeDocumentReference(
        run_id=run_id,
        document_kind=document_kind,
        availability=RuntimeDocumentAvailability.AVAILABLE,
        path=str(path),
        size_bytes=size_bytes,
        guard_limit_bytes=max_inline_bytes,
        sha256=sha256,
        note="document is available for review",
        content=content,
    )


def build_runtime_status_response(
    base_dir: Path,
    run_id: str,
    *,
    artifacts_dir: Path | None = None,
    include_documents: bool = False,
    max_inline_bytes: int = _DOCUMENT_MAX_INLINE_BYTES,
) -> RuntimeStatusResponse:
    """Build the stable runtime status surface for one run."""
    summary = RunResponse.model_validate(
        _load_run_summary_payload(base_dir, run_id, artifacts_dir)
    )
    workspace = RunWorkspace.for_run(base_dir, run_id, artifacts_root_override=artifacts_dir)
    evidence_path = workspace.artifact_items_dir / "evidence_bundle.json"
    review_path = workspace.artifact_items_dir / "review_packet.json"
    return RuntimeStatusResponse(
        summary=summary,
        evidence_bundle=_document_reference(
            run_id=run_id,
            document_kind="evidence_bundle",
            path=evidence_path,
            requested=include_documents,
            supported=True,
            max_inline_bytes=max_inline_bytes,
        ),
        review_packet=_document_reference(
            run_id=run_id,
            document_kind="review_packet",
            path=review_path,
            requested=include_documents,
            supported=True,
            max_inline_bytes=max_inline_bytes,
        ),
    )


def build_run_artifacts_response(
    base_dir: Path,
    run_id: str,
    *,
    artifacts_dir: Path | None = None,
) -> RunArtifactsResponse:
    """Build the stable artifact inventory for one run."""
    workspace = RunWorkspace.for_run(base_dir, run_id, artifacts_root_override=artifacts_dir)
    if not workspace.run_dir.exists():
        raise FileNotFoundError(f"Run not found at {workspace.run_dir}")
    artifacts: list[RuntimeArtifactRecord] = []
    for key, kind, description in _TOP_LEVEL_ARTIFACTS:
        path = getattr(workspace, f"{key}_path")
        if path.exists():
            artifacts.append(
                _artifact_record(
                    run_id=run_id,
                    artifact_key=key,
                    artifact_kind=kind,
                    path=path,
                    tags=["top-level", "runtime"],
                    description=description,
                )
            )
    for artifact_path in sorted(workspace.artifact_items_dir.glob("*.json")):
        tags: list[str] = ["artifact-item", "runtime"]
        artifact_kind = "runtime-artifact-item"
        description = "runtime artifact item"
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            artifact_kind = str(payload.get("kind") or artifact_kind)
            payload_tags = payload.get("tags")
            if isinstance(payload_tags, list):
                tags.extend(str(tag) for tag in payload_tags)
            payload_description = payload.get("description")
            if isinstance(payload_description, str) and payload_description:
                description = payload_description
        artifacts.append(
            _artifact_record(
                run_id=run_id,
                artifact_key=artifact_path.stem,
                artifact_kind=artifact_kind,
                path=artifact_path,
                tags=tags,
                description=description,
            )
        )
    return RunArtifactsResponse(run_id=run_id, artifacts=artifacts)


def build_run_evidence_response(
    base_dir: Path,
    run_id: str,
    *,
    artifacts_dir: Path | None = None,
    include_document: bool = False,
    max_inline_bytes: int = _DOCUMENT_MAX_INLINE_BYTES,
) -> RunEvidenceResponse:
    """Build the stable evidence-bundle surface for one run."""
    workspace = RunWorkspace.for_run(base_dir, run_id, artifacts_root_override=artifacts_dir)
    path = workspace.artifact_items_dir / "evidence_bundle.json"
    return RunEvidenceResponse(
        run_id=run_id,
        evidence_bundle=_document_reference(
            run_id=run_id,
            document_kind="evidence_bundle",
            path=path,
            requested=include_document,
            supported=True,
            max_inline_bytes=max_inline_bytes,
        ),
    )


def build_run_review_response(
    base_dir: Path,
    run_id: str,
    *,
    artifacts_dir: Path | None = None,
    include_document: bool = False,
    max_inline_bytes: int = _DOCUMENT_MAX_INLINE_BYTES,
) -> RunReviewResponse:
    """Build the stable review-packet surface for one run."""
    workspace = RunWorkspace.for_run(base_dir, run_id, artifacts_root_override=artifacts_dir)
    path = workspace.artifact_items_dir / "review_packet.json"
    return RunReviewResponse(
        run_id=run_id,
        review_packet=_document_reference(
            run_id=run_id,
            document_kind="review_packet",
            path=path,
            requested=include_document,
            supported=True,
            max_inline_bytes=max_inline_bytes,
        ),
    )


def build_runtime_health_response(base_dir: Path) -> RuntimeHealthResponse:
    """Build a typed runtime health report for operator diagnostics."""
    artifacts_root = base_dir / "artifacts"
    cache_root = artifacts_root / "cache"
    components: list[RuntimeHealthComponent] = []

    if base_dir.exists() and artifacts_root.parent.exists():
        components.append(
            _component(
                "storage",
                RuntimeHealthComponentState.HEALTHY,
                f"runtime base directory is present at {base_dir}",
                "ensure the runtime base directory stays readable and writable",
            )
        )
    else:
        components.append(
            _component(
                "storage",
                RuntimeHealthComponentState.FAILED,
                f"runtime base directory is missing at {base_dir}",
                "start the runtime from a valid workspace or restore the storage root",
            )
        )

    if cache_root.exists() and cache_root.is_dir():
        components.append(
            _component(
                "cache",
                RuntimeHealthComponentState.HEALTHY,
                f"runtime cache root is available at {cache_root}",
                "keep the cache directory writable for future reuse surfaces",
            )
        )
    else:
        components.append(
            _component(
                "cache",
                RuntimeHealthComponentState.DEGRADED,
                f"runtime cache root is not provisioned at {cache_root}",
                "create artifacts/cache when cache-backed runtime reuse is required",
            )
        )

    try:
        providers = tuple(provider_metadata())
        for name in providers:
            provider_requirements(name)
        components.append(
            _component(
                "tooling",
                RuntimeHealthComponentState.HEALTHY,
                f"provider metadata resolved for {len(providers)} providers",
                "keep provider metadata and requirement probes importable",
            )
        )
    except Exception as exc:  # noqa: BLE001
        components.append(
            _component(
                "tooling",
                RuntimeHealthComponentState.FAILED,
                f"provider requirement probing failed: {exc}",
                "repair provider configuration or dependency imports before execution",
            )
        )

    missing_contracts = [
        rel_path
        for rel_path in _RUNTIME_API_CONTRACT_FILES
        if not (base_dir / rel_path).exists()
    ]
    if missing_contracts:
        components.append(
            _component(
                "manifest",
                RuntimeHealthComponentState.FAILED,
                "runtime API contract files are missing",
                f"restore the checked-in API contracts: {', '.join(missing_contracts)}",
            )
        )
    else:
        components.append(
            _component(
                "manifest",
                RuntimeHealthComponentState.HEALTHY,
                "runtime API contract files are present",
                "keep schema, pinned_openapi, and schema.hash synchronized",
            )
        )

    status = "ok"
    states = {component.state for component in components}
    if RuntimeHealthComponentState.FAILED in states:
        status = "failed"
    elif RuntimeHealthComponentState.DEGRADED in states:
        status = "degraded"

    return RuntimeHealthResponse(
        status=status,
        runtime=runtime_banner(),
        components=components,
    )


def build_run_history_response(
    base_dir: Path,
    *,
    provider: str | None = None,
    workflow_state: str | None = None,
    outcome: str | None = None,
    candidate_id: str | None = None,
) -> RunHistoryResponse:
    """Build the stable run-history lookup response."""
    runs: list[RunResponse] = []
    for run_id in _iter_run_ids(base_dir):
        response = RunResponse.model_validate(
            _load_run_summary_payload(base_dir, run_id, None)
        )
        if provider is not None and response.provider != provider:
            continue
        if workflow_state is not None and response.workflow_state.value != workflow_state:
            continue
        if outcome is not None and response.outcome.value != outcome:
            continue
        if candidate_id is not None and response.candidate_id != candidate_id:
            continue
        runs.append(response)
    return RunHistoryResponse(runs=runs)


def build_artifact_lookup_response(
    base_dir: Path,
    *,
    run_id: str | None = None,
    artifact_kind: str | None = None,
) -> ArtifactLookupResponse:
    """Build the stable artifact-lookup response across runs."""
    records: list[RuntimeArtifactRecord] = []
    run_ids = [run_id] if run_id is not None else _iter_run_ids(base_dir)
    for current_run_id in run_ids:
        for artifact in build_run_artifacts_response(base_dir, current_run_id).artifacts:
            if artifact_kind is not None and artifact.artifact_kind != artifact_kind:
                continue
            records.append(artifact)
    return ArtifactLookupResponse(artifacts=records)


def build_evidence_lookup_response(
    base_dir: Path,
    *,
    run_id: str | None = None,
    document_kind: str | None = None,
    availability: str | None = None,
) -> EvidenceLookupResponse:
    """Build the stable evidence and review lookup response across runs."""
    documents: list[RuntimeDocumentReference] = []
    run_ids = [run_id] if run_id is not None else _iter_run_ids(base_dir)
    for current_run_id in run_ids:
        candidates = [
            build_run_evidence_response(base_dir, current_run_id).evidence_bundle,
            build_run_review_response(base_dir, current_run_id).review_packet,
        ]
        for document in candidates:
            if document_kind is not None and document.document_kind != document_kind:
                continue
            if availability is not None and document.availability.value != availability:
                continue
            documents.append(document)
    return EvidenceLookupResponse(documents=documents)
