from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.package_shape.package_fixture_realism import (
    REALISTIC_FIXTURE_SIZE_LIMIT,
    SERIOUS_PRODUCT_AREAS,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    fixture_files,
    workspace_package_names,
)

__all__ = [
    "PACKAGE_FIXTURE_SCENARIO_COVERAGE_PATH",
    "PackageFixtureScenarioCoverageEntry",
    "PackageFixtureScenarioCoverageGuard",
    "PackageFixtureScenarioCoverageReport",
    "build_package_fixture_scenario_coverage_report",
    "run",
    "validate_package_fixture_scenario_coverage",
]


PACKAGE_FIXTURE_SCENARIO_COVERAGE_PATH = (
    REPO_ROOT
    / "configs"
    / "package-governance"
    / "package-fixture-scenario-coverage.toml"
)
NEGATIVE_FIXTURE_TOKENS = (
    "refusal",
    "refused",
    "failure",
    "invalid",
    "missing",
    "weak",
    "trap",
    "blocked",
)
AMBIGUITY_FIXTURE_TOKENS = ("ambiguity", "ambiguous")
CONTRADICTION_FIXTURE_TOKENS = ("contradiction", "conflict")
DEGRADED_PROVENANCE_FIXTURE_TOKENS = (
    "provenance",
    "lineage",
    "aging",
    "stale",
)
BENCHMARK_FIXTURE_TOKENS = ("benchmark", "performance", "scale_medium")


@dataclass(frozen=True)
class PackageFixtureScenarioCoverageEntry:
    """Scenario-bearing fixture coverage metrics for one package."""

    distribution_name: str
    serious_product_area: bool
    fixture_file_count: int
    medium_realistic_fixture_count_ge_1024: int
    negative_fixture_count: int
    ambiguity_fixture_count: int
    contradiction_fixture_count: int
    degraded_provenance_fixture_count: int
    benchmark_fixture_count: int


@dataclass(frozen=True)
class PackageFixtureScenarioCoverageGuard:
    """Release-blocking guardrails over serious fixture scenario coverage."""

    min_total_medium_realistic_fixture_count: int
    min_total_negative_fixture_count: int
    min_total_ambiguity_fixture_count: int
    min_total_contradiction_fixture_count: int
    min_total_degraded_provenance_fixture_count: int
    min_total_benchmark_fixture_count: int
    min_serious_package_with_medium_fixture_count: int


@dataclass(frozen=True)
class PackageFixtureScenarioCoverageReport:
    """Checked fixture scenario coverage report across repository packages."""

    entries: tuple[PackageFixtureScenarioCoverageEntry, ...]
    guard: PackageFixtureScenarioCoverageGuard


def _count_matching_tokens(
    package_name: str,
    tokens: tuple[str, ...],
) -> int:
    return sum(
        any(token in path.as_posix().lower() for token in tokens)
        for path in fixture_files(package_name)
    )


def build_package_fixture_scenario_coverage_report() -> (
    PackageFixtureScenarioCoverageReport
):
    """Build the checked fixture scenario coverage report."""

    entries: list[PackageFixtureScenarioCoverageEntry] = []
    for package_name in workspace_package_names():
        files = fixture_files(package_name)
        entries.append(
            PackageFixtureScenarioCoverageEntry(
                distribution_name=package_name,
                serious_product_area=package_name in SERIOUS_PRODUCT_AREAS,
                fixture_file_count=len(files),
                medium_realistic_fixture_count_ge_1024=sum(
                    path.stat().st_size >= REALISTIC_FIXTURE_SIZE_LIMIT
                    for path in files
                ),
                negative_fixture_count=_count_matching_tokens(
                    package_name,
                    NEGATIVE_FIXTURE_TOKENS,
                ),
                ambiguity_fixture_count=_count_matching_tokens(
                    package_name,
                    AMBIGUITY_FIXTURE_TOKENS,
                ),
                contradiction_fixture_count=_count_matching_tokens(
                    package_name,
                    CONTRADICTION_FIXTURE_TOKENS,
                ),
                degraded_provenance_fixture_count=_count_matching_tokens(
                    package_name,
                    DEGRADED_PROVENANCE_FIXTURE_TOKENS,
                ),
                benchmark_fixture_count=_count_matching_tokens(
                    package_name,
                    BENCHMARK_FIXTURE_TOKENS,
                ),
            )
        )
    serious_entries = tuple(
        entry
        for entry in entries
        if entry.serious_product_area and entry.fixture_file_count > 0
    )
    return PackageFixtureScenarioCoverageReport(
        entries=tuple(entries),
        guard=PackageFixtureScenarioCoverageGuard(
            min_total_medium_realistic_fixture_count=sum(
                entry.medium_realistic_fixture_count_ge_1024
                for entry in serious_entries
            ),
            min_total_negative_fixture_count=sum(
                entry.negative_fixture_count for entry in serious_entries
            ),
            min_total_ambiguity_fixture_count=sum(
                entry.ambiguity_fixture_count for entry in serious_entries
            ),
            min_total_contradiction_fixture_count=sum(
                entry.contradiction_fixture_count for entry in serious_entries
            ),
            min_total_degraded_provenance_fixture_count=sum(
                entry.degraded_provenance_fixture_count for entry in serious_entries
            ),
            min_total_benchmark_fixture_count=sum(
                entry.benchmark_fixture_count for entry in serious_entries
            ),
            min_serious_package_with_medium_fixture_count=sum(
                entry.medium_realistic_fixture_count_ge_1024 > 0
                for entry in serious_entries
            ),
        ),
    )


def validate_package_fixture_scenario_coverage(
    report: PackageFixtureScenarioCoverageReport | None = None,
) -> tuple[str, ...]:
    """Fail release when serious scenario-bearing fixture coverage gets weaker."""

    report = report or build_package_fixture_scenario_coverage_report()
    serious_entries = tuple(
        entry
        for entry in report.entries
        if entry.serious_product_area and entry.fixture_file_count > 0
    )
    failures: list[str] = []
    medium_realistic_fixture_count = sum(
        entry.medium_realistic_fixture_count_ge_1024 for entry in serious_entries
    )
    negative_fixture_count = sum(
        entry.negative_fixture_count for entry in serious_entries
    )
    ambiguity_fixture_count = sum(
        entry.ambiguity_fixture_count for entry in serious_entries
    )
    contradiction_fixture_count = sum(
        entry.contradiction_fixture_count for entry in serious_entries
    )
    degraded_provenance_fixture_count = sum(
        entry.degraded_provenance_fixture_count for entry in serious_entries
    )
    benchmark_fixture_count = sum(
        entry.benchmark_fixture_count for entry in serious_entries
    )
    serious_package_with_medium_fixture_count = sum(
        entry.medium_realistic_fixture_count_ge_1024 > 0 for entry in serious_entries
    )
    if (
        medium_realistic_fixture_count
        < report.guard.min_total_medium_realistic_fixture_count
    ):
        failures.append(
            "medium realistic fixture coverage dropped below the governed serious-package baseline"
        )
    if negative_fixture_count < report.guard.min_total_negative_fixture_count:
        failures.append(
            "negative fixture coverage dropped below the governed serious-package baseline"
        )
    if ambiguity_fixture_count < report.guard.min_total_ambiguity_fixture_count:
        failures.append(
            "ambiguity fixture coverage dropped below the governed serious-package baseline"
        )
    if contradiction_fixture_count < report.guard.min_total_contradiction_fixture_count:
        failures.append(
            "contradiction fixture coverage dropped below the governed serious-package baseline"
        )
    if (
        degraded_provenance_fixture_count
        < report.guard.min_total_degraded_provenance_fixture_count
    ):
        failures.append(
            "degraded provenance fixture coverage dropped below the governed serious-package baseline"
        )
    if benchmark_fixture_count < report.guard.min_total_benchmark_fixture_count:
        failures.append(
            "benchmark fixture coverage dropped below the governed serious-package baseline"
        )
    if (
        serious_package_with_medium_fixture_count
        < report.guard.min_serious_package_with_medium_fixture_count
    ):
        failures.append(
            "serious-package medium fixture coverage dropped below the governed baseline"
        )
    return tuple(failures)


def _toml_text(report: PackageFixtureScenarioCoverageReport) -> str:
    lines = [
        "# Generated package fixture scenario coverage report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_fixture_scenario_coverage",
        "",
        "[guard]",
        (
            "min_total_medium_realistic_fixture_count = "
            f"{report.guard.min_total_medium_realistic_fixture_count}"
        ),
        f"min_total_negative_fixture_count = {report.guard.min_total_negative_fixture_count}",
        f"min_total_ambiguity_fixture_count = {report.guard.min_total_ambiguity_fixture_count}",
        (
            "min_total_contradiction_fixture_count = "
            f"{report.guard.min_total_contradiction_fixture_count}"
        ),
        (
            "min_total_degraded_provenance_fixture_count = "
            f"{report.guard.min_total_degraded_provenance_fixture_count}"
        ),
        f"min_total_benchmark_fixture_count = {report.guard.min_total_benchmark_fixture_count}",
        (
            "min_serious_package_with_medium_fixture_count = "
            f"{report.guard.min_serious_package_with_medium_fixture_count}"
        ),
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"serious_product_area = {str(entry.serious_product_area).lower()}",
                f"fixture_file_count = {entry.fixture_file_count}",
                (
                    "medium_realistic_fixture_count_ge_1024 = "
                    f"{entry.medium_realistic_fixture_count_ge_1024}"
                ),
                f"negative_fixture_count = {entry.negative_fixture_count}",
                f"ambiguity_fixture_count = {entry.ambiguity_fixture_count}",
                f"contradiction_fixture_count = {entry.contradiction_fixture_count}",
                (
                    "degraded_provenance_fixture_count = "
                    f"{entry.degraded_provenance_fixture_count}"
                ),
                f"benchmark_fixture_count = {entry.benchmark_fixture_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageFixtureScenarioCoverageReport) -> bool:
    if not PACKAGE_FIXTURE_SCENARIO_COVERAGE_PATH.exists():
        return False
    return PACKAGE_FIXTURE_SCENARIO_COVERAGE_PATH.read_text(
        encoding="utf-8"
    ) == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_fixture_scenario_coverage_report()
    failures = validate_package_fixture_scenario_coverage(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package fixture scenario coverage report is up to date")
            return 0
        print("package fixture scenario coverage report is stale; regenerate it")
        return 1
    PACKAGE_FIXTURE_SCENARIO_COVERAGE_PATH.write_text(
        _toml_text(report),
        encoding="utf-8",
    )
    print("generated package fixture scenario coverage report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package fixture scenario coverage report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package fixture scenario coverage report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
