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
    dynamic_targets = _dynamic_import_targets(
        tree,
        static_bindings=static_bindings,
        import_module_names=import_module_names,
        importlib_module_names=importlib_module_names,
    )
    for target_name in {*dynamic_targets, *_facade_owner_targets(tree)}:
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


def _facade_owner_targets(tree: ast.Module) -> tuple[str, ...]:
    """Resolve declared lazy facade ownership without executing product code."""

    targets: set[str] = set()
    constructors: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            if not node.module.startswith("bijux_proteomics."):
                continue
            for alias in node.names:
                if alias.name == "build_facade_module" or alias.name.endswith(
                    "FacadeOwner"
                ):
                    constructors[alias.asname or alias.name] = alias.name
    for node in tree.body:
        if (
            isinstance(node, ast.ClassDef)
            and node.name.endswith("FacadeOwner")
            and any(
                isinstance(item, ast.AnnAssign)
                and isinstance(item.target, ast.Name)
                and item.target.id == "owner_module"
                for item in node.body
            )
        ):
            constructors[node.name] = node.name
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.args.args:
            continue
        parameter = node.args.args[0].arg
        for child in node.body:
            if not isinstance(child, ast.Return) or not isinstance(
                child.value, ast.Call
            ):
                continue
            call = child.value
            if not isinstance(call.func, ast.Name) or call.func.id not in constructors:
                continue
            if any(
                item.arg == "owner_module"
                and isinstance(item.value, ast.Name)
                and item.value.id == parameter
                for item in call.keywords
            ):
                constructors[node.name] = "build_facade_module"
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        constructor = constructors.get(node.func.id)
        value: ast.AST | None = None
        if constructor == "build_facade_module" and node.args:
            value = node.args[0]
        elif constructor is not None and constructor.endswith("FacadeOwner"):
            value = next(
                (item.value for item in node.keywords if item.arg == "owner_module"),
                None,
            )
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            targets.add(value.value)

    export_maps: dict[str, tuple[str, ...]] = {}
    name: ast.AST
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            name, value = node.target, node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            name, value = node.targets[0], node.value
        else:
            continue
        if not isinstance(name, ast.Name) or not isinstance(
            value, (ast.Tuple, ast.List)
        ):
            continue
        owners: list[str] = []
        for pair in value.elts:
            if not isinstance(pair, (ast.Tuple, ast.List)) or len(pair.elts) != 2:
                break
            if not all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in pair.elts
            ):
                break
            owner = pair.elts[1]
            assert isinstance(owner, ast.Constant) and isinstance(owner.value, str)
            owners.append(owner.value)
        else:
            export_maps[name.id] = tuple(owners)
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not isinstance(node.iter, ast.Name):
            continue
        if (
            not isinstance(node.target, (ast.Tuple, ast.List))
            or len(node.target.elts) != 2
        ):
            continue
        owner = node.target.elts[1]
        if not isinstance(owner, ast.Name):
            continue
        for descendant in ast.walk(ast.Module(body=node.body, type_ignores=[])):
            if (
                isinstance(descendant, ast.Assign)
                and isinstance(descendant.value, ast.Name)
                and descendant.value.id == owner.id
                and any(isinstance(item, ast.Subscript) for item in descendant.targets)
            ):
                targets.update(export_maps.get(node.iter.id, ()))
    return tuple(sorted(targets))


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
