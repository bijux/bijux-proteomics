from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.api.support.workspace_inventory import (
    is_wrapper_module,
    source_modules,
    workspace_package_names,
)
from bijux_proteomics_dev.api.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_WRAPPER_DENSITY_PATH",
    "PackageWrapperDensityEntry",
    "PackageWrapperDensityGuard",
    "PackageWrapperDensityReport",
    "build_package_wrapper_density_report",
    "run",
    "validate_package_wrapper_density",
]


PACKAGE_WRAPPER_DENSITY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-wrapper-density.toml"
)


@dataclass(frozen=True)
class PackageWrapperDensityEntry:
    """Wrapper density metrics for one package."""

    distribution_name: str
    total_source_module_count: int
    wrapper_module_count: int
    wrapper_density: float
    max_wrapper_module_count: int


@dataclass(frozen=True)
class PackageWrapperDensityGuard:
    """Release-blocking ceilings over wrapper growth."""

    max_total_wrapper_module_count: int
    max_average_wrapper_density: float


@dataclass(frozen=True)
class PackageWrapperDensityReport:
    """Checked wrapper density report across repository packages."""

    entries: tuple[PackageWrapperDensityEntry, ...]
    guard: PackageWrapperDensityGuard


def build_package_wrapper_density_report() -> PackageWrapperDensityReport:
    """Build the checked wrapper density report."""

    entries = []
    for package_name in workspace_package_names():
        modules = source_modules(package_name)
        wrapper_module_count = sum(1 for path in modules if is_wrapper_module(path))
        total_source_module_count = len(modules)
        wrapper_density = round(
            0.0
            if total_source_module_count == 0
            else wrapper_module_count / total_source_module_count,
            4,
        )
        entries.append(
            PackageWrapperDensityEntry(
                distribution_name=package_name,
                total_source_module_count=total_source_module_count,
                wrapper_module_count=wrapper_module_count,
                wrapper_density=wrapper_density,
                max_wrapper_module_count=wrapper_module_count,
            )
        )
    average_wrapper_density = round(
        sum(entry.wrapper_density for entry in entries) / len(entries), 4
    )
    return PackageWrapperDensityReport(
        entries=tuple(entries),
        guard=PackageWrapperDensityGuard(
            max_total_wrapper_module_count=sum(
                entry.wrapper_module_count for entry in entries
            ),
            max_average_wrapper_density=average_wrapper_density,
        ),
    )


def validate_package_wrapper_density(
    report: PackageWrapperDensityReport | None = None,
) -> tuple[str, ...]:
    """Fail release when wrapper density grows beyond the governed baseline."""

    report = report or build_package_wrapper_density_report()
    failures: list[str] = []
    total_wrapper_module_count = sum(entry.wrapper_module_count for entry in report.entries)
    average_wrapper_density = round(
        sum(entry.wrapper_density for entry in report.entries) / len(report.entries), 4
    )
    if total_wrapper_module_count > report.guard.max_total_wrapper_module_count:
        failures.append("package wrapper-module count grew beyond the governed baseline")
    if average_wrapper_density > report.guard.max_average_wrapper_density:
        failures.append("package average wrapper density grew beyond the governed baseline")
    for entry in report.entries:
        if entry.wrapper_module_count > entry.max_wrapper_module_count:
            failures.append(
                f"{entry.distribution_name} wrapper-module count grew beyond its governed package ceiling"
            )
    return tuple(failures)


def _toml_text(report: PackageWrapperDensityReport) -> str:
    lines = [
        "# Generated package wrapper density report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.package_shape.package_wrapper_density",
        "",
        "[guard]",
        f"max_total_wrapper_module_count = {report.guard.max_total_wrapper_module_count}",
        f"max_average_wrapper_density = {report.guard.max_average_wrapper_density}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"total_source_module_count = {entry.total_source_module_count}",
                f"wrapper_module_count = {entry.wrapper_module_count}",
                f"wrapper_density = {entry.wrapper_density}",
                f"max_wrapper_module_count = {entry.max_wrapper_module_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageWrapperDensityReport) -> bool:
    if not PACKAGE_WRAPPER_DENSITY_PATH.exists():
        return False
    return PACKAGE_WRAPPER_DENSITY_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_wrapper_density_report()
    failures = validate_package_wrapper_density(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package wrapper density report is up to date")
            return 0
        print("package wrapper density report is stale; regenerate it")
        return 1
    PACKAGE_WRAPPER_DENSITY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package wrapper density report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package wrapper density report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package wrapper density report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
