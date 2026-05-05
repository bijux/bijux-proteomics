from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runtime import RunManager
from bijux_proteomics_runtime.runtime.control import (
    ContainerRunBundle,
    ImportRunBundle,
    LocalRunBundle,
    SchedulerJobBundle,
    RuntimeImportTrace,
    load_container_run_bundle,
    load_import_run_bundle,
    load_import_trace,
    load_local_run_bundle,
    load_scheduler_job_bundle,
)
from bijux_proteomics_runtime.runtime.context import RunConfig
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace


def _fake_success(candidate, context, tool):  # type: ignore[no-untyped-def]
    return {
        "candidate_id": candidate.candidate_id,
        "candidate": candidate.model_dump(),
        "plan_fingerprint": "plan-1",
        "tool_status": "success",
        "report": {"status": "ok"},
        "qc_status": "acceptable",
        "coordinator_decision": "TerminateRun",
        "failure_type": "none",
        "lifecycle_state": "done",
    }


def test_runtime_local_execution_surface_is_reusable(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runtime.control.execution.run_flow",
        _fake_success,
    )

    manager = RunManager(tmp_path)
    manager.run("MPEPTIDE", run_id="runtime-local-conformance-1")

    bundle = load_local_run_bundle(
        RunWorkspace.for_run(tmp_path, "runtime-local-conformance-1")
    )

    assert isinstance(bundle, LocalRunBundle)
    assert bundle.run_context.workflow.import_only is False


def test_runtime_container_execution_surface_is_runtime_owned(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runtime.control.execution.run_flow",
        _fake_success,
    )
    manager = RunManager(
        tmp_path,
        RunConfig(
            launch_surface="container",
            container_image="ghcr.io/bijux/runtime:proteomics",
            container_image_digest="sha256:conformance",
        ),
    )
    manager.run("MPEPTIDE", run_id="runtime-container-conformance-1")

    bundle = load_container_run_bundle(
        RunWorkspace.for_run(tmp_path, "runtime-container-conformance-1")
    )

    assert isinstance(bundle, ContainerRunBundle)
    assert bundle.image_digest == "sha256:conformance"


def test_runtime_scheduler_execution_surface_is_runtime_owned(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runtime.control.execution.run_flow",
        _fake_success,
    )
    manager = RunManager(
        tmp_path,
        RunConfig(
            launch_surface="scheduler",
            scheduler_system="slurm",
            scheduler_queue="gpu-short",
        ),
    )
    manager.run("MPEPTIDE", run_id="runtime-scheduler-conformance-1")

    bundle = load_scheduler_job_bundle(
        RunWorkspace.for_run(tmp_path, "runtime-scheduler-conformance-1")
    )

    assert isinstance(bundle, SchedulerJobBundle)
    assert bundle.launch_metadata.scheduler_system == "slurm"


def test_runtime_import_execution_surface_is_runtime_owned(tmp_path: Path) -> None:
    source_path = tmp_path / "external" / "imported.json"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text('{"report":"ok"}', encoding="utf-8")
    manager = RunManager(tmp_path)
    manager.import_result(
        sequence="MPEPTIDE",
        source_path=source_path,
        imported_payload={"proteins": ["P12345"]},
        engine_name="maxquant",
        engine_version="2.1.0",
        run_id="runtime-import-conformance-1",
    )

    workspace = RunWorkspace.for_run(tmp_path, "runtime-import-conformance-1")
    assert isinstance(load_import_trace(workspace), RuntimeImportTrace)
    assert isinstance(load_import_run_bundle(workspace), ImportRunBundle)
