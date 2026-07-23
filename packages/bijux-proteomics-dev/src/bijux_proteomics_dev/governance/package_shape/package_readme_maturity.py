from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import cache
import re

from bijux_proteomics_dev.docs.governance.package_document_contracts import (
    readme_opening_lines,
)
from bijux_proteomics_dev.governance.package_shape.package_owned_value_audit import (
    build_package_owned_value_audit_report,
)
from bijux_proteomics_dev.governance.package_shape.package_release_dossiers import (
    build_package_release_dossier_report,
)
from bijux_proteomics_dev.governance.package_shape.package_scorecard import (
    build_package_scorecard_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_README_MATURITY_PATH",
    "PackageReadmeMaturityEntry",
    "PackageReadmeMaturityGuard",
    "PackageReadmeMaturityReport",
    "build_package_readme_maturity_report",
    "run",
    "validate_package_readme_maturity",
]


PACKAGE_README_MATURITY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-readme-maturity.toml"
)
MATURITY_TOKENS = (
    "ready",
    "publish",
    "stable",
    "mature",
    "reviewer-ready",
    "release-ready",
)
MATURITY_PATTERNS = tuple(
    re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE) for token in MATURITY_TOKENS
)
COMPLETION_PATTERNS = (
    re.compile(r"\bcomplete\b", re.IGNORECASE),
    re.compile(r"\bend-to-end\b", re.IGNORECASE),
    re.compile(r"\bfull scientific coverage\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class PackageReadmeMaturityEntry:
    """README maturity language measured against owner depth and proof."""

    distribution_name: str
    maturity_claim_count: int
    completion_claim_count: int
    owned_value_bullet_count: int
    proof_depth_count: int
    unresolved_debt_count: int
    maturity_outpaces_owner_logic: bool
    completion_claims_while_not_ready: bool


@dataclass(frozen=True)
class PackageReadmeMaturityGuard:
    """Release-blocking baseline for README maturity overclaim."""

    max_total_maturity_outpaces_owner_logic_count: int
    max_total_completion_claims_while_not_ready_count: int


@dataclass(frozen=True)
class PackageReadmeMaturityReport:
    """Checked README maturity report across workspace packages."""

    entries: tuple[PackageReadmeMaturityEntry, ...]
    guard: PackageReadmeMaturityGuard


@cache
def build_package_readme_maturity_report() -> PackageReadmeMaturityReport:
    """Build the checked README maturity report."""

    owned_value = {
        entry.distribution_name: entry
        for entry in build_package_owned_value_audit_report().entries
    }
    scorecard = {
        entry.distribution_name: entry
        for entry in build_package_scorecard_report().entries
    }
    release_dossiers = {
        entry.distribution_name: entry
        for entry in build_package_release_dossier_report().entries
    }
    entries: list[PackageReadmeMaturityEntry] = []
    for package_name, owned_entry in sorted(owned_value.items()):
        readme_text = "\n".join(readme_opening_lines(package_name))
        maturity_claim_count = sum(
            len(pattern.findall(readme_text)) for pattern in MATURITY_PATTERNS
        )
        completion_claim_count = sum(
            len(pattern.findall(readme_text)) for pattern in COMPLETION_PATTERNS
        )
        scorecard_entry = scorecard[package_name]
        unresolved_debt_count = len(release_dossiers[package_name].unresolved_debt_ids)
        maturity_outpaces_owner_logic = maturity_claim_count > 0 and (
            unresolved_debt_count > 0 or not scorecard_entry.architectural_ready
        )
        completion_claims_while_not_ready = completion_claim_count > 0 and (
            not scorecard_entry.architectural_ready
        )
        entries.append(
            PackageReadmeMaturityEntry(
                distribution_name=package_name,
                maturity_claim_count=maturity_claim_count,
                completion_claim_count=completion_claim_count,
                owned_value_bullet_count=len(owned_entry.owned_value_bullets),
                proof_depth_count=scorecard_entry.proof_depth_count,
                unresolved_debt_count=unresolved_debt_count,
                maturity_outpaces_owner_logic=maturity_outpaces_owner_logic,
                completion_claims_while_not_ready=completion_claims_while_not_ready,
            )
        )
    return PackageReadmeMaturityReport(
        entries=tuple(entries),
        guard=PackageReadmeMaturityGuard(
            max_total_maturity_outpaces_owner_logic_count=sum(
                entry.maturity_outpaces_owner_logic for entry in entries
            ),
            max_total_completion_claims_while_not_ready_count=sum(
                entry.completion_claims_while_not_ready for entry in entries
            ),
        ),
    )


def validate_package_readme_maturity(
    report: PackageReadmeMaturityReport | None = None,
) -> tuple[str, ...]:
    """Fail release when README maturity overclaim grows."""

    report = report or build_package_readme_maturity_report()
    total_overclaim_count = sum(
        entry.maturity_outpaces_owner_logic for entry in report.entries
    )
    if (
        total_overclaim_count
        <= report.guard.max_total_maturity_outpaces_owner_logic_count
    ):
        pass
    else:
        failures = [
            "README maturity overclaim grew beyond the governed owner-logic baseline"
        ]
        total_completion_claim_count = sum(
            entry.completion_claims_while_not_ready for entry in report.entries
        )
        if (
            total_completion_claim_count
            > report.guard.max_total_completion_claims_while_not_ready_count
        ):
            failures.append(
                "package completion claims grew while architectural-ready status is still false"
            )
        return tuple(failures)
    total_completion_claim_count = sum(
        entry.completion_claims_while_not_ready for entry in report.entries
    )
    if (
        total_completion_claim_count
        <= report.guard.max_total_completion_claims_while_not_ready_count
    ):
        return ()
    return (
        "package completion claims grew while architectural-ready status is still false",
    )


def _toml_text(report: PackageReadmeMaturityReport) -> str:
    lines = [
        "# Generated package README maturity report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_readme_maturity",
        "",
        "[guard]",
        (
            "max_total_maturity_outpaces_owner_logic_count = "
            f"{report.guard.max_total_maturity_outpaces_owner_logic_count}"
        ),
        (
            "max_total_completion_claims_while_not_ready_count = "
            f"{report.guard.max_total_completion_claims_while_not_ready_count}"
        ),
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"maturity_claim_count = {entry.maturity_claim_count}",
                f"completion_claim_count = {entry.completion_claim_count}",
                f"owned_value_bullet_count = {entry.owned_value_bullet_count}",
                f"proof_depth_count = {entry.proof_depth_count}",
                f"unresolved_debt_count = {entry.unresolved_debt_count}",
                (
                    "maturity_outpaces_owner_logic = "
                    f"{str(entry.maturity_outpaces_owner_logic).lower()}"
                ),
                (
                    "completion_claims_while_not_ready = "
                    f"{str(entry.completion_claims_while_not_ready).lower()}"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageReadmeMaturityReport) -> bool:
    if not PACKAGE_README_MATURITY_PATH.exists():
        return False
    return PACKAGE_README_MATURITY_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_readme_maturity_report()
    failures = validate_package_readme_maturity(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package README maturity report is up to date")
            return 0
        print("package README maturity report is stale; regenerate it")
        return 1
    PACKAGE_README_MATURITY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package README maturity report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package README maturity report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the README maturity report is stale.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
