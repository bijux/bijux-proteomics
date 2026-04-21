from __future__ import annotations

from bijux_proteomics.execution_contracts import CandidateLike, ExecutionIteration, ToolResultLike


def test_execution_contract_symbols_are_importable() -> None:
    assert CandidateLike is not None
    assert ExecutionIteration is not None
    assert ToolResultLike is not None
