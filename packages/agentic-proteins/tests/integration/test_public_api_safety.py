# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from agentic_proteins.runtime import RunManager
from agentic_proteins.runtime.infra import RunConfig


def test_public_api_dry_run(tmp_path: Path) -> None:
    config = RunConfig(dry_run=True, logging_enabled=False)
    manager = RunManager(tmp_path, config)
    result = manager.run("ACDE")
    assert result["run_id"]
    assert result["status"] in {"partial", "success", "failure"}
