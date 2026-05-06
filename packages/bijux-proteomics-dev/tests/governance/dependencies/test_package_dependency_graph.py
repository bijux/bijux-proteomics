from __future__ import annotations

from bijux_proteomics_dev.governance.dependencies.package_dependency_graph import (
    PACKAGE_DEPENDENCY_GRAPH_PATH,
    build_package_dependency_graph_report,
    run,
    validate_package_dependency_graph,
)


def test_package_dependency_graph_report_is_up_to_date() -> None:
    assert run(check=True) == 0


def test_package_dependency_graph_report_tracks_live_workspace_edges() -> None:
    report = build_package_dependency_graph_report()
    by_edge = {
        (entry.source_distribution, entry.target_distribution): entry
        for entry in report.entries
    }

    assert PACKAGE_DEPENDENCY_GRAPH_PATH.exists()
    assert ("bijux-proteomics-runtime", "bijux-proteomics-core") in by_edge
    assert ("bijux-proteomics-intelligence", "bijux-proteomics-knowledge") in by_edge
    assert ("bijux-proteomics-foundation", "bijux-proteomics-core") not in by_edge
    assert report.guard.max_total_edges == len(report.entries)


def test_package_dependency_graph_release_guard_has_no_failures() -> None:
    assert validate_package_dependency_graph() == ()
