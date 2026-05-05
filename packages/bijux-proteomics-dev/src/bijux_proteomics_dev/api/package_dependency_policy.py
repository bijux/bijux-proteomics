from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.api.package_dependency_graph import (
    build_package_dependency_graph_report,
)
from bijux_proteomics_dev.api.package_quality_inventory import workspace_package_names
from bijux_proteomics_dev.api.runtime_topology import REPO_ROOT

__all__ = [
    "PACKAGE_DEPENDENCY_POLICY_PATH",
    "PackageDependencyPolicyEntry",
    "PackageDependencyPolicyReport",
    "build_package_dependency_policy_report",
    "run",
    "validate_package_dependency_policy",
]


PACKAGE_DEPENDENCY_POLICY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-dependency-policy.toml"
)


@dataclass(frozen=True)
class PackageDependencyPolicyEntry:
    """Allowed outbound dependency directions for one package."""

    distribution_name: str
    allowed_outbound_edges: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class PackageDependencyPolicyReport:
    """Explicit release-blocking package dependency policy."""

    entries: tuple[PackageDependencyPolicyEntry, ...]


def _policy_entry(package_name: str) -> PackageDependencyPolicyEntry:
    if package_name == "agentic-proteins":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-intelligence",
                "bijux-proteomics-runtime",
            ),
            rationale="agentic-proteins stays as a narrow product-layer consumer of canonical core, intelligence, and runtime owners.",
        )
    if package_name == "bijux-proteomics-dev":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-foundation",
                "bijux-proteomics-intelligence",
                "bijux-proteomics-knowledge",
                "bijux-proteomics-lab",
                "bijux-proteomics-runtime",
            ),
            rationale="maintainer governance may inspect publishable packages directly, but it must stay a consumer rather than a product owner.",
        )
    if package_name == "bijux-proteomics-foundation":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(),
            rationale="foundation remains the primitive base and does not import product packages.",
        )
    if package_name == "bijux-proteomics-core":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-foundation",
                "bijux-proteomics-intelligence",
                "bijux-proteomics-lab",
                "bijux-proteomics-runtime",
            ),
            rationale="core currently exposes narrow scientific seams into runtime, intelligence, and lab while remaining grounded on foundation primitives.",
        )
    if package_name == "bijux-proteomics-runtime":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-foundation",
                "bijux-proteomics-intelligence",
            ),
            rationale="runtime depends on core scientific seams, foundation contracts, and a narrow intelligence review path that remains explicitly governed.",
        )
    if package_name == "bijux-proteomics-intelligence":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-foundation",
                "bijux-proteomics-knowledge",
            ),
            rationale="intelligence consumes core scientific semantics, foundation contracts, and knowledge evidence/reference owners.",
        )
    if package_name == "bijux-proteomics-knowledge":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=("bijux-proteomics-foundation",),
            rationale="knowledge stays as cited memory over foundation primitives and does not lean on product-package owners.",
        )
    if package_name == "bijux-proteomics-lab":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-foundation",
                "bijux-proteomics-intelligence",
                "bijux-proteomics-knowledge",
            ),
            rationale="lab consumes core science, intelligence judgment, knowledge evidence, and foundation contracts without owning runtime orchestration.",
        )
    raise KeyError(f"unknown package {package_name!r}")


def build_package_dependency_policy_report() -> PackageDependencyPolicyReport:
    """Build the explicit workspace dependency policy report."""

    return PackageDependencyPolicyReport(
        entries=tuple(_policy_entry(package_name) for package_name in workspace_package_names())
    )


def validate_package_dependency_policy(
    report: PackageDependencyPolicyReport | None = None,
) -> tuple[str, ...]:
    """Fail release when live package dependencies violate the explicit policy."""

    report = report or build_package_dependency_policy_report()
    by_package = {entry.distribution_name: entry for entry in report.entries}
    actual_outbound: dict[str, set[str]] = {
        package_name: set() for package_name in workspace_package_names()
    }
    for edge in build_package_dependency_graph_report().entries:
        actual_outbound[edge.source_distribution].add(edge.target_distribution)

    failures: list[str] = []
    for package_name, actual_edges in sorted(actual_outbound.items()):
        allowed = set(by_package[package_name].allowed_outbound_edges)
        unexpected = sorted(actual_edges - allowed)
        if unexpected:
            failures.append(
                f"{package_name} imports disallowed package edges: {', '.join(unexpected)}"
            )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: PackageDependencyPolicyReport) -> str:
    lines = [
        "# Generated package dependency policy.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.package_dependency_policy",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"allowed_outbound_edges = [{_render_tuple(entry.allowed_outbound_edges)}]",
                f'rationale = "{entry.rationale}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageDependencyPolicyReport) -> bool:
    if not PACKAGE_DEPENDENCY_POLICY_PATH.exists():
        return False
    return PACKAGE_DEPENDENCY_POLICY_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_dependency_policy_report()
    failures = validate_package_dependency_policy(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package dependency policy is up to date")
            return 0
        print("package dependency policy is stale; regenerate it")
        return 1
    PACKAGE_DEPENDENCY_POLICY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package dependency policy")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package dependency policy."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package dependency policy is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
