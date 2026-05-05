from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "REPO_ROOT",
    "RUNTIME_IMPORT_GRAPH_PATH",
    "RUNTIME_SRC_ROOT",
    "RuntimeImportCycle",
    "RuntimeImportSurface",
    "build_runtime_import_cycles",
    "build_runtime_import_surfaces",
    "run",
]


@dataclass(frozen=True)
class RuntimeImportSurface:
    """One runtime-owned surface and its internal import edges."""

    name: str
    outgoing_surfaces: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeImportCycle:
    """One normalized runtime import cycle."""

    surfaces: tuple[str, ...]


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for runtime import graph")


REPO_ROOT = _repo_root()
RUNTIME_SRC_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-runtime"
    / "src"
    / "bijux_proteomics_runtime"
)
RUNTIME_IMPORT_GRAPH_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "runtime-import-graph.toml"
)
_RUNTIME_IMPORT_PREFIX = "bijux_proteomics_runtime."


def _surface_name(path: Path) -> str:
    relative = path.relative_to(RUNTIME_SRC_ROOT)
    if len(relative.parts) > 1:
        return relative.parts[0]
    if relative.name == "__init__.py":
        return "package_root"
    return relative.stem


def _surface_graph() -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for path in sorted(RUNTIME_SRC_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        source_surface = _surface_name(path)
        graph.setdefault(source_surface, set())
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target_surface = _target_surface(alias.name)
                    if target_surface is None or target_surface == source_surface:
                        continue
                    graph[source_surface].add(target_surface)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                target_surface = _target_surface(node.module)
                if target_surface is None or target_surface == source_surface:
                    continue
                graph[source_surface].add(target_surface)
    return graph


def _target_surface(module_name: str) -> str | None:
    if module_name == "bijux_proteomics_runtime":
        return "package_root"
    if not module_name.startswith(_RUNTIME_IMPORT_PREFIX):
        return None
    tail = module_name[len(_RUNTIME_IMPORT_PREFIX) :]
    if not tail:
        return "package_root"
    return tail.split(".")[0]


def build_runtime_import_surfaces() -> tuple[RuntimeImportSurface, ...]:
    """Build the current internal runtime import graph."""

    graph = _surface_graph()
    return tuple(
        RuntimeImportSurface(
            name=name,
            outgoing_surfaces=tuple(sorted(targets)),
        )
        for name, targets in sorted(graph.items())
    )


def _normalize_cycle(cycle: tuple[str, ...]) -> tuple[str, ...]:
    candidates = [cycle[index:] + cycle[:index] for index in range(len(cycle))]
    return min(candidates)


def build_runtime_import_cycles() -> tuple[RuntimeImportCycle, ...]:
    """Build the normalized set of runtime import cycles."""

    graph = _surface_graph()
    found: set[tuple[str, ...]] = set()
    stack: list[str] = []
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in stack:
            start = stack.index(node)
            found.add(_normalize_cycle(tuple(stack[start:])))
            return
        if node in visited:
            return
        stack.append(node)
        for target in sorted(graph[node]):
            if target in graph:
                visit(target)
        stack.pop()
        visited.add(node)

    for node in sorted(graph):
        visit(node)

    return tuple(RuntimeImportCycle(surfaces=cycle) for cycle in sorted(found))


def _toml_text(
    surfaces: tuple[RuntimeImportSurface, ...],
    cycles: tuple[RuntimeImportCycle, ...],
) -> str:
    lines = [
        "# Generated runtime import graph.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.runtime_import_graph",
        "",
    ]
    for surface in surfaces:
        outgoing = ", ".join(f'"{value}"' for value in surface.outgoing_surfaces)
        lines.extend(
            [
                "[[surface]]",
                f'name = "{surface.name}"',
                f"outgoing_surfaces = [{outgoing}]",
                "",
            ]
        )
    for cycle in cycles:
        members = ", ".join(f'"{value}"' for value in cycle.surfaces)
        lines.extend(
            [
                "[[cycle]]",
                f"surfaces = [{members}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(
    surfaces: tuple[RuntimeImportSurface, ...],
    cycles: tuple[RuntimeImportCycle, ...],
) -> bool:
    if not RUNTIME_IMPORT_GRAPH_PATH.exists():
        return False
    return RUNTIME_IMPORT_GRAPH_PATH.read_text(encoding="utf-8") == _toml_text(
        surfaces,
        cycles,
    )


def run(check: bool = False) -> int:
    surfaces = build_runtime_import_surfaces()
    cycles = build_runtime_import_cycles()
    if check:
        if _is_up_to_date(surfaces, cycles):
            print(
                "runtime import graph is up to date for "
                f"{len(surfaces)} surfaces and {len(cycles)} cycles"
            )
            return 0
        print("runtime import graph is stale; regenerate it")
        return 1
    RUNTIME_IMPORT_GRAPH_PATH.write_text(
        _toml_text(surfaces, cycles),
        encoding="utf-8",
    )
    print(
        "generated runtime import graph for "
        f"{len(surfaces)} surfaces and {len(cycles)} cycles"
    )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the runtime import graph."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the runtime import graph is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
