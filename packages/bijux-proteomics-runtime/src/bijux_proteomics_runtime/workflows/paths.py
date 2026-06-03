# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned workflow path manifests for reviewable execution outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runs.contracts import RunContextContract
from bijux_proteomics_runtime.runs.ledger import (
    refresh_runtime_artifact_ledger,
)
from bijux_proteomics_runtime.runs.manager import RunManager
from bijux_proteomics_runtime.runs.operations import build_runtime_run_config
from bijux_proteomics_runtime.support.workspace import RunWorkspace, write_json_atomic


class RuntimeWorkflowStep(JsonModel):
    """One runtime-owned operational step inside a smoke workflow path."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    operation_name: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    import_only: bool = False
    required_artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)
    review_artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)
    handoff_surface: str = Field(..., min_length=1)


class RuntimeSmokeWorkflow(JsonModel):
    """One runtime-owned smoke workflow definition."""

    model_config = ConfigDict(extra="forbid")

    workflow_key: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    steps: tuple[RuntimeWorkflowStep, ...] = Field(default_factory=tuple)


class RuntimeReviewableOutputPath(JsonModel):
    """Reviewable runtime output path for one completed or imported run."""

    model_config = ConfigDict(extra="forbid")

    path_key: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    import_only: bool
    downstream_surface: str = Field(..., min_length=1)
    summary_path: str = Field(..., min_length=1)
    report_path: str = Field(..., min_length=1)
    replay_contract_path: str = Field(..., min_length=1)
    integrity_report_path: str = Field(..., min_length=1)
    import_trace_path: str | None = Field(default=None)
    artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_runtime_smoke_workflows() -> tuple[RuntimeSmokeWorkflow, ...]:
    """Return the canonical runtime smoke workflow catalog."""
    return (
        RuntimeSmokeWorkflow(
            workflow_key="sequence_to_digest",
            display_name="sequence to digest review path",
            steps=(
                RuntimeWorkflowStep(
                    step_id="run-sequence",
                    operation_name="run_reviewable_sequence_path",
                    command="run",
                    workflow_family="sequence_to_digest",
                    required_artifact_kinds=(
                        "runtime-run-context",
                        "runtime-replay-contract",
                    ),
                    review_artifact_kinds=(
                        "runtime-status",
                        "runtime-report",
                    ),
                    handoff_surface="intelligence_review",
                ),
            ),
        ),
        RuntimeSmokeWorkflow(
            workflow_key="dda_import",
            display_name="dda import review path",
            steps=(
                RuntimeWorkflowStep(
                    step_id="import-dda",
                    operation_name="run_reviewable_import_path",
                    command="import",
                    workflow_family="dda_import",
                    import_only=True,
                    required_artifact_kinds=("runtime-import-trace",),
                    review_artifact_kinds=(
                        "runtime-status",
                        "runtime-import-run-bundle",
                    ),
                    handoff_surface="intelligence_review",
                ),
            ),
        ),
        RuntimeSmokeWorkflow(
            workflow_key="dia_import",
            display_name="dia import review path",
            steps=(
                RuntimeWorkflowStep(
                    step_id="import-dia",
                    operation_name="run_reviewable_import_path",
                    command="import",
                    workflow_family="dia_import",
                    import_only=True,
                    required_artifact_kinds=("runtime-import-trace",),
                    review_artifact_kinds=(
                        "runtime-status",
                        "runtime-import-run-bundle",
                    ),
                    handoff_surface="intelligence_review",
                ),
            ),
        ),
        RuntimeSmokeWorkflow(
            workflow_key="quant",
            display_name="quant review path",
            steps=(
                RuntimeWorkflowStep(
                    step_id="import-quant",
                    operation_name="run_reviewable_import_path",
                    command="import",
                    workflow_family="quant_review",
                    import_only=True,
                    required_artifact_kinds=("runtime-import-trace",),
                    review_artifact_kinds=(
                        "runtime-status",
                        "runtime-import-run-bundle",
                    ),
                    handoff_surface="intelligence_review",
                ),
            ),
        ),
        RuntimeSmokeWorkflow(
            workflow_key="ptm",
            display_name="ptm review path",
            steps=(
                RuntimeWorkflowStep(
                    step_id="import-ptm",
                    operation_name="run_reviewable_import_path",
                    command="import",
                    workflow_family="ptm_review",
                    import_only=True,
                    required_artifact_kinds=("runtime-import-trace",),
                    review_artifact_kinds=(
                        "runtime-status",
                        "runtime-import-run-bundle",
                    ),
                    handoff_surface="intelligence_review",
                ),
            ),
        ),
        RuntimeSmokeWorkflow(
            workflow_key="review",
            display_name="analytical review path",
            steps=(
                RuntimeWorkflowStep(
                    step_id="publish-review",
                    operation_name="run_reviewable_sequence_path",
                    command="run",
                    workflow_family="review",
                    required_artifact_kinds=("runtime-replay-contract",),
                    review_artifact_kinds=(
                        "runtime-status",
                        "runtime-integrity-report",
                    ),
                    handoff_surface="intelligence_review",
                ),
            ),
        ),
        RuntimeSmokeWorkflow(
            workflow_key="lab_handoff",
            display_name="lab handoff review path",
            steps=(
                RuntimeWorkflowStep(
                    step_id="publish-handoff",
                    operation_name="run_reviewable_sequence_path",
                    command="run",
                    workflow_family="lab_handoff",
                    required_artifact_kinds=("runtime-replay-contract",),
                    review_artifact_kinds=(
                        "runtime-status",
                        "runtime-integrity-report",
                    ),
                    handoff_surface="lab_operational_follow_up",
                ),
            ),
        ),
        RuntimeSmokeWorkflow(
            workflow_key="package_smoke",
            display_name="runtime package smoke archive path",
            steps=(
                RuntimeWorkflowStep(
                    step_id="run-package-smoke",
                    operation_name="run_runtime_package_smoke_workflow",
                    command="run",
                    workflow_family="runtime_package_smoke",
                    required_artifact_kinds=("result_manifest",),
                    review_artifact_kinds=(
                        "runtime-package-smoke-report",
                        "result-archive",
                    ),
                    handoff_surface="archived_result_review",
                ),
            ),
        ),
        RuntimeSmokeWorkflow(
            workflow_key="architecture_demo",
            display_name="runtime architecture demo archive path",
            steps=(
                RuntimeWorkflowStep(
                    step_id="run-architecture-demo",
                    operation_name="run_runtime_architecture_demo",
                    command="run",
                    workflow_family="runtime_architecture_demo",
                    required_artifact_kinds=(
                        "runtime-step-artifacts",
                        "result_manifest",
                    ),
                    review_artifact_kinds=(
                        "runtime-architecture-demo-report",
                        "result-archive",
                    ),
                    handoff_surface="archived_result_review",
                ),
            ),
        ),
    )


def run_reviewable_sequence_path(
    base_dir: Path,
    *,
    sequence: str,
    provider: str | None = None,
    artifacts_dir: Path | None = None,
    execution_mode: str = "cpu",
) -> RuntimeReviewableOutputPath:
    """Run one canonical runtime-owned sequence path to a reviewable output."""
    config = build_runtime_run_config(
        rounds=1,
        dry_run=False,
        logging_enabled=True,
        provider=provider,
        artifacts_dir=artifacts_dir,
        execution_mode=execution_mode,
    )
    output = RunManager(base_dir, config).run(sequence)
    run_id = str(output["run_id"])
    workspace = RunWorkspace.for_run(
        base_dir,
        run_id,
        artifacts_root_override=artifacts_dir,
    )
    manifest = RuntimeReviewableOutputPath(
        path_key="reviewable_run_path",
        run_id=run_id,
        command="run",
        workflow_family="sequence_to_digest",
        import_only=False,
        downstream_surface="intelligence_review",
        summary_path=str(workspace.run_summary_path),
        report_path=str(workspace.report_path),
        replay_contract_path=str(workspace.replay_contract_path),
        integrity_report_path=str(workspace.integrity_report_path),
        artifact_kinds=(
            "runtime-status",
            "runtime-report",
            "runtime-replay-contract",
            "runtime-integrity-report",
        ),
        notes=(
            "clean-install useful run path stays inside runtime-owned execution surfaces",
            "review consumers should read the run manifest instead of private workspace glue",
        ),
    )
    _write_reviewable_output_manifest(
        workspace,
        manifest,
        manifest_name="reviewable_run_path.json",
    )
    _refresh_review_manifest_ledger(workspace, run_id)
    return manifest


def run_reviewable_import_path(
    base_dir: Path,
    *,
    sequence: str,
    source_path: Path,
    engine_name: str,
    engine_version: str,
    artifacts_dir: Path | None = None,
) -> RuntimeReviewableOutputPath:
    """Import one external result to a runtime-owned reviewable output."""
    output = RunManager(
        base_dir,
        build_runtime_run_config(
            rounds=1,
            dry_run=False,
            logging_enabled=True,
            provider=None,
            artifacts_dir=artifacts_dir,
            execution_mode="cpu",
            launch_surface="import",
        ),
    ).import_result(
        sequence=sequence,
        source_path=source_path,
        imported_payload=_load_import_payload(source_path),
        engine_name=engine_name,
        engine_version=engine_version,
    )
    run_id = str(output["run_id"])
    workspace = RunWorkspace.for_run(
        base_dir,
        run_id,
        artifacts_root_override=artifacts_dir,
    )
    manifest = RuntimeReviewableOutputPath(
        path_key="reviewable_import_path",
        run_id=run_id,
        command="import",
        workflow_family="external_import",
        import_only=True,
        downstream_surface="intelligence_review",
        summary_path=str(workspace.run_summary_path),
        report_path=str(workspace.report_path),
        replay_contract_path=str(workspace.replay_contract_path),
        integrity_report_path=str(workspace.integrity_report_path),
        import_trace_path=str(workspace.import_trace_path),
        artifact_kinds=(
            "runtime-status",
            "runtime-import-trace",
            "runtime-import-run-bundle",
            "runtime-replay-contract",
            "runtime-integrity-report",
        ),
        notes=(
            "import-only useful path preserves third-party provenance without pretending runtime executed the upstream engine",
            "review consumers should follow the import trace before interpreting the derived decision brief",
        ),
    )
    _write_reviewable_output_manifest(
        workspace,
        manifest,
        manifest_name="reviewable_import_path.json",
    )
    _refresh_review_manifest_ledger(workspace, run_id)
    return manifest


def _load_import_payload(source_path: Path) -> dict[str, object]:
    suffix = source_path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload
        return {"items": payload}
    if suffix in {".tsv", ".csv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with source_path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            rows = [dict(row) for row in reader]
            columns = tuple(reader.fieldnames or ())
        return {
            "source_format": suffix.lstrip("."),
            "columns": columns,
            "row_count": len(rows),
            "rows": rows,
        }
    return {
        "source_format": suffix.lstrip(".") or "text",
        "text": source_path.read_text(encoding="utf-8"),
    }


def _write_reviewable_output_manifest(
    workspace: RunWorkspace,
    manifest: RuntimeReviewableOutputPath,
    *,
    manifest_name: str,
) -> None:
    write_json_atomic(workspace.artifact_items_dir / manifest_name, manifest.to_dict())


def _refresh_review_manifest_ledger(workspace: RunWorkspace, run_id: str) -> None:
    run_context = RunContextContract.load_json(workspace.run_context_path)
    refresh_runtime_artifact_ledger(
        workspace,
        run_id=run_id,
        artifact_policy=run_context.artifact_policy,
        producer="bijux_proteomics_runtime.workflows.paths",
    )


__all__ = [
    "RuntimeReviewableOutputPath",
    "RuntimeSmokeWorkflow",
    "RuntimeWorkflowStep",
    "build_runtime_smoke_workflows",
    "run_reviewable_import_path",
    "run_reviewable_sequence_path",
]
