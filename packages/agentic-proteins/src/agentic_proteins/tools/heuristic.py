# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Heuristic structure tool for proxy analysis."""

from __future__ import annotations

from agentic_proteins.providers.factory import create_provider
from agentic_proteins.providers.heuristic import HeuristicStructureProvider
from agentic_proteins.tools.base import Tool
from agentic_proteins.tools.schemas import InvocationInput, ToolMetric, ToolResult


class HeuristicStructureTool(Tool):
    """HeuristicStructureTool."""

    name = HeuristicStructureProvider.name
    version = "v1"

    def __init__(self, provider_name: str | None = None) -> None:
        """__init__."""
        self._provider_name = provider_name or self.name
        self.name = self._provider_name

    def run(self, invocation_id: str, inputs: list[InvocationInput]) -> ToolResult:
        """run."""
        payload = self._inputs_to_dict(inputs)
        sequence = payload.get("sequence", "")
        if payload.get("mode") == "fail":
            return self._error_result(invocation_id, "forced_failure")
        if not sequence:
            return self._error_result(invocation_id, "missing_sequence")

        provider = create_provider(self._provider_name)
        prediction = provider.predict(sequence, seed=None)
        raw = prediction.raw or {}

        outputs = [
            InvocationInput(
                name="sequence_length",
                value=str(raw.get("sequence_length", len(sequence))),
            ),
            InvocationInput(
                name="mean_plddt", value=f"{float(raw.get('mean_plddt', 0.0)):.2f}"
            ),
            InvocationInput(
                name="helix_pct", value=f"{float(raw.get('helix_pct', 0.0)):.2f}"
            ),
            InvocationInput(
                name="sheet_pct", value=f"{float(raw.get('sheet_pct', 0.0)):.2f}"
            ),
        ]
        if prediction.pdb_text:
            outputs.append(InvocationInput(name="pdb_text", value=prediction.pdb_text))
        metrics = [ToolMetric(name="latency_ms", value=1.0, unit="ms")]
        return ToolResult(
            invocation_id=invocation_id,
            tool_name=self._provider_name,
            status="success",
            outputs=outputs,
            metrics=metrics,
            error=None,
        )
