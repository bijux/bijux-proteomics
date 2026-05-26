from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    WorkspaceModuleDependencyEdge,
    module_dependency_edges,
)
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
    source_owner_families,
    workspace_package_names,
)

__all__ = [
    "CIRCULAR_IMPORT_SCOPES_PATH",
    "CircularImportScope",
    "CircularImportScopeCycle",
    "CircularImportScopeIssue",
    "build_declared_workspace_package_cycles",
    "build_circular_import_scope_cycles",
    "build_circular_import_scope_issues",
    "load_circular_import_scopes",
    "run",
    "validate_circular_import_scopes",
]


CIRCULAR_IMPORT_SCOPES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "circular-import-scopes.toml"
)
CIRCULAR_IMPORT_ARTIFACTS_DIR = REPO_ROOT / "artifacts" / "root" / "circular-imports"
_FACADE_MODULE_BASENAMES = {"__init__", "public", "public_api"}
_DEPENDENCY_NAME_PATTERN = re.compile(r"([A-Za-z0-9_.-]+)")


@dataclass(frozen=True)
class CircularImportScope:
    """One governed package-family graph that must remain acyclic."""

    distribution_name: str
    scope_name: str
    monitored_families: tuple[str, ...]


@dataclass(frozen=True)
class CircularImportScopeCycle:
    """One normalized family cycle inside a governed package scope."""

    distribution_name: str
    scope_name: str
    families: tuple[str, ...]


@dataclass(frozen=True)
class CircularImportScopeIssue:
    """One live circular-import contract failure."""

    scope_name: str
    detail: str


def load_circular_import_scopes(
    path: Path = CIRCULAR_IMPORT_SCOPES_PATH,
) -> tuple[CircularImportScope, ...]:
    """Load the governed circular-import scope manifest."""

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    scopes = cast(list[dict[str, Any]], data["scope"])
    return tuple(
        CircularImportScope(
            distribution_name=str(scope["distribution_name"]),
            scope_name=str(scope["scope_name"]),
            monitored_families=tuple(str(value) for value in scope["monitored_families"]),
        )
        for scope in scopes
    )


def _normalize_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    candidates = [cycle[index:] + cycle[:index] for index in range(len(cycle))]
    return min(candidates)


def _find_normalized_cycles(
    adjacency: dict[str, set[str]],
) -> tuple[tuple[str, ...], ...]:
    found: set[tuple[str, ...]] = set()
    active: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            start = active.index(node)
            found.add(_normalize_cycle(tuple(active[start:])))
            return
        visiting.add(node)
        active.append(node)
        for dependency in sorted(adjacency[node]):
            visit(dependency)
        active.pop()
        visiting.remove(node)
        visited.add(node)

    for family_name in sorted(adjacency):
        visit(family_name)
    return tuple(sorted(found))


def _is_facade_module(module_name: str) -> bool:
    return module_name.split(".")[-1] in _FACADE_MODULE_BASENAMES


def _family_name(module_name: str) -> str | None:
    parts = module_name.split(".")
    if len(parts) <= 2:
        return None
    return parts[1]


def _normalize_dependency_name(requirement: str) -> str:
    match = _DEPENDENCY_NAME_PATTERN.match(requirement.strip())
    return match.group(1).lower() if match else requirement.strip().lower()


def _declared_workspace_package_dependencies() -> dict[str, tuple[str, ...]]:
    package_names = workspace_package_names()
    package_by_distribution: dict[str, str] = {}
    dependencies_by_package: dict[str, tuple[str, ...]] = {}

    for package_name in package_names:
        pyproject_path = package_root(package_name) / "pyproject.toml"
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        project = cast(dict[str, Any], data["project"])
        distribution_name = str(project["name"]).lower()
        package_by_distribution[distribution_name] = package_name
        dependencies_by_package[package_name] = tuple(
            _normalize_dependency_name(str(value))
            for value in cast(list[str], project.get("dependencies", []))
        )

    return {
        package_name: tuple(
            sorted(
                {
                    package_by_distribution[dependency_name]
                    for dependency_name in dependency_names
                    if dependency_name in package_by_distribution
                }
            )
        )
        for package_name, dependency_names in dependencies_by_package.items()
    }


def build_declared_workspace_package_cycles(
    package_dependencies: dict[str, tuple[str, ...]] | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Return cycles across declared workspace package dependencies."""

    package_dependencies = (
        package_dependencies or _declared_workspace_package_dependencies()
    )
    adjacency = {
        package_name: set(dependency_names)
        for package_name, dependency_names in package_dependencies.items()
    }
    return _find_normalized_cycles(adjacency)


def build_circular_import_scope_cycles(
    scope: CircularImportScope,
    *,
    dependency_edges: tuple[WorkspaceModuleDependencyEdge, ...] | None = None,
) -> tuple[CircularImportScopeCycle, ...]:
    """Return the normalized set of family cycles for one governed scope."""

    dependency_edges = dependency_edges or module_dependency_edges(scope.distribution_name)
    monitored_families = set(scope.monitored_families)
    adjacency: dict[str, set[str]] = defaultdict(set)
    for family_name in scope.monitored_families:
        adjacency.setdefault(family_name, set())
    for edge in dependency_edges:
        if not edge.internal:
            continue
        if _is_facade_module(edge.source_module) or _is_facade_module(edge.target_module):
            continue
        source_family = _family_name(edge.source_module)
        target_family = _family_name(edge.target_module)
        if source_family is None or target_family is None:
            continue
        if source_family == target_family:
            continue
        if source_family not in monitored_families or target_family not in monitored_families:
            continue
        adjacency[source_family].add(target_family)

    return tuple(
        CircularImportScopeCycle(
            distribution_name=scope.distribution_name,
            scope_name=scope.scope_name,
            families=cycle,
        )
        for cycle in _find_normalized_cycles(adjacency)
    )


def validate_circular_import_scopes(
    scopes: tuple[CircularImportScope, ...] | None = None,
) -> tuple[CircularImportScopeIssue, ...]:
    """Validate declared package cycles and governed family import scopes."""

    scopes = scopes or load_circular_import_scopes()
    issues: list[CircularImportScopeIssue] = []
    seen_scope_names: set[str] = set()

    for cycle in build_declared_workspace_package_cycles():
        issues.append(
            CircularImportScopeIssue(
                scope_name="workspace-declared-package-graph",
                detail=(
                    "declared workspace package dependency cycle: "
                    + " -> ".join([*cycle, cycle[0]])
                ),
            )
        )

    for scope in scopes:
        if scope.scope_name in seen_scope_names:
            issues.append(
                CircularImportScopeIssue(
                    scope_name=scope.scope_name,
                    detail=f"duplicate circular-import scope name {scope.scope_name}",
                )
            )
            continue
        seen_scope_names.add(scope.scope_name)
        if len(scope.monitored_families) < 2:
            issues.append(
                CircularImportScopeIssue(
                    scope_name=scope.scope_name,
                    detail=(
                        f"{scope.scope_name} must govern at least two package families"
                    ),
                )
            )
            continue
        live_families = set(source_owner_families(scope.distribution_name))
        missing = sorted(set(scope.monitored_families) - live_families)
        if missing:
            issues.append(
                CircularImportScopeIssue(
                    scope_name=scope.scope_name,
                    detail=(
                        f"{scope.distribution_name} scope {scope.scope_name} names missing "
                        f"families: {', '.join(missing)}"
                    ),
                )
            )
            continue
        for cycle in build_circular_import_scope_cycles(scope):
            loop = " -> ".join([*cycle.families, cycle.families[0]])
            issues.append(
                CircularImportScopeIssue(
                    scope_name=scope.scope_name,
                    detail=(
                        f"{scope.distribution_name} family import cycle detected: {loop}"
                    ),
                )
            )
    return tuple(issues)


def build_circular_import_scope_issues() -> tuple[CircularImportScopeIssue, ...]:
    """Return the live set of circular-import issues for repository checks."""

    return validate_circular_import_scopes()


def run(*, check: bool = False) -> int:
    """Validate the governed circular-import scopes."""

    issues = build_circular_import_scope_issues()
    CIRCULAR_IMPORT_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    artifact_path = CIRCULAR_IMPORT_ARTIFACTS_DIR / "validation.txt"
    if issues:
        text = "\n".join(issue.detail for issue in issues) + "\n"
        artifact_path.write_text(text, encoding="utf-8")
        for issue in issues:
            print(issue.detail)
        return 1
    artifact_path.write_text("no governed circular imports detected\n", encoding="utf-8")
    if not check:
        print("governed circular import scopes are acyclic")
    else:
        print("governed circular import scopes are acyclic")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate governed workspace package and package-family circular import scopes."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when a governed package or family import cycle is present.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
