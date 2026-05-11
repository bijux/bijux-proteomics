from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.runs import (
    RunConfig,
    RunManager,
    build_run_context_contract,
    create_run_context,
)
from bijux_proteomics_runtime.runs.context import RunContext
from bijux_proteomics_runtime.runs.contracts import RunContextContract
from bijux_proteomics_runtime.runs.launch_bundles import (
    ContainerRunBundle,
    SchedulerJobBundle,
    build_container_run_bundle,
    build_scheduler_job_bundle,
)
from bijux_proteomics_runtime.runs.replay import ReplayContract, build_replay_contract


def _contract(
    tmp_path: Path,
    *,
    run_id: str,
    config: RunConfig | None = None,
) -> tuple[RunContext, RunContextContract, ReplayContract]:
    context, _ = create_run_context(tmp_path, config=config, run_id=run_id)
    run_context = build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config=context.config,
        provider_name="heuristic_proxy",
        artifact_policy=context.artifact_policy,
        sequence="ACDEFGHIKLMNPQRSTVWY",
        command="run",
        workflow_family="structure_prediction",
        candidate_id=f"{run_id}-c0",
    )
    replay_contract = build_replay_contract(
        run_context,
        app_version="1.2.3",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.1"},
    )
    return context, run_context, replay_contract


def test_runtime_container_run_bundle_captures_image_mounts_and_artifacts(
    tmp_path: Path,
) -> None:
    config = RunConfig(
        launch_surface="container",
        container_image="ghcr.io/bijux/runtime:proteomics",
        container_image_digest="sha256:1234",
        execution_mode="gpu",
        predictors_enabled=["local_esmfold"],
        tool_versions={"local_esmfold": "2.0"},
    )
    context, run_context, replay_contract = _contract(
        tmp_path,
        run_id="container-bundle-1",
        config=config,
    )

    bundle = build_container_run_bundle(
        workspace=context.workspace,
        run_context=run_context,
        replay_contract=replay_contract,
        config=context.config,
    )

    assert isinstance(bundle, ContainerRunBundle)
    assert bundle.image_digest == "sha256:1234"
    assert {mount.target_path for mount in bundle.mount_maps} == {
        "/artifacts",
        "/workspace",
    }
    assert any(
        expectation.artifact_kind == "runtime-replay-contract"
        for expectation in bundle.artifact_expectations
    )


def test_runtime_scheduler_job_bundle_captures_launch_metadata_and_replay_boundary(
    tmp_path: Path,
) -> None:
    config = RunConfig(
        launch_surface="scheduler",
        scheduler_system="slurm",
        scheduler_queue="gpu-long",
        scheduler_job_name="bijux-queue-review",
        scheduler_submission_id="slurm:42",
    )
    _context, run_context, replay_contract = _contract(
        tmp_path,
        run_id="scheduler-bundle-1",
        config=config,
    )

    bundle = build_scheduler_job_bundle(
        run_context=run_context,
        replay_contract=replay_contract,
        config=config.model_dump(),
    )

    assert isinstance(bundle, SchedulerJobBundle)
    assert bundle.launch_metadata.scheduler_system == "slurm"
    assert bundle.launch_metadata.queue_name == "gpu-long"
    assert bundle.replay_boundary.requires_human_resume is True


def test_runtime_run_manager_persists_non_local_execution_bundles(
    tmp_path: Path,
) -> None:
    container_manager = RunManager(
        tmp_path,
        RunConfig(
            launch_surface="container",
            container_image="ghcr.io/bijux/runtime:proteomics",
            container_image_digest="sha256:abcd",
        ),
    )
    container_result = container_manager.run("MPEPTIDE", run_id="runtime-container-1")

    scheduler_manager = RunManager(
        tmp_path,
        RunConfig(
            launch_surface="scheduler",
            scheduler_system="slurm",
            scheduler_queue="gpu-short",
        ),
    )
    scheduler_result = scheduler_manager.run("MPEPTIDE", run_id="runtime-scheduler-1")

    assert container_result["status"] == "success"
    assert scheduler_result["status"] == "success"
    assert (
        tmp_path / "artifacts" / "runtime-container-1" / "container_run_bundle.json"
    ).exists()
    assert (
        tmp_path / "artifacts" / "runtime-scheduler-1" / "scheduler_job_bundle.json"
    ).exists()
