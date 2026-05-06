from __future__ import annotations

from bijux_proteomics_dev.docs.governance.topology_references import (
    DOCS_TOPOLOGY_REFERENCES_PATH,
    build_docs_topology_reference_report,
    run,
    validate_docs_topology_references,
)


def test_docs_topology_reference_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_docs_topology_reference_report_keeps_live_imports_and_owner_paths() -> None:
    report = build_docs_topology_reference_report()

    assert DOCS_TOPOLOGY_REFERENCES_PATH.exists()
    assert report.entries == ()
    assert report.guard.max_total_violation_count == 0


def test_docs_topology_reference_release_guard_has_no_failures() -> None:
    assert validate_docs_topology_references() == ()
