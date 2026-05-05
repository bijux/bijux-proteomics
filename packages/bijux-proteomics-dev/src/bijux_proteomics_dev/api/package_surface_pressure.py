from __future__ import annotations

import argparse
from dataclasses import dataclass
import tomllib

from bijux_proteomics_dev.api.package_module_ledger import build_package_module_ledger_report
from bijux_proteomics_dev.api.public_symbol_ledger import build_public_symbol_ledger_report
from bijux_proteomics_dev.api.runtime_topology import REPO_ROOT

__all__ = [
    "PACKAGE_SURFACE_PRESSURE_PATH",
    "PackageSurfacePressureEntry",
    "PackageSurfacePressureGuard",
    "PackageSurfacePressureReport",
    "build_package_surface_pressure_report",
    "run",
    "validate_package_surface_pressure",
]


PACKAGE_SURFACE_PRESSURE_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-surface-pressure.toml"
)
PACKAGE_TREE_DOSSIERS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-tree-dossiers.toml"
)


@dataclass(frozen=True)
class PackageSurfacePressureEntry:
    """Public breadth versus owned owner-logic depth for one package."""

    distribution_name: str
    owner_logic_module_count: int
    compatibility_surface_count: int
    root_export_symbol_count: int
    public_module_count: int
    public_breadth_count: int
    breadth_to_owner_ratio: float
    breadth_outpaces_owner_logic: bool


@dataclass(frozen=True)
class PackageSurfacePressureGuard:
    """Release-blocking baseline for surface breadth pressure."""

    max_total_root_export_symbol_count: int
    max_total_public_breadth_count: int
    max_overexposed_package_count: int


@dataclass(frozen=True)
class PackageSurfacePressureReport:
    """Checked public breadth pressure report across workspace packages."""

    entries: tuple[PackageSurfacePressureEntry, ...]
    guard: PackageSurfacePressureGuard


def _load_tree_dossiers() -> dict[str, dict[str, object]]:
    with PACKAGE_TREE_DOSSIERS_PATH.open("rb") as handle:
        data = tomllib.load(handle)
    return {
        entry["distribution_name"]: entry
        for entry in data["package"]
    }


def build_package_surface_pressure_report() -> PackageSurfacePressureReport:
    """Build the checked package surface pressure report."""

    module_ledger = build_package_module_ledger_report()
    public_symbol_ledger = build_public_symbol_ledger_report()
    tree_dossiers = _load_tree_dossiers()

    owner_logic_counts: dict[str, int] = {}
    compatibility_counts: dict[str, int] = {}
    for entry in module_ledger.entries:
        if entry.module_kind == "owner_logic":
            owner_logic_counts[entry.distribution_name] = (
                owner_logic_counts.get(entry.distribution_name, 0) + 1
            )
        elif entry.module_kind == "compatibility_surface":
            compatibility_counts[entry.distribution_name] = (
                compatibility_counts.get(entry.distribution_name, 0) + 1
            )

    root_export_counts: dict[str, int] = {}
    for entry in public_symbol_ledger.entries:
        root_export_counts[entry.distribution_name] = (
            root_export_counts.get(entry.distribution_name, 0) + 1
        )

    entries: list[PackageSurfacePressureEntry] = []
    for package_name in sorted(tree_dossiers):
        owner_logic_module_count = owner_logic_counts.get(package_name, 0)
        compatibility_surface_count = compatibility_counts.get(package_name, 0)
        root_export_symbol_count = root_export_counts.get(package_name, 0)
        public_module_count = len(tree_dossiers[package_name]["public_modules"])
        public_breadth_count = root_export_symbol_count + public_module_count
        breadth_outpaces_owner_logic = public_breadth_count > owner_logic_module_count
        breadth_to_owner_ratio = round(
            public_breadth_count / max(owner_logic_module_count, 1),
            4,
        )
        entries.append(
            PackageSurfacePressureEntry(
                distribution_name=package_name,
                owner_logic_module_count=owner_logic_module_count,
                compatibility_surface_count=compatibility_surface_count,
                root_export_symbol_count=root_export_symbol_count,
                public_module_count=public_module_count,
                public_breadth_count=public_breadth_count,
                breadth_to_owner_ratio=breadth_to_owner_ratio,
                breadth_outpaces_owner_logic=breadth_outpaces_owner_logic,
            )
        )

    return PackageSurfacePressureReport(
        entries=tuple(entries),
        guard=PackageSurfacePressureGuard(
            max_total_root_export_symbol_count=sum(
                entry.root_export_symbol_count for entry in entries
            ),
            max_total_public_breadth_count=sum(
                entry.public_breadth_count for entry in entries
            ),
            max_overexposed_package_count=sum(
                entry.breadth_outpaces_owner_logic for entry in entries
            ),
        ),
    )


def validate_package_surface_pressure(
    report: PackageSurfacePressureReport | None = None,
) -> tuple[str, ...]:
    """Fail release when public breadth expands faster than owned logic depth."""

    report = report or build_package_surface_pressure_report()
    total_root_export_symbol_count = sum(
        entry.root_export_symbol_count for entry in report.entries
    )
    total_public_breadth_count = sum(entry.public_breadth_count for entry in report.entries)
    overexposed_package_count = sum(entry.breadth_outpaces_owner_logic for entry in report.entries)
    failures: list[str] = []
    if total_root_export_symbol_count > report.guard.max_total_root_export_symbol_count:
        failures.append("root export symbol count grew beyond the governed owner-depth baseline")
    if total_public_breadth_count > report.guard.max_total_public_breadth_count:
        failures.append("public breadth grew beyond the governed owner-depth baseline")
    if overexposed_package_count > report.guard.max_overexposed_package_count:
        failures.append("more packages expose broader root surfaces than owner logic depth")
    return tuple(failures)


def _toml_text(report: PackageSurfacePressureReport) -> str:
    lines = [
        "# Generated package surface pressure report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.package_surface_pressure",
        "",
        "[guard]",
        f"max_total_root_export_symbol_count = {report.guard.max_total_root_export_symbol_count}",
        f"max_total_public_breadth_count = {report.guard.max_total_public_breadth_count}",
        f"max_overexposed_package_count = {report.guard.max_overexposed_package_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"owner_logic_module_count = {entry.owner_logic_module_count}",
                f"compatibility_surface_count = {entry.compatibility_surface_count}",
                f"root_export_symbol_count = {entry.root_export_symbol_count}",
                f"public_module_count = {entry.public_module_count}",
                f"public_breadth_count = {entry.public_breadth_count}",
                f"breadth_to_owner_ratio = {entry.breadth_to_owner_ratio}",
                f"breadth_outpaces_owner_logic = {str(entry.breadth_outpaces_owner_logic).lower()}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageSurfacePressureReport) -> bool:
    if not PACKAGE_SURFACE_PRESSURE_PATH.exists():
        return False
    return PACKAGE_SURFACE_PRESSURE_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_surface_pressure_report()
    failures = validate_package_surface_pressure(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package surface pressure report is up to date")
            return 0
        print("package surface pressure report is stale; regenerate it")
        return 1
    PACKAGE_SURFACE_PRESSURE_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package surface pressure report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package surface pressure report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package surface pressure report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
