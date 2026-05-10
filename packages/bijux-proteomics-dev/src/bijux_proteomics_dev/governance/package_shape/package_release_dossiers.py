from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any, cast

from bijux_proteomics_dev.governance.support.workspace_inventory import (
    package_root,
    workspace_package_names,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_RELEASE_DOSSIERS_PATH",
    "PackageReleaseDossierEntry",
    "PackageReleaseDossierReport",
    "build_package_release_dossier_report",
    "run",
    "validate_package_release_dossiers",
]


PACKAGE_RELEASE_DOSSIERS_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-release-dossiers.toml"
)


@dataclass(frozen=True)
class PackageReleaseDossierEntry:
    """Reviewer-ready release dossier for one workspace package."""

    distribution_name: str
    strongest_value: str
    weakest_value: str
    broadest_debt: str
    strengths: tuple[str, ...]
    limits: tuple[str, ...]
    proofs: tuple[str, ...]
    unresolved_debt_ids: tuple[str, ...]
    exact_not_ready_reasons: tuple[str, ...]
    publishable: bool


@dataclass(frozen=True)
class PackageReleaseDossierReport:
    """Checked reviewer-ready release dossiers across workspace packages."""

    entries: tuple[PackageReleaseDossierEntry, ...]


def _load_report(name: str) -> dict[str, Any]:
    return tomllib.loads(
        (REPO_ROOT / "configs" / "package-governance" / name).read_text(
            encoding="utf-8"
        )
    )


def _rows(name: str, key: str) -> tuple[dict[str, Any], ...]:
    rows = _load_report(name)[key]
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise TypeError(f"{name}:{key} must be a list of TOML tables")
    return tuple(cast(dict[str, Any], row) for row in rows)


def _boundary_doc_path(package_name: str) -> Path:
    root = package_root(package_name)
    if package_name == "bijux-proteomics-dev":
        return root / "docs" / "SCOPE.md"
    return root / "docs" / "BOUNDARIES.md"


def _section_lines(path: Path, heading: str) -> tuple[str, ...]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    section: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if in_section:
                break
            in_section = line.strip() == heading
            continue
        if in_section:
            section.append(line.rstrip())
    return tuple(section)


def _owner_summary(package_name: str) -> str:
    lines = _section_lines(_boundary_doc_path(package_name), "## This package owns")
    prose = " ".join(
        line.strip() for line in lines if line.strip() and not line.startswith("- ")
    )
    return prose or f"{package_name} owns its documented package surface."


def _debt_priority(entry: dict[str, str]) -> tuple[int, str]:
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    return (severity_rank.get(entry["severity"], 3), entry["debt_family"])


def build_package_release_dossier_report() -> PackageReleaseDossierReport:
    """Build reviewer-ready release dossiers for every workspace package."""

    tree_dossiers = {
        entry["distribution_name"]: entry
        for entry in _rows("package-tree-dossiers.toml", "package")
    }
    dependency_dossiers = {
        entry["distribution_name"]: entry
        for entry in _rows("package-dependency-dossiers.toml", "package")
    }
    docs_claim_proof = {
        entry["distribution_name"]: entry
        for entry in _rows("package-docs-claim-proof.toml", "package")
    }
    fixture_coverage = {
        entry["distribution_name"]: entry
        for entry in _rows("package-fixture-scenario-coverage.toml", "package")
    }
    reopened_debt_entries = _rows("reopened-debt-ledger.toml", "debt")
    debt_by_package: dict[str, list[dict[str, str]]] = {}
    for entry in reopened_debt_entries:
        debt_by_package.setdefault(str(entry["distribution_name"]), []).append(entry)
    module_graph_dir = (
        REPO_ROOT / "configs" / "package-governance" / "module-dependency-graphs"
    )

    entries: list[PackageReleaseDossierEntry] = []
    for package_name in workspace_package_names():
        tree_entry = tree_dossiers[package_name]
        dependency_entry = dependency_dossiers[package_name]
        proof_entry = docs_claim_proof[package_name]
        fixture_entry = fixture_coverage[package_name]
        debt_entries = sorted(debt_by_package.get(package_name, []), key=_debt_priority)
        unresolved_debt_ids = tuple(str(entry["debt_id"]) for entry in debt_entries)
        exact_not_ready_reasons = tuple(str(entry["summary"]) for entry in debt_entries)
        owner_summary = _owner_summary(package_name)
        strongest_value = owner_summary
        weakest_value = (
            exact_not_ready_reasons[0]
            if exact_not_ready_reasons
            else "no reopened structural debt is currently recorded"
        )
        broadest_debt = weakest_value
        strengths = (
            f"owner domains: {len(tree_entry['owner_domains'])}",
            f"dependency dossier: {len(dependency_entry['actual_outbound_edges'])} outbound edges and {len(dependency_entry['actual_inbound_edges'])} inbound consumers are explicitly mapped",
            f"module graph: {(module_graph_dir / f'{package_name}.toml').relative_to(REPO_ROOT).as_posix()}",
        )
        limits = tuple(str(value) for value in tree_entry["excluded_responsibilities"])
        proof_total = (
            int(proof_entry["benchmark_proof_artifact_count"])
            + int(proof_entry["replay_proof_artifact_count"])
            + int(proof_entry["integrity_proof_artifact_count"])
        )
        proofs = (
            f"docs proof artifacts: {proof_total}",
            f"scenario fixtures: medium={fixture_entry['medium_realistic_fixture_count_ge_1024']} negative={fixture_entry['negative_fixture_count']} ambiguity={fixture_entry['ambiguity_fixture_count']} contradiction={fixture_entry['contradiction_fixture_count']}",
            f"compatibility surfaces: {len(tree_entry['compatibility_surfaces'])}",
        )
        publishable = not unresolved_debt_ids
        entries.append(
            PackageReleaseDossierEntry(
                distribution_name=package_name,
                strongest_value=strongest_value,
                weakest_value=weakest_value,
                broadest_debt=broadest_debt,
                strengths=strengths,
                limits=limits,
                proofs=proofs,
                unresolved_debt_ids=unresolved_debt_ids,
                exact_not_ready_reasons=exact_not_ready_reasons,
                publishable=publishable,
            )
        )
    return PackageReleaseDossierReport(entries=tuple(entries))


def validate_package_release_dossiers(
    report: PackageReleaseDossierReport | None = None,
) -> tuple[str, ...]:
    """Validate that reviewer-ready release dossiers stay honest about debt."""

    report = report or build_package_release_dossier_report()
    failures: list[str] = []
    for entry in report.entries:
        if not entry.strongest_value:
            failures.append(
                f"{entry.distribution_name} is missing a strongest value summary"
            )
        if not entry.proofs:
            failures.append(f"{entry.distribution_name} is missing proof points")
        if entry.unresolved_debt_ids and entry.publishable:
            failures.append(
                f"{entry.distribution_name} is marked publishable despite reopened debt"
            )
        if entry.exact_not_ready_reasons and entry.publishable:
            failures.append(
                f"{entry.distribution_name} still needs governance excuses but is marked publishable"
            )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(
        f'"{value.replace(chr(34), chr(92) + chr(34))}"' for value in values
    )


def _escape(value: str) -> str:
    return value.replace('"', '\\"')


def _toml_text(report: PackageReleaseDossierReport) -> str:
    lines = [
        "# Generated package release dossiers.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_release_dossiers",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f'strongest_value = "{_escape(entry.strongest_value)}"',
                f'weakest_value = "{_escape(entry.weakest_value)}"',
                f'broadest_debt = "{_escape(entry.broadest_debt)}"',
                f"strengths = [{_render_tuple(entry.strengths)}]",
                f"limits = [{_render_tuple(entry.limits)}]",
                f"proofs = [{_render_tuple(entry.proofs)}]",
                f"unresolved_debt_ids = [{_render_tuple(entry.unresolved_debt_ids)}]",
                f"exact_not_ready_reasons = [{_render_tuple(entry.exact_not_ready_reasons)}]",
                f"publishable = {str(entry.publishable).lower()}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageReleaseDossierReport) -> bool:
    if not PACKAGE_RELEASE_DOSSIERS_PATH.exists():
        return False
    return PACKAGE_RELEASE_DOSSIERS_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_release_dossier_report()
    failures = validate_package_release_dossiers(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package release dossiers are up to date")
            return 0
        print("package release dossiers are stale; regenerate them")
        return 1
    PACKAGE_RELEASE_DOSSIERS_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package release dossiers")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate package release dossiers."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the package release dossiers are not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
