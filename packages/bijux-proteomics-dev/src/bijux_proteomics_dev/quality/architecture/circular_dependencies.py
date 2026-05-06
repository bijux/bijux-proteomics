from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.quality.graphs.package_graph import build_workspace_package_graph

__all__ = [
    "CircularDependencyIssue",
    "find_workspace_dependency_cycles",
    "validate_workspace_dependency_cycles",
]


@dataclass(frozen=True)
class CircularDependencyIssue:
    """One circular workspace dependency issue."""

    cycle: tuple[str, ...]
    detail: str


def _normalize_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    if not cycle:
        return cycle
    candidates = [cycle[index:] + cycle[:index] for index in range(len(cycle))]
    return min(candidates)


def find_workspace_dependency_cycles(repo_root: Path) -> tuple[tuple[str, ...], ...]:
    """Find circular dependencies across declared workspace packages."""
    graph = build_workspace_package_graph(repo_root)
    adjacency = {
        package.package_name: set(package.workspace_dependencies)
        for package in graph.packages
    }
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

    for package_name in sorted(adjacency):
        visit(package_name)
    return tuple(sorted(found))


def validate_workspace_dependency_cycles(
    repo_root: Path,
) -> tuple[CircularDependencyIssue, ...]:
    """Validate that the workspace package graph has no cycles."""
    return tuple(
        CircularDependencyIssue(
            cycle=cycle,
            detail=" -> ".join([*cycle, cycle[0]]),
        )
        for cycle in find_workspace_dependency_cycles(repo_root)
    )
