from __future__ import annotations

import argparse
from dataclasses import dataclass
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_SCORECARD_PATH",
    "PackageScorecardEntry",
    "PackageScorecardGuard",
    "PackageScorecardReport",
    "build_package_scorecard_report",
    "run",
    "validate_package_scorecard",
]


PACKAGE_SCORECARD_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-scorecard.toml"
)


@dataclass(frozen=True)
class PackageScorecardEntry:
    """One package scorecard across owned logic, surface breadth, and proof."""

    distribution_name: str
    owner_logic_module_count: int
    public_breadth_count: int
    wrapper_module_count: int
    missing_test_family_count: int
    flat_test_module_count: int
    proof_depth_count: int
    unresolved_debt_count: int
    architectural_ready: bool


@dataclass(frozen=True)
class PackageScorecardGuard:
    """Release-blocking baseline for architectural scorecards."""

    min_architectural_ready_package_count: int
    max_total_unresolved_debt_count: int


@dataclass(frozen=True)
class PackageScorecardReport:
    """Checked package scorecard across the workspace."""

    entries: tuple[PackageScorecardEntry, ...]
    guard: PackageScorecardGuard


def _load_report(name: str) -> dict[str, Any]:
    with (REPO_ROOT / "configs" / "package-governance" / name).open("rb") as handle:
        return tomllib.load(handle)


def _rows(name: str, key: str = "package") -> tuple[dict[str, Any], ...]:
    rows = _load_report(name)[key]
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise TypeError(f"{name}:{key} must be a list of TOML tables")
    return tuple(cast(dict[str, Any], row) for row in rows)


def build_package_scorecard_report() -> PackageScorecardReport:
    """Build the checked package scorecard report."""

    surface_pressure = {
        entry["distribution_name"]: entry
        for entry in _rows("package-surface-pressure.toml")
    }
    wrapper_density = {
        entry["distribution_name"]: entry
        for entry in _rows("package-wrapper-density.toml")
    }
    test_tree = {
        entry["distribution_name"]: entry
        for entry in _rows("package-test-tree-mirror.toml")
    }
    docs_claims = {
        entry["distribution_name"]: entry
        for entry in _rows("package-docs-claim-proof.toml")
    }
    release_dossiers = {
        entry["distribution_name"]: entry
        for entry in _rows("package-release-dossiers.toml")
    }

    entries: list[PackageScorecardEntry] = []
    for package_name in sorted(surface_pressure):
        surface_entry = surface_pressure[package_name]
        wrapper_entry = wrapper_density[package_name]
        tree_entry = test_tree[package_name]
        docs_entry = docs_claims[package_name]
        dossier_entry = release_dossiers[package_name]
        proof_depth_count = (
            int(docs_entry["benchmark_proof_artifact_count"])
            + int(docs_entry["replay_proof_artifact_count"])
            + int(docs_entry["integrity_proof_artifact_count"])
        )
        unresolved_debt_count = len(dossier_entry["unresolved_debt_ids"])
        architectural_ready = (
            not surface_entry["breadth_outpaces_owner_logic"]
            and unresolved_debt_count == 0
            and int(tree_entry["flat_test_module_count"]) == 0
            and len(tree_entry["missing_test_families"]) == 0
            and len(docs_entry["unproven_claim_kinds"]) == 0
        )
        entries.append(
            PackageScorecardEntry(
                distribution_name=package_name,
                owner_logic_module_count=int(surface_entry["owner_logic_module_count"]),
                public_breadth_count=int(surface_entry["public_breadth_count"]),
                wrapper_module_count=int(wrapper_entry["wrapper_module_count"]),
                missing_test_family_count=len(tree_entry["missing_test_families"]),
                flat_test_module_count=int(tree_entry["flat_test_module_count"]),
                proof_depth_count=proof_depth_count,
                unresolved_debt_count=unresolved_debt_count,
                architectural_ready=architectural_ready,
            )
        )
    return PackageScorecardReport(
        entries=tuple(entries),
        guard=PackageScorecardGuard(
            min_architectural_ready_package_count=sum(
                entry.architectural_ready for entry in entries
            ),
            max_total_unresolved_debt_count=sum(
                entry.unresolved_debt_count for entry in entries
            ),
        ),
    )


def validate_package_scorecard(
    report: PackageScorecardReport | None = None,
) -> tuple[str, ...]:
    """Fail release when scorecard readiness drops further."""

    report = report or build_package_scorecard_report()
    architectural_ready_package_count = sum(
        entry.architectural_ready for entry in report.entries
    )
    total_unresolved_debt_count = sum(
        entry.unresolved_debt_count for entry in report.entries
    )
    failures: list[str] = []
    if (
        architectural_ready_package_count
        < report.guard.min_architectural_ready_package_count
    ):
        failures.append(
            "architectural-ready package count dropped below the governed baseline"
        )
    if total_unresolved_debt_count > report.guard.max_total_unresolved_debt_count:
        failures.append(
            "unresolved structural debt grew beyond the governed scorecard baseline"
        )
    return tuple(failures)


def _toml_text(report: PackageScorecardReport) -> str:
    lines = [
        "# Generated package scorecard.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_scorecard",
        "",
        "[guard]",
        (
            "min_architectural_ready_package_count = "
            f"{report.guard.min_architectural_ready_package_count}"
        ),
        f"max_total_unresolved_debt_count = {report.guard.max_total_unresolved_debt_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"owner_logic_module_count = {entry.owner_logic_module_count}",
                f"public_breadth_count = {entry.public_breadth_count}",
                f"wrapper_module_count = {entry.wrapper_module_count}",
                f"missing_test_family_count = {entry.missing_test_family_count}",
                f"flat_test_module_count = {entry.flat_test_module_count}",
                f"proof_depth_count = {entry.proof_depth_count}",
                f"unresolved_debt_count = {entry.unresolved_debt_count}",
                f"architectural_ready = {str(entry.architectural_ready).lower()}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageScorecardReport) -> bool:
    if not PACKAGE_SCORECARD_PATH.exists():
        return False
    return PACKAGE_SCORECARD_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_scorecard_report()
    failures = validate_package_scorecard(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package scorecard is up to date")
            return 0
        print("package scorecard is stale; regenerate it")
        return 1
    PACKAGE_SCORECARD_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package scorecard")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package scorecard."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package scorecard is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
