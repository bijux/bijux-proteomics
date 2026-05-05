from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.api.package_module_ledger import build_package_module_ledger_report
from bijux_proteomics_dev.api.runtime_topology import REPO_ROOT

__all__ = [
    "PACKAGE_WRAPPER_OWNER_BALANCE_PATH",
    "PackageWrapperOwnerBalanceEntry",
    "PackageWrapperOwnerBalanceGuard",
    "PackageWrapperOwnerBalanceReport",
    "build_package_wrapper_owner_balance_report",
    "run",
    "validate_package_wrapper_owner_balance",
]


PACKAGE_WRAPPER_OWNER_BALANCE_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-wrapper-owner-balance.toml"
)


@dataclass(frozen=True)
class PackageWrapperOwnerBalanceEntry:
    """Wrapper pressure compared with owner-logic depth for one package."""

    distribution_name: str
    owner_logic_module_count: int
    wrapper_module_count: int
    wrapper_to_owner_ratio: float
    wrapper_outpaces_owner_logic: bool


@dataclass(frozen=True)
class PackageWrapperOwnerBalanceGuard:
    """Release-blocking baseline for wrapper versus owner balance."""

    max_total_wrapper_outpaces_owner_count: int
    max_average_wrapper_to_owner_ratio: float


@dataclass(frozen=True)
class PackageWrapperOwnerBalanceReport:
    """Checked wrapper-versus-owner balance report across packages."""

    entries: tuple[PackageWrapperOwnerBalanceEntry, ...]
    guard: PackageWrapperOwnerBalanceGuard


def build_package_wrapper_owner_balance_report() -> PackageWrapperOwnerBalanceReport:
    """Build the checked wrapper-versus-owner balance report."""

    module_ledger = build_package_module_ledger_report()
    counts: dict[str, dict[str, int]] = {}
    for entry in module_ledger.entries:
        bucket = counts.setdefault(entry.distribution_name, {"owner": 0, "wrapper": 0})
        if entry.module_kind == "owner_logic":
            bucket["owner"] += 1
        elif entry.module_kind == "compatibility_surface":
            bucket["wrapper"] += 1
    entries: list[PackageWrapperOwnerBalanceEntry] = []
    for distribution_name in sorted(counts):
        owner_logic_module_count = counts[distribution_name]["owner"]
        wrapper_module_count = counts[distribution_name]["wrapper"]
        wrapper_to_owner_ratio = round(
            wrapper_module_count / max(owner_logic_module_count, 1),
            4,
        )
        entries.append(
            PackageWrapperOwnerBalanceEntry(
                distribution_name=distribution_name,
                owner_logic_module_count=owner_logic_module_count,
                wrapper_module_count=wrapper_module_count,
                wrapper_to_owner_ratio=wrapper_to_owner_ratio,
                wrapper_outpaces_owner_logic=wrapper_module_count > owner_logic_module_count,
            )
        )
    return PackageWrapperOwnerBalanceReport(
        entries=tuple(entries),
        guard=PackageWrapperOwnerBalanceGuard(
            max_total_wrapper_outpaces_owner_count=sum(
                entry.wrapper_outpaces_owner_logic for entry in entries
            ),
            max_average_wrapper_to_owner_ratio=round(
                sum(entry.wrapper_to_owner_ratio for entry in entries) / len(entries),
                4,
            ),
        ),
    )


def validate_package_wrapper_owner_balance(
    report: PackageWrapperOwnerBalanceReport | None = None,
) -> tuple[str, ...]:
    """Fail release when wrapper pressure grows faster than owner depth."""

    report = report or build_package_wrapper_owner_balance_report()
    total_wrapper_outpaces_owner_count = sum(
        entry.wrapper_outpaces_owner_logic for entry in report.entries
    )
    average_wrapper_to_owner_ratio = round(
        sum(entry.wrapper_to_owner_ratio for entry in report.entries) / len(report.entries),
        4,
    )
    failures: list[str] = []
    if total_wrapper_outpaces_owner_count > report.guard.max_total_wrapper_outpaces_owner_count:
        failures.append("wrapper-heavy packages grew beyond the governed owner-balance baseline")
    if average_wrapper_to_owner_ratio > report.guard.max_average_wrapper_to_owner_ratio:
        failures.append("wrapper-to-owner ratio grew beyond the governed owner-balance baseline")
    return tuple(failures)


def _toml_text(report: PackageWrapperOwnerBalanceReport) -> str:
    lines = [
        "# Generated package wrapper-owner balance report.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.package_wrapper_owner_balance",
        "",
        "[guard]",
        f"max_total_wrapper_outpaces_owner_count = {report.guard.max_total_wrapper_outpaces_owner_count}",
        f"max_average_wrapper_to_owner_ratio = {report.guard.max_average_wrapper_to_owner_ratio}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"owner_logic_module_count = {entry.owner_logic_module_count}",
                f"wrapper_module_count = {entry.wrapper_module_count}",
                f"wrapper_to_owner_ratio = {entry.wrapper_to_owner_ratio}",
                f"wrapper_outpaces_owner_logic = {str(entry.wrapper_outpaces_owner_logic).lower()}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageWrapperOwnerBalanceReport) -> bool:
    if not PACKAGE_WRAPPER_OWNER_BALANCE_PATH.exists():
        return False
    return PACKAGE_WRAPPER_OWNER_BALANCE_PATH.read_text(encoding="utf-8") == _toml_text(report)


def run(check: bool = False) -> int:
    report = build_package_wrapper_owner_balance_report()
    failures = validate_package_wrapper_owner_balance(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package wrapper-owner balance report is up to date")
            return 0
        print("package wrapper-owner balance report is stale; regenerate it")
        return 1
    PACKAGE_WRAPPER_OWNER_BALANCE_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package wrapper-owner balance report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate or validate the package wrapper-owner balance report.")
    parser.add_argument("--check", action="store_true", help="Fail if the report is stale.")
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
