from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.quality.graphs.package_graph import (
    build_workspace_package_graph,
)

__all__ = [
    "PackageCouplingHotspot",
    "build_package_coupling_report",
    "render_package_coupling_summary",
]


@dataclass(frozen=True)
class PackageCouplingHotspot:
    """One package-level coupling hotspot report row."""

    package_name: str
    direct_dependency_count: int
    reverse_dependency_count: int
    external_dependency_count: int
    coupling_score: int
    pressure_level: str
    notes: tuple[str, ...]


def _pressure_level(score: int) -> str:
    if score >= 8:
        return "elevated"
    if score >= 5:
        return "watch"
    return "stable"


def build_package_coupling_report(
    repo_root: Path,
) -> tuple[PackageCouplingHotspot, ...]:
    """Build a workspace package coupling report from declared dependencies."""
    graph = build_workspace_package_graph(repo_root)
    rows: list[PackageCouplingHotspot] = []
    for package in graph.packages:
        direct_dependency_count = len(package.workspace_dependencies)
        reverse_dependency_count = len(
            graph.reverse_dependencies_of(package.package_name)
        )
        external_dependency_count = len(package.external_dependencies)
        coupling_score = (
            direct_dependency_count
            + reverse_dependency_count
            + max(external_dependency_count - 2, 0)
        )
        notes: list[str] = []
        if reverse_dependency_count >= 4:
            notes.append("many packages depend on this surface directly")
        if direct_dependency_count >= 4:
            notes.append("this package reaches broadly across the workspace")
        if external_dependency_count >= 3:
            notes.append("external dependency load is high for a bounded package")
        if not notes:
            notes.append("current coupling stays within the normal package budget")
        rows.append(
            PackageCouplingHotspot(
                package_name=package.package_name,
                direct_dependency_count=direct_dependency_count,
                reverse_dependency_count=reverse_dependency_count,
                external_dependency_count=external_dependency_count,
                coupling_score=coupling_score,
                pressure_level=_pressure_level(coupling_score),
                notes=tuple(notes),
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (-row.coupling_score, row.package_name),
        )
    )


def render_package_coupling_summary(repo_root: Path) -> str:
    """Render the package coupling report as a plain-text summary."""
    lines = ["package_name\tpressure\tscore\tdirect\treverse\texternal\tnotes"]
    for row in build_package_coupling_report(repo_root):
        lines.append(
            "\t".join(
                [
                    row.package_name,
                    row.pressure_level,
                    str(row.coupling_score),
                    str(row.direct_dependency_count),
                    str(row.reverse_dependency_count),
                    str(row.external_dependency_count),
                    " | ".join(row.notes),
                ]
            )
        )
    return "\n".join(lines) + "\n"
