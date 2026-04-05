from __future__ import annotations

from pathlib import Path

import importlib.metadata
import pytest

from agentic_proteins.runtime.context import create_run_context, VersionInfo, RunLifecycleState
from agentic_proteins.runtime.control.execution import (
    _build_run_summary,
    _ensure_telemetry_costs,
    _select_structure_tool,
    _version_info,
)


def test_build_run_summary_maps_status(tmp_path: Path) -> None:
    context, _warnings = create_run_context(tmp_path)
    version = VersionInfo(app_version="0.0.0", git_commit="unknown", tool_versions={})
    summary = _build_run_summary(
        context=context,
        command="run",
        candidate_id="cand",
        status="success",
        failure_type="none",
        lifecycle_state=RunLifecycleState.EXECUTING.value,
        tool_status="success",
        qc_status="acceptable",
        warnings=["cpu_fallback:using_cpu"],
        version_info=version,
        provider_name="heuristic",
    )
    assert summary["tool_status"] == "degraded"
    assert summary["outcome"] in {"accepted", "rejected"}


def test_version_info_handles_missing_package(monkeypatch: pytest.MonkeyPatch) -> None:
    def _missing(_: str) -> str:
        raise importlib.metadata.PackageNotFoundError()

    monkeypatch.setattr(importlib.metadata, "version", _missing)
    info = _version_info(None)
    assert info.app_version == "unknown"


def test_select_structure_tool_defaults() -> None:
    tool = _select_structure_tool({"predictors_enabled": []})
    assert tool.name


def test_ensure_telemetry_costs_adds_defaults(tmp_path: Path) -> None:
    context, _warnings = create_run_context(tmp_path)
    context.telemetry.cost.clear()
    _ensure_telemetry_costs(context)
    assert {"tool_units", "cpu_seconds", "gpu_seconds"} <= set(context.telemetry.cost)
