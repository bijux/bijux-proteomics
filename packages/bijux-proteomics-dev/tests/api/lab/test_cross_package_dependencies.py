from __future__ import annotations

from bijux_proteomics_dev.api.lab.cross_package_dependencies import (
    LAB_CROSS_PACKAGE_DEPENDENCIES_PATH,
    build_lab_cross_package_dependency_report,
    run,
    validate_lab_cross_package_dependencies,
)


def test_lab_cross_package_dependency_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_lab_cross_package_dependency_report_tracks_live_edges() -> None:
    report = build_lab_cross_package_dependency_report()
    importers = {entry.importer_module_path for entry in report.entries}
    owner_counts = {
        owner_distribution: sum(
            1
            for entry in report.entries
            if entry.owner_distribution == owner_distribution
        )
        for owner_distribution in {
            "bijux-proteomics-core",
            "bijux-proteomics-foundation",
            "bijux-proteomics-intelligence",
            "bijux-proteomics-knowledge",
            "bijux-proteomics-runtime",
        }
    }

    assert LAB_CROSS_PACKAGE_DEPENDENCIES_PATH.exists()
    assert "planning/assays.py" in importers
    assert "readiness/stages.py" in importers
    assert "outcomes/observations.py" in importers
    assert "benchmarks/claims.py" in importers
    assert owner_counts["bijux-proteomics-core"] == report.guard.max_core_edges
    assert (
        owner_counts["bijux-proteomics-foundation"]
        == report.guard.max_foundation_edges
    )
    assert (
        owner_counts["bijux-proteomics-intelligence"]
        == report.guard.max_intelligence_edges
    )
    assert (
        owner_counts["bijux-proteomics-knowledge"]
        == report.guard.max_knowledge_edges
    )
    assert owner_counts["bijux-proteomics-runtime"] == report.guard.max_runtime_edges


def test_lab_cross_package_dependency_guard_has_no_failures() -> None:
    assert validate_lab_cross_package_dependencies() == ()
