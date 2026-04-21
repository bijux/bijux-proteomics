from __future__ import annotations

from bijux_proteomics_intelligence.design_loop.convergence import is_convergence_failure
from bijux_proteomics_intelligence.design_loop.stagnation import update_stagnation_count


def test_design_loop_helpers_smoke() -> None:
    assert is_convergence_failure(["stagnation"]) is True
    assert update_stagnation_count(1, 0.01, 0.1) == 2
