from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics_dev.api.runtime_topology import REPO_ROOT
from bijux_proteomics_intelligence.governance.charter import (
    list_intelligence_capability_map,
)

__all__ = [
    "INTELLIGENCE_BOUNDARY_MIX_PATH",
    "IntelligenceBoundaryMixEntry",
    "IntelligenceBoundaryMixGuard",
    "IntelligenceBoundaryMixMetrics",
    "IntelligenceBoundaryMixReport",
    "build_intelligence_boundary_mix_report",
    "run",
    "validate_intelligence_boundary_mix",
]


@dataclass(frozen=True)
class IntelligenceBoundaryMixEntry:
    """One intelligence owner module and the analytical bands it touches."""

    module_path: str
    band: str
    touched_band_count: int
    cross_band_import_count: int
    internal_import_count: int
    touched_bands: tuple[str, ...]
    hotspot: bool


@dataclass(frozen=True)
class IntelligenceBoundaryMixMetrics:
    """Current cross-band mix shape for intelligence owner modules."""

    scanned_module_count: int
    hotspot_count: int
    max_touched_band_count: int
    entries: tuple[IntelligenceBoundaryMixEntry, ...]


@dataclass(frozen=True)
class IntelligenceBoundaryMixGuard:
    """Release-blocking guardrails for intelligence boundary-mix spread."""

    baseline_hotspot_count: int
    baseline_max_touched_band_count: int
    baseline_hotspot_modules: tuple[str, ...]


@dataclass(frozen=True)
class IntelligenceBoundaryMixReport:
    """Checked intelligence boundary-mix report."""

    metrics: IntelligenceBoundaryMixMetrics
    guard: IntelligenceBoundaryMixGuard


INTELLIGENCE_SRC_ROOT = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-intelligence"
    / "src"
    / "bijux_proteomics_intelligence"
)
INTELLIGENCE_BOUNDARY_MIX_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "intelligence-boundary-mix.toml"
)


def _module_band_map() -> dict[str, str]:
    band_map: dict[str, str] = {}
    for entry in list_intelligence_capability_map():
        for required_module in entry.required_modules:
            if required_module.endswith("/"):
                directory = INTELLIGENCE_SRC_ROOT / required_module.rstrip("/")
                for path in sorted(directory.rglob("*.py")):
                    if path.name == "__init__.py":
                        continue
                    band_map[path.relative_to(INTELLIGENCE_SRC_ROOT).as_posix()] = (
                        entry.band.value
                    )
                continue
            band_map[required_module] = entry.band.value
    return band_map


def _dotted_band_map(module_band_map: dict[str, str]) -> dict[str, str]:
    return {
        module_path.removesuffix(".py").replace("/", "."): band
        for module_path, band in module_band_map.items()
    }


def _internal_imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("bijux_proteomics_intelligence."):
                    imports.add(alias.name.removeprefix("bijux_proteomics_intelligence."))
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(
            "bijux_proteomics_intelligence."
        ):
            imports.add(node.module.removeprefix("bijux_proteomics_intelligence."))
    return tuple(sorted(imports))


def build_intelligence_boundary_mix_report() -> IntelligenceBoundaryMixReport:
    """Build the checked report of intelligence modules that mix bands heavily."""

    module_band_map = _module_band_map()
    dotted_band_map = _dotted_band_map(module_band_map)
    entries: list[IntelligenceBoundaryMixEntry] = []
    for module_path, band in sorted(module_band_map.items()):
        path = INTELLIGENCE_SRC_ROOT / module_path
        touched_bands = {band}
        cross_band_import_count = 0
        internal_import_count = 0
        for imported_module in _internal_imports(path):
            imported_band = dotted_band_map.get(imported_module)
            if imported_band is None:
                continue
            internal_import_count += 1
            touched_bands.add(imported_band)
            if imported_band != band:
                cross_band_import_count += 1
        touched_band_names = tuple(sorted(touched_bands))
        entries.append(
            IntelligenceBoundaryMixEntry(
                module_path=module_path,
                band=band,
                touched_band_count=len(touched_band_names),
                cross_band_import_count=cross_band_import_count,
                internal_import_count=internal_import_count,
                touched_bands=touched_band_names,
                hotspot=len(touched_band_names) >= 3,
            )
        )
    metrics = IntelligenceBoundaryMixMetrics(
        scanned_module_count=len(entries),
        hotspot_count=sum(1 for entry in entries if entry.hotspot),
        max_touched_band_count=max(
            (entry.touched_band_count for entry in entries),
            default=0,
        ),
        entries=tuple(entries),
    )
    baseline_hotspot_modules = tuple(
        entry.module_path for entry in entries if entry.hotspot
    )
    return IntelligenceBoundaryMixReport(
        metrics=metrics,
        guard=IntelligenceBoundaryMixGuard(
            baseline_hotspot_count=metrics.hotspot_count,
            baseline_max_touched_band_count=metrics.max_touched_band_count,
            baseline_hotspot_modules=baseline_hotspot_modules,
        ),
    )


def validate_intelligence_boundary_mix() -> tuple[str, ...]:
    """Fail when cross-band intelligence hotspots spread beyond the governed set."""

    report = build_intelligence_boundary_mix_report()
    metrics = report.metrics
    guard = report.guard
    failures: list[str] = []
    current_hotspots = tuple(entry.module_path for entry in metrics.entries if entry.hotspot)

    if metrics.hotspot_count > guard.baseline_hotspot_count:
        failures.append("intelligence cross-band hotspots increased")
    if metrics.max_touched_band_count > guard.baseline_max_touched_band_count:
        failures.append("intelligence modules now touch more analytical bands than governed")
    if current_hotspots != guard.baseline_hotspot_modules:
        failures.append("intelligence hotspot modules drifted from the governed set")
    return tuple(failures)


def _toml_text(report: IntelligenceBoundaryMixReport) -> str:
    metrics = report.metrics
    guard = report.guard
    lines = [
        "# Generated intelligence boundary-mix report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.intelligence_boundary_mix",
        "",
        "[metrics]",
        f"scanned_module_count = {metrics.scanned_module_count}",
        f"hotspot_count = {metrics.hotspot_count}",
        f"max_touched_band_count = {metrics.max_touched_band_count}",
        "",
        "[guard]",
        f"baseline_hotspot_count = {guard.baseline_hotspot_count}",
        f"baseline_max_touched_band_count = {guard.baseline_max_touched_band_count}",
        "baseline_hotspot_modules = ["
        + ", ".join(f'"{module_path}"' for module_path in guard.baseline_hotspot_modules)
        + "]",
        "",
    ]
    for entry in metrics.entries:
        lines.extend(
            [
                "[[module]]",
                f'module_path = "{entry.module_path}"',
                f'band = "{entry.band}"',
                f"touched_band_count = {entry.touched_band_count}",
                f"cross_band_import_count = {entry.cross_band_import_count}",
                f"internal_import_count = {entry.internal_import_count}",
                "touched_bands = ["
                + ", ".join(f'"{band}"' for band in entry.touched_bands)
                + "]",
                f"hotspot = {str(entry.hotspot).lower()}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: IntelligenceBoundaryMixReport) -> bool:
    if not INTELLIGENCE_BOUNDARY_MIX_PATH.exists():
        return False
    return INTELLIGENCE_BOUNDARY_MIX_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_intelligence_boundary_mix_report()
    failures = validate_intelligence_boundary_mix()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("intelligence boundary-mix report is up to date")
            return 0
        print("intelligence boundary-mix report is stale; regenerate it")
        return 1
    INTELLIGENCE_BOUNDARY_MIX_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated intelligence boundary-mix report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the intelligence boundary-mix report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the intelligence boundary-mix report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
