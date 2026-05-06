from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.api.runtime_topology import (
    REPO_ROOT,
    build_runtime_topology_budget,
)
from bijux_proteomics_runtime.governance.charter import (
    DEFAULT_RUNTIME_MODULE_AUDIT,
    RuntimeModuleClassification,
)
from bijux_proteomics_runtime.support.primitives.surface_area import (
    CONFIG_KNOBS,
    EXTENSION_POINTS,
    PUBLIC_ENTRYPOINTS,
)

__all__ = [
    "RUNTIME_BREADTH_PATH",
    "RuntimeBreadthGuard",
    "RuntimeBreadthMetrics",
    "RuntimeBreadthReport",
    "build_runtime_breadth_report",
    "run",
    "validate_runtime_breadth",
]


@dataclass(frozen=True)
class RuntimeBreadthMetrics:
    """Live runtime breadth paired with owned execution substance."""

    public_entrypoint_count: int
    extension_point_count: int
    config_knob_count: int
    first_level_subtree_count: int
    total_breadth_count: int
    owner_execution_module_count: int
    thin_module_count: int
    owner_execution_modules_per_surface: float


@dataclass(frozen=True)
class RuntimeBreadthGuard:
    """Release-blocking guardrails for runtime breadth growth."""

    baseline_total_breadth_count: int
    baseline_first_level_subtree_count: int
    baseline_owner_execution_module_count: int
    baseline_owner_execution_modules_per_surface: float


@dataclass(frozen=True)
class RuntimeBreadthReport:
    """Checked runtime breadth report."""

    metrics: RuntimeBreadthMetrics
    guard: RuntimeBreadthGuard


RUNTIME_BREADTH_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "runtime-breadth.toml"
)


def _rounded_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 2)


def build_runtime_breadth_report() -> RuntimeBreadthReport:
    """Build the checked report that pairs runtime breadth with owned logic."""

    topology = build_runtime_topology_budget()
    owner_execution_module_count = sum(
        1
        for entry in DEFAULT_RUNTIME_MODULE_AUDIT
        if entry.classification is RuntimeModuleClassification.EXECUTION_VALUE
    )
    thin_module_count = sum(
        1
        for entry in DEFAULT_RUNTIME_MODULE_AUDIT
        if entry.classification is RuntimeModuleClassification.THIN_ABSTRACTION
    )
    total_breadth_count = (
        len(PUBLIC_ENTRYPOINTS)
        + len(EXTENSION_POINTS)
        + len(CONFIG_KNOBS)
        + topology.actual_first_level_subtrees
    )
    metrics = RuntimeBreadthMetrics(
        public_entrypoint_count=len(PUBLIC_ENTRYPOINTS),
        extension_point_count=len(EXTENSION_POINTS),
        config_knob_count=len(CONFIG_KNOBS),
        first_level_subtree_count=topology.actual_first_level_subtrees,
        total_breadth_count=total_breadth_count,
        owner_execution_module_count=owner_execution_module_count,
        thin_module_count=thin_module_count,
        owner_execution_modules_per_surface=_rounded_ratio(
            owner_execution_module_count,
            total_breadth_count,
        ),
    )
    return RuntimeBreadthReport(
        metrics=metrics,
        guard=RuntimeBreadthGuard(
            baseline_total_breadth_count=metrics.total_breadth_count,
            baseline_first_level_subtree_count=metrics.first_level_subtree_count,
            baseline_owner_execution_module_count=metrics.owner_execution_module_count,
            baseline_owner_execution_modules_per_surface=(
                metrics.owner_execution_modules_per_surface
            ),
        ),
    )


def validate_runtime_breadth() -> tuple[str, ...]:
    """Fail when runtime breadth grows faster than owned execution logic."""

    report = build_runtime_breadth_report()
    metrics = report.metrics
    guard = report.guard
    failures: list[str] = []

    if (
        metrics.owner_execution_modules_per_surface
        < guard.baseline_owner_execution_modules_per_surface
    ):
        failures.append(
            "runtime breadth now outpaces owned execution logic per governed surface"
        )
    if metrics.total_breadth_count > guard.baseline_total_breadth_count:
        if (
            metrics.owner_execution_module_count
            <= guard.baseline_owner_execution_module_count
        ):
            failures.append(
                "runtime breadth grew without adding owned execution modules"
            )
    if metrics.first_level_subtree_count > guard.baseline_first_level_subtree_count:
        if (
            metrics.owner_execution_modules_per_surface
            <= guard.baseline_owner_execution_modules_per_surface
        ):
            failures.append(
                "runtime topology widened without stronger owned execution density"
            )
    return tuple(failures)


def _toml_text(report: RuntimeBreadthReport) -> str:
    metrics = report.metrics
    guard = report.guard
    return "\n".join(
        (
            "# Generated runtime breadth-versus-owned-logic report.",
            "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.runtime_breadth",
            "",
            "[metrics]",
            f"public_entrypoint_count = {metrics.public_entrypoint_count}",
            f"extension_point_count = {metrics.extension_point_count}",
            f"config_knob_count = {metrics.config_knob_count}",
            f"first_level_subtree_count = {metrics.first_level_subtree_count}",
            f"total_breadth_count = {metrics.total_breadth_count}",
            f"owner_execution_module_count = {metrics.owner_execution_module_count}",
            f"thin_module_count = {metrics.thin_module_count}",
            (
                "owner_execution_modules_per_surface = "
                f"{metrics.owner_execution_modules_per_surface}"
            ),
            "",
            "[guard]",
            f"baseline_total_breadth_count = {guard.baseline_total_breadth_count}",
            (
                "baseline_first_level_subtree_count = "
                f"{guard.baseline_first_level_subtree_count}"
            ),
            (
                "baseline_owner_execution_module_count = "
                f"{guard.baseline_owner_execution_module_count}"
            ),
            (
                "baseline_owner_execution_modules_per_surface = "
                f"{guard.baseline_owner_execution_modules_per_surface}"
            ),
        )
    )


def _is_up_to_date(report: RuntimeBreadthReport) -> bool:
    if not RUNTIME_BREADTH_PATH.exists():
        return False
    return RUNTIME_BREADTH_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_runtime_breadth_report()
    failures = validate_runtime_breadth()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("runtime breadth report is up to date")
            return 0
        print("runtime breadth report is stale; regenerate it")
        return 1
    RUNTIME_BREADTH_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated runtime breadth report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the runtime breadth report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the runtime breadth report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
