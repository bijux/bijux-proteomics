from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    nonempty_line_count,
    public_definition_counts,
    source_modules,
    workspace_package_names,
)

__all__ = [
    "PACKAGE_THIN_MODULES_PATH",
    "PackageThinModuleEntry",
    "PackageThinModuleGuard",
    "PackageThinModuleReport",
    "build_package_thin_module_report",
    "run",
    "validate_package_thin_modules",
]


PACKAGE_THIN_MODULES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-thin-modules.toml"
)
THIN_NONEMPTY_LINE_LIMIT = 40


@dataclass(frozen=True)
class PackageThinModuleEntry:
    """One thin module that likely wants merging or deletion follow-up."""

    distribution_name: str
    module_path: str
    nonempty_line_count: int
    public_function_count: int
    public_class_count: int


@dataclass(frozen=True)
class PackageThinModuleGuard:
    """Release-blocking ceiling over thin-module growth."""

    max_total_thin_module_count: int


@dataclass(frozen=True)
class PackageThinModuleReport:
    """Checked thin-module report across repository packages."""

    entries: tuple[PackageThinModuleEntry, ...]
    guard: PackageThinModuleGuard


def build_package_thin_module_report() -> PackageThinModuleReport:
    """Build the checked thin-module report."""

    entries: list[PackageThinModuleEntry] = []
    for package_name in workspace_package_names():
        for path in source_modules(package_name):
            if path.name == "__init__.py":
                continue
            line_count = nonempty_line_count(path)
            public_function_count, public_class_count = public_definition_counts(path)
            if line_count > THIN_NONEMPTY_LINE_LIMIT:
                continue
            if public_function_count + public_class_count > 1:
                continue
            entries.append(
                PackageThinModuleEntry(
                    distribution_name=package_name,
                    module_path=path.relative_to(REPO_ROOT).as_posix(),
                    nonempty_line_count=line_count,
                    public_function_count=public_function_count,
                    public_class_count=public_class_count,
                )
            )
    return PackageThinModuleReport(
        entries=tuple(entries),
        guard=PackageThinModuleGuard(max_total_thin_module_count=len(entries)),
    )


def validate_package_thin_modules(
    report: PackageThinModuleReport | None = None,
) -> tuple[str, ...]:
    """Fail release when thin-module count grows beyond the governed baseline."""

    report = report or build_package_thin_module_report()
    if len(report.entries) <= report.guard.max_total_thin_module_count:
        return ()
    return ("package thin-module count grew beyond the governed baseline",)


def _toml_text(report: PackageThinModuleReport) -> str:
    lines = [
        "# Generated package thin-module report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_thin_modules",
        "",
        "[guard]",
        f"max_total_thin_module_count = {report.guard.max_total_thin_module_count}",
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
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageThinModuleReport) -> bool:
    if not PACKAGE_THIN_MODULES_PATH.exists():
        return False
    return PACKAGE_THIN_MODULES_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_thin_module_report()
    failures = validate_package_thin_modules(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package thin-module report is up to date")
            return 0
        print("package thin-module report is stale; regenerate it")
        return 1
    PACKAGE_THIN_MODULES_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package thin-module report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package thin-module report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package thin-module report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
