# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run context for a single execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from agentic_proteins.runtime.infra import RunConfig
from agentic_proteins.runtime.infra.observability import (
    NoopStructuredLogger,
    StructuredLogger,
)
from agentic_proteins.runtime.infra.telemetry import TelemetryClient
from agentic_proteins.runtime.workspace import RunWorkspace


@dataclass(frozen=True)
class RunContext:
    """RunContext."""

    run_id: str
    start_time: datetime
    config: dict[str, Any]
    artifact_dir: Path
    logger: StructuredLogger
    telemetry: TelemetryClient
    workspace: RunWorkspace


def create_run_context(
    base_dir: Path, config: RunConfig | None = None, run_id: str | None = None
) -> tuple[RunContext, list[str]]:
    """create_run_context."""
    run_id = run_id or uuid4().hex
    start_time = datetime.now(UTC)
    config = config or RunConfig()
    normalized, warnings = config.with_defaults()
    artifacts_override = (
        Path(normalized.artifacts_dir) if normalized.artifacts_dir else None
    )
    workspace = RunWorkspace.for_run(
        base_dir, run_id, artifacts_root_override=artifacts_override
    )
    workspace.ensure_layout(normalized.model_dump())
    logger = (
        StructuredLogger(run_id=run_id, log_path=workspace.logs_dir / "run.jsonl")
        if normalized.logging_enabled
        else NoopStructuredLogger()
    )
    telemetry = TelemetryClient(run_id=run_id, metrics_path=workspace.telemetry_path)
    return RunContext(
        run_id=run_id,
        start_time=start_time,
        config=normalized.model_dump(),
        artifact_dir=workspace.run_dir,
        logger=logger,
        telemetry=telemetry,
        workspace=workspace,
    ), warnings
