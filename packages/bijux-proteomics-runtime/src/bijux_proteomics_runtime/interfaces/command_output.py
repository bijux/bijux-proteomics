# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable script-safe command output contracts."""

from __future__ import annotations

import json

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ScriptSafeOutputField(JsonModel):
    """One deterministic JSON field for script-safe command outputs."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)


class ScriptSafeCommandOutput(JsonModel):
    """Stable script-safe JSON output envelope with concise human summary."""

    model_config = ConfigDict(extra="forbid")

    command: str = Field(..., min_length=1)
    schema_ref: str = Field(..., min_length=1)
    json_output: str = Field(..., min_length=1)
    human_output: str = Field(..., min_length=1)
    warnings: tuple[str, ...] = Field(default_factory=tuple)


def build_script_safe_command_output(
    command: str,
    fields: tuple[ScriptSafeOutputField, ...],
    *,
    warnings: tuple[str, ...] = (),
) -> ScriptSafeCommandOutput:
    """Render deterministic JSON output and concise human output for major commands."""

    payload = {
        field.key: field.value for field in sorted(fields, key=lambda entry: entry.key)
    }
    json_output = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    human_output = (
        f"{command}: {', '.join(f'{key}={value}' for key, value in payload.items())}"
    )
    return ScriptSafeCommandOutput(
        command=command,
        schema_ref="api.script-safe-command-output.v1",
        json_output=json_output,
        human_output=human_output,
        warnings=warnings,
    )


__all__ = [
    "ScriptSafeCommandOutput",
    "ScriptSafeOutputField",
    "build_script_safe_command_output",
]
