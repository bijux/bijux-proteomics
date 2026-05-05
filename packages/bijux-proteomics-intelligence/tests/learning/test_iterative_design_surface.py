from __future__ import annotations

from bijux_proteomics_intelligence.learning.iterative_design.convergence import (
    is_convergence_failure,
)
from bijux_proteomics_intelligence.learning.iterative_design.stagnation import (
    update_stagnation_count,
)


def test_iterative_design_helpers_smoke() -> None:
    assert is_convergence_failure(["stagnation"]) is True
    assert update_stagnation_count(1, 0.01, 0.1) == 2
