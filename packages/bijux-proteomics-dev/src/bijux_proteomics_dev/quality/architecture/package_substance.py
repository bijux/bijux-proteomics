from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from bijux_proteomics_dev.quality.architecture.agentic_compatibility_inventory import (
    AgenticModuleClassification,
    build_agentic_compatibility_inventory,
    validate_agentic_compatibility_inventory,
)
from bijux_proteomics_dev.quality.graphs.package_graph import (
    WorkspacePackage,
    load_workspace_packages,
)
from bijux_proteomics_foundation.support.charter import (
    DEFAULT_FOUNDATION_MODULE_AUDIT,
    FoundationModuleClassification,
)
from bijux_proteomics_intelligence.governance.charter import (
    DEFAULT_INTELLIGENCE_MODULE_AUDIT,
    IntelligenceModuleClassification,
)
from bijux_proteomics_knowledge.governance.charter import (
    DEFAULT_KNOWLEDGE_MODULE_AUDIT,
    KnowledgeModuleClassification,
)
from bijux_proteomics_lab.governance.charter import (
    DEFAULT_LAB_MODULE_AUDIT,
    LabModuleClassification,
)
from bijux_proteomics_runtime.governance.charter import (
    DEFAULT_RUNTIME_MODULE_AUDIT,
    RuntimeModuleClassification,
)

__all__ = [
    "PACKAGE_SUBSTANCE_CSV_PATH",
    "PACKAGE_SUBSTANCE_SUMMARY_PATH",
    "PackageBoundaryRole",
    "PackageSubstanceEntry",
    "PackageSubstanceIssue",
    "build_package_substance_inventory",
    "run",
    "validate_package_substance",
]


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "packages").exists():
            return parent
    raise RuntimeError("Unable to resolve repository root for package substance")


REPO_ROOT = _repo_root()
PACKAGE_SUBSTANCE_CSV_PATH = (
    REPO_ROOT
    / "docs"
    / "08-bijux-proteomics-maintain"
    / "bijux-proteomics-dev"
    / "package-substance.csv"
)
PACKAGE_SUBSTANCE_SUMMARY_PATH = (
    REPO_ROOT
    / "docs"
    / "08-bijux-proteomics-maintain"
    / "bijux-proteomics-dev"
    / "package-substance.md"
)


class PackageBoundaryRole(StrEnum):
    """Durable package roles in the proteomics suite."""

    CANONICAL_PRODUCT = "canonical_product"
    SHARED_KERNEL = "shared_kernel"
    COMPATIBILITY_BRIDGE = "compatibility_bridge"
    MAINTAINER_SUPPORT = "maintainer_support"


@dataclass(frozen=True)
class PackageSubstanceEntry:
    """One package-boundary substance record."""

    package_name: str
    boundary_role: PackageBoundaryRole
    source_module_count: int
    owned_logic_count: int
    wrapper_module_count: int
    thin_module_count: int
    evidence_locator: str
    ready: bool


@dataclass(frozen=True)
class PackageSubstanceIssue:
    """One release-blocking package substance issue."""

    code: str
    detail: str


@dataclass(frozen=True)
class _PackageSubstanceExpectation:
    boundary_role: PackageBoundaryRole
    minimum_owned_logic_count: int
    maximum_thin_module_count: int
    evidence_locator: str


_CANONICAL_PRODUCT_EXPECTATIONS = {
    "bijux-proteomics-core": _PackageSubstanceExpectation(
        boundary_role=PackageBoundaryRole.CANONICAL_PRODUCT,
        minimum_owned_logic_count=70,
        maximum_thin_module_count=70,
        evidence_locator="packages/bijux-proteomics-core/src/bijux_proteomics/",
    ),
    "bijux-proteomics-foundation": _PackageSubstanceExpectation(
        boundary_role=PackageBoundaryRole.SHARED_KERNEL,
        minimum_owned_logic_count=12,
        maximum_thin_module_count=2,
        evidence_locator=(
            "packages/bijux-proteomics-foundation/src/"
            "bijux_proteomics_foundation/support/charter.py"
        ),
    ),
    "bijux-proteomics-runtime": _PackageSubstanceExpectation(
        boundary_role=PackageBoundaryRole.CANONICAL_PRODUCT,
        minimum_owned_logic_count=60,
        maximum_thin_module_count=35,
        evidence_locator=(
            "packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/governance/charter.py"
        ),
    ),
    "bijux-proteomics-intelligence": _PackageSubstanceExpectation(
        boundary_role=PackageBoundaryRole.CANONICAL_PRODUCT,
        minimum_owned_logic_count=8,
        maximum_thin_module_count=2,
        evidence_locator=(
            "packages/bijux-proteomics-intelligence/src/"
            "bijux_proteomics_intelligence/governance/charter.py"
        ),
    ),
    "bijux-proteomics-knowledge": _PackageSubstanceExpectation(
        boundary_role=PackageBoundaryRole.CANONICAL_PRODUCT,
        minimum_owned_logic_count=12,
        maximum_thin_module_count=22,
        evidence_locator=(
            "packages/bijux-proteomics-knowledge/src/"
            "bijux_proteomics_knowledge/governance/charter.py"
        ),
    ),
    "bijux-proteomics-lab": _PackageSubstanceExpectation(
        boundary_role=PackageBoundaryRole.CANONICAL_PRODUCT,
        minimum_owned_logic_count=10,
        maximum_thin_module_count=10,
        evidence_locator=(
            "packages/bijux-proteomics-lab/src/bijux_proteomics_lab/governance/charter.py"
        ),
    ),
    "agentic-proteins": _PackageSubstanceExpectation(
        boundary_role=PackageBoundaryRole.COMPATIBILITY_BRIDGE,
        minimum_owned_logic_count=0,
        maximum_thin_module_count=0,
        evidence_locator=(
            "packages/bijux-proteomics-dev/src/bijux_proteomics_dev/quality/"
            "architecture/agentic_compatibility_inventory.py"
        ),
    ),
    "bijux-proteomics-dev": _PackageSubstanceExpectation(
        boundary_role=PackageBoundaryRole.MAINTAINER_SUPPORT,
        minimum_owned_logic_count=20,
        maximum_thin_module_count=12,
        evidence_locator="packages/bijux-proteomics-dev/src/bijux_proteomics_dev/",
    ),
}

FOUNDATION_COMPATIBILITY_WRAPPER_PATHS: frozenset[str] = frozenset()


def _source_module_paths(package: WorkspacePackage) -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in package.src_dir.rglob("*.py")
            if "__pycache__" not in path.parts
        )
    )


def _core_entry(package: WorkspacePackage) -> PackageSubstanceEntry:
    source_paths = _source_module_paths(package)
    thin_module_count = sum(1 for path in source_paths if path.name == "__init__.py")
    owned_logic_count = len(source_paths) - thin_module_count
    expectation = _CANONICAL_PRODUCT_EXPECTATIONS[package.package_name]
    return PackageSubstanceEntry(
        package_name=package.package_name,
        boundary_role=expectation.boundary_role,
        source_module_count=len(source_paths),
        owned_logic_count=owned_logic_count,
        wrapper_module_count=0,
        thin_module_count=thin_module_count,
        evidence_locator=expectation.evidence_locator,
        ready=(
            owned_logic_count >= expectation.minimum_owned_logic_count
            and thin_module_count <= expectation.maximum_thin_module_count
        ),
    )


def _charter_backed_entry(
    package_name: str,
    package: WorkspacePackage,
    *,
    audit: tuple[object, ...],
    owned_logic_value: str,
    thin_value: str,
) -> PackageSubstanceEntry:
    source_paths = _source_module_paths(package)
    counts = Counter(
        str(getattr(getattr(entry, "classification", ""), "value", ""))
        for entry in audit
    )
    expectation = _CANONICAL_PRODUCT_EXPECTATIONS[package_name]
    owned_logic_count = counts[owned_logic_value]
    thin_module_count = counts[thin_value]
    return PackageSubstanceEntry(
        package_name=package_name,
        boundary_role=expectation.boundary_role,
        source_module_count=len(source_paths),
        owned_logic_count=owned_logic_count,
        wrapper_module_count=0,
        thin_module_count=thin_module_count,
        evidence_locator=expectation.evidence_locator,
        ready=(
            owned_logic_count >= expectation.minimum_owned_logic_count
            and thin_module_count <= expectation.maximum_thin_module_count
        ),
    )


def _foundation_kernel_entry(package: WorkspacePackage) -> PackageSubstanceEntry:
    source_paths = _source_module_paths(package)
    counts = Counter(
        entry.classification.value for entry in DEFAULT_FOUNDATION_MODULE_AUDIT
    )
    expectation = _CANONICAL_PRODUCT_EXPECTATIONS["bijux-proteomics-foundation"]
    wrapper_module_count = len(
        [
            entry
            for entry in DEFAULT_FOUNDATION_MODULE_AUDIT
            if entry.module_path in FOUNDATION_COMPATIBILITY_WRAPPER_PATHS
        ]
    )
    thin_module_count = len(
        [
            entry
            for entry in DEFAULT_FOUNDATION_MODULE_AUDIT
            if (
                entry.classification is FoundationModuleClassification.THIN_ABSTRACTION
                and entry.module_path not in FOUNDATION_COMPATIBILITY_WRAPPER_PATHS
            )
        ]
    )
    return PackageSubstanceEntry(
        package_name="bijux-proteomics-foundation",
        boundary_role=expectation.boundary_role,
        source_module_count=len(source_paths),
        owned_logic_count=counts[
            FoundationModuleClassification.SHARED_CONTRACT_VALUE.value
        ],
        wrapper_module_count=wrapper_module_count,
        thin_module_count=thin_module_count,
        evidence_locator=expectation.evidence_locator,
        ready=(
            counts[FoundationModuleClassification.SHARED_CONTRACT_VALUE.value]
            >= expectation.minimum_owned_logic_count
            and thin_module_count <= expectation.maximum_thin_module_count
        ),
    )


def _compatibility_bridge_entry(package: WorkspacePackage) -> PackageSubstanceEntry:
    source_paths = _source_module_paths(package)
    inventory = build_agentic_compatibility_inventory(REPO_ROOT)
    counts = Counter(entry.classification.value for entry in inventory)
    wrapper_module_count = counts[AgenticModuleClassification.WRAPPER.value]
    expectation = _CANONICAL_PRODUCT_EXPECTATIONS[package.package_name]
    return PackageSubstanceEntry(
        package_name=package.package_name,
        boundary_role=expectation.boundary_role,
        source_module_count=len(source_paths),
        owned_logic_count=0,
        wrapper_module_count=wrapper_module_count,
        thin_module_count=0,
        evidence_locator=expectation.evidence_locator,
        ready=all(
            entry.classification
            in {
                AgenticModuleClassification.WRAPPER,
                AgenticModuleClassification.DEAD,
            }
            for entry in inventory
        ),
    )


def _maintainer_support_entry(package: WorkspacePackage) -> PackageSubstanceEntry:
    source_paths = _source_module_paths(package)
    thin_module_count = sum(1 for path in source_paths if path.name == "__init__.py")
    owned_logic_count = len(source_paths) - thin_module_count
    expectation = _CANONICAL_PRODUCT_EXPECTATIONS[package.package_name]
    return PackageSubstanceEntry(
        package_name=package.package_name,
        boundary_role=expectation.boundary_role,
        source_module_count=len(source_paths),
        owned_logic_count=owned_logic_count,
        wrapper_module_count=0,
        thin_module_count=thin_module_count,
        evidence_locator=expectation.evidence_locator,
        ready=(
            owned_logic_count >= expectation.minimum_owned_logic_count
            and thin_module_count <= expectation.maximum_thin_module_count
        ),
    )


def build_package_substance_inventory(
    repo_root: Path,
) -> tuple[PackageSubstanceEntry, ...]:
    """Build the package-boundary substance inventory across the workspace."""

    package_by_name = {
        package.package_name: package for package in load_workspace_packages(repo_root)
    }
    entries = [
        _compatibility_bridge_entry(package_by_name["agentic-proteins"]),
        _maintainer_support_entry(package_by_name["bijux-proteomics-dev"]),
        _core_entry(package_by_name["bijux-proteomics-core"]),
        _foundation_kernel_entry(package_by_name["bijux-proteomics-foundation"]),
        _charter_backed_entry(
            "bijux-proteomics-runtime",
            package_by_name["bijux-proteomics-runtime"],
            audit=DEFAULT_RUNTIME_MODULE_AUDIT,
            owned_logic_value=RuntimeModuleClassification.EXECUTION_VALUE.value,
            thin_value=RuntimeModuleClassification.THIN_ABSTRACTION.value,
        ),
        _charter_backed_entry(
            "bijux-proteomics-intelligence",
            package_by_name["bijux-proteomics-intelligence"],
            audit=DEFAULT_INTELLIGENCE_MODULE_AUDIT,
            owned_logic_value=IntelligenceModuleClassification.ANALYTICAL_VALUE.value,
            thin_value=IntelligenceModuleClassification.THIN_ABSTRACTION.value,
        ),
        _charter_backed_entry(
            "bijux-proteomics-knowledge",
            package_by_name["bijux-proteomics-knowledge"],
            audit=DEFAULT_KNOWLEDGE_MODULE_AUDIT,
            owned_logic_value=KnowledgeModuleClassification.CURATED_REFERENCE_VALUE.value,
            thin_value=KnowledgeModuleClassification.THIN_PLACEHOLDER.value,
        ),
        _charter_backed_entry(
            "bijux-proteomics-lab",
            package_by_name["bijux-proteomics-lab"],
            audit=DEFAULT_LAB_MODULE_AUDIT,
            owned_logic_value=LabModuleClassification.OPERATIONAL_VALUE.value,
            thin_value=LabModuleClassification.THIN_ABSTRACTION.value,
        ),
    ]
    return tuple(sorted(entries, key=lambda entry: entry.package_name))


def validate_package_substance(repo_root: Path) -> tuple[PackageSubstanceIssue, ...]:
    """Validate that every package boundary still has enough live substance."""

    issues: list[PackageSubstanceIssue] = []
    entries = build_package_substance_inventory(repo_root)
    seen_packages = {entry.package_name for entry in entries}
    expected_packages = set(_CANONICAL_PRODUCT_EXPECTATIONS)
    if seen_packages != expected_packages:
        issues.append(
            PackageSubstanceIssue(
                code="package-coverage-mismatch",
                detail=(
                    "package substance inventory covers "
                    f"{sorted(seen_packages)} instead of {sorted(expected_packages)}"
                ),
            )
        )
    for entry in entries:
        expectation = _CANONICAL_PRODUCT_EXPECTATIONS[entry.package_name]
        if entry.boundary_role is not expectation.boundary_role:
            issues.append(
                PackageSubstanceIssue(
                    code="boundary-role-drift",
                    detail=(
                        f"{entry.package_name} resolved as {entry.boundary_role.value} "
                        f"instead of {expectation.boundary_role.value}"
                    ),
                )
            )
        if entry.boundary_role is PackageBoundaryRole.CANONICAL_PRODUCT:
            if entry.owned_logic_count < expectation.minimum_owned_logic_count:
                issues.append(
                    PackageSubstanceIssue(
                        code="insufficient-owned-logic",
                        detail=(
                            f"{entry.package_name} exposes only {entry.owned_logic_count} "
                            "owned-logic modules and is too thin to justify its release boundary"
                        ),
                    )
                )
            if entry.thin_module_count > expectation.maximum_thin_module_count:
                issues.append(
                    PackageSubstanceIssue(
                        code="too-many-thin-modules",
                        detail=(
                            f"{entry.package_name} exposes {entry.thin_module_count} "
                            "thin modules and needs tighter ownership boundaries"
                        ),
                    )
                )
            if entry.wrapper_module_count != 0:
                issues.append(
                    PackageSubstanceIssue(
                        code="wrapper-leak-into-product",
                        detail=(
                            f"{entry.package_name} should not rely on compatibility-wrapper "
                            "module counts to justify its release boundary"
                        ),
                    )
                )
        elif entry.boundary_role is PackageBoundaryRole.SHARED_KERNEL:
            if entry.owned_logic_count < expectation.minimum_owned_logic_count:
                issues.append(
                    PackageSubstanceIssue(
                        code="insufficient-owned-logic",
                        detail=(
                            f"{entry.package_name} exposes only {entry.owned_logic_count} "
                            "owned-logic modules and is too thin to justify its release boundary"
                        ),
                    )
                )
            if entry.thin_module_count > expectation.maximum_thin_module_count:
                issues.append(
                    PackageSubstanceIssue(
                        code="too-many-thin-modules",
                        detail=(
                            f"{entry.package_name} exposes {entry.thin_module_count} "
                            "thin modules and needs tighter ownership boundaries"
                        ),
                    )
                )
        elif entry.boundary_role is PackageBoundaryRole.COMPATIBILITY_BRIDGE:
            if entry.owned_logic_count != 0:
                issues.append(
                    PackageSubstanceIssue(
                        code="bridge-regained-owned-logic",
                        detail=(
                            f"{entry.package_name} reports owned logic even though it must "
                            "remain a wrapper-only compatibility bridge"
                        ),
                    )
                )
            if not entry.ready:
                issues.append(
                    PackageSubstanceIssue(
                        code="bridge-wrapper-loss",
                        detail=(
                            f"{entry.package_name} exposes {entry.wrapper_module_count} "
                            f"wrapper modules across {entry.source_module_count} source modules"
                        ),
                    )
                )
        else:
            if entry.owned_logic_count < expectation.minimum_owned_logic_count:
                issues.append(
                    PackageSubstanceIssue(
                        code="maintainer-support-too-thin",
                        detail=(
                            f"{entry.package_name} has only {entry.owned_logic_count} "
                            "owned-logic modules and no longer justifies a separate maintainer package"
                        ),
                    )
                )
        if not (repo_root / entry.evidence_locator).exists():
            issues.append(
                PackageSubstanceIssue(
                    code="missing-evidence-locator",
                    detail=(
                        f"{entry.package_name} references missing package substance evidence "
                        f"{entry.evidence_locator}"
                    ),
                )
            )

    for issue in validate_agentic_compatibility_inventory(repo_root):
        issues.append(
            PackageSubstanceIssue(
                code="compatibility-bridge-drift",
                detail=issue.detail,
            )
        )

    return tuple(sorted(issues, key=lambda issue: (issue.code, issue.detail)))


def _csv_text(entries: tuple[PackageSubstanceEntry, ...]) -> str:
    lines = [
        "package_name,boundary_role,source_module_count,owned_logic_count,wrapper_module_count,thin_module_count,evidence_locator,ready"
    ]
    for entry in entries:
        lines.append(
            ",".join(
                (
                    entry.package_name,
                    entry.boundary_role.value,
                    str(entry.source_module_count),
                    str(entry.owned_logic_count),
                    str(entry.wrapper_module_count),
                    str(entry.thin_module_count),
                    entry.evidence_locator,
                    "true" if entry.ready else "false",
                )
            )
        )
    return "\n".join(lines) + "\n"


def _summary_text(entries: tuple[PackageSubstanceEntry, ...]) -> str:
    role_counts = Counter(entry.boundary_role.value for entry in entries)
    lines = [
        "---",
        "title: Package Substance",
        "audience: maintainer",
        "type: reference",
        "status: canonical",
        "owner: bijux-proteomics-dev",
        "last_reviewed: 2026-05-05",
        "---",
        "",
        "# package substance",
        "",
        "This report makes package-boundary substance explicit. The five real product "
        "packages must carry enough owned logic to justify their boundaries, the "
        "shared kernel must stay narrow and reusable, the compatibility bridge must "
        "stay wrapper-only, and the maintainer package must remain a real "
        "repository-health surface instead of a token directory.",
        "",
        "## Boundary Roles",
        "",
        f"- canonical products: {role_counts[PackageBoundaryRole.CANONICAL_PRODUCT.value]}",
        f"- shared kernels: {role_counts[PackageBoundaryRole.SHARED_KERNEL.value]}",
        f"- compatibility bridges: {role_counts[PackageBoundaryRole.COMPATIBILITY_BRIDGE.value]}",
        f"- maintainer support packages: {role_counts[PackageBoundaryRole.MAINTAINER_SUPPORT.value]}",
        "",
        "## Current Package Counts",
        "",
    ]
    for entry in entries:
        lines.append(
            "- "
            f"`{entry.package_name}`: role={entry.boundary_role.value}, "
            f"owned_logic={entry.owned_logic_count}, wrappers={entry.wrapper_module_count}, "
            f"thin={entry.thin_module_count}, ready={'yes' if entry.ready else 'no'}"
        )
    lines.extend(
        [
            "",
            "## Release Rule",
            "",
            "- the five real product packages must keep enough owned logic to justify separate release identities",
            "- the shared kernel must stay narrow, reusable, and free of presentation or workflow ownership drift",
            "- the compatibility bridge is allowed to be thin only because it is explicitly a wrapper-only bridge",
            "- package-boundary thinness is release-blocking when it hides unresolved SSOT ownership",
            f"- current package substance issues: {len(validate_package_substance(REPO_ROOT))}",
            "",
            "## First Proof Check",
            "",
            f"- `{PACKAGE_SUBSTANCE_CSV_PATH.relative_to(REPO_ROOT).as_posix()}`",
            f"- `{PACKAGE_SUBSTANCE_SUMMARY_PATH.relative_to(REPO_ROOT).as_posix()}`",
            "- `packages/bijux-proteomics-dev/tests/quality/architecture/test_package_substance.py`",
            "",
        ]
    )
    return "\n".join(lines)


def _is_up_to_date(entries: tuple[PackageSubstanceEntry, ...]) -> bool:
    if not PACKAGE_SUBSTANCE_CSV_PATH.exists():
        return False
    if not PACKAGE_SUBSTANCE_SUMMARY_PATH.exists():
        return False
    return PACKAGE_SUBSTANCE_CSV_PATH.read_text(encoding="utf-8").replace(
        "\r\n", "\n"
    ) == _csv_text(entries).replace(
        "\r\n", "\n"
    ) and PACKAGE_SUBSTANCE_SUMMARY_PATH.read_text(encoding="utf-8") == _summary_text(
        entries
    )


def run(check: bool = False) -> int:
    entries = build_package_substance_inventory(REPO_ROOT)
    issues = validate_package_substance(REPO_ROOT)
    if issues:
        for issue in issues:
            print(f"{issue.code}: {issue.detail}")
        return 1
    if check:
        if _is_up_to_date(entries):
            print(f"package substance report is up to date for {len(entries)} packages")
            return 0
        print("package substance report is stale; regenerate it")
        return 1
    PACKAGE_SUBSTANCE_CSV_PATH.write_text(_csv_text(entries), encoding="utf-8")
    PACKAGE_SUBSTANCE_SUMMARY_PATH.write_text(_summary_text(entries), encoding="utf-8")
    print(f"generated package substance report for {len(entries)} packages")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package-boundary substance report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package substance report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
