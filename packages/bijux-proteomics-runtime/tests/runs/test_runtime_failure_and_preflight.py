from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.core.failures import FailureType
from bijux_proteomics_runtime.runs import create_run_context
from bijux_proteomics_runtime.runs.failure_reports import (
    RuntimeFailureCategory,
    build_runtime_failure_report,
)
from bijux_proteomics_runtime.runs.preflight import (
    PreflightCheckState,
    build_runtime_preflight_report,
)


def test_runtime_failure_report_classifies_subprocess_and_container_failures() -> None:
    subprocess_report = build_runtime_failure_report(
        run_id="failure-run-1",
        failure_type=FailureType.TOOL_TIMEOUT.value,
        message="tool timed out",
        detail_codes=("tool_timeout",),
    )
    container_report = build_runtime_failure_report(
        run_id="failure-run-2",
        failure_type=FailureType.CAPABILITY_MISSING.value,
        message="missing docker",
        detail_codes=("missing_dependency:docker",),
    )

    assert subprocess_report.failure_category is RuntimeFailureCategory.SUBPROCESS
    assert subprocess_report.retryable is True
    assert container_report.failure_category is RuntimeFailureCategory.CONTAINER


def test_runtime_failure_report_classifies_workspace_breakage() -> None:
    report = build_runtime_failure_report(
        run_id="failure-run-3",
        failure_type=FailureType.CAPABILITY_MISSING.value,
        message="workspace files missing",
        detail_codes=("missing:config.json",),
    )

    assert report.failure_category is RuntimeFailureCategory.WORKSPACE


def test_runtime_preflight_report_flags_missing_workspace_files(tmp_path: Path) -> None:
    context, _ = create_run_context(tmp_path, run_id="preflight-run-1")
    context.workspace.config_path.unlink()

    report = build_runtime_preflight_report(
        context.workspace,
        run_id=context.run_id,
        provider_name="heuristic_proxy",
    )

    assert report.passed is False
    layout_check = next(
        check for check in report.checks if check.check_id == "workspace_layout"
    )
    assert layout_check.state is PreflightCheckState.FAIL


def test_runtime_preflight_report_passes_for_heuristic_provider(tmp_path: Path) -> None:
    context, _ = create_run_context(tmp_path, run_id="preflight-run-2")

    report = build_runtime_preflight_report(
        context.workspace,
        run_id=context.run_id,
        provider_name="heuristic_proxy",
    )

    assert report.passed is True
    assert all(check.state is not PreflightCheckState.FAIL for check in report.checks)
