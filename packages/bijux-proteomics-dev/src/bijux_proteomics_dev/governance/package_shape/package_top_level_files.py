from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.support.workspace_inventory import (
    root_python_modules,
    workspace_package_names,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_TOP_LEVEL_FILES_PATH",
    "PackageTopLevelFileEntry",
    "PackageTopLevelFileGuard",
    "PackageTopLevelFileReport",
    "build_package_top_level_file_report",
    "run",
    "validate_package_top_level_files",
]


PACKAGE_TOP_LEVEL_FILES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-top-level-files.toml"
)


@dataclass(frozen=True)
class PackageTopLevelFileEntry:
    """One package's current top-level python files under its import root."""

    distribution_name: str
    top_level_files: tuple[str, ...]


@dataclass(frozen=True)
class PackageTopLevelFileGuard:
    """Release-blocking ceilings over top-level file growth."""

    max_total_top_level_file_count: int


@dataclass(frozen=True)
class PackageTopLevelFileReport:
    """Checked top-level file report across repository packages."""

    entries: tuple[PackageTopLevelFileEntry, ...]
    guard: PackageTopLevelFileGuard


def build_package_top_level_file_report() -> PackageTopLevelFileReport:
    """Build the checked top-level file report."""

    entries = tuple(
        PackageTopLevelFileEntry(
            distribution_name=package_name,
            top_level_files=tuple(
                sorted(path.name for path in root_python_modules(package_name))
            ),
        )
        for package_name in workspace_package_names()
    )
    return PackageTopLevelFileReport(
        entries=entries,
        guard=PackageTopLevelFileGuard(
            max_total_top_level_file_count=sum(
                len(entry.top_level_files) for entry in entries
            )
        ),
    )


def validate_package_top_level_files(
    report: PackageTopLevelFileReport | None = None,
) -> tuple[str, ...]:
    """Fail release when top-level file growth outruns current package rationale."""

    report = report or build_package_top_level_file_report()
    total_top_level_file_count = sum(
        len(entry.top_level_files) for entry in report.entries
    )
    if total_top_level_file_count <= report.guard.max_total_top_level_file_count:
        return ()
    return (
        "package top-level file count grew beyond the governed domain-subpackage rationale baseline",
    )


def _toml_text(report: PackageTopLevelFileReport) -> str:
    lines = [
        "# Generated package top-level file report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_top_level_files",
        "",
        "[guard]",
        f"max_total_top_level_file_count = {report.guard.max_total_top_level_file_count}",
        "",
    ]
    for entry in report.entries:
        top_level_files = ", ".join(f'"{value}"' for value in entry.top_level_files)
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"top_level_files = [{top_level_files}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageTopLevelFileReport) -> bool:
    if not PACKAGE_TOP_LEVEL_FILES_PATH.exists():
        return False
    return PACKAGE_TOP_LEVEL_FILES_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_top_level_file_report()
    failures = validate_package_top_level_files(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package top-level file report is up to date")
            return 0
        print("package top-level file report is stale; regenerate it")
        return 1
    PACKAGE_TOP_LEVEL_FILES_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package top-level file report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package top-level file report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package top-level file report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
