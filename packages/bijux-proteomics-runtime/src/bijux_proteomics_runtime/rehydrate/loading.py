# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned loading of completed run directories into archived study results."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import ProteomicsStudyResult
from bijux_proteomics.workflow.exports import load_result_archive


def load_completed_run(run_dir: Path) -> ProteomicsStudyResult:
    """Load one completed runtime run directory into a queryable study result."""

    manifest_path = _resolve_completed_run_manifest(run_dir)
    return load_result_archive(manifest_path)


def _resolve_completed_run_manifest(run_dir: Path) -> Path:
    if not run_dir.exists():
        raise ValueError(f"completed run directory does not exist: {run_dir}")
    if run_dir.is_file():
        raise ValueError(
            "completed run rehydration requires a run directory, not a file path"
        )

    candidates = (
        run_dir / "result_manifest.json",
        run_dir / "archive" / "result_manifest.json",
        run_dir / "artifacts" / "result_manifest.json",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise ValueError(
        "completed run rehydration requires result_manifest.json in the run directory "
        "root, archive/, or artifacts/"
    )


__all__ = ["load_completed_run"]
