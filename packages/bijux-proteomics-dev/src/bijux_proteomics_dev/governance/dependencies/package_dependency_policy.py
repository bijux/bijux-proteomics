from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.dependencies.package_dependency_graph import (
    build_package_dependency_graph_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_package_names,
)

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
                "bijux-proteomics-runtime",
            ),
            rationale="agentic-proteins stays as a narrow compatibility bridge that forwards to canonical core and runtime owners only.",
        )
    if package_name == "bijux-proteomics":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=("bijux-proteomics-core",),
            rationale="bijux-proteomics stays as an install-and-command alias for the canonical core package without owning additional product behavior.",
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
                "bijux-proteomics-knowledge",
                "bijux-proteomics-lab",
                "bijux-proteomics-runtime",
            ),
            rationale="core stays grounded on foundation primitives while owning benchmark acceptance and workflow contracts that consume narrow knowledge references plus reviewed seams into runtime, intelligence, and lab.",
        )
    if package_name == "bijux-proteomics-runtime":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-foundation",
                "bijux-proteomics-intelligence",
                "bijux-proteomics-knowledge",
                "bijux-proteomics-lab",
            ),
            rationale="runtime depends on core scientific seams, foundation contracts, and governed downstream review surfaces when it assembles replayable cross-package workflow evidence.",
        )
    if package_name == "bijux-proteomics-intelligence":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-foundation",
                "bijux-proteomics-knowledge",
                "bijux-proteomics-lab",
                "bijux-proteomics-runtime",
            ),
            rationale="intelligence consumes core scientific semantics, foundation contracts, knowledge evidence owners, runtime replay truth, and lab burden signals when it publishes release-facing review posture.",
        )
    if package_name == "bijux-proteomics-knowledge":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-foundation",
            ),
            rationale="knowledge owns grounded evidence memory over foundation primitives and the canonical core interpretation and sequence contracts that normalize cited scientific entities.",
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
    if package_name == "proteomics":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-foundation",
            ),
            rationale="proteomics stays as the short install and import alias for canonical core surfaces while reusing shared alias-helper primitives from foundation.",
        )
    if package_name == "proteomics-core":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-core",
                "bijux-proteomics-foundation",
            ),
            rationale="proteomics-core stays as the short alias for the canonical core distribution while reusing shared alias-helper primitives from foundation.",
        )
    if package_name == "proteomics-foundation":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=("bijux-proteomics-foundation",),
            rationale="proteomics-foundation stays as the short alias for the canonical foundation distribution.",
        )
    if package_name == "proteomics-runtime":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-foundation",
                "bijux-proteomics-runtime",
            ),
            rationale="proteomics-runtime stays as the short alias for the canonical runtime distribution while reusing shared alias-helper primitives from foundation.",
        )
    if package_name == "proteomics-intelligence":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-foundation",
                "bijux-proteomics-intelligence",
            ),
            rationale="proteomics-intelligence stays as the short alias for the canonical intelligence distribution while reusing shared alias-helper primitives from foundation.",
        )
    if package_name == "proteomics-knowledge":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-foundation",
                "bijux-proteomics-knowledge",
            ),
            rationale="proteomics-knowledge stays as the short alias for the canonical knowledge distribution while reusing shared alias-helper primitives from foundation.",
        )
    if package_name == "proteomics-lab":
        return PackageDependencyPolicyEntry(
            distribution_name=package_name,
            allowed_outbound_edges=(
                "bijux-proteomics-foundation",
                "bijux-proteomics-lab",
            ),
            rationale="proteomics-lab stays as the short alias for the canonical lab distribution while reusing shared alias-helper primitives from foundation.",
        )
    raise KeyError(f"unknown package {package_name!r}")


def build_package_dependency_policy_report() -> PackageDependencyPolicyReport:
    """Build the explicit workspace dependency policy report."""

    return PackageDependencyPolicyReport(
        entries=tuple(
            _policy_entry(package_name) for package_name in workspace_package_names()
        )
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
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.dependencies.package_dependency_policy",
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
