from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    nonempty_line_count,
    public_definition_counts,
    source_modules,
    workspace_import_roots_used,
    workspace_package_names,
)

__all__ = [
    "OVERSIZED_NONEMPTY_LINE_LIMIT",
    "MIXED_IMPORT_ROOT_LIMIT",
    "MIXED_PUBLIC_DEFINITION_LIMIT",
    "PACKAGE_OVERSIZED_MIXED_MODULES_PATH",
    "PackageOversizedMixedModuleEntry",
    "PackageOversizedMixedModuleGuard",
    "PackageOversizedMixedModuleReport",
    "build_package_oversized_mixed_module_report",
    "run",
    "validate_package_oversized_mixed_modules",
]


OVERSIZED_NONEMPTY_LINE_LIMIT = 600
MIXED_IMPORT_ROOT_LIMIT = 3
MIXED_PUBLIC_DEFINITION_LIMIT = 20
PACKAGE_OVERSIZED_MIXED_MODULES_PATH = (
    REPO_ROOT
    / "configs"
    / "package-governance"
    / "package-oversized-mixed-modules.toml"
)


@dataclass(frozen=True)
class PackageOversizedMixedModuleEntry:
    """One oversized module that still mixes too much responsibility."""

    distribution_name: str
    module_path: str
    nonempty_line_count: int
    public_function_count: int
    public_class_count: int
    workspace_import_root_count: int


@dataclass(frozen=True)
class PackageOversizedMixedModuleGuard:
    """Release-blocking ceilings over oversized mixed-module growth."""

    max_total_oversized_mixed_module_count: int
    max_largest_nonempty_line_count: int


@dataclass(frozen=True)
class PackageOversizedMixedModuleReport:
    """Checked oversized mixed-module report across repository packages."""

    entries: tuple[PackageOversizedMixedModuleEntry, ...]
    guard: PackageOversizedMixedModuleGuard


def build_package_oversized_mixed_module_report() -> PackageOversizedMixedModuleReport:
    """Build the checked oversized mixed-module report."""

    entries: list[PackageOversizedMixedModuleEntry] = []
    for package_name in workspace_package_names():
        for path in source_modules(package_name):
            line_count = nonempty_line_count(path)
            if line_count <= OVERSIZED_NONEMPTY_LINE_LIMIT:
                continue
            public_function_count, public_class_count = public_definition_counts(path)
            workspace_import_root_count = len(workspace_import_roots_used(path))
            public_definition_count = public_function_count + public_class_count
            if (
                public_definition_count <= MIXED_PUBLIC_DEFINITION_LIMIT
                and workspace_import_root_count < MIXED_IMPORT_ROOT_LIMIT
            ):
                continue
            entries.append(
                PackageOversizedMixedModuleEntry(
                    distribution_name=package_name,
                    module_path=path.relative_to(REPO_ROOT).as_posix(),
                    nonempty_line_count=line_count,
                    public_function_count=public_function_count,
                    public_class_count=public_class_count,
                    workspace_import_root_count=workspace_import_root_count,
                )
            )
    entries.sort(
        key=lambda entry: (
            -entry.nonempty_line_count,
            entry.distribution_name,
            entry.module_path,
        )
    )
    largest_nonempty_line_count = max(
        (entry.nonempty_line_count for entry in entries),
        default=0,
    )
    return PackageOversizedMixedModuleReport(
        entries=tuple(entries),
        guard=PackageOversizedMixedModuleGuard(
            max_total_oversized_mixed_module_count=len(entries),
            max_largest_nonempty_line_count=largest_nonempty_line_count,
        ),
    )


def validate_package_oversized_mixed_modules(
    report: PackageOversizedMixedModuleReport | None = None,
) -> tuple[str, ...]:
    """Fail release when oversized mixed-module pressure grows."""

    report = report or build_package_oversized_mixed_module_report()
    failures: list[str] = []
    if len(report.entries) > report.guard.max_total_oversized_mixed_module_count:
        failures.append(
            "oversized mixed-module count grew beyond the governed split-follow-up baseline"
        )
    largest_nonempty_line_count = max(
        (entry.nonempty_line_count for entry in report.entries),
        default=0,
    )
    if largest_nonempty_line_count > report.guard.max_largest_nonempty_line_count:
        failures.append(
            "largest oversized mixed module grew beyond the governed split-follow-up baseline"
        )
    return tuple(failures)


def _toml_text(report: PackageOversizedMixedModuleReport) -> str:
    lines = [
        "# Generated package oversized mixed-module report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_oversized_mixed_modules",
        "",
        "[guard]",
        (
            "max_total_oversized_mixed_module_count = "
            f"{report.guard.max_total_oversized_mixed_module_count}"
        ),
        f"max_largest_nonempty_line_count = {report.guard.max_largest_nonempty_line_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[module]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'module_path = "{entry.module_path}"',
                f"nonempty_line_count = {entry.nonempty_line_count}",
                f"public_function_count = {entry.public_function_count}",
                f"public_class_count = {entry.public_class_count}",
                f"workspace_import_root_count = {entry.workspace_import_root_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageOversizedMixedModuleReport) -> bool:
    if not PACKAGE_OVERSIZED_MIXED_MODULES_PATH.exists():
        return False
    return PACKAGE_OVERSIZED_MIXED_MODULES_PATH.read_text(
        encoding="utf-8"
    ) == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_oversized_mixed_module_report()
    failures = validate_package_oversized_mixed_modules(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package oversized mixed-module report is up to date")
            return 0
        print("package oversized mixed-module report is stale; regenerate it")
        return 1
    PACKAGE_OVERSIZED_MIXED_MODULES_PATH.write_text(
        _toml_text(report),
        encoding="utf-8",
    )
    print("generated package oversized mixed-module report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package oversized mixed-module report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package oversized mixed-module report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
