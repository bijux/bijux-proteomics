# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""FragPipe bundle import over PSM, peptide, and protein evidence tables."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.search_engine_modified_peptides import (
    SearchEngineModifiedPeptideDialect,
    build_search_engine_modified_peptide_report,
)
from bijux_proteomics.identification.contracts import (
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    parse_target_decoy_label,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    normalize_search_results_with_adapter,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics_foundation import JsonModel


class FragpipePsmReviewEntry(JsonModel):
    """Reviewer-facing PSM row from one FragPipe import bundle."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    canonical_modified_peptide: str | None = None
    charge: int = Field(..., ge=1)
    hyperscore: float
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    assigned_modifications: tuple[str, ...] = Field(default_factory=tuple)
    observed_modifications: tuple[str, ...] = Field(default_factory=tuple)
    mass_difference: float | None = None
    open_search_candidate: bool = False


class FragpipePeptideReviewEntry(JsonModel):
    """Reviewer-facing peptide-table row from one FragPipe bundle."""

    model_config = ConfigDict(extra="forbid")

    peptide: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    canonical_modified_peptide: str | None = None
    charge: int | None = Field(default=None, ge=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    mapped_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    assigned_modifications: tuple[str, ...] = Field(default_factory=tuple)
    observed_modifications: tuple[str, ...] = Field(default_factory=tuple)
    hyperscore: float | None = None
    probability: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0)
    spectral_count: int | None = Field(default=None, ge=0)
    mass_difference: float | None = None
    open_search_candidate: bool = False


class FragpipeProteinReviewEntry(JsonModel):
    """Reviewer-facing protein-table row from one FragPipe bundle."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    entry_name: str | None = None
    gene_name: str | None = None
    description: str | None = None
    coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    total_peptides: int | None = Field(default=None, ge=0)
    unique_peptides: int | None = Field(default=None, ge=0)
    spectral_count: int | None = Field(default=None, ge=0)
    probability: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel


class FragpipeImportSummary(JsonModel):
    """Compact summary over one imported FragPipe result bundle."""

    model_config = ConfigDict(extra="forbid")

    accepted_psm_count: int = Field(..., ge=0)
    rejected_psm_count: int = Field(..., ge=0)
    peptide_row_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    modified_psm_count: int = Field(..., ge=0)
    modified_peptide_row_count: int = Field(..., ge=0)
    open_search_psm_count: int = Field(..., ge=0)
    open_search_peptide_count: int = Field(..., ge=0)
    q_value_psm_count: int = Field(..., ge=0)
    q_value_peptide_count: int = Field(..., ge=0)
    mapped_protein_count: int = Field(..., ge=0)
    target_protein_count: int = Field(..., ge=0)
    decoy_protein_count: int = Field(..., ge=0)


class FragpipeImportReport(JsonModel):
    """One governed FragPipe bundle import report."""

    model_config = ConfigDict(extra="forbid")

    psm_normalization: SearchAdapterNormalizationReport
    psm_rows: tuple[FragpipePsmReviewEntry, ...] = Field(default_factory=tuple)
    peptide_rows: tuple[FragpipePeptideReviewEntry, ...] = Field(default_factory=tuple)
    protein_rows: tuple[FragpipeProteinReviewEntry, ...] = Field(default_factory=tuple)
    summary: FragpipeImportSummary


def build_fragpipe_import_report(
    psm_tsv_path: Path,
    *,
    peptide_tsv_path: Path,
    protein_tsv_path: Path,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
    open_search_mass_tolerance: float = 0.01,
) -> FragpipeImportReport:
    """Import one FragPipe result bundle with explicit table preservation."""
    if open_search_mass_tolerance < 0:
        raise ValueError("open_search_mass_tolerance must be non-negative")
    active_decoy_policy = decoy_policy or TargetDecoyLabelPolicy(
        protein_prefix="DECOY_"
    )
    psm_normalization = normalize_search_results_with_adapter(
        source_path=psm_tsv_path,
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        dialect_id="fragpipe-psm",
    )
    psm_rows = _build_fragpipe_psm_rows(
        normalization_report=psm_normalization,
        open_search_mass_tolerance=open_search_mass_tolerance,
    )
    peptide_rows = _parse_fragpipe_peptide_table(
        peptide_tsv_path,
        decoy_policy=active_decoy_policy,
        open_search_mass_tolerance=open_search_mass_tolerance,
    )
    protein_rows = _parse_fragpipe_protein_table(
        protein_tsv_path,
        decoy_policy=active_decoy_policy,
    )
    protein_refs = {
        protein_ref
        for row in peptide_rows
        for protein_ref in row.protein_refs + row.mapped_protein_refs
    }
    summary = FragpipeImportSummary(
        accepted_psm_count=len(psm_rows),
        rejected_psm_count=len(psm_normalization.parse_report.rejected_rows),
        peptide_row_count=len(peptide_rows),
        protein_row_count=len(protein_rows),
        modified_psm_count=sum(1 for row in psm_rows if _has_modified_content(row)),
        modified_peptide_row_count=sum(
            1 for row in peptide_rows if _has_modified_content(row)
        ),
        open_search_psm_count=sum(1 for row in psm_rows if row.open_search_candidate),
        open_search_peptide_count=sum(
            1 for row in peptide_rows if row.open_search_candidate
        ),
        q_value_psm_count=sum(1 for row in psm_rows if row.q_value is not None),
        q_value_peptide_count=sum(1 for row in peptide_rows if row.q_value is not None),
        mapped_protein_count=len(protein_refs),
        target_protein_count=sum(
            1
            for row in protein_rows
            if row.target_decoy_label is TargetDecoyLabel.TARGET
        ),
        decoy_protein_count=sum(
            1
            for row in protein_rows
            if row.target_decoy_label is TargetDecoyLabel.DECOY
        ),
    )
    return FragpipeImportReport(
        psm_normalization=psm_normalization,
        psm_rows=psm_rows,
        peptide_rows=peptide_rows,
        protein_rows=protein_rows,
        summary=summary,
    )


def render_fragpipe_summary_tsv(summary: FragpipeImportSummary) -> str:
    """Render the one-row FragPipe bundle summary as TSV."""
    header = (
        "accepted_psm_count",
        "rejected_psm_count",
        "peptide_row_count",
        "protein_row_count",
        "modified_psm_count",
        "modified_peptide_row_count",
        "open_search_psm_count",
        "open_search_peptide_count",
        "q_value_psm_count",
        "q_value_peptide_count",
        "mapped_protein_count",
        "target_protein_count",
        "decoy_protein_count",
    )
    row = (
        str(summary.accepted_psm_count),
        str(summary.rejected_psm_count),
        str(summary.peptide_row_count),
        str(summary.protein_row_count),
        str(summary.modified_psm_count),
        str(summary.modified_peptide_row_count),
        str(summary.open_search_psm_count),
        str(summary.open_search_peptide_count),
        str(summary.q_value_psm_count),
        str(summary.q_value_peptide_count),
        str(summary.mapped_protein_count),
        str(summary.target_protein_count),
        str(summary.decoy_protein_count),
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_fragpipe_psm_tsv(rows: tuple[FragpipePsmReviewEntry, ...]) -> str:
    """Render reviewer-facing FragPipe PSM rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "spectrum_id",
        "charge",
        "canonical_peptide",
    )
    lines = [
        "\t".join(
            (
                "spectrum_id",
                "peptide",
                "canonical_peptide",
                "modified_peptide",
                "canonical_modified_peptide",
                "charge",
                "hyperscore",
                "q_value",
                "protein_refs",
                "target_decoy_label",
                "assigned_modifications",
                "observed_modifications",
                "mass_difference",
                "open_search_candidate",
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.spectrum_id,
                    row.peptide,
                    row.canonical_peptide,
                    row.modified_peptide or "",
                    row.canonical_modified_peptide or "",
                    str(row.charge),
                    f"{row.hyperscore:.6g}",
                    "" if row.q_value is None else f"{row.q_value:.6g}",
                    ";".join(sort_strings(row.protein_refs)),
                    row.target_decoy_label.value,
                    ";".join(sort_strings(row.assigned_modifications)),
                    ";".join(sort_strings(row.observed_modifications)),
                    "" if row.mass_difference is None else f"{row.mass_difference:.6g}",
                    "1" if row.open_search_candidate else "0",
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_fragpipe_peptide_tsv(rows: tuple[FragpipePeptideReviewEntry, ...]) -> str:
    """Render reviewer-facing FragPipe peptide rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "peptide",
        "canonical_modified_peptide",
        "charge",
    )
    lines = [
        "\t".join(
            (
                "peptide",
                "modified_peptide",
                "canonical_modified_peptide",
                "charge",
                "protein_refs",
                "mapped_protein_refs",
                "assigned_modifications",
                "observed_modifications",
                "hyperscore",
                "probability",
                "q_value",
                "spectral_count",
                "mass_difference",
                "open_search_candidate",
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.peptide,
                    row.modified_peptide or "",
                    row.canonical_modified_peptide or "",
                    "" if row.charge is None else str(row.charge),
                    ";".join(sort_strings(row.protein_refs)),
                    ";".join(sort_strings(row.mapped_protein_refs)),
                    ";".join(sort_strings(row.assigned_modifications)),
                    ";".join(sort_strings(row.observed_modifications)),
                    "" if row.hyperscore is None else f"{row.hyperscore:.6g}",
                    "" if row.probability is None else f"{row.probability:.6g}",
                    "" if row.q_value is None else f"{row.q_value:.6g}",
                    "" if row.spectral_count is None else str(row.spectral_count),
                    "" if row.mass_difference is None else f"{row.mass_difference:.6g}",
                    "1" if row.open_search_candidate else "0",
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_fragpipe_protein_tsv(rows: tuple[FragpipeProteinReviewEntry, ...]) -> str:
    """Render reviewer-facing FragPipe protein rows as TSV."""
    ordered_rows = sort_rows_by_fields(rows, "protein_ref")
    lines = [
        "\t".join(
            (
                "protein_ref",
                "entry_name",
                "gene_name",
                "description",
                "coverage_fraction",
                "total_peptides",
                "unique_peptides",
                "spectral_count",
                "probability",
                "target_decoy_label",
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.protein_ref,
                    row.entry_name or "",
                    row.gene_name or "",
                    row.description or "",
                    ""
                    if row.coverage_fraction is None
                    else f"{row.coverage_fraction:.6g}",
                    "" if row.total_peptides is None else str(row.total_peptides),
                    "" if row.unique_peptides is None else str(row.unique_peptides),
                    "" if row.spectral_count is None else str(row.spectral_count),
                    "" if row.probability is None else f"{row.probability:.6g}",
                    row.target_decoy_label.value,
                )
            )
        )
    return "\n".join(lines) + "\n"


def _build_fragpipe_psm_rows(
    *,
    normalization_report: SearchAdapterNormalizationReport,
    open_search_mass_tolerance: float,
) -> tuple[FragpipePsmReviewEntry, ...]:
    accepted_rows = tuple(
        row
        for row in normalization_report.evidence_rows
        if row.accepted and row.normalized_record
    )
    rows: list[FragpipePsmReviewEntry] = []
    for row in accepted_rows:
        record = row.normalized_record
        if record is None:
            continue
        raw = row.raw_fields
        modified_peptide = raw.get("Modified Peptide", "").strip() or None
        canonical_modified = _canonical_modified_peptide(modified_peptide)
        mass_difference = _optional_float(raw.get("Mass Difference"))
        rows.append(
            FragpipePsmReviewEntry(
                spectrum_id=record.spectrum_id,
                peptide=record.peptide,
                canonical_peptide=record.canonical_peptide,
                modified_peptide=modified_peptide,
                canonical_modified_peptide=canonical_modified,
                charge=record.charge,
                hyperscore=record.score,
                q_value=record.q_value,
                protein_refs=record.protein_refs,
                target_decoy_label=record.target_decoy_label,
                assigned_modifications=_split_multi_value(
                    raw.get("Assigned Modifications")
                ),
                observed_modifications=_split_multi_value(
                    raw.get("Observed Modifications")
                ),
                mass_difference=mass_difference,
                open_search_candidate=_is_open_search_candidate(
                    mass_difference,
                    tolerance=open_search_mass_tolerance,
                ),
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.spectrum_id,
                row.q_value if row.q_value is not None else float("inf"),
                -row.hyperscore,
            ),
        )
    )


def _parse_fragpipe_peptide_table(
    path: Path,
    *,
    decoy_policy: TargetDecoyLabelPolicy,
    open_search_mass_tolerance: float,
) -> tuple[FragpipePeptideReviewEntry, ...]:
    required = ("Peptide", "Modified Peptide", "Protein")
    rows: list[FragpipePeptideReviewEntry] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("FragPipe peptide table must include a header row")
        for column in required:
            if column not in reader.fieldnames:
                raise ValueError(f"missing required FragPipe peptide column {column!r}")
        for row in reader:
            peptide = str(row.get("Peptide", "")).strip()
            modified_peptide = str(row.get("Modified Peptide", "")).strip() or None
            mass_difference = _optional_float(row.get("Mass Difference"))
            proteins = _split_multi_value(row.get("Protein"))
            mapped_proteins = _split_multi_value(row.get("Mapped Proteins"))
            rows.append(
                FragpipePeptideReviewEntry(
                    peptide=peptide,
                    modified_peptide=modified_peptide,
                    canonical_modified_peptide=_canonical_modified_peptide(
                        modified_peptide
                    ),
                    charge=_optional_int(row.get("Charge")),
                    protein_refs=proteins,
                    mapped_protein_refs=mapped_proteins,
                    assigned_modifications=_split_multi_value(
                        row.get("Assigned Modifications")
                    ),
                    observed_modifications=_split_multi_value(
                        row.get("Observed Modifications")
                    ),
                    hyperscore=_optional_float(row.get("Hyperscore")),
                    probability=_optional_float(row.get("Probability")),
                    q_value=_optional_float(row.get("QValue")),
                    spectral_count=_optional_int(row.get("Spectral Count")),
                    mass_difference=mass_difference,
                    open_search_candidate=_is_open_search_candidate(
                        mass_difference,
                        tolerance=open_search_mass_tolerance,
                    ),
                )
            )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.q_value if row.q_value is not None else float("inf"),
                -(row.hyperscore or 0.0),
                row.peptide,
            ),
        )
    )


def _parse_fragpipe_protein_table(
    path: Path,
    *,
    decoy_policy: TargetDecoyLabelPolicy,
) -> tuple[FragpipeProteinReviewEntry, ...]:
    required = ("Protein",)
    rows: list[FragpipeProteinReviewEntry] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("FragPipe protein table must include a header row")
        for column in required:
            if column not in reader.fieldnames:
                raise ValueError(f"missing required FragPipe protein column {column!r}")
        for row in reader:
            protein_ref = str(row.get("Protein", "")).strip()
            rows.append(
                FragpipeProteinReviewEntry(
                    protein_ref=protein_ref,
                    entry_name=_optional_text(row.get("Entry Name")),
                    gene_name=_optional_text(row.get("Gene")),
                    description=_optional_text(row.get("Protein Description")),
                    coverage_fraction=_optional_float(row.get("Coverage")),
                    total_peptides=_optional_int(row.get("Total Peptides")),
                    unique_peptides=_optional_int(row.get("Unique Peptides")),
                    spectral_count=_optional_int(row.get("Spectral Count")),
                    probability=_optional_float(row.get("Probability")),
                    target_decoy_label=parse_target_decoy_label(
                        protein_refs=(protein_ref,),
                        explicit_label=None,
                        policy=decoy_policy,
                    ),
                )
            )
    return tuple(sorted(rows, key=lambda row: row.protein_ref))


def _canonical_modified_peptide(notation: str | None) -> str | None:
    if notation is None:
        return None
    try:
        return build_search_engine_modified_peptide_report(
            notation,
            dialect=SearchEngineModifiedPeptideDialect.FRAGPIPE,
        ).canonical_notation
    except ValueError:
        return None


def _split_multi_value(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    text = str(value).strip()
    if not text:
        return ()
    separators = (";", ",")
    tokens = [text]
    for separator in separators:
        expanded: list[str] = []
        for token in tokens:
            expanded.extend(token.split(separator))
        tokens = expanded
    normalized = tuple(token.strip() for token in tokens if token.strip())
    return tuple(dict.fromkeys(normalized))


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


def _is_open_search_candidate(
    mass_difference: float | None, *, tolerance: float
) -> bool:
    if mass_difference is None:
        return False
    return abs(mass_difference) > tolerance


def _has_modified_content(
    row: FragpipePsmReviewEntry | FragpipePeptideReviewEntry,
) -> bool:
    if row.canonical_modified_peptide is None:
        return False
    return row.canonical_modified_peptide != row.peptide
