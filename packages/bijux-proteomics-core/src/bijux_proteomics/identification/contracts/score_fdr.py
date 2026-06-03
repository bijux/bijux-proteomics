# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Score-orientation, calibration, and base FDR contracts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics._scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationIssue,
    build_psm_table_schema,
    validate_scientific_table,
)
from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
    TargetDecoyState,
)
from bijux_proteomics.domain.records import (
    ModifiedPeptide as CanonicalModifiedPeptide,
)
from bijux_proteomics.domain.records import (
    PeptideRecord as CanonicalPeptideRecord,
)
from bijux_proteomics.domain.records import (
    ProteinGroup as CanonicalProteinGroup,
)
from bijux_proteomics.domain.records import (
    ProteinRecord as CanonicalProteinRecord,
)
from bijux_proteomics.domain.records import (
    PSMRecord as CanonicalPsmRecord,
)
from bijux_proteomics.domain.records import (
    RejectedEvidence as CanonicalRejectedEvidence,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    build_peptide_uniqueness_index,
)

if TYPE_CHECKING:
    from bijux_proteomics.identification.cross_run_reproducibility import (
        RunDetectionContext,
    )
from bijux_proteomics._tabular import render_rows_tsv
from bijux_proteomics.identification.contracts.evidence import (
    rollup_peptide_evidence,
    rollup_protein_evidence,
)
from bijux_proteomics.identification.contracts.psm import (
    PsmRecord,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    _raise_on_target_decoy_accession_collisions,
)
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class FdrPolicy(JsonModel):
    """Stable policy for basic target-decoy FDR evaluation."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(
        default="higher_better", pattern="^(higher_better|lower_better)$"
    )
    tie_handling: str = Field(
        default="score_group", pattern="^(score_group|stable_record_order)$"
    )
    threshold: float | None = Field(default=None, ge=0.0)
    decoy_policy: TargetDecoyLabelPolicy = Field(default_factory=TargetDecoyLabelPolicy)


class FdrAnnotatedPsm(JsonModel):
    """PSM record plus cumulative target-decoy FDR state."""

    model_config = ConfigDict(extra="forbid")

    psm: PsmRecord
    rank: int = Field(..., ge=1)
    tie_group_rank: int = Field(..., ge=1)
    tie_group_size: int = Field(..., ge=1)
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool = True


class NormalizedScoreEntry(JsonModel):
    """One PSM score normalized onto an orientation-stable rank scale."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    raw_score: float
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    rank: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel


class CalibrationPlotBin(JsonModel):
    """One score-calibration bin over normalized target-decoy evidence."""

    model_config = ConfigDict(extra="forbid")

    bin_lower: float = Field(..., ge=0.0, le=1.0)
    bin_upper: float = Field(..., ge=0.0, le=1.0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)
    unknown_count: int = Field(..., ge=0)
    decoy_fraction: float = Field(..., ge=0.0)


class CalibrationPlotData(JsonModel):
    """Plot-ready calibration data for one scored target-decoy ranking."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    total_psms: int = Field(..., ge=0)
    bins: tuple[CalibrationPlotBin, ...] = Field(default_factory=tuple)


class _CalibrationEvidenceRecord(JsonModel):
    """Internal scored evidence row for calibration across supported levels."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    sort_token: str = Field(..., min_length=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel


class ScoreOrientationAdvisoryCandidate(JsonModel):
    """One candidate explanation for a score-orientation recommendation."""

    model_config = ConfigDict(extra="forbid")

    orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    top_ranked_count: int = Field(..., ge=0)
    top_target_count: int = Field(..., ge=0)
    top_decoy_count: int = Field(..., ge=0)
    top_mean_q_value: float | None = Field(default=None, ge=0.0)
    support_score: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class ScoreOrientationAdvisory(JsonModel):
    """Advisory recommendation over score orientation, never an enforced choice."""

    model_config = ConfigDict(extra="forbid")

    advisory_only: bool = True
    recommended_orientation: str | None = Field(
        default=None, pattern="^(higher_better|lower_better)$"
    )
    support_gap: float = Field(..., ge=0.0, le=1.0)
    candidates: tuple[ScoreOrientationAdvisoryCandidate, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


class FdrAuditEntry(JsonModel):
    """One sorted FDR-audit row with cumulative derivation state."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., ge=1)
    tie_group_rank: int = Field(..., ge=1)
    tie_group_size: int = Field(..., ge=1)
    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    raw_score: float
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    target_decoy_label: TargetDecoyLabel
    cumulative_targets: int = Field(..., ge=0)
    cumulative_decoys: int = Field(..., ge=0)
    fdr: float = Field(..., ge=0.0)
    q_value: float = Field(..., ge=0.0)
    accepted: bool


class FdrAuditTrail(JsonModel):
    """Stable audit payload for one target-decoy FDR calculation."""

    model_config = ConfigDict(extra="forbid")

    policy: FdrPolicy
    entries: tuple[FdrAuditEntry, ...] = Field(default_factory=tuple)
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)


class FdrEvidenceLevel(StrEnum):
    """Supported evidence levels for level-specific FDR reporting."""

    PSM = "psm"
    PEPTIDE = "peptide"
    PROTEIN = "protein"


class FdrLevelEntry(JsonModel):
    """One FDR-annotated entity at the PSM, peptide, or protein level."""

    model_config = ConfigDict(extra="forbid")

    evidence_level: FdrEvidenceLevel
    entity_id: str = Field(..., min_length=1)
    score: float
    q_value: float = Field(..., ge=0.0)
    fdr: float = Field(..., ge=0.0)
    rank: int = Field(..., ge=1)
    accepted: bool
    target_decoy_label: TargetDecoyLabel
    member_count: int = Field(..., ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class FdrEdgeCaseKind(StrEnum):
    """Explicit edge-case classification for target-decoy result sets."""

    MIXED = "mixed"
    ALL_TARGET = "all_target"
    ALL_DECOY = "all_decoy"
    NO_DECOY = "no_decoy"
    EMPTY = "empty"


class FdrEdgeCaseReport(JsonModel):
    """Structured report for notable target-decoy edge cases."""

    model_config = ConfigDict(extra="forbid")

    kind: FdrEdgeCaseKind
    total_records: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)
    unknown_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class GroupedFdrBucket(JsonModel):
    """One grouped-FDR bucket with its own ranked entries."""

    model_config = ConfigDict(extra="forbid")

    group_key: str = Field(..., min_length=1)
    entries: tuple[FdrLevelEntry, ...] = Field(default_factory=tuple)


class GroupedFdrReport(JsonModel):
    """Stable grouped-FDR report across multiple evidence buckets."""

    model_config = ConfigDict(extra="forbid")

    group_by: str = Field(..., pattern="^(charge_state|modification_state)$")
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    threshold: float | None = Field(default=None, ge=0.0)
    groups: tuple[GroupedFdrBucket, ...] = Field(default_factory=tuple)


class ConfidenceCalibrationLevel(StrEnum):
    """Evidence levels supported by the calibration assessment surface."""

    PSM = "psm"
    PEPTIDE = "peptide"
    PROTEIN = "protein"


class ConfidenceCalibrationEntry(JsonModel):
    """Calibration-aware confidence summary beyond raw q-values."""

    model_config = ConfigDict(extra="forbid")

    evidence_level: ConfidenceCalibrationLevel
    entity_id: str = Field(..., min_length=1)
    q_value: float | None = Field(default=None, ge=0.0)
    normalized_score: float = Field(..., ge=0.0, le=1.0)
    calibration_bin_lower: float = Field(..., ge=0.0, le=1.0)
    calibration_bin_upper: float = Field(..., ge=0.0, le=1.0)
    empirical_decoy_fraction: float = Field(..., ge=0.0, le=1.0)
    support_score: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class ConfidenceCalibrationReport(JsonModel):
    """Calibration assessment that keeps empirical decoy context beside q-values."""

    model_config = ConfigDict(extra="forbid")

    evidence_level: ConfidenceCalibrationLevel
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    entries: tuple[ConfidenceCalibrationEntry, ...] = Field(default_factory=tuple)
    calibration_plot: CalibrationPlotData


def calculate_basic_target_decoy_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> tuple[FdrAnnotatedPsm, ...]:
    """Annotate PSMs with cumulative target-decoy FDR and monotonic q-values."""
    from bijux_proteomics.identification.psm_target_decoy_fdr import (
        build_psm_target_decoy_fdr_report,
    )

    _raise_on_target_decoy_accession_collisions(records, decoy_policy=decoy_policy)
    report = build_psm_target_decoy_fdr_report(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
    )
    return tuple(
        FdrAnnotatedPsm(
            psm=entry.psm,
            rank=entry.rank,
            tie_group_rank=entry.tie_group_rank,
            tie_group_size=entry.tie_group_size,
            cumulative_targets=entry.cumulative_targets,
            cumulative_decoys=entry.cumulative_decoys,
            fdr=entry.raw_fdr,
            q_value=entry.q_value,
            accepted=entry.accepted,
        )
        for entry in report.entries
    )


def normalize_psm_score_orientation(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
) -> tuple[NormalizedScoreEntry, ...]:
    """Normalize scores onto a stable best-to-worst rank scale."""
    return _normalize_calibration_score_orientation(
        tuple(
            _CalibrationEvidenceRecord(
                entity_id=record.spectrum_id,
                sort_token=record.canonical_peptide,
                score=record.score,
                q_value=record.q_value,
                target_decoy_label=record.target_decoy_label,
            )
            for record in records
        ),
        score_orientation=score_orientation,
    )


def _normalize_calibration_score_orientation(
    records: tuple[_CalibrationEvidenceRecord, ...],
    *,
    score_orientation: str = "higher_better",
) -> tuple[NormalizedScoreEntry, ...]:
    """Normalize generic calibration evidence onto a stable rank scale."""
    if score_orientation not in {"higher_better", "lower_better"}:
        raise ValueError("score_orientation must be 'higher_better' or 'lower_better'")

    sorted_records = tuple(
        sorted(
            records,
            key=(
                (
                    lambda record: (
                        -record.score,
                        record.entity_id,
                        record.sort_token,
                    )
                )
                if score_orientation == "higher_better"
                else (
                    lambda record: (
                        record.score,
                        record.entity_id,
                        record.sort_token,
                    )
                )
            ),
        )
    )
    if not sorted_records:
        return ()

    denominator = max(len(sorted_records) - 1, 1)
    normalized_entries: list[NormalizedScoreEntry] = []
    for rank, record in enumerate(sorted_records, start=1):
        normalized_score = (
            1.0 if len(sorted_records) == 1 else 1.0 - ((rank - 1) / denominator)
        )
        normalized_entries.append(
            NormalizedScoreEntry(
                spectrum_id=record.entity_id,
                canonical_peptide=record.sort_token,
                raw_score=record.score,
                normalized_score=normalized_score,
                rank=rank,
                target_decoy_label=record.target_decoy_label,
            )
        )
    return tuple(normalized_entries)


def _score_sorted_psm_records(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str,
) -> tuple[PsmRecord, ...]:
    if score_orientation == "higher_better":
        key_fn = lambda record: (  # noqa: E731
            -record.score,
            record.spectrum_id,
            record.canonical_peptide,
            record.charge,
        )
    else:
        key_fn = lambda record: (  # noqa: E731
            record.score,
            record.spectrum_id,
            record.canonical_peptide,
            record.charge,
        )
    return tuple(sorted(records, key=key_fn))


def _score_orientation_support_candidate(
    records: tuple[PsmRecord, ...],
    *,
    orientation: str,
    top_fraction: float,
) -> ScoreOrientationAdvisoryCandidate:
    sorted_records = _score_sorted_psm_records(
        records,
        score_orientation=orientation,
    )
    top_count = (
        max(1, math.ceil(len(sorted_records) * top_fraction)) if sorted_records else 0
    )
    top_records = sorted_records[:top_count]
    top_target_count = sum(
        1
        for record in top_records
        if record.target_decoy_label is TargetDecoyLabel.TARGET
    )
    top_decoy_count = sum(
        1
        for record in top_records
        if record.target_decoy_label is TargetDecoyLabel.DECOY
    )
    q_values = [record.q_value for record in top_records if record.q_value is not None]
    top_mean_q_value = sum(q_values) / len(q_values) if q_values else None
    labeled_count = top_target_count + top_decoy_count
    decoy_fraction = top_decoy_count / labeled_count if labeled_count else 0.5
    q_component = 1.0 - min(
        top_mean_q_value if top_mean_q_value is not None else 0.5, 1.0
    )
    support_score = max(0.0, min(1.0, ((1.0 - decoy_fraction) + q_component) / 2.0))
    return ScoreOrientationAdvisoryCandidate(
        orientation=orientation,
        top_ranked_count=top_count,
        top_target_count=top_target_count,
        top_decoy_count=top_decoy_count,
        top_mean_q_value=top_mean_q_value,
        support_score=support_score,
        note=(
            "candidate support is derived from target-decoy enrichment and q-value concentration near the top ranks"
        ),
    )


def detect_score_orientation_advisory(
    records: tuple[PsmRecord, ...],
    *,
    top_fraction: float = 0.25,
) -> ScoreOrientationAdvisory:
    """Recommend a score orientation as advisory evidence, never as an enforced rule."""
    if not 0.0 < top_fraction <= 1.0:
        raise ValueError("top_fraction must be greater than 0 and at most 1")

    higher = _score_orientation_support_candidate(
        records,
        orientation="higher_better",
        top_fraction=top_fraction,
    )
    lower = _score_orientation_support_candidate(
        records,
        orientation="lower_better",
        top_fraction=top_fraction,
    )
    sorted_candidates = sorted(
        (higher, lower),
        key=lambda candidate: (-candidate.support_score, candidate.orientation),
    )
    support_gap = (
        sorted_candidates[0].support_score - sorted_candidates[1].support_score
    )
    recommended_orientation = (
        sorted_candidates[0].orientation if support_gap >= 0.05 else None
    )
    note = (
        f"advisory evidence favors {recommended_orientation}"
        if recommended_orientation is not None
        else "advisory evidence is too balanced to recommend one score orientation"
    )
    return ScoreOrientationAdvisory(
        advisory_only=True,
        recommended_orientation=recommended_orientation,
        support_gap=support_gap,
        candidates=tuple(sorted_candidates),
        note=note,
    )


def _records_for_confidence_calibration(
    records: tuple[PsmRecord, ...],
    *,
    evidence_level: ConfidenceCalibrationLevel,
) -> tuple[_CalibrationEvidenceRecord, ...]:
    if evidence_level is ConfidenceCalibrationLevel.PSM:
        return tuple(
            _CalibrationEvidenceRecord(
                entity_id=record.spectrum_id,
                sort_token=record.canonical_peptide,
                score=record.score,
                q_value=record.q_value,
                target_decoy_label=record.target_decoy_label,
            )
            for record in records
        )
    if evidence_level is ConfidenceCalibrationLevel.PEPTIDE:
        rollups = rollup_peptide_evidence(records)
        return tuple(
            _CalibrationEvidenceRecord(
                entity_id=entry.canonical_peptide,
                sort_token=entry.canonical_peptide,
                score=entry.best_score,
                q_value=entry.best_q_value,
                target_decoy_label=entry.target_decoy_label,
            )
            for entry in rollups
        )
    protein_rollups = rollup_protein_evidence(records)
    return tuple(
        _CalibrationEvidenceRecord(
            entity_id=entry.protein_ref,
            sort_token=entry.protein_ref,
            score=entry.best_score,
            q_value=entry.best_q_value,
            target_decoy_label=entry.target_decoy_label,
        )
        for entry in protein_rollups
    )


def build_confidence_calibration_report(
    records: tuple[PsmRecord, ...],
    *,
    evidence_level: ConfidenceCalibrationLevel = ConfidenceCalibrationLevel.PSM,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
) -> ConfidenceCalibrationReport:
    """Assess confidence with empirical calibration context beyond q-values."""
    calibration_records = _records_for_confidence_calibration(
        records,
        evidence_level=evidence_level,
    )
    calibration_plot = _build_calibration_plot_data_for_records(
        calibration_records,
        score_orientation=score_orientation,
        bin_count=bin_count,
    )
    normalized_entries = _normalize_calibration_score_orientation(
        calibration_records,
        score_orientation=score_orientation,
    )
    q_value_by_entity_id = {
        record.entity_id: record.q_value for record in calibration_records
    }
    entries: list[ConfidenceCalibrationEntry] = []
    for entry in normalized_entries:
        bin_match = next(
            (
                calibration_bin
                for calibration_bin in calibration_plot.bins
                if calibration_bin.bin_lower <= entry.normalized_score
                and (
                    entry.normalized_score < calibration_bin.bin_upper
                    or calibration_bin.bin_upper == 1.0
                )
            ),
            calibration_plot.bins[-1] if calibration_plot.bins else None,
        )
        if bin_match is None:
            continue
        q_value = q_value_by_entity_id.get(entry.spectrum_id)
        q_component = 1.0 - min(q_value if q_value is not None else 0.5, 1.0)
        support_score = max(
            0.0,
            min(
                1.0,
                (
                    (1.0 - bin_match.decoy_fraction)
                    + entry.normalized_score
                    + q_component
                )
                / 3.0,
            ),
        )
        entries.append(
            ConfidenceCalibrationEntry(
                evidence_level=evidence_level,
                entity_id=entry.spectrum_id,
                q_value=q_value,
                normalized_score=entry.normalized_score,
                calibration_bin_lower=bin_match.bin_lower,
                calibration_bin_upper=bin_match.bin_upper,
                empirical_decoy_fraction=bin_match.decoy_fraction,
                support_score=support_score,
                note="support combines normalized rank, q-value, and empirical decoy fraction in the matched calibration bin",
            )
        )
    return ConfidenceCalibrationReport(
        evidence_level=evidence_level,
        score_orientation=score_orientation,
        entries=tuple(entries),
        calibration_plot=calibration_plot,
    )


def build_calibration_plot_data(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
) -> CalibrationPlotData:
    """Build plot-ready score calibration bins over target-decoy evidence."""
    calibration_records = tuple(
        _CalibrationEvidenceRecord(
            entity_id=record.spectrum_id,
            sort_token=record.canonical_peptide,
            score=record.score,
            q_value=record.q_value,
            target_decoy_label=record.target_decoy_label,
        )
        for record in records
    )
    return _build_calibration_plot_data_for_records(
        calibration_records,
        score_orientation=score_orientation,
        bin_count=bin_count,
    )


def _build_calibration_plot_data_for_records(
    records: tuple[_CalibrationEvidenceRecord, ...],
    *,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
) -> CalibrationPlotData:
    """Build plot-ready score calibration bins over generic evidence rows."""
    if bin_count < 1:
        raise ValueError("bin_count must be at least 1")

    normalized_entries = _normalize_calibration_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    bins: list[CalibrationPlotBin] = []
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        if index == bin_count - 1:
            bucket = tuple(
                entry
                for entry in normalized_entries
                if lower <= entry.normalized_score <= upper
            )
        else:
            bucket = tuple(
                entry
                for entry in normalized_entries
                if lower <= entry.normalized_score < upper
            )
        target_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.TARGET
        )
        decoy_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.DECOY
        )
        mixed_count = sum(
            1 for entry in bucket if entry.target_decoy_label is TargetDecoyLabel.MIXED
        )
        unknown_count = sum(
            1
            for entry in bucket
            if entry.target_decoy_label is TargetDecoyLabel.UNKNOWN
        )
        denominator = target_count + decoy_count
        bins.append(
            CalibrationPlotBin(
                bin_lower=lower,
                bin_upper=upper,
                target_count=target_count,
                decoy_count=decoy_count,
                mixed_count=mixed_count,
                unknown_count=unknown_count,
                decoy_fraction=decoy_count / denominator if denominator else 0.0,
            )
        )
    return CalibrationPlotData(
        score_orientation=score_orientation,
        total_psms=len(records),
        bins=tuple(bins),
    )


def build_fdr_edge_case_report(
    records: tuple[PsmRecord, ...],
) -> FdrEdgeCaseReport:
    """Build an explicit report for all-target, all-decoy, and no-decoy cases."""
    target_count = sum(
        1 for record in records if record.target_decoy_label is TargetDecoyLabel.TARGET
    )
    decoy_count = sum(
        1 for record in records if record.target_decoy_label is TargetDecoyLabel.DECOY
    )
    mixed_count = sum(
        1 for record in records if record.target_decoy_label is TargetDecoyLabel.MIXED
    )
    unknown_count = sum(
        1 for record in records if record.target_decoy_label is TargetDecoyLabel.UNKNOWN
    )
    if not records:
        kind = FdrEdgeCaseKind.EMPTY
        note = "no PSM records were provided for FDR evaluation"
    elif decoy_count == 0 and target_count == len(records):
        kind = FdrEdgeCaseKind.ALL_TARGET
        note = "all records are labeled target, so target-decoy separation cannot be checked"
    elif target_count == 0 and decoy_count == len(records):
        kind = FdrEdgeCaseKind.ALL_DECOY
        note = "all records are labeled decoy, so no biological evidence can pass"
    elif decoy_count == 0:
        kind = FdrEdgeCaseKind.NO_DECOY
        note = "no decoy records are present, so FDR behavior is advisory rather than comparative"
    else:
        kind = FdrEdgeCaseKind.MIXED
        note = "target and decoy evidence are both present"
    return FdrEdgeCaseReport(
        kind=kind,
        total_records=len(records),
        target_count=target_count,
        decoy_count=decoy_count,
        mixed_count=mixed_count,
        unknown_count=unknown_count,
        note=note,
    )


def compute_fdr_reproducibility_hash(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> str:
    """Compute a stable digest over the sorted FDR derivation inputs."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    payload = {
        "score_orientation": score_orientation,
        "tie_handling": tie_handling,
        "threshold": threshold,
        "entries": [
            {
                "rank": entry.rank,
                "tie_group_rank": entry.tie_group_rank,
                "tie_group_size": entry.tie_group_size,
                "spectrum_id": entry.psm.spectrum_id,
                "canonical_peptide": entry.psm.canonical_peptide,
                "charge": entry.psm.charge,
                "score": entry.psm.score,
                "target_decoy_label": entry.psm.target_decoy_label.value,
                "cumulative_targets": entry.cumulative_targets,
                "cumulative_decoys": entry.cumulative_decoys,
                "fdr": entry.fdr,
                "q_value": entry.q_value,
                "accepted": entry.accepted,
            }
            for entry in annotated
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_fdr_audit_trail(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = None,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> FdrAuditTrail:
    """Build a stable audit trail for one target-decoy FDR calculation.

    Inputs:
    ``records`` must contain governed PSM records, ``threshold`` optionally
    applies an acceptance cutoff, and ``score_orientation`` plus ``tie_handling``
    select the owned target-decoy ranking policy.

    Outputs:
    Returns one ``FdrAuditTrail`` with ranked audit entries, the resolved policy,
    and a reproducibility hash for the exact calculation inputs.

    Failure Modes:
    Propagates score-orientation normalization and target-decoy calculation
    errors when the records cannot satisfy the owned FDR policy assumptions.

    Scientific Caveats:
    The audit trail explains the package's target-decoy calculation only; it
    does not prove that the decoy strategy is appropriate for every search
    engine, sample type, or experimental design.
    """
    policy = FdrPolicy(
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        threshold=threshold,
    )
    normalized_entries = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    score_index = {
        (entry.spectrum_id, entry.canonical_peptide, entry.rank): entry
        for entry in normalized_entries
    }
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    audit_entries: list[FdrAuditEntry] = []
    for entry in annotated:
        normalized_entry = score_index.get(
            (entry.psm.spectrum_id, entry.psm.canonical_peptide, entry.rank)
        )
        audit_entries.append(
            FdrAuditEntry(
                rank=entry.rank,
                tie_group_rank=entry.tie_group_rank,
                tie_group_size=entry.tie_group_size,
                spectrum_id=entry.psm.spectrum_id,
                canonical_peptide=entry.psm.canonical_peptide,
                raw_score=entry.psm.score,
                normalized_score=normalized_entry.normalized_score
                if normalized_entry is not None
                else 0.0,
                target_decoy_label=entry.psm.target_decoy_label,
                cumulative_targets=entry.cumulative_targets,
                cumulative_decoys=entry.cumulative_decoys,
                fdr=entry.fdr,
                q_value=entry.q_value,
                accepted=entry.accepted,
            )
        )
    return FdrAuditTrail(
        policy=policy,
        entries=tuple(audit_entries),
        reproducibility_hash=compute_fdr_reproducibility_hash(
            records,
            threshold=threshold,
            score_orientation=score_orientation,
            tie_handling=tie_handling,
        ),
    )


def apply_q_values(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> tuple[PsmRecord, ...]:
    """Return PSM records with q-values filled from target-decoy FDR."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    return tuple(
        entry.psm.model_copy(update={"q_value": entry.q_value}) for entry in annotated
    )


def filter_psms_by_fdr(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float,
    score_orientation: str = "higher_better",
    tie_handling: str = "score_group",
) -> tuple[PsmRecord, ...]:
    """Filter PSMs to those that pass the requested q-value threshold."""
    annotated = calculate_basic_target_decoy_fdr(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        tie_handling=tie_handling,
        decoy_policy=None,
    )
    return tuple(
        entry.psm.model_copy(update={"q_value": entry.q_value})
        for entry in annotated
        if entry.accepted
    )


__all__ = [
    "FdrPolicy",
    "FdrAnnotatedPsm",
    "NormalizedScoreEntry",
    "CalibrationPlotBin",
    "CalibrationPlotData",
    "ScoreOrientationAdvisoryCandidate",
    "ScoreOrientationAdvisory",
    "FdrAuditEntry",
    "FdrAuditTrail",
    "FdrEvidenceLevel",
    "FdrLevelEntry",
    "FdrEdgeCaseKind",
    "FdrEdgeCaseReport",
    "GroupedFdrBucket",
    "GroupedFdrReport",
    "ConfidenceCalibrationLevel",
    "ConfidenceCalibrationEntry",
    "ConfidenceCalibrationReport",
    "calculate_basic_target_decoy_fdr",
    "normalize_psm_score_orientation",
    "detect_score_orientation_advisory",
    "build_confidence_calibration_report",
    "build_calibration_plot_data",
    "build_fdr_edge_case_report",
    "compute_fdr_reproducibility_hash",
    "build_fdr_audit_trail",
    "apply_q_values",
    "filter_psms_by_fdr",
]
