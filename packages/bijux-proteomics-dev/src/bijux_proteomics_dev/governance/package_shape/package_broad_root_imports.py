from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root_import_occurrences,
    workspace_package_names,
)

__all__ = [
    "PACKAGE_BROAD_ROOT_IMPORTS_PATH",
    "PackageBroadRootImportEntry",
    "PackageBroadRootImportGuard",
    "PackageBroadRootImportReport",
    "build_package_broad_root_import_report",
    "run",
    "validate_package_broad_root_imports",
]


PACKAGE_BROAD_ROOT_IMPORTS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-broad-root-imports.toml"
)


@dataclass(frozen=True)
class PackageBroadRootImportEntry:
    """One broad package-root import that bypasses an owner path."""

    distribution_name: str
    package_broad_root_import_count: int
    max_package_broad_root_import_count: int
    importer_module_path: str
    import_kind: str
    line_number: int


@dataclass(frozen=True)
class PackageBroadRootImportGuard:
    """Release-blocking ceiling over broad package-root imports."""

    max_total_broad_root_import_count: int


@dataclass(frozen=True)
class PackageBroadRootImportReport:
    """Checked broad package-root import report across repository packages."""

    entries: tuple[PackageBroadRootImportEntry, ...]
    guard: PackageBroadRootImportGuard


def build_package_broad_root_import_report() -> PackageBroadRootImportReport:
    """Build the checked broad package-root import report."""

    entries: list[PackageBroadRootImportEntry] = []
    for package_name in workspace_package_names():
        occurrences = package_root_import_occurrences(package_name)
        package_broad_root_import_count = len(occurrences)
        for module_path, import_kind, line_number in occurrences:
            entries.append(
                PackageBroadRootImportEntry(
                    distribution_name=package_name,
                    package_broad_root_import_count=package_broad_root_import_count,
                    max_package_broad_root_import_count=package_broad_root_import_count,
                    importer_module_path=module_path,
                    import_kind=import_kind,
                    line_number=line_number,
                )
            )
    return PackageBroadRootImportReport(
        entries=tuple(entries),
        guard=PackageBroadRootImportGuard(
            max_total_broad_root_import_count=len(entries)
        ),
    )


def validate_package_broad_root_imports(
    report: PackageBroadRootImportReport | None = None,
) -> tuple[str, ...]:
    """Fail release when broad package-root imports return."""

    report = report or build_package_broad_root_import_report()
    failures: list[str] = []
    if len(report.entries) > report.guard.max_total_broad_root_import_count:
        failures.append(
            "broad package-root imports grew beyond the governed owner-path rewrite baseline"
        )
    package_counts: dict[str, int] = {}
    package_limits: dict[str, int] = {}
    for entry in report.entries:
        package_counts[entry.distribution_name] = entry.package_broad_root_import_count
        package_limits[entry.distribution_name] = (
            entry.max_package_broad_root_import_count
        )
    for package_name, count in sorted(package_counts.items()):
        if count > package_limits[package_name]:
            failures.append(
                f"{package_name} broad package-root imports grew beyond the governed package ceiling"
            )
    return tuple(failures)


def _toml_text(report: PackageBroadRootImportReport) -> str:
    lines = [
        "# Generated package broad-root import report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_broad_root_imports",
        "",
        "[guard]",
        f"max_total_broad_root_import_count = {report.guard.max_total_broad_root_import_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[import]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"package_broad_root_import_count = {entry.package_broad_root_import_count}",
                (
                    "max_package_broad_root_import_count = "
                    f"{entry.max_package_broad_root_import_count}"
                ),
                f'importer_module_path = "{entry.importer_module_path}"',
                f'import_kind = "{entry.import_kind}"',
                f"line_number = {entry.line_number}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageBroadRootImportReport) -> bool:
    if not PACKAGE_BROAD_ROOT_IMPORTS_PATH.exists():
        return False
    return PACKAGE_BROAD_ROOT_IMPORTS_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_broad_root_import_report()
    failures = validate_package_broad_root_imports(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package broad-root import report is up to date")
            return 0
        print("package broad-root import report is stale; regenerate it")
        return 1
    PACKAGE_BROAD_ROOT_IMPORTS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package broad-root import report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package broad-root import report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package broad-root import report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
