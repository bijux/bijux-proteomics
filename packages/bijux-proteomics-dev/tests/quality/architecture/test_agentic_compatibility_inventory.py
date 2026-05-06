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

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_agentic_compatibility_inventory_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_agentic_compatibility_inventory_marks_every_live_module() -> None:
    entries = build_agentic_compatibility_inventory(REPO_ROOT)
    by_path = {entry.module_path: entry for entry in entries}

    assert len(entries) == 116
    assert "sandbox/__init__.py" not in by_path
    assert "design_loop/loop.py" not in by_path
    assert "domain/sequence/summary.py" not in by_path
    assert "registry/agents.py" not in by_path
    assert (
        by_path["interfaces/http/app.py"].classification
        is AgenticModuleClassification.WRAPPER
    )
    assert (
        by_path["execution/manager.py"].classification
        is AgenticModuleClassification.WRAPPER
    )
    assert (
        by_path["orchestration/manager.py"].classification
        is AgenticModuleClassification.WRAPPER
    )
    assert (
        by_path["providers/capabilities.py"].classification
        is AgenticModuleClassification.WRAPPER
    )
    assert (
        by_path["interfaces/structure_reports.py"].owner_package
        == "bijux-proteomics-core"
    )
    assert by_path["state/context.py"].owner_package == "bijux-proteomics-runtime"
    assert (
        by_path["agents/coordination/coordinator.py"].owner_package
        == "bijux-proteomics-runtime"
    )
    assert (
        by_path["providers/remote/openprotein.py"].owner_package
        == "bijux-proteomics-runtime"
    )
    assert (
        by_path["agents/catalog.py"].classification
        is AgenticModuleClassification.WRAPPER
    )
    assert (
        by_path["tools/contracts.py"].classification
        is AgenticModuleClassification.WRAPPER
    )
    assert AGENTIC_COMPATIBILITY_INVENTORY_CSV_PATH.exists()
    assert AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH.exists()


def test_agentic_compatibility_inventory_rejects_non_wrapper_logic() -> None:
    issues = validate_agentic_compatibility_inventory(REPO_ROOT)
    assert issues == ()


def test_agentic_compatibility_inventory_summary_tracks_direct_wrapper_counts() -> None:
    summary_text = AGENTIC_COMPATIBILITY_INVENTORY_SUMMARY_PATH.read_text(
        encoding="utf-8"
    )
    assert "`bijux-proteomics-foundation`: 0" in summary_text
    assert "`bijux-proteomics-knowledge`: 0" in summary_text
    assert "`bijux-proteomics-lab`: 0" in summary_text
    assert "direct compat-to-compat import hops remaining: 0" in summary_text
    assert "wrapper modules with local definitions remaining: 0" in summary_text
