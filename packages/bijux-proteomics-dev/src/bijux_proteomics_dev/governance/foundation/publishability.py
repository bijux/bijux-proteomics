from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.foundation.kernel_boundaries import (
    FOUNDATION_KERNEL_BOUNDARIES_PATH,
    build_foundation_kernel_boundaries,
    validate_foundation_kernel_boundaries,
)
from bijux_proteomics_dev.governance.foundation.root_consumers import (
    REPO_ROOT,
    build_foundation_root_consumers,
)
from bijux_proteomics_dev.governance.foundation.size_reuse import (
    FOUNDATION_SIZE_REUSE_PATH,
    build_foundation_size_reuse_report,
    validate_foundation_size_reuse,
)
from bijux_proteomics_dev.governance.package_shape.public_surfaces import (
    default_public_surface_contracts,
)

__all__ = [
    "FOUNDATION_PUBLISHABILITY_PATH",
    "FoundationPublishabilityGuard",
    "FoundationPublishabilityReport",
    "build_foundation_publishability_report",
    "run",
    "validate_foundation_publishability",
]


FOUNDATION_PUBLISHABILITY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-publishability.toml"
)


@dataclass(frozen=True)
class FoundationPublishabilityGuard:
    """Release thresholds for a publishable foundation surface."""

    max_supported_attribute_count: int
    max_root_public_symbol_count: int
    min_downstream_distribution_count: int
    min_supported_multi_distribution_count: int
    max_supported_single_distribution_count: int


@dataclass(frozen=True)
class FoundationPublishabilityReport:
    """One checked publishability decision for foundation."""

    supported_attributes: tuple[str, ...]
    supported_attribute_count: int
    root_public_symbol_count: int
    downstream_distribution_count: int
    consumer_modules_per_symbol: float
    supported_multi_distribution_count: int
    supported_single_distribution_count: int
    unsupported_reuse_gaps: tuple[str, ...]
    kernel_boundaries_ready: bool
    size_reuse_ready: bool
    guard: FoundationPublishabilityGuard

    @property
    def publishable(self) -> bool:
        return not validate_foundation_publishability(self)


def _foundation_supported_attributes() -> tuple[str, ...]:
    contract = next(
        contract
        for contract in default_public_surface_contracts()
        if contract.distribution_name == "bijux-proteomics-foundation"
    )
    return contract.supported_attributes


def build_foundation_publishability_report() -> FoundationPublishabilityReport:
    """Build the checked publishability report for foundation."""

    supported_attributes = _foundation_supported_attributes()
    root_entries = {
        entry.symbol_name: entry for entry in build_foundation_root_consumers()
    }
    size_reuse_report = build_foundation_size_reuse_report()
    kernel_checks = build_foundation_kernel_boundaries()

    multi_distribution_count = 0
    single_distribution_count = 0
    reuse_gaps: list[str] = []

    for attribute in supported_attributes:
        entry = root_entries.get(attribute)
        if entry is None:
            reuse_gaps.append(f"{attribute}: missing from foundation root consumer report")
            continue
        distribution_count = len(entry.consumer_distributions)
        if distribution_count >= 2:
            multi_distribution_count += 1
        elif distribution_count == 1:
            single_distribution_count += 1
        else:
            reuse_gaps.append(f"{attribute}: no downstream consumer distributions")

    metrics = size_reuse_report.metrics
    guard = FoundationPublishabilityGuard(
        max_supported_attribute_count=len(supported_attributes),
        max_root_public_symbol_count=size_reuse_report.guard.baseline_root_public_symbol_count,
        min_downstream_distribution_count=size_reuse_report.guard.baseline_root_consumer_distribution_count,
        min_supported_multi_distribution_count=max(0, len(supported_attributes) - 1),
        max_supported_single_distribution_count=1,
    )
    return FoundationPublishabilityReport(
        supported_attributes=supported_attributes,
        supported_attribute_count=len(supported_attributes),
        root_public_symbol_count=metrics.root_public_symbol_count,
        downstream_distribution_count=metrics.root_consumer_distribution_count,
        consumer_modules_per_symbol=metrics.root_consumer_modules_per_symbol,
        supported_multi_distribution_count=multi_distribution_count,
        supported_single_distribution_count=single_distribution_count,
        unsupported_reuse_gaps=tuple(sorted(reuse_gaps)),
        kernel_boundaries_ready=all(check.ready for check in kernel_checks),
        size_reuse_ready=not validate_foundation_size_reuse(),
        guard=guard,
    )


def validate_foundation_publishability(
    report: FoundationPublishabilityReport | None = None,
) -> tuple[str, ...]:
    """Fail release when foundation stops being narrow and clearly reused."""

    report = report or build_foundation_publishability_report()
    failures: list[str] = []

    if report.supported_attribute_count > report.guard.max_supported_attribute_count:
        failures.append("foundation supported attribute count grew beyond the guarded publishability surface")
    if report.root_public_symbol_count > report.guard.max_root_public_symbol_count:
        failures.append("foundation root public symbol count grew beyond the guarded publishability budget")
    if report.downstream_distribution_count < report.guard.min_downstream_distribution_count:
        failures.append("foundation reuse fell below the guarded downstream distribution count")
    if (
        report.supported_multi_distribution_count
        < report.guard.min_supported_multi_distribution_count
    ):
        failures.append(
            "foundation publishability requires almost every supported root attribute to be reused by multiple downstream distributions"
        )
    if (
        report.supported_single_distribution_count
        > report.guard.max_supported_single_distribution_count
    ):
        failures.append(
            "foundation publishability allows at most one supported root attribute with single-distribution reuse"
        )
    if report.unsupported_reuse_gaps:
        failures.append(
            "foundation publishability found unsupported reuse gaps: "
            + ", ".join(report.unsupported_reuse_gaps)
        )
    if not report.kernel_boundaries_ready:
        failures.append(
            "foundation publishability requires a clean kernel boundary report"
        )
    if not report.size_reuse_ready:
        failures.append(
            "foundation publishability requires a clean size-versus-reuse guard"
        )

    for failure in validate_foundation_kernel_boundaries():
        failures.append(f"kernel-boundary: {failure}")
    for failure in validate_foundation_size_reuse():
        failures.append(f"size-reuse: {failure}")

    return tuple(failures)


def _toml_text(report: FoundationPublishabilityReport) -> str:
    supported_attributes = ", ".join(f'"{value}"' for value in report.supported_attributes)
    reuse_gaps = ", ".join(f'"{value}"' for value in report.unsupported_reuse_gaps)
    guard = report.guard
    return "\n".join(
        (
            "# Generated foundation publishability report.",
            "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.foundation.publishability",
            "",
            "[metrics]",
            f"supported_attributes = [{supported_attributes}]",
            f"supported_attribute_count = {report.supported_attribute_count}",
            f"root_public_symbol_count = {report.root_public_symbol_count}",
            f"downstream_distribution_count = {report.downstream_distribution_count}",
            f"consumer_modules_per_symbol = {report.consumer_modules_per_symbol}",
            (
                "supported_multi_distribution_count = "
                f"{report.supported_multi_distribution_count}"
            ),
            (
                "supported_single_distribution_count = "
                f"{report.supported_single_distribution_count}"
            ),
            f"unsupported_reuse_gaps = [{reuse_gaps}]",
            f"kernel_boundaries_ready = {str(report.kernel_boundaries_ready).lower()}",
            f"size_reuse_ready = {str(report.size_reuse_ready).lower()}",
            f"publishable = {str(report.publishable).lower()}",
            "",
            "[guard]",
            f"max_supported_attribute_count = {guard.max_supported_attribute_count}",
            f"max_root_public_symbol_count = {guard.max_root_public_symbol_count}",
            (
                "min_downstream_distribution_count = "
                f"{guard.min_downstream_distribution_count}"
            ),
            (
                "min_supported_multi_distribution_count = "
                f"{guard.min_supported_multi_distribution_count}"
            ),
            (
                "max_supported_single_distribution_count = "
                f"{guard.max_supported_single_distribution_count}"
            ),
            "",
            "[evidence]",
            f'kernel_boundaries_path = "{FOUNDATION_KERNEL_BOUNDARIES_PATH.relative_to(REPO_ROOT).as_posix()}"',
            f'size_reuse_path = "{FOUNDATION_SIZE_REUSE_PATH.relative_to(REPO_ROOT).as_posix()}"',
        )
    )


def _is_up_to_date(report: FoundationPublishabilityReport) -> bool:
    if not FOUNDATION_PUBLISHABILITY_PATH.exists():
        return False
    return FOUNDATION_PUBLISHABILITY_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_foundation_publishability_report()
    failures = validate_foundation_publishability(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("foundation publishability report is up to date")
            return 0
        print("foundation publishability report is stale; regenerate it")
        return 1
    FOUNDATION_PUBLISHABILITY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated foundation publishability report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the foundation publishability report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the foundation publishability report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
