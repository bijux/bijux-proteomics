from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib

from bijux_proteomics_dev.governance.package_shape.public_api_snapshots import (
    CANONICAL_PUBLIC_API_PACKAGES,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    root_python_modules,
    workspace_import_path,
)

__all__ = [
    "TOP_LEVEL_MODULE_VISIBILITY_PATH",
    "PackageTopLevelModuleVisibilityEntry",
    "PackageTopLevelModuleVisibilityReport",
    "build_top_level_module_visibility_report",
    "run",
    "validate_top_level_module_visibility",
]


TOP_LEVEL_MODULE_VISIBILITY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "top-level-module-visibility.toml"
)


@dataclass(frozen=True)
class PackageTopLevelModuleVisibilityEntry:
    """One canonical package root and the visibility of its leaf modules."""

    distribution_name: str
    public_module_files: tuple[str, ...]
    private_module_files: tuple[str, ...]


@dataclass(frozen=True)
class PackageTopLevelModuleVisibilityReport:
    """Checked visibility report for canonical package-root leaf modules."""

    entries: tuple[PackageTopLevelModuleVisibilityEntry, ...]


def _public_api_module_name(package_name: str) -> str:
    return f"{import_root(package_name)}.public_api"


def _declared_public_module_names(package_name: str) -> tuple[str, ...]:
    with workspace_import_path():
        package_module = importlib.import_module(import_root(package_name))
        public_api_module = importlib.import_module(_public_api_module_name(package_name))
    declared_names = set(getattr(package_module, "__all__", ()))
    declared_names.update(
        str(name)
        for name in getattr(public_api_module, "PUBLIC_ROOT_MODULE_NAMES", ())
    )
    return tuple(sorted(declared_names))


def build_top_level_module_visibility_report() -> PackageTopLevelModuleVisibilityReport:
    """Build the checked canonical root-module visibility report."""

    entries: list[PackageTopLevelModuleVisibilityEntry] = []
    for package_name in CANONICAL_PUBLIC_API_PACKAGES:
        declared_public_names = set(_declared_public_module_names(package_name))
        public_module_files: list[str] = []
        private_module_files: list[str] = []
        for path in root_python_modules(package_name):
            if path.name in {"__init__.py", "public_api.py"}:
                continue
            target_list = (
                public_module_files
                if path.stem in declared_public_names
                else private_module_files
            )
            target_list.append(path.name)
        entries.append(
            PackageTopLevelModuleVisibilityEntry(
                distribution_name=package_name,
                public_module_files=tuple(sorted(public_module_files)),
                private_module_files=tuple(sorted(private_module_files)),
            )
        )
    return PackageTopLevelModuleVisibilityReport(entries=tuple(entries))


def validate_top_level_module_visibility(
    report: PackageTopLevelModuleVisibilityReport | None = None,
) -> tuple[str, ...]:
    """Fail release when canonical package leaf modules leak private ownership."""

    report = report or build_top_level_module_visibility_report()
    failures: list[str] = []
    for entry in report.entries:
        leaked_private = [
            name for name in entry.private_module_files if not name.startswith("_")
        ]
        if leaked_private:
            leaked = ", ".join(sorted(leaked_private))
            failures.append(
                f"{entry.distribution_name} exposes undeclared top-level modules without private naming: {leaked}"
            )
        leaked_public = [
            name for name in entry.public_module_files if name.startswith("_")
        ]
        if leaked_public:
            leaked = ", ".join(sorted(leaked_public))
            failures.append(
                f"{entry.distribution_name} declared underscored private modules as public root modules: {leaked}"
            )
    return tuple(failures)


def _toml_text(report: PackageTopLevelModuleVisibilityReport) -> str:
    lines = [
        "# Generated canonical package top-level module visibility report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.top_level_module_visibility",
        "",
    ]
    for entry in report.entries:
        public_modules = ", ".join(f'"{value}"' for value in entry.public_module_files)
        private_modules = ", ".join(f'"{value}"' for value in entry.private_module_files)
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"public_module_files = [{public_modules}]",
                f"private_module_files = [{private_modules}]",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageTopLevelModuleVisibilityReport) -> bool:
    if not TOP_LEVEL_MODULE_VISIBILITY_PATH.exists():
        return False
    return TOP_LEVEL_MODULE_VISIBILITY_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_top_level_module_visibility_report()
    failures = validate_top_level_module_visibility(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("top-level module visibility report is up to date")
            return 0
        print("top-level module visibility report is stale; regenerate it")
        return 1
    TOP_LEVEL_MODULE_VISIBILITY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated top-level module visibility report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the canonical top-level module visibility report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the top-level module visibility report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
