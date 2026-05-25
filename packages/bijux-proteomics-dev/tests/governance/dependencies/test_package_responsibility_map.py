from __future__ import annotations

from bijux_proteomics_dev.governance.dependencies.package_responsibility_map import (
    build_package_responsibility_map_report,
    validate_package_responsibility_map,
)


def test_package_responsibility_map_covers_workspace_packages_and_roles() -> None:
    report = build_package_responsibility_map_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}

    assert len(report.entries) == 16
    assert report.guard.max_foundation_higher_package_edges == 0
    assert report.guard.max_knowledge_runtime_edges == 0
    assert report.guard.max_core_cli_edges == 0
    assert by_package["bijux-proteomics-foundation"].responsibility_kind == (
        "foundation"
    )
    assert by_package["bijux-proteomics-core"].responsibility_kind == "core"
    assert by_package["bijux-proteomics-runtime"].responsibility_kind == "runtime"
    assert (
        by_package["bijux-proteomics-intelligence"].responsibility_kind
        == "intelligence"
    )
    assert by_package["bijux-proteomics-knowledge"].responsibility_kind == (
        "knowledge"
    )
    assert by_package["bijux-proteomics-lab"].responsibility_kind == "lab"
    assert by_package["bijux-proteomics"].responsibility_kind == "app_wrapper"
    assert by_package["agentic-proteins"].responsibility_kind == (
        "compatibility_bridge"
    )
    assert by_package["proteomics-core"].canonical_surface_targets == (
        "bijux-proteomics-core",
    )
    assert "shared document primitives" in by_package[
        "bijux-proteomics-foundation"
    ].reason_to_exist
    assert "scientific semantics" in by_package["bijux-proteomics-core"].reason_to_exist
    assert "evidence memory" in by_package[
        "bijux-proteomics-knowledge"
    ].reason_to_exist


def test_package_responsibility_map_has_no_live_boundary_violations() -> None:
    assert validate_package_responsibility_map() == ()
