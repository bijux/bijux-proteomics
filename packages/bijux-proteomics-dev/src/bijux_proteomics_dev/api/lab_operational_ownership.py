from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.api.runtime_topology import REPO_ROOT
from bijux_proteomics_lab.governance.charter import (
    DEFAULT_LAB_MODULE_AUDIT,
    LabModuleClassification,
)

__all__ = [
    "LAB_OPERATIONAL_OWNERSHIP_PATH",
    "LabOperationalOwnershipGuard",
    "LabOperationalOwnershipMetrics",
    "LabOperationalOwnershipReport",
    "build_lab_operational_ownership_report",
    "run",
    "validate_lab_operational_ownership",
]


LAB_SRC_ROOT = (
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "src" / "bijux_proteomics_lab"
)
LAB_TEST_ROOT = REPO_ROOT / "packages" / "bijux-proteomics-lab" / "tests"
LAB_OPERATIONAL_OWNERSHIP_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "lab-operational-ownership.toml"
)
REQUIRED_SOURCE_OWNER_FAMILIES = tuple(
    sorted(
        (
            "benchmarks",
            "design",
            "handoffs",
            "lifecycle",
            "outcomes",
            "planning",
            "readiness",
            "reconciliation",
        )
    )
)
REQUIRED_TEST_FAMILIES = tuple(
    sorted(REQUIRED_SOURCE_OWNER_FAMILIES + ("boundaries", "package"))
)


@dataclass(frozen=True)
class LabOperationalOwnershipMetrics:
    """Current source and test tree evidence for deep lab operational ownership."""

    source_owner_families: tuple[str, ...]
    test_families: tuple[str, ...]
    flat_test_module_count: int
    mirrored_owner_family_count: int
    operational_value_module_count: int
    thin_abstraction_module_count: int
    unresolved_reasons: tuple[str, ...]


@dataclass(frozen=True)
class LabOperationalOwnershipGuard:
    """Release-blocking thresholds for a deep operational lab tree."""

    required_source_owner_family_count: int
    required_test_family_count: int
    required_mirrored_owner_family_count: int
    max_flat_test_module_count: int
    min_operational_value_module_count: int
    max_thin_abstraction_module_count: int


@dataclass(frozen=True)
class LabOperationalOwnershipReport:
    """Checked report over whether the lab tree shows real operational ownership."""

    metrics: LabOperationalOwnershipMetrics
    guard: LabOperationalOwnershipGuard

    @property
    def ownership_ready(self) -> bool:
        return not self.metrics.unresolved_reasons


def build_lab_operational_ownership_report() -> LabOperationalOwnershipReport:
    """Build the checked report over the lab source and test tree shape."""

    source_owner_families = tuple(
        sorted(
            path.name
            for path in LAB_SRC_ROOT.iterdir()
            if path.is_dir() and path.name != "__pycache__"
        )
    )
    test_families = tuple(
        sorted(
            path.name
            for path in LAB_TEST_ROOT.iterdir()
            if path.is_dir() and path.name not in {"__pycache__", "fixtures"}
        )
    )
    flat_test_module_count = len(tuple(LAB_TEST_ROOT.glob("test_*.py")))
    mirrored_owner_family_count = sum(
        1 for family in source_owner_families if family in set(test_families)
    )
    operational_value_module_count = sum(
        1
        for entry in DEFAULT_LAB_MODULE_AUDIT
        if entry.classification is LabModuleClassification.OPERATIONAL_VALUE
    )
    thin_abstraction_module_count = sum(
        1
        for entry in DEFAULT_LAB_MODULE_AUDIT
        if entry.classification is LabModuleClassification.THIN_ABSTRACTION
    )

    unresolved_reasons: list[str] = []
    if source_owner_families != REQUIRED_SOURCE_OWNER_FAMILIES:
        unresolved_reasons.append("source owner families drifted from the governed operational map")
    if test_families != REQUIRED_TEST_FAMILIES:
        unresolved_reasons.append("test families drifted from the governed operational mirror")
    if flat_test_module_count != 0:
        unresolved_reasons.append("flat root test modules remain under tests/")
    if mirrored_owner_family_count != len(REQUIRED_SOURCE_OWNER_FAMILIES):
        unresolved_reasons.append("not every operational source family is mirrored in tests/")
    if operational_value_module_count <= thin_abstraction_module_count:
        unresolved_reasons.append("operational value modules no longer dominate compatibility facades")

    metrics = LabOperationalOwnershipMetrics(
        source_owner_families=source_owner_families,
        test_families=test_families,
        flat_test_module_count=flat_test_module_count,
        mirrored_owner_family_count=mirrored_owner_family_count,
        operational_value_module_count=operational_value_module_count,
        thin_abstraction_module_count=thin_abstraction_module_count,
        unresolved_reasons=tuple(unresolved_reasons),
    )
    return LabOperationalOwnershipReport(
        metrics=metrics,
        guard=LabOperationalOwnershipGuard(
            required_source_owner_family_count=len(REQUIRED_SOURCE_OWNER_FAMILIES),
            required_test_family_count=len(REQUIRED_TEST_FAMILIES),
            required_mirrored_owner_family_count=len(REQUIRED_SOURCE_OWNER_FAMILIES),
            max_flat_test_module_count=0,
            min_operational_value_module_count=operational_value_module_count,
            max_thin_abstraction_module_count=thin_abstraction_module_count,
        ),
    )


def validate_lab_operational_ownership(
    report: LabOperationalOwnershipReport | None = None,
) -> tuple[str, ...]:
    """Fail release when the lab tree stops showing deep operational ownership."""

    report = report or build_lab_operational_ownership_report()
    failures = list(report.metrics.unresolved_reasons)
    if (
        report.metrics.operational_value_module_count
        < report.guard.min_operational_value_module_count
    ):
        failures.append("lab operational value module count shrank below the governed baseline")
    if (
        report.metrics.thin_abstraction_module_count
        > report.guard.max_thin_abstraction_module_count
    ):
        failures.append("lab thin abstraction count grew beyond the governed baseline")
    return tuple(failures)


def _toml_text(report: LabOperationalOwnershipReport) -> str:
    metrics = report.metrics
    guard = report.guard
    source_owner_families = ", ".join(f'"{value}"' for value in metrics.source_owner_families)
    test_families = ", ".join(f'"{value}"' for value in metrics.test_families)
    unresolved_reasons = ", ".join(f'"{value}"' for value in metrics.unresolved_reasons)
    return "\n".join(
        (
            "# Generated lab operational ownership report.",
            "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.lab_operational_ownership",
            "",
            "[metrics]",
            f"source_owner_families = [{source_owner_families}]",
            f"test_families = [{test_families}]",
            f"flat_test_module_count = {metrics.flat_test_module_count}",
            f"mirrored_owner_family_count = {metrics.mirrored_owner_family_count}",
            f"operational_value_module_count = {metrics.operational_value_module_count}",
            f"thin_abstraction_module_count = {metrics.thin_abstraction_module_count}",
            f"ownership_ready = {str(report.ownership_ready).lower()}",
            f"unresolved_reasons = [{unresolved_reasons}]",
            "",
            "[guard]",
            (
                "required_source_owner_family_count = "
                f"{guard.required_source_owner_family_count}"
            ),
            f"required_test_family_count = {guard.required_test_family_count}",
            (
                "required_mirrored_owner_family_count = "
                f"{guard.required_mirrored_owner_family_count}"
            ),
            f"max_flat_test_module_count = {guard.max_flat_test_module_count}",
            f"min_operational_value_module_count = {guard.min_operational_value_module_count}",
            f"max_thin_abstraction_module_count = {guard.max_thin_abstraction_module_count}",
        )
    )


def _is_up_to_date(report: LabOperationalOwnershipReport) -> bool:
    if not LAB_OPERATIONAL_OWNERSHIP_PATH.exists():
        return False
    return LAB_OPERATIONAL_OWNERSHIP_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_lab_operational_ownership_report()
    failures = validate_lab_operational_ownership(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("lab operational ownership report is up to date")
            return 0
        print("lab operational ownership report is stale; regenerate it")
        return 1
    LAB_OPERATIONAL_OWNERSHIP_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated lab operational ownership report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the lab operational ownership report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the lab operational ownership report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
