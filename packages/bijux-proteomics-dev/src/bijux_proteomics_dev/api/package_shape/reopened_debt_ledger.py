from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import tomllib

from bijux_proteomics_dev.api.runtime.topology import REPO_ROOT

__all__ = [
    "REOPENED_DEBT_LEDGER_PATH",
    "ReopenedDebtEntry",
    "ReopenedDebtLedgerReport",
    "build_reopened_debt_ledger_report",
    "run",
    "validate_reopened_debt_ledger",
]


REOPENED_DEBT_LEDGER_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "reopened-debt-ledger.toml"
)


@dataclass(frozen=True)
class ReopenedDebtEntry:
    """One still-open structural debt item that reopens prior completion claims."""

    debt_id: str
    distribution_name: str
    debt_family: str
    severity: str
    summary: str
    evidence_report: str


@dataclass(frozen=True)
class ReopenedDebtLedgerReport:
    """Checked ledger of structurally reopened package debt."""

    entries: tuple[ReopenedDebtEntry, ...]


def _load_report(name: str) -> dict[str, object]:
    return tomllib.loads(
        (REPO_ROOT / "configs" / "package-governance" / name).read_text(encoding="utf-8")
    )


def build_reopened_debt_ledger_report() -> ReopenedDebtLedgerReport:
    """Build the checked reopened-debt ledger from live governance reports."""

    entries: list[ReopenedDebtEntry] = []

    docs_claim_proof = _load_report("package-docs-claim-proof.toml")
    for package in docs_claim_proof["package"]:
        distribution_name = str(package["distribution_name"])
        claim_kinds = tuple(str(value) for value in package["unproven_claim_kinds"])
        if not claim_kinds:
            continue
        entries.append(
            ReopenedDebtEntry(
                debt_id=f"{distribution_name}:docs-claim-gap",
                distribution_name=distribution_name,
                debt_family="docs-claim-gap",
                severity="high",
                summary=(
                    "public docs still outrun proof for "
                    + ", ".join(claim_kinds)
                ),
                evidence_report="configs/package-governance/package-docs-claim-proof.toml",
            )
        )

    tree_dossiers = _load_report("package-tree-dossiers.toml")
    for package in tree_dossiers["package"]:
        distribution_name = str(package["distribution_name"])
        compatibility_surfaces = tuple(
            str(value) for value in package["compatibility_surfaces"]
        )
        if not compatibility_surfaces:
            continue
        entries.append(
            ReopenedDebtEntry(
                debt_id=f"{distribution_name}:compatibility-surfaces",
                distribution_name=distribution_name,
                debt_family="compatibility-surfaces",
                severity="medium",
                summary=(
                    f"{len(compatibility_surfaces)} compatibility surfaces still survive at the package root"
                ),
                evidence_report="configs/package-governance/package-tree-dossiers.toml",
            )
        )

    test_tree_mirror = _load_report("package-test-tree-mirror.toml")
    for package in test_tree_mirror["package"]:
        distribution_name = str(package["distribution_name"])
        missing_test_families = tuple(
            str(value) for value in package["missing_test_families"]
        )
        if not missing_test_families:
            continue
        entries.append(
            ReopenedDebtEntry(
                debt_id=f"{distribution_name}:test-tree-gaps",
                distribution_name=distribution_name,
                debt_family="test-tree-gaps",
                severity="medium",
                summary=(
                    f"{len(missing_test_families)} source owner families still lack matching test families"
                ),
                evidence_report="configs/package-governance/package-test-tree-mirror.toml",
            )
        )

    oversized_modules = _load_report("package-oversized-mixed-modules.toml")
    oversized_counts: dict[str, int] = {}
    for module in oversized_modules["module"]:
        distribution_name = str(module["distribution_name"])
        oversized_counts[distribution_name] = oversized_counts.get(distribution_name, 0) + 1
    for distribution_name, module_count in sorted(oversized_counts.items()):
        entries.append(
            ReopenedDebtEntry(
                debt_id=f"{distribution_name}:mixed-responsibility-modules",
                distribution_name=distribution_name,
                debt_family="mixed-responsibility-modules",
                severity="high",
                summary=(
                    f"{module_count} oversized mixed-responsibility modules still need owner splits"
                ),
                evidence_report="configs/package-governance/package-oversized-mixed-modules.toml",
            )
        )

    tree_quality = _load_report("repository-tree-quality.toml")
    for package in tree_quality["package"]:
        distribution_name = str(package["distribution_name"])
        overall_tree_quality_score = float(package["overall_tree_quality_score"])
        if overall_tree_quality_score >= 70.0:
            continue
        entries.append(
            ReopenedDebtEntry(
                debt_id=f"{distribution_name}:tree-quality",
                distribution_name=distribution_name,
                debt_family="tree-quality",
                severity="high",
                summary=(
                    f"overall tree quality remains below reviewer comfort at {overall_tree_quality_score:.2f}"
                ),
                evidence_report="configs/package-governance/repository-tree-quality.toml",
            )
        )

    reopened_completion_claims = _load_report("package-reopened-completion-claims.toml")
    for package in reopened_completion_claims["package"]:
        distribution_name = str(package["distribution_name"])
        reopened_reasons = tuple(str(value) for value in package["reopened_reasons"])
        if not reopened_reasons:
            continue
        entries.append(
            ReopenedDebtEntry(
                debt_id=f"{distribution_name}:reopened-completion-claim",
                distribution_name=distribution_name,
                debt_family="reopened-completion-claim",
                severity="high",
                summary=reopened_reasons[0],
                evidence_report="configs/package-governance/package-reopened-completion-claims.toml",
            )
        )

    return ReopenedDebtLedgerReport(
        entries=tuple(
            sorted(
                entries,
                key=lambda entry: (
                    entry.distribution_name,
                    entry.debt_family,
                    entry.debt_id,
                ),
            )
        )
    )


def validate_reopened_debt_ledger(
    report: ReopenedDebtLedgerReport | None = None,
) -> tuple[str, ...]:
    """Validate that reopened debt entries remain explicit and evidence-backed."""

    report = report or build_reopened_debt_ledger_report()
    failures: list[str] = []
    for entry in report.entries:
        if not entry.summary:
            failures.append(f"{entry.debt_id} is missing a summary")
        if not entry.evidence_report:
            failures.append(f"{entry.debt_id} is missing an evidence report")
        elif not (REPO_ROOT / entry.evidence_report).exists():
            failures.append(f"{entry.debt_id} points to a missing evidence report")
    return tuple(failures)


def _toml_text(report: ReopenedDebtLedgerReport) -> str:
    lines = [
        "# Generated reopened debt ledger.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.package_shape.reopened_debt_ledger",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[debt]]",
                f'debt_id = "{entry.debt_id}"',
                f'distribution_name = "{entry.distribution_name}"',
                f'debt_family = "{entry.debt_family}"',
                f'severity = "{entry.severity}"',
                f'summary = "{entry.summary}"',
                f'evidence_report = "{entry.evidence_report}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: ReopenedDebtLedgerReport) -> bool:
    if not REOPENED_DEBT_LEDGER_PATH.exists():
        return False
    return REOPENED_DEBT_LEDGER_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_reopened_debt_ledger_report()
    failures = validate_reopened_debt_ledger(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("reopened debt ledger is up to date")
            return 0
        print("reopened debt ledger is stale; regenerate it")
        return 1
    REOPENED_DEBT_LEDGER_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated reopened debt ledger")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the reopened debt ledger."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the reopened debt ledger is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
