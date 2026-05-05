# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Environment preflight checks for runtime execution."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.providers.factory import provider_requirements
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace, write_json_atomic


class PreflightCheckState(StrEnum):
    """Allowed states for one runtime preflight check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class PreflightCheck(JsonModel):
    """One runtime preflight check result."""

    model_config = ConfigDict(extra="forbid")

    check_id: str = Field(..., min_length=1)
    state: PreflightCheckState
    message: str = Field(..., min_length=1)
    detail_codes: tuple[str, ...] = Field(default_factory=tuple)


class RuntimePreflightReport(JsonModel):
    """Machine-readable preflight report for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    provider_name: str = Field(..., min_length=1)
    passed: bool
    checks: tuple[PreflightCheck, ...] = Field(default_factory=tuple)


def build_runtime_preflight_report(
    workspace: RunWorkspace,
    *,
    run_id: str,
    provider_name: str,
) -> RuntimePreflightReport:
    """Build a runtime preflight report before execution starts."""
    checks: list[PreflightCheck] = []
    workspace_errors = tuple(workspace.validate())
    checks.append(
        PreflightCheck(
            check_id="workspace_layout",
            state=(
                PreflightCheckState.FAIL if workspace_errors else PreflightCheckState.PASS
            ),
            message=(
                "workspace layout is ready"
                if not workspace_errors
                else "workspace layout is missing required runtime files"
            ),
            detail_codes=workspace_errors,
        )
    )
    provider_errors = tuple(provider_requirements(provider_name))
    checks.append(
        PreflightCheck(
            check_id="provider_requirements",
            state=(
                PreflightCheckState.FAIL if provider_errors else PreflightCheckState.PASS
            ),
            message=(
                "provider requirements are available"
                if not provider_errors
                else "provider requirements are missing"
            ),
            detail_codes=provider_errors,
        )
    )
    candidate_store_ready = workspace.candidate_store_dir.parent.exists()
    checks.append(
        PreflightCheck(
            check_id="candidate_store_root",
            state=(
                PreflightCheckState.PASS
                if candidate_store_ready
                else PreflightCheckState.FAIL
            ),
            message=(
                "candidate store root is available"
                if candidate_store_ready
                else "candidate store root is unavailable"
            ),
            detail_codes=()
            if candidate_store_ready
            else ("workspace_candidate_store_root_missing",),
        )
    )
    return RuntimePreflightReport(
        run_id=run_id,
        provider_name=provider_name,
        passed=all(check.state is not PreflightCheckState.FAIL for check in checks),
        checks=tuple(checks),
    )


def write_runtime_preflight_report(
    workspace: RunWorkspace,
    report: RuntimePreflightReport,
) -> None:
    """Persist a runtime preflight report."""
    write_json_atomic(workspace.preflight_report_path, report.to_dict())


__all__ = [
    "PreflightCheck",
    "PreflightCheckState",
    "RuntimePreflightReport",
    "build_runtime_preflight_report",
    "write_runtime_preflight_report",
]
