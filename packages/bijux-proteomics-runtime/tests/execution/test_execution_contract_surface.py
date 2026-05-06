from __future__ import annotations

from bijux_proteomics.interfaces.execution.contracts import (
    CandidateLike,
    ExecutionToolResultLike,
    ExecutionIteration,
)


def test_execution_contract_symbols_are_importable() -> None:
    assert CandidateLike is not None
    assert ExecutionIteration is not None
    assert ExecutionToolResultLike is not None
