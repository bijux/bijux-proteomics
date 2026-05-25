# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Scientific result diffs over completed runtime runs."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow import (
    InteractiveResultPathwayComparisonEntry,
    InteractiveResultProteinComparisonEntry,
    InteractiveResultPtmSiteComparisonEntry,
    InteractiveResultQcComparisonEntry,
    ProteomicsStudyConclusionEntry,
    ProteomicsStudyConclusionKind,
    build_interactive_result_comparison_payload,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.rehydrate import load_completed_run


class RunConfidenceTierDiffEntry(JsonModel):
    """One changed biological confidence tier across two completed runs."""

    model_config = ConfigDict(extra="forbid")

    conclusion_id: str = Field(..., min_length=1)
    conclusion_kind: str = Field(..., min_length=1)
    subject_id: str = Field(..., min_length=1)
    subject_label: str = Field(..., min_length=1)
    left_confidence_tier: str | None = None
    right_confidence_tier: str | None = None
    left_confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    right_confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class CompletedRunScientificDiffSummary(JsonModel):
    """Compact counts over one completed-run scientific diff."""

    model_config = ConfigDict(extra="forbid")

    changed_protein_count: int = Field(..., ge=0)
    changed_ptm_site_count: int = Field(..., ge=0)
    changed_pathway_count: int = Field(..., ge=0)
    changed_qc_decision_count: int = Field(..., ge=0)
    changed_confidence_tier_count: int = Field(..., ge=0)
    total_change_count: int = Field(..., ge=0)


class CompletedRunScientificDiffReport(JsonModel):
    """Stable scientific diff over two completed runtime runs."""

    model_config = ConfigDict(extra="forbid")

    left_run_dir: str = Field(..., min_length=1)
    right_run_dir: str = Field(..., min_length=1)
    changed_proteins: tuple[InteractiveResultProteinComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    changed_ptm_sites: tuple[InteractiveResultPtmSiteComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    changed_pathways: tuple[InteractiveResultPathwayComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    changed_qc_decisions: tuple[InteractiveResultQcComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    changed_confidence_tiers: tuple[RunConfidenceTierDiffEntry, ...] = Field(
        default_factory=tuple
    )
    summary: CompletedRunScientificDiffSummary
    note: str = Field(..., min_length=1)


def diff_completed_runs(run_a: Path, run_b: Path) -> CompletedRunScientificDiffReport:
    """Compare completed runs through rehydrated scientific result surfaces only."""

    left_result = load_completed_run(run_a)
    right_result = load_completed_run(run_b)
    if left_result.interactive_result_bundle is None:
        raise ValueError("left completed run is missing an interactive result bundle")
    if right_result.interactive_result_bundle is None:
        raise ValueError("right completed run is missing an interactive result bundle")

    bundle_diff = build_interactive_result_comparison_payload(
        left_result.interactive_result_bundle,
        right_result.interactive_result_bundle,
    )
    confidence_tier_changes = _build_confidence_tier_changes(
        left_result.biological_conclusions,
        right_result.biological_conclusions,
    )
    total_change_count = (
        len(bundle_diff.changed_proteins)
        + len(bundle_diff.changed_ptm_sites)
        + len(bundle_diff.changed_pathways)
        + len(bundle_diff.changed_qc_entries)
        + len(confidence_tier_changes)
    )
    return CompletedRunScientificDiffReport(
        left_run_dir=str(run_a),
        right_run_dir=str(run_b),
        changed_proteins=bundle_diff.changed_proteins,
        changed_ptm_sites=bundle_diff.changed_ptm_sites,
        changed_pathways=bundle_diff.changed_pathways,
        changed_qc_decisions=bundle_diff.changed_qc_entries,
        changed_confidence_tiers=confidence_tier_changes,
        summary=CompletedRunScientificDiffSummary(
            changed_protein_count=len(bundle_diff.changed_proteins),
            changed_ptm_site_count=len(bundle_diff.changed_ptm_sites),
            changed_pathway_count=len(bundle_diff.changed_pathways),
            changed_qc_decision_count=len(bundle_diff.changed_qc_entries),
            changed_confidence_tier_count=len(confidence_tier_changes),
            total_change_count=total_change_count,
        ),
        note=(
            "completed run scientific diffs compare rehydrated proteins, PTM sites, "
            "pathways, QC decisions, and biological hypothesis confidence tiers "
            "instead of reacting to runtime-only timestamp drift"
        ),
    )


def _build_confidence_tier_changes(
    left_conclusions: tuple[ProteomicsStudyConclusionEntry, ...],
    right_conclusions: tuple[ProteomicsStudyConclusionEntry, ...],
) -> tuple[RunConfidenceTierDiffEntry, ...]:
    left_by_key = {
        _conclusion_key(entry): entry
        for entry in left_conclusions
        if entry.kind is ProteomicsStudyConclusionKind.BIOLOGICAL_HYPOTHESIS
    }
    right_by_key = {
        _conclusion_key(entry): entry
        for entry in right_conclusions
        if entry.kind is ProteomicsStudyConclusionKind.BIOLOGICAL_HYPOTHESIS
    }
    entries: list[RunConfidenceTierDiffEntry] = []
    for key in sorted(set(left_by_key) | set(right_by_key)):
        left_entry = left_by_key.get(key)
        right_entry = right_by_key.get(key)
        left_tier = None if left_entry is None else left_entry.status
        right_tier = None if right_entry is None else right_entry.status
        if left_tier == right_tier:
            continue
        exemplar = left_entry or right_entry
        if exemplar is None:
            continue
        entries.append(
            RunConfidenceTierDiffEntry(
                conclusion_id=exemplar.conclusion_id,
                conclusion_kind=exemplar.kind.value,
                subject_id=exemplar.subject_id,
                subject_label=exemplar.subject_label,
                left_confidence_tier=left_tier,
                right_confidence_tier=right_tier,
                left_confidence_score=None if left_entry is None else left_entry.score,
                right_confidence_score=None if right_entry is None else right_entry.score,
                note=_confidence_change_note(left_entry, right_entry),
            )
        )
    return tuple(entries)


def _conclusion_key(entry: ProteomicsStudyConclusionEntry) -> tuple[str, str, str]:
    return (entry.kind.value, entry.conclusion_id, entry.subject_id)


def _confidence_change_note(
    left_entry: ProteomicsStudyConclusionEntry | None,
    right_entry: ProteomicsStudyConclusionEntry | None,
) -> str:
    if left_entry is None and right_entry is not None:
        return "biological hypothesis confidence appears only in the right completed run"
    if left_entry is not None and right_entry is None:
        return "biological hypothesis confidence appears only in the left completed run"
    assert left_entry is not None
    assert right_entry is not None
    return (
        "biological hypothesis confidence tier changed across completed runs after "
        "rehydrating archived scientific conclusions"
    )


__all__ = [
    "CompletedRunScientificDiffReport",
    "CompletedRunScientificDiffSummary",
    "RunConfidenceTierDiffEntry",
    "diff_completed_runs",
]
