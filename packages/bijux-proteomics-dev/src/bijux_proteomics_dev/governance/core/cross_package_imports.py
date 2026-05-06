from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.foundation.root_consumers import REPO_ROOT

__all__ = [
    "CORE_CROSS_PACKAGE_IMPORTS_PATH",
    "CoreCrossPackageImportEntry",
    "CoreCrossPackageImportGuard",
    "CoreCrossPackageImportReport",
    "build_core_cross_package_import_report",
    "run",
    "validate_core_cross_package_imports",
]


@dataclass(frozen=True)
class CoreCrossPackageImportEntry:
    """One direct import edge from core into another package owner."""

    importer_module_path: str
    owner_distribution: str
    imported_module_name: str
    imported_symbols: tuple[str, ...]


@dataclass(frozen=True)
class CoreCrossPackageImportGuard:
    """Release-blocking ceiling over current cross-package dependency edges."""

    max_runtime_edges: int
    max_intelligence_edges: int
    max_lab_edges: int
    max_total_edges: int


@dataclass(frozen=True)
class CoreCrossPackageImportReport:
    """One checked report over core imports of runtime, intelligence, and lab."""

    entries: tuple[CoreCrossPackageImportEntry, ...]
    guard: CoreCrossPackageImportGuard


CORE_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-core" / "src" / "bijux_proteomics"
)
CORE_CROSS_PACKAGE_IMPORTS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "core-cross-package-imports.toml"
)
OWNER_BY_PREFIX = {
    "bijux_proteomics_runtime": "bijux-proteomics-runtime",
    "bijux_proteomics_intelligence": "bijux-proteomics-intelligence",
    "bijux_proteomics_lab": "bijux-proteomics-lab",
}


def _entry_key(entry: CoreCrossPackageImportEntry) -> tuple[str, str, str]:
    return (
        entry.importer_module_path,
        entry.owner_distribution,
        entry.imported_module_name,
    )


def build_core_cross_package_import_report() -> CoreCrossPackageImportReport:
    """Build the checked report over live core cross-package imports."""

    entries: list[CoreCrossPackageImportEntry] = []
    for path in sorted(CORE_SRC_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        importer_module_path = path.relative_to(CORE_SRC_ROOT).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix, distribution in OWNER_BY_PREFIX.items():
                        if alias.name == prefix or alias.name.startswith(f"{prefix}."):
                            entries.append(
                                CoreCrossPackageImportEntry(
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
                    CoreCrossPackageImportEntry(
                        importer_module_path=importer_module_path,
                        owner_distribution=distribution,
                        imported_module_name=node.module,
                        imported_symbols=tuple(
                            sorted(alias.name for alias in node.names)
                        ),
                    )
                )

    entries = sorted(entries, key=_entry_key)
    runtime_edges = sum(
        1 for entry in entries if entry.owner_distribution == "bijux-proteomics-runtime"
    )
    intelligence_edges = sum(
        1
        for entry in entries
        if entry.owner_distribution == "bijux-proteomics-intelligence"
    )
    lab_edges = sum(
        1 for entry in entries if entry.owner_distribution == "bijux-proteomics-lab"
    )
    return CoreCrossPackageImportReport(
        entries=tuple(entries),
        guard=CoreCrossPackageImportGuard(
            max_runtime_edges=runtime_edges,
            max_intelligence_edges=intelligence_edges,
            max_lab_edges=lab_edges,
            max_total_edges=len(entries),
        ),
    )


def validate_core_cross_package_imports() -> tuple[str, ...]:
    """Fail when cross-package import edges grow beyond the guarded baseline."""

    report = build_core_cross_package_import_report()
    runtime_edges = sum(
        1
        for entry in report.entries
        if entry.owner_distribution == "bijux-proteomics-runtime"
    )
    intelligence_edges = sum(
        1
        for entry in report.entries
        if entry.owner_distribution == "bijux-proteomics-intelligence"
    )
    lab_edges = sum(
        1
        for entry in report.entries
        if entry.owner_distribution == "bijux-proteomics-lab"
    )
    failures: list[str] = []
    if runtime_edges > report.guard.max_runtime_edges:
        failures.append("core runtime import edges grew beyond the guarded baseline")
    if intelligence_edges > report.guard.max_intelligence_edges:
        failures.append(
            "core intelligence import edges grew beyond the guarded baseline"
        )
    if lab_edges > report.guard.max_lab_edges:
        failures.append("core lab import edges grew beyond the guarded baseline")
    if len(report.entries) > report.guard.max_total_edges:
        failures.append(
            "core cross-package import count grew beyond the guarded baseline"
        )
    return tuple(failures)


def _toml_text(report: CoreCrossPackageImportReport) -> str:
    lines = [
        "# Generated core cross-package import report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.core.cross_package_imports",
        "",
        "[guard]",
        f"max_runtime_edges = {report.guard.max_runtime_edges}",
        f"max_intelligence_edges = {report.guard.max_intelligence_edges}",
        f"max_lab_edges = {report.guard.max_lab_edges}",
        f"max_total_edges = {report.guard.max_total_edges}",
        "",
    ]
    for entry in report.entries:
        imported_symbols = ", ".join(f'"{value}"' for value in entry.imported_symbols)
        lines.extend(
            [
                "[[import]]",
                f'importer_module_path = "{entry.importer_module_path}"',
                f'owner_distribution = "{entry.owner_distribution}"',
                f'imported_module_name = "{entry.imported_module_name}"',
                f"imported_symbols = [{imported_symbols}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: CoreCrossPackageImportReport) -> bool:
    if not CORE_CROSS_PACKAGE_IMPORTS_PATH.exists():
        return False
    return CORE_CROSS_PACKAGE_IMPORTS_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_core_cross_package_import_report()
    failures = validate_core_cross_package_imports()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print(
                f"core cross-package import report is up to date for {len(report.entries)} edges"
            )
            return 0
        print("core cross-package import report is stale; regenerate it")
        return 1
    CORE_CROSS_PACKAGE_IMPORTS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print(f"generated core cross-package import report for {len(report.entries)} edges")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the core cross-package import report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the cross-package import report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
