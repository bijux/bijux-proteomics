from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "LAB_CROSS_PACKAGE_DEPENDENCIES_PATH",
    "LabCrossPackageDependencyEntry",
    "LabCrossPackageDependencyGuard",
    "LabCrossPackageDependencyReport",
    "build_lab_cross_package_dependency_report",
    "run",
    "validate_lab_cross_package_dependencies",
]


@dataclass(frozen=True)
class LabCrossPackageDependencyEntry:
    """One direct import edge from lab into another workspace package."""

    importer_module_path: str
    owner_distribution: str
    imported_module_name: str
    imported_symbols: tuple[str, ...]


@dataclass(frozen=True)
class LabCrossPackageDependencyGuard:
    """Release-blocking ceilings over current lab cross-package dependencies."""

    max_core_edges: int
    max_foundation_edges: int
    max_intelligence_edges: int
    max_knowledge_edges: int
    max_runtime_edges: int
    max_total_edges: int


@dataclass(frozen=True)
class LabCrossPackageDependencyReport:
    """One checked report over lab imports of workspace owner packages."""

    entries: tuple[LabCrossPackageDependencyEntry, ...]
    guard: LabCrossPackageDependencyGuard


LAB_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src" / "bijux_proteomics_lab"
)
LAB_CROSS_PACKAGE_DEPENDENCIES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "lab-cross-package-dependencies.toml"
)
OWNER_BY_PREFIX = {
    "bijux_proteomics": "bijux-proteomics-core",
    "bijux_proteomics_foundation": "bijux-proteomics-foundation",
    "bijux_proteomics_intelligence": "bijux-proteomics-intelligence",
    "bijux_proteomics_knowledge": "bijux-proteomics-knowledge",
    "bijux_proteomics_runtime": "bijux-proteomics-runtime",
}


def _entry_key(
    entry: LabCrossPackageDependencyEntry,
) -> tuple[str, str, str, tuple[str, ...]]:
    return (
        entry.importer_module_path,
        entry.owner_distribution,
        entry.imported_module_name,
        entry.imported_symbols,
    )


def build_lab_cross_package_dependency_report() -> LabCrossPackageDependencyReport:
    """Build the checked report over live lab cross-package import edges."""

    entries: list[LabCrossPackageDependencyEntry] = []
    for path in sorted(LAB_SRC_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        importer_module_path = path.relative_to(LAB_SRC_ROOT).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix, distribution in OWNER_BY_PREFIX.items():
                        if alias.name == prefix or alias.name.startswith(f"{prefix}."):
                            entries.append(
                                LabCrossPackageDependencyEntry(
                                    importer_module_path=importer_module_path,
                                    owner_distribution=distribution,
                                    imported_module_name=alias.name,
                                    imported_symbols=(),
                                )
                            )
            if not isinstance(node, ast.ImportFrom) or node.module is None:
                continue
            for prefix, distribution in OWNER_BY_PREFIX.items():
                if node.module != prefix and not node.module.startswith(f"{prefix}."):
                    continue
                entries.append(
                    LabCrossPackageDependencyEntry(
                        importer_module_path=importer_module_path,
                        owner_distribution=distribution,
                        imported_module_name=node.module,
                        imported_symbols=tuple(
                            sorted(alias.name for alias in node.names)
                        ),
                    )
                )

    entries = tuple(sorted(entries, key=_entry_key))

    def _count(distribution: str) -> int:
        return sum(1 for entry in entries if entry.owner_distribution == distribution)

    return LabCrossPackageDependencyReport(
        entries=entries,
        guard=LabCrossPackageDependencyGuard(
            max_core_edges=_count("bijux-proteomics-core"),
            max_foundation_edges=_count("bijux-proteomics-foundation"),
            max_intelligence_edges=_count("bijux-proteomics-intelligence"),
            max_knowledge_edges=_count("bijux-proteomics-knowledge"),
            max_runtime_edges=_count("bijux-proteomics-runtime"),
            max_total_edges=len(entries),
        ),
    )


def validate_lab_cross_package_dependencies() -> tuple[str, ...]:
    """Fail when lab cross-package dependency edges grow beyond the guarded baseline."""

    report = build_lab_cross_package_dependency_report()

    def _count(distribution: str) -> int:
        return sum(
            1 for entry in report.entries if entry.owner_distribution == distribution
        )

    failures: list[str] = []
    if _count("bijux-proteomics-core") > report.guard.max_core_edges:
        failures.append("lab core dependency edges grew beyond the guarded baseline")
    if _count("bijux-proteomics-foundation") > report.guard.max_foundation_edges:
        failures.append(
            "lab foundation dependency edges grew beyond the guarded baseline"
        )
    if _count("bijux-proteomics-intelligence") > report.guard.max_intelligence_edges:
        failures.append(
            "lab intelligence dependency edges grew beyond the guarded baseline"
        )
    if _count("bijux-proteomics-knowledge") > report.guard.max_knowledge_edges:
        failures.append(
            "lab knowledge dependency edges grew beyond the guarded baseline"
        )
    if _count("bijux-proteomics-runtime") > report.guard.max_runtime_edges:
        failures.append("lab runtime dependency edges grew beyond the guarded baseline")
    if len(report.entries) > report.guard.max_total_edges:
        failures.append(
            "lab cross-package dependency count grew beyond the guarded baseline"
        )
    return tuple(failures)


def _toml_text(report: LabCrossPackageDependencyReport) -> str:
    lines = [
        "# Generated lab cross-package dependency report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.lab.cross_package_dependencies",
        "",
        "[guard]",
        f"max_core_edges = {report.guard.max_core_edges}",
        f"max_foundation_edges = {report.guard.max_foundation_edges}",
        f"max_intelligence_edges = {report.guard.max_intelligence_edges}",
        f"max_knowledge_edges = {report.guard.max_knowledge_edges}",
        f"max_runtime_edges = {report.guard.max_runtime_edges}",
        f"max_total_edges = {report.guard.max_total_edges}",
        "",
    ]
    for entry in report.entries:
        imported_symbols = ", ".join(f'"{value}"' for value in entry.imported_symbols)
        lines.extend(
            [
                "[[dependency]]",
                f'importer_module_path = "{entry.importer_module_path}"',
                f'owner_distribution = "{entry.owner_distribution}"',
                f'imported_module_name = "{entry.imported_module_name}"',
                f"imported_symbols = [{imported_symbols}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: LabCrossPackageDependencyReport) -> bool:
    if not LAB_CROSS_PACKAGE_DEPENDENCIES_PATH.exists():
        return False
    return LAB_CROSS_PACKAGE_DEPENDENCIES_PATH.read_text(
        encoding="utf-8"
    ) == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_lab_cross_package_dependency_report()
    failures = validate_lab_cross_package_dependencies()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("lab cross-package dependency report is up to date")
            return 0
        print("lab cross-package dependency report is stale; regenerate it")
        return 1
    LAB_CROSS_PACKAGE_DEPENDENCIES_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated lab cross-package dependency report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the lab cross-package dependency report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the lab cross-package dependency report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
