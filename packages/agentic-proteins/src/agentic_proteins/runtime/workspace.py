# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run workspace layout and path management."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class RunWorkspace:
    """RunWorkspace."""

    base_dir: Path
    run_id: str
    artifacts_root_override: Path | None = None

    @classmethod
    def create(
        cls, base_dir: Path, artifacts_root_override: Path | None = None
    ) -> RunWorkspace:
        """create."""
        return cls(
            base_dir=base_dir,
            run_id=uuid4().hex,
            artifacts_root_override=artifacts_root_override,
        )

    @classmethod
    def for_run(
        cls, base_dir: Path, run_id: str, artifacts_root_override: Path | None = None
    ) -> RunWorkspace:
        """for_run."""
        return cls(
            base_dir=base_dir,
            run_id=run_id,
            artifacts_root_override=artifacts_root_override,
        )

    @property
    def artifacts_root(self) -> Path:
        """artifacts_root."""
        if self.artifacts_root_override is not None:
            return self.artifacts_root_override
        return self.base_dir / "artifacts"

    @property
    def run_dir(self) -> Path:
        """run_dir."""
        return self.artifacts_root / self.run_id

    @property
    def logs_dir(self) -> Path:
        """logs_dir."""
        return self.run_dir / "logs"

    @property
    def artifact_items_dir(self) -> Path:
        """artifact_items_dir."""
        return self.run_dir / "artifacts"

    @property
    def candidate_store_dir(self) -> Path:
        """candidate_store_dir."""
        return self.base_dir / "candidate_store"

    @property
    def config_path(self) -> Path:
        """config_path."""
        return self.run_dir / "config.json"

    @property
    def plan_path(self) -> Path:
        """plan_path."""
        return self.run_dir / "plan.json"

    @property
    def state_path(self) -> Path:
        """state_path."""
        return self.run_dir / "state.json"

    @property
    def report_path(self) -> Path:
        """report_path."""
        return self.run_dir / "report.json"

    @property
    def telemetry_path(self) -> Path:
        """telemetry_path."""
        return self.run_dir / "telemetry.json"

    @property
    def analysis_path(self) -> Path:
        """analysis_path."""
        return self.run_dir / "analysis.json"

    @property
    def execution_path(self) -> Path:
        """execution_path."""
        return self.run_dir / "execution.json"

    @property
    def timings_path(self) -> Path:
        """timings_path."""
        return self.run_dir / "timings.json"

    @property
    def run_summary_path(self) -> Path:
        """run_summary_path."""
        return self.run_dir / "run_summary.json"

    @property
    def run_output_path(self) -> Path:
        """run_output_path."""
        return self.run_dir / "run_output.json"

    @property
    def error_path(self) -> Path:
        """error_path."""
        return self.run_dir / "error.json"

    @property
    def lifecycle_path(self) -> Path:
        """lifecycle_path."""
        return self.run_dir / "lifecycle.json"

    @property
    def execution_snapshots_path(self) -> Path:
        """execution_snapshots_path."""
        return self.run_dir / "execution_snapshots.json"

    @property
    def telemetry_snapshots_path(self) -> Path:
        """telemetry_snapshots_path."""
        return self.run_dir / "telemetry_snapshots.json"

    @property
    def human_decision_path(self) -> Path:
        """human_decision_path."""
        return self.run_dir / "human_decision.json"

    @property
    def candidate_selection_path(self) -> Path:
        """candidate_selection_path."""
        return self.run_dir / "candidate_selection.json"

    def ensure_layout(self, config_payload: dict[str, Any]) -> None:
        """ensure_layout."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.artifact_items_dir.mkdir(parents=True, exist_ok=True)
        write_json_atomic(self.config_path, config_payload)
        write_json_atomic(self.plan_path, {})
        write_json_atomic(
            self.state_path,
            {
                "state_id": "state-0",
                "parent_state_id": None,
                "plan_fingerprint": "unknown",
                "timestamp": datetime.now(UTC).isoformat(),
                "agent_decisions": [],
                "artifacts": [],
                "metrics": [],
                "confidence_summary": [],
            },
        )
        write_json_atomic(self.report_path, {})
        write_json_atomic(self.telemetry_path, {})

    def validate(self) -> list[str]:
        """validate."""
        errors: list[str] = []
        if not self.run_dir.exists():
            errors.append("run_dir_missing")
        required_paths = [
            self.config_path,
            self.plan_path,
            self.state_path,
            self.report_path,
            self.telemetry_path,
        ]
        errors.extend(
            f"missing:{required.name}"
            for required in required_paths
            if not required.exists()
        )
        return errors


def write_text_atomic(path: Path, payload: str) -> None:
    """write_text_atomic."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    tmp_path.write_text(payload)
    tmp_path.replace(path)


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """write_json_atomic."""
    write_text_atomic(path, json.dumps(payload, indent=2, sort_keys=True))
