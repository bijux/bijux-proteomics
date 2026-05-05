from __future__ import annotations

import argparse
from dataclasses import dataclass

import bijux_proteomics_lab

from bijux_proteomics_dev.api.foundation_root_consumers import REPO_ROOT
from bijux_proteomics_dev.api.lab_analytical_logic import validate_lab_analytical_logic
from bijux_proteomics_dev.api.lab_core_scientific_semantics import (
    LAB_CORE_SCIENTIFIC_SEMANTICS_PATH,
    validate_lab_core_scientific_semantics,
)
from bijux_proteomics_dev.api.lab_cross_package_dependencies import (
    LAB_CROSS_PACKAGE_DEPENDENCIES_PATH,
    validate_lab_cross_package_dependencies,
)
from bijux_proteomics_dev.api.lab_operational_ownership import (
    LAB_OPERATIONAL_OWNERSHIP_PATH,
    build_lab_operational_ownership_report,
    validate_lab_operational_ownership,
)
from bijux_proteomics_dev.api.lab_packet_only_modules import (
    LAB_PACKET_ONLY_MODULES_PATH,
    validate_lab_module_shapes,
)
from bijux_proteomics_dev.api.lab_root_imports import (
    LAB_ROOT_IMPORTS_PATH,
    validate_lab_root_imports,
)
from bijux_proteomics_dev.api.lab_runtime_boundary_drift import (
    LAB_RUNTIME_BOUNDARY_DRIFT_PATH,
    validate_lab_runtime_boundary_drift,
)

__all__ = [
    "LAB_PUBLISHABILITY_PATH",
    "LabPublishabilityGuard",
    "LabPublishabilityReport",
    "build_lab_publishability_report",
    "run",
    "validate_lab_publishability",
]


LAB_PUBLISHABILITY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "lab-publishability.toml"
)
LAB_ROOT_API_POLICY = REPO_ROOT / "configs" / "package-governance" / "lab-root-api.toml"
LAB_DOC_PATHS = (
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "README.md",
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "docs" / "ARCHITECTURE.md",
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "docs" / "BOUNDARIES.md",
    REPO_ROOT / "packages" / "bijux-proteomics-lab" / "docs" / "CONTRACTS.md",
)


@dataclass(frozen=True)
class LabPublishabilityGuard:
    """Release thresholds for a publishable lab package."""

    max_root_entrypoint_count: int
    min_source_owner_family_count: int
    min_test_family_count: int
    min_mirrored_owner_family_count: int
    max_flat_test_module_count: int


@dataclass(frozen=True)
class LabPublishabilityReport:
    """One checked publishability decision for lab."""

    root_entrypoint_count: int
    source_owner_family_count: int
    test_family_count: int
    mirrored_owner_family_count: int
    flat_test_module_count: int
    honesty_ready: bool
    feasibility_ready: bool
    traceability_ready: bool
    ownership_ready: bool
    boundary_ready: bool
    guard: LabPublishabilityGuard

    @property
    def operations_reviewer_ready(self) -> bool:
        return (
            self.honesty_ready
            and self.feasibility_ready
            and self.traceability_ready
            and self.ownership_ready
            and self.boundary_ready
        )

    @property
    def publishable(self) -> bool:
        return not validate_lab_publishability(self)


def _combined_docs() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in LAB_DOC_PATHS).lower()


def build_lab_publishability_report() -> LabPublishabilityReport:
    """Build the checked publishability report for lab."""

    ownership_report = build_lab_operational_ownership_report()
    docs_text = _combined_docs()
    honesty_ready = (
        "handoff honesty" in docs_text
        and "refusal behavior" in docs_text
        and "lossy export notes" in docs_text
    )
    feasibility_ready = "queue pressure" in docs_text and "material limits" in docs_text
    traceability_ready = (
        "traceability" in docs_text and "requested work" in docs_text and "observed work" in docs_text
    )
    boundary_ready = not any(
        (
            validate_lab_analytical_logic(),
            validate_lab_core_scientific_semantics(),
            validate_lab_runtime_boundary_drift(),
            validate_lab_cross_package_dependencies(),
            validate_lab_module_shapes(),
            validate_lab_root_imports(),
        )
    )
    metrics = ownership_report.metrics
    return LabPublishabilityReport(
        root_entrypoint_count=len(tuple(bijux_proteomics_lab.__all__)),
        source_owner_family_count=len(metrics.source_owner_families),
        test_family_count=len(metrics.test_families),
        mirrored_owner_family_count=metrics.mirrored_owner_family_count,
        flat_test_module_count=metrics.flat_test_module_count,
        honesty_ready=honesty_ready,
        feasibility_ready=feasibility_ready,
        traceability_ready=traceability_ready,
        ownership_ready=ownership_report.ownership_ready,
        boundary_ready=boundary_ready,
        guard=LabPublishabilityGuard(
            max_root_entrypoint_count=len(tuple(bijux_proteomics_lab.__all__)),
            min_source_owner_family_count=len(metrics.source_owner_families),
            min_test_family_count=len(metrics.test_families),
            min_mirrored_owner_family_count=metrics.mirrored_owner_family_count,
            max_flat_test_module_count=0,
        ),
    )


def validate_lab_publishability(
    report: LabPublishabilityReport | None = None,
) -> tuple[str, ...]:
    """Fail release when lab stops looking like a trustworthy operational product."""

    report = report or build_lab_publishability_report()
    failures: list[str] = []
    if report.root_entrypoint_count > report.guard.max_root_entrypoint_count:
        failures.append("lab publishability disallows widening the curated root entrypoint set")
    if report.source_owner_family_count < report.guard.min_source_owner_family_count:
        failures.append("lab publishability requires the full governed owner family map")
    if report.test_family_count < report.guard.min_test_family_count:
        failures.append("lab publishability requires the full governed test family map")
    if (
        report.mirrored_owner_family_count
        < report.guard.min_mirrored_owner_family_count
    ):
        failures.append("lab publishability requires every operational owner family to be mirrored in tests")
    if report.flat_test_module_count > report.guard.max_flat_test_module_count:
        failures.append("lab publishability requires zero flat root test modules")
    if not report.honesty_ready:
        failures.append("lab publishability requires docs that keep handoff honesty and refusal behavior explicit")
    if not report.feasibility_ready:
        failures.append("lab publishability requires docs that keep queue pressure and material limits explicit")
    if not report.traceability_ready:
        failures.append("lab publishability requires docs that keep requested-versus-observed traceability explicit")
    if not report.ownership_ready:
        failures.append("lab publishability requires a clean operational ownership report")
    if not report.boundary_ready:
        failures.append("lab publishability requires clean analytical, scientific, runtime, root-import, dependency, and shape guards")
    for failure in validate_lab_operational_ownership():
        failures.append(f"ownership: {failure}")
    return tuple(failures)


def _toml_text(report: LabPublishabilityReport) -> str:
    guard = report.guard
    return "\n".join(
        (
            "# Generated lab publishability report.",
            "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.lab_publishability",
            "",
            "[metrics]",
            f"root_entrypoint_count = {report.root_entrypoint_count}",
            f"source_owner_family_count = {report.source_owner_family_count}",
            f"test_family_count = {report.test_family_count}",
            f"mirrored_owner_family_count = {report.mirrored_owner_family_count}",
            f"flat_test_module_count = {report.flat_test_module_count}",
            f"honesty_ready = {str(report.honesty_ready).lower()}",
            f"feasibility_ready = {str(report.feasibility_ready).lower()}",
            f"traceability_ready = {str(report.traceability_ready).lower()}",
            f"ownership_ready = {str(report.ownership_ready).lower()}",
            f"boundary_ready = {str(report.boundary_ready).lower()}",
            (
                "operations_reviewer_ready = "
                f"{str(report.operations_reviewer_ready).lower()}"
            ),
            f"publishable = {str(report.publishable).lower()}",
            "",
            "[guard]",
            f"max_root_entrypoint_count = {guard.max_root_entrypoint_count}",
            f"min_source_owner_family_count = {guard.min_source_owner_family_count}",
            f"min_test_family_count = {guard.min_test_family_count}",
            (
                "min_mirrored_owner_family_count = "
                f"{guard.min_mirrored_owner_family_count}"
            ),
            f"max_flat_test_module_count = {guard.max_flat_test_module_count}",
            "",
            "[evidence]",
            f'lab_operational_ownership_path = "{LAB_OPERATIONAL_OWNERSHIP_PATH.relative_to(REPO_ROOT).as_posix()}"',
            f'lab_packet_only_modules_path = "{LAB_PACKET_ONLY_MODULES_PATH.relative_to(REPO_ROOT).as_posix()}"',
            f'lab_cross_package_dependencies_path = "{LAB_CROSS_PACKAGE_DEPENDENCIES_PATH.relative_to(REPO_ROOT).as_posix()}"',
            f'lab_root_imports_path = "{LAB_ROOT_IMPORTS_PATH.relative_to(REPO_ROOT).as_posix()}"',
            f'lab_root_api_policy_path = "{LAB_ROOT_API_POLICY.relative_to(REPO_ROOT).as_posix()}"',
            f'lab_core_scientific_semantics_path = "{LAB_CORE_SCIENTIFIC_SEMANTICS_PATH.relative_to(REPO_ROOT).as_posix()}"',
            f'lab_runtime_boundary_drift_path = "{LAB_RUNTIME_BOUNDARY_DRIFT_PATH.relative_to(REPO_ROOT).as_posix()}"',
        )
    )


def _is_up_to_date(report: LabPublishabilityReport) -> bool:
    if not LAB_PUBLISHABILITY_PATH.exists():
        return False
    return LAB_PUBLISHABILITY_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_lab_publishability_report()
    failures = validate_lab_publishability(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("lab publishability report is up to date")
            return 0
        print("lab publishability report is stale; regenerate it")
        return 1
    LAB_PUBLISHABILITY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated lab publishability report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the lab publishability report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the lab publishability report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
