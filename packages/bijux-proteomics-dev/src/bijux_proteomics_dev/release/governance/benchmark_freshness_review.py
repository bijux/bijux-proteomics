# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generated review of benchmark freshness pressure per flagship workflow family."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta

from bijux_proteomics.benchmarks.flagship_asset_roots import (
    build_flagship_asset_obsolescence_audit,
    build_flagship_asset_refresh_report,
    flagship_asset_obsolescence_audit_path,
    flagship_asset_refresh_report_path,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)

from bijux_proteomics_dev.release.governance.benchmark_review_support import (
    CORE_FOUNDATION_DIR,
    LAST_REVIEWED,
    build_workflow_authority_row_map,
    iter_benchmark_package_bundles,
)

__all__ = [
    "BENCHMARK_FRESHNESS_REVIEW_PATH",
    "BenchmarkFreshnessReviewEntry",
    "BenchmarkFreshnessReviewIssue",
    "build_benchmark_freshness_review",
    "run",
    "validate_benchmark_freshness_review",
]


BENCHMARK_FRESHNESS_REVIEW_PATH = (
    CORE_FOUNDATION_DIR / "benchmark-freshness-review.md"
)


@dataclass(frozen=True)
class BenchmarkFreshnessReviewEntry:
    """One family-level freshness and replacement-pressure row."""

    workflow_family: KnowledgeWorkflowFamily
    benchmark_title: str
    public_dataset_identity: str
    package_root: str
    last_reviewed_on: date
    freshness_window_days: int
    freshness_due_on: date
    review_state: str
    remote_reference_state: str
    stronger_replacement_recorded: bool
    stronger_replacement_note: str
    requested_release_language: str
    release_language_floor: str
    blockers: tuple[str, ...]
    evidence_paths: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkFreshnessReviewIssue:
    """One release-facing freshness issue."""

    code: str
    detail: str


def _today() -> date:
    return date.today()


def _language_rank(language: str) -> int:
    return {
        "internal_support_only": 0,
        "review_grade_bounded": 1,
        "outsider_auditable_bounded": 2,
    }[language]


def _narrow(current: str, fallback: str) -> str:
    if _language_rank(fallback) < _language_rank(current):
        return fallback
    return current


def build_benchmark_freshness_review() -> tuple[BenchmarkFreshnessReviewEntry, ...]:
    """Build the benchmark freshness review across flagship workflow families."""

    authority_rows = build_workflow_authority_row_map()
    refresh_by_family = {
        entry.workflow_family: entry
        for entry in build_flagship_asset_refresh_report(check_remote=False).entries
    }
    obsolescence_by_family = {
        entry.workflow_family: entry
        for entry in build_flagship_asset_obsolescence_audit().entries
    }
    entries: list[BenchmarkFreshnessReviewEntry] = []
    for bundle in iter_benchmark_package_bundles():
        if bundle.package_role != "primary":
            continue
        workflow_family = bundle.workflow_family
        refresh = refresh_by_family[workflow_family.value]
        obsolescence = obsolescence_by_family[workflow_family.value]
        requested_release_language = authority_rows[workflow_family.value].public_release_language
        freshness_due_on = bundle.benchmark_manifest.last_reviewed_on + timedelta(
            days=bundle.benchmark_manifest.freshness_window_days
        )
        review_state = "current"
        blockers: list[str] = []
        if _today() > freshness_due_on:
            review_state = "overdue"
            blockers.append(
                f"benchmark review window expired on {freshness_due_on.isoformat()}"
            )
        remote_reference_state = (
            "recorded_available"
            if refresh.freshness_state == "ready"
            else "attention_required"
        )
        if remote_reference_state != "recorded_available":
            blockers.append(
                "remote reference availability or copied benchmark snapshots need maintainer attention"
            )
        stronger_replacement_recorded = False
        stronger_replacement_note = (
            "No stronger checked replacement is recorded yet. "
            + obsolescence.replacement_direction
        )
        release_language_floor = requested_release_language
        if blockers and requested_release_language != "internal_support_only":
            release_language_floor = _narrow(
                requested_release_language,
                "review_grade_bounded",
            )
        entries.append(
            BenchmarkFreshnessReviewEntry(
                workflow_family=workflow_family,
                benchmark_title=bundle.benchmark_manifest.title,
                public_dataset_identity=bundle.public_dataset_identity,
                package_root=bundle.package_root,
                last_reviewed_on=bundle.benchmark_manifest.last_reviewed_on,
                freshness_window_days=bundle.benchmark_manifest.freshness_window_days,
                freshness_due_on=freshness_due_on,
                review_state=review_state,
                remote_reference_state=remote_reference_state,
                stronger_replacement_recorded=stronger_replacement_recorded,
                stronger_replacement_note=stronger_replacement_note,
                requested_release_language=requested_release_language,
                release_language_floor=release_language_floor,
                blockers=tuple(blockers),
                evidence_paths=(
                    bundle.benchmark_manifest_path,
                    bundle.source_locator_manifest_path,
                    flagship_asset_refresh_report_path(),
                    flagship_asset_obsolescence_audit_path(),
                ),
            )
        )
    return tuple(entries)


def validate_benchmark_freshness_review() -> tuple[BenchmarkFreshnessReviewIssue, ...]:
    """Return release-facing issues from the freshness review."""

    issues: list[BenchmarkFreshnessReviewIssue] = []
    for entry in build_benchmark_freshness_review():
        if entry.review_state != "current":
            issues.append(
                BenchmarkFreshnessReviewIssue(
                    code="benchmark-review-window-expired",
                    detail=(
                        f"{entry.workflow_family.value} benchmark review window expired on "
                        f"{entry.freshness_due_on.isoformat()}"
                    ),
                )
            )
        if entry.remote_reference_state != "recorded_available":
            issues.append(
                BenchmarkFreshnessReviewIssue(
                    code="benchmark-remote-reference-attention-required",
                    detail=(
                        f"{entry.workflow_family.value} benchmark freshness report no longer "
                        "records all remote references and copied snapshots as available"
                    ),
                )
            )
    return tuple(issues)


def _render_markdown(entries: tuple[BenchmarkFreshnessReviewEntry, ...]) -> str:
    lines = [
        "---",
        "title: Benchmark Freshness Review",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-core-docs",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
        "# Benchmark Freshness Review",
        "",
        "This page records whether each flagship workflow family still has a current benchmark review window, whether the checked freshness report still records its copied snapshots and remote references as available, and whether a stronger checked replacement is already recorded. Release narrowing consumes these rows directly when freshness drops below the current public sentence.",
        "",
        "## Coverage",
        "",
        "| workflow family | review state | remote reference state | requested language | release language floor |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            f"| `{entry.workflow_family.value}` | `{entry.review_state}` | "
            f"`{entry.remote_reference_state}` | `{entry.requested_release_language}` | "
            f"`{entry.release_language_floor}` |"
        )
    lines.extend(
        [
            "",
            "## Family Review",
            "",
        ]
    )
    for entry in entries:
        lines.extend(
            [
                f"### `{entry.workflow_family.value}`",
                "",
                f"- benchmark title: {entry.benchmark_title}",
                f"- public dataset identity: {entry.public_dataset_identity}",
                f"- package root: `{entry.package_root}`",
                f"- last reviewed on: `{entry.last_reviewed_on.isoformat()}`",
                f"- freshness window: `{entry.freshness_window_days}` days",
                f"- freshness due on: `{entry.freshness_due_on.isoformat()}`",
                f"- review state: `{entry.review_state}`",
                f"- remote reference state: `{entry.remote_reference_state}`",
                f"- stronger replacement recorded: `{'yes' if entry.stronger_replacement_recorded else 'no'}`",
                f"- replacement note: {entry.stronger_replacement_note}",
                f"- requested release language: `{entry.requested_release_language}`",
                f"- release language floor: `{entry.release_language_floor}`",
                f"- blockers: {', '.join(entry.blockers) if entry.blockers else 'none'}",
                f"- evidence paths: {', '.join(f'`{path}`' for path in entry.evidence_paths)}",
                "",
            ]
        )
    return "\n".join(lines)


def _is_up_to_date(entries: tuple[BenchmarkFreshnessReviewEntry, ...]) -> bool:
    if not BENCHMARK_FRESHNESS_REVIEW_PATH.exists():
        return False
    return BENCHMARK_FRESHNESS_REVIEW_PATH.read_text(encoding="utf-8") == _render_markdown(
        entries
    )


def run(check: bool = False) -> int:
    entries = build_benchmark_freshness_review()
    if check:
        if _is_up_to_date(entries):
            print("benchmark freshness review is up to date")
            return 0
        print("benchmark freshness review is stale; regenerate it")
        return 1
    BENCHMARK_FRESHNESS_REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    BENCHMARK_FRESHNESS_REVIEW_PATH.write_text(
        _render_markdown(entries),
        encoding="utf-8",
    )
    print("generated benchmark freshness review")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if outputs are stale")
    return parser


def main() -> int:
    args = _parser().parse_args()
    return run(check=args.check)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
