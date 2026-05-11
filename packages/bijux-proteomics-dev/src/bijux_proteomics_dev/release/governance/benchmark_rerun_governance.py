# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generated runtime-handbook surfaces for benchmark rerun and comparability."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.benchmarks.workflow_generalization import (
    WorkflowGeneralizationFindingState,
    WorkflowGeneralizationReport,
)
from bijux_proteomics_dev.release.governance.benchmark_asset_governance import (
    build_benchmark_asset_audit,
    build_benchmark_licensing_matrix,
)
from bijux_proteomics_dev.release.governance.benchmark_review_support import (
    LAST_REVIEWED,
    RUNTIME_DIR,
    BenchmarkPackageBundle,
    build_generalization_report_map,
    build_workflow_authority_row_map,
    bundle_runtime_spec,
    family_order,
    iter_benchmark_package_bundles,
)
from bijux_proteomics_intelligence.reviews.external_review_kits import (
    WorkflowExternalReviewKit,
    build_workflow_external_review_kit_family,
)
from bijux_proteomics_intelligence.reviews.independent_reruns import (
    WorkflowIndependentRerunDossier,
    build_workflow_independent_rerun_dossier_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_runtime.workflows.benchmark_runs import (
    BenchmarkRunMode,
    BenchmarkRunSpec,
)

__all__ = [
    "BENCHMARK_COMPARABILITY_MATRIX_PATH",
    "BENCHMARK_RERUN_KITS_PATH",
    "BLACK_BOX_BENCHMARK_DASHBOARD_PATH",
    "BenchmarkBlackBoxDashboardRow",
    "BenchmarkBlackBoxIssue",
    "BenchmarkComparabilityRow",
    "BenchmarkRerunKitEntry",
    "build_black_box_benchmark_dashboard",
    "build_benchmark_comparability_matrix",
    "build_benchmark_rerun_kits",
    "run",
    "validate_black_box_benchmark_language",
]


BENCHMARK_RERUN_KITS_PATH = RUNTIME_DIR / "benchmark-rerun-kits.md"
BENCHMARK_COMPARABILITY_MATRIX_PATH = RUNTIME_DIR / "benchmark-comparability-matrix.md"
BLACK_BOX_BENCHMARK_DASHBOARD_PATH = RUNTIME_DIR / "black-box-benchmark-dashboard.md"


@dataclass(frozen=True)
class BenchmarkRerunKitEntry:
    """One public rerun kit path for a workflow family."""

    workflow_family: KnowledgeWorkflowFamily
    public_release_language: str
    primary_package_root: str
    companion_package_root: str
    primary_spec: BenchmarkRunSpec
    companion_spec: BenchmarkRunSpec
    opening_order: tuple[str, ...]
    validating_test_paths: tuple[str, ...]
    independent_rerun_path: str | None
    external_review_kit_path: str | None
    remaining_limits: tuple[str, ...]
    note: str


@dataclass(frozen=True)
class BenchmarkComparabilityRow:
    """One cross-package comparability row for a workflow family."""

    workflow_family: KnowledgeWorkflowFamily
    public_release_language: str
    primary_package_root: str
    companion_package_root: str
    primary_run_mode: str
    companion_run_mode: str
    family_stability_score: float
    family_stability_label: str
    surviving_claim_count: int
    weakened_claim_count: int
    collapsed_claim_count: int
    report_path: str
    comparison_notes: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkBlackBoxDashboardRow:
    """One workflow-family row in the black-box benchmark dashboard."""

    workflow_family: KnowledgeWorkflowFamily
    requested_language: str
    allowed_language: str
    primary_run_mode: str
    companion_run_mode: str
    drift_status: str
    artifact_completeness: str
    remaining_blockers: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkBlackBoxIssue:
    """One mismatch between black-box benchmark evidence and public language."""

    code: str
    detail: str


def _kit_maps() -> tuple[
    dict[KnowledgeWorkflowFamily, WorkflowIndependentRerunDossier],
    dict[KnowledgeWorkflowFamily, WorkflowExternalReviewKit],
]:
    dossier_family = build_workflow_independent_rerun_dossier_family()
    rerun_dossiers = {
        dossier.workflow_family: dossier for dossier in dossier_family.dossiers
    }
    kit_family = build_workflow_external_review_kit_family()
    external_review_kits = {kit.workflow_family: kit for kit in kit_family.kits}
    return rerun_dossiers, external_review_kits


def _family_bundles() -> dict[
    KnowledgeWorkflowFamily, tuple[BenchmarkPackageBundle, BenchmarkPackageBundle]
]:
    grouped: dict[KnowledgeWorkflowFamily, list[BenchmarkPackageBundle]] = {}
    for bundle in iter_benchmark_package_bundles():
        grouped.setdefault(bundle.workflow_family, []).append(bundle)
    ordered: dict[
        KnowledgeWorkflowFamily, tuple[BenchmarkPackageBundle, BenchmarkPackageBundle]
    ] = {}
    for workflow_family, bundles in grouped.items():
        primary = next(bundle for bundle in bundles if bundle.package_role == "primary")
        companion = next(
            bundle for bundle in bundles if bundle.package_role == "companion"
        )
        ordered[workflow_family] = (primary, companion)
    return ordered


def build_benchmark_rerun_kits() -> tuple[BenchmarkRerunKitEntry, ...]:
    """Return the rerun kit surface for each workflow family."""

    authority_rows = build_workflow_authority_row_map()
    rerun_dossiers, external_review_kits = _kit_maps()
    entries: list[BenchmarkRerunKitEntry] = []
    for workflow_family, (primary, companion) in sorted(
        _family_bundles().items(),
        key=lambda item: family_order(item[0]),
    ):
        primary_spec = bundle_runtime_spec(primary)
        companion_spec = bundle_runtime_spec(companion)
        if primary_spec is None or companion_spec is None:  # pragma: no cover
            raise ValueError(
                f"missing runtime benchmark spec for {workflow_family.value} package family"
            )
        rerun_dossier = rerun_dossiers.get(workflow_family)
        external_review_kit = external_review_kits.get(workflow_family)
        opening_order = [
            primary.benchmark_manifest_path,
            primary.artifact_inventory_path,
            primary_spec.primary_input_path,
            companion.benchmark_manifest_path,
            companion.artifact_inventory_path,
            companion_spec.primary_input_path,
        ]
        if rerun_dossier is not None:
            opening_order.append(rerun_dossier.artifact_path)
        if external_review_kit is not None:
            opening_order.append(external_review_kit.artifact_path)
        remaining_limits: list[str] = list(primary.quality_sheet.exact_blockers[:2])
        remaining_limits.extend(companion.quality_sheet.exact_blockers[:2])
        if rerun_dossier is not None:
            remaining_limits.extend(rerun_dossier.remaining_limits[:2])
        elif workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
            remaining_limits.append(
                "Multiplex remains internal-support only, so the rerun kit is reviewable but not a route to outsider-auditable language."
            )
        entries.append(
            BenchmarkRerunKitEntry(
                workflow_family=workflow_family,
                public_release_language=authority_rows[
                    workflow_family.value
                ].public_release_language,
                primary_package_root=primary.package_root,
                companion_package_root=companion.package_root,
                primary_spec=primary_spec,
                companion_spec=companion_spec,
                opening_order=tuple(dict.fromkeys(opening_order)),
                validating_test_paths=tuple(
                    dict.fromkeys(
                        primary_spec.validating_test_paths
                        + companion_spec.validating_test_paths
                    )
                ),
                independent_rerun_path=(
                    rerun_dossier.artifact_path if rerun_dossier is not None else None
                ),
                external_review_kit_path=(
                    external_review_kit.artifact_path
                    if external_review_kit is not None
                    else None
                ),
                remaining_limits=tuple(dict.fromkeys(remaining_limits)),
                note=(
                    "Open the primary package first, then the companion package, then the rerun dossier or external review kit if one exists. The kit is meant to survive without maintainer narration."
                ),
            )
        )
    return tuple(entries)


def build_benchmark_comparability_matrix() -> tuple[BenchmarkComparabilityRow, ...]:
    """Return cross-package comparability rows for every workflow family."""

    authority_rows = build_workflow_authority_row_map()
    reports = build_generalization_report_map()
    rows: list[BenchmarkComparabilityRow] = []
    for workflow_family, (primary, companion) in sorted(
        _family_bundles().items(),
        key=lambda item: family_order(item[0]),
    ):
        report: WorkflowGeneralizationReport = reports[workflow_family.value]
        primary_spec = bundle_runtime_spec(primary)
        companion_spec = bundle_runtime_spec(companion)
        if primary_spec is None or companion_spec is None:  # pragma: no cover
            raise ValueError(
                f"missing runtime benchmark spec for {workflow_family.value} package family"
            )
        surviving_claim_count = sum(
            finding.state is WorkflowGeneralizationFindingState.SURVIVES
            for finding in report.findings
        )
        weakened_claim_count = sum(
            finding.state is WorkflowGeneralizationFindingState.WEAKENS
            for finding in report.findings
        )
        collapsed_claim_count = sum(
            finding.state is WorkflowGeneralizationFindingState.COLLAPSES
            for finding in report.findings
        )
        comparison_notes = tuple(
            dict.fromkeys(
                (
                    *primary.benchmark_manifest.comparison_notes[:2],
                    *companion.benchmark_manifest.comparison_notes[:2],
                    report.note,
                )
            )
        )
        rows.append(
            BenchmarkComparabilityRow(
                workflow_family=workflow_family,
                public_release_language=authority_rows[
                    workflow_family.value
                ].public_release_language,
                primary_package_root=primary.package_root,
                companion_package_root=companion.package_root,
                primary_run_mode=primary_spec.run_mode.value,
                companion_run_mode=companion_spec.run_mode.value,
                family_stability_score=report.family_stability_score,
                family_stability_label=report.family_stability_label,
                surviving_claim_count=surviving_claim_count,
                weakened_claim_count=weakened_claim_count,
                collapsed_claim_count=collapsed_claim_count,
                report_path=report.artifact_path,
                comparison_notes=comparison_notes,
            )
        )
    return tuple(rows)


def _language_rank(language: str) -> int:
    ranks = {
        "internal_support_only": 0,
        "review_grade_bounded": 1,
        "outsider_auditable_bounded": 2,
    }
    return ranks[language]


def _narrow_language(current: str, fallback: str) -> str:
    if _language_rank(fallback) < _language_rank(current):
        return fallback
    return current


def build_black_box_benchmark_dashboard() -> tuple[BenchmarkBlackBoxDashboardRow, ...]:
    """Return the black-box benchmark dashboard across workflow families."""

    audit_by_id = {entry.package_id: entry for entry in build_benchmark_asset_audit()}
    licensing_by_id = {
        entry.package_id: entry for entry in build_benchmark_licensing_matrix()
    }
    rerun_kits = {
        entry.workflow_family: entry for entry in build_benchmark_rerun_kits()
    }
    comparability = {
        entry.workflow_family: entry for entry in build_benchmark_comparability_matrix()
    }

    rows: list[BenchmarkBlackBoxDashboardRow] = []
    for workflow_family in sorted(rerun_kits, key=family_order):
        rerun_kit = rerun_kits[workflow_family]
        comparison = comparability[workflow_family]
        requested_language = rerun_kit.public_release_language
        allowed_language = requested_language
        remaining_blockers: list[str] = []

        if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
            allowed_language = "internal_support_only"
        if rerun_kit.primary_spec.run_mode is not BenchmarkRunMode.RAW_EXECUTABLE:
            allowed_language = _narrow_language(
                allowed_language, "review_grade_bounded"
            )
            remaining_blockers.append(
                "primary flagship lane is still not raw-executable in the runtime layer"
            )
        if rerun_kit.companion_spec.run_mode is not BenchmarkRunMode.RAW_EXECUTABLE:
            allowed_language = _narrow_language(
                allowed_language, "review_grade_bounded"
            )
            remaining_blockers.append(
                "companion generalization lane is still not raw-executable in the runtime layer"
            )
        if (
            requested_language != "internal_support_only"
            and rerun_kit.independent_rerun_path is None
        ):
            allowed_language = _narrow_language(
                allowed_language, "review_grade_bounded"
            )
            remaining_blockers.append(
                "no published independent rerun dossier currently backs the family"
            )
        if (
            requested_language != "internal_support_only"
            and rerun_kit.external_review_kit_path is None
        ):
            allowed_language = _narrow_language(
                allowed_language, "review_grade_bounded"
            )
            remaining_blockers.append(
                "no published external review kit currently backs the family"
            )

        primary_audit = audit_by_id[
            next(
                bundle.package_id
                for bundle in iter_benchmark_package_bundles()
                if bundle.workflow_family is workflow_family
                and bundle.package_role == "primary"
            )
        ]
        primary_license = licensing_by_id[primary_audit.package_id]
        artifact_completeness = "complete"
        if not primary_audit.support_files_present or not primary_audit.source_rows:
            artifact_completeness = "incomplete"
            remaining_blockers.append(
                "primary flagship asset audit is missing support files or copied source rows"
            )
        if not primary_license.source_license_notes:
            artifact_completeness = "incomplete"
            remaining_blockers.append(
                "primary flagship licensing story is still too thin to defend redistribution"
            )

        drift_status = comparison.family_stability_label
        if comparison.collapsed_claim_count:
            remaining_blockers.append(
                f"{comparison.collapsed_claim_count} cross-package claim(s) collapse under the companion rerun path"
            )
        rows.append(
            BenchmarkBlackBoxDashboardRow(
                workflow_family=workflow_family,
                requested_language=requested_language,
                allowed_language=allowed_language,
                primary_run_mode=rerun_kit.primary_spec.run_mode.value,
                companion_run_mode=rerun_kit.companion_spec.run_mode.value,
                drift_status=drift_status,
                artifact_completeness=artifact_completeness,
                remaining_blockers=tuple(
                    dict.fromkeys(
                        [*remaining_blockers, *rerun_kit.remaining_limits[:2]]
                    )
                ),
            )
        )
    return tuple(rows)


def _render_rerun_kits(entries: tuple[BenchmarkRerunKitEntry, ...]) -> str:
    lines = [
        "---",
        "title: Benchmark Rerun Kits",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-runtime",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
        "# Benchmark Rerun Kits",
        "",
        "These rerun kits are the shortest path through the shipped package roots and runtime entrypoints for each workflow family. Each kit names the primary package, the companion package, the exact runtime entrypoints, and the review surfaces that still keep the family bounded.",
        "",
    ]
    for entry in entries:
        lines.extend(
            [
                f"## `{entry.workflow_family.value}`",
                "",
                f"- public release language: `{entry.public_release_language}`",
                f"- primary package root: `{entry.primary_package_root}`",
                f"- companion package root: `{entry.companion_package_root}`",
                f"- primary runtime entrypoint: `{entry.primary_spec.canonical_entrypoint}`",
                f"- primary run mode: `{entry.primary_spec.run_mode.value}`",
                f"- companion runtime entrypoint: `{entry.companion_spec.canonical_entrypoint}`",
                f"- companion run mode: `{entry.companion_spec.run_mode.value}`",
                "",
                "Opening order:",
                "",
            ]
        )
        for path in entry.opening_order:
            lines.append(f"- `{path}`")
        lines.extend(
            [
                "",
                "Validating tests:",
                "",
            ]
        )
        for path in entry.validating_test_paths:
            lines.append(f"- `{path}`")
        lines.extend(
            [
                "",
                f"- independent rerun dossier: `{entry.independent_rerun_path or 'not published for this family'}`",
                f"- external review kit: `{entry.external_review_kit_path or 'not published for this family'}`",
                "",
                "Remaining limits:",
                "",
            ]
        )
        for item in entry.remaining_limits:
            lines.append(f"- {item}")
        lines.extend(["", entry.note, ""])
    return "\n".join(lines)


def _render_comparability_matrix(rows: tuple[BenchmarkComparabilityRow, ...]) -> str:
    lines = [
        "---",
        "title: Benchmark Comparability Matrix",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-runtime",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
        "# Benchmark Comparability Matrix",
        "",
        "This matrix states how each workflow family behaves when the public sentence has to survive both the primary flagship package and the companion generalization package.",
        "",
        "| workflow family | public language | primary run mode | companion run mode | stability score | surviving claims | weakened claims | collapsed claims |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"`{row.workflow_family.value}` | `{row.public_release_language}` | "
            f"`{row.primary_run_mode}` | `{row.companion_run_mode}` | "
            f"`{row.family_stability_score}` | `{row.surviving_claim_count}` | "
            f"`{row.weakened_claim_count}` | `{row.collapsed_claim_count}` |"
        )
    lines.extend(["", "## Family Notes", ""])
    for row in rows:
        lines.extend(
            [
                f"### `{row.workflow_family.value}`",
                "",
                f"- primary package root: `{row.primary_package_root}`",
                f"- companion package root: `{row.companion_package_root}`",
                f"- generalization report: `{row.report_path}`",
                f"- stability label: `{row.family_stability_label}`",
                "",
            ]
        )
        for note in row.comparison_notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def _render_black_box_dashboard(
    rows: tuple[BenchmarkBlackBoxDashboardRow, ...],
) -> str:
    lines = [
        "---",
        "title: Black-Box Benchmark Dashboard",
        "audience: mixed",
        "type: explanation",
        "status: canonical",
        "owner: bijux-proteomics-runtime",
        f"last_reviewed: {LAST_REVIEWED}",
        "---",
        "",
        "# Black-Box Benchmark Dashboard",
        "",
        "This dashboard states what the runtime and public benchmark evidence can defend without maintainer narration. It lists every workflow family by current public language, black-box-allowed language, run mode, drift visibility, artifact completeness, and remaining rerun blockers.",
        "",
        "| workflow family | requested language | allowed language | primary run mode | companion run mode | drift status | artifact completeness |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            f"`{row.workflow_family.value}` | `{row.requested_language}` | "
            f"`{row.allowed_language}` | `{row.primary_run_mode}` | "
            f"`{row.companion_run_mode}` | `{row.drift_status}` | "
            f"`{row.artifact_completeness}` |"
        )
    lines.extend(["", "## Remaining Independent-Rerun Blockers", ""])
    for row in rows:
        lines.extend([f"### `{row.workflow_family.value}`", ""])
        for blocker in row.remaining_blockers:
            lines.append(f"- {blocker}")
        lines.append("")
    return "\n".join(lines)


def validate_black_box_benchmark_language() -> tuple[BenchmarkBlackBoxIssue, ...]:
    """Fail when public workflow language outruns black-box benchmark evidence."""

    issues: list[BenchmarkBlackBoxIssue] = []
    for row in build_black_box_benchmark_dashboard():
        if _language_rank(row.allowed_language) < _language_rank(
            row.requested_language
        ):
            issues.append(
                BenchmarkBlackBoxIssue(
                    code="black-box-language-outruns-rerun-evidence",
                    detail=(
                        f"{row.workflow_family.value} still requests {row.requested_language} "
                        f"but the black-box benchmark dashboard only defends {row.allowed_language}"
                    ),
                )
            )
    return tuple(issues)


def _write_text(path: Path, text: str) -> int:
    rendered = text.rstrip() + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return 0
    path.write_text(rendered, encoding="utf-8")
    return 1


def run(*, check: bool = False) -> int:
    """Write or verify runtime-facing benchmark rerun and comparability pages."""

    rendered = {
        BENCHMARK_RERUN_KITS_PATH: _render_rerun_kits(build_benchmark_rerun_kits()),
        BENCHMARK_COMPARABILITY_MATRIX_PATH: _render_comparability_matrix(
            build_benchmark_comparability_matrix()
        ),
        BLACK_BOX_BENCHMARK_DASHBOARD_PATH: _render_black_box_dashboard(
            build_black_box_benchmark_dashboard()
        ),
    }
    changed = 0
    for path, text in rendered.items():
        rendered_text = text.rstrip() + "\n"
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != rendered_text:
                return 1
            continue
        changed += _write_text(path, text)
    return 0 if check or changed >= 0 else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bijux-proteomics benchmark-rerun-governance",
        description=(
            "Generate or verify runtime-facing benchmark rerun and comparability pages."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that the checked-in runtime handbook pages match generated content",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return run(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
