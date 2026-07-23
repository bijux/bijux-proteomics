from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    import_root,
    is_wrapper_module,
    package_root,
    root_python_modules,
    source_owner_families,
    workspace_package_names,
)

__all__ = [
    "PACKAGE_TREE_DOSSIERS_PATH",
    "PackageTreeDossierEntry",
    "PackageTreeDossierGuard",
    "PackageTreeDossierReport",
    "build_package_tree_dossier_report",
    "run",
    "validate_package_tree_dossier",
]


PACKAGE_TREE_DOSSIERS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-tree-dossiers.toml"
)


@dataclass(frozen=True)
class PackageTreeDossierEntry:
    """One package-tree dossier with owners, roots, shims, and exclusions."""

    distribution_name: str
    import_root: str
    owner_domains: tuple[str, ...]
    public_modules: tuple[str, ...]
    compatibility_surfaces: tuple[str, ...]
    excluded_responsibilities: tuple[str, ...]


@dataclass(frozen=True)
class PackageTreeDossierGuard:
    """Release-blocking guardrails over package-tree dossier drift."""

    min_total_owner_domain_count: int
    max_total_compatibility_surface_count: int
    min_total_excluded_responsibility_count: int


@dataclass(frozen=True)
class PackageTreeDossierReport:
    """Checked package-tree dossiers across repository packages."""

    entries: tuple[PackageTreeDossierEntry, ...]
    guard: PackageTreeDossierGuard


def _public_module_names(package_name: str) -> tuple[str, ...]:
    return tuple(
        path.stem
        for path in root_python_modules(package_name)
        if path.stem != "__init__"
    )


def _compatibility_surface_names(package_name: str) -> tuple[str, ...]:
    return tuple(
        path.stem
        for path in root_python_modules(package_name)
        if path.stem != "__init__" and is_wrapper_module(path)
    )


def _section_lines(path: Path, heading: str) -> tuple[str, ...]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    section: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() == heading
            continue
        if in_section:
            section.append(line.rstrip())
    return tuple(section)


def _boundary_doc_path(package_name: str) -> Path:
    root = package_root(package_name)
    if package_name == "bijux-proteomics-dev":
        return root / "docs" / "SCOPE.md"
    return root / "docs" / "BOUNDARIES.md"


def _excluded_responsibilities(package_name: str) -> tuple[str, ...]:
    path = _boundary_doc_path(package_name)
    section = _section_lines(path, "## This package does not own")
    values = [line[2:].strip() for line in section if line.startswith("- ")]
    return tuple(values)


def build_package_tree_dossier_report() -> PackageTreeDossierReport:
    """Build the checked package-tree dossier report."""

    entries = tuple(
        PackageTreeDossierEntry(
            distribution_name=package_name,
            import_root=import_root(package_name),
            owner_domains=source_owner_families(package_name),
            public_modules=_public_module_names(package_name),
            compatibility_surfaces=_compatibility_surface_names(package_name),
            excluded_responsibilities=_excluded_responsibilities(package_name),
        )
        for package_name in workspace_package_names()
    )
    return PackageTreeDossierReport(
        entries=entries,
        guard=PackageTreeDossierGuard(
            min_total_owner_domain_count=sum(
                len(entry.owner_domains) for entry in entries
            ),
            max_total_compatibility_surface_count=sum(
                len(entry.compatibility_surfaces) for entry in entries
            ),
            min_total_excluded_responsibility_count=sum(
                len(entry.excluded_responsibilities) for entry in entries
            ),
        ),
    )


def validate_package_tree_dossier(
    report: PackageTreeDossierReport | None = None,
) -> tuple[str, ...]:
    """Fail release when package-tree dossiers lose clarity or grow more shims."""

    report = report or build_package_tree_dossier_report()
    failures: list[str] = []
    owner_domain_count = sum(len(entry.owner_domains) for entry in report.entries)
    compatibility_surface_count = sum(
        len(entry.compatibility_surfaces) for entry in report.entries
    )
    excluded_responsibility_count = sum(
        len(entry.excluded_responsibilities) for entry in report.entries
    )
    if owner_domain_count < report.guard.min_total_owner_domain_count:
        failures.append(
            "package owner-domain coverage dropped below the governed dossier baseline"
        )
    if compatibility_surface_count > report.guard.max_total_compatibility_surface_count:
        failures.append(
            "package compatibility-surface count grew beyond the governed dossier baseline"
        )
    if (
        excluded_responsibility_count
        < report.guard.min_total_excluded_responsibility_count
    ):
        failures.append(
            "package excluded-responsibility coverage dropped below the governed dossier baseline"
        )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(f'"{value}"' for value in values)


def _toml_text(report: PackageTreeDossierReport) -> str:
    lines = [
        "# Generated package-tree dossier report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_tree_dossiers",
        "",
        "[guard]",
        f"min_total_owner_domain_count = {report.guard.min_total_owner_domain_count}",
        f"max_total_compatibility_surface_count = {report.guard.max_total_compatibility_surface_count}",
        (
            "min_total_excluded_responsibility_count = "
            f"{report.guard.min_total_excluded_responsibility_count}"
        ),
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'import_root = "{entry.import_root}"',
                f"owner_domains = [{_render_tuple(entry.owner_domains)}]",
                f"public_modules = [{_render_tuple(entry.public_modules)}]",
                f"compatibility_surfaces = [{_render_tuple(entry.compatibility_surfaces)}]",
                (
                    "excluded_responsibilities = "
                    f"[{_render_tuple(entry.excluded_responsibilities)}]"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageTreeDossierReport) -> bool:
    if not PACKAGE_TREE_DOSSIERS_PATH.exists():
        return False
    return PACKAGE_TREE_DOSSIERS_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_tree_dossier_report()
    failures = validate_package_tree_dossier(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package-tree dossier report is up to date")
            return 0
        print("package-tree dossier report is stale; regenerate it")
        return 1
    PACKAGE_TREE_DOSSIERS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package-tree dossier report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package-tree dossier report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package-tree dossier report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
