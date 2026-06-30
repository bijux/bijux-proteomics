# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Sage result import over realistic PSM exports."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.modified_peptide_parser import (
    SearchEngineModifiedPeptideDialect,
    build_search_engine_modified_peptide_report,
)
from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
    build_rejected_evidence_rows_from_psm_rows,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchParameterReport,
)
from bijux_proteomics.identification.search_adapters.normalization import (
    normalize_search_results_with_adapter,
)
from bijux_proteomics.identification.search_adapters.parameter_review import (
    parse_search_parameter_file,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics_foundation import JsonModel


class SagePsmReviewEntry(JsonModel):
    """Reviewer-facing row from one Sage PSM import."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    residue_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modification_count: int = Field(..., ge=0)
    charge: int = Field(..., ge=1)
    discriminant_score: float
    hyperscore: float | None = None
    q_value: float | None = Field(default=None, ge=0.0)
    peptide_q_value: float | None = Field(default=None, ge=0.0)
    protein_q_value: float | None = Field(default=None, ge=0.0)
    posterior_error: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    matched_peaks: int | None = Field(default=None, ge=0)
    longest_b: int | None = Field(default=None, ge=0)
    longest_y: int | None = Field(default=None, ge=0)
    matched_intensity_fraction: float | None = Field(default=None, ge=0.0)
    precursor_ppm: float | None = None
    fragment_ppm: float | None = None
    provenance: ImportedEvidenceProvenance


class SageCanonicalPsmEntry(JsonModel):
    """Canonical PSM plus Sage-native scoring and match-quality evidence."""

    model_config = ConfigDict(extra="forbid")

    record: PsmRecord
    discriminant_score: float
    hyperscore: float | None = None
    peptide_q_value: float | None = Field(default=None, ge=0.0)
    protein_q_value: float | None = Field(default=None, ge=0.0)
    posterior_error: float | None = Field(default=None, ge=0.0)
    matched_peaks: int | None = Field(default=None, ge=0)
    longest_b: int | None = Field(default=None, ge=0)
    longest_y: int | None = Field(default=None, ge=0)
    matched_intensity_fraction: float | None = Field(default=None, ge=0.0)
    precursor_ppm: float | None = None
    fragment_ppm: float | None = None


class SageImportSummary(JsonModel):
    """Compact summary over one imported Sage result table."""

    model_config = ConfigDict(extra="forbid")

    accepted_psm_count: int = Field(..., ge=0)
    rejected_psm_count: int = Field(..., ge=0)
    canonical_psm_count: int = Field(..., ge=0)
    modified_psm_count: int = Field(..., ge=0)
    q_value_psm_count: int = Field(..., ge=0)
    hyperscore_psm_count: int = Field(..., ge=0)
    multi_protein_psm_count: int = Field(..., ge=0)
    target_psm_count: int = Field(..., ge=0)
    decoy_psm_count: int = Field(..., ge=0)


class SageImportReport(JsonModel):
    """One governed Sage import report."""

    model_config = ConfigDict(extra="forbid")

    normalization: SearchAdapterNormalizationReport
    canonical_psms: tuple[SageCanonicalPsmEntry, ...] = Field(default_factory=tuple)
    psm_rows: tuple[SagePsmReviewEntry, ...] = Field(default_factory=tuple)
    rejected_evidence_rows: tuple[RejectedEvidenceTableEntry, ...] = Field(
        default_factory=tuple
    )
    summary: SageImportSummary
    parameter_report: SearchParameterReport | None = None
    dialect_id: str = Field(..., min_length=1)


def build_sage_import_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
) -> SageImportReport:
    """Import one Sage result table into an owned review contract."""
    dialect_id = _detect_sage_dialect(result_tsv_path)
    normalization = normalize_search_results_with_adapter(
        source_path=result_tsv_path,
        adapter_kind=SearchAdapterKind.SAGE,
        dialect_id=dialect_id,
    )
    canonical_psms = _build_sage_canonical_psm_rows(normalization)
    psm_rows = _build_sage_psm_rows(normalization)
    parameter_report = (
        None
        if config_path is None
        else parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind.SAGE,
        )
    )
    summary = SageImportSummary(
        accepted_psm_count=len(psm_rows),
        rejected_psm_count=len(normalization.parse_report.rejected_rows),
        canonical_psm_count=len(canonical_psms),
        modified_psm_count=sum(1 for row in psm_rows if row.modification_count > 0),
        q_value_psm_count=sum(1 for row in psm_rows if row.q_value is not None),
        hyperscore_psm_count=sum(1 for row in psm_rows if row.hyperscore is not None),
        multi_protein_psm_count=sum(1 for row in psm_rows if len(row.protein_refs) > 1),
        target_psm_count=sum(
            1 for row in psm_rows if row.target_decoy_label is TargetDecoyLabel.TARGET
        ),
        decoy_psm_count=sum(
            1 for row in psm_rows if row.target_decoy_label is TargetDecoyLabel.DECOY
        ),
    )
    return SageImportReport(
        normalization=normalization,
        canonical_psms=canonical_psms,
        psm_rows=psm_rows,
        rejected_evidence_rows=build_rejected_evidence_rows_from_psm_rows(
            normalization.parse_report.rejected_rows,
            source_file=result_tsv_path.name,
            entity_type="psm",
            entity_id_columns=("scannr", "peptide"),
        ),
        summary=summary,
        parameter_report=parameter_report,
        dialect_id=dialect_id,
    )


def render_sage_summary_tsv(summary: SageImportSummary) -> str:
    """Render the one-row Sage import summary as TSV."""
    header = (
        "accepted_psm_count",
        "rejected_psm_count",
        "canonical_psm_count",
        "modified_psm_count",
        "q_value_psm_count",
        "hyperscore_psm_count",
        "multi_protein_psm_count",
        "target_psm_count",
        "decoy_psm_count",
    )
    row = (
        str(summary.accepted_psm_count),
        str(summary.rejected_psm_count),
        str(summary.canonical_psm_count),
        str(summary.modified_psm_count),
        str(summary.q_value_psm_count),
        str(summary.hyperscore_psm_count),
        str(summary.multi_protein_psm_count),
        str(summary.target_psm_count),
        str(summary.decoy_psm_count),
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_sage_canonical_psm_tsv(rows: tuple[SageCanonicalPsmEntry, ...]) -> str:
    """Render canonical Sage PSM rows as TSV."""

    ordered_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                row.record.run_id or "",
                row.record.spectrum_id,
                row.record.charge,
                row.record.canonical_peptide,
            ),
        )
    )
    lines = [
        "\t".join(
            (
                "run_id",
                "spectrum_id",
                "peptide",
                "peptide_sequence",
                "modified_peptide",
                "canonical_peptide",
                "charge",
                "score",
                "q_value",
                "protein_refs",
                "target_decoy_label",
                "contaminant_flag",
                "discriminant_score",
                "hyperscore",
                "peptide_q_value",
                "protein_q_value",
                "posterior_error",
                "matched_peaks",
                "longest_b",
                "longest_y",
                "matched_intensity_fraction",
                "precursor_ppm",
                "fragment_ppm",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.record.run_id or "",
                    row.record.spectrum_id,
                    row.record.peptide,
                    row.record.peptide_sequence or "",
                    row.record.modified_peptide or "",
                    row.record.canonical_peptide,
                    str(row.record.charge),
                    f"{row.record.score:.6g}",
                    "" if row.record.q_value is None else f"{row.record.q_value:.6g}",
                    ";".join(sort_strings(row.record.protein_refs)),
                    row.record.target_decoy_label.value,
                    "1" if row.record.contaminant_flag else "0",
                    f"{row.discriminant_score:.6g}",
                    "" if row.hyperscore is None else f"{row.hyperscore:.6g}",
                    "" if row.peptide_q_value is None else f"{row.peptide_q_value:.6g}",
                    "" if row.protein_q_value is None else f"{row.protein_q_value:.6g}",
                    "" if row.posterior_error is None else f"{row.posterior_error:.6g}",
                    "" if row.matched_peaks is None else str(row.matched_peaks),
                    "" if row.longest_b is None else str(row.longest_b),
                    "" if row.longest_y is None else str(row.longest_y),
                    ""
                    if row.matched_intensity_fraction is None
                    else f"{row.matched_intensity_fraction:.6g}",
                    "" if row.precursor_ppm is None else f"{row.precursor_ppm:.6g}",
                    "" if row.fragment_ppm is None else f"{row.fragment_ppm:.6g}",
                    *(
                        row.record.provenance.to_tsv_cells()
                        if row.record.provenance
                        else ("", "", "", "")
                    ),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_sage_psm_tsv(rows: tuple[SagePsmReviewEntry, ...]) -> str:
    """Render reviewer-facing Sage PSM rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows, "spectrum_id", "charge", "canonical_peptide"
    )
    lines = [
        "\t".join(
            (
                "spectrum_id",
                "peptide",
                "residue_sequence",
                "canonical_peptide",
                "modification_count",
                "charge",
                "discriminant_score",
                "hyperscore",
                "q_value",
                "peptide_q_value",
                "protein_q_value",
                "posterior_error",
                "protein_refs",
                "target_decoy_label",
                "matched_peaks",
                "longest_b",
                "longest_y",
                "matched_intensity_fraction",
                "precursor_ppm",
                "fragment_ppm",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.spectrum_id,
                    row.peptide,
                    row.residue_sequence,
                    row.canonical_peptide,
                    str(row.modification_count),
                    str(row.charge),
                    f"{row.discriminant_score:.6g}",
                    "" if row.hyperscore is None else f"{row.hyperscore:.6g}",
                    "" if row.q_value is None else f"{row.q_value:.6g}",
                    "" if row.peptide_q_value is None else f"{row.peptide_q_value:.6g}",
                    "" if row.protein_q_value is None else f"{row.protein_q_value:.6g}",
                    "" if row.posterior_error is None else f"{row.posterior_error:.6g}",
                    ";".join(sort_strings(row.protein_refs)),
                    row.target_decoy_label.value,
                    "" if row.matched_peaks is None else str(row.matched_peaks),
                    "" if row.longest_b is None else str(row.longest_b),
                    "" if row.longest_y is None else str(row.longest_y),
                    ""
                    if row.matched_intensity_fraction is None
                    else f"{row.matched_intensity_fraction:.6g}",
                    "" if row.precursor_ppm is None else f"{row.precursor_ppm:.6g}",
                    "" if row.fragment_ppm is None else f"{row.fragment_ppm:.6g}",
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def _detect_sage_dialect(result_tsv_path: Path) -> str:
    with result_tsv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader, None)
    if not header:
        raise ValueError("Sage result table must include a header row")
    columns = {column.strip() for column in header if column.strip()}
    if {"scannr", "peptide", "discriminant_score", "hyperscore"}.issubset(columns):
        return "sage-psm"
    if {"scan_id", "stripped_peptide", "score_discriminant"}.issubset(columns):
        return "pipeline-export"
    return "default"


def _build_sage_psm_rows(
    normalization: SearchAdapterNormalizationReport,
) -> tuple[SagePsmReviewEntry, ...]:
    rows: list[SagePsmReviewEntry] = []
    for evidence_row in normalization.evidence_rows:
        if not evidence_row.accepted or evidence_row.normalized_record is None:
            continue
        record = evidence_row.normalized_record
        provenance = record.provenance
        if provenance is None:
            raise ValueError("normalized Sage PSM rows must preserve row provenance")
        peptide_report = build_search_engine_modified_peptide_report(
            record.peptide,
            dialect=SearchEngineModifiedPeptideDialect.SAGE,
        )
        raw = evidence_row.raw_fields
        rows.append(
            SagePsmReviewEntry(
                spectrum_id=record.spectrum_id,
                peptide=record.peptide,
                residue_sequence=peptide_report.residue_sequence,
                canonical_peptide=record.canonical_peptide,
                modification_count=len(peptide_report.modifications),
                charge=record.charge,
                discriminant_score=record.score,
                hyperscore=_optional_float(raw.get("hyperscore")),
                q_value=record.q_value,
                peptide_q_value=_optional_float(raw.get("peptide_q_value")),
                protein_q_value=_optional_float(raw.get("protein_q_value")),
                posterior_error=_optional_float(raw.get("posterior_error")),
                protein_refs=record.protein_refs,
                target_decoy_label=record.target_decoy_label,
                matched_peaks=_optional_int(raw.get("matched_peaks")),
                longest_b=_optional_int(raw.get("longest_b")),
                longest_y=_optional_int(raw.get("longest_y")),
                matched_intensity_fraction=_fraction(raw.get("matched_intensity_pct")),
                precursor_ppm=_optional_float(raw.get("precursor_ppm")),
                fragment_ppm=_optional_float(raw.get("fragment_ppm")),
                provenance=provenance,
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.q_value if row.q_value is not None else float("inf"),
                -row.discriminant_score,
                row.spectrum_id,
            ),
        )
    )


def _build_sage_canonical_psm_rows(
    normalization: SearchAdapterNormalizationReport,
) -> tuple[SageCanonicalPsmEntry, ...]:
    rows: list[SageCanonicalPsmEntry] = []
    for evidence_row in normalization.evidence_rows:
        if not evidence_row.accepted or evidence_row.normalized_record is None:
            continue
        raw = evidence_row.raw_fields
        run_id = _optional_text(raw.get("filename"))
        record = evidence_row.normalized_record.model_copy(update={"run_id": run_id})
        rows.append(
            SageCanonicalPsmEntry(
                record=record,
                discriminant_score=record.score,
                hyperscore=_optional_float(raw.get("hyperscore")),
                peptide_q_value=_optional_float(raw.get("peptide_q_value")),
                protein_q_value=_optional_float(raw.get("protein_q_value")),
                posterior_error=_optional_float(raw.get("posterior_error")),
                matched_peaks=_optional_int(raw.get("matched_peaks")),
                longest_b=_optional_int(raw.get("longest_b")),
                longest_y=_optional_int(raw.get("longest_y")),
                matched_intensity_fraction=_fraction(raw.get("matched_intensity_pct")),
                precursor_ppm=_optional_float(raw.get("precursor_ppm")),
                fragment_ppm=_optional_float(raw.get("fragment_ppm")),
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.record.q_value if row.record.q_value is not None else float("inf"),
                -row.discriminant_score,
                row.record.spectrum_id,
            ),
        )
    )


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return float(text)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return int(text)


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _fraction(value: object) -> float | None:
    numeric = _optional_float(value)
    if numeric is None:
        return None
    return numeric / 100.0
