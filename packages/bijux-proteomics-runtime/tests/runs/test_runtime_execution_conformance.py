from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runs import RunConfig, RunManager
from bijux_proteomics_runtime.runs.import_lineage import (
    ImportRunBundle,
    RuntimeImportTrace,
    load_import_run_bundle,
    load_import_trace,
)
from bijux_proteomics_runtime.runs.launch_bundles import (
    ContainerRunBundle,
    SchedulerJobBundle,
    load_container_run_bundle,
    load_scheduler_job_bundle,
)
from bijux_proteomics_runtime.runs.replay import LocalRunBundle, load_local_run_bundle
from bijux_proteomics_runtime.support.workspace import RunWorkspace


def test_runtime_local_execution_surface_is_reusable(
    tmp_path: Path,
) -> None:
    manager = RunManager(tmp_path)
    manager.run("MPEPTIDE", run_id="runtime-local-conformance-1")

    bundle = load_local_run_bundle(
        RunWorkspace.for_run(tmp_path, "runtime-local-conformance-1")
    )

    assert isinstance(bundle, LocalRunBundle)
    assert bundle.run_context.workflow.import_only is False


def test_runtime_container_execution_surface_is_runtime_owned(
    tmp_path: Path,
) -> None:
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
) -> None:
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
