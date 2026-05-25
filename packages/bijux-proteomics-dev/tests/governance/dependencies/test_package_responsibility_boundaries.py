from __future__ import annotations

import pytest

from bijux_proteomics_dev.governance.dependencies.package_responsibility_map import (
    PACKAGE_RESPONSIBILITY_MAP_PATH,
    evaluate_package_responsibility_boundary_violations,
    run,
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


def test_package_responsibility_boundaries_flag_required_import_directions() -> None:
    violations = evaluate_package_responsibility_boundary_violations(
        foundation_edges=(
            _edge(
                source_distribution="bijux-proteomics-foundation",
                source_module="bijux_proteomics_foundation.serialization.hashes",
                target_distribution="bijux-proteomics-core",
                target_module="bijux_proteomics.workflow.study_result",
                internal=False,
            ),
        ),
        knowledge_edges=(
            _edge(
                source_distribution="bijux-proteomics-knowledge",
                source_module="bijux_proteomics_knowledge.memory.adapters",
                target_distribution="bijux-proteomics-runtime",
                target_module="bijux_proteomics_runtime.resume.execution",
                internal=False,
            ),
        ),
        core_internal_edges=(
            _edge(
                source_distribution="bijux-proteomics-core",
                source_module="bijux_proteomics.workflow.advanced_diann",
                target_distribution="bijux-proteomics-core",
                target_module="bijux_proteomics.interfaces.cli.app",
                internal=True,
            ),
        ),
    )

    assert [violation.boundary_name for violation in violations] == [
        "core_cli_import",
        "foundation_higher_package_import",
        "knowledge_runtime_import",
    ]


@pytest.mark.slow
def test_package_responsibility_map_is_up_to_date() -> None:
    assert PACKAGE_RESPONSIBILITY_MAP_PATH.exists()
    assert run(check=True) == 0
