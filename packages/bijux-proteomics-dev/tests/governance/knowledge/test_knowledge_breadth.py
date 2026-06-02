from __future__ import annotations

from bijux_proteomics_dev.governance.knowledge.breadth import (
    KNOWLEDGE_BREADTH_PATH,
    build_knowledge_breadth_report,
    run,
    validate_knowledge_breadth,
)


def test_knowledge_breadth_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_knowledge_breadth_keeps_menu_surface_narrow_relative_to_curation_depth() -> (
    None
):
    report = build_knowledge_breadth_report()
    metrics = report.metrics

    assert KNOWLEDGE_BREADTH_PATH.exists()
    assert metrics.root_public_symbol_count == 61
    assert metrics.references_public_symbol_count == 10
    assert metrics.total_public_surface_count == 71
    assert metrics.query_helper_count == 1
    assert metrics.curated_registry_entry_count >= 60
    assert metrics.curated_entries_per_public_surface >= 1.27
    assert metrics.curated_entries_per_query_helper >= 60.0


def test_knowledge_breadth_release_guard_has_no_failures() -> None:
    assert validate_knowledge_breadth() == ()
