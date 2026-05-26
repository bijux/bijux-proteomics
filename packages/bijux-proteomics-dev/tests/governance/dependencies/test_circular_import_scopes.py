from __future__ import annotations

from bijux_proteomics_dev.governance.dependencies.circular_import_scopes import (
    CIRCULAR_IMPORT_SCOPES_PATH,
    CircularImportScope,
    build_declared_workspace_package_cycles,
    build_circular_import_scope_cycles,
    load_circular_import_scopes,
    run,
    validate_circular_import_scopes,
)
from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    WorkspaceModuleDependencyEdge,
)


def test_circular_import_scope_manifest_covers_curated_package_families() -> None:
    scopes = load_circular_import_scopes()

    assert [(scope.distribution_name, scope.scope_name) for scope in scopes] == [
        ("bijux-proteomics-core", "scientific-kernel"),
        ("bijux-proteomics-foundation", "document-kernel"),
        ("bijux-proteomics-intelligence", "review-surface"),
        ("bijux-proteomics-knowledge", "knowledge-families"),
        ("bijux-proteomics-lab", "handoff-kernel"),
        ("bijux-proteomics-runtime", "execution-kernel"),
    ]


def test_circular_import_scopes_are_structurally_valid_and_cycle_free() -> None:
    assert validate_circular_import_scopes() == ()
    assert run(check=True) == 0


def test_declared_workspace_package_cycles_detect_synthetic_cycle() -> None:
    package_dependencies = {
        "bijux-proteomics-core": ("bijux-proteomics-intelligence",),
        "bijux-proteomics-foundation": (),
        "bijux-proteomics-intelligence": ("bijux-proteomics-runtime",),
        "bijux-proteomics-runtime": ("bijux-proteomics-core",),
    }

    assert build_declared_workspace_package_cycles(package_dependencies) == (
        (
            "bijux-proteomics-core",
            "bijux-proteomics-intelligence",
            "bijux-proteomics-runtime",
        ),
    )


def test_circular_import_scope_detects_synthetic_family_cycle() -> None:
    scope = CircularImportScope(
        distribution_name="bijux-proteomics-runtime",
        scope_name="synthetic-runtime-cycle",
        monitored_families=("api", "runs", "workflows"),
    )
    dependency_edges = (
        WorkspaceModuleDependencyEdge(
            source_distribution="bijux-proteomics-runtime",
            source_module="bijux_proteomics_runtime.api.router",
            target_distribution="bijux-proteomics-runtime",
            target_module="bijux_proteomics_runtime.runs.manager",
            internal=True,
        ),
        WorkspaceModuleDependencyEdge(
            source_distribution="bijux-proteomics-runtime",
            source_module="bijux_proteomics_runtime.runs.manager",
            target_distribution="bijux-proteomics-runtime",
            target_module="bijux_proteomics_runtime.workflows.executor",
            internal=True,
        ),
        WorkspaceModuleDependencyEdge(
            source_distribution="bijux-proteomics-runtime",
            source_module="bijux_proteomics_runtime.workflows.executor",
            target_distribution="bijux-proteomics-runtime",
            target_module="bijux_proteomics_runtime.api.schemas",
            internal=True,
        ),
    )

    cycles = build_circular_import_scope_cycles(
        scope,
        dependency_edges=dependency_edges,
    )

    assert len(cycles) == 1
    assert cycles[0].families == ("api", "runs", "workflows")


def test_circular_import_scope_manifest_is_repository_owned() -> None:
    assert CIRCULAR_IMPORT_SCOPES_PATH.as_posix().endswith(
        "configs/package-governance/circular-import-scopes.toml"
    )
