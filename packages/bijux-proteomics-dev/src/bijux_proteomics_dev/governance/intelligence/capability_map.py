from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_intelligence.governance.charter import (
    DEFAULT_INTELLIGENCE_CAPABILITY_MAP,
    list_intelligence_analytical_bands,
)

__all__ = [
    "INTELLIGENCE_CAPABILITY_MAP_PATH",
    "IntelligenceCapabilityBandReportEntry",
    "IntelligenceCapabilityMapGuard",
    "IntelligenceCapabilityMapMetrics",
    "IntelligenceCapabilityMapReport",
    "build_intelligence_capability_map_report",
    "run",
    "validate_intelligence_capability_map",
]


@dataclass(frozen=True)
class IntelligenceCapabilityBandReportEntry:
    """One governed analytical band in the intelligence capability map."""

    band: str
    owned_surface: str
    required_modules: tuple[str, ...]
    decision_scope_count: int
    refusal_scope_count: int


@dataclass(frozen=True)
class IntelligenceCapabilityMapMetrics:
    """Current analytical-band coverage for the intelligence package."""

    analytical_band_count: int
    owned_surface_count: int
    required_module_count: int
    decision_scope_count: int
    refusal_scope_count: int
    bands: tuple[IntelligenceCapabilityBandReportEntry, ...]


@dataclass(frozen=True)
class IntelligenceCapabilityMapGuard:
    """Release-blocking guardrails for the governed capability map."""

    baseline_analytical_band_count: int
    baseline_owned_surface_count: int
    baseline_required_module_count: int


@dataclass(frozen=True)
class IntelligenceCapabilityMapReport:
    """Checked report for the intelligence capability map."""

    metrics: IntelligenceCapabilityMapMetrics
    guard: IntelligenceCapabilityMapGuard


INTELLIGENCE_CAPABILITY_MAP_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "intelligence-capability-map.toml"
)


def build_intelligence_capability_map_report() -> IntelligenceCapabilityMapReport:
    """Build the checked analytical-band capability map report."""

    bands = tuple(
        IntelligenceCapabilityBandReportEntry(
            band=entry.band.value,
            owned_surface=entry.owned_surface,
            required_modules=entry.required_modules,
            decision_scope_count=len(entry.decision_scope),
            refusal_scope_count=len(entry.refusal_scope),
        )
        for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
    )
    metrics = IntelligenceCapabilityMapMetrics(
        analytical_band_count=len(bands),
        owned_surface_count=len(bands),
        required_module_count=sum(len(entry.required_modules) for entry in bands),
        decision_scope_count=sum(entry.decision_scope_count for entry in bands),
        refusal_scope_count=sum(entry.refusal_scope_count for entry in bands),
        bands=bands,
    )
    return IntelligenceCapabilityMapReport(
        metrics=metrics,
        guard=IntelligenceCapabilityMapGuard(
            baseline_analytical_band_count=metrics.analytical_band_count,
            baseline_owned_surface_count=metrics.owned_surface_count,
            baseline_required_module_count=metrics.required_module_count,
        ),
    )


def validate_intelligence_capability_map() -> tuple[str, ...]:
    """Fail when the intelligence capability map loses stable analytical shape."""

    report = build_intelligence_capability_map_report()
    metrics = report.metrics
    guard = report.guard
    failures: list[str] = []
    seen_modules: set[str] = set()

    if tuple(list_intelligence_analytical_bands()) != tuple(
        entry.band for entry in DEFAULT_INTELLIGENCE_CAPABILITY_MAP
    ):
        failures.append("intelligence analytical bands drifted from the governed order")
    if metrics.analytical_band_count != guard.baseline_analytical_band_count:
        failures.append("intelligence capability map lost or gained analytical bands")
    if metrics.owned_surface_count != guard.baseline_owned_surface_count:
        failures.append("intelligence capability map lost or gained owned surfaces")
    if metrics.required_module_count < guard.baseline_required_module_count:
        failures.append(
            "intelligence capability map now covers fewer owner modules than governed"
        )
    for band in metrics.bands:
        for module_path in band.required_modules:
            if module_path in seen_modules:
                failures.append(
                    f"required module {module_path!r} is assigned to multiple analytical bands"
                )
            seen_modules.add(module_path)
    return tuple(failures)


def _toml_text(report: IntelligenceCapabilityMapReport) -> str:
    metrics = report.metrics
    guard = report.guard
    lines = [
        "# Generated intelligence capability map.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.intelligence.capability_map",
        "",
        "[metrics]",
        f"analytical_band_count = {metrics.analytical_band_count}",
        f"owned_surface_count = {metrics.owned_surface_count}",
        f"required_module_count = {metrics.required_module_count}",
        f"decision_scope_count = {metrics.decision_scope_count}",
        f"refusal_scope_count = {metrics.refusal_scope_count}",
        "",
        "[guard]",
        f"baseline_analytical_band_count = {guard.baseline_analytical_band_count}",
        f"baseline_owned_surface_count = {guard.baseline_owned_surface_count}",
        f"baseline_required_module_count = {guard.baseline_required_module_count}",
        "",
    ]
    for band in metrics.bands:
        lines.extend(
            [
                "[[band]]",
                f'band = "{band.band}"',
                f'owned_surface = "{band.owned_surface}"',
                "required_modules = ["
                + ", ".join(f'"{module_path}"' for module_path in band.required_modules)
                + "]",
                f"decision_scope_count = {band.decision_scope_count}",
                f"refusal_scope_count = {band.refusal_scope_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: IntelligenceCapabilityMapReport) -> bool:
    if not INTELLIGENCE_CAPABILITY_MAP_PATH.exists():
        return False
    return INTELLIGENCE_CAPABILITY_MAP_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_intelligence_capability_map_report()
    failures = validate_intelligence_capability_map()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("intelligence capability map is up to date")
            return 0
        print("intelligence capability map is stale; regenerate it")
        return 1
    INTELLIGENCE_CAPABILITY_MAP_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated intelligence capability map")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the intelligence capability map."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the intelligence capability map is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
