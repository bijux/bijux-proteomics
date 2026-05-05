from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.architecture.agentic_compatibility_inventory import (
    AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH,
    AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH,
    AgenticModuleClassification,
    build_agentic_compatibility_inventory,
    run,
    validate_agentic_compatibility_inventory,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_agentic_compatibility_inventory_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_agentic_compatibility_inventory_marks_every_live_module() -> None:
    entries = build_agentic_compatibility_inventory(REPO_ROOT)
    by_path = {entry.module_path: entry for entry in entries}

    assert len(entries) >= 100
    assert by_path["report/render.py"].classification is AgenticModuleClassification.WRAPPER
    assert (
        by_path["runtime/infra/capabilities.py"].classification
        is AgenticModuleClassification.WRAPPER
    )
    assert by_path["report/render.py"].owner_package == "bijux-proteomics-core"
    assert (
        by_path["domain/confidence/segments.py"].owner_package
        == "bijux-proteomics-intelligence"
    )
    assert by_path["registry/__init__.py"].classification is AgenticModuleClassification.WRAPPER
    assert by_path["validation/__init__.py"].classification is AgenticModuleClassification.WRAPPER
    assert AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH.exists()
    assert AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH.exists()


def test_agentic_compatibility_inventory_rejects_non_wrapper_logic() -> None:
    issues = validate_agentic_compatibility_inventory(REPO_ROOT)
    assert issues == ()


def test_agentic_compatibility_inventory_summary_tracks_direct_wrapper_counts() -> None:
    summary_text = AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH.read_text(
        encoding="utf-8"
    )
    assert "direct compat-to-compat import hops remaining: 0" in summary_text
    assert "wrapper modules with local definitions remaining: 0" in summary_text
