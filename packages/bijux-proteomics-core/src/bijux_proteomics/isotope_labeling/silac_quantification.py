# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned SILAC pair and triplet quantification over labeled feature evidence."""

from __future__ import annotations

from collections.abc import Iterable
import csv
from enum import StrEnum
from io import StringIO
import math
from pathlib import Path

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics._scientific_tables import (
    build_silac_feature_table_schema,
    validate_scientific_table,
)
from bijux_proteomics_foundation import JsonModel


class SilacLabel(StrEnum):
    """Supported SILAC label states."""

    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


class SilacColumnMapping(JsonModel):
    """Column mapping for governed SILAC feature-table import."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = "sample_id"
    peptide: str = "peptide"
    protein_refs: str = "protein_refs"
    charge: str = "charge"
    label: str = "label"
    intensity: str = "intensity"
    feature_id: str = "feature_id"
    protein_separator: str = ";"


class SilacFeatureObservation(JsonModel):
    """One SILAC-labeled peptide observation from a feature table."""

    model_config = ConfigDict(extra="forbid")

    feature_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    charge: int = Field(..., ge=1)
    label: SilacLabel
    intensity: float = Field(..., ge=0.0)


class RejectedSilacFeatureRow(JsonModel):
    """One rejected SILAC feature row with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    reason: str = Field(..., min_length=1)


class SilacImportSummary(JsonModel):
    """Compact summary over one SILAC feature-table import."""

    model_config = ConfigDict(extra="forbid")

    total_row_count: int = Field(..., ge=0)
    accepted_row_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)


class SilacImportReport(JsonModel):
    """Governed SILAC feature-table import surface."""

    model_config = ConfigDict(extra="forbid")

    accepted_rows: tuple[SilacFeatureObservation, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedSilacFeatureRow, ...] = Field(default_factory=tuple)
    summary: SilacImportSummary
    mapping: SilacColumnMapping
    note: str = Field(..., min_length=1)


class SilacQuantificationPolicy(JsonModel):
    """Policy for SILAC pair or triplet ratio quantification."""

    model_config = ConfigDict(extra="forbid")

    expected_labels: tuple[SilacLabel, ...] = (
        SilacLabel.LIGHT,
        SilacLabel.HEAVY,
    )
    reference_label: SilacLabel = SilacLabel.LIGHT
    separate_charge_states: bool = True

    @model_validator(mode="after")
    def _validate_expected_labels(self) -> SilacQuantificationPolicy:
        normalized = tuple(dict.fromkeys(self.expected_labels))
        if len(normalized) < 2:
            raise ValueError(
                "silac quantification requires at least two expected labels"
            )
        if self.reference_label not in normalized:
            raise ValueError("reference label must be included in expected labels")
        self.expected_labels = normalized
        return self


class SilacPeptideRatioEntry(JsonModel):
    """One SILAC peptide ratio against the governed reference label."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    charge: int | None = Field(default=None, ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    numerator_label: SilacLabel
    reference_label: SilacLabel
    numerator_abundance: float | None = Field(default=None, ge=0.0)
    reference_abundance: float | None = Field(default=None, ge=0.0)
    ratio: float | None = Field(default=None, ge=0.0)
    log2_ratio: float | None = None
    missing_reason: str | None = None
    note: str = Field(..., min_length=1)


class SilacProteinRatioEntry(JsonModel):
    """One SILAC protein ratio against the governed reference label."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    contributing_peptide_ids: tuple[str, ...] = Field(default_factory=tuple)
    numerator_label: SilacLabel
    reference_label: SilacLabel
    numerator_abundance: float | None = Field(default=None, ge=0.0)
    reference_abundance: float | None = Field(default=None, ge=0.0)
    ratio: float | None = Field(default=None, ge=0.0)
    log2_ratio: float | None = None
    missing_reason: str | None = None
    note: str = Field(..., min_length=1)


class SilacRatioSummary(JsonModel):
    """Compact summary over one SILAC ratio-analysis run."""

    model_config = ConfigDict(extra="forbid")

    sample_count: int = Field(..., ge=0)
    expected_label_count: int = Field(..., ge=0)
    peptide_ratio_count: int = Field(..., ge=0)
    protein_ratio_count: int = Field(..., ge=0)
    missing_ratio_count: int = Field(..., ge=0)


class SilacRatioReport(JsonModel):
    """Owned SILAC ratio-analysis surface."""

    model_config = ConfigDict(extra="forbid")

    import_report: SilacImportReport
    policy: SilacQuantificationPolicy
    peptide_ratios: tuple[SilacPeptideRatioEntry, ...] = Field(default_factory=tuple)
    protein_ratios: tuple[SilacProteinRatioEntry, ...] = Field(default_factory=tuple)
    summary: SilacRatioSummary
    note: str = Field(..., min_length=1)


def parse_silac_feature_table(
    path: Path,
    *,
    mapping: SilacColumnMapping | None = None,
) -> SilacImportReport:
    """Parse one SILAC feature table into a governed import report."""

    active_mapping = mapping or SilacColumnMapping()
    validation_report = validate_scientific_table(
        path,
        schema=build_silac_feature_table_schema(active_mapping),
    )
    accepted_rows: list[SilacFeatureObservation] = []
    rejected_rows: list[RejectedSilacFeatureRow] = [
        RejectedSilacFeatureRow(
            row_number=row.row_number,
            reason=row.issues[0].message
            if row.issues
            else "silac feature row was rejected",
        )
        for row in validation_report.rejected_rows
    ]
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows_by_number = dict(enumerate(reader, start=2))
        for accepted_row in validation_report.accepted_rows:
            row_number = accepted_row.row_number
            row = rows_by_number.get(row_number, {})
            try:
                accepted_rows.append(
                    SilacFeatureObservation(
                        feature_id=(row.get(active_mapping.feature_id) or "").strip(),
                        sample_id=(row.get(active_mapping.sample_id) or "").strip(),
                        peptide=(row.get(active_mapping.peptide) or "").strip(),
                        protein_refs=_split_protein_refs(
                            row.get(active_mapping.protein_refs),
                            separator=active_mapping.protein_separator,
                        ),
                        charge=int((row.get(active_mapping.charge) or "").strip()),
                        label=SilacLabel(
                            (row.get(active_mapping.label) or "").strip().lower()
                        ),
                        intensity=float(
                            (row.get(active_mapping.intensity) or "").strip()
                        ),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                rejected_rows.append(
                    RejectedSilacFeatureRow(
                        row_number=row_number,
                        reason=str(exc),
                    )
                )
    sample_count = len({row.sample_id for row in accepted_rows})
    return SilacImportReport(
        accepted_rows=tuple(accepted_rows),
        rejected_rows=tuple(rejected_rows),
        summary=SilacImportSummary(
            total_row_count=len(accepted_rows) + len(rejected_rows),
            accepted_row_count=len(accepted_rows),
            rejected_row_count=len(rejected_rows),
            sample_count=sample_count,
        ),
        mapping=active_mapping,
        note=(
            "silac feature import preserves explicit label state, charge state, and peptide/protein identity for downstream ratio quantification"
        ),
    )


def build_silac_ratio_report(
    import_report: SilacImportReport,
    *,
    policy: SilacQuantificationPolicy | None = None,
) -> SilacRatioReport:
    """Build SILAC peptide ratios against the governed reference label."""

    active_policy = policy or SilacQuantificationPolicy()
    grouped: dict[tuple[str, str, int | None], list[SilacFeatureObservation]] = {}
    for row in import_report.accepted_rows:
        key = (
            row.sample_id,
            row.peptide,
            row.charge if active_policy.separate_charge_states else None,
        )
        grouped.setdefault(key, []).append(row)

    peptide_ratios: list[SilacPeptideRatioEntry] = []
    for sample_id, peptide, charge in sorted(grouped):
        observations = grouped[(sample_id, peptide, charge)]
        label_to_abundance: dict[SilacLabel, float] = {}
        protein_refs = observations[0].protein_refs
        for observation in observations:
            label_to_abundance[observation.label] = (
                label_to_abundance.get(observation.label, 0.0) + observation.intensity
            )
        reference_abundance = label_to_abundance.get(active_policy.reference_label)
        peptide_id = (
            f"{peptide}/z{charge}"
            if active_policy.separate_charge_states and charge is not None
            else peptide
        )
        for numerator_label in active_policy.expected_labels:
            if numerator_label is active_policy.reference_label:
                continue
            numerator_abundance = label_to_abundance.get(numerator_label)
            ratio, log2_ratio, missing_reason = _build_ratio(
                numerator_abundance=numerator_abundance,
                reference_abundance=reference_abundance,
            )
            peptide_ratios.append(
                SilacPeptideRatioEntry(
                    sample_id=sample_id,
                    peptide_id=peptide_id,
                    peptide_sequence=peptide,
                    charge=charge,
                    protein_refs=protein_refs,
                    numerator_label=numerator_label,
                    reference_label=active_policy.reference_label,
                    numerator_abundance=numerator_abundance,
                    reference_abundance=reference_abundance,
                    ratio=ratio,
                    log2_ratio=log2_ratio,
                    missing_reason=missing_reason,
                    note=(
                        "silac peptide ratio compares the labeled numerator channel to the governed reference label"
                        if missing_reason is None
                        else "silac peptide ratio is preserved even though one expected label member is missing"
                    ),
                )
            )
    protein_ratios = _build_protein_ratios(
        peptide_ratios=tuple(peptide_ratios),
        policy=active_policy,
    )
    all_ratio_entries: tuple[SilacPeptideRatioEntry | SilacProteinRatioEntry, ...] = (
        *peptide_ratios,
        *protein_ratios,
    )
    missing_ratio_count = sum(
        1 for entry in all_ratio_entries if entry.missing_reason is not None
    )
    return SilacRatioReport(
        import_report=import_report,
        policy=active_policy,
        peptide_ratios=tuple(peptide_ratios),
        protein_ratios=protein_ratios,
        summary=SilacRatioSummary(
            sample_count=import_report.summary.sample_count,
            expected_label_count=len(active_policy.expected_labels),
            peptide_ratio_count=len(peptide_ratios),
            protein_ratio_count=len(protein_ratios),
            missing_ratio_count=missing_ratio_count,
        ),
        note=(
            "silac ratio analysis preserves peptide and protein label ratios with explicit missing pair-member evidence"
        ),
    )


def _split_protein_refs(value: str | None, *, separator: str) -> tuple[str, ...]:
    if value is None:
        return ()
    refs = tuple(token.strip() for token in value.split(separator) if token.strip())
    return tuple(dict.fromkeys(refs))


def _build_ratio(
    *,
    numerator_abundance: float | None,
    reference_abundance: float | None,
) -> tuple[float | None, float | None, str | None]:
    if numerator_abundance is None:
        return None, None, "numerator_label_missing"
    if reference_abundance is None:
        return None, None, "reference_label_missing"
    if reference_abundance <= 0.0:
        return None, None, "reference_label_zero"
    ratio = float(numerator_abundance) / float(reference_abundance)
    return ratio, float(math.log2(ratio)) if ratio > 0.0 else None, None


def _build_protein_ratios(
    *,
    peptide_ratios: tuple[SilacPeptideRatioEntry, ...],
    policy: SilacQuantificationPolicy,
) -> tuple[SilacProteinRatioEntry, ...]:
    grouped: dict[tuple[str, str, SilacLabel], list[SilacPeptideRatioEntry]] = {}
    protein_refs_by_group: dict[tuple[str, str], tuple[str, ...]] = {}
    peptide_ids_by_group: dict[tuple[str, str], set[str]] = {}
    for entry in peptide_ratios:
        for protein_ref in entry.protein_refs:
            grouped.setdefault(
                (entry.sample_id, protein_ref, entry.numerator_label),
                [],
            ).append(entry)
            protein_refs_by_group[(entry.sample_id, protein_ref)] = (protein_ref,)
            peptide_ids_by_group.setdefault((entry.sample_id, protein_ref), set()).add(
                entry.peptide_id
            )
    rows: list[SilacProteinRatioEntry] = []
    for sample_id, protein_id in sorted(peptide_ids_by_group):
        contributing_peptide_ids = tuple(
            sorted(peptide_ids_by_group[(sample_id, protein_id)])
        )
        for numerator_label in policy.expected_labels:
            if numerator_label is policy.reference_label:
                continue
            numerator_entries = grouped.get(
                (sample_id, protein_id, numerator_label), ()
            )
            numerator_abundance = _sum_present(
                entry.numerator_abundance for entry in numerator_entries
            )
            reference_abundance = _sum_present(
                entry.reference_abundance for entry in numerator_entries
            )
            ratio, log2_ratio, missing_reason = _build_ratio(
                numerator_abundance=numerator_abundance,
                reference_abundance=reference_abundance,
            )
            rows.append(
                SilacProteinRatioEntry(
                    sample_id=sample_id,
                    protein_id=protein_id,
                    protein_refs=protein_refs_by_group[(sample_id, protein_id)],
                    contributing_peptide_ids=contributing_peptide_ids,
                    numerator_label=numerator_label,
                    reference_label=policy.reference_label,
                    numerator_abundance=numerator_abundance,
                    reference_abundance=reference_abundance,
                    ratio=ratio,
                    log2_ratio=log2_ratio,
                    missing_reason=missing_reason,
                    note=(
                        "silac protein ratio aggregates labeled peptide abundances to the governed protein surface"
                        if missing_reason is None
                        else "silac protein ratio is preserved even though one protein-level label member is missing"
                    ),
                )
            )
    return tuple(rows)


def _sum_present(values: Iterable[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return float(sum(present))


def render_silac_ratio_summary_tsv(report: SilacRatioReport) -> str:
    """Render a compact summary over one SILAC ratio-analysis run."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_count",
            "expected_label_count",
            "peptide_ratio_count",
            "protein_ratio_count",
            "missing_ratio_count",
        ]
    )
    writer.writerow(
        [
            report.summary.sample_count,
            report.summary.expected_label_count,
            report.summary.peptide_ratio_count,
            report.summary.protein_ratio_count,
            report.summary.missing_ratio_count,
        ]
    )
    return buffer.getvalue()


def render_silac_peptide_ratio_tsv(report: SilacRatioReport) -> str:
    """Render the SILAC peptide ratio ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_id",
            "peptide_id",
            "peptide_sequence",
            "charge",
            "protein_refs",
            "numerator_label",
            "reference_label",
            "numerator_abundance",
            "reference_abundance",
            "ratio",
            "log2_ratio",
            "missing_reason",
            "note",
        ]
    )
    for entry in report.peptide_ratios:
        writer.writerow(
            [
                entry.sample_id,
                entry.peptide_id,
                entry.peptide_sequence,
                "" if entry.charge is None else entry.charge,
                ";".join(entry.protein_refs),
                entry.numerator_label.value,
                entry.reference_label.value,
                "" if entry.numerator_abundance is None else entry.numerator_abundance,
                "" if entry.reference_abundance is None else entry.reference_abundance,
                "" if entry.ratio is None else entry.ratio,
                "" if entry.log2_ratio is None else entry.log2_ratio,
                entry.missing_reason or "",
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_silac_protein_ratio_tsv(report: SilacRatioReport) -> str:
    """Render the SILAC protein ratio ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "sample_id",
            "protein_id",
            "protein_refs",
            "contributing_peptide_ids",
            "numerator_label",
            "reference_label",
            "numerator_abundance",
            "reference_abundance",
            "ratio",
            "log2_ratio",
            "missing_reason",
            "note",
        ]
    )
    for entry in report.protein_ratios:
        writer.writerow(
            [
                entry.sample_id,
                entry.protein_id,
                ";".join(entry.protein_refs),
                ";".join(entry.contributing_peptide_ids),
                entry.numerator_label.value,
                entry.reference_label.value,
                "" if entry.numerator_abundance is None else entry.numerator_abundance,
                "" if entry.reference_abundance is None else entry.reference_abundance,
                "" if entry.ratio is None else entry.ratio,
                "" if entry.log2_ratio is None else entry.log2_ratio,
                entry.missing_reason or "",
                entry.note,
            ]
        )
    return buffer.getvalue()


def export_silac_ratio_summary_tsv(report: SilacRatioReport, path: Path) -> None:
    """Write the compact SILAC ratio summary ledger."""

    write_output_table_tsv(path, render_silac_ratio_summary_tsv(report))


def export_silac_peptide_ratio_tsv(report: SilacRatioReport, path: Path) -> None:
    """Write the SILAC peptide ratio ledger."""

    write_output_table_tsv(path, render_silac_peptide_ratio_tsv(report))


def export_silac_protein_ratio_tsv(report: SilacRatioReport, path: Path) -> None:
    """Write the SILAC protein ratio ledger."""

    write_output_table_tsv(path, render_silac_protein_ratio_tsv(report))
