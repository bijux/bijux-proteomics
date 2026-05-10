from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    source_modules,
    src_root,
    workspace_package_names,
)

__all__ = [
    "WorkspaceModuleDependencyEdge",
    "cross_package_dependency_edges",
    "module_dependency_edges",
    "module_identifier",
    "workspace_import_roots",
]


@dataclass(frozen=True)
class WorkspaceModuleDependencyEdge:
    """One resolved module dependency edge inside the workspace."""

    source_distribution: str
    source_module: str
    target_distribution: str
    target_module: str
    internal: bool


@lru_cache(maxsize=1)
def workspace_import_roots() -> dict[str, str]:
    """Map import roots to workspace distribution names."""

    return {
        import_root(package_name): package_name
        for package_name in workspace_package_names()
    }


def module_identifier(package_name: str, path: Path) -> str:
    """Return the dotted module identifier for one source path."""

    relative = path.relative_to(src_root(package_name)).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    root = import_root(package_name)
    return ".".join((root, *parts)) if parts else root


def _module_package_parts(package_name: str, path: Path) -> tuple[str, ...]:
    identifier = module_identifier(package_name, path)
    parts = tuple(identifier.split("."))
    if path.name == "__init__.py":
        return parts
    return parts[:-1]


def _resolve_relative_module(
    package_name: str,
    path: Path,
    *,
    level: int,
    module_name: str | None,
) -> str | None:
    package_parts = _module_package_parts(package_name, path)
    if level <= 0 or level > len(package_parts):
        return None
    if level == 1:
        base_parts = package_parts
    else:
        base_parts = package_parts[: -(level - 1)]
    suffix = tuple(module_name.split(".")) if module_name else ()
    target_parts = (*base_parts, *suffix)
    return ".".join(target_parts) if target_parts else None


def module_dependency_edges(
    package_name: str,
) -> tuple[WorkspaceModuleDependencyEdge, ...]:
    """Return resolved workspace module dependency edges for one package."""

    roots = workspace_import_roots()
    edges: set[WorkspaceModuleDependencyEdge] = set()
    for path in source_modules(package_name):
        source_module = module_identifier(package_name, path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target_name = alias.name
                    root_name = target_name.split(".")[0]
                    target_distribution = roots.get(root_name)
                    if target_distribution is None:
                        continue
                    edges.add(
                        WorkspaceModuleDependencyEdge(
                            source_distribution=package_name,
                            source_module=source_module,
                            target_distribution=target_distribution,
                            target_module=target_name,
                            internal=target_distribution == package_name,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                resolved_target_name: str | None = None
                resolved_target_distribution: str | None = None
                if node.level > 0:
                    resolved_target_name = _resolve_relative_module(
                        package_name,
                        path,
                        level=node.level,
                        module_name=node.module,
                    )
                    if resolved_target_name is not None:
                        resolved_target_distribution = package_name
                elif node.module is not None:
                    resolved_target_name = node.module
                    root_name = resolved_target_name.split(".")[0]
                    resolved_target_distribution = roots.get(root_name)
                if (
                    resolved_target_name is None
                    or resolved_target_distribution is None
                ):
                    continue
                edges.add(
                    WorkspaceModuleDependencyEdge(
                        source_distribution=package_name,
                        source_module=source_module,
                        target_distribution=resolved_target_distribution,
                        target_module=resolved_target_name,
                        internal=resolved_target_distribution == package_name,
                    )
                )
    return tuple(
        sorted(
            edges,
            key=lambda edge: (
                edge.source_distribution,
                edge.source_module,
                edge.target_distribution,
                edge.target_module,
                edge.internal,
            ),
        )
    )


def cross_package_dependency_edges() -> tuple[WorkspaceModuleDependencyEdge, ...]:
    """Return every live cross-package module dependency edge in the workspace."""

    edges: list[WorkspaceModuleDependencyEdge] = []
    for package_name in workspace_package_names():
        edges.extend(
            edge for edge in module_dependency_edges(package_name) if not edge.internal
        )
    return tuple(
        sorted(
            edges,
            key=lambda edge: (
                edge.source_distribution,
                edge.source_module,
                edge.target_distribution,
                edge.target_module,
            ),
        )
    )
