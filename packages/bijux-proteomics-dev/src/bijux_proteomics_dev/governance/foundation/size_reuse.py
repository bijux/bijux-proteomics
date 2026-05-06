from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.foundation.root_consumers import (
    REPO_ROOT,
    build_foundation_root_consumers,
)
from bijux_proteomics_dev.governance.foundation.surface_usage import (
    build_foundation_compatibility_aliases,
    build_foundation_dead_exports,
    build_foundation_surface_consumers,
)

__all__ = [
    "FOUNDATION_SIZE_REUSE_PATH",
    "FoundationSizeReuseGuard",
    "FoundationSizeReuseMetrics",
    "FoundationSizeReuseReport",
    "build_foundation_size_reuse_report",
    "run",
    "validate_foundation_size_reuse",
]


@dataclass(frozen=True)
class FoundationSizeReuseMetrics:
    """Live foundation breadth and reuse metrics derived from checked reports."""

    root_public_symbol_count: int
    root_consumer_module_count: int
    root_consumer_distribution_count: int
    root_consumer_modules_per_symbol: float
    direct_surface_count: int
    direct_surface_consumer_module_count: int
    compatibility_wrapper_count: int
    live_compatibility_wrapper_count: int
    live_direct_export_count: int
    dead_direct_export_count: int


@dataclass(frozen=True)
class FoundationSizeReuseGuard:
    """Release-blocking guardrails for foundation breadth growth."""

    baseline_root_public_symbol_count: int
    baseline_root_consumer_module_count: int
    baseline_root_consumer_distribution_count: int
    baseline_root_consumer_modules_per_symbol: float


@dataclass(frozen=True)
class FoundationSizeReuseReport:
    """One checked report tying foundation breadth to downstream reuse."""

    metrics: FoundationSizeReuseMetrics
    guard: FoundationSizeReuseGuard


FOUNDATION_SIZE_REUSE_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-size-reuse.toml"
)


def _rounded_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 2)


def build_foundation_size_reuse_report() -> FoundationSizeReuseReport:
    """Build the checked report that pairs root breadth with downstream reuse."""

    root_entries = build_foundation_root_consumers()
    surface_entries = build_foundation_surface_consumers()
    dead_export_entries = build_foundation_dead_exports()
    compatibility_alias_entries = build_foundation_compatibility_aliases()

    root_consumer_modules = {
        module_name
        for entry in root_entries
        for module_name in entry.consumer_modules
    }
    root_consumer_distributions = {
        distribution_name
        for entry in root_entries
        for distribution_name in entry.consumer_distributions
    }
    direct_surface_entries = tuple(
        entry for entry in surface_entries if entry.module_name != "bijux_proteomics_foundation"
    )
    direct_surface_consumer_modules = {
        module_name
        for entry in direct_surface_entries
        for module_name in entry.consumer_modules
    }
    direct_dead_export_entries = tuple(
        entry
        for entry in dead_export_entries
        if entry.module_name != "bijux_proteomics_foundation"
    )
    metrics = FoundationSizeReuseMetrics(
        root_public_symbol_count=len(root_entries),
        root_consumer_module_count=len(root_consumer_modules),
        root_consumer_distribution_count=len(root_consumer_distributions),
        root_consumer_modules_per_symbol=_rounded_ratio(
            len(root_consumer_modules),
            len(root_entries),
        ),
        direct_surface_count=len(direct_surface_entries),
        direct_surface_consumer_module_count=len(direct_surface_consumer_modules),
        compatibility_wrapper_count=len(compatibility_alias_entries),
        live_compatibility_wrapper_count=sum(
            1 for entry in compatibility_alias_entries if entry.requires_alias_test
        ),
        live_direct_export_count=sum(
            len(entry.live_symbols) for entry in direct_dead_export_entries
        ),
        dead_direct_export_count=sum(
            len(entry.dead_symbols) for entry in direct_dead_export_entries
        ),
    )
    return FoundationSizeReuseReport(
        metrics=metrics,
        guard=FoundationSizeReuseGuard(
            baseline_root_public_symbol_count=metrics.root_public_symbol_count,
            baseline_root_consumer_module_count=metrics.root_consumer_module_count,
            baseline_root_consumer_distribution_count=metrics.root_consumer_distribution_count,
            baseline_root_consumer_modules_per_symbol=metrics.root_consumer_modules_per_symbol,
        ),
    )


def validate_foundation_size_reuse() -> tuple[str, ...]:
    """Fail when root breadth outgrows measured downstream reuse."""

    report = build_foundation_size_reuse_report()
    metrics = report.metrics
    guard = report.guard
    failures: list[str] = []

    if (
        metrics.root_consumer_distribution_count
        < guard.baseline_root_consumer_distribution_count
    ):
        failures.append(
            "foundation root reuse fell below the guarded downstream distribution count"
        )
    if (
        metrics.root_consumer_modules_per_symbol
        < guard.baseline_root_consumer_modules_per_symbol
    ):
        failures.append(
            "foundation root reuse fell below the guarded consumer-modules-per-symbol ratio"
        )
    if metrics.root_public_symbol_count > guard.baseline_root_public_symbol_count:
        if metrics.root_consumer_module_count <= guard.baseline_root_consumer_module_count:
            failures.append(
                "foundation root breadth grew without increasing downstream consumer modules"
            )
        if (
            metrics.root_consumer_modules_per_symbol
            <= guard.baseline_root_consumer_modules_per_symbol
        ):
            failures.append(
                "foundation root breadth grew without stronger downstream reuse per symbol"
            )
    return tuple(failures)


def _toml_text(report: FoundationSizeReuseReport) -> str:
    metrics = report.metrics
    guard = report.guard
    return "\n".join(
        (
            "# Generated foundation size-versus-reuse report.",
            "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.foundation.size_reuse",
            "",
            "[metrics]",
            f"root_public_symbol_count = {metrics.root_public_symbol_count}",
            f"root_consumer_module_count = {metrics.root_consumer_module_count}",
            f"root_consumer_distribution_count = {metrics.root_consumer_distribution_count}",
            f"root_consumer_modules_per_symbol = {metrics.root_consumer_modules_per_symbol}",
            f"direct_surface_count = {metrics.direct_surface_count}",
            (
                "direct_surface_consumer_module_count = "
                f"{metrics.direct_surface_consumer_module_count}"
            ),
            f"compatibility_wrapper_count = {metrics.compatibility_wrapper_count}",
            (
                "live_compatibility_wrapper_count = "
                f"{metrics.live_compatibility_wrapper_count}"
            ),
            f"live_direct_export_count = {metrics.live_direct_export_count}",
            f"dead_direct_export_count = {metrics.dead_direct_export_count}",
            "",
            "[guard]",
            (
                "baseline_root_public_symbol_count = "
                f"{guard.baseline_root_public_symbol_count}"
            ),
            (
                "baseline_root_consumer_module_count = "
                f"{guard.baseline_root_consumer_module_count}"
            ),
            (
                "baseline_root_consumer_distribution_count = "
                f"{guard.baseline_root_consumer_distribution_count}"
            ),
            (
                "baseline_root_consumer_modules_per_symbol = "
                f"{guard.baseline_root_consumer_modules_per_symbol}"
            ),
        )
    )


def _is_up_to_date(report: FoundationSizeReuseReport) -> bool:
    if not FOUNDATION_SIZE_REUSE_PATH.exists():
        return False
    return FOUNDATION_SIZE_REUSE_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_foundation_size_reuse_report()
    failures = validate_foundation_size_reuse()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("foundation size-versus-reuse report is up to date")
            return 0
        print("foundation size-versus-reuse report is stale; regenerate it")
        return 1
    FOUNDATION_SIZE_REUSE_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated foundation size-versus-reuse report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the foundation size-versus-reuse report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the size-versus-reuse report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
