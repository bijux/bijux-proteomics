from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    root_python_modules,
    workspace_import_path,
)

__all__ = [
    "ROOT_MODULE_MIGRATION_SURFACES_PATH",
    "RootModuleMigrationSurfaceEntry",
    "RootModuleMigrationSurfaceReport",
    "build_root_module_migration_surface_report",
    "run",
    "validate_root_module_migration_surface_report",
]


ROOT_MODULE_MIGRATION_SURFACES_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "root-module-migration-surfaces.toml"
)
_CANONICAL_PACKAGES = (
    "bijux-proteomics-foundation",
    "bijux-proteomics-core",
)


@dataclass(frozen=True)
class RootModuleMigrationSurfaceEntry:
    """One compatibility root module and its canonical private owner."""

    distribution_name: str
    legacy_import_path: str
    canonical_import_path: str
    module_file: str
    retirement_condition: str
    rationale: str


@dataclass(frozen=True)
class RootModuleMigrationSurfaceReport:
    """Checked report over deprecated root-module compatibility surfaces."""

    entries: tuple[RootModuleMigrationSurfaceEntry, ...]


def build_root_module_migration_surface_report() -> RootModuleMigrationSurfaceReport:
    """Build the checked compatibility report for migrated root modules."""

    entries: list[RootModuleMigrationSurfaceEntry] = []
    with workspace_import_path():
        for package_name in _CANONICAL_PACKAGES:
            root_name = import_root(package_name)
            for path in root_python_modules(package_name):
                if path.name in {
                    "__init__.py",
                    "public_api.py",
                } or path.name.startswith("_"):
                    continue
                module = importlib.import_module(f"{root_name}.{path.stem}")
                migration_surface = getattr(module, "MIGRATION_SURFACE", None)
                if migration_surface is None:
                    continue
                entries.append(
                    RootModuleMigrationSurfaceEntry(
                        distribution_name=package_name,
                        legacy_import_path=str(migration_surface.legacy_import_path),
                        canonical_import_path=str(
                            migration_surface.canonical_import_path
                        ),
                        module_file=path.name,
                        retirement_condition=str(
                            migration_surface.retirement_condition
                        ),
                        rationale=str(migration_surface.rationale),
                    )
                )
    return RootModuleMigrationSurfaceReport(
        entries=tuple(
            sorted(
                entries,
                key=lambda entry: (entry.distribution_name, entry.legacy_import_path),
            )
        )
    )


def validate_root_module_migration_surface_report(
    report: RootModuleMigrationSurfaceReport | None = None,
) -> tuple[str, ...]:
    """Fail release when migrated root modules lose explicit compatibility metadata."""

    report = report or build_root_module_migration_surface_report()
    failures: list[str] = []
    for entry in report.entries:
        expected_legacy_import = f"{import_root(entry.distribution_name)}.{entry.module_file.removesuffix('.py')}"
        if entry.legacy_import_path != expected_legacy_import:
            failures.append(
                f"{entry.distribution_name} migration surface {entry.module_file} no longer matches its legacy import path"
            )
        if not entry.canonical_import_path.split(".")[-1].startswith("_"):
            failures.append(
                f"{entry.legacy_import_path} no longer points to a private canonical owner"
            )
        if not entry.retirement_condition:
            failures.append(
                f"{entry.legacy_import_path} is missing a retirement condition"
            )
        if not entry.rationale:
            failures.append(f"{entry.legacy_import_path} is missing a rationale")
    return tuple(failures)


def _toml_text(report: RootModuleMigrationSurfaceReport) -> str:
    lines = [
        "# Generated root-module migration surface report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.root_module_migration_surfaces",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[surface]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'legacy_import_path = "{entry.legacy_import_path}"',
                f'canonical_import_path = "{entry.canonical_import_path}"',
                f'module_file = "{entry.module_file}"',
                f'retirement_condition = "{entry.retirement_condition}"',
                f'rationale = "{entry.rationale}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: RootModuleMigrationSurfaceReport) -> bool:
    if not ROOT_MODULE_MIGRATION_SURFACES_PATH.exists():
        return False
    return ROOT_MODULE_MIGRATION_SURFACES_PATH.read_text(
        encoding="utf-8"
    ) == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_root_module_migration_surface_report()
    failures = validate_root_module_migration_surface_report(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("root module migration surface report is up to date")
            return 0
        print("root module migration surface report is stale; regenerate it")
        return 1
    ROOT_MODULE_MIGRATION_SURFACES_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated root module migration surface report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the root-module migration surface report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the root-module migration surface report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
