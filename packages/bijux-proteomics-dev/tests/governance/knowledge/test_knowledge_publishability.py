from __future__ import annotations

from bijux_proteomics_dev.governance.knowledge.publishability import (
    KNOWLEDGE_PUBLISHABILITY_PATH,
    build_knowledge_publishability_report,
    run,
    validate_knowledge_publishability,
)


def test_knowledge_publishability_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_knowledge_publishability_requires_dense_selective_memory() -> None:
    report = build_knowledge_publishability_report()

    assert KNOWLEDGE_PUBLISHABILITY_PATH.exists()
    assert report.total_public_surface_count == 15
    assert report.query_helper_count == 1
    assert report.curated_registry_entry_count >= 60
    assert report.curated_entries_per_public_surface >= 4.0
    assert report.provenance_complete_surface_count == 9
    assert report.under_curated_workflow_count == 0
    assert report.orphan_reference_count == 0
    assert report.breadth_ready is True
    assert report.publishable is True


def test_knowledge_publishability_release_guard_has_no_failures() -> None:
    assert validate_knowledge_publishability() == ()
