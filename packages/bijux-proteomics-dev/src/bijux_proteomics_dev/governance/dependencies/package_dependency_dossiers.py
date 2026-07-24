from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.dependencies.package_dependency_graph import (
    build_package_dependency_graph_report,
)
from bijux_proteomics_dev.governance.dependencies.package_dependency_policy import (
    build_package_dependency_policy_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_package_names,
)

__all__ = [
    "PACKAGE_DEPENDENCY_DOSSIERS_PATH",
    "PackageDependencyDossierEntry",
    "PackageDependencyDossierReport",
    "build_package_dependency_dossier_report",
    "run",
    "validate_package_dependency_dossiers",
]


PACKAGE_DEPENDENCY_DOSSIERS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-dependency-dossiers.toml"
)


@dataclass(frozen=True)
class PackageDependencyDossierEntry:
    """Inbound and outbound dependency dossier for one package."""

    distribution_name: str
    allowed_outbound_edges: tuple[str, ...]
    allowed_inbound_edges: tuple[str, ...]
    actual_outbound_edges: tuple[str, ...]
    actual_inbound_edges: tuple[str, ...]
    unexpected_outbound_edges: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class PackageDependencyDossierReport:
    """Checked per-package dependency dossiers for reviewer use."""

    entries: tuple[PackageDependencyDossierEntry, ...]


def build_package_dependency_dossier_report() -> PackageDependencyDossierReport:
    """Build dependency dossiers for every workspace package."""

    policy = build_package_dependency_policy_report()
    by_package = {entry.distribution_name: entry for entry in policy.entries}
    actual_outbound: dict[str, set[str]] = {
        package_name: set() for package_name in workspace_package_names()
    }
    actual_inbound: dict[str, set[str]] = {
        package_name: set() for package_name in workspace_package_names()
    }
    for edge in build_package_dependency_graph_report().entries:
        actual_outbound[edge.source_distribution].add(edge.target_distribution)
        actual_inbound[edge.target_distribution].add(edge.source_distribution)

    allowed_inbound: dict[str, set[str]] = {
        package_name: set() for package_name in workspace_package_names()
    }
    for entry in policy.entries:
        for target in entry.allowed_outbound_edges:
            allowed_inbound[target].add(entry.distribution_name)

    entries = tuple(
        PackageDependencyDossierEntry(
            distribution_name=package_name,
            allowed_outbound_edges=by_package[package_name].allowed_outbound_edges,
            allowed_inbound_edges=tuple(sorted(allowed_inbound[package_name])),
            actual_outbound_edges=tuple(sorted(actual_outbound[package_name])),
            actual_inbound_edges=tuple(sorted(actual_inbound[package_name])),
            unexpected_outbound_edges=tuple(
                sorted(
                    actual_outbound[package_name]
                    - set(by_package[package_name].allowed_outbound_edges)
                )
            ),
            rationale=by_package[package_name].rationale,
        )
        for package_name in workspace_package_names()
    )
    return PackageDependencyDossierReport(entries=entries)


def validate_package_dependency_dossiers(
    report: PackageDependencyDossierReport | None = None,
) -> tuple[str, ...]:
    """Fail release when package dependency dossiers show disallowed edges."""

    report = report or build_package_dependency_dossier_report()
    failures = [
        f"{entry.distribution_name} still has unexpected outbound edges: {', '.join(entry.unexpected_outbound_edges)}"
        for entry in report.entries
        if entry.unexpected_outbound_edges
    ]
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: PackageDependencyDossierReport) -> str:
    lines = [
        "# Generated package dependency dossiers.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.dependencies.package_dependency_dossiers",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"allowed_outbound_edges = [{_render_tuple(entry.allowed_outbound_edges)}]",
                f"allowed_inbound_edges = [{_render_tuple(entry.allowed_inbound_edges)}]",
                f"actual_outbound_edges = [{_render_tuple(entry.actual_outbound_edges)}]",
                f"actual_inbound_edges = [{_render_tuple(entry.actual_inbound_edges)}]",
                (
                    "unexpected_outbound_edges = "
                    f"[{_render_tuple(entry.unexpected_outbound_edges)}]"
                ),
                f'rationale = "{entry.rationale}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageDependencyDossierReport) -> bool:
    if not PACKAGE_DEPENDENCY_DOSSIERS_PATH.exists():
        return False
    return PACKAGE_DEPENDENCY_DOSSIERS_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_dependency_dossier_report()
    failures = validate_package_dependency_dossiers(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package dependency dossiers are up to date")
            return 0
        print("package dependency dossiers are stale; regenerate them")
        return 1
    PACKAGE_DEPENDENCY_DOSSIERS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package dependency dossiers")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate package dependency dossiers."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package dependency dossiers are not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
