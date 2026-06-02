from __future__ import annotations

import argparse
from dataclasses import dataclass
import re

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    fixture_files,
    workspace_package_names,
)

__all__ = [
    "REALISTIC_FIXTURE_SIZE_LIMIT",
    "TOY_FIXTURE_NAME_TOKENS",
    "SERIOUS_PRODUCT_AREAS",
    "PACKAGE_FIXTURE_REALISM_PATH",
    "PackageFixtureRealismEntry",
    "PackageFixtureRealismGuard",
    "PackageFixtureRealismReport",
    "build_package_fixture_realism_report",
    "run",
    "validate_package_fixture_realism",
]


REALISTIC_FIXTURE_SIZE_LIMIT = 1024
TOY_FIXTURE_NAME_TOKENS = ("toy", "tiny", "minimal", "sample")
SERIOUS_PRODUCT_AREAS = frozenset(
    {
        "bijux-proteomics-core",
        "bijux-proteomics-intelligence",
        "bijux-proteomics-knowledge",
        "bijux-proteomics-lab",
        "bijux-proteomics-runtime",
    }
)
PACKAGE_FIXTURE_REALISM_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-fixture-realism.toml"
)


def _fixture_name_tokens(name: str) -> tuple[str, ...]:
    return tuple(
        token for token in re.split(r"[^a-z0-9]+", name.lower()) if token
    )


@dataclass(frozen=True)
class PackageFixtureRealismEntry:
    """Fixture realism metrics for one package."""

    distribution_name: str
    serious_product_area: bool
    fixture_file_count: int
    small_fixture_count_lt_512: int
    realistic_fixture_count_ge_1024: int
    toy_named_fixture_count: int


@dataclass(frozen=True)
class PackageFixtureRealismGuard:
    """Release-blocking realism baselines over serious fixture sets."""

    max_total_toy_named_fixture_count: int
    min_total_realistic_fixture_count: int
    min_serious_package_with_realistic_fixtures_count: int


@dataclass(frozen=True)
class PackageFixtureRealismReport:
    """Checked fixture realism report across repository packages."""

    entries: tuple[PackageFixtureRealismEntry, ...]
    guard: PackageFixtureRealismGuard


def build_package_fixture_realism_report() -> PackageFixtureRealismReport:
    """Build the checked fixture realism report."""

    entries: list[PackageFixtureRealismEntry] = []
    for package_name in workspace_package_names():
        files = fixture_files(package_name)
        entries.append(
            PackageFixtureRealismEntry(
                distribution_name=package_name,
                serious_product_area=package_name in SERIOUS_PRODUCT_AREAS,
                fixture_file_count=len(files),
                small_fixture_count_lt_512=sum(
                    path.stat().st_size < 512 for path in files
                ),
                realistic_fixture_count_ge_1024=sum(
                    path.stat().st_size >= REALISTIC_FIXTURE_SIZE_LIMIT
                    for path in files
                ),
                toy_named_fixture_count=sum(
                    bool(
                        set(_fixture_name_tokens(path.name))
                        & set(TOY_FIXTURE_NAME_TOKENS)
                    )
                    for path in files
                ),
            )
        )
    serious_entries = tuple(
        entry
        for entry in entries
        if entry.serious_product_area and entry.fixture_file_count > 0
    )
    return PackageFixtureRealismReport(
        entries=tuple(entries),
        guard=PackageFixtureRealismGuard(
            max_total_toy_named_fixture_count=sum(
                entry.toy_named_fixture_count for entry in serious_entries
            ),
            min_total_realistic_fixture_count=sum(
                entry.realistic_fixture_count_ge_1024 for entry in serious_entries
            ),
            min_serious_package_with_realistic_fixtures_count=sum(
                entry.realistic_fixture_count_ge_1024 > 0 for entry in serious_entries
            ),
        ),
    )


def validate_package_fixture_realism(
    report: PackageFixtureRealismReport | None = None,
) -> tuple[str, ...]:
    """Fail release when serious fixture realism gets worse."""

    report = report or build_package_fixture_realism_report()
    serious_entries = tuple(
        entry
        for entry in report.entries
        if entry.serious_product_area and entry.fixture_file_count > 0
    )
    total_toy_named_fixture_count = sum(
        entry.toy_named_fixture_count for entry in serious_entries
    )
    total_realistic_fixture_count = sum(
        entry.realistic_fixture_count_ge_1024 for entry in serious_entries
    )
    serious_package_with_realistic_fixtures_count = sum(
        entry.realistic_fixture_count_ge_1024 > 0 for entry in serious_entries
    )
    failures: list[str] = []
    if total_toy_named_fixture_count > report.guard.max_total_toy_named_fixture_count:
        failures.append(
            "toy-named fixtures grew beyond the governed serious-fixture baseline"
        )
    if total_realistic_fixture_count < report.guard.min_total_realistic_fixture_count:
        failures.append(
            "realistic fixture coverage dropped below the governed serious-fixture baseline"
        )
    if (
        serious_package_with_realistic_fixtures_count
        < report.guard.min_serious_package_with_realistic_fixtures_count
    ):
        failures.append(
            "serious fixture realism dropped below the governed package coverage baseline"
        )
    return tuple(failures)


def _toml_text(report: PackageFixtureRealismReport) -> str:
    lines = [
        "# Generated package fixture realism report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_fixture_realism",
        "",
        "[guard]",
        f"max_total_toy_named_fixture_count = {report.guard.max_total_toy_named_fixture_count}",
        f"min_total_realistic_fixture_count = {report.guard.min_total_realistic_fixture_count}",
        "min_serious_package_with_realistic_fixtures_count = "
        f"{report.guard.min_serious_package_with_realistic_fixtures_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"serious_product_area = {str(entry.serious_product_area).lower()}",
                f"fixture_file_count = {entry.fixture_file_count}",
                f"small_fixture_count_lt_512 = {entry.small_fixture_count_lt_512}",
                "realistic_fixture_count_ge_1024 = "
                f"{entry.realistic_fixture_count_ge_1024}",
                f"toy_named_fixture_count = {entry.toy_named_fixture_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageFixtureRealismReport) -> bool:
    if not PACKAGE_FIXTURE_REALISM_PATH.exists():
        return False
    return PACKAGE_FIXTURE_REALISM_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_fixture_realism_report()
    failures = validate_package_fixture_realism(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package fixture realism report is up to date")
            return 0
        print("package fixture realism report is stale; regenerate it")
        return 1
    PACKAGE_FIXTURE_REALISM_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package fixture realism report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package fixture realism report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package fixture realism report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
