# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path


def assert_valid_run_artifacts(run_dir: Path) -> dict[str, object]:
    """Validate core artifact files exist and return loaded payloads."""
    required_files = [
        "run_output.json",
        "run_summary.json",
        "telemetry.json",
        "state.json",
        "plan.json",
    ]
    for name in required_files:
        path = run_dir / name
        assert path.exists(), f"Missing artifact: {path}"

    run_output = json.loads((run_dir / "run_output.json").read_text())
    summary = json.loads((run_dir / "run_summary.json").read_text())
    telemetry = json.loads((run_dir / "telemetry.json").read_text())

    report_payload = None
    report_path = run_dir / "report.json"
    if report_path.exists():
        report_payload = json.loads(report_path.read_text())

    return {
        "run_output": run_output,
        "summary": summary,
        "telemetry": telemetry,
        "report": report_payload,
    }
