# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow authority matrix for flagship and internal-support proteomics families."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.flagship_acceptance import (
    build_flagship_acceptance_sheet,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.reviews.benchmarks import (
    WorkflowBenchmarkReview,
    build_dda_benchmark_review,
    build_dia_benchmark_review,
    build_lfq_benchmark_review,
    build_multiplex_benchmark_review,
    build_ptm_benchmark_review,
    build_targeted_benchmark_review,
)
from bijux_proteomics_intelligence.reviews.outsider_packets import (
    FlagshipOutsiderReviewPacket,
    build_flagship_outsider_review_packet_family,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    BenchmarkManifest,
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.comparator_failures import (
    ComparatorClaimSupportState,
)
from bijux_proteomics_knowledge.references.workflows.reference_support import (
    get_benchmark_manifest_for_family,
)
from bijux_proteomics_lab.benchmarks.follow_up import (
    FlagshipLabFollowUpPacket,
    build_flagship_lab_follow_up_packet_family,
)
from bijux_proteomics_lab.benchmarks.outcome_dossiers import (
    FlagshipAssayWorthLedgerEntry,
    FlagshipFollowUpOutcomeDossier,
    build_flagship_assay_worth_ledger,
    build_flagship_follow_up_outcome_dossier_family,
)
from bijux_proteomics_runtime.workflows import (
    BenchmarkRunMode,
    BenchmarkRunSpec,
    BenchmarkRuntimeTruthRow,
    build_benchmark_run_specs,
    build_benchmark_runtime_truth_surface,
)

__all__ = [
    "WorkflowAuthorityCell",
    "WorkflowAuthorityKind",
    "WorkflowAuthorityMatrix",
    "WorkflowAuthorityRow",
    "build_workflow_authority_matrix",
]


class WorkflowAuthorityKind(StrEnum):
    """Stable identifiers for authority cells inside the workflow matrix."""

    INTERNAL_BENCHMARK_BACKED = "internal_benchmark_backed"
    RAW_EXECUTABLE = "raw_executable"
    EXTERNALLY_CROSS_CHECKED = "externally_cross_checked"
    OUTSIDER_AUDITABLE = "outsider_auditable"
    LAB_CONSEQUENTIAL = "lab_consequential"


class WorkflowAuthorityCell(JsonModel):
    """One earned or unearned authority cell for a workflow family."""

    model_config = ConfigDict(extra="forbid")

    authority_kind: WorkflowAuthorityKind
    earned: bool
    artifact_paths: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowAuthorityRow(JsonModel):
    """One workflow-family authority row spanning public and internal postures."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: KnowledgeWorkflowFamily
    public_release_language: str = Field(..., min_length=1)
    cells: tuple[WorkflowAuthorityCell, ...] = Field(default_factory=tuple)
    blocked_claims: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class WorkflowAuthorityMatrix(JsonModel):
    """Matrix of authority earned by each flagship workflow family."""

    model_config = ConfigDict(extra="forbid")

    matrix_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    rows: tuple[WorkflowAuthorityRow, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


_WORKFLOW_FAMILIES: tuple[KnowledgeWorkflowFamily, ...] = (
    KnowledgeWorkflowFamily.DDA,
    KnowledgeWorkflowFamily.DIA,
    KnowledgeWorkflowFamily.LFQ,
    KnowledgeWorkflowFamily.MULTIPLEX,
    KnowledgeWorkflowFamily.PTM,
    KnowledgeWorkflowFamily.TARGETED,
)


@lru_cache(maxsize=1)
def _reviews() -> dict[KnowledgeWorkflowFamily, WorkflowBenchmarkReview]:
    return {
        review.workflow_family: review
        for review in (
            build_dda_benchmark_review(),
            build_dia_benchmark_review(),
            build_lfq_benchmark_review(),
            build_multiplex_benchmark_review(),
            build_ptm_benchmark_review(),
            build_targeted_benchmark_review(),
        )
    }


@lru_cache(maxsize=1)
def _outsider_packets() -> dict[KnowledgeWorkflowFamily, FlagshipOutsiderReviewPacket]:
    family = build_flagship_outsider_review_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


@lru_cache(maxsize=1)
def _lab_packets() -> dict[KnowledgeWorkflowFamily, FlagshipLabFollowUpPacket]:
    family = build_flagship_lab_follow_up_packet_family()
    return {packet.workflow_family: packet for packet in family.packets}


@lru_cache(maxsize=1)
def _lab_outcome_dossiers() -> dict[
    KnowledgeWorkflowFamily, FlagshipFollowUpOutcomeDossier
]:
    family = build_flagship_follow_up_outcome_dossier_family()
    return {dossier.workflow_family: dossier for dossier in family.dossiers}


@lru_cache(maxsize=1)
def _worth_ledger_entries() -> dict[
    KnowledgeWorkflowFamily, FlagshipAssayWorthLedgerEntry
]:
    ledger = build_flagship_assay_worth_ledger()
    return {entry.workflow_family: entry for entry in ledger.entries}


@lru_cache(maxsize=1)
def _runtime_rows() -> dict[str, BenchmarkRuntimeTruthRow]:
    return {row.workflow_family: row for row in build_benchmark_runtime_truth_surface()}


@lru_cache(maxsize=1)
def _runtime_specs() -> dict[str, BenchmarkRunSpec]:
    return {spec.package_id: spec for spec in build_benchmark_run_specs()}


def build_workflow_authority_matrix() -> WorkflowAuthorityMatrix:
    """Build the release-facing workflow authority matrix across all six families."""

    rows = tuple(_build_row(workflow_family) for workflow_family in _WORKFLOW_FAMILIES)
    return WorkflowAuthorityMatrix(
        matrix_id="workflow-authority-matrix",
        artifact_path="artifacts/intelligence/reviews/workflow_authority_matrix.json",
        rows=rows,
        note=(
            "This matrix is the release-facing authority source of truth for which workflow "
            "families are only benchmark-backed internally, which are raw-executable, which are "
            "externally cross-checked, which are outsider-auditable, and which have real lab "
            "consequence surfaces."
        ),
    )


def _build_row(workflow_family: KnowledgeWorkflowFamily) -> WorkflowAuthorityRow:
    manifest = get_benchmark_manifest_for_family(workflow_family)
    review = _reviews()[workflow_family]
    outsider_packet = _outsider_packets().get(workflow_family)
    lab_packet = _lab_packets().get(workflow_family)
    outcome_dossier = _lab_outcome_dossiers().get(workflow_family)
    worth_entry = _worth_ledger_entries().get(workflow_family)
    runtime_row = _runtime_row_for_family(workflow_family)
    runtime_spec = (
        _runtime_specs()[runtime_row.package_id]
        if runtime_row is not None and runtime_row.package_id in _runtime_specs()
        else None
    )
    public_release_language = (
        "internal_support_only"
        if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX
        else "outsider_auditable_bounded"
    )
    blocked_claims = _blocked_claims(
        workflow_family=workflow_family,
        review=review,
        outsider_packet=outsider_packet,
        lab_packet=lab_packet,
        outcome_dossier=outcome_dossier,
        worth_entry=worth_entry,
    )
    return WorkflowAuthorityRow(
        workflow_family=workflow_family,
        public_release_language=public_release_language,
        cells=(
            _internal_benchmark_backed_cell(manifest),
            _raw_executable_cell(runtime_row=runtime_row, runtime_spec=runtime_spec),
            _externally_cross_checked_cell(
                workflow_family=workflow_family,
                review=review,
                manifest=manifest,
                runtime_spec=runtime_spec,
            ),
            _outsider_auditable_cell(
                workflow_family=workflow_family,
                outsider_packet=outsider_packet,
                runtime_spec=runtime_spec,
            ),
            _lab_consequential_cell(
                workflow_family=workflow_family,
                lab_packet=lab_packet,
                outcome_dossier=outcome_dossier,
                worth_entry=worth_entry,
            ),
        ),
        blocked_claims=blocked_claims,
        note=(
            "Multiplex is intentionally narrowed to internal support only. The other flagship "
            "families now earn bounded outsider-auditable posture, not decision-grade or "
            "vendor-parity authority."
            if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX
            else "This workflow family earns bounded outsider-auditable posture, but its explicit blocked claims still cap the public language."
        ),
    )


def _internal_benchmark_backed_cell(
    manifest: BenchmarkManifest,
) -> WorkflowAuthorityCell:
    package = manifest.benchmark_package
    artifact_paths: tuple[str, ...] = ()
    if package is not None and package.package_artifacts:
        first_artifact = Path(package.package_artifacts[0].repo_relative_path)
        package_root = first_artifact.parent.parent.as_posix()
        artifact_paths = (
            f"{package_root}/package_manifest.json",
            f"{package_root}/artifact_inventory.json",
        )
    return WorkflowAuthorityCell(
        authority_kind=WorkflowAuthorityKind.INTERNAL_BENCHMARK_BACKED,
        earned=package is not None,
        artifact_paths=artifact_paths,
        note=(
            "A workflow is benchmark-backed only when it has a tracked flagship public package "
            "and inventory inside the product-owned benchmark asset root."
        ),
    )


def _raw_executable_cell(
    *,
    runtime_row: BenchmarkRuntimeTruthRow | None,
    runtime_spec: BenchmarkRunSpec | None,
) -> WorkflowAuthorityCell:
    raw_executable = (
        runtime_row is not None
        and runtime_row.run_mode is BenchmarkRunMode.RAW_EXECUTABLE
    )
    artifact_paths = ()
    if runtime_spec is not None:
        artifact_paths = (
            runtime_spec.primary_input_path,
            *runtime_spec.public_package_paths[:1],
        )
    return WorkflowAuthorityCell(
        authority_kind=WorkflowAuthorityKind.RAW_EXECUTABLE,
        earned=raw_executable,
        artifact_paths=artifact_paths,
        note=(
            "Raw-executable authority is earned only when the strongest current runtime lane "
            "runs the flagship package directly rather than stopping at an import-only bridge."
        ),
    )


def _externally_cross_checked_cell(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    review: WorkflowBenchmarkReview,
    manifest: BenchmarkManifest,
    runtime_spec: BenchmarkRunSpec | None,
) -> WorkflowAuthorityCell:
    earned = (
        review.public_claim_support_state is not ComparatorClaimSupportState.REFUSED
    )
    artifact_paths: list[str] = []
    if (
        manifest.benchmark_package is not None
        and manifest.benchmark_package.package_artifacts
    ):
        first_artifact = Path(
            manifest.benchmark_package.package_artifacts[0].repo_relative_path
        )
        artifact_paths.append(
            f"{first_artifact.parent.parent.as_posix()}/package_manifest.json"
        )
    if runtime_spec is not None:
        artifact_paths.extend(runtime_spec.companion_input_paths[:2])
    return WorkflowAuthorityCell(
        authority_kind=WorkflowAuthorityKind.EXTERNALLY_CROSS_CHECKED,
        earned=earned,
        artifact_paths=tuple(dict.fromkeys(artifact_paths)),
        note=(
            "Externally cross-checked authority is earned only when the public comparator posture "
            "is at least advisory instead of refused."
            if earned
            else "This workflow still lacks externally cross-checked authority because its public comparator posture remains refused."
        ),
    )


def _outsider_auditable_cell(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    outsider_packet: FlagshipOutsiderReviewPacket | None,
    runtime_spec: BenchmarkRunSpec | None,
) -> WorkflowAuthorityCell:
    acceptance_sheet = build_flagship_acceptance_sheet(workflow_family)
    earned = (
        outsider_packet.complete_outsider_surface
        if outsider_packet is not None
        else False
    )
    artifact_paths = [
        link.repo_relative_path
        for link in (
            outsider_packet.primary_data_links[:3]
            if outsider_packet is not None
            else ()
        )
    ]
    artifact_paths.append(acceptance_sheet.artifact_path)
    if runtime_spec is not None:
        artifact_paths.extend(runtime_spec.public_package_paths[:1])
    return WorkflowAuthorityCell(
        authority_kind=WorkflowAuthorityKind.OUTSIDER_AUDITABLE,
        earned=earned,
        artifact_paths=tuple(dict.fromkeys(artifact_paths)),
        note=(
            "This workflow family ships enough benchmark, runtime, recommendation, lab, and acceptance-sheet evidence to support bounded outsider review."
            if earned
            else "This workflow family does not currently earn outsider-auditable language because the outsider packet or acceptance sheet still fails."
        ),
    )


def _lab_consequential_cell(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    lab_packet: FlagshipLabFollowUpPacket | None,
    outcome_dossier: FlagshipFollowUpOutcomeDossier | None,
    worth_entry: FlagshipAssayWorthLedgerEntry | None,
) -> WorkflowAuthorityCell:
    earned = (
        lab_packet is not None
        and outcome_dossier is not None
        and worth_entry is not None
    )
    artifact_paths: tuple[str, ...] = ()
    if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX or earned:
        artifact_paths = tuple(
            dict.fromkeys(
                path
                for path in (
                    "packages/bijux-proteomics-lab/src/bijux_proteomics_lab/benchmarks/follow_up.py",
                    outcome_dossier.artifact_path
                    if outcome_dossier is not None
                    else "",
                    build_flagship_assay_worth_ledger().artifact_path
                    if worth_entry is not None
                    else "",
                )
                if path
            )
        )
    return WorkflowAuthorityCell(
        authority_kind=WorkflowAuthorityKind.LAB_CONSEQUENTIAL,
        earned=earned,
        artifact_paths=artifact_paths,
        note=(
            "The lab consequence surface is earned only when a dedicated flagship lab packet, one shipped requested-versus-observed dossier, and one assay-worth-it ledger row all exist together."
            if earned
            else "This workflow still lacks the shipped outcome dossier and assay-worth-it evidence required for lab-consequential public authority."
        ),
    )


def _blocked_claims(
    *,
    workflow_family: KnowledgeWorkflowFamily,
    review: WorkflowBenchmarkReview,
    outsider_packet: FlagshipOutsiderReviewPacket | None,
    lab_packet: FlagshipLabFollowUpPacket | None,
    outcome_dossier: FlagshipFollowUpOutcomeDossier | None,
    worth_entry: FlagshipAssayWorthLedgerEntry | None,
) -> tuple[str, ...]:
    blocked = list(review.scientific_limits[:4])
    blocked.extend(review.reviewer_grounding_limits[:2])
    if outsider_packet is not None:
        blocked.extend(outsider_packet.known_limits[:3])
    if lab_packet is not None:
        blocked.extend(lab_packet.stop_reasons[:2])
    if outcome_dossier is None:
        blocked.append(
            "no shipped requested-versus-observed lab outcome dossier exists yet"
        )
    if worth_entry is None:
        blocked.append("no shipped assay-worth-it ledger row exists yet")
    if workflow_family is KnowledgeWorkflowFamily.MULTIPLEX:
        blocked.append(
            "multiplex does not ride with outsider-auditable flagship families until a dedicated lab outcome dossier, assay-worth-it ledger row, and outsider decision brief are all shipped"
        )
    return tuple(dict.fromkeys(blocked))


def _runtime_row_for_family(
    workflow_family: KnowledgeWorkflowFamily,
) -> BenchmarkRuntimeTruthRow | None:
    runtime_family = {
        KnowledgeWorkflowFamily.DDA: "dda_import",
        KnowledgeWorkflowFamily.DIA: "dia_import",
        KnowledgeWorkflowFamily.LFQ: "quant_review",
        KnowledgeWorkflowFamily.MULTIPLEX: "multiplex_review",
        KnowledgeWorkflowFamily.PTM: "ptm_review",
        KnowledgeWorkflowFamily.TARGETED: "targeted_review",
    }[workflow_family]
    return _runtime_rows().get(runtime_family)
