from __future__ import annotations

from bijux_proteomics_dev.api.knowledge.boundary_drift import (
    KNOWLEDGE_BOUNDARY_DRIFT_PATH,
    build_knowledge_boundary_drift_report,
    run,
    validate_knowledge_boundary_drift,
)


def test_knowledge_boundary_drift_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_knowledge_boundary_drift_report_stays_empty() -> None:
    report = build_knowledge_boundary_drift_report()

    assert KNOWLEDGE_BOUNDARY_DRIFT_PATH.exists()
    assert report.forbidden_module_paths == ()
    assert report.forbidden_import_edges == ()
    assert report.forbidden_definition_names == ()


def test_knowledge_boundary_drift_release_guard_has_no_failures() -> None:
    assert validate_knowledge_boundary_drift() == ()
