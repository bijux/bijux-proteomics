# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""MaxQuant bundle import over evidence, peptide, and protein-group tables."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.chemistry.modified_peptide_parser import (
    SearchEngineModifiedPeptideDialect,
    build_search_engine_modified_peptide_report,
)
from bijux_proteomics.identification.contracts import (
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    parse_target_decoy_label,
)
from bijux_proteomics.identification.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
    build_rejected_evidence_rows_from_psm_rows,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchParameterReport,
    normalize_search_results_with_adapter,
    parse_search_parameter_file,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics._scientific_tables import (
    build_maxquant_peptides_schema,
    build_maxquant_protein_groups_schema,
    require_valid_scientific_table,
)
from bijux_proteomics_foundation import JsonModel

_MAXQUANT_DECOY_POLICY = TargetDecoyLabelPolicy(
    protein_prefix="REV__",
    explicit_decoy_values=("+", "decoy", "true", "1"),
    explicit_target_values=("", "target", "false", "0"),
)


class MaxquantLfqIntensityEntry(JsonModel):
    """One named LFQ intensity extracted from a MaxQuant protein-group row."""

    model_config = ConfigDict(extra="forbid")

    experiment_name: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    provenance: ImportedEvidenceProvenance


class MaxquantEvidenceReviewEntry(JsonModel):
    """Reviewer-facing row from one MaxQuant evidence import."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    experiment_name: str | None = None
    peptide: str = Field(..., min_length=1)
    residue_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modification_count: int = Field(..., ge=0)
    charge: int = Field(..., ge=1)
    score: float
    posterior_error_probability: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    reverse_flag: bool = False
    contaminant_flag: bool = False
    provenance: ImportedEvidenceProvenance


class MaxquantPeptideReviewEntry(JsonModel):
    """Reviewer-facing row from one MaxQuant peptides table."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    modified_sequence: str | None = None
    residue_sequence: str = Field(..., min_length=1)
    canonical_modified_peptide: str | None = None
    modification_count: int = Field(..., ge=0)
    leading_razor_protein: str | None = None
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    score: float | None = None
    posterior_error_probability: float | None = Field(default=None, ge=0.0)
    intensity: float | None = Field(default=None, ge=0.0)
    msms_count: int | None = Field(default=None, ge=0)
    target_decoy_label: TargetDecoyLabel
    reverse_flag: bool = False
    contaminant_flag: bool = False
    provenance: ImportedEvidenceProvenance


class MaxquantProteinGroupReviewEntry(JsonModel):
    """Reviewer-facing row from one MaxQuant protein-groups table."""

    model_config = ConfigDict(extra="forbid")

    protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    majority_protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    gene_names: tuple[str, ...] = Field(default_factory=tuple)
    fasta_headers: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int | None = Field(default=None, ge=0)
    razor_unique_peptide_count: int | None = Field(default=None, ge=0)
    msms_count: int | None = Field(default=None, ge=0)
    sequence_coverage_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    target_decoy_label: TargetDecoyLabel
    reverse_flag: bool = False
    contaminant_flag: bool = False
    only_identified_by_site: bool = False
    lfq_intensities: tuple[MaxquantLfqIntensityEntry, ...] = Field(
        default_factory=tuple
    )
    provenance: ImportedEvidenceProvenance


class MaxquantLfqMatrixCandidateEntry(JsonModel):
    """Owned LFQ-ready protein candidate derived from one MaxQuant protein group."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    majority_protein_ids: tuple[str, ...] = Field(default_factory=tuple)
    gene_names: tuple[str, ...] = Field(default_factory=tuple)
    fasta_headers: tuple[str, ...] = Field(default_factory=tuple)
    member_peptides: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    reverse_flag: bool = False
    contaminant_flag: bool = False
    only_identified_by_site: bool = False
    observed_lfq_experiment_count: int = Field(..., ge=0)
    lfq_intensities: tuple[MaxquantLfqIntensityEntry, ...] = Field(
        default_factory=tuple
    )
    provenance: ImportedEvidenceProvenance


class MaxquantImportSummary(JsonModel):
    """Compact summary over one imported MaxQuant result bundle."""

    model_config = ConfigDict(extra="forbid")

    accepted_evidence_count: int = Field(..., ge=0)
    rejected_evidence_count: int = Field(..., ge=0)
    peptide_row_count: int = Field(..., ge=0)
    protein_group_row_count: int = Field(..., ge=0)
    modified_evidence_count: int = Field(..., ge=0)
    modified_peptide_row_count: int = Field(..., ge=0)
    experiment_count: int = Field(..., ge=0)
    lfq_experiment_count: int = Field(..., ge=0)
    lfq_candidate_count: int = Field(..., ge=0)
    contaminant_evidence_count: int = Field(..., ge=0)
    reverse_evidence_count: int = Field(..., ge=0)
    contaminant_peptide_count: int = Field(..., ge=0)
    reverse_peptide_count: int = Field(..., ge=0)
    contaminant_protein_group_count: int = Field(..., ge=0)
    reverse_protein_group_count: int = Field(..., ge=0)
    experiment_names: tuple[str, ...] = Field(default_factory=tuple)
    lfq_experiment_names: tuple[str, ...] = Field(default_factory=tuple)


class MaxquantImportReport(JsonModel):
    """One governed MaxQuant bundle import report."""

    model_config = ConfigDict(extra="forbid")

    evidence_normalization: SearchAdapterNormalizationReport
    evidence_rows: tuple[MaxquantEvidenceReviewEntry, ...] = Field(
        default_factory=tuple
    )
    peptide_rows: tuple[MaxquantPeptideReviewEntry, ...] = Field(default_factory=tuple)
    protein_group_rows: tuple[MaxquantProteinGroupReviewEntry, ...] = Field(
        default_factory=tuple
    )
    lfq_matrix_candidates: tuple[MaxquantLfqMatrixCandidateEntry, ...] = Field(
        default_factory=tuple
    )
    rejected_evidence_rows: tuple[RejectedEvidenceTableEntry, ...] = Field(
        default_factory=tuple
    )
    summary: MaxquantImportSummary
    parameter_report: SearchParameterReport | None = None


def build_maxquant_import_report(
    evidence_txt_path: Path,
    *,
    peptides_txt_path: Path,
    protein_groups_txt_path: Path,
    config_path: Path | None = None,
) -> MaxquantImportReport:
    """Import one MaxQuant result bundle with explicit table preservation."""
    evidence_normalization = normalize_search_results_with_adapter(
        source_path=evidence_txt_path,
        adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
        dialect_id="bundle-evidence",
    )
    evidence_rows = _build_maxquant_evidence_rows(
        evidence_normalization,
        source_path=evidence_txt_path,
    )
    peptide_rows = _parse_maxquant_peptide_table(peptides_txt_path)
    protein_group_rows, lfq_experiment_names = _parse_maxquant_protein_groups_table(
        protein_groups_txt_path
    )
    lfq_matrix_candidates = build_maxquant_lfq_matrix_candidates(
        protein_group_rows,
        peptide_rows=peptide_rows,
    )
    experiment_names = tuple(
        sorted(
            {
                row.experiment_name
                for row in evidence_rows
                if row.experiment_name is not None and row.experiment_name.strip()
            }
        )
    )
    parameter_report = (
        None
        if config_path is None
        else parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind.MAXQUANT_EVIDENCE,
        )
    )
    summary = MaxquantImportSummary(
        accepted_evidence_count=len(evidence_rows),
        rejected_evidence_count=len(evidence_normalization.parse_report.rejected_rows),
        peptide_row_count=len(peptide_rows),
        protein_group_row_count=len(protein_group_rows),
        modified_evidence_count=sum(
            1 for row in evidence_rows if row.modification_count > 0
        ),
        modified_peptide_row_count=sum(
            1 for row in peptide_rows if row.modification_count > 0
        ),
        experiment_count=len(experiment_names),
        lfq_experiment_count=len(lfq_experiment_names),
        lfq_candidate_count=len(lfq_matrix_candidates),
        contaminant_evidence_count=sum(
            1 for row in evidence_rows if row.contaminant_flag
        ),
        reverse_evidence_count=sum(1 for row in evidence_rows if row.reverse_flag),
        contaminant_peptide_count=sum(
            1 for row in peptide_rows if row.contaminant_flag
        ),
        reverse_peptide_count=sum(1 for row in peptide_rows if row.reverse_flag),
        contaminant_protein_group_count=sum(
            1 for row in protein_group_rows if row.contaminant_flag
        ),
        reverse_protein_group_count=sum(
            1 for row in protein_group_rows if row.reverse_flag
        ),
        experiment_names=experiment_names,
        lfq_experiment_names=lfq_experiment_names,
    )
    return MaxquantImportReport(
        evidence_normalization=evidence_normalization,
        evidence_rows=evidence_rows,
        peptide_rows=peptide_rows,
        protein_group_rows=protein_group_rows,
        lfq_matrix_candidates=lfq_matrix_candidates,
        rejected_evidence_rows=build_rejected_evidence_rows_from_psm_rows(
            evidence_normalization.parse_report.rejected_rows,
            source_file=evidence_txt_path.name,
            entity_type="psm",
            entity_id_columns=(
                "MS/MS scan number",
                "Modified sequence",
                "Sequence",
            ),
        ),
        summary=summary,
        parameter_report=parameter_report,
    )


def render_maxquant_summary_tsv(summary: MaxquantImportSummary) -> str:
    """Render the one-row MaxQuant bundle summary as TSV."""
    header = (
        "accepted_evidence_count",
        "rejected_evidence_count",
        "peptide_row_count",
        "protein_group_row_count",
        "modified_evidence_count",
        "modified_peptide_row_count",
        "experiment_count",
        "lfq_experiment_count",
        "lfq_candidate_count",
        "contaminant_evidence_count",
        "reverse_evidence_count",
        "contaminant_peptide_count",
        "reverse_peptide_count",
        "contaminant_protein_group_count",
        "reverse_protein_group_count",
        "experiment_names",
        "lfq_experiment_names",
    )
    row = (
        str(summary.accepted_evidence_count),
        str(summary.rejected_evidence_count),
        str(summary.peptide_row_count),
        str(summary.protein_group_row_count),
        str(summary.modified_evidence_count),
        str(summary.modified_peptide_row_count),
        str(summary.experiment_count),
        str(summary.lfq_experiment_count),
        str(summary.lfq_candidate_count),
        str(summary.contaminant_evidence_count),
        str(summary.reverse_evidence_count),
        str(summary.contaminant_peptide_count),
        str(summary.reverse_peptide_count),
        str(summary.contaminant_protein_group_count),
        str(summary.reverse_protein_group_count),
        ";".join(summary.experiment_names),
        ";".join(summary.lfq_experiment_names),
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_maxquant_evidence_tsv(rows: tuple[MaxquantEvidenceReviewEntry, ...]) -> str:
    """Render reviewer-facing MaxQuant evidence rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "posterior_error_probability",
        "spectrum_id",
    )
    lines = [
        "\t".join(
            (
                "spectrum_id",
                "experiment_name",
                "peptide",
                "residue_sequence",
                "canonical_peptide",
                "modification_count",
                "charge",
                "score",
                "posterior_error_probability",
                "protein_refs",
                "target_decoy_label",
                "reverse_flag",
                "contaminant_flag",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.spectrum_id,
                    row.experiment_name or "",
                    row.peptide,
                    row.residue_sequence,
                    row.canonical_peptide,
                    str(row.modification_count),
                    str(row.charge),
                    f"{row.score:.6g}",
                    ""
                    if row.posterior_error_probability is None
                    else f"{row.posterior_error_probability:.6g}",
                    ";".join(sort_strings(row.protein_refs)),
                    row.target_decoy_label.value,
                    str(row.reverse_flag).lower(),
                    str(row.contaminant_flag).lower(),
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_maxquant_peptide_tsv(rows: tuple[MaxquantPeptideReviewEntry, ...]) -> str:
    """Render reviewer-facing MaxQuant peptide rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "posterior_error_probability",
        "sequence",
    )
    lines = [
        "\t".join(
            (
                "sequence",
                "modified_sequence",
                "residue_sequence",
                "canonical_modified_peptide",
                "modification_count",
                "leading_razor_protein",
                "protein_refs",
                "score",
                "posterior_error_probability",
                "intensity",
                "msms_count",
                "target_decoy_label",
                "reverse_flag",
                "contaminant_flag",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.sequence,
                    row.modified_sequence or "",
                    row.residue_sequence,
                    row.canonical_modified_peptide or "",
                    str(row.modification_count),
                    row.leading_razor_protein or "",
                    ";".join(sort_strings(row.protein_refs)),
                    "" if row.score is None else f"{row.score:.6g}",
                    ""
                    if row.posterior_error_probability is None
                    else f"{row.posterior_error_probability:.6g}",
                    "" if row.intensity is None else f"{row.intensity:.6g}",
                    "" if row.msms_count is None else str(row.msms_count),
                    row.target_decoy_label.value,
                    str(row.reverse_flag).lower(),
                    str(row.contaminant_flag).lower(),
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_maxquant_protein_group_tsv(
    rows: tuple[MaxquantProteinGroupReviewEntry, ...],
) -> str:
    """Render reviewer-facing MaxQuant protein-group rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "reverse_flag",
        "contaminant_flag",
        "majority_protein_ids",
        "protein_ids",
    )
    lines = [
        "\t".join(
            (
                "protein_ids",
                "majority_protein_ids",
                "gene_names",
                "fasta_headers",
                "peptide_count",
                "razor_unique_peptide_count",
                "msms_count",
                "sequence_coverage_fraction",
                "target_decoy_label",
                "reverse_flag",
                "contaminant_flag",
                "only_identified_by_site",
                "lfq_intensities",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lfq_payload = ";".join(
            f"{entry.experiment_name}:{entry.intensity:.6g}"
            for entry in row.lfq_intensities
        )
        lines.append(
            "\t".join(
                (
                    ";".join(sort_strings(row.protein_ids)),
                    ";".join(sort_strings(row.majority_protein_ids)),
                    ";".join(sort_strings(row.gene_names)),
                    ";".join(sort_strings(row.fasta_headers)),
                    "" if row.peptide_count is None else str(row.peptide_count),
                    ""
                    if row.razor_unique_peptide_count is None
                    else str(row.razor_unique_peptide_count),
                    "" if row.msms_count is None else str(row.msms_count),
                    ""
                    if row.sequence_coverage_fraction is None
                    else f"{row.sequence_coverage_fraction:.6g}",
                    row.target_decoy_label.value,
                    str(row.reverse_flag).lower(),
                    str(row.contaminant_flag).lower(),
                    str(row.only_identified_by_site).lower(),
                    lfq_payload,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_maxquant_lfq_candidate_tsv(
    rows: tuple[MaxquantLfqMatrixCandidateEntry, ...],
) -> str:
    """Render LFQ-ready MaxQuant protein candidates as TSV."""

    ordered_rows = sort_rows_by_fields(
        rows,
        "reverse_flag",
        "contaminant_flag",
        "entity_id",
    )
    lines = [
        "\t".join(
            (
                "entity_id",
                "protein_ids",
                "majority_protein_ids",
                "gene_names",
                "fasta_headers",
                "member_peptides",
                "target_decoy_label",
                "reverse_flag",
                "contaminant_flag",
                "only_identified_by_site",
                "observed_lfq_experiment_count",
                "lfq_intensities",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lfq_payload = ";".join(
            f"{entry.experiment_name}:{entry.intensity:.6g}"
            for entry in row.lfq_intensities
        )
        lines.append(
            "\t".join(
                (
                    row.entity_id,
                    ";".join(sort_strings(row.protein_ids)),
                    ";".join(sort_strings(row.majority_protein_ids)),
                    ";".join(sort_strings(row.gene_names)),
                    ";".join(sort_strings(row.fasta_headers)),
                    ";".join(sort_strings(row.member_peptides)),
                    row.target_decoy_label.value,
                    str(row.reverse_flag).lower(),
                    str(row.contaminant_flag).lower(),
                    str(row.only_identified_by_site).lower(),
                    str(row.observed_lfq_experiment_count),
                    lfq_payload,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def _build_maxquant_evidence_rows(
    normalization: SearchAdapterNormalizationReport,
    *,
    source_path: Path,
) -> tuple[MaxquantEvidenceReviewEntry, ...]:
    rows: list[MaxquantEvidenceReviewEntry] = []
    for evidence_row in normalization.evidence_rows:
        if not evidence_row.accepted or evidence_row.normalized_record is None:
            continue
        record = evidence_row.normalized_record
        raw = evidence_row.raw_fields
        native_peptide = raw.get("Modified sequence", record.peptide)
        peptide_report = build_search_engine_modified_peptide_report(
            native_peptide,
            dialect=SearchEngineModifiedPeptideDialect.MAXQUANT,
        )
        rows.append(
            MaxquantEvidenceReviewEntry(
                spectrum_id=record.spectrum_id,
                experiment_name=_optional_text(raw.get("Experiment")),
                peptide=native_peptide,
                residue_sequence=peptide_report.residue_sequence,
                canonical_peptide=record.canonical_peptide,
                modification_count=len(peptide_report.modifications),
                charge=record.charge,
                score=record.score,
                posterior_error_probability=record.q_value,
                protein_refs=record.protein_refs,
                target_decoy_label=record.target_decoy_label,
                reverse_flag=_flagged(raw.get("Reverse")),
                contaminant_flag=_flagged(raw.get("Potential contaminant")),
                provenance=record.provenance
                or ImportedEvidenceProvenance.from_single_row(
                    source_engine="maxquant-evidence",
                    source_file=str(source_path),
                    source_row_number=evidence_row.row_number,
                    original_identifiers={"spectrum_id": record.spectrum_id},
                ),
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.posterior_error_probability
                if row.posterior_error_probability is not None
                else float("inf"),
                -row.score,
                row.spectrum_id,
            ),
        )
    )


def _parse_maxquant_peptide_table(
    peptides_txt_path: Path,
) -> tuple[MaxquantPeptideReviewEntry, ...]:
    require_valid_scientific_table(
        peptides_txt_path,
        schema=build_maxquant_peptides_schema(),
    )
    rows: list[MaxquantPeptideReviewEntry] = []
    with peptides_txt_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row_number, raw_row in enumerate(reader, start=2):
            sequence = _required_text(raw_row, "Sequence")
            modified_sequence = _optional_text(raw_row.get("Modified sequence"))
            if modified_sequence:
                peptide_report = build_search_engine_modified_peptide_report(
                    modified_sequence,
                    dialect=SearchEngineModifiedPeptideDialect.MAXQUANT,
                )
                residue_sequence = peptide_report.residue_sequence
                canonical_modified_peptide = peptide_report.canonical_notation
                modification_count = len(peptide_report.modifications)
            else:
                residue_sequence = sequence
                canonical_modified_peptide = None
                modification_count = 0
            protein_refs = _split_semicolon_field(raw_row.get("Proteins"))
            reverse_flag = _flagged(raw_row.get("Reverse"))
            provenance = ImportedEvidenceProvenance.from_single_row(
                source_engine="maxquant",
                source_file=str(peptides_txt_path),
                source_row_number=row_number,
                original_identifiers={
                    "sequence": sequence,
                    **(
                        {"modified_sequence": modified_sequence}
                        if modified_sequence is not None
                        else {}
                    ),
                    **(
                        {
                            "leading_razor_protein": _optional_text(
                                raw_row.get("Leading razor protein")
                            )
                            or ""
                        }
                    ),
                },
            )
            rows.append(
                MaxquantPeptideReviewEntry(
                    sequence=sequence,
                    modified_sequence=modified_sequence,
                    residue_sequence=residue_sequence,
                    canonical_modified_peptide=canonical_modified_peptide,
                    modification_count=modification_count,
                    leading_razor_protein=_optional_text(
                        raw_row.get("Leading razor protein")
                    ),
                    protein_refs=protein_refs,
                    score=_optional_float(raw_row.get("Score")),
                    posterior_error_probability=_optional_float(raw_row.get("PEP")),
                    intensity=_optional_float(raw_row.get("Intensity")),
                    msms_count=_optional_int(raw_row.get("MS/MS Count")),
                    target_decoy_label=parse_target_decoy_label(
                        protein_refs=protein_refs,
                        explicit_label=raw_row.get("Reverse"),
                        policy=_MAXQUANT_DECOY_POLICY,
                    ),
                    reverse_flag=reverse_flag,
                    contaminant_flag=_flagged(raw_row.get("Potential contaminant")),
                    provenance=provenance,
                )
            )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.posterior_error_probability
                if row.posterior_error_probability is not None
                else float("inf"),
                row.sequence,
            ),
        )
    )


def _parse_maxquant_protein_groups_table(
    protein_groups_txt_path: Path,
) -> tuple[tuple[MaxquantProteinGroupReviewEntry, ...], tuple[str, ...]]:
    require_valid_scientific_table(
        protein_groups_txt_path,
        schema=build_maxquant_protein_groups_schema(),
    )
    rows: list[MaxquantProteinGroupReviewEntry] = []
    with protein_groups_txt_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames or ()
        lfq_columns = tuple(
            column for column in fieldnames if column.startswith("LFQ intensity ")
        )
        for row_number, raw_row in enumerate(reader, start=2):
            protein_ids = _split_semicolon_field(raw_row.get("Protein IDs"))
            reverse_flag = _flagged(raw_row.get("Reverse"))
            row_provenance = ImportedEvidenceProvenance.from_single_row(
                source_engine="maxquant",
                source_file=str(protein_groups_txt_path),
                source_row_number=row_number,
                original_identifiers={
                    "protein_ids": ";".join(protein_ids),
                    "majority_protein_ids": raw_row.get("Majority protein IDs", ""),
                },
            )
            lfq_intensities = tuple(
                MaxquantLfqIntensityEntry(
                    experiment_name=column.removeprefix("LFQ intensity ").strip(),
                    intensity=_optional_float(raw_row.get(column)) or 0.0,
                    provenance=ImportedEvidenceProvenance.combine(
                        (row_provenance,),
                        original_identifiers={
                            "protein_ids": ";".join(protein_ids),
                            "experiment_name": column.removeprefix(
                                "LFQ intensity "
                            ).strip(),
                        },
                    ),
                )
                for column in lfq_columns
            )
            rows.append(
                MaxquantProteinGroupReviewEntry(
                    protein_ids=protein_ids,
                    majority_protein_ids=_split_semicolon_field(
                        raw_row.get("Majority protein IDs")
                    ),
                    gene_names=_split_semicolon_field(raw_row.get("Gene names")),
                    fasta_headers=_split_semicolon_field(raw_row.get("Fasta headers")),
                    peptide_count=_optional_int(raw_row.get("Peptides")),
                    razor_unique_peptide_count=_optional_int(
                        raw_row.get("Razor + unique peptides")
                    ),
                    msms_count=_optional_int(raw_row.get("MS/MS count")),
                    sequence_coverage_fraction=_coverage_fraction(
                        raw_row.get("Sequence coverage [%]")
                    ),
                    target_decoy_label=parse_target_decoy_label(
                        protein_refs=protein_ids,
                        explicit_label=raw_row.get("Reverse"),
                        policy=_MAXQUANT_DECOY_POLICY,
                    ),
                    reverse_flag=reverse_flag,
                    contaminant_flag=_flagged(raw_row.get("Potential contaminant")),
                    only_identified_by_site=_flagged(
                        raw_row.get("Only identified by site")
                    ),
                    lfq_intensities=lfq_intensities,
                    provenance=row_provenance,
                )
            )
    experiment_names = tuple(
        column.removeprefix("LFQ intensity ").strip() for column in lfq_columns
    )
    return (
        tuple(
            sorted(
                rows,
                key=lambda row: (
                    row.reverse_flag,
                    row.contaminant_flag,
                    ";".join(row.majority_protein_ids or row.protein_ids),
                ),
            )
        ),
        experiment_names,
    )


def build_maxquant_lfq_matrix_candidates(
    protein_group_rows: tuple[MaxquantProteinGroupReviewEntry, ...],
    *,
    peptide_rows: tuple[MaxquantPeptideReviewEntry, ...],
) -> tuple[MaxquantLfqMatrixCandidateEntry, ...]:
    """Build LFQ-ready protein candidates from imported MaxQuant protein groups."""

    member_peptides = _build_member_peptides_by_entity(
        protein_group_rows,
        peptide_rows=peptide_rows,
    )
    rows = [
        MaxquantLfqMatrixCandidateEntry(
            entity_id=_protein_group_entity_id(row),
            protein_ids=row.protein_ids,
            majority_protein_ids=row.majority_protein_ids,
            gene_names=row.gene_names,
            fasta_headers=row.fasta_headers,
            member_peptides=member_peptides.get(_protein_group_entity_id(row), ()),
            target_decoy_label=row.target_decoy_label,
            reverse_flag=row.reverse_flag,
            contaminant_flag=row.contaminant_flag,
            only_identified_by_site=row.only_identified_by_site,
            observed_lfq_experiment_count=sum(
                1 for entry in row.lfq_intensities if entry.intensity > 0.0
            ),
            lfq_intensities=row.lfq_intensities,
            provenance=row.provenance,
        )
        for row in protein_group_rows
    ]
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.reverse_flag,
                row.contaminant_flag,
                row.entity_id,
            ),
        )
    )


def _required_text(row: dict[str, str], column: str) -> str:
    value = row.get(column, "").strip()
    if not value:
        raise ValueError(f"MaxQuant table is missing required {column!r} value")
    return value


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _split_semicolon_field(value: str | None) -> tuple[str, ...]:
    if value is None or not value.strip():
        return ()
    return tuple(token.strip() for token in value.split(";") if token.strip())


def _flagged(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"+", "true", "1", "yes", "contaminant", "reverse"}


def _optional_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value.strip())


def _optional_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(float(value.strip()))


def _coverage_fraction(value: str | None) -> float | None:
    parsed = _optional_float(value)
    if parsed is None:
        return None
    return parsed / 100.0


def _protein_group_entity_id(row: MaxquantProteinGroupReviewEntry) -> str:
    protein_ids = row.majority_protein_ids or row.protein_ids
    if protein_ids:
        return ";".join(protein_ids)
    return "unassigned_protein_group"


def _build_member_peptides_by_entity(
    protein_group_rows: tuple[MaxquantProteinGroupReviewEntry, ...],
    *,
    peptide_rows: tuple[MaxquantPeptideReviewEntry, ...],
) -> dict[str, tuple[str, ...]]:
    peptides_by_entity: dict[str, set[str]] = {
        _protein_group_entity_id(row): set() for row in protein_group_rows
    }
    for peptide_row in peptide_rows:
        peptide_protein_refs = set(peptide_row.protein_refs)
        if peptide_row.leading_razor_protein is not None:
            peptide_protein_refs.add(peptide_row.leading_razor_protein)
        if not peptide_protein_refs:
            continue
        for protein_group_row in protein_group_rows:
            if peptide_protein_refs.intersection(protein_group_row.protein_ids):
                peptides_by_entity[_protein_group_entity_id(protein_group_row)].add(
                    peptide_row.residue_sequence
                )
    return {
        entity_id: tuple(sorted(peptides))
        for entity_id, peptides in peptides_by_entity.items()
    }
