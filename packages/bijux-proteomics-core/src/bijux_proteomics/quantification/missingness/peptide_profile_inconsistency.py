# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Detect peptide profiles that disagree with their protein-level consensus."""

from __future__ import annotations

from collections import defaultdict
from enum import StrEnum
import math

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.quantification.contracts.input_models import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
    PeptideIntensityMatrixRow,
    PeptideIntensityMatrixValue,
    PeptideMatrixGroupingMode,
    PeptideMatrixSourceKind,
    build_peptide_intensity_matrix_from_features,
    build_peptide_intensity_matrix_from_psms,
)
from bijux_proteomics.quantification.matrix.protein_intensity_matrix import (
    ProteinMatrixTargetKind,
)
from bijux_proteomics_foundation import JsonModel


class PeptideProfileOutlierReason(StrEnum):
    """Deterministic reasons why one peptide disagrees with its protein profile."""

    CONSISTENT = "consistent"
    INSUFFICIENT_OVERLAP = "insufficient_overlap"
    DIRECTIONAL_PROFILE_INVERSION = "directional_profile_inversion"
    LOW_PROFILE_CORRELATION = "low_profile_correlation"
    LARGE_PROFILE_RESIDUAL = "large_profile_residual"


class PeptideProfileResidualEntry(JsonModel):
    """One sample-level residual between a peptide and leave-one-out protein profile."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    peptide_log2_abundance: float
    protein_profile_log2_abundance: float
    log2_residual: float


class PeptideProfileInconsistencyEntry(JsonModel):
    """One peptide-versus-protein profile comparison row."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    target_kind: ProteinMatrixTargetKind
    peptide_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    reference_peptide_ids: tuple[str, ...] = Field(default_factory=tuple)
    overlap_sample_count: int = Field(..., ge=0)
    reference_peptide_count: int = Field(..., ge=0)
    correlation_to_protein_profile: float | None = Field(default=None, ge=-1.0, le=1.0)
    residual_rmsd_log2: float | None = Field(default=None, ge=0.0)
    max_abs_residual_log2: float | None = Field(default=None, ge=0.0)
    profile_agreement_score: float = Field(..., ge=0.0, le=1.0)
    inconsistent_with_protein_profile: bool
    outlier_reason: PeptideProfileOutlierReason
    sample_residuals: tuple[PeptideProfileResidualEntry, ...] = Field(
        default_factory=tuple
    )


class PeptideProfileInconsistencySummary(JsonModel):
    """Compact summary over peptide-profile inconsistency detection."""

    model_config = ConfigDict(extra="forbid")

    peptide_row_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    evaluated_entry_count: int = Field(..., ge=0)
    inconsistent_entry_count: int = Field(..., ge=0)
    insufficient_overlap_entry_count: int = Field(..., ge=0)


class PeptideProfileInconsistencyReport(JsonModel):
    """Owned peptide inconsistency ledger over protein-level consensus profiles."""

    model_config = ConfigDict(extra="forbid")

    source_kind: PeptideMatrixSourceKind
    grouping_mode: PeptideMatrixGroupingMode
    target_kind: ProteinMatrixTargetKind
    unique_only: bool = False
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    entries: tuple[PeptideProfileInconsistencyEntry, ...] = Field(default_factory=tuple)
    summary: PeptideProfileInconsistencySummary
    note: str = Field(..., min_length=1)


def build_peptide_profile_inconsistency_report(
    peptide_matrix: PeptideIntensityMatrixReport | CanonicalQuantMatrix,
    *,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    unique_only: bool = False,
    minimum_reference_peptides: int = 2,
    minimum_overlap_samples: int = 2,
    low_correlation_threshold: float = 0.6,
    large_residual_threshold_log2: float = 1.0,
) -> PeptideProfileInconsistencyReport:
    """Compare each peptide profile to a leave-one-out protein consensus profile."""

    if isinstance(peptide_matrix, CanonicalQuantMatrix):
        peptide_matrix = PeptideIntensityMatrixReport.from_quant_matrix(peptide_matrix)
    if minimum_reference_peptides < 1:
        raise ValueError("minimum_reference_peptides must be at least 1")
    if minimum_overlap_samples < 2:
        raise ValueError("minimum_overlap_samples must be at least 2")
    if not 0.0 <= low_correlation_threshold <= 1.0:
        raise ValueError("low_correlation_threshold must be between 0 and 1")
    if large_residual_threshold_log2 <= 0.0:
        raise ValueError("large_residual_threshold_log2 must be greater than zero")

    grouped_rows: dict[str, list[PeptideIntensityMatrixRow]] = defaultdict(list)
    target_refs: dict[str, tuple[str, ...]] = {}
    for peptide_row in peptide_matrix.rows:
        is_unique = len(peptide_row.protein_refs) == 1
        if unique_only and not is_unique:
            continue
        if not peptide_row.protein_refs:
            continue
        target_ids = (
            peptide_row.protein_refs
            if target_kind is ProteinMatrixTargetKind.PROTEIN
            else (";".join(peptide_row.protein_refs),)
        )
        for target_id in target_ids:
            grouped_rows[target_id].append(peptide_row)
            target_refs.setdefault(
                target_id,
                peptide_row.protein_refs
                if target_kind is ProteinMatrixTargetKind.PROTEIN_GROUP
                else (target_id,),
            )

    entries: list[PeptideProfileInconsistencyEntry] = []
    inconsistent_entry_count = 0
    insufficient_overlap_entry_count = 0
    for target_id in sorted(grouped_rows):
        peptide_rows = grouped_rows[target_id]
        for peptide_row in peptide_rows:
            reference_rows = tuple(
                candidate
                for candidate in peptide_rows
                if candidate.entity_id != peptide_row.entity_id
            )
            entry = _build_inconsistency_entry(
                target_id=target_id,
                target_kind=target_kind,
                protein_refs=target_refs[target_id],
                peptide_row=peptide_row,
                reference_rows=reference_rows,
                minimum_reference_peptides=minimum_reference_peptides,
                minimum_overlap_samples=minimum_overlap_samples,
                low_correlation_threshold=low_correlation_threshold,
                large_residual_threshold_log2=large_residual_threshold_log2,
            )
            entries.append(entry)
            if entry.inconsistent_with_protein_profile:
                inconsistent_entry_count += 1
            if entry.outlier_reason is PeptideProfileOutlierReason.INSUFFICIENT_OVERLAP:
                insufficient_overlap_entry_count += 1

    sorted_entries = tuple(
        sort_rows_by_fields(tuple(entries), "entity_id", "peptide_id")
    )
    return PeptideProfileInconsistencyReport(
        source_kind=peptide_matrix.source_kind,
        grouping_mode=peptide_matrix.grouping_mode,
        target_kind=target_kind,
        unique_only=unique_only,
        sample_ids=peptide_matrix.sample_ids,
        entries=sorted_entries,
        summary=PeptideProfileInconsistencySummary(
            peptide_row_count=len(peptide_matrix.rows),
            protein_row_count=len(grouped_rows),
            evaluated_entry_count=len(sorted_entries),
            inconsistent_entry_count=inconsistent_entry_count,
            insufficient_overlap_entry_count=insufficient_overlap_entry_count,
        ),
        note=(
            "peptide profile inconsistency compares each peptide against a leave-one-out "
            "protein consensus so discordant abundance trajectories become explicit "
            "review and confidence signals"
        ),
    )


def build_peptide_profile_inconsistency_report_from_features(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = (
        PeptideMatrixGroupingMode.MODIFIED_PEPTIDE
    ),
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    separate_charge_states: bool = False,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    minimum_reference_peptides: int = 2,
    minimum_overlap_samples: int = 2,
    top_n: int = 3,
) -> PeptideProfileInconsistencyReport:
    """Build one peptide inconsistency report from MS1 feature evidence."""

    peptide_matrix = build_peptide_intensity_matrix_from_features(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_peptide_profile_inconsistency_report(
        peptide_matrix,
        target_kind=target_kind,
        unique_only=unique_only,
        minimum_reference_peptides=minimum_reference_peptides,
        minimum_overlap_samples=minimum_overlap_samples,
    )


def build_peptide_profile_inconsistency_report_from_psms(
    records: tuple[PsmRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = (
        PeptideMatrixGroupingMode.MODIFIED_PEPTIDE
    ),
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    separate_charge_states: bool = False,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    minimum_reference_peptides: int = 2,
    minimum_overlap_samples: int = 2,
    top_n: int = 3,
) -> PeptideProfileInconsistencyReport:
    """Build one peptide inconsistency report from canonical PSM evidence."""

    peptide_matrix = build_peptide_intensity_matrix_from_psms(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_peptide_profile_inconsistency_report(
        peptide_matrix,
        target_kind=target_kind,
        unique_only=unique_only,
        minimum_reference_peptides=minimum_reference_peptides,
        minimum_overlap_samples=minimum_overlap_samples,
    )


def render_peptide_profile_inconsistency_tsv(
    report: PeptideProfileInconsistencyReport,
) -> str:
    """Render one peptide inconsistency ledger as deterministic TSV."""

    header = (
        "entity_id",
        "target_kind",
        "peptide_id",
        "peptide_sequence",
        "protein_refs",
        "reference_peptide_ids",
        "overlap_sample_count",
        "reference_peptide_count",
        "correlation_to_protein_profile",
        "residual_rmsd_log2",
        "max_abs_residual_log2",
        "profile_agreement_score",
        "inconsistent_with_protein_profile",
        "outlier_reason",
        "sample_residuals_log2",
    )
    rows = ["\t".join(header)]
    for entry in sort_rows_by_fields(report.entries, "entity_id", "peptide_id"):
        sample_residuals = ";".join(
            f"{residual.sample_id}:{residual.log2_residual:.4f}"
            for residual in entry.sample_residuals
        )
        rows.append(
            "\t".join(
                (
                    entry.entity_id,
                    entry.target_kind.value,
                    entry.peptide_id,
                    entry.peptide_sequence,
                    ";".join(sort_strings(entry.protein_refs)),
                    ";".join(sort_strings(entry.reference_peptide_ids)),
                    str(entry.overlap_sample_count),
                    str(entry.reference_peptide_count),
                    (
                        ""
                        if entry.correlation_to_protein_profile is None
                        else f"{entry.correlation_to_protein_profile:.4f}"
                    ),
                    (
                        ""
                        if entry.residual_rmsd_log2 is None
                        else f"{entry.residual_rmsd_log2:.4f}"
                    ),
                    (
                        ""
                        if entry.max_abs_residual_log2 is None
                        else f"{entry.max_abs_residual_log2:.4f}"
                    ),
                    f"{entry.profile_agreement_score:.4f}",
                    str(entry.inconsistent_with_protein_profile).lower(),
                    entry.outlier_reason.value,
                    sample_residuals,
                )
            )
        )
    return "\n".join(rows) + "\n"


def _build_inconsistency_entry(
    *,
    target_id: str,
    target_kind: ProteinMatrixTargetKind,
    protein_refs: tuple[str, ...],
    peptide_row: PeptideIntensityMatrixRow,
    reference_rows: tuple[PeptideIntensityMatrixRow, ...],
    minimum_reference_peptides: int,
    minimum_overlap_samples: int,
    low_correlation_threshold: float,
    large_residual_threshold_log2: float,
) -> PeptideProfileInconsistencyEntry:
    peptide_log2_by_sample = _observed_log2_by_sample(peptide_row.values)
    reference_log2_by_sample = _reference_profile_log2_by_sample(reference_rows)
    overlap_sample_ids = tuple(
        sorted(set(peptide_log2_by_sample).intersection(reference_log2_by_sample))
    )

    if (
        len(reference_rows) < minimum_reference_peptides
        or len(overlap_sample_ids) < minimum_overlap_samples
    ):
        return PeptideProfileInconsistencyEntry(
            entity_id=target_id,
            target_kind=target_kind,
            peptide_id=peptide_row.entity_id,
            peptide_sequence=peptide_row.peptide_sequence,
            protein_refs=protein_refs,
            reference_peptide_ids=tuple(
                sorted(reference_row.entity_id for reference_row in reference_rows)
            ),
            overlap_sample_count=len(overlap_sample_ids),
            reference_peptide_count=len(reference_rows),
            correlation_to_protein_profile=None,
            residual_rmsd_log2=None,
            max_abs_residual_log2=None,
            profile_agreement_score=0.85,
            inconsistent_with_protein_profile=False,
            outlier_reason=PeptideProfileOutlierReason.INSUFFICIENT_OVERLAP,
            sample_residuals=(),
        )

    peptide_logs = tuple(
        peptide_log2_by_sample[sample_id] for sample_id in overlap_sample_ids
    )
    reference_logs = tuple(
        reference_log2_by_sample[sample_id] for sample_id in overlap_sample_ids
    )
    offset = _median(
        tuple(
            peptide - reference
            for peptide, reference in zip(peptide_logs, reference_logs, strict=False)
        )
    )
    centered_peptide_logs = tuple(
        value - _median(peptide_logs) for value in peptide_logs
    )
    centered_reference_logs = tuple(
        value - _median(reference_logs) for value in reference_logs
    )
    correlation = _pearson(centered_peptide_logs, centered_reference_logs)
    residual_entries = tuple(
        PeptideProfileResidualEntry(
            sample_id=sample_id,
            peptide_log2_abundance=peptide_log2_by_sample[sample_id],
            protein_profile_log2_abundance=reference_log2_by_sample[sample_id] + offset,
            log2_residual=peptide_log2_by_sample[sample_id]
            - (reference_log2_by_sample[sample_id] + offset),
        )
        for sample_id in overlap_sample_ids
    )
    residual_values = tuple(residual.log2_residual for residual in residual_entries)
    residual_rmsd_log2 = math.sqrt(
        sum(value * value for value in residual_values) / len(residual_values)
    )
    max_abs_residual_log2 = max(abs(value) for value in residual_values)
    outlier_reason = PeptideProfileOutlierReason.CONSISTENT
    inconsistent_with_protein_profile = False
    profile_agreement_score = 1.0
    if correlation is not None and correlation < 0.0:
        outlier_reason = PeptideProfileOutlierReason.DIRECTIONAL_PROFILE_INVERSION
        inconsistent_with_protein_profile = True
        profile_agreement_score = 0.2
    elif correlation is not None and correlation < low_correlation_threshold:
        outlier_reason = PeptideProfileOutlierReason.LOW_PROFILE_CORRELATION
        inconsistent_with_protein_profile = True
        profile_agreement_score = 0.45
    elif max_abs_residual_log2 >= large_residual_threshold_log2:
        outlier_reason = PeptideProfileOutlierReason.LARGE_PROFILE_RESIDUAL
        inconsistent_with_protein_profile = True
        profile_agreement_score = 0.6

    return PeptideProfileInconsistencyEntry(
        entity_id=target_id,
        target_kind=target_kind,
        peptide_id=peptide_row.entity_id,
        peptide_sequence=peptide_row.peptide_sequence,
        protein_refs=protein_refs,
        reference_peptide_ids=tuple(
            sorted(reference_row.entity_id for reference_row in reference_rows)
        ),
        overlap_sample_count=len(overlap_sample_ids),
        reference_peptide_count=len(reference_rows),
        correlation_to_protein_profile=correlation,
        residual_rmsd_log2=residual_rmsd_log2,
        max_abs_residual_log2=max_abs_residual_log2,
        profile_agreement_score=profile_agreement_score,
        inconsistent_with_protein_profile=inconsistent_with_protein_profile,
        outlier_reason=outlier_reason,
        sample_residuals=tuple(sort_rows_by_fields(residual_entries, "sample_id")),
    )


def _observed_log2_by_sample(
    values: tuple[PeptideIntensityMatrixValue, ...],
) -> dict[str, float]:
    return {
        value.sample_id: math.log2(float(value.abundance))
        for value in values
        if value.abundance is not None
        and value.abundance > 0.0
        and value.missing_value_kind is MissingValueKind.OBSERVED
    }


def _reference_profile_log2_by_sample(
    reference_rows: tuple[PeptideIntensityMatrixRow, ...],
) -> dict[str, float]:
    observed_by_sample: dict[str, list[float]] = defaultdict(list)
    for row in reference_rows:
        for sample_id, log2_value in _observed_log2_by_sample(row.values).items():
            observed_by_sample[sample_id].append(log2_value)
    return {
        sample_id: _median(tuple(values))
        for sample_id, values in observed_by_sample.items()
        if values
    }


def _median(values: tuple[float, ...]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[midpoint])
    return float((ordered[midpoint - 1] + ordered[midpoint]) / 2.0)


def _pearson(left: tuple[float, ...], right: tuple[float, ...]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    mean_left = sum(left) / len(left)
    mean_right = sum(right) / len(right)
    numerator = sum(
        (left_value - mean_left) * (right_value - mean_right)
        for left_value, right_value in zip(left, right, strict=False)
    )
    denominator_left = math.sqrt(sum((value - mean_left) ** 2 for value in left))
    denominator_right = math.sqrt(sum((value - mean_right) ** 2 for value in right))
    if denominator_left == 0.0 or denominator_right == 0.0:
        return None
    correlation = float(numerator / (denominator_left * denominator_right))
    return max(-1.0, min(1.0, correlation))
