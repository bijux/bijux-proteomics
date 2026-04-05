# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Candidate update helpers from tool results."""

from __future__ import annotations

from agentic_proteins.core.tooling import InvocationInput, ToolResult
from agentic_proteins.domain.candidates.schema import Candidate, CandidateStructure


def metrics_from_outputs(outputs: list[InvocationInput]) -> dict[str, float]:
    """metrics_from_outputs."""
    metrics: dict[str, float] = {}
    for item in outputs:
        try:
            metrics[item.name] = float(item.value)
        except (TypeError, ValueError):
            continue
    return metrics


def update_candidate_from_result(
    candidate: Candidate,
    tool_name: str,
    tool_version: str,
    result: ToolResult,
    plan_fingerprint: str,
    iteration_index: int,
) -> Candidate:
    """update_candidate_from_result."""
    if result.status != "success":
        updated = candidate.model_copy(deep=True)
        updated.flags.append("tool_failure")
        return updated
    updated = candidate.model_copy(deep=True)
    outputs_map = {item.name: item.value for item in result.outputs}
    metrics = metrics_from_outputs(result.outputs)
    updated.metrics.update(metrics)
    if "mean_plddt" in metrics:
        updated.confidence = updated.confidence.model_copy(
            update={
                "structural": max(0.0, min(1.0, metrics["mean_plddt"] / 100.0)),
                "computational": max(
                    0.0, min(1.0, updated.confidence.computational or 0.0)
                ),
            }
        )
    structure = CandidateStructure(
        structure_id=f"{candidate.candidate_id}-s{len(updated.structures)}",
        provider=tool_name,
        pdb_text=outputs_map.get("pdb_text"),
        metrics={
            k: metrics[k]
            for k in ("mean_plddt", "helix_pct", "sheet_pct")
            if k in metrics
        },
        metadata={
            "plan_fingerprint": plan_fingerprint,
            "iteration_index": iteration_index,
            "tool_version": tool_version,
        },
    )
    updated.structures.append(structure)
    provenance = dict(updated.provenance)
    provenance.setdefault("iterations", []).append(
        {
            "iteration_index": iteration_index,
            "plan_fingerprint": plan_fingerprint,
            "tool": tool_name,
            "tool_version": tool_version,
        }
    )
    updated.provenance = provenance
    return updated
