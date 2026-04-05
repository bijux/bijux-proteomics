from __future__ import annotations

from agentic_proteins.design_loop.stagnation import update_stagnation_count


def test_update_stagnation_count_increments_and_resets() -> None:
    assert update_stagnation_count(1, improvement_delta=0.01, threshold=0.1) == 2
    assert update_stagnation_count(2, improvement_delta=0.5, threshold=0.1) == 0
