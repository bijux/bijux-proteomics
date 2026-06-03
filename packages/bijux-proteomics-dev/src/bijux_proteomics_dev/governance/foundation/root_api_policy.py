from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_foundation import __all__ as FOUNDATION_ROOT_EXPORTS
from bijux_proteomics_foundation.public_api import (
    FOUNDATION_ROOT_API_BUDGET,
    list_foundation_root_api_entries,
)

__all__ = [
    "FOUNDATION_ROOT_API_POLICY_PATH",
    "FoundationRootApiBudget",
    "FoundationRootApiPolicyEntry",
    "FoundationRootApiPolicyReport",
    "build_foundation_root_api_policy_report",
    "run",
    "validate_foundation_root_api_policy",
]


FOUNDATION_ROOT_API_POLICY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "foundation-root-api.toml"
)
FOUNDATION_ROOT_INIT_PATH = (
    REPO_ROOT
    / "packages"
    / "bijux-proteomics-foundation"
    / "src"
    / "bijux_proteomics_foundation"
    / "__init__.py"
)


@dataclass(frozen=True)
class FoundationRootApiBudget:
    """Budgets for the curated foundation root API surface."""

    max_public_symbols: int
    max_init_lines: int


@dataclass(frozen=True)
class FoundationRootApiPolicyEntry:
    """One curated export in the checked root API policy."""

    name: str
    owner_module: str
    classification: str
    rationale: str


@dataclass(frozen=True)
class FoundationRootApiPolicyReport:
    """Checked policy for the foundation root API."""

    budget: FoundationRootApiBudget
    symbols: tuple[FoundationRootApiPolicyEntry, ...]


def build_foundation_root_api_policy_report() -> FoundationRootApiPolicyReport:
    """Build the checked foundation root API policy."""

    return FoundationRootApiPolicyReport(
        budget=FoundationRootApiBudget(
            max_public_symbols=FOUNDATION_ROOT_API_BUDGET.max_public_symbols,
            max_init_lines=FOUNDATION_ROOT_API_BUDGET.max_init_lines,
        ),
        symbols=tuple(
            FoundationRootApiPolicyEntry(
                name=entry.export_name,
                owner_module=entry.owner_module,
                classification=entry.capability.value,
                rationale=entry.kernel_rationale,
            )
            for entry in list_foundation_root_api_entries()
        ),
    )


def validate_foundation_root_api_policy(
    report: FoundationRootApiPolicyReport | None = None,
) -> tuple[str, ...]:
    """Validate that the checked root API policy stays synchronized."""

    report = report or build_foundation_root_api_policy_report()
    failures: list[str] = []
    if [entry.name for entry in report.symbols] != list(FOUNDATION_ROOT_EXPORTS):
        failures.append("foundation root API policy no longer matches __all__")
    if len(report.symbols) > report.budget.max_public_symbols:
        failures.append("foundation root API exceeded the governed symbol budget")
    if (
        len(FOUNDATION_ROOT_INIT_PATH.read_text(encoding="utf-8").splitlines())
        > report.budget.max_init_lines
    ):
        failures.append(
            "foundation root API exceeded the governed __init__ line budget"
        )
    return tuple(failures)


def _escape(value: str) -> str:
    return value.replace('"', '\\"')


def _toml_text(report: FoundationRootApiPolicyReport) -> str:
    lines = [
        "# Generated bijux-proteomics-foundation root API policy.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.public_api_snapshots",
        "",
        "[budget]",
        f"max_public_symbols = {report.budget.max_public_symbols}",
        f"max_init_lines = {report.budget.max_init_lines}",
        "",
    ]
    for entry in report.symbols:
        lines.extend(
            [
                "[[symbol]]",
                f'name = "{entry.name}"',
                f'owner_module = "{entry.owner_module}"',
                f'classification = "{entry.classification}"',
                f'rationale = "{_escape(entry.rationale)}"',
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: FoundationRootApiPolicyReport) -> bool:
    if not FOUNDATION_ROOT_API_POLICY_PATH.exists():
        return False
    return FOUNDATION_ROOT_API_POLICY_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_foundation_root_api_policy_report()
    failures = validate_foundation_root_api_policy(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("foundation root API policy is up to date")
            return 0
        print("foundation root API policy is stale; regenerate it")
        return 1
    FOUNDATION_ROOT_API_POLICY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated foundation root API policy")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the foundation root API policy."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the foundation root API policy is stale.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
