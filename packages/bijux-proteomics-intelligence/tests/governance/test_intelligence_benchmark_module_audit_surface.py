from __future__ import annotations

from pathlib import Path

from bijux_proteomics_intelligence.governance.charter import (
    DEFAULT_INTELLIGENCE_MODULE_AUDIT,
    IntelligenceCharterCapability,
    IntelligenceModuleClassification,
)

INTELLIGENCE_SRC_ROOT = Path(
    "packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence"
)


def test_benchmark_module_audit_marks_review_owner_as_analytical_value() -> None:
    benchmark_entry = next(
        entry
        for entry in DEFAULT_INTELLIGENCE_MODULE_AUDIT
        if entry.module_path == "reviews/benchmarks.py"
    )

    assert (
        benchmark_entry.classification
        is IntelligenceModuleClassification.ANALYTICAL_VALUE
    )
    assert benchmark_entry.anchor_capabilities == (
        IntelligenceCharterCapability.REVIEW_REASONING,
    )


def test_benchmark_module_audit_points_to_live_owner_module() -> None:
    benchmark_path = INTELLIGENCE_SRC_ROOT / "reviews/benchmarks.py"

    assert benchmark_path.exists()
    assert benchmark_path.read_text(encoding="utf-8")
