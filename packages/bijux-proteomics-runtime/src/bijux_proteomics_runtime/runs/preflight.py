# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Environment preflight checks for runtime execution."""

from __future__ import annotations

from enum import StrEnum
import json
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.providers.catalog import provider_requirements
from bijux_proteomics_runtime.support.workspace import RunWorkspace, write_json_atomic


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
    source_path: Path | None = None,
    required_tool_versions: dict[str, str] | None = None,
    available_tool_versions: dict[str, str] | None = None,
) -> RuntimePreflightReport:
    """Build a runtime preflight report before execution starts."""
    checks: list[PreflightCheck] = []
    workspace_errors = tuple(workspace.validate())
    checks.append(
        PreflightCheck(
            check_id="workspace_layout",
            state=(
                PreflightCheckState.FAIL
                if workspace_errors
                else PreflightCheckState.PASS
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
                PreflightCheckState.FAIL
                if provider_errors
                else PreflightCheckState.PASS
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
    if source_path is not None:
        dataset_exists = source_path.exists() and source_path.is_file()
        checks.append(
            PreflightCheck(
                check_id="source_dataset",
                state=(
                    PreflightCheckState.PASS
                    if dataset_exists
                    else PreflightCheckState.FAIL
                ),
                message=(
                    "source dataset is available"
                    if dataset_exists
                    else "source dataset is missing"
                ),
                detail_codes=() if dataset_exists else ("source_dataset_missing",),
            )
        )
        if dataset_exists:
            try:
                if source_path.suffix.lower() in {".tsv", ".csv"}:
                    header = source_path.read_text(encoding="utf-8").splitlines()[:1]
                    layout_valid = bool(header and header[0].strip())
                else:
                    payload = json.loads(source_path.read_text(encoding="utf-8"))
                    layout_valid = isinstance(payload, (dict, list))
            except json.JSONDecodeError:
                layout_valid = False
            checks.append(
                PreflightCheck(
                    check_id="source_dataset_layout",
                    state=(
                        PreflightCheckState.PASS
                        if layout_valid
                        else PreflightCheckState.FAIL
                    ),
                    message=(
                        "source dataset layout is valid"
                        if layout_valid
                        else "source dataset layout is invalid"
                    ),
                    detail_codes=()
                    if layout_valid
                    else ("source_dataset_layout_invalid",),
                )
            )
    required_versions = required_tool_versions or {}
    available_versions = available_tool_versions or {}
    version_mismatches = tuple(
        f"{tool_name}:expected={expected}:actual={available_versions.get(tool_name, 'missing')}"
        for tool_name, expected in sorted(required_versions.items())
        if available_versions.get(tool_name) != expected
    )
    if required_versions:
        checks.append(
            PreflightCheck(
                check_id="tool_versions",
                state=(
                    PreflightCheckState.PASS
                    if not version_mismatches
                    else PreflightCheckState.FAIL
                ),
                message=(
                    "tool versions match runtime expectations"
                    if not version_mismatches
                    else "tool versions do not match runtime expectations"
                ),
                detail_codes=version_mismatches,
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
