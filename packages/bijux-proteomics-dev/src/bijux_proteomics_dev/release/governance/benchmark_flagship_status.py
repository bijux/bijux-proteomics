# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship-status review and promotion gate for public benchmark packages."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bijux_proteomics_dev.release.governance.benchmark_asset_governance import (
    BENCHMARK_INCOMPLETENESS_LEDGER_PATH,
    BENCHMARK_LICENSING_PATH,
    BenchmarkIncompletenessEntry,
    BenchmarkLicensingEntry,
    build_benchmark_asset_audit,
    build_benchmark_incompleteness_ledger,
    build_benchmark_licensing_matrix,
)
from bijux_proteomics_dev.release.governance.benchmark_rerun_governance import (
    BENCHMARK_COMPARABILITY_MATRIX_PATH,
    BENCHMARK_RERUN_KITS_PATH,
    BenchmarkComparabilityRow,
    BenchmarkRerunKitEntry,
    build_benchmark_comparability_matrix,
    build_benchmark_rerun_kits,
)
from bijux_proteomics_dev.release.governance.benchmark_review_support import (
    CORE_FOUNDATION_DIR,
    LAST_REVIEWED,
    family_order,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

__all__ = [
    "BENCHMARK_FLAGSHIP_STATUS_PATH",
    "BenchmarkFlagshipPromotionIssue",
    "BenchmarkFlagshipStatusEntry",
    "build_benchmark_flagship_status",
    "run",
    "validate_benchmark_flagship_promotion",
]


BENCHMARK_FLAGSHIP_STATUS_PATH = CORE_FOUNDATION_DIR / "benchmark-flagship-status.md"


@dataclass(frozen=True)
class BenchmarkFlagshipStatusEntry:
    """One current designation decision for a public benchmark package root."""

    workflow_family: KnowledgeWorkflowFamily
    package_role: str
    package_id: str
    package_root: str
    designation: str
    asset_audit_complete: bool
    rebuild_path_complete: bool
    licensing_story_complete: bool
    comparability_complete: bool
    rerun_kit_complete: bool
    eligible_for_designation: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkFlagshipPromotionIssue:
    """One package naming issue caught by the benchmark promotion gate."""

    code: str
    detail: str


def _designation(workflow_family: KnowledgeWorkflowFamily, package_role: str) -> str:
    if package_role == "companion generalization package":
        return "generalization_companion"
    if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
        return "flagship_primary_internal_support"
    return "flagship_primary_outsider_auditable"


def _by_package_id(entries: tuple[Any, ...]) -> dict[str, Any]:
    return {str(entry.package_id): entry for entry in entries}


def build_benchmark_flagship_status() -> tuple[BenchmarkFlagshipStatusEntry, ...]:
    """Review the current designation allowed for each public benchmark root."""

    asset_audit = _by_package_id(build_benchmark_asset_audit())
    licensing = _by_package_id(build_benchmark_licensing_matrix())
    incompleteness = _by_package_id(build_benchmark_incompleteness_ledger())
    rerun_kits = {
        entry.workflow_family: entry for entry in build_benchmark_rerun_kits()
    }
    comparability = {
        entry.workflow_family: entry for entry in build_benchmark_comparability_matrix()
    }

    rows: list[BenchmarkFlagshipStatusEntry] = []
    for package_id, audit_entry in sorted(
        asset_audit.items(),
        key=lambda item: (
            family_order(item[1].workflow_family),
            0 if item[1].package_role == "primary flagship package" else 1,
        ),
    ):
        licensing_entry: BenchmarkLicensingEntry = licensing[package_id]
        incompleteness_entry: BenchmarkIncompletenessEntry = incompleteness[package_id]
        rerun_kit: BenchmarkRerunKitEntry = rerun_kits[audit_entry.workflow_family]
        comparability_row: BenchmarkComparabilityRow = comparability[
            audit_entry.workflow_family
        ]
        designation = _designation(
            audit_entry.workflow_family, audit_entry.package_role
        )
        asset_audit_complete = audit_entry.support_files_present and bool(
            audit_entry.source_rows
        )
        rebuild_path_complete = bool(
            audit_entry.rebuild_command and audit_entry.rebuild_instructions_path
        )
        licensing_story_complete = bool(
            licensing_entry.dataset_license_and_reuse_note
            and licensing_entry.known_license_limits
            and licensing_entry.source_license_notes
        )
        comparability_complete = bool(
            comparability_row.report_path and comparability_row.comparison_notes
        )
        rerun_kit_complete = bool(
            rerun_kit.opening_order
            and rerun_kit.validating_test_paths
            and rerun_kit.primary_spec.canonical_entrypoint
            and rerun_kit.companion_spec.canonical_entrypoint
        )
        reasons: list[str] = []
        if audit_entry.package_role == "companion generalization package":
            reasons.append(
                "Companion roots remain published, but their durable role is cross-package challenge rather than flagship naming."
            )
        if audit_entry.workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
            reasons.append(
                "Multiplex remains flagship-visible but internal-support only because public workflow language is intentionally narrower."
            )
        reasons.extend(incompleteness_entry.quality_blockers[:2])
        eligible_for_designation = (
            asset_audit_complete
            and rebuild_path_complete
            and licensing_story_complete
            and comparability_complete
            and rerun_kit_complete
        )
        rows.append(
            BenchmarkFlagshipStatusEntry(
                workflow_family=audit_entry.workflow_family,
                package_role=audit_entry.package_role,
                package_id=package_id,
                package_root=audit_entry.package_root,
                designation=designation,
                asset_audit_complete=asset_audit_complete,
                rebuild_path_complete=rebuild_path_complete,
                licensing_story_complete=licensing_story_complete,
                comparability_complete=comparability_complete,
                rerun_kit_complete=rerun_kit_complete,
                eligible_for_designation=eligible_for_designation,
                reasons=tuple(dict.fromkeys(reasons)),
            )
        )
    return tuple(rows)


def validate_benchmark_flagship_promotion() -> tuple[
    BenchmarkFlagshipPromotionIssue, ...
]:
    """Fail when a package keeps flagship naming without the required evidence."""

    issues: list[BenchmarkFlagshipPromotionIssue] = []
    for entry in build_benchmark_flagship_status():
        if (
            entry.designation.startswith("flagship_")
            and not entry.eligible_for_designation
        ):
            issues.append(
                BenchmarkFlagshipPromotionIssue(
                    code="flagship-designation-without-complete-evidence",
                    detail=(
                        f"{entry.package_id} still carries flagship naming while one of the required "
                        "asset, rebuild, licensing, comparability, or rerun-kit surfaces is incomplete"
                    ),
                )
            )
        if (
            entry.package_role == "companion generalization package"
            and entry.designation.startswith("flagship_")
        ):
            issues.append(
                BenchmarkFlagshipPromotionIssue(
                    code="companion-package-called-flagship",
                    detail=(
                        f"{entry.package_id} is a companion challenge root and must not keep flagship designation"
                    ),
                )
            )
    return tuple(issues)


def _render_status_page(entries: tuple[BenchmarkFlagshipStatusEntry, ...]) -> str:
    lines = [
        "---",
        "title: Benchmark Flagship Status",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-core-docs",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
        "# Benchmark Flagship Status",
        "",
        "This page re-evaluates which public benchmark roots still deserve flagship naming. The promotion gate requires complete asset audit coverage, rebuild discipline, licensing story, comparability notes, and rerun-kit coverage before a root may keep `flagship` in its durable designation.",
        "",
        "Reference surfaces:",
        "",
        f"- `{BENCHMARK_LICENSING_PATH.relative_to(CORE_FOUNDATION_DIR.parents[2]).as_posix()}`",
        f"- `{BENCHMARK_INCOMPLETENESS_LEDGER_PATH.relative_to(CORE_FOUNDATION_DIR.parents[2]).as_posix()}`",
        f"- `{BENCHMARK_RERUN_KITS_PATH.relative_to(CORE_FOUNDATION_DIR.parents[2]).as_posix()}`",
        f"- `{BENCHMARK_COMPARABILITY_MATRIX_PATH.relative_to(CORE_FOUNDATION_DIR.parents[2]).as_posix()}`",
        "",
        "| workflow family | package role | designation | eligible |",
        "| --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            "| "
            f"`{entry.workflow_family.value}` | {entry.package_role} | "
            f"`{entry.designation}` | {'yes' if entry.eligible_for_designation else 'no'} |"
        )
    lines.extend(["", "## Current Review", ""])
    for entry in entries:
        lines.extend(
            [
                f"### `{entry.workflow_family.value}`: {entry.package_role}",
                "",
                f"- package id: `{entry.package_id}`",
                f"- package root: `{entry.package_root}`",
                f"- designation: `{entry.designation}`",
                f"- asset audit complete: {'yes' if entry.asset_audit_complete else 'no'}",
                f"- rebuild path complete: {'yes' if entry.rebuild_path_complete else 'no'}",
                f"- licensing story complete: {'yes' if entry.licensing_story_complete else 'no'}",
                f"- comparability complete: {'yes' if entry.comparability_complete else 'no'}",
                f"- rerun kit complete: {'yes' if entry.rerun_kit_complete else 'no'}",
                f"- eligible for designation: {'yes' if entry.eligible_for_designation else 'no'}",
                "",
            ]
        )
        for reason in entry.reasons:
            lines.append(f"- {reason}")
        lines.append("")
    return "\n".join(lines)


def _write_text(path: Path, text: str) -> int:
    rendered = text.rstrip() + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return 0
    path.write_text(rendered, encoding="utf-8")
    return 1


def run(*, check: bool = False) -> int:
    """Write or verify the benchmark flagship-status page."""

    rendered_text = _render_status_page(build_benchmark_flagship_status())
    if check:
        return (
            0
            if BENCHMARK_FLAGSHIP_STATUS_PATH.exists()
            and BENCHMARK_FLAGSHIP_STATUS_PATH.read_text(encoding="utf-8")
            == rendered_text.rstrip() + "\n"
            else 1
        )
    _write_text(BENCHMARK_FLAGSHIP_STATUS_PATH, rendered_text)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bijux-proteomics benchmark-flagship-status",
        description=(
            "Generate or verify benchmark flagship-status review and promotion gate docs."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that the checked-in flagship-status page matches generated content",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return run(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
