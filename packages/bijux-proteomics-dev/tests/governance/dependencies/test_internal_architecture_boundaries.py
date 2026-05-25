from __future__ import annotations

from bijux_proteomics_dev.governance.dependencies.internal_architecture_map import (
    evaluate_internal_architecture_violations,
)
from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    WorkspaceModuleDependencyEdge,
)


def _edge(
    *,
    source_distribution: str,
    source_module: str,
    target_distribution: str,
    target_module: str,
    internal: bool,
) -> WorkspaceModuleDependencyEdge:
    return WorkspaceModuleDependencyEdge(
        source_distribution=source_distribution,
        source_module=source_module,
        target_distribution=target_distribution,
        target_module=target_module,
        internal=internal,
    )


def test_internal_architecture_boundaries_flag_forbidden_edges_and_cycles() -> None:
    violations = evaluate_internal_architecture_violations(
        package_edges=(
            _edge(
                source_distribution="bijux-proteomics-foundation",
                source_module="bijux_proteomics_foundation.serialization.hashes",
                target_distribution="bijux-proteomics-core",
                target_module="bijux_proteomics.workflow.study_result",
                internal=False,
            ),
        ),
        module_edges=(
            _edge(
                source_distribution="bijux-proteomics-core",
                source_module="bijux_proteomics.workflow.pipelines.orchestrator",
                target_distribution="bijux-proteomics-core",
                target_module="bijux_proteomics.interfaces.cli.app",
                internal=True,
            ),
        ),
        workspace_cycles=(("bijux-proteomics-core", "bijux-proteomics-runtime"),),
    )

    assert [violation.boundary_name for violation in violations] == [
        "package_outbound_edge",
        "module_family_outbound_edge",
        "workspace_cycle",
    ]
    assert "bijux-proteomics-foundation imports disallowed package edges" in violations[0].detail
    assert "workflow_pipelines imports" in violations[1].detail
    assert violations[2].detail == (
        "bijux-proteomics-core -> bijux-proteomics-runtime -> bijux-proteomics-core"
    )
