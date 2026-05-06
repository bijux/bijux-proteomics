from __future__ import annotations

from bijux_proteomics_dev.governance.dependencies.module_dependency_graphs import (
    MODULE_DEPENDENCY_GRAPHS_DIR,
    build_module_dependency_graph_report,
    run,
)
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_package_names,
)


def test_module_dependency_graphs_are_up_to_date() -> None:
    assert run(check=True) == 0


def test_module_dependency_graphs_cover_every_workspace_package() -> None:
    package_names = workspace_package_names()

    assert MODULE_DEPENDENCY_GRAPHS_DIR.exists()
    assert {path.stem for path in MODULE_DEPENDENCY_GRAPHS_DIR.glob("*.toml")} == set(
        package_names
    )


def test_module_dependency_graph_tracks_live_internal_and_workspace_edges() -> None:
    runtime = build_module_dependency_graph_report("bijux-proteomics-runtime")
    knowledge = build_module_dependency_graph_report("bijux-proteomics-knowledge")

    runtime_by_module = {entry.module_name: entry for entry in runtime.entries}
    knowledge_by_module = {entry.module_name: entry for entry in knowledge.entries}

    assert "bijux_proteomics_runtime.runs.manager" in runtime_by_module
    assert any(
        target.startswith("bijux_proteomics_runtime.runs")
        for target in runtime_by_module[
            "bijux_proteomics_runtime.runs.manager"
        ].outgoing_internal_modules
    )
    assert any(
        target.startswith("bijux_proteomics")
        for target in runtime_by_module[
            "bijux_proteomics_runtime.runs.manager"
        ].outgoing_workspace_modules
    )
    assert (
        "bijux_proteomics_knowledge.references.workflows.benchmarks"
        in knowledge_by_module
    )
