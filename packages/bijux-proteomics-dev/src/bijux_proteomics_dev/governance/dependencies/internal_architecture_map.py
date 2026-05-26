from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.dependencies.package_dependency_policy import (
    PackageDependencyPolicyEntry,
    build_package_dependency_policy_report,
)
from bijux_proteomics_dev.governance.dependencies.package_dependency_graph import (
    build_package_dependency_graph_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    WorkspaceModuleDependencyEdge,
    cross_package_dependency_edges,
    module_dependency_edges,
)
from bijux_proteomics_dev.quality.architecture.circular_dependencies import (
    find_workspace_dependency_cycles,
)

__all__ = [
    "INTERNAL_ARCHITECTURE_MAP_PATH",
    "InternalArchitectureCycleGuard",
    "InternalArchitectureMapReport",
    "InternalArchitectureModuleFamilyEntry",
    "InternalArchitecturePackageEntry",
    "InternalArchitectureViolation",
    "build_internal_architecture_map_report",
    "evaluate_internal_architecture_violations",
    "is_internal_architecture_map_up_to_date",
    "run",
]


INTERNAL_ARCHITECTURE_MAP_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "internal-architecture-map.toml"
)

_CORE_WORKFLOW_COMPATIBILITY_MODULES = (
    "bijux_proteomics.workflow.advanced_diann",
    "bijux_proteomics.workflow.advanced_fragpipe",
    "bijux_proteomics.workflow.advanced_maxquant",
    "bijux_proteomics.workflow.advanced_ptm",
    "bijux_proteomics.workflow.advanced_targeted",
    "bijux_proteomics.workflow.advanced_tmt",
    "bijux_proteomics.workflow.discovery_to_assay",
    "bijux_proteomics.workflow.flagship_run",
    "bijux_proteomics.workflow.integrated_scientific_report",
    "bijux_proteomics.workflow.multi_study",
    "bijux_proteomics.workflow.orchestrator",
    "bijux_proteomics.workflow.public_benchmark_runner",
    "bijux_proteomics.workflow.surprising_demo",
    "bijux_proteomics.workflow.surprising_demo_interrogation",
    "bijux_proteomics.workflow.trust_bundle",
)


@dataclass(frozen=True)
class InternalArchitecturePackageEntry:
    """Allowed outbound package dependencies for one distribution."""

    distribution_name: str
    allowed_outbound_edges: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class InternalArchitectureModuleFamilyEntry:
    """One internal module family and the families it may import."""

    distribution_name: str
    family_name: str
    module_prefixes: tuple[str, ...]
    allowed_outbound_families: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class InternalArchitectureCycleGuard:
    """Release-blocking workspace cycle guard."""

    max_workspace_cycle_count: int


@dataclass(frozen=True)
class InternalArchitectureMapReport:
    """Machine-checkable internal architecture map."""

    package_entries: tuple[InternalArchitecturePackageEntry, ...]
    module_family_entries: tuple[InternalArchitectureModuleFamilyEntry, ...]
    cycle_guard: InternalArchitectureCycleGuard


@dataclass(frozen=True)
class InternalArchitectureViolation:
    """One release-blocking internal architecture violation."""

    boundary_name: str
    detail: str


def _package_entry_from_policy(
    entry: PackageDependencyPolicyEntry,
) -> InternalArchitecturePackageEntry:
    return InternalArchitecturePackageEntry(
        distribution_name=entry.distribution_name,
        allowed_outbound_edges=entry.allowed_outbound_edges,
        rationale=entry.rationale,
    )


def _core_module_family_entries() -> tuple[InternalArchitectureModuleFamilyEntry, ...]:
    distribution_name = "bijux-proteomics-core"
    return (
        InternalArchitectureModuleFamilyEntry(
            distribution_name=distribution_name,
            family_name="workflow_compatibility",
            module_prefixes=_CORE_WORKFLOW_COMPATIBILITY_MODULES,
            allowed_outbound_families=("workflow_pipelines",),
            rationale="root workflow wrapper modules stay as compatibility facades that forward only to the canonical pipeline owners.",
        ),
        InternalArchitectureModuleFamilyEntry(
            distribution_name=distribution_name,
            family_name="workflow_pipelines",
            module_prefixes=("bijux_proteomics.workflow.pipelines",),
            allowed_outbound_families=("benchmarks", "workflow_scientific"),
            rationale="workflow pipelines may assemble governed workflow support and benchmark inputs, but they do not reach back into interfaces or compatibility facades.",
        ),
        InternalArchitectureModuleFamilyEntry(
            distribution_name=distribution_name,
            family_name="workflow_scientific",
            module_prefixes=("bijux_proteomics.workflow",),
            allowed_outbound_families=("workflow_compatibility", "workflow_pipelines"),
            rationale="non-pipeline workflow modules may expose package surfaces and consume pipeline manifests, while their scientific engines stay within the workflow family.",
        ),
        InternalArchitectureModuleFamilyEntry(
            distribution_name=distribution_name,
            family_name="interfaces",
            module_prefixes=("bijux_proteomics.interfaces",),
            allowed_outbound_families=(
                "benchmarks",
                "workflow_pipelines",
                "workflow_scientific",
            ),
            rationale="interfaces may invoke workflow pipelines and selected scientific report surfaces, but they do not become scientific owners themselves.",
        ),
        InternalArchitectureModuleFamilyEntry(
            distribution_name=distribution_name,
            family_name="benchmarks",
            module_prefixes=("bijux_proteomics.benchmarks",),
            allowed_outbound_families=("workflow_pipelines", "workflow_scientific"),
            rationale="benchmarks may exercise canonical workflow pipelines and inspect scientific artifacts, but they do not route through interfaces.",
        ),
    )


def build_internal_architecture_map_report() -> InternalArchitectureMapReport:
    """Build the generated internal architecture map."""

    policy_report = build_package_dependency_policy_report()
    policy_by_package = {
        entry.distribution_name: entry for entry in policy_report.entries
    }
    outbound_by_package: dict[str, set[str]] = {
        entry.distribution_name: set() for entry in policy_report.entries
    }
    for edge in build_package_dependency_graph_report().entries:
        outbound_by_package.setdefault(edge.source_distribution, set()).add(
            edge.target_distribution
        )
    return InternalArchitectureMapReport(
        package_entries=tuple(
            InternalArchitecturePackageEntry(
                distribution_name=distribution_name,
                allowed_outbound_edges=tuple(sorted(outbound_by_package[distribution_name])),
                rationale=policy_by_package[distribution_name].rationale,
            )
            for distribution_name in sorted(outbound_by_package)
        ),
        module_family_entries=_core_module_family_entries(),
        cycle_guard=InternalArchitectureCycleGuard(max_workspace_cycle_count=0),
    )


def _classifier_for_distribution(
    entries: tuple[InternalArchitectureModuleFamilyEntry, ...],
    distribution_name: str,
):
    candidates = tuple(
        sorted(
            (
                entry
                for entry in entries
                if entry.distribution_name == distribution_name
            ),
            key=lambda entry: max(len(prefix) for prefix in entry.module_prefixes),
            reverse=True,
        )
    )

    def classify(module_name: str) -> str | None:
        for entry in candidates:
            if any(
                module_name == prefix or module_name.startswith(prefix + ".")
                for prefix in entry.module_prefixes
            ):
                return entry.family_name
        return None

    return classify


def _coverage_prefixes(
    entries: tuple[InternalArchitectureModuleFamilyEntry, ...],
    distribution_name: str,
) -> tuple[str, ...]:
    prefixes: set[str] = set()
    for entry in entries:
        if entry.distribution_name == distribution_name:
            prefixes.update(entry.module_prefixes)
    return tuple(sorted(prefixes))


def _module_is_covered(module_name: str, prefixes: tuple[str, ...]) -> bool:
    return any(module_name == prefix or module_name.startswith(prefix + ".") for prefix in prefixes)


def evaluate_internal_architecture_violations(
    report: InternalArchitectureMapReport | None = None,
    *,
    package_edges: tuple[WorkspaceModuleDependencyEdge, ...] | None = None,
    module_edges: tuple[WorkspaceModuleDependencyEdge, ...] | None = None,
    workspace_cycles: tuple[tuple[str, ...], ...] | None = None,
) -> tuple[InternalArchitectureViolation, ...]:
    """Evaluate live or synthetic edges against the internal architecture map."""

    report = report or build_internal_architecture_map_report()
    violations: list[InternalArchitectureViolation] = []

    if package_edges is None:
        package_edges = cross_package_dependency_edges()
    actual_outbound: dict[str, set[str]] = {
        entry.distribution_name: set() for entry in report.package_entries
    }
    for edge in package_edges:
        actual_outbound.setdefault(edge.source_distribution, set()).add(
            edge.target_distribution
        )

    for entry in report.package_entries:
        unexpected = sorted(actual_outbound.get(entry.distribution_name, set()) - set(entry.allowed_outbound_edges))
        if unexpected:
            violations.append(
                InternalArchitectureViolation(
                    boundary_name="package_outbound_edge",
                    detail=(
                        f"{entry.distribution_name} imports disallowed package edges: "
                        f"{', '.join(unexpected)}"
                    ),
                )
            )

    family_entries_by_name = {
        (entry.distribution_name, entry.family_name): entry
        for entry in report.module_family_entries
    }
    distributions = sorted({entry.distribution_name for entry in report.module_family_entries})
    if module_edges is None:
        module_edges = tuple(
            edge
            for distribution_name in distributions
            for edge in module_dependency_edges(distribution_name)
            if edge.internal
        )

    for distribution_name in distributions:
        classify = _classifier_for_distribution(report.module_family_entries, distribution_name)
        covered_prefixes = _coverage_prefixes(report.module_family_entries, distribution_name)
        for edge in module_edges:
            if edge.source_distribution != distribution_name or not edge.internal:
                continue
            if not _module_is_covered(edge.source_module, covered_prefixes):
                continue
            source_family = classify(edge.source_module)
            if source_family is None:
                violations.append(
                    InternalArchitectureViolation(
                        boundary_name="unclassified_source_module",
                        detail=(
                            f"{distribution_name} source module {edge.source_module} is "
                            "inside covered architecture space but is not assigned to a family"
                        ),
                    )
                )
                continue
            if not _module_is_covered(edge.target_module, covered_prefixes):
                continue
            target_family = classify(edge.target_module)
            if target_family is None:
                violations.append(
                    InternalArchitectureViolation(
                        boundary_name="unclassified_target_module",
                        detail=(
                            f"{distribution_name} target module {edge.target_module} is "
                            "inside covered architecture space but is not assigned to a family"
                        ),
                    )
                )
                continue
            if source_family == target_family:
                continue
            source_entry = family_entries_by_name[(distribution_name, source_family)]
            if target_family not in source_entry.allowed_outbound_families:
                violations.append(
                    InternalArchitectureViolation(
                        boundary_name="module_family_outbound_edge",
                        detail=(
                            f"{edge.source_module} in {source_family} imports "
                            f"{edge.target_module} in {target_family}, which is outside "
                            "the governed internal architecture map"
                        ),
                    )
                )

    if workspace_cycles is None:
        workspace_cycles = find_workspace_dependency_cycles(REPO_ROOT)
    if len(workspace_cycles) > report.cycle_guard.max_workspace_cycle_count:
        for cycle in workspace_cycles:
            violations.append(
                InternalArchitectureViolation(
                    boundary_name="workspace_cycle",
                    detail=" -> ".join([*cycle, cycle[0]]),
                )
            )
    return tuple(violations)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: InternalArchitectureMapReport) -> str:
    lines = [
        "# Generated internal architecture map.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.dependencies.internal_architecture_map",
        "",
        "[cycle_guard]",
        f"max_workspace_cycle_count = {report.cycle_guard.max_workspace_cycle_count}",
        "",
    ]
    for entry in report.package_entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"allowed_outbound_edges = [{_render_tuple(entry.allowed_outbound_edges)}]",
                f'rationale = "{entry.rationale}"',
                "",
            ]
        )
    for entry in report.module_family_entries:
        lines.extend(
            [
                "[[module_family]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'family_name = "{entry.family_name}"',
                f"module_prefixes = [{_render_tuple(entry.module_prefixes)}]",
                f"allowed_outbound_families = [{_render_tuple(entry.allowed_outbound_families)}]",
                f'rationale = "{entry.rationale}"',
                "",
            ]
        )
    return "\n".join(lines)


def is_internal_architecture_map_up_to_date(
    report: InternalArchitectureMapReport,
) -> bool:
    if not INTERNAL_ARCHITECTURE_MAP_PATH.exists():
        return False
    return INTERNAL_ARCHITECTURE_MAP_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_internal_architecture_map_report()
    failures = evaluate_internal_architecture_violations(report)
    if failures:
        for failure in failures:
            print(failure.detail)
        return 1
    if check:
        if is_internal_architecture_map_up_to_date(report):
            print("internal architecture map is up to date")
            return 0
        print("internal architecture map is stale; regenerate it")
        return 1
    INTERNAL_ARCHITECTURE_MAP_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated internal architecture map")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the internal architecture map."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the internal architecture map is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
