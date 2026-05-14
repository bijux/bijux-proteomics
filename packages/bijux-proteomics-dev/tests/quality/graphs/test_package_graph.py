from __future__ import annotations

from pathlib import Path

from bijux_proteomics_dev.quality.graphs.package_graph import (
    build_workspace_package_graph,
    load_workspace_packages,
)

REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "packages").is_dir() and (parent / "configs").is_dir()
)


def test_workspace_packages_load_expected_import_roots() -> None:
    packages = {
        package.package_name: package for package in load_workspace_packages(REPO_ROOT)
    }

    assert packages["bijux-proteomics-core"].import_root == "bijux_proteomics"
    assert packages["agentic-proteins"].import_root == "agentic_proteins"
    assert packages["bijux-proteomics-foundation"].workspace_dependencies == ()


def test_workspace_package_graph_tracks_declared_dependencies() -> None:
    graph = build_workspace_package_graph(REPO_ROOT)

    assert "bijux-proteomics-core" in graph.direct_dependencies_of(
        "bijux-proteomics-runtime"
    )
    assert "bijux-proteomics-runtime" in graph.reverse_dependencies_of(
        "bijux-proteomics-core"
    )
    assert "bijux-proteomics-knowledge" not in graph.direct_dependencies_of(
        "bijux-proteomics-core"
    )
