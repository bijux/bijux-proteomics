from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_import_inventory import (
    WorkspaceModuleDependencyEdge,
    cross_package_dependency_edges,
    module_dependency_edges,
)
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    workspace_package_names,
)

__all__ = [
    "PACKAGE_RESPONSIBILITY_MAP_PATH",
    "PackageResponsibilityBoundaryGuard",
    "PackageResponsibilityBoundaryViolation",
    "PackageResponsibilityMapEntry",
    "PackageResponsibilityMapReport",
    "build_package_responsibility_map_report",
    "collect_package_responsibility_boundary_violations",
    "evaluate_package_responsibility_boundary_violations",
    "run",
    "validate_package_responsibility_map",
]


PACKAGE_RESPONSIBILITY_MAP_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-responsibility-map.toml"
)


@dataclass(frozen=True)
class PackageResponsibilityMapEntry:
    """One durable package responsibility entry for the workspace."""

    distribution_name: str
    import_root: str
    responsibility_kind: str
    reason_to_exist: str
    must_not_absorb: str
    canonical_surface_targets: tuple[str, ...]


@dataclass(frozen=True)
class PackageResponsibilityBoundaryViolation:
    """One release-blocking violation against the package responsibility map."""

    boundary_name: str
    source_distribution: str
    source_module: str
    target_distribution: str
    target_module: str


@dataclass(frozen=True)
class PackageResponsibilityBoundaryGuard:
    """Release-blocking import boundary ceilings implied by the responsibility map."""

    max_foundation_higher_package_edges: int
    max_knowledge_runtime_edges: int
    max_core_cli_edges: int


@dataclass(frozen=True)
class PackageResponsibilityMapReport:
    """Human-readable and machine-checkable package responsibility map."""

    entries: tuple[PackageResponsibilityMapEntry, ...]
    guard: PackageResponsibilityBoundaryGuard


def _entry(package_name: str) -> PackageResponsibilityMapEntry:
    if package_name == "agentic-proteins":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="compatibility_bridge",
            reason_to_exist=(
                "forward legacy import and packaging expectations into the canonical "
                "core and runtime owners without reviving a second scientific source "
                "of truth"
            ),
            must_not_absorb=(
                "independent scientific logic, new review behavior, or original "
                "workflow engines"
            ),
            canonical_surface_targets=(
                "bijux-proteomics-core",
                "bijux-proteomics-runtime",
            ),
        )
    if package_name == "bijux-proteomics":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="app_wrapper",
            reason_to_exist=(
                "reserve the flagship install name and route users to the canonical "
                "core command and import surface"
            ),
            must_not_absorb=(
                "scientific ownership, recommendation policy, runtime orchestration, "
                "or laboratory follow-up logic"
            ),
            canonical_surface_targets=("bijux-proteomics-core",),
        )
    if package_name == "bijux-proteomics-dev":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="governance",
            reason_to_exist=(
                "own maintainer governance, release checks, architecture audits, "
                "and package-shape validation across the repository"
            ),
            must_not_absorb=(
                "scientific product behavior, runtime execution, or compatibility "
                "alias logic"
            ),
            canonical_surface_targets=("bijux-proteomics-dev",),
        )
    if package_name == "bijux-proteomics-foundation":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="foundation",
            reason_to_exist=(
                "centralize shared document primitives, deterministic "
                "serialization, identifiers, compatibility, and stable outcome "
                "contracts for every higher package"
            ),
            must_not_absorb=(
                "scientific policy, evidence memory, workflow orchestration, lab "
                "execution, runtime transport, or CLI behavior"
            ),
            canonical_surface_targets=("bijux-proteomics-foundation",),
        )
    if package_name == "bijux-proteomics-core":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="core",
            reason_to_exist=(
                "own canonical scientific semantics, review artifacts, benchmark "
                "evidence, workflow seams, and the flagship Python and CLI product "
                "surface"
            ),
            must_not_absorb=(
                "wrapper-only install behavior, runtime transport ownership, or "
                "judgment-only policy that belongs in intelligence"
            ),
            canonical_surface_targets=("bijux-proteomics-core",),
        )
    if package_name == "bijux-proteomics-runtime":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="runtime",
            reason_to_exist=(
                "own execution, persistence, replay, resumability, handoff, and "
                "artifact-valid scientific workflow runtime behavior"
            ),
            must_not_absorb=(
                "canonical scientific law, evidence memory ownership, or wrapper "
                "distribution behavior"
            ),
            canonical_surface_targets=("bijux-proteomics-runtime",),
        )
    if package_name == "bijux-proteomics-intelligence":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="intelligence",
            reason_to_exist=(
                "own analytical judgment, skepticism, questioning, falsification, "
                "and recommendation surfaces over governed scientific outputs"
            ),
            must_not_absorb=(
                "raw evidence storage, low-level execution orchestration, or the "
                "canonical scientific contracts that belong in core and foundation"
            ),
            canonical_surface_targets=("bijux-proteomics-intelligence",),
        )
    if package_name == "bijux-proteomics-knowledge":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="knowledge",
            reason_to_exist=(
                "own structured evidence memory, grounding rules, references, and "
                "graph-oriented knowledge surfaces cited by higher packages"
            ),
            must_not_absorb=(
                "runtime orchestration, recommendation logic, or laboratory "
                "execution ownership"
            ),
            canonical_surface_targets=("bijux-proteomics-knowledge",),
        )
    if package_name == "bijux-proteomics-lab":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="lab",
            reason_to_exist=(
                "own laboratory feasibility, assay planning, operator handoff, and "
                "real-world follow-up surfaces around the scientific engine"
            ),
            must_not_absorb=(
                "runtime transport ownership, canonical evidence memory, or "
                "duplicate scientific source-of-truth logic"
            ),
            canonical_surface_targets=("bijux-proteomics-lab",),
        )
    if package_name == "proteomics":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="short_alias",
            reason_to_exist=(
                "provide the short install and import alias for the canonical core "
                "surface without creating a second owner"
            ),
            must_not_absorb=(
                "independent scientific logic, execution policy, or package-local "
                "workflow behavior"
            ),
            canonical_surface_targets=("bijux-proteomics-core",),
        )
    if package_name == "proteomics-core":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="short_alias",
            reason_to_exist=(
                "provide the short distribution alias for the canonical core package"
            ),
            must_not_absorb=(
                "independent scientific logic, execution policy, or package-local "
                "workflow behavior"
            ),
            canonical_surface_targets=("bijux-proteomics-core",),
        )
    if package_name == "proteomics-foundation":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="short_alias",
            reason_to_exist=(
                "provide the short distribution alias for the canonical foundation "
                "package"
            ),
            must_not_absorb=(
                "independent scientific logic, higher-package policy, or wrapper "
                "runtime behavior"
            ),
            canonical_surface_targets=("bijux-proteomics-foundation",),
        )
    if package_name == "proteomics-runtime":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="short_alias",
            reason_to_exist=(
                "provide the short distribution alias for the canonical runtime package"
            ),
            must_not_absorb=(
                "independent workflow runtime logic, scientific semantics, or alias-"
                "local product behavior"
            ),
            canonical_surface_targets=("bijux-proteomics-runtime",),
        )
    if package_name == "proteomics-intelligence":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="short_alias",
            reason_to_exist=(
                "provide the short distribution alias for the canonical intelligence "
                "package"
            ),
            must_not_absorb=(
                "independent recommendation logic, evidence ownership, or alias-"
                "local analytical behavior"
            ),
            canonical_surface_targets=("bijux-proteomics-intelligence",),
        )
    if package_name == "proteomics-knowledge":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="short_alias",
            reason_to_exist=(
                "provide the short distribution alias for the canonical knowledge package"
            ),
            must_not_absorb=(
                "independent evidence memory logic, runtime behavior, or alias-local "
                "scientific ownership"
            ),
            canonical_surface_targets=("bijux-proteomics-knowledge",),
        )
    if package_name == "proteomics-lab":
        return PackageResponsibilityMapEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            responsibility_kind="short_alias",
            reason_to_exist=(
                "provide the short distribution alias for the canonical lab package"
            ),
            must_not_absorb=(
                "independent laboratory logic, runtime behavior, or alias-local "
                "scientific ownership"
            ),
            canonical_surface_targets=("bijux-proteomics-lab",),
        )
    raise KeyError(f"unknown package {package_name!r}")


def build_package_responsibility_map_report() -> PackageResponsibilityMapReport:
    """Build the checked workspace package responsibility map."""

    return PackageResponsibilityMapReport(
        entries=tuple(
            _entry(package_name) for package_name in workspace_package_names()
        ),
        guard=PackageResponsibilityBoundaryGuard(
            max_foundation_higher_package_edges=0,
            max_knowledge_runtime_edges=0,
            max_core_cli_edges=0,
        ),
    )


def collect_package_responsibility_boundary_violations() -> tuple[
    PackageResponsibilityBoundaryViolation, ...
]:
    """Return live import-direction violations against the responsibility map."""

    return evaluate_package_responsibility_boundary_violations(
        foundation_edges=tuple(
            edge
            for edge in cross_package_dependency_edges()
            if edge.source_distribution == "bijux-proteomics-foundation"
        ),
        knowledge_edges=tuple(
            edge
            for edge in cross_package_dependency_edges()
            if edge.source_distribution == "bijux-proteomics-knowledge"
        ),
        core_internal_edges=tuple(
            edge
            for edge in module_dependency_edges("bijux-proteomics-core")
            if edge.internal
        ),
    )


def evaluate_package_responsibility_boundary_violations(
    *,
    foundation_edges: tuple[WorkspaceModuleDependencyEdge, ...],
    knowledge_edges: tuple[WorkspaceModuleDependencyEdge, ...],
    core_internal_edges: tuple[WorkspaceModuleDependencyEdge, ...],
) -> tuple[PackageResponsibilityBoundaryViolation, ...]:
    """Evaluate the explicit boundary rules required by the responsibility map."""

    violations: list[PackageResponsibilityBoundaryViolation] = []
    for edge in foundation_edges:
        violations.append(
            PackageResponsibilityBoundaryViolation(
                boundary_name="foundation_higher_package_import",
                source_distribution=edge.source_distribution,
                source_module=edge.source_module,
                target_distribution=edge.target_distribution,
                target_module=edge.target_module,
            )
        )
    for edge in knowledge_edges:
        if edge.target_distribution != "bijux-proteomics-runtime":
            continue
        violations.append(
            PackageResponsibilityBoundaryViolation(
                boundary_name="knowledge_runtime_import",
                source_distribution=edge.source_distribution,
                source_module=edge.source_module,
                target_distribution=edge.target_distribution,
                target_module=edge.target_module,
            )
        )
    for edge in core_internal_edges:
        if edge.source_module.startswith("bijux_proteomics.interfaces.cli"):
            continue
        if not edge.target_module.startswith("bijux_proteomics.interfaces.cli"):
            continue
        violations.append(
            PackageResponsibilityBoundaryViolation(
                boundary_name="core_cli_import",
                source_distribution=edge.source_distribution,
                source_module=edge.source_module,
                target_distribution=edge.target_distribution,
                target_module=edge.target_module,
            )
        )
    return tuple(
        sorted(
            violations,
            key=lambda violation: (
                violation.boundary_name,
                violation.source_distribution,
                violation.source_module,
                violation.target_distribution,
                violation.target_module,
            ),
        )
    )


def validate_package_responsibility_map(
    report: PackageResponsibilityMapReport | None = None,
) -> tuple[str, ...]:
    """Fail release when package responsibility boundaries drift."""

    report = report or build_package_responsibility_map_report()
    violations = collect_package_responsibility_boundary_violations()
    failures: list[str] = []
    foundation_count = sum(
        violation.boundary_name == "foundation_higher_package_import"
        for violation in violations
    )
    knowledge_count = sum(
        violation.boundary_name == "knowledge_runtime_import"
        for violation in violations
    )
    core_cli_count = sum(
        violation.boundary_name == "core_cli_import" for violation in violations
    )
    if foundation_count > report.guard.max_foundation_higher_package_edges:
        failures.extend(
            _format_violation(violation)
            for violation in violations
            if violation.boundary_name == "foundation_higher_package_import"
        )
    if knowledge_count > report.guard.max_knowledge_runtime_edges:
        failures.extend(
            _format_violation(violation)
            for violation in violations
            if violation.boundary_name == "knowledge_runtime_import"
        )
    if core_cli_count > report.guard.max_core_cli_edges:
        failures.extend(
            _format_violation(violation)
            for violation in violations
            if violation.boundary_name == "core_cli_import"
        )
    return tuple(failures)


def _format_violation(violation: PackageResponsibilityBoundaryViolation) -> str:
    if violation.boundary_name == "foundation_higher_package_import":
        return (
            "foundation imported a higher package module: "
            f"{violation.source_module} -> {violation.target_module}"
        )
    if violation.boundary_name == "knowledge_runtime_import":
        return (
            "knowledge imported runtime: "
            f"{violation.source_module} -> {violation.target_module}"
        )
    return (
        "core imported app or cli code from a non-cli module: "
        f"{violation.source_module} -> {violation.target_module}"
    )


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: PackageResponsibilityMapReport) -> str:
    lines = [
        "# Generated package responsibility map.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.dependencies.package_responsibility_map",
        "",
        "[guard]",
        "max_foundation_higher_package_edges = "
        f"{report.guard.max_foundation_higher_package_edges}",
        f"max_knowledge_runtime_edges = {report.guard.max_knowledge_runtime_edges}",
        f"max_core_cli_edges = {report.guard.max_core_cli_edges}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'import_root = "{entry.import_root}"',
                f'responsibility_kind = "{entry.responsibility_kind}"',
                f'reason_to_exist = "{entry.reason_to_exist}"',
                f'must_not_absorb = "{entry.must_not_absorb}"',
                "canonical_surface_targets = "
                f"[{_render_tuple(entry.canonical_surface_targets)}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageResponsibilityMapReport) -> bool:
    if not PACKAGE_RESPONSIBILITY_MAP_PATH.exists():
        return False
    return PACKAGE_RESPONSIBILITY_MAP_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_responsibility_map_report()
    failures = validate_package_responsibility_map(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package responsibility map is up to date")
            return 0
        print("package responsibility map is stale; regenerate it")
        return 1
    PACKAGE_RESPONSIBILITY_MAP_PATH.write_text(
        _toml_text(report),
        encoding="utf-8",
    )
    print("generated package responsibility map")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package responsibility map."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package responsibility map is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
