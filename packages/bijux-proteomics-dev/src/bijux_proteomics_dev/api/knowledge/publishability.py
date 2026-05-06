from __future__ import annotations

import argparse
from dataclasses import dataclass

from bijux_proteomics_dev.api.foundation.root_consumers import REPO_ROOT
from bijux_proteomics_dev.api.knowledge.breadth import (
    KNOWLEDGE_BREADTH_PATH,
    build_knowledge_breadth_report,
    validate_knowledge_breadth,
)
from bijux_proteomics_dev.api.knowledge.reference_quality import (
    KNOWLEDGE_ORPHAN_REFERENCES_PATH,
    KNOWLEDGE_PROVENANCE_COMPLETENESS_PATH,
    KNOWLEDGE_UNDER_CURATED_WORKFLOWS_PATH,
    build_knowledge_orphan_reference_report,
    build_knowledge_provenance_completeness_report,
    build_knowledge_under_curated_workflow_report,
)

__all__ = [
    "KNOWLEDGE_PUBLISHABILITY_PATH",
    "KnowledgePublishabilityGuard",
    "KnowledgePublishabilityReport",
    "build_knowledge_publishability_report",
    "run",
    "validate_knowledge_publishability",
]


KNOWLEDGE_PUBLISHABILITY_PATH = (
    REPO_ROOT / "configs" / "package-governance" / "knowledge-publishability.toml"
)


@dataclass(frozen=True)
class KnowledgePublishabilityGuard:
    """Release thresholds for a publishable knowledge package."""

    max_total_public_surface_count: int
    max_query_helper_count: int
    min_curated_entries_per_public_surface: float
    min_provenance_complete_surface_count: int
    max_under_curated_workflow_count: int
    max_orphan_reference_count: int


@dataclass(frozen=True)
class KnowledgePublishabilityReport:
    """One checked publishability decision for knowledge."""

    total_public_surface_count: int
    query_helper_count: int
    curated_registry_entry_count: int
    curated_entries_per_public_surface: float
    provenance_complete_surface_count: int
    under_curated_workflow_count: int
    orphan_reference_count: int
    breadth_ready: bool
    guard: KnowledgePublishabilityGuard

    @property
    def publishable(self) -> bool:
        return not validate_knowledge_publishability(self)


def build_knowledge_publishability_report() -> KnowledgePublishabilityReport:
    """Build the checked publishability report for knowledge."""

    breadth_report = build_knowledge_breadth_report()
    provenance_entries = build_knowledge_provenance_completeness_report()
    under_curated_entries = build_knowledge_under_curated_workflow_report()
    orphan_entries = build_knowledge_orphan_reference_report()

    provenance_complete_surface_count = sum(
        1
        for entry in provenance_entries
        if entry.complete_entry_count == entry.entry_count
    )
    under_curated_workflow_count = sum(
        1 for entry in under_curated_entries if entry.under_curated_reasons
    )
    orphan_reference_count = sum(len(entry.orphan_ids) for entry in orphan_entries)
    metrics = breadth_report.metrics

    return KnowledgePublishabilityReport(
        total_public_surface_count=metrics.total_public_surface_count,
        query_helper_count=metrics.query_helper_count,
        curated_registry_entry_count=metrics.curated_registry_entry_count,
        curated_entries_per_public_surface=metrics.curated_entries_per_public_surface,
        provenance_complete_surface_count=provenance_complete_surface_count,
        under_curated_workflow_count=under_curated_workflow_count,
        orphan_reference_count=orphan_reference_count,
        breadth_ready=not validate_knowledge_breadth(),
        guard=KnowledgePublishabilityGuard(
            max_total_public_surface_count=metrics.total_public_surface_count,
            max_query_helper_count=metrics.query_helper_count,
            min_curated_entries_per_public_surface=(
                metrics.curated_entries_per_public_surface
            ),
            min_provenance_complete_surface_count=provenance_complete_surface_count,
            max_under_curated_workflow_count=0,
            max_orphan_reference_count=0,
        ),
    )


def validate_knowledge_publishability(
    report: KnowledgePublishabilityReport | None = None,
) -> tuple[str, ...]:
    """Fail release when knowledge stops being dense, selective, and fully cited."""

    report = report or build_knowledge_publishability_report()
    failures: list[str] = []

    if report.total_public_surface_count > report.guard.max_total_public_surface_count:
        failures.append(
            "knowledge publishability disallows broader public menus than the governed memory surface"
        )
    if report.query_helper_count > report.guard.max_query_helper_count:
        failures.append(
            "knowledge publishability allows only the governed single query-helper surface"
        )
    if (
        report.curated_entries_per_public_surface
        < report.guard.min_curated_entries_per_public_surface
    ):
        failures.append(
            "knowledge publishability requires the exported menu to stay denser than the curated memory beneath it"
        )
    if (
        report.provenance_complete_surface_count
        < report.guard.min_provenance_complete_surface_count
    ):
        failures.append(
            "knowledge publishability requires full provenance coverage across every curated reference surface"
        )
    if (
        report.under_curated_workflow_count
        > report.guard.max_under_curated_workflow_count
    ):
        failures.append(
            "knowledge publishability requires zero under-curated workflow families"
        )
    if report.orphan_reference_count > report.guard.max_orphan_reference_count:
        failures.append(
            "knowledge publishability requires zero orphan curated references"
        )
    if not report.breadth_ready:
        failures.append(
            "knowledge publishability requires a clean breadth-versus-curation-depth report"
        )
    for failure in validate_knowledge_breadth():
        failures.append(f"breadth: {failure}")
    return tuple(failures)


def _toml_text(report: KnowledgePublishabilityReport) -> str:
    guard = report.guard
    return "\n".join(
        (
            "# Generated knowledge publishability report.",
            "# Regenerate with: ./.venv/bin/python -m bijux_proteomics_dev.api.knowledge.publishability",
            "",
            "[metrics]",
            f"total_public_surface_count = {report.total_public_surface_count}",
            f"query_helper_count = {report.query_helper_count}",
            f"curated_registry_entry_count = {report.curated_registry_entry_count}",
            (
                "curated_entries_per_public_surface = "
                f"{report.curated_entries_per_public_surface}"
            ),
            (
                "provenance_complete_surface_count = "
                f"{report.provenance_complete_surface_count}"
            ),
            (
                "under_curated_workflow_count = "
                f"{report.under_curated_workflow_count}"
            ),
            f"orphan_reference_count = {report.orphan_reference_count}",
            f"breadth_ready = {str(report.breadth_ready).lower()}",
            f"publishable = {str(report.publishable).lower()}",
            "",
            "[guard]",
            (
                "max_total_public_surface_count = "
                f"{guard.max_total_public_surface_count}"
            ),
            f"max_query_helper_count = {guard.max_query_helper_count}",
            (
                "min_curated_entries_per_public_surface = "
                f"{guard.min_curated_entries_per_public_surface}"
            ),
            (
                "min_provenance_complete_surface_count = "
                f"{guard.min_provenance_complete_surface_count}"
            ),
            (
                "max_under_curated_workflow_count = "
                f"{guard.max_under_curated_workflow_count}"
            ),
            f"max_orphan_reference_count = {guard.max_orphan_reference_count}",
            "",
            "[evidence]",
            f'knowledge_breadth_path = "{KNOWLEDGE_BREADTH_PATH.relative_to(REPO_ROOT).as_posix()}"',
            f'provenance_completeness_path = "{KNOWLEDGE_PROVENANCE_COMPLETENESS_PATH.relative_to(REPO_ROOT).as_posix()}"',
            f'under_curated_workflows_path = "{KNOWLEDGE_UNDER_CURATED_WORKFLOWS_PATH.relative_to(REPO_ROOT).as_posix()}"',
            f'orphan_references_path = "{KNOWLEDGE_ORPHAN_REFERENCES_PATH.relative_to(REPO_ROOT).as_posix()}"',
        )
    )


def _is_up_to_date(report: KnowledgePublishabilityReport) -> bool:
    if not KNOWLEDGE_PUBLISHABILITY_PATH.exists():
        return False
    return KNOWLEDGE_PUBLISHABILITY_PATH.read_text(encoding="utf-8") == _toml_text(
        report
    )


def run(check: bool = False) -> int:
    report = build_knowledge_publishability_report()
    failures = validate_knowledge_publishability(report)
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if check:
        if _is_up_to_date(report):
            print("knowledge publishability report is up to date")
            return 0
        print("knowledge publishability report is stale; regenerate it")
        return 1
    KNOWLEDGE_PUBLISHABILITY_PATH.write_text(_toml_text(report), encoding="utf-8")
    print("generated knowledge publishability report")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate or validate the knowledge publishability report."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the knowledge publishability report is not up to date.",
    )
    args = parser.parse_args()
    raise SystemExit(run(check=args.check))
