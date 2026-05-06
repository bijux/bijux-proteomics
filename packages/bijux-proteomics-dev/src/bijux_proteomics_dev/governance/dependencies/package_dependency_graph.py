from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    cross_package_dependency_edges,
)

__all__ = [
    "PACKAGE_DEPENDENCY_GRAPH_PATH",
    "PackageDependencyGraphEntry",
    "PackageDependencyGraphGuard",
    "PackageDependencyGraphReport",
    "build_package_dependency_graph_report",
    "run",
    "validate_package_dependency_graph",
]


PACKAGE_DEPENDENCY_GRAPH_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-dependency-graph.toml"
)


@dataclass(frozen=True)
class PackageDependencyGraphEntry:
    """One aggregated package-to-package dependency edge."""

    source_distribution: str
    target_distribution: str
    source_module_count: int
    source_modules: tuple[str, ...]
    target_modules: tuple[str, ...]


@dataclass(frozen=True)
class PackageDependencyGraphGuard:
    """Release-blocking ceilings over live package dependency growth."""

    max_total_edges: int
    max_total_source_module_uses: int


@dataclass(frozen=True)
class PackageDependencyGraphReport:
    """Checked package dependency graph across workspace packages."""

    entries: tuple[PackageDependencyGraphEntry, ...]
    guard: PackageDependencyGraphGuard


def build_package_dependency_graph_report() -> PackageDependencyGraphReport:
    """Build the checked package dependency graph report."""

    by_edge: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for edge in cross_package_dependency_edges():
        by_edge.setdefault(
            (edge.source_distribution, edge.target_distribution),
            [],
        ).append((edge.source_module, edge.target_module))

    entries = tuple(
        PackageDependencyGraphEntry(
            source_distribution=source_distribution,
            target_distribution=target_distribution,
            source_module_count=len({source_module for source_module, _ in uses}),
            source_modules=tuple(sorted({source_module for source_module, _ in uses})),
            target_modules=tuple(sorted({target_module for _, target_module in uses})),
        )
        for (source_distribution, target_distribution), uses in sorted(by_edge.items())
    )
    return PackageDependencyGraphReport(
        entries=entries,
        guard=PackageDependencyGraphGuard(
            max_total_edges=len(entries),
            max_total_source_module_uses=sum(
                entry.source_module_count for entry in entries
            ),
        ),
    )


def validate_package_dependency_graph(
    report: PackageDependencyGraphReport | None = None,
) -> tuple[str, ...]:
    """Fail release when live package dependency edges grow beyond the baseline."""

    report = report or build_package_dependency_graph_report()
    failures: list[str] = []
    total_edges = len(report.entries)
    total_source_module_uses = sum(
        entry.source_module_count for entry in report.entries
    )
    if total_edges > report.guard.max_total_edges:
        failures.append(
            "package dependency edge count grew beyond the governed baseline"
        )
    if total_source_module_uses > report.guard.max_total_source_module_uses:
        failures.append(
            "package dependency source-module usage grew beyond the governed baseline"
        )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: PackageDependencyGraphReport) -> str:
    lines = [
        "# Generated package dependency graph.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.dependencies.package_dependency_graph",
        "",
        "[guard]",
        f"max_total_edges = {report.guard.max_total_edges}",
        f"max_total_source_module_uses = {report.guard.max_total_source_module_uses}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[edge]]",
                f'source_distribution = "{entry.source_distribution}"',
                f'target_distribution = "{entry.target_distribution}"',
                f"source_module_count = {entry.source_module_count}",
                f"source_modules = [{_render_tuple(entry.source_modules)}]",
                f"target_modules = [{_render_tuple(entry.target_modules)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageDependencyGraphReport) -> bool:
    if not PACKAGE_DEPENDENCY_GRAPH_PATH.exists():
        return False
    return PACKAGE_DEPENDENCY_GRAPH_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_dependency_graph_report()
    failures = validate_package_dependency_graph(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package dependency graph is up to date")
            return 0
        print("package dependency graph is stale; regenerate it")
        return 1
    PACKAGE_DEPENDENCY_GRAPH_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package dependency graph")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package dependency graph."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package dependency graph is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
