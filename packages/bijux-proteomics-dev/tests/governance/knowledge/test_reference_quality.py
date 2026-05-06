from __future__ import annotations

from bijux_proteomics_dev.governance.knowledge.reference_quality import (
    KNOWLEDGE_ORPHAN_REFERENCES_PATH,
    KNOWLEDGE_PROVENANCE_COMPLETENESS_PATH,
    KNOWLEDGE_UNDER_CURATED_WORKFLOWS_PATH,
    build_knowledge_orphan_reference_report,
    build_knowledge_provenance_completeness_report,
    build_knowledge_under_curated_workflow_report,
    run,
)


def test_knowledge_reference_quality_reports_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_knowledge_provenance_completeness_is_full_for_current_reference_surfaces() -> None:
    entries = build_knowledge_provenance_completeness_report()

    assert KNOWLEDGE_PROVENANCE_COMPLETENESS_PATH.exists()
    assert {entry.surface_name for entry in entries} == {
        "benchmarks",
        "citations",
        "contexts",
        "corpora",
        "known_problems",
        "literature_groups",
        "narratives",
        "ontology_mappings",
        "scientific_rules",
    }
    assert all(entry.complete_entry_count == entry.entry_count for entry in entries)
    assert all(entry.incomplete_entry_ids == () for entry in entries)


def test_knowledge_under_curated_workflow_report_captures_current_shallow_families() -> (
    None
):
    entries = build_knowledge_under_curated_workflow_report()
    reasons_by_family = {
        entry.workflow_family: set(entry.under_curated_reasons)
        for entry in entries
        if entry.under_curated_reasons
    }

    assert KNOWLEDGE_UNDER_CURATED_WORKFLOWS_PATH.exists()
    assert reasons_by_family == {}


def test_knowledge_orphan_reference_report_records_current_usage_gaps() -> None:
    entries = build_knowledge_orphan_reference_report()
    orphan_ids_by_surface = {entry.surface_name: entry.orphan_ids for entry in entries}

    assert KNOWLEDGE_ORPHAN_REFERENCES_PATH.exists()
    assert orphan_ids_by_surface["citations"] == ()
    assert orphan_ids_by_surface["benchmarks"] == ()
    assert orphan_ids_by_surface["corpora"] == ()
    assert orphan_ids_by_surface["scientific_context"] == ()
    assert orphan_ids_by_surface["known_problems"] == ()
    assert orphan_ids_by_surface["literature_groups"] == ()
    assert orphan_ids_by_surface["scientific_rules"] == ()
