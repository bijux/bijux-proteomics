from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import cache

from bijux_proteomics_dev.governance.package_shape.package_readme_maturity import (
    build_package_readme_maturity_report,
)
from bijux_proteomics_dev.governance.package_shape.package_root_surface_illusions import (
    build_package_root_surface_illusion_report,
)
from bijux_proteomics_dev.governance.package_shape.package_topology_drift import (
    build_package_topology_drift_report,
)
from bijux_proteomics_dev.governance.package_shape.package_wrapper_owner_balance import (
    build_package_wrapper_owner_balance_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT

__all__ = [
    "PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH",
    "PackageReopenedCompletionClaimEntry",
    "PackageReopenedCompletionClaimGuard",
    "PackageReopenedCompletionClaimReport",
    "build_package_reopened_completion_claim_report",
    "run",
    "validate_package_reopened_completion_claims",
]


PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH = (
    REPO_ROOT
    / "configs"
    / "package-governance"
    / "package-reopened-completion-claims.toml"
)


@dataclass(frozen=True)
class PackageReopenedCompletionClaimEntry:
    """One package whose prior completion claim is structurally reopened."""

    distribution_name: str
    reopened_reasons: tuple[str, ...]
    reopened_completion_claim: bool


@dataclass(frozen=True)
class PackageReopenedCompletionClaimGuard:
    """Release-blocking baseline for reopened completion pressure."""

    max_total_reopened_completion_claim_count: int


@dataclass(frozen=True)
class PackageReopenedCompletionClaimReport:
    """Checked reopened completion-claim report across packages."""

    entries: tuple[PackageReopenedCompletionClaimEntry, ...]
    guard: PackageReopenedCompletionClaimGuard


@cache
def build_package_reopened_completion_claim_report() -> (
    PackageReopenedCompletionClaimReport
):
    """Build the checked reopened completion-claim report."""

    topology = {
        entry.distribution_name: entry
        for entry in build_package_topology_drift_report().entries
    }
    maturity = {
        entry.distribution_name: entry
        for entry in build_package_readme_maturity_report().entries
    }
    root_illusions = {
        entry.distribution_name: entry
        for entry in build_package_root_surface_illusion_report().entries
    }
    wrapper_balance = {
        entry.distribution_name: entry
        for entry in build_package_wrapper_owner_balance_report().entries
    }
    entries: list[PackageReopenedCompletionClaimEntry] = []
    for package_name in sorted(topology):
        reasons: list[str] = []
        if topology[package_name].docs_tree_contradiction:
            reasons.append("docs and tree still contradict each other")
        if topology[package_name].historical_shape_dominates_design:
            reasons.append(
                "historical topology language still dominates current design"
            )
        if root_illusions[package_name].root_surface_hides_owner_depth:
            reasons.extend(root_illusions[package_name].illusion_reasons)
        if maturity[package_name].maturity_outpaces_owner_logic:
            reasons.append(
                "README maturity language still outruns owned logic and proof"
            )
        if wrapper_balance[package_name].wrapper_outpaces_owner_logic:
            reasons.append("wrapper pressure still outweighs owner logic depth")
        entries.append(
            PackageReopenedCompletionClaimEntry(
                distribution_name=package_name,
                reopened_reasons=tuple(dict.fromkeys(reasons)),
                reopened_completion_claim=bool(reasons),
            )
        )
    return PackageReopenedCompletionClaimReport(
        entries=tuple(entries),
        guard=PackageReopenedCompletionClaimGuard(
            max_total_reopened_completion_claim_count=sum(
                entry.reopened_completion_claim for entry in entries
            )
        ),
    )


def validate_package_reopened_completion_claims(
    report: PackageReopenedCompletionClaimReport | None = None,
) -> tuple[str, ...]:
    """Fail release when more packages need reopened completion caveats."""

    report = report or build_package_reopened_completion_claim_report()
    total_reopened_completion_claim_count = sum(
        entry.reopened_completion_claim for entry in report.entries
    )
    if (
        total_reopened_completion_claim_count
        <= report.guard.max_total_reopened_completion_claim_count
    ):
        return ()
    return ("reopened completion claims grew beyond the governed structural baseline",)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(
        f'"{value.replace(chr(34), chr(92) + chr(34))}"' for value in values
    )


def _toml_text(report: PackageReopenedCompletionClaimReport) -> str:
    lines = [
        "# Generated package reopened completion-claim report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_reopened_completion_claims",
        "",
        "[guard]",
        (
            "max_total_reopened_completion_claim_count = "
            f"{report.guard.max_total_reopened_completion_claim_count}"
        ),
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"reopened_reasons = [{_render_tuple(entry.reopened_reasons)}]",
                (
                    "reopened_completion_claim = "
                    f"{str(entry.reopened_completion_claim).lower()}"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageReopenedCompletionClaimReport) -> bool:
    if not PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH.exists():
        return False
    return PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH.read_text(
        encoding="utf-8"
    ) == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_reopened_completion_claim_report()
    failures = validate_package_reopened_completion_claims(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package reopened completion-claim report is up to date")
            return 0
        print("package reopened completion-claim report is stale; regenerate it")
        return 1
    PACKAGE_REOPENED_COMPLETION_CLAIMS_PATH.write_text(
        _toml_text(report), encoding="utf-8"
    )
    print("generated package reopened completion-claim report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package reopened completion-claim report."
    )
    parser.add_argument(
        "--check", action="store_true", help="Fail if the report is stale."
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
