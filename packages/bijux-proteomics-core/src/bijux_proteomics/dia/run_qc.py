# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned DIA run-level QC surfaces over DIA-NN import evidence."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

from collections.abc import Sequence
import csv
import math
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.identification.diann_import import (
        DiaNnBundleImportReport,
        DiaNnPrecursorReviewEntry,
        DiaNnProteinGroupReviewEntry,
    )


class DiaRunQcRunEntry(JsonModel):
    """One DIA run summarized at precursor and protein identity level."""

    model_config = ConfigDict(extra="forbid")

    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    precursor_id_count: int = Field(..., ge=0)
    precursor_key_count: int = Field(..., ge=0)
    protein_group_id_count: int = Field(..., ge=0)
    protein_id_count: int = Field(..., ge=0)
    observed_precursor_quantity_count: int = Field(..., ge=0)
    observed_protein_quantity_count: int = Field(..., ge=0)
    median_log10_precursor_quantity: float | None = None
    precursor_missing_fraction: float = Field(..., ge=0.0, le=1.0)
    protein_missing_fraction: float = Field(..., ge=0.0, le=1.0)
    weak_run_flag_count: int = Field(..., ge=0)
    flagged: bool = False


class DiaRunQcIntensityDistributionEntry(JsonModel):
    """One run-specific precursor intensity distribution bucket."""

    model_config = ConfigDict(extra="forbid")

    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    bucket: str = Field(..., min_length=1)
    count: int = Field(..., ge=0)


class DiaRunQcCorrelationEntry(JsonModel):
    """One pairwise DIA run correlation over shared precursor quantities."""

    model_config = ConfigDict(extra="forbid")

    run_name_a: str = Field(..., min_length=1)
    sample_name_a: str = Field(..., min_length=1)
    run_name_b: str = Field(..., min_length=1)
    sample_name_b: str = Field(..., min_length=1)
    shared_precursor_key_count: int = Field(..., ge=0)
    pearson_correlation: float | None = Field(default=None, ge=-1.0, le=1.0)


class DiaRunQcOutlierRunEntry(JsonModel):
    """One DIA run flagged as weak under explicit QC signals."""

    model_config = ConfigDict(extra="forbid")

    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    flags: tuple["DiaRunQcWeakRunFlagEntry", ...] = Field(default_factory=tuple)
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class DiaRunQcWeakRunFlagCode(StrEnum):
    """Governed weak-run flag codes on DIA run QC."""

    LOW_PRECURSOR_COVERAGE = "low_precursor_coverage"
    LOW_PROTEIN_COVERAGE = "low_protein_coverage"
    HIGH_PRECURSOR_MISSINGNESS = "high_precursor_missingness"
    HIGH_PROTEIN_MISSINGNESS = "high_protein_missingness"
    LOW_RUN_CORRELATION = "low_run_correlation"
    INSUFFICIENT_SHARED_PRECURSOR_OVERLAP = "insufficient_shared_precursor_overlap"


class DiaRunQcWeakRunFlagEntry(JsonModel):
    """One structured weak-run flag with explicit reason and threshold."""

    model_config = ConfigDict(extra="forbid")

    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    code: DiaRunQcWeakRunFlagCode
    reason: str = Field(..., min_length=1)
    threshold_name: str = Field(..., min_length=1)
    threshold_value: float = Field(...)
    observed_value: float = Field(...)


class DiaRunQcPolicy(JsonModel):
    """Owned DIA run-QC thresholds that drive weak-run flags."""

    model_config = ConfigDict(extra="forbid")

    include_decoys: bool = False
    max_q_value: float | None = Field(default=None, ge=0.0, le=1.0)
    low_precursor_count_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    low_protein_count_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    high_missing_fraction: float = Field(default=0.4, ge=0.0, le=1.0)
    low_correlation_threshold: float = Field(default=0.9, ge=-1.0, le=1.0)


class DiaRunQcSummary(JsonModel):
    """Compact summary over one DIA run-QC report."""

    model_config = ConfigDict(extra="forbid")

    run_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    union_precursor_key_count: int = Field(..., ge=0)
    union_protein_group_id_count: int = Field(..., ge=0)
    union_protein_id_count: int = Field(..., ge=0)
    flagged_run_count: int = Field(..., ge=0)
    weak_run_flag_count: int = Field(..., ge=0)


class DiaRunQcReport(JsonModel):
    """Owned DIA run QC report over imported precursor and protein-group rows."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(default="DIA-NN", min_length=1)
    policy: DiaRunQcPolicy
    run_entries: tuple[DiaRunQcRunEntry, ...] = Field(default_factory=tuple)
    intensity_distribution: tuple[DiaRunQcIntensityDistributionEntry, ...] = Field(
        default_factory=tuple
    )
    pairwise_correlations: tuple[DiaRunQcCorrelationEntry, ...] = Field(
        default_factory=tuple
    )
    outlier_runs: tuple[DiaRunQcOutlierRunEntry, ...] = Field(default_factory=tuple)
    summary: DiaRunQcSummary
    note: str = Field(..., min_length=1)


def build_dia_run_qc_report(
    import_report: DiaNnBundleImportReport,
    *,
    include_decoys: bool = False,
    max_q_value: float | None = None,
    low_precursor_count_fraction: float = 0.5,
    low_protein_count_fraction: float = 0.5,
    high_missing_fraction: float = 0.4,
    low_correlation_threshold: float = 0.9,
) -> DiaRunQcReport:
    """Build DIA run-level QC over imported DIA-NN evidence."""

    policy = DiaRunQcPolicy(
        include_decoys=include_decoys,
        max_q_value=max_q_value,
        low_precursor_count_fraction=low_precursor_count_fraction,
        low_protein_count_fraction=low_protein_count_fraction,
        high_missing_fraction=high_missing_fraction,
        low_correlation_threshold=low_correlation_threshold,
    )

    precursor_rows = _filtered_precursor_rows(
        import_report.precursor_rows,
        include_decoys=policy.include_decoys,
        max_q_value=policy.max_q_value,
    )
    protein_rows = _filtered_protein_rows(
        import_report.protein_group_rows,
        include_decoys=policy.include_decoys,
        max_q_value=policy.max_q_value,
    )
    run_names = sorted({row.run_name for row in precursor_rows})
    union_precursor_keys = {_stable_precursor_key(row) for row in precursor_rows}
    union_protein_group_ids = {row.protein_group_id for row in protein_rows}
    union_protein_ids = {
        protein_ref for row in protein_rows for protein_ref in row.protein_refs
    }
    run_entries: list[DiaRunQcRunEntry] = []
    intensity_distribution: list[DiaRunQcIntensityDistributionEntry] = []
    run_precursor_quantity_maps: dict[str, dict[str, float]] = {}
    sample_name_by_run: dict[str, str] = {}
    for run_name in run_names:
        run_precursors = [row for row in precursor_rows if row.run_name == run_name]
        run_proteins = [row for row in protein_rows if row.run_name == run_name]
        sample_names = sorted({row.sample_name for row in run_precursors})
        sample_name = sample_names[0] if sample_names else "unknown"
        sample_name_by_run[run_name] = sample_name
        precursor_keys = {_stable_precursor_key(row) for row in run_precursors}
        protein_ids = {
            protein_ref for row in run_proteins for protein_ref in row.protein_refs
        }
        observed_precursor_quantities = [
            row.precursor_quantity
            for row in run_precursors
            if row.precursor_quantity is not None
        ]
        median_log10_precursor_quantity = (
            float(
                _median(
                    [
                        math.log10(quantity)
                        for quantity in observed_precursor_quantities
                        if quantity > 0.0
                    ]
                )
            )
            if observed_precursor_quantities
            else None
        )
        run_precursor_quantity_maps[run_name] = {
            _stable_precursor_key(row): float(row.precursor_quantity)
            for row in run_precursors
            if row.precursor_quantity is not None
        }
        run_entries.append(
            DiaRunQcRunEntry(
                run_name=run_name,
                sample_name=sample_name,
                precursor_id_count=len({row.precursor_id for row in run_precursors}),
                precursor_key_count=len(precursor_keys),
                protein_group_id_count=len(
                    {row.protein_group_id for row in run_proteins}
                ),
                protein_id_count=len(protein_ids),
                observed_precursor_quantity_count=sum(
                    row.precursor_quantity is not None for row in run_precursors
                ),
                observed_protein_quantity_count=sum(
                    row.protein_group_quantity is not None for row in run_proteins
                ),
                median_log10_precursor_quantity=median_log10_precursor_quantity,
                precursor_missing_fraction=_fraction(
                    len(union_precursor_keys) - len(precursor_keys),
                    len(union_precursor_keys),
                ),
                protein_missing_fraction=_fraction(
                    len(union_protein_ids) - len(protein_ids),
                    len(union_protein_ids),
                ),
                weak_run_flag_count=0,
            )
        )
        for bucket, count in _intensity_distribution(observed_precursor_quantities).items():
            intensity_distribution.append(
                DiaRunQcIntensityDistributionEntry(
                    run_name=run_name,
                    sample_name=sample_name,
                    bucket=bucket,
                    count=count,
                )
            )
    pairwise_correlations = _build_pairwise_correlations(
        run_names=run_names,
        sample_name_by_run=sample_name_by_run,
        run_precursor_quantity_maps=run_precursor_quantity_maps,
    )
    median_precursor_count = _median(
        [float(entry.precursor_key_count) for entry in run_entries]
    )
    median_protein_count = _median([float(entry.protein_id_count) for entry in run_entries])
    median_correlation_by_run = _median_correlation_by_run(pairwise_correlations)
    max_shared_precursor_key_count_by_run = _max_shared_precursor_key_count_by_run(
        pairwise_correlations
    )
    outlier_runs: list[DiaRunQcOutlierRunEntry] = []
    flagged_run_names: set[str] = set()
    weak_run_flag_count = 0
    final_run_entries: list[DiaRunQcRunEntry] = []
    for entry in run_entries:
        flags: list[DiaRunQcWeakRunFlagEntry] = []
        if median_precursor_count > 0 and (
            entry.precursor_key_count / median_precursor_count
        ) < policy.low_precursor_count_fraction:
            flags.append(
                DiaRunQcWeakRunFlagEntry(
                    run_name=entry.run_name,
                    sample_name=entry.sample_name,
                    code=DiaRunQcWeakRunFlagCode.LOW_PRECURSOR_COVERAGE,
                    reason="precursor coverage is far below the study median",
                    threshold_name="low_precursor_count_fraction",
                    threshold_value=policy.low_precursor_count_fraction,
                    observed_value=entry.precursor_key_count / median_precursor_count,
                )
            )
        if median_protein_count > 0 and (
            entry.protein_id_count / median_protein_count
        ) < policy.low_protein_count_fraction:
            flags.append(
                DiaRunQcWeakRunFlagEntry(
                    run_name=entry.run_name,
                    sample_name=entry.sample_name,
                    code=DiaRunQcWeakRunFlagCode.LOW_PROTEIN_COVERAGE,
                    reason="protein coverage is far below the study median",
                    threshold_name="low_protein_count_fraction",
                    threshold_value=policy.low_protein_count_fraction,
                    observed_value=entry.protein_id_count / median_protein_count,
                )
            )
        if entry.precursor_missing_fraction > policy.high_missing_fraction:
            flags.append(
                DiaRunQcWeakRunFlagEntry(
                    run_name=entry.run_name,
                    sample_name=entry.sample_name,
                    code=DiaRunQcWeakRunFlagCode.HIGH_PRECURSOR_MISSINGNESS,
                    reason="precursor missingness is above the configured threshold",
                    threshold_name="high_missing_fraction",
                    threshold_value=policy.high_missing_fraction,
                    observed_value=entry.precursor_missing_fraction,
                )
            )
        if entry.protein_missing_fraction > policy.high_missing_fraction:
            flags.append(
                DiaRunQcWeakRunFlagEntry(
                    run_name=entry.run_name,
                    sample_name=entry.sample_name,
                    code=DiaRunQcWeakRunFlagCode.HIGH_PROTEIN_MISSINGNESS,
                    reason="protein missingness is above the configured threshold",
                    threshold_name="high_missing_fraction",
                    threshold_value=policy.high_missing_fraction,
                    observed_value=entry.protein_missing_fraction,
                )
            )
        median_correlation = median_correlation_by_run.get(entry.run_name)
        if median_correlation is None:
            flags.append(
                DiaRunQcWeakRunFlagEntry(
                    run_name=entry.run_name,
                    sample_name=entry.sample_name,
                    code=DiaRunQcWeakRunFlagCode.INSUFFICIENT_SHARED_PRECURSOR_OVERLAP,
                    reason="shared precursor overlap is too small for stable correlation review",
                    threshold_name="minimum_shared_precursor_key_count",
                    threshold_value=2.0,
                    observed_value=float(
                        max_shared_precursor_key_count_by_run.get(entry.run_name, 0)
                    ),
                )
            )
        elif median_correlation < policy.low_correlation_threshold:
            flags.append(
                DiaRunQcWeakRunFlagEntry(
                    run_name=entry.run_name,
                    sample_name=entry.sample_name,
                    code=DiaRunQcWeakRunFlagCode.LOW_RUN_CORRELATION,
                    reason="run correlation is below the configured threshold",
                    threshold_name="low_correlation_threshold",
                    threshold_value=policy.low_correlation_threshold,
                    observed_value=median_correlation,
                )
            )
        flagged = bool(flags)
        if flagged:
            flagged_run_names.add(entry.run_name)
            weak_run_flag_count += len(flags)
            outlier_runs.append(
                DiaRunQcOutlierRunEntry(
                    run_name=entry.run_name,
                    sample_name=entry.sample_name,
                    flags=tuple(sorted(flags, key=lambda flag: flag.code.value)),
                    reasons=tuple(sorted(flag.reason for flag in flags)),
                )
            )
        final_run_entries.append(
            entry.model_copy(
                update={
                    "flagged": flagged,
                    "weak_run_flag_count": len(flags),
                }
            )
        )
    sample_count = len({entry.sample_name for entry in run_entries})
    return DiaRunQcReport(
        policy=policy,
        run_entries=tuple(sorted(final_run_entries, key=lambda entry: entry.run_name)),
        intensity_distribution=tuple(
            sorted(
                intensity_distribution,
                key=lambda entry: (entry.run_name, entry.bucket),
            )
        ),
        pairwise_correlations=pairwise_correlations,
        outlier_runs=tuple(sorted(outlier_runs, key=lambda entry: entry.run_name)),
        summary=DiaRunQcSummary(
            run_count=len(final_run_entries),
            sample_count=sample_count,
            union_precursor_key_count=len(union_precursor_keys),
            union_protein_group_id_count=len(union_protein_group_ids),
            union_protein_id_count=len(union_protein_ids),
            flagged_run_count=len(flagged_run_names),
            weak_run_flag_count=weak_run_flag_count,
        ),
        note=(
            "run qc keeps precursor and protein identity burden, intensity distribution, missingness, pairwise correlation, and threshold-aware weak-run flags visible per run"
        ),
    )


def build_diann_run_qc_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = None,
) -> DiaRunQcReport:
    """Build DIA run-level QC directly from one DIA-NN report."""

    from bijux_proteomics.identification.diann_import import build_diann_import_report

    return build_dia_run_qc_report(
        build_diann_import_report(result_tsv_path, config_path=config_path),
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )


def render_dia_run_qc_summary_tsv(report: DiaRunQcReport) -> str:
    """Render a compact summary for one DIA run-QC report."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "source_name",
            "run_count",
            "sample_count",
            "union_precursor_key_count",
            "union_protein_group_id_count",
            "union_protein_id_count",
            "flagged_run_count",
            "weak_run_flag_count",
            "note",
        ]
    )
    writer.writerow(
        [
            report.source_name,
            report.summary.run_count,
            report.summary.sample_count,
            report.summary.union_precursor_key_count,
            report.summary.union_protein_group_id_count,
            report.summary.union_protein_id_count,
            report.summary.flagged_run_count,
            report.summary.weak_run_flag_count,
            report.note,
        ]
    )
    return buffer.getvalue()


def render_dia_run_qc_run_table_tsv(report: DiaRunQcReport) -> str:
    """Render one DIA run-QC table with run-level counts and burden."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "run_name",
            "sample_name",
            "precursor_id_count",
            "precursor_key_count",
            "protein_group_id_count",
            "protein_id_count",
            "observed_precursor_quantity_count",
            "observed_protein_quantity_count",
            "median_log10_precursor_quantity",
            "precursor_missing_fraction",
            "protein_missing_fraction",
            "weak_run_flag_count",
            "flagged",
        ]
    )
    for entry in report.run_entries:
        writer.writerow(
            [
                entry.run_name,
                entry.sample_name,
                entry.precursor_id_count,
                entry.precursor_key_count,
                entry.protein_group_id_count,
                entry.protein_id_count,
                entry.observed_precursor_quantity_count,
                entry.observed_protein_quantity_count,
                ""
                if entry.median_log10_precursor_quantity is None
                else f"{entry.median_log10_precursor_quantity:.6g}",
                f"{entry.precursor_missing_fraction:.6g}",
                f"{entry.protein_missing_fraction:.6g}",
                entry.weak_run_flag_count,
                str(entry.flagged).lower(),
            ]
        )
    return buffer.getvalue()


def render_dia_run_qc_intensity_distribution_tsv(report: DiaRunQcReport) -> str:
    """Render one DIA run-QC intensity distribution ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(["run_name", "sample_name", "bucket", "count"])
    for entry in report.intensity_distribution:
        writer.writerow(
            [entry.run_name, entry.sample_name, entry.bucket, entry.count]
        )
    return buffer.getvalue()


def render_dia_run_qc_correlation_tsv(report: DiaRunQcReport) -> str:
    """Render pairwise DIA run correlations."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "run_name_a",
            "sample_name_a",
            "run_name_b",
            "sample_name_b",
            "shared_precursor_key_count",
            "pearson_correlation",
        ]
    )
    for entry in report.pairwise_correlations:
        writer.writerow(
            [
                entry.run_name_a,
                entry.sample_name_a,
                entry.run_name_b,
                entry.sample_name_b,
                entry.shared_precursor_key_count,
                ""
                if entry.pearson_correlation is None
                else f"{entry.pearson_correlation:.6g}",
            ]
        )
    return buffer.getvalue()


def render_dia_run_qc_outlier_tsv(report: DiaRunQcReport) -> str:
    """Render flagged DIA runs and explicit reasons."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "run_name",
            "sample_name",
            "reason_code",
            "reason",
            "threshold_name",
            "threshold_value",
            "observed_value",
        ]
    )
    for entry in report.outlier_runs:
        for flag in entry.flags:
            writer.writerow(
                [
                    entry.run_name,
                    entry.sample_name,
                    flag.code.value,
                    flag.reason,
                    flag.threshold_name,
                    f"{flag.threshold_value:.6g}",
                    f"{flag.observed_value:.6g}",
                ]
            )
    return buffer.getvalue()


def export_dia_run_qc_summary_tsv(report: DiaRunQcReport, path: Path) -> None:
    write_output_table_tsv(path, render_dia_run_qc_summary_tsv(report))


def export_dia_run_qc_run_table_tsv(report: DiaRunQcReport, path: Path) -> None:
    write_output_table_tsv(path, render_dia_run_qc_run_table_tsv(report))


def export_dia_run_qc_intensity_distribution_tsv(
    report: DiaRunQcReport,
    path: Path,
) -> None:
    write_output_table_tsv(path, render_dia_run_qc_intensity_distribution_tsv(report))


def export_dia_run_qc_correlation_tsv(report: DiaRunQcReport, path: Path) -> None:
    write_output_table_tsv(path, render_dia_run_qc_correlation_tsv(report))


def export_dia_run_qc_outlier_tsv(report: DiaRunQcReport, path: Path) -> None:
    write_output_table_tsv(path, render_dia_run_qc_outlier_tsv(report))


def _filtered_precursor_rows(
    rows: tuple[DiaNnPrecursorReviewEntry, ...],
    *,
    include_decoys: bool,
    max_q_value: float | None,
) -> tuple[DiaNnPrecursorReviewEntry, ...]:
    filtered: list[DiaNnPrecursorReviewEntry] = []
    for row in rows:
        if not include_decoys and row.target_decoy_label is TargetDecoyLabel.DECOY:
            continue
        if max_q_value is not None and row.q_value > max_q_value:
            continue
        filtered.append(row)
    return tuple(filtered)


def _filtered_protein_rows(
    rows: tuple[DiaNnProteinGroupReviewEntry, ...],
    *,
    include_decoys: bool,
    max_q_value: float | None,
) -> tuple[DiaNnProteinGroupReviewEntry, ...]:
    filtered: list[DiaNnProteinGroupReviewEntry] = []
    for row in rows:
        if not include_decoys and row.target_decoy_label is TargetDecoyLabel.DECOY:
            continue
        if max_q_value is not None and row.q_value > max_q_value:
            continue
        filtered.append(row)
    return tuple(filtered)


def _stable_precursor_key(row: DiaNnPrecursorReviewEntry) -> str:
    return f"{row.modified_peptide}|z{row.charge}|{row.protein_group_id}"


def _fraction(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return min(1.0, max(0.0, numerator / denominator))


def _intensity_distribution(
    observed_precursor_quantities: Sequence[float | None],
) -> dict[str, int]:
    distribution = {
        "<1e5": 0,
        "1e5-1e6": 0,
        "1e6+": 0,
    }
    for quantity in observed_precursor_quantities:
        if quantity is None:
            continue
        if quantity < 1.0e5:
            distribution["<1e5"] += 1
        elif quantity < 1.0e6:
            distribution["1e5-1e6"] += 1
        else:
            distribution["1e6+"] += 1
    return distribution


def _build_pairwise_correlations(
    *,
    run_names: list[str],
    sample_name_by_run: dict[str, str],
    run_precursor_quantity_maps: dict[str, dict[str, float]],
) -> tuple[DiaRunQcCorrelationEntry, ...]:
    entries: list[DiaRunQcCorrelationEntry] = []
    for index, run_name_a in enumerate(run_names):
        for run_name_b in run_names[index + 1 :]:
            map_a = run_precursor_quantity_maps.get(run_name_a, {})
            map_b = run_precursor_quantity_maps.get(run_name_b, {})
            shared_keys = sorted(set(map_a) & set(map_b))
            correlation = None
            if len(shared_keys) >= 2:
                correlation = _pearson_correlation(
                    [math.log10(map_a[key]) for key in shared_keys if map_a[key] > 0.0],
                    [math.log10(map_b[key]) for key in shared_keys if map_b[key] > 0.0],
                )
            entries.append(
                DiaRunQcCorrelationEntry(
                    run_name_a=run_name_a,
                    sample_name_a=sample_name_by_run.get(run_name_a, "unknown"),
                    run_name_b=run_name_b,
                    sample_name_b=sample_name_by_run.get(run_name_b, "unknown"),
                    shared_precursor_key_count=len(shared_keys),
                    pearson_correlation=correlation,
                )
            )
    return tuple(entries)


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[midpoint])
    return float((ordered[midpoint - 1] + ordered[midpoint]) / 2.0)


def _pearson_correlation(values_a: list[float], values_b: list[float]) -> float | None:
    if len(values_a) != len(values_b) or len(values_a) < 2:
        return None
    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)
    numerator = sum(
        (value_a - mean_a) * (value_b - mean_b)
        for value_a, value_b in zip(values_a, values_b, strict=False)
    )
    denominator_a = math.sqrt(sum((value - mean_a) ** 2 for value in values_a))
    denominator_b = math.sqrt(sum((value - mean_b) ** 2 for value in values_b))
    if denominator_a == 0.0 or denominator_b == 0.0:
        return None
    return numerator / (denominator_a * denominator_b)


def _median_correlation_by_run(
    correlations: tuple[DiaRunQcCorrelationEntry, ...],
) -> dict[str, float | None]:
    values_by_run: dict[str, list[float]] = {}
    for entry in correlations:
        if entry.pearson_correlation is None:
            continue
        values_by_run.setdefault(entry.run_name_a, []).append(entry.pearson_correlation)
        values_by_run.setdefault(entry.run_name_b, []).append(entry.pearson_correlation)
    all_runs = {
        run_name
        for entry in correlations
        for run_name in (entry.run_name_a, entry.run_name_b)
    }
    return {
        run_name: _median(values_by_run[run_name]) if run_name in values_by_run else None
        for run_name in all_runs
    }


def _max_shared_precursor_key_count_by_run(
    correlations: tuple[DiaRunQcCorrelationEntry, ...],
) -> dict[str, int]:
    counts_by_run: dict[str, int] = {}
    for entry in correlations:
        counts_by_run[entry.run_name_a] = max(
            counts_by_run.get(entry.run_name_a, 0),
            entry.shared_precursor_key_count,
        )
        counts_by_run[entry.run_name_b] = max(
            counts_by_run.get(entry.run_name_b, 0),
            entry.shared_precursor_key_count,
        )
    return counts_by_run
