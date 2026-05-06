from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.support.workspace_inventory import (
    public_symbol_count_from_init,
    root_api_policy_budget,
    src_root,
    workspace_package_names,
)
from bijux_proteomics_dev.governance.package_shape.package_root_line_counts import (
    PACKAGE_ROOT_LINE_COUNTS_PATH,
    build_package_root_line_count_report,
    validate_package_root_line_count_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_ROOT_BUDGETS_PATH",
    "PackageRootBudgetEntry",
    "PackageRootBudgetReport",
    "build_package_root_budget_report",
    "run",
    "validate_package_root_budgets",
]


PACKAGE_ROOT_BUDGETS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-root-budgets.toml"
)


@dataclass(frozen=True)
class PackageRootBudgetEntry:
    """One package root measured against its durable budget when it has one."""

    distribution_name: str
    init_line_count: int
    public_symbol_count: int
    max_init_lines: int | None
    max_public_symbols: int | None
    within_budget: bool


@dataclass(frozen=True)
class PackageRootBudgetReport:
    """Checked package-root budget report across repository packages."""

    entries: tuple[PackageRootBudgetEntry, ...]
    total_init_line_count: int
    over_budget_packages: tuple[str, ...]


def build_package_root_budget_report() -> PackageRootBudgetReport:
    """Build the checked package-root budget report."""

    entries: list[PackageRootBudgetEntry] = []
    for package_name in workspace_package_names():
        budget = root_api_policy_budget(package_name)
        init_line_count = len(
            (src_root(package_name) / "__init__.py")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        public_symbol_count = public_symbol_count_from_init(package_name)
        max_init_lines = budget["max_init_lines"] if budget is not None else None
        max_public_symbols = (
            budget["max_public_symbols"] if budget is not None else None
        )
        within_budget = budget is None or (
            init_line_count <= max_init_lines
            and public_symbol_count <= max_public_symbols
        )
        entries.append(
            PackageRootBudgetEntry(
                distribution_name=package_name,
                init_line_count=init_line_count,
                public_symbol_count=public_symbol_count,
                max_init_lines=max_init_lines,
                max_public_symbols=max_public_symbols,
                within_budget=within_budget,
            )
        )
    over_budget_packages = tuple(
        entry.distribution_name for entry in entries if not entry.within_budget
    )
    return PackageRootBudgetReport(
        entries=tuple(entries),
        total_init_line_count=sum(entry.init_line_count for entry in entries),
        over_budget_packages=over_budget_packages,
    )


def validate_package_root_budgets(
    report: PackageRootBudgetReport | None = None,
) -> tuple[str, ...]:
    """Fail release when package roots exceed durable budgets without offsetting simplification."""

    report = report or build_package_root_budget_report()
    failures: list[str] = []
    if report.over_budget_packages:
        failures.append(
            "package roots exceeded governed root-api budgets: "
            + ", ".join(report.over_budget_packages)
        )
    for failure in validate_package_root_line_count_report():
        failures.append(f"line-count: {failure}")
    return tuple(failures)


def _toml_text(report: PackageRootBudgetReport) -> str:
    over_budget_packages = ", ".join(
        f'"{value}"' for value in report.over_budget_packages
    )
    lines = [
        "# Generated package-root budget report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_root_budgets",
        "",
        f"total_init_line_count = {report.total_init_line_count}",
        f"over_budget_packages = [{over_budget_packages}]",
        "",
        "[evidence]",
        f'package_root_line_counts_path = "{PACKAGE_ROOT_LINE_COUNTS_PATH.relative_to(REPO_ROOT).as_posix()}"',
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"init_line_count = {entry.init_line_count}",
                f"public_symbol_count = {entry.public_symbol_count}",
                f"budgeted = {str(entry.max_init_lines is not None).lower()}",
            ]
        )
        if entry.max_init_lines is not None:
            lines.append(f"max_init_lines = {entry.max_init_lines}")
        if entry.max_public_symbols is not None:
            lines.append(f"max_public_symbols = {entry.max_public_symbols}")
        lines.extend(
            [
                f"within_budget = {str(entry.within_budget).lower()}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageRootBudgetReport) -> bool:
    if not PACKAGE_ROOT_BUDGETS_PATH.exists():
        return False
    return PACKAGE_ROOT_BUDGETS_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_root_budget_report()
    failures = validate_package_root_budgets(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package root budget report is up to date")
            return 0
        print("package root budget report is stale; regenerate it")
        return 1
    PACKAGE_ROOT_BUDGETS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package root budget report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package-root budget report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package-root budget report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
