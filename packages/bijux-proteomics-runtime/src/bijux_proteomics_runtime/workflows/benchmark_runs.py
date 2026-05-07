# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned flagship benchmark package catalog and execution wrappers."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runs.contracts import RunContextContract
from bijux_proteomics_runtime.runs.ledger import RuntimeArtifactLedger
from bijux_proteomics_runtime.runs.recovery import (
    RuntimeFailureRecoveryAudit,
    build_runtime_failure_recovery_audit,
)
from bijux_proteomics_runtime.runs.replay import ReplayContract
from bijux_proteomics_runtime.runs.reruns import (
    PartialRerunPlan,
    build_partial_rerun_plan,
)
from bijux_proteomics_runtime.support.workspace import RunWorkspace
from bijux_proteomics_runtime.workflows.assurance import build_workflow_assurance_matrix
from bijux_proteomics_runtime.workflows.paths import (
    RuntimeReviewableOutputPath,
    run_reviewable_import_path,
    run_reviewable_sequence_path,
)


class BenchmarkRunMode(StrEnum):
    """Execution posture for one runtime benchmark package."""

    RAW_EXECUTABLE = "raw_executable"
    IMPORT_ONLY = "import_only"
    BLOCKED = "blocked"


class BenchmarkRunSpec(JsonModel):
    """One runtime-owned benchmark package specification."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    run_mode: BenchmarkRunMode
    canonical_entrypoint: str = Field(..., min_length=1)
    primary_input_path: str = Field(..., min_length=1)
    companion_input_paths: tuple[str, ...] = Field(default_factory=tuple)
    engine_name: str | None = Field(default=None)
    engine_version: str | None = Field(default=None)
    validating_test_paths: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkRuntimeTruthRow(JsonModel):
    """Honest runtime truth posture for one flagship benchmark package."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    run_mode: BenchmarkRunMode
    replayable: bool
    externally_cross_checked: bool
    artifact_browser_ready: bool
    blocker_notes: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkArtifactEntry(JsonModel):
    """Human-readable artifact row for runtime benchmark inspection."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    summary: str = Field(..., min_length=1)
    preview_lines: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkArtifactBrowser(JsonModel):
    """Reviewable benchmark artifact browser for one runtime run."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    parameter_choices: tuple[str, ...] = Field(default_factory=tuple)
    input_artifacts: tuple[BenchmarkArtifactEntry, ...] = Field(default_factory=tuple)
    imported_results: tuple[BenchmarkArtifactEntry, ...] = Field(default_factory=tuple)
    review_outputs: tuple[BenchmarkArtifactEntry, ...] = Field(default_factory=tuple)
    handoff_outputs: tuple[BenchmarkArtifactEntry, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkReplayDecision(JsonModel):
    """One replay scenario over a runtime benchmark package."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    eligible: bool
    invalidation_reasons: tuple[str, ...] = Field(default_factory=tuple)
    reused_nodes: tuple[str, ...] = Field(default_factory=tuple)
    rerun_nodes: tuple[str, ...] = Field(default_factory=tuple)


class BenchmarkReplayAudit(JsonModel):
    """Replay and invalidation posture for one runtime benchmark run."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    exact_reuse: BenchmarkReplayDecision
    tool_change: BenchmarkReplayDecision
    input_change: BenchmarkReplayDecision


class BenchmarkFailureRecoveryBundle(JsonModel):
    """Engineering-failure and scientific-invalidation split for one run."""

    model_config = ConfigDict(extra="forbid")

    package_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    engineering_recovery: RuntimeFailureRecoveryAudit
    scientific_invalidation_reasons: tuple[str, ...] = Field(default_factory=tuple)
    preserved_artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)
    blocked_artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_benchmark_run_specs() -> tuple[BenchmarkRunSpec, ...]:
    """Return the runtime-owned flagship benchmark packages."""
    return (
        BenchmarkRunSpec(
            package_id="sequence-first-useful-corpus",
            display_name="sequence first useful corpus",
            workflow_family="sequence_to_digest",
            run_mode=BenchmarkRunMode.RAW_EXECUTABLE,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_sequence_path",
            primary_input_path="packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/proteins.fasta",
            companion_input_paths=(
                "packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/results.tsv",
                "packages/bijux-proteomics-runtime/tests/fixtures/first_useful_run/spectra.mgf",
            ),
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_operator_path_surface.py",
            ),
            notes=(
                "runtime executes this corpus directly instead of replaying a toy result payload",
            ),
        ),
        BenchmarkRunSpec(
            package_id="dda-maxquant-pipeline-corpus",
            display_name="dda maxquant pipeline corpus",
            workflow_family="dda_import",
            run_mode=BenchmarkRunMode.IMPORT_ONLY,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path",
            primary_input_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_pipeline_export.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_evidence.tsv",
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/maxquant/maxquant_settings.txt",
            ),
            engine_name="maxquant",
            engine_version="19.0",
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py",
            ),
            notes=(
                "runtime imports the tracked MaxQuant export and keeps provenance explicit instead of pretending to execute MaxQuant",
            ),
        ),
        BenchmarkRunSpec(
            package_id="dia-diann-pipeline-corpus",
            display_name="dia diann pipeline corpus",
            workflow_family="dia_import",
            run_mode=BenchmarkRunMode.IMPORT_ONLY,
            canonical_entrypoint="bijux_proteomics_runtime.workflows.paths.run_reviewable_import_path",
            primary_input_path="packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_pipeline_export.tsv",
            companion_input_paths=(
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_report.tsv",
                "packages/bijux-proteomics-core/tests/fixtures/search_adapter_corpora/diann/diann_config.json",
            ),
            engine_name="dia-nn",
            engine_version="2.1.0",
            validating_test_paths=(
                "packages/bijux-proteomics-runtime/tests/workflows/test_runtime_external_pack_surface.py",
            ),
            notes=(
                "runtime imports the tracked DIA-NN export and preserves the external engine identity in review lineage",
            ),
        ),
    )


def run_benchmark_sequence_path(
    base_dir: Path,
    *,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    """Execute the flagship raw runtime benchmark package."""
    spec = _spec_by_id("sequence-first-useful-corpus")
    return run_reviewable_sequence_path(
        base_dir,
        sequence=_sequence_from_fasta(_repo_root() / spec.primary_input_path),
        execution_mode="cpu",
        artifacts_dir=artifacts_dir,
    )


def run_benchmark_dda_import_path(
    base_dir: Path,
    *,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    """Import the flagship DDA comparator export into runtime lineage."""
    return _run_import_benchmark_path(
        base_dir,
        package_id="dda-maxquant-pipeline-corpus",
        artifacts_dir=artifacts_dir,
    )


def run_benchmark_dia_import_path(
    base_dir: Path,
    *,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    """Import the flagship DIA comparator export into runtime lineage."""
    return _run_import_benchmark_path(
        base_dir,
        package_id="dia-diann-pipeline-corpus",
        artifacts_dir=artifacts_dir,
    )


def build_benchmark_runtime_truth_surface() -> tuple[BenchmarkRuntimeTruthRow, ...]:
    """Return the honest runtime posture across flagship benchmark packages."""
    matrix = {row.workflow_family: row for row in build_workflow_assurance_matrix()}
    specs = {spec.workflow_family: spec for spec in build_benchmark_run_specs()}
    rows: list[BenchmarkRuntimeTruthRow] = []
    for workflow_family in (
        "sequence_to_digest",
        "dda_import",
        "dia_import",
        "quant_review",
        "ptm_review",
    ):
        spec = specs.get(workflow_family)
        matrix_row = matrix[workflow_family]
        if spec is None:
            rows.append(
                BenchmarkRuntimeTruthRow(
                    package_id=f"{workflow_family}-blocked-runtime-path",
                    workflow_family=workflow_family,
                    run_mode=BenchmarkRunMode.BLOCKED,
                    replayable=False,
                    externally_cross_checked=False,
                    artifact_browser_ready=False,
                    blocker_notes=matrix_row.blocker_notes
                    or (
                        "no flagship runtime benchmark path is wired for this workflow family yet",
                    ),
                    notes=matrix_row.notes,
                )
            )
            continue
        rows.append(
            BenchmarkRuntimeTruthRow(
                package_id=spec.package_id,
                workflow_family=workflow_family,
                run_mode=spec.run_mode,
                replayable=True,
                externally_cross_checked=workflow_family in {"dda_import", "dia_import"},
                artifact_browser_ready=workflow_family != "sequence_to_digest",
                blocker_notes=matrix_row.blocker_notes,
                notes=spec.notes + matrix_row.notes,
            )
        )
    return tuple(rows)


def build_benchmark_artifact_browser(
    base_dir: Path,
    *,
    package_id: str,
    manifest: RuntimeReviewableOutputPath,
    artifacts_dir: Path | None = None,
) -> BenchmarkArtifactBrowser:
    """Build one human-readable artifact browser for a runtime benchmark run."""
    spec = _spec_by_id(package_id)
    workspace = RunWorkspace.for_run(
        base_dir,
        manifest.run_id,
        artifacts_root_override=artifacts_dir,
    )
    run_context = RunContextContract.load_json(workspace.run_context_path)
    replay_contract = ReplayContract.load_json(workspace.replay_contract_path)
    input_paths = (_repo_root() / spec.primary_input_path,) + tuple(
        _repo_root() / path for path in spec.companion_input_paths
    )
    imported_results = ()
    handoff_outputs: list[BenchmarkArtifactEntry] = []
    if manifest.import_trace_path is not None:
        imported_payload = _load_json_dict(
            workspace.artifact_items_dir / "imported_evidence.json"
        )
        imported_results = (
            _summarize_imported_payload(
                path=workspace.artifact_items_dir / "imported_evidence.json",
                imported_payload=imported_payload,
            ),
        )
        for path, artifact_kind in (
            (workspace.artifact_items_dir / "evidence_bundle.json", "runtime-evidence-bundle"),
            (workspace.artifact_items_dir / "review_packet.json", "runtime-review-packet"),
        ):
            if path.exists():
                handoff_outputs.append(
                    BenchmarkArtifactEntry(
                        artifact_kind=artifact_kind,
                        path=str(path),
                        sha256=_sha256(path),
                        summary=f"{artifact_kind} stays downstream-readable from the runtime import lane",
                        preview_lines=_preview_for_json(path),
                    )
                )
    return BenchmarkArtifactBrowser(
        package_id=package_id,
        run_id=manifest.run_id,
        command=manifest.command,
        workflow_family=manifest.workflow_family,
        parameter_choices=(
            f"provider_name={run_context.provider_name}",
            f"command={run_context.workflow.command}",
            f"config_fingerprint={run_context.config_fingerprint}",
            f"parameter_fingerprint={replay_contract.parameter_fingerprint}",
            f"tool_fingerprint={replay_contract.tool_fingerprint}",
        ),
        input_artifacts=tuple(_summarize_source_path(path) for path in input_paths),
        imported_results=imported_results,
        review_outputs=tuple(
            _summarize_runtime_output(path, artifact_kind)
            for path, artifact_kind in (
                (workspace.run_summary_path, "runtime-status"),
                (workspace.report_path, "runtime-report"),
                (workspace.replay_contract_path, "runtime-replay-contract"),
                (workspace.integrity_report_path, "runtime-integrity-report"),
            )
            if path.exists()
        ),
        handoff_outputs=tuple(handoff_outputs),
        notes=(
            "artifact browser surfaces reviewable runtime files without requiring a human to open raw run JSON by hand",
        ),
    )


def build_benchmark_replay_audit(
    base_dir: Path,
    *,
    package_id: str,
    manifest: RuntimeReviewableOutputPath,
    artifacts_dir: Path | None = None,
) -> BenchmarkReplayAudit:
    """Build replay and invalidation posture for one runtime benchmark run."""
    workspace = RunWorkspace.for_run(
        base_dir,
        manifest.run_id,
        artifacts_root_override=artifacts_dir,
    )
    run_context = RunContextContract.load_json(workspace.run_context_path)
    replay_contract = ReplayContract.load_json(workspace.replay_contract_path)
    artifact_ledger = RuntimeArtifactLedger.load_json(workspace.artifact_ledger_path)
    exact_plan = build_partial_rerun_plan(
        previous_run_context=run_context,
        previous_replay_contract=replay_contract,
        current_replay_contract=replay_contract,
        artifact_ledger=artifact_ledger,
    )
    tool_change_contract = replay_contract.model_copy(
        update={
            "tool_fingerprint": _stable_fingerprint(
                {
                    "provider_name": run_context.provider_name,
                    "tool_versions": {run_context.provider_name: "changed"},
                }
            )
        }
    )
    tool_change_plan = build_partial_rerun_plan(
        previous_run_context=run_context,
        previous_replay_contract=replay_contract,
        current_replay_contract=tool_change_contract,
        artifact_ledger=artifact_ledger,
    )
    input_change_contract = replay_contract.model_copy(
        update={"input_fingerprint": "changed_" + replay_contract.input_fingerprint}
    )
    input_change_plan = build_partial_rerun_plan(
        previous_run_context=run_context,
        previous_replay_contract=replay_contract,
        current_replay_contract=input_change_contract,
        artifact_ledger=artifact_ledger,
    )
    return BenchmarkReplayAudit(
        package_id=package_id,
        run_id=manifest.run_id,
        exact_reuse=_replay_decision("exact_reuse", exact_plan),
        tool_change=_replay_decision("tool_change", tool_change_plan),
        input_change=_replay_decision("input_change", input_change_plan),
    )


def build_benchmark_failure_recovery_bundle(
    base_dir: Path,
    *,
    package_id: str,
    manifest: RuntimeReviewableOutputPath,
    artifacts_dir: Path | None = None,
) -> BenchmarkFailureRecoveryBundle:
    """Build engineering-failure and scientific-invalidation split for one run."""
    workspace = RunWorkspace.for_run(
        base_dir,
        manifest.run_id,
        artifacts_root_override=artifacts_dir,
    )
    engineering = build_runtime_failure_recovery_audit(workspace, run_id=manifest.run_id)
    replay_audit = build_benchmark_replay_audit(
        base_dir,
        package_id=package_id,
        manifest=manifest,
        artifacts_dir=artifacts_dir,
    )
    return BenchmarkFailureRecoveryBundle(
        package_id=package_id,
        run_id=manifest.run_id,
        engineering_recovery=engineering,
        scientific_invalidation_reasons=replay_audit.input_change.invalidation_reasons,
        preserved_artifact_kinds=tuple(
            _normalize_recovery_artifact_kind(artifact.artifact_kind, artifact.path)
            for artifact in engineering.preserved_artifacts
        ),
        blocked_artifact_kinds=tuple(
            _normalize_recovery_artifact_kind(artifact.artifact_kind, artifact.path)
            for artifact in engineering.blocked_artifacts
        ),
        notes=(
            "engineering failure is determined from artifact survivability and integrity checks",
            "scientific invalidation is determined from replay fingerprint changes rather than filesystem corruption",
        ),
    )


def _run_import_benchmark_path(
    base_dir: Path,
    *,
    package_id: str,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    spec = _spec_by_id(package_id)
    return run_reviewable_import_path(
        base_dir,
        sequence="MPEPTIDE",
        source_path=_repo_root() / spec.primary_input_path,
        engine_name=str(spec.engine_name),
        engine_version=str(spec.engine_version),
        artifacts_dir=artifacts_dir,
    )


def _spec_by_id(package_id: str) -> BenchmarkRunSpec:
    return next(spec for spec in build_benchmark_run_specs() if spec.package_id == package_id)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "configs").is_dir()
    )


def _sequence_from_fasta(path: Path) -> str:
    return "".join(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith(">")
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_fingerprint(payload: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_json_dict(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object at {path}")
    return payload


def _preview_for_json(path: Path, *, limit: int = 3) -> tuple[str, ...]:
    payload = _load_json_dict(path)
    return tuple(
        f"{key}={json.dumps(value, sort_keys=True)}"
        for key, value in list(payload.items())[:limit]
    )


def _summarize_source_path(path: Path) -> BenchmarkArtifactEntry:
    preview = path.read_text(encoding="utf-8").splitlines()[:3]
    return BenchmarkArtifactEntry(
        artifact_kind="benchmark-source-input",
        path=str(path),
        sha256=_sha256(path),
        summary=f"tracked benchmark source input {path.name}",
        preview_lines=tuple(preview),
    )


def _summarize_imported_payload(
    *,
    path: Path,
    imported_payload: dict[str, Any],
) -> BenchmarkArtifactEntry:
    payload = imported_payload.get("payload", {})
    preview_lines: list[str] = []
    if isinstance(payload, dict) and "rows" in payload:
        columns = payload.get("columns", ())
        row_count = payload.get("row_count", 0)
        preview_lines.append(
            f"columns={','.join(str(column) for column in columns)}"
        )
        preview_lines.append(f"row_count={row_count}")
        rows = payload.get("rows", [])
        if isinstance(rows, list) and rows:
            first = rows[0]
            if isinstance(first, dict):
                preview_lines.append(
                    ",".join(f"{key}={value}" for key, value in list(first.items())[:4])
                )
        summary = f"imported tabular comparator payload with {row_count} rows"
    else:
        preview_lines.extend(_preview_for_json(path))
        summary = "imported json comparator payload"
    return BenchmarkArtifactEntry(
        artifact_kind="runtime-imported-evidence",
        path=str(path),
        sha256=_sha256(path),
        summary=summary,
        preview_lines=tuple(preview_lines),
    )


def _summarize_runtime_output(path: Path, artifact_kind: str) -> BenchmarkArtifactEntry:
    if path.suffix == ".json":
        preview = _preview_for_json(path)
    else:
        preview = tuple(path.read_text(encoding="utf-8").splitlines()[:3])
    return BenchmarkArtifactEntry(
        artifact_kind=artifact_kind,
        path=str(path),
        sha256=_sha256(path),
        summary=f"runtime review output {path.name}",
        preview_lines=preview,
    )


def _replay_decision(scenario_id: str, plan: PartialRerunPlan) -> BenchmarkReplayDecision:
    return BenchmarkReplayDecision(
        scenario_id=scenario_id,
        eligible=plan.replay_eligibility.eligible,
        invalidation_reasons=plan.replay_eligibility.invalidation_reasons,
        reused_nodes=tuple(step.node_id for step in plan.reuse_steps),
        rerun_nodes=tuple(step.node_id for step in plan.rerun_steps),
    )


def _normalize_recovery_artifact_kind(artifact_kind: str, path: str) -> str:
    name = Path(path).name
    if artifact_kind == "runtime-artifact-item":
        if name == "review_packet.json":
            return "runtime-review-packet"
        if name == "evidence_bundle.json":
            return "runtime-evidence-bundle"
        if name == "reviewable_import_path.json":
            return "runtime-reviewable-import-path"
    return artifact_kind


__all__ = [
    "BenchmarkArtifactBrowser",
    "BenchmarkArtifactEntry",
    "BenchmarkFailureRecoveryBundle",
    "BenchmarkReplayAudit",
    "BenchmarkReplayDecision",
    "BenchmarkRunMode",
    "BenchmarkRunSpec",
    "BenchmarkRuntimeTruthRow",
    "build_benchmark_artifact_browser",
    "build_benchmark_failure_recovery_bundle",
    "build_benchmark_replay_audit",
    "build_benchmark_run_specs",
    "build_benchmark_runtime_truth_surface",
    "run_benchmark_dda_import_path",
    "run_benchmark_dia_import_path",
    "run_benchmark_sequence_path",
]
