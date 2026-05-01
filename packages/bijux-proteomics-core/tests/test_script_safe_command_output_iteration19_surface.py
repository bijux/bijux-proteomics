# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.product_api_iteration19 import (
    ScriptSafeOutputField,
    build_script_safe_command_output,
)


def test_build_script_safe_command_output_emits_deterministic_json() -> None:
    report = build_script_safe_command_output(
        "workflow run",
        (
            ScriptSafeOutputField(key="status", value="completed"),
            ScriptSafeOutputField(key="run_id", value="run-77"),
        ),
        warnings=("used cached artifacts",),
    )

    assert report.schema_ref == "api.script-safe-command-output.v1"
    assert report.json_output == '{"run_id":"run-77","status":"completed"}'
    assert report.human_output == "workflow run: run_id=run-77, status=completed"
    assert report.warnings == ("used cached artifacts",)
