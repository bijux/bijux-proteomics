from __future__ import annotations

import argparse
from dataclasses import dataclass
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.package_shape.package_surface_pressure import (
    build_package_surface_pressure_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_ROOT_SURFACE_ILLUSIONS_PATH",
    "PackageRootSurfaceIllusionEntry",
    "PackageRootSurfaceIllusionGuard",
    "PackageRootSurfaceIllusionReport",
    "build_package_root_surface_illusion_report",
    "run",
    "validate_package_root_surface_illusions",
]


PACKAGE_ROOT_SURFACE_ILLUSIONS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-root-surface-illusions.toml"
)


@dataclass(frozen=True)
class PackageRootSurfaceIllusionEntry:
    """One package area whose root surface hides awkward internals."""

    distribution_name: str
    compatibility_surfaces: tuple[str, ...]
    root_public_module_count: int
    root_export_symbol_count: int
    owner_logic_module_count: int
    illusion_reasons: tuple[str, ...]
    root_surface_hides_owner_depth: bool


@dataclass(frozen=True)
class PackageRootSurfaceIllusionGuard:
    """Release-blocking baseline for root-surface illusion pressure."""

    max_total_root_surface_illusion_count: int


@dataclass(frozen=True)
class PackageRootSurfaceIllusionReport:
    """Checked root-surface illusion report across workspace packages."""

    entries: tuple[PackageRootSurfaceIllusionEntry, ...]
    guard: PackageRootSurfaceIllusionGuard


def _load_tree_dossiers() -> dict[str, dict[str, Any]]:
    with (
        REPO_ROOT / "configs" / "package-governance" / "package-tree-dossiers.toml"
    ).open("rb") as handle:
        data = tomllib.load(handle)
    package_rows = data["package"]
    if not isinstance(package_rows, list) or not all(
        isinstance(row, dict) for row in package_rows
    ):
        raise TypeError(
            "package-tree-dossiers.toml:package must be a list of TOML tables"
        )
    return {
        str(entry["distribution_name"]): cast(dict[str, Any], entry)
        for entry in package_rows
    }


def build_package_root_surface_illusion_report() -> PackageRootSurfaceIllusionReport:
    """Build the checked root-surface illusion report."""

    tree_dossiers = _load_tree_dossiers()
    surface_pressure = {
        entry.distribution_name: entry
        for entry in build_package_surface_pressure_report().entries
    }
    entries: list[PackageRootSurfaceIllusionEntry] = []
    for package_name in sorted(tree_dossiers):
        tree_entry = tree_dossiers[package_name]
        pressure_entry = surface_pressure[package_name]
        compatibility_surfaces = tuple(
            str(value) for value in tree_entry["compatibility_surfaces"]
        )
        reasons: list[str] = []
        if compatibility_surfaces:
            reasons.append(
                f"{len(compatibility_surfaces)} compatibility surfaces still survive at the package root"
            )
        if pressure_entry.breadth_outpaces_owner_logic:
            reasons.append("root public breadth still exceeds owner logic depth")
        if pressure_entry.public_module_count >= max(
            len(tree_entry["owner_domains"]), 1
        ):
            reasons.append(
                "root public module count still rivals the package owner-family count"
            )
        entries.append(
            PackageRootSurfaceIllusionEntry(
                distribution_name=package_name,
                compatibility_surfaces=compatibility_surfaces,
                root_public_module_count=int(pressure_entry.public_module_count),
                root_export_symbol_count=int(pressure_entry.root_export_symbol_count),
                owner_logic_module_count=int(pressure_entry.owner_logic_module_count),
                illusion_reasons=tuple(reasons),
                root_surface_hides_owner_depth=bool(reasons),
            )
        )
    return PackageRootSurfaceIllusionReport(
        entries=tuple(entries),
        guard=PackageRootSurfaceIllusionGuard(
            max_total_root_surface_illusion_count=sum(
                entry.root_surface_hides_owner_depth for entry in entries
            )
        ),
    )


def validate_package_root_surface_illusions(
    report: PackageRootSurfaceIllusionReport | None = None,
) -> tuple[str, ...]:
    """Fail release when more packages need root-surface caveats."""

    report = report or build_package_root_surface_illusion_report()
    total_root_surface_illusion_count = sum(
        entry.root_surface_hides_owner_depth for entry in report.entries
    )
    if (
        total_root_surface_illusion_count
        <= report.guard.max_total_root_surface_illusion_count
    ):
        return ()
    return (
        "root-surface illusion count grew beyond the governed owner-depth baseline",
    )


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(
        f'"{value.replace(chr(34), chr(92) + chr(34))}"' for value in values
    )


def _toml_text(report: PackageRootSurfaceIllusionReport) -> str:
    lines = [
        "# Generated package root-surface illusion report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_root_surface_illusions",
        "",
        "[guard]",
        f"max_total_root_surface_illusion_count = {report.guard.max_total_root_surface_illusion_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"compatibility_surfaces = [{_render_tuple(entry.compatibility_surfaces)}]",
                f"root_public_module_count = {entry.root_public_module_count}",
                f"root_export_symbol_count = {entry.root_export_symbol_count}",
                f"owner_logic_module_count = {entry.owner_logic_module_count}",
                f"illusion_reasons = [{_render_tuple(entry.illusion_reasons)}]",
                (
                    "root_surface_hides_owner_depth = "
                    f"{str(entry.root_surface_hides_owner_depth).lower()}"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageRootSurfaceIllusionReport) -> bool:
    if not PACKAGE_ROOT_SURFACE_ILLUSIONS_PATH.exists():
        return False
    return PACKAGE_ROOT_SURFACE_ILLUSIONS_PATH.read_text(
        encoding="utf-8"
    ) == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_root_surface_illusion_report()
    failures = validate_package_root_surface_illusions(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package root-surface illusion report is up to date")
            return 0
        print("package root-surface illusion report is stale; regenerate it")
        return 1
    PACKAGE_ROOT_SURFACE_ILLUSIONS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package root-surface illusion report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package root-surface illusion report."
    )
    parser.add_argument(
        "--check", action="store_true", help="Fail if the report is stale."
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
