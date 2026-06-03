from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TypeAlias

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
    "workspace_dependency_edges_for_path",
    "workspace_import_roots",
]


StaticModuleValue: TypeAlias = str | tuple[str, ...]


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
    package_parts: tuple[str, ...],
    *,
    level: int,
    module_name: str | None,
) -> str | None:
    if level <= 0 or level > len(package_parts):
        return None
    base_parts = package_parts if level == 1 else package_parts[: -(level - 1)]
    suffix = tuple(module_name.split(".")) if module_name else ()
    target_parts = (*base_parts, *suffix)
    return ".".join(target_parts) if target_parts else None


def module_dependency_edges(
    package_name: str,
) -> tuple[WorkspaceModuleDependencyEdge, ...]:
    """Return resolved workspace module dependency edges for one package."""

    edges = {
        edge
        for path in source_modules(package_name)
        for edge in workspace_dependency_edges_for_path(package_name, path)
    }
    return tuple(sorted(edges, key=_edge_sort_key))


def workspace_dependency_edges_for_path(
    package_name: str,
    path: Path,
    *,
    source_module_name: str | None = None,
) -> tuple[WorkspaceModuleDependencyEdge, ...]:
    """Return resolved workspace dependency edges for one Python module path."""

    roots = workspace_import_roots()
    source_module = source_module_name or module_identifier(package_name, path)
    source_module_parts = tuple(source_module.split("."))
    package_parts = (
        source_module_parts if path.name == "__init__.py" else source_module_parts[:-1]
    )
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    static_bindings = _static_module_bindings(tree)
    import_module_names, importlib_module_names = _import_module_aliases(tree)
    edges: set[WorkspaceModuleDependencyEdge] = set()
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
                    package_parts,
                    level=node.level,
                    module_name=node.module,
                )
                if resolved_target_name is not None:
                    resolved_target_distribution = package_name
            elif node.module is not None:
                resolved_target_name = node.module
                root_name = resolved_target_name.split(".")[0]
                resolved_target_distribution = roots.get(root_name)
            if resolved_target_name is None or resolved_target_distribution is None:
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
            for alias in node.names:
                if alias.name == "*":
                    continue
                edges.add(
                    WorkspaceModuleDependencyEdge(
                        source_distribution=package_name,
                        source_module=source_module,
                        target_distribution=resolved_target_distribution,
                        target_module=f"{resolved_target_name}.{alias.name}",
                        internal=resolved_target_distribution == package_name,
                    )
                )
    for target_name in _dynamic_import_targets(
        tree,
        static_bindings=static_bindings,
        import_module_names=import_module_names,
        importlib_module_names=importlib_module_names,
    ):
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
    return tuple(sorted(edges, key=_edge_sort_key))


def _static_module_bindings(tree: ast.Module) -> dict[str, StaticModuleValue]:
    bindings: dict[str, StaticModuleValue] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            value = _static_module_value(node.value)
            if value is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    bindings[target.id] = value
        elif isinstance(node, ast.AnnAssign):
            if not isinstance(node.target, ast.Name) or node.value is None:
                continue
            value = _static_module_value(node.value)
            if value is not None:
                bindings[node.target.id] = value
    return bindings


def _static_module_value(node: ast.AST) -> StaticModuleValue | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, (ast.Tuple, ast.List)):
        values: list[str] = []
        for element in node.elts:
            if not isinstance(element, ast.Constant) or not isinstance(
                element.value, str
            ):
                return None
            values.append(element.value)
        return tuple(values)
    return None


def _import_module_aliases(tree: ast.Module) -> tuple[set[str], set[str]]:
    import_module_names: set[str] = set()
    importlib_module_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    importlib_module_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "importlib":
            for alias in node.names:
                if alias.name == "import_module":
                    import_module_names.add(alias.asname or alias.name)
    return import_module_names, importlib_module_names


def _dynamic_import_targets(
    tree: ast.Module,
    *,
    static_bindings: dict[str, StaticModuleValue],
    import_module_names: set[str],
    importlib_module_names: set[str],
) -> tuple[str, ...]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target_name = _resolve_dynamic_import_call(
                node,
                static_bindings=static_bindings,
                import_module_names=import_module_names,
                importlib_module_names=importlib_module_names,
            )
            if target_name is not None:
                targets.add(target_name)
        elif isinstance(node, ast.For):
            targets.update(
                _resolve_dynamic_import_loop(
                    node,
                    static_bindings=static_bindings,
                    import_module_names=import_module_names,
                    importlib_module_names=importlib_module_names,
                )
            )
    return tuple(sorted(targets))


def _resolve_dynamic_import_call(
    node: ast.Call,
    *,
    static_bindings: dict[str, StaticModuleValue],
    import_module_names: set[str],
    importlib_module_names: set[str],
) -> str | None:
    if not _is_import_module_call(
        node.func,
        import_module_names=import_module_names,
        importlib_module_names=importlib_module_names,
    ):
        return None
    if not node.args:
        return None
    return _resolve_static_module_name(node.args[0], static_bindings)


def _resolve_dynamic_import_loop(
    node: ast.For,
    *,
    static_bindings: dict[str, StaticModuleValue],
    import_module_names: set[str],
    importlib_module_names: set[str],
) -> tuple[str, ...]:
    if not isinstance(node.target, ast.Name):
        return ()
    if not isinstance(node.iter, ast.Name):
        return ()
    iter_value = static_bindings.get(node.iter.id)
    if not isinstance(iter_value, tuple):
        return ()
    loop_targets: set[str] = set()
    for child in ast.walk(ast.Module(body=node.body, type_ignores=[])):
        if not isinstance(child, ast.Call):
            continue
        if not _is_import_module_call(
            child.func,
            import_module_names=import_module_names,
            importlib_module_names=importlib_module_names,
        ):
            continue
        if not child.args:
            continue
        arg = child.args[0]
        if isinstance(arg, ast.Name) and arg.id == node.target.id:
            loop_targets.update(iter_value)
    return tuple(sorted(loop_targets))


def _is_import_module_call(
    node: ast.AST,
    *,
    import_module_names: set[str],
    importlib_module_names: set[str],
) -> bool:
    if isinstance(node, ast.Name):
        return node.id in import_module_names
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.attr == "import_module"
    ):
        return node.value.id in importlib_module_names
    return False


def _resolve_static_module_name(
    node: ast.AST,
    static_bindings: dict[str, StaticModuleValue],
) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        bound = static_bindings.get(node.id)
        if isinstance(bound, str):
            return bound
    return None


def _edge_sort_key(
    edge: WorkspaceModuleDependencyEdge,
) -> tuple[str, str, str, str, bool]:
    return (
        edge.source_distribution,
        edge.source_module,
        edge.target_distribution,
        edge.target_module,
        edge.internal,
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
            key=_edge_sort_key,
        )
    )
