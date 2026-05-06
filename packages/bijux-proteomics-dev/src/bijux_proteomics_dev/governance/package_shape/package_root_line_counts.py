from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    public_symbol_count_from_init,
    root_python_modules,
    src_root,
    workspace_package_names,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_ROOT_LINE_COUNTS_PATH",
    "PackageRootLineCountEntry",
    "PackageRootLineCountGuard",
    "PackageRootLineCountReport",
    "build_package_root_line_count_report",
    "run",
    "validate_package_root_line_count_report",
]


PACKAGE_ROOT_LINE_COUNTS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-root-line-counts.toml"
)


@dataclass(frozen=True)
class PackageRootLineCountEntry:
    """One current package-root line-count snapshot."""

    distribution_name: str
    import_root: str
    init_line_count: int
    top_level_python_module_count: int
    public_symbol_count: int


@dataclass(frozen=True)
class PackageRootLineCountGuard:
    """Baseline ceilings for package-root line-count drift."""

    max_total_init_line_count: int
    max_total_top_level_python_module_count: int


@dataclass(frozen=True)
class PackageRootLineCountReport:
    """Checked root line-count report across repository packages."""

    entries: tuple[PackageRootLineCountEntry, ...]
    guard: PackageRootLineCountGuard


def build_package_root_line_count_report() -> PackageRootLineCountReport:
    """Build the checked package-root line-count report."""

    entries = tuple(
        PackageRootLineCountEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            init_line_count=len(
                (src_root(package_name) / "__init__.py").read_text(
                    encoding="utf-8"
                ).splitlines()
            ),
            top_level_python_module_count=len(root_python_modules(package_name)),
            public_symbol_count=public_symbol_count_from_init(package_name),
        )
        for package_name in workspace_package_names()
    )
    return PackageRootLineCountReport(
        entries=entries,
        guard=PackageRootLineCountGuard(
            max_total_init_line_count=sum(entry.init_line_count for entry in entries),
            max_total_top_level_python_module_count=sum(
                entry.top_level_python_module_count for entry in entries
            ),
        ),
    )


def validate_package_root_line_count_report(
    report: PackageRootLineCountReport | None = None,
) -> tuple[str, ...]:
    """Fail release when root line-count drift exceeds the governed baseline."""

    report = report or build_package_root_line_count_report()
    failures: list[str] = []
    total_init_line_count = sum(entry.init_line_count for entry in report.entries)
    total_top_level_python_module_count = sum(
        entry.top_level_python_module_count for entry in report.entries
    )
    if total_init_line_count > report.guard.max_total_init_line_count:
        failures.append(
            "package root total init line count grew beyond the governed baseline"
        )
    if (
        total_top_level_python_module_count
        > report.guard.max_total_top_level_python_module_count
    ):
        failures.append(
            "package root total top-level python module count grew beyond the governed baseline"
        )
    return tuple(failures)


def _toml_text(report: PackageRootLineCountReport) -> str:
    lines = [
        "# Generated package-root line-count report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_root_line_counts",
        "",
        "[guard]",
        f"max_total_init_line_count = {report.guard.max_total_init_line_count}",
        (
            "max_total_top_level_python_module_count = "
            f"{report.guard.max_total_top_level_python_module_count}"
        ),
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'import_root = "{entry.import_root}"',
                f"init_line_count = {entry.init_line_count}",
                (
                    "top_level_python_module_count = "
                    f"{entry.top_level_python_module_count}"
                ),
                f"public_symbol_count = {entry.public_symbol_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageRootLineCountReport) -> bool:
    if not PACKAGE_ROOT_LINE_COUNTS_PATH.exists():
        return False
    return PACKAGE_ROOT_LINE_COUNTS_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_root_line_count_report()
    failures = validate_package_root_line_count_report(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package root line-count report is up to date")
            return 0
        print("package root line-count report is stale; regenerate it")
        return 1
    PACKAGE_ROOT_LINE_COUNTS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package root line-count report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package-root line-count report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package-root line-count report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
