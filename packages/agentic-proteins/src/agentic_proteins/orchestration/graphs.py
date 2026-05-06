"""Compatibility execution-graph validation entrypoints."""

from bijux_proteomics_runtime.execution.graph_validation import (
    validate_execution_graph,
    validate_state_snapshot,
)

__all__ = ["validate_execution_graph", "validate_state_snapshot"]
