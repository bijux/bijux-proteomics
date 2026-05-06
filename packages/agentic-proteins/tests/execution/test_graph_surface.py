# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from agentic_proteins.execution.graphs import (
    validate_execution_graph,
    validate_state_snapshot,
)
from bijux_proteomics_runtime.execution.graph_validation import (
    validate_execution_graph as runtime_validate_execution_graph,
    validate_state_snapshot as runtime_validate_state_snapshot,
)


def test_graph_validation_surface_forwards_to_runtime_symbols() -> None:
    assert validate_execution_graph is runtime_validate_execution_graph
    assert validate_state_snapshot is runtime_validate_state_snapshot
