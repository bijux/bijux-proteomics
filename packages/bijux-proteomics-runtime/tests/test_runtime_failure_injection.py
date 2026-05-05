from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics_runtime.runs import RunManager
from bijux_proteomics_runtime.runs import (
    build_run_context_contract,
    create_run_context,
)
from bijux_proteomics_runtime.runtime.control.failure_reports import (
    RuntimeFailureCategory,
    RuntimeFailureReport,
)
from bijux_proteomics_runtime.runs.replay import (
    build_replay_contract,
    evaluate_replay_eligibility,
)
from bijux_proteomics_runtime.runs import RunConfig


def test_runtime_failure_injection_reports_broken_container_requirements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runtime.control.preflight.provider_requirements",
        lambda _name: ["missing_dependency:docker"],
    )
    manager = RunManager(
        tmp_path,
        RunConfig(predictors_enabled=["local_rosettafold"], launch_surface="container"),
    )

    result = manager.run("MPEPTIDE", run_id="runtime-failure-container-1")

    report = RuntimeFailureReport.load_json(
        tmp_path / "artifacts" / "runtime-failure-container-1" / "failure_report.json"
    )
    assert result["status"] == "failure"
    assert report.failure_category is RuntimeFailureCategory.CONTAINER
    assert "missing_dependency:docker" in report.detail_codes


def test_runtime_failure_injection_reports_missing_tool_requirements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "bijux_proteomics_runtime.runtime.control.preflight.provider_requirements",
        lambda _name: ["missing_dependency:transformers"],
    )
    manager = RunManager(
        tmp_path,
        RunConfig(predictors_enabled=["local_esmfold"]),
    )

    result = manager.run("MPEPTIDE", run_id="runtime-failure-tool-1")

    report = RuntimeFailureReport.load_json(
        tmp_path / "artifacts" / "runtime-failure-tool-1" / "failure_report.json"
    )
    assert result["status"] == "failure"
    assert report.failure_category is RuntimeFailureCategory.VALIDATION
    assert "missing_dependency:transformers" in report.detail_codes


def test_runtime_failure_injection_handles_interrupted_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise_interrupt(candidate, context, tool):  # type: ignore[no-untyped-def]
        raise KeyboardInterrupt

    monkeypatch.setattr(
        "bijux_proteomics_runtime.runs.manager.run_flow",
        _raise_interrupt,
    )
    manager = RunManager(tmp_path)

    result = manager.run("MPEPTIDE", run_id="runtime-failure-interrupt-1")

    assert result["status"] == "failure"
    assert result["failure_type"] == "unknown"


def test_runtime_failure_injection_flags_stale_replay_state(tmp_path: Path) -> None:
    context, _ = create_run_context(tmp_path, run_id="runtime-stale-replay-1")
    expected = build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config=context.config,
        provider_name="heuristic_proxy",
        artifact_policy=context.artifact_policy,
        sequence="MPEPTIDE",
        command="run",
        workflow_family="structure_prediction",
        candidate_id="runtime-stale-replay-1-c0",
    )
    changed = build_run_context_contract(
        run_id=context.run_id,
        started_at=context.start_time.isoformat(),
        base_dir=tmp_path,
        config={**context.config, "execution_mode": "gpu"},
        provider_name="local_esmfold",
        artifact_policy=context.artifact_policy,
        sequence="MPEPTIDER",
        command="run",
        workflow_family="structure_prediction",
        candidate_id="runtime-stale-replay-1-c0",
    )
    expected_contract = build_replay_contract(
        expected,
        app_version="1.0.0",
        git_commit="abc123",
        tool_versions={"heuristic_proxy": "0.1"},
    )
    changed_contract = build_replay_contract(
        changed,
        app_version="1.0.1",
        git_commit="def456",
        tool_versions={"local_esmfold": "2.0"},
    )

    decision = evaluate_replay_eligibility(expected_contract, changed_contract)

    assert decision.eligible is False
    assert set(decision.invalidation_reasons) >= {
        "input_changed",
        "parameters_changed",
        "tools_changed",
        "code_expectations_changed",
    }
