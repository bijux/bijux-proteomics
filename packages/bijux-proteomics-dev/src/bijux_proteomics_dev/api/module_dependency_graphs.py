from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.package_quality_inventory import (
    source_modules,
    workspace_package_names,
)
from bijux_proteomics_dev.api.runtime_topology import REPO_ROOT
from bijux_proteomics_dev.api.workspace_import_inventory import (
    module_dependency_edges,
    module_identifier,
)

__all__ = [
    "MODULE_DEPENDENCY_GRAPHS_DIR",
    "ModuleDependencyGraphEntry",
    "ModuleDependencyGraphReport",
    "build_module_dependency_graph_report",
    "run",
]


MODULE_DEPENDENCY_GRAPHS_DIR = (
    REPO_ROOT / "configs" / "package-governance" / "module-dependency-graphs"
)


@dataclass(frozen=True)
class ModuleDependencyGraphEntry:
    """One module node and its outgoing internal and workspace edges."""

    module_name: str
    outgoing_internal_modules: tuple[str, ...]
    outgoing_workspace_modules: tuple[str, ...]


@dataclass(frozen=True)
class ModuleDependencyGraphReport:
    """One checked module dependency graph for a package."""

    distribution_name: str
    entries: tuple[ModuleDependencyGraphEntry, ...]


def build_module_dependency_graph_report(
    package_name: str,
) -> ModuleDependencyGraphReport:
    """Build the module dependency graph for one workspace package."""

    outgoing_internal: dict[str, set[str]] = {}
    outgoing_workspace: dict[str, set[str]] = {}
    for path in source_modules(package_name):
        module_name = module_identifier(package_name, path)
        outgoing_internal.setdefault(module_name, set())
        outgoing_workspace.setdefault(module_name, set())

    for edge in module_dependency_edges(package_name):
        if edge.internal:
            outgoing_internal.setdefault(edge.source_module, set()).add(edge.target_module)
        else:
            outgoing_workspace.setdefault(edge.source_module, set()).add(
                edge.target_module
            )

    entries = tuple(
        ModuleDependencyGraphEntry(
            module_name=module_name,
            outgoing_internal_modules=tuple(sorted(outgoing_internal[module_name])),
            outgoing_workspace_modules=tuple(sorted(outgoing_workspace[module_name])),
        )
        for module_name in sorted(outgoing_internal)
    )
    return ModuleDependencyGraphReport(
        distribution_name=package_name,
        entries=entries,
    )


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _report_path(package_name: str) -> Path:
    return MODULE_DEPENDENCY_GRAPHS_DIR / f"{package_name}.toml"


def _toml_text(report: ModuleDependencyGraphReport) -> str:
    lines = [
        "# Generated module dependency graph.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.module_dependency_graphs",
        "",
        f'distribution_name = "{report.distribution_name}"',
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[module]]",
                f'module_name = "{entry.module_name}"',
                f"outgoing_internal_modules = [{_render_tuple(entry.outgoing_internal_modules)}]",
                f"outgoing_workspace_modules = [{_render_tuple(entry.outgoing_workspace_modules)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(package_name: str, report: ModuleDependencyGraphReport) -> bool:
    path = _report_path(package_name)
    if not path.exists():
        return False
    return path.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    MODULE_DEPENDENCY_GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    reports = {
        package_name: build_module_dependency_graph_report(package_name)
        for package_name in workspace_package_names()
    }
    if check:
        stale = [
            package_name
            for package_name, report in reports.items()
            if not _is_up_to_date(package_name, report)
        ]
        if not stale:
            print("module dependency graphs are up to date")
            return 0
        print("module dependency graphs are stale for " + ", ".join(sorted(stale)))
        return 1
    for package_name, report in reports.items():
        _report_path(package_name).write_text(_toml_text(report), encoding="utf-8")
    print("generated module dependency graphs")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate module dependency graphs."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the module dependency graphs are not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
