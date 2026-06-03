# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned imported-PEP and computed local-FDR annotations for PSM evidence."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
import io
import json
import math

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.psm_target_decoy_fdr import (
    PsmTargetDecoyFdrEntry,
    build_psm_target_decoy_fdr_report,
)
from bijux_proteomics_foundation import JsonModel


class ErrorRateProvenanceFlag(StrEnum):
    """Stable provenance for one per-PSM error-rate annotation."""

    IMPORTED_PEP = "imported_pep"
    COMPUTED_LOCAL_FDR = "computed_local_fdr"
    UNAVAILABLE = "unavailable"


class PsmErrorRateAnnotationPolicy(JsonModel):
    """Stable policy for one PSM error-rate annotation pass."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(
        default="higher_better",
        pattern="^(higher_better|lower_better)$",
    )
    local_window_size: int = Field(default=5, ge=1)


class PsmErrorRateAnnotationEntry(JsonModel):
    """One PSM plus imported PEP or computed local-FDR state."""

    model_config = ConfigDict(extra="forbid")

    psm: PsmRecord
    imported_pep: float | None = Field(default=None, ge=0.0, le=1.0)
    computed_local_fdr: float | None = Field(default=None, ge=0.0, le=1.0)
    provenance_flag: ErrorRateProvenanceFlag


class PsmErrorRateAnnotationSummary(JsonModel):
    """Compact summary over imported and computed error-rate annotations."""

    model_config = ConfigDict(extra="forbid")

    total_psm_count: int = Field(..., ge=0)
    imported_pep_count: int = Field(..., ge=0)
    computed_local_fdr_count: int = Field(..., ge=0)
    unavailable_count: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)


class PsmErrorRateAnnotationReport(JsonModel):
    """Owned report over imported PEP and computed local-FDR annotations."""

    model_config = ConfigDict(extra="forbid")

    policy: PsmErrorRateAnnotationPolicy
    summary: PsmErrorRateAnnotationSummary
    reproducibility_hash: str = Field(..., min_length=64, max_length=64)
    entries: tuple[PsmErrorRateAnnotationEntry, ...] = Field(default_factory=tuple)


def build_psm_error_rate_annotation_report(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    local_window_size: int | None = None,
) -> PsmErrorRateAnnotationReport:
    """Prefer imported PEP and otherwise compute local-FDR from target-decoy density."""
    resolved_window_size = local_window_size or max(
        3, math.ceil(math.sqrt(max(len(records), 1)))
    )
    policy = PsmErrorRateAnnotationPolicy(
        score_orientation=score_orientation,
        local_window_size=resolved_window_size,
    )
    ranked_entries = build_psm_target_decoy_fdr_report(
        records,
        score_orientation=score_orientation,
    ).entries
    local_fdr_by_rank = _compute_local_fdr_by_rank(
        ranked_entries,
        window_size=resolved_window_size,
    )
    entries = tuple(
        _build_annotation_entry(
            entry.psm,
            local_fdr=local_fdr_by_rank[index],
        )
        for index, entry in enumerate(ranked_entries)
    )
    payload = {
        "policy": policy.to_dict(),
        "entries": [entry.to_dict() for entry in entries],
    }
    return PsmErrorRateAnnotationReport(
        policy=policy,
        summary=PsmErrorRateAnnotationSummary(
            total_psm_count=len(entries),
            imported_pep_count=sum(
                1
                for entry in entries
                if entry.provenance_flag is ErrorRateProvenanceFlag.IMPORTED_PEP
            ),
            computed_local_fdr_count=sum(
                1
                for entry in entries
                if entry.provenance_flag is ErrorRateProvenanceFlag.COMPUTED_LOCAL_FDR
            ),
            unavailable_count=sum(
                1
                for entry in entries
                if entry.provenance_flag is ErrorRateProvenanceFlag.UNAVAILABLE
            ),
            target_count=sum(
                1
                for record in records
                if record.target_decoy_label is TargetDecoyLabel.TARGET
            ),
            decoy_count=sum(
                1
                for record in records
                if record.target_decoy_label is TargetDecoyLabel.DECOY
            ),
        ),
        reproducibility_hash=hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        entries=entries,
    )


def annotate_psm_error_rates(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    local_window_size: int | None = None,
) -> tuple[PsmRecord, ...]:
    """Return PSMs annotated with imported PEP or computed local-FDR provenance."""
    report = build_psm_error_rate_annotation_report(
        records,
        score_orientation=score_orientation,
        local_window_size=local_window_size,
    )
    return tuple(entry.psm for entry in report.entries)


def render_psm_error_rate_annotation_tsv(report: PsmErrorRateAnnotationReport) -> str:
    """Render one row per PSM error-rate annotation."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "spectrum_id",
            "canonical_peptide",
            "charge",
            "score",
            "target_decoy_label",
            "q_value",
            "posterior_error_probability",
            "local_fdr",
            "error_rate_provenance",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.psm.spectrum_id,
                entry.psm.canonical_peptide,
                entry.psm.charge,
                entry.psm.score,
                entry.psm.target_decoy_label.value,
                entry.psm.q_value,
                entry.imported_pep,
                entry.computed_local_fdr,
                entry.provenance_flag.value,
            )
        )
    return buffer.getvalue()


def render_psm_error_rate_annotation_summary_tsv(
    report: PsmErrorRateAnnotationReport,
) -> str:
    """Render one summary row over imported PEP and computed local-FDR support."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "score_orientation",
            "local_window_size",
            "total_psm_count",
            "imported_pep_count",
            "computed_local_fdr_count",
            "unavailable_count",
            "target_count",
            "decoy_count",
            "reproducibility_hash",
        )
    )
    writer.writerow(
        (
            report.policy.score_orientation,
            report.policy.local_window_size,
            report.summary.total_psm_count,
            report.summary.imported_pep_count,
            report.summary.computed_local_fdr_count,
            report.summary.unavailable_count,
            report.summary.target_count,
            report.summary.decoy_count,
            report.reproducibility_hash,
        )
    )
    return buffer.getvalue()


def _compute_local_fdr_by_rank(
    ranked_entries: tuple[PsmTargetDecoyFdrEntry, ...],
    *,
    window_size: int,
) -> tuple[float | None, ...]:
    labeled_positions = [
        index
        for index, entry in enumerate(ranked_entries)
        if entry.psm.target_decoy_label
        in {TargetDecoyLabel.TARGET, TargetDecoyLabel.DECOY}
    ]
    labeled_count = len(labeled_positions)
    if labeled_count == 0:
        return tuple(None for _ in ranked_entries)
    half_window = max((window_size - 1) // 2, 0)
    values: list[float | None] = [None] * len(ranked_entries)
    for position_index, entry_index in enumerate(labeled_positions):
        start = max(0, position_index - half_window)
        end = min(labeled_count, position_index + half_window + 1)
        window_entries = [
            ranked_entries[labeled_positions[index]] for index in range(start, end)
        ]
        target_count = sum(
            1
            for window_entry in window_entries
            if window_entry.psm.target_decoy_label is TargetDecoyLabel.TARGET
        )
        decoy_count = sum(
            1
            for window_entry in window_entries
            if window_entry.psm.target_decoy_label is TargetDecoyLabel.DECOY
        )
        values[entry_index] = min(decoy_count / max(target_count, 1), 1.0)
    return tuple(values)


def _build_annotation_entry(
    record: PsmRecord,
    *,
    local_fdr: float | None,
) -> PsmErrorRateAnnotationEntry:
    if record.posterior_error_probability is not None:
        annotated = record.model_copy(
            update={
                "local_fdr": None,
                "error_rate_provenance": ErrorRateProvenanceFlag.IMPORTED_PEP.value,
            }
        )
        return PsmErrorRateAnnotationEntry(
            psm=annotated,
            imported_pep=record.posterior_error_probability,
            computed_local_fdr=None,
            provenance_flag=ErrorRateProvenanceFlag.IMPORTED_PEP,
        )
    if local_fdr is not None:
        annotated = record.model_copy(
            update={
                "local_fdr": local_fdr,
                "error_rate_provenance": (
                    ErrorRateProvenanceFlag.COMPUTED_LOCAL_FDR.value
                ),
            }
        )
        return PsmErrorRateAnnotationEntry(
            psm=annotated,
            imported_pep=None,
            computed_local_fdr=local_fdr,
            provenance_flag=ErrorRateProvenanceFlag.COMPUTED_LOCAL_FDR,
        )
    annotated = record.model_copy(
        update={
            "local_fdr": None,
            "error_rate_provenance": ErrorRateProvenanceFlag.UNAVAILABLE.value,
        }
    )
    return PsmErrorRateAnnotationEntry(
        psm=annotated,
        imported_pep=None,
        computed_local_fdr=None,
        provenance_flag=ErrorRateProvenanceFlag.UNAVAILABLE,
    )


__all__ = [
    "ErrorRateProvenanceFlag",
    "PsmErrorRateAnnotationEntry",
    "PsmErrorRateAnnotationPolicy",
    "PsmErrorRateAnnotationReport",
    "PsmErrorRateAnnotationSummary",
    "annotate_psm_error_rates",
    "build_psm_error_rate_annotation_report",
    "render_psm_error_rate_annotation_summary_tsv",
    "render_psm_error_rate_annotation_tsv",
]
