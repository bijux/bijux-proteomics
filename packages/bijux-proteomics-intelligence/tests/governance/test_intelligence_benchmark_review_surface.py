from __future__ import annotations

from bijux_proteomics_intelligence.governance.charter import (
    DEFAULT_INTELLIGENCE_CHARTER,
)


def test_benchmark_review_boundary_keeps_truth_and_execution_outside_intelligence() -> (
    None
):
    assert "knowledge-owned evidence bundles and references" in (
        DEFAULT_INTELLIGENCE_CHARTER.required_inputs
    )
    assert "runtime execution and artifact transport" in (
        DEFAULT_INTELLIGENCE_CHARTER.excluded_ownership
    )
