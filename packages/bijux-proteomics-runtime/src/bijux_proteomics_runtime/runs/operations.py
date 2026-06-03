# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned public operations for CLI and API entrypoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from bijux_proteomics_runtime.runs.run_config import RunConfig
from bijux_proteomics_runtime.support.workspace import RunWorkspace

if TYPE_CHECKING:
    from bijux_proteomics_intelligence.candidates import CandidateStore
    from bijux_proteomics_intelligence.candidates.schema import Candidate
    from bijux_proteomics_runtime.runs.artifacts import RunComparisonReport
    from bijux_proteomics_runtime.runs.manager import RunManager

_PROVIDER_MAP: dict[str | None, list[str]] = {
    None: ["heuristic_proxy"],
    "esmfold": ["local_esmfold"],
    "local_esmfold": ["local_esmfold"],
    "rosettafold": ["local_rosettafold"],
    "local_rosettafold": ["local_rosettafold"],
    "openprotein": ["api_openprotein_esmfold"],
}


def _candidate_store_type() -> type[CandidateStore]:
    """Load the runtime candidate store only when a candidate workflow needs it."""
    from bijux_proteomics_intelligence.candidates import CandidateStore

    return CandidateStore


def _compare_runs_operation() -> Callable[[Path, Path], RunComparisonReport]:
    """Load the runtime comparison helper only for explicit compare requests."""
    from bijux_proteomics_runtime.runs.artifacts import compare_runs

    return compare_runs


def _run_manager_type() -> type[RunManager]:
    """Load the runtime manager only when a run-bearing operation is invoked."""
    from bijux_proteomics_runtime.runs.manager import RunManager

    return RunManager


def build_runtime_run_config(
    *,
    rounds: int,
    dry_run: bool,
    logging_enabled: bool,
    provider: str | None,
    artifacts_dir: Path | None,
    execution_mode: str,
    launch_surface: str = "local",
) -> RunConfig:
    """Build one canonical runtime run config for CLI and API entrypoints."""
    if rounds < 1:
        raise ValueError("--rounds must be >= 1")
    if provider not in _PROVIDER_MAP:
        raise ValueError(
            "--provider must be one of: esmfold, local_esmfold, rosettafold, local_rosettafold, openprotein"
        )
    resource_limits = {"cpu_seconds": 0.0, "gpu_seconds": 0.0}
    if provider in {"esmfold", "rosettafold"}:
        resource_limits["gpu_seconds"] = 1.0
    return RunConfig(
        dry_run=dry_run,
        logging_enabled=logging_enabled,
        loop_max_iterations=rounds,
        predictors_enabled=_PROVIDER_MAP[provider],
        resource_limits=resource_limits,
        artifacts_dir=str(artifacts_dir) if artifacts_dir else None,
        execution_mode=execution_mode,
        launch_surface=launch_surface,
    )


def run_sequence_operation(
    base_dir: Path, sequence: str, config: RunConfig
) -> dict[str, Any]:
    """Run one sequence through the canonical runtime manager."""
    return _run_manager_type()(base_dir, config).run(sequence)


def resume_candidate_operation(
    base_dir: Path,
    *,
    candidate_id: str,
    rounds: int,
    provider: str | None,
    artifacts_dir: Path | None,
    execution_mode: str,
) -> dict[str, Any]:
    """Resume one runtime candidate through the canonical runtime manager."""
    store = _candidate_store_type()(
        RunWorkspace.for_run(base_dir, "noop").candidate_store_dir
    )
    candidate = store.get_candidate(candidate_id)
    config = build_runtime_run_config(
        rounds=rounds,
        dry_run=False,
        logging_enabled=True,
        provider=provider,
        artifacts_dir=artifacts_dir,
        execution_mode=execution_mode,
    )
    return _run_manager_type()(base_dir, config).run_candidate(candidate)


def import_external_result_operation(
    base_dir: Path,
    *,
    sequence: str,
    source_path: Path,
    engine_name: str,
    engine_version: str,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    """Import one external-engine result through the canonical runtime manager."""
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    imported_payload = payload if isinstance(payload, dict) else {"items": payload}
    config = RunConfig(artifacts_dir=str(artifacts_dir) if artifacts_dir else None)
    return _run_manager_type()(base_dir, config).import_result(
        sequence=sequence,
        source_path=source_path,
        imported_payload=imported_payload,
        engine_name=engine_name,
        engine_version=engine_version,
    )


def compare_run_operation(run_a: Path, run_b: Path) -> dict[str, Any]:
    """Compare two runtime runs through the canonical runtime control surface."""
    return _compare_runs_operation()(run_a, run_b).model_dump(mode="json")


def inspect_candidate_operation(base_dir: Path, candidate_id: str) -> Candidate:
    """Load one candidate through the canonical runtime candidate store."""
    store = _candidate_store_type()(
        RunWorkspace.for_run(base_dir, "noop").candidate_store_dir
    )
    return store.get_candidate(candidate_id)


def load_run_summary_operation(
    base_dir: Path, run_id: str, artifacts_dir: Path | None
) -> dict[str, Any]:
    """Load one canonical run summary."""
    workspace = RunWorkspace.for_run(
        base_dir,
        run_id,
        artifacts_root_override=artifacts_dir,
    )
    payload = json.loads(workspace.run_summary_path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def load_run_config_operation(run_dir: Path) -> RunConfig:
    """Load one canonical run config from disk."""
    config_path = run_dir / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found at {config_path}")
    return RunConfig.model_validate(json.loads(config_path.read_text(encoding="utf-8")))


def export_report_operation(base_dir: Path, run_id: str) -> str:
    """Load one runtime report payload from disk."""
    report_path = RunWorkspace.for_run(base_dir, run_id).report_path
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found at {report_path}")
    return report_path.read_text(encoding="utf-8")


__all__ = [
    "build_runtime_run_config",
    "compare_run_operation",
    "export_report_operation",
    "import_external_result_operation",
    "inspect_candidate_operation",
    "load_run_config_operation",
    "load_run_summary_operation",
    "resume_candidate_operation",
    "run_sequence_operation",
]
