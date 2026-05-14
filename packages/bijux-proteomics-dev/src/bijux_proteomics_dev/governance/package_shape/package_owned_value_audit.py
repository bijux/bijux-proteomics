from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import cache

from bijux_proteomics_dev.docs.governance.package_document_contracts import (
    boundary_doc_path,
    markdown_bullets,
    readme_path,
    section_lines,
)
from bijux_proteomics_dev.governance.package_shape.package_surface_pressure import (
    build_package_surface_pressure_report,
)
from bijux_proteomics_dev.governance.runtime.topology import REPO_ROOT
from bijux_proteomics_dev.governance.support.workspace_inventory import (
    workspace_package_names,
)

__all__ = [
    "PACKAGE_OWNED_VALUE_AUDIT_PATH",
    "PackageOwnedValueAuditEntry",
    "PackageOwnedValueAuditGuard",
    "PackageOwnedValueAuditReport",
    "build_package_owned_value_audit_report",
    "run",
    "validate_package_owned_value_audit",
]


PACKAGE_OWNED_VALUE_AUDIT_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "package-owned-value-audit.toml"
)


@dataclass(frozen=True)
class PackageOwnedValueAuditEntry:
    """Current owned-value audit for one package."""

    distribution_name: str
    owned_value_bullets: tuple[str, ...]
    owned_value_summary: str
    owner_depth_count: int
    public_breadth_count: int
    readme_sentence_count: int


@dataclass(frozen=True)
class PackageOwnedValueAuditGuard:
    """Release-blocking baseline for explicit owned-value audits."""

    min_total_owned_value_bullet_count: int
    min_total_owner_depth_count: int


@dataclass(frozen=True)
class PackageOwnedValueAuditReport:
    """Checked current-value audit across workspace packages."""

    entries: tuple[PackageOwnedValueAuditEntry, ...]
    guard: PackageOwnedValueAuditGuard


def _owned_value_summary(package_name: str) -> str:
    bullets = _owned_value_bullets(package_name)
    return "; ".join(bullets)


def _owned_value_bullets(package_name: str) -> tuple[str, ...]:
    path = boundary_doc_path(package_name)
    bullets = markdown_bullets(path, "## This package owns")
    if bullets:
        return bullets
    if package_name == "bijux-proteomics-dev":
        fallback = markdown_bullets(path, "## Owned maintenance surfaces")
        if fallback:
            return fallback
    return tuple(
        line.strip()
        for line in section_lines(path, "## This package owns")
        if line.strip() and not line.startswith("- ")
    )


@cache
def build_package_owned_value_audit_report() -> PackageOwnedValueAuditReport:
    """Build the checked owned-value audit across packages."""

    surface_pressure = {
        entry.distribution_name: entry
        for entry in build_package_surface_pressure_report().entries
    }
    entries: list[PackageOwnedValueAuditEntry] = []
    for package_name in workspace_package_names():
        bullets = _owned_value_bullets(package_name)
        readme_sentence_count = sum(
            1
            for line in readme_path(package_name)
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        )
        entries.append(
            PackageOwnedValueAuditEntry(
                distribution_name=package_name,
                owned_value_bullets=bullets,
                owned_value_summary=_owned_value_summary(package_name),
                owner_depth_count=surface_pressure[
                    package_name
                ].owner_logic_module_count,
                public_breadth_count=surface_pressure[
                    package_name
                ].public_breadth_count,
                readme_sentence_count=readme_sentence_count,
            )
        )
    return PackageOwnedValueAuditReport(
        entries=tuple(entries),
        guard=PackageOwnedValueAuditGuard(
            min_total_owned_value_bullet_count=sum(
                len(entry.owned_value_bullets) for entry in entries
            ),
            min_total_owner_depth_count=sum(
                entry.owner_depth_count for entry in entries
            ),
        ),
    )


def validate_package_owned_value_audit(
    report: PackageOwnedValueAuditReport | None = None,
) -> tuple[str, ...]:
    """Fail release when owned-value audits disappear or lose depth."""

    report = report or build_package_owned_value_audit_report()
    failures: list[str] = []
    total_owned_value_bullet_count = sum(
        len(entry.owned_value_bullets) for entry in report.entries
    )
    total_owner_depth_count = sum(entry.owner_depth_count for entry in report.entries)
    if total_owned_value_bullet_count < report.guard.min_total_owned_value_bullet_count:
        failures.append(
            "owned-value audit coverage dropped below the governed baseline"
        )
    if total_owner_depth_count < report.guard.min_total_owner_depth_count:
        failures.append(
            "owner-depth coverage dropped below the governed owned-value baseline"
        )
    for entry in report.entries:
        if not entry.owned_value_bullets:
            failures.append(
                f"{entry.distribution_name} is missing a current owned-value audit"
            )
    return tuple(failures)


def _render_tuple(values: tuple[str, ...]) -> str:
    return ", ".join(
        f'"{value.replace(chr(34), chr(92) + chr(34))}"' for value in values
    )


def _escape(value: str) -> str:
    return value.replace('"', '\\"')


def _toml_text(report: PackageOwnedValueAuditReport) -> str:
    lines = [
        "# Generated package owned-value audit.",
        "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.governance.package_shape.package_owned_value_audit",
        "",
        "[guard]",
        f"min_total_owned_value_bullet_count = {report.guard.min_total_owned_value_bullet_count}",
        f"min_total_owner_depth_count = {report.guard.min_total_owner_depth_count}",
        "",
    ]
    for entry in report.entries:
        lines.extend(
            [
                "[[package]]",
                f'distribution_name = "{entry.distribution_name}"',
                f"owned_value_bullets = [{_render_tuple(entry.owned_value_bullets)}]",
                f'owned_value_summary = "{_escape(entry.owned_value_summary)}"',
                f"owner_depth_count = {entry.owner_depth_count}",
                f"public_breadth_count = {entry.public_breadth_count}",
                f"readme_sentence_count = {entry.readme_sentence_count}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(report: PackageOwnedValueAuditReport) -> bool:
    if not PACKAGE_OWNED_VALUE_AUDIT_PATH.exists():
        return False
    return PACKAGE_OWNED_VALUE_AUDIT_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_package_owned_value_audit_report()
    failures = validate_package_owned_value_audit(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("package owned-value audit is up to date")
            return 0
        print("package owned-value audit is stale; regenerate it")
        return 1
    PACKAGE_OWNED_VALUE_AUDIT_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated package owned-value audit")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the package owned-value audit."
    )
    parser.add_argument(
        "--check", action="store_true", help="Fail if the owned-value audit is stale."
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
