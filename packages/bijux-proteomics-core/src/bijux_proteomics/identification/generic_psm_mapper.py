# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generic lab-local PSM mapping over explicit YAML or JSON column maps."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ConfigDict, Field
import yaml

from bijux_proteomics.identification.contracts import (
    RejectedPsmRow,
    SearchResultColumnMapping,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    normalize_search_results_with_adapter,
)
from bijux_proteomics_foundation import JsonModel


class GenericPsmTableColumnMapping(JsonModel):
    """Explicit lab-local PSM column map with optional run identity."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    charge: str = Field(..., min_length=1)
    score: str = Field(..., min_length=1)
    run_id: str | None = None
    protein_refs: str | None = None
    q_value: str | None = None
    decoy_label: str | None = None
    contaminant_label: str | None = None
    protein_separator: str = ";"

    def to_search_result_mapping(self) -> SearchResultColumnMapping:
        """Convert the generic mapper config into the base search-result mapping."""
        return SearchResultColumnMapping(
            run_id=self.run_id,
            spectrum_id=self.spectrum_id,
            peptide=self.peptide,
            modified_peptide=self.modified_peptide,
            charge=self.charge,
            score=self.score,
            protein_refs=self.protein_refs,
            q_value=self.q_value,
            decoy_label=self.decoy_label,
            contaminant_label=self.contaminant_label,
            protein_separator=self.protein_separator,
        )


class GenericMappedPsmRow(JsonModel):
    """One normalized PSM row produced through a lab-local generic map."""

    model_config = ConfigDict(extra="forbid")

    run_id: str | None = None
    spectrum_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    modified_peptide: str | None = None
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    score: float
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    contaminant_flag: bool = False


class GenericPsmMapperSummary(JsonModel):
    """Compact summary over one generic mapped PSM table."""

    model_config = ConfigDict(extra="forbid")

    total_rows: int = Field(..., ge=0)
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    mapped_run_count: int = Field(..., ge=0)
    q_value_row_count: int = Field(..., ge=0)
    protein_mapped_row_count: int = Field(..., ge=0)
    unmapped_source_column_count: int = Field(..., ge=0)
    unmapped_source_columns: tuple[str, ...] = Field(default_factory=tuple)


class GenericPsmMapperReport(JsonModel):
    """One governed report over a lab-local mapped PSM table."""

    model_config = ConfigDict(extra="forbid")

    column_mapping: GenericPsmTableColumnMapping
    source_columns: tuple[str, ...] = Field(default_factory=tuple)
    normalization: SearchAdapterNormalizationReport
    mapped_rows: tuple[GenericMappedPsmRow, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[RejectedPsmRow, ...] = Field(default_factory=tuple)
    summary: GenericPsmMapperSummary


def load_generic_psm_table_mapping(path: Path) -> GenericPsmTableColumnMapping:
    """Load one generic PSM mapping document from YAML or JSON."""
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".yaml", ".yml"}:
        data = yaml.safe_load(text)
    else:
        raise ValueError("generic PSM mapping must use .json, .yaml, or .yml")
    if not isinstance(data, dict):
        raise ValueError("generic PSM mapping document must be one mapping object")
    return GenericPsmTableColumnMapping.model_validate(data)


def build_generic_psm_mapper_report(
    source_path: Path,
    *,
    mapping_path: Path,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> GenericPsmMapperReport:
    """Normalize one lab-local PSM table through an explicit generic column map."""
    column_mapping = load_generic_psm_table_mapping(mapping_path)
    normalization = normalize_search_results_with_adapter(
        source_path=source_path,
        adapter_kind=SearchAdapterKind.GENERIC,
        mapping=column_mapping.to_search_result_mapping(),
        decoy_policy=decoy_policy,
    )
    mapped_rows = _build_mapped_rows(
        normalization_report=normalization,
        column_mapping=column_mapping,
    )
    unmapped_source_columns = tuple(
        sorted(
            set(normalization.source_columns) - _mapped_source_columns(column_mapping)
        )
    )
    summary = GenericPsmMapperSummary(
        total_rows=normalization.parse_report.total_rows,
        accepted_rows=len(mapped_rows),
        rejected_rows=len(normalization.parse_report.rejected_rows),
        mapped_run_count=sum(1 for row in mapped_rows if row.run_id is not None),
        q_value_row_count=sum(1 for row in mapped_rows if row.q_value is not None),
        protein_mapped_row_count=sum(1 for row in mapped_rows if row.protein_refs),
        unmapped_source_column_count=len(unmapped_source_columns),
        unmapped_source_columns=unmapped_source_columns,
    )
    return GenericPsmMapperReport(
        column_mapping=column_mapping,
        source_columns=normalization.source_columns,
        normalization=normalization,
        mapped_rows=mapped_rows,
        rejected_rows=normalization.parse_report.rejected_rows,
        summary=summary,
    )


def render_generic_psm_mapper_tsv(rows: tuple[GenericMappedPsmRow, ...]) -> str:
    """Render normalized generic PSM rows as TSV."""
    lines = [
        "\t".join(
            (
                "run_id",
                "spectrum_id",
                "peptide_sequence",
                "peptide",
                "modified_peptide",
                "canonical_peptide",
                "charge",
                "score",
                "q_value",
                "protein_refs",
                "target_decoy_label",
                "contaminant_flag",
            )
        )
    ]
    for row in rows:
        lines.append(
            "\t".join(
                (
                    row.run_id or "",
                    row.spectrum_id,
                    row.peptide_sequence,
                    row.peptide,
                    row.modified_peptide or "",
                    row.canonical_peptide,
                    str(row.charge),
                    f"{row.score:.6g}",
                    "" if row.q_value is None else f"{row.q_value:.6g}",
                    ";".join(row.protein_refs),
                    row.target_decoy_label.value,
                    "true" if row.contaminant_flag else "false",
                )
            )
        )
    return "\n".join(lines) + "\n"


def _build_mapped_rows(
    *,
    normalization_report: SearchAdapterNormalizationReport,
    column_mapping: GenericPsmTableColumnMapping,
) -> tuple[GenericMappedPsmRow, ...]:
    rows: list[GenericMappedPsmRow] = []
    for evidence_row in normalization_report.evidence_rows:
        if not evidence_row.accepted or evidence_row.normalized_record is None:
            continue
        record = evidence_row.normalized_record
        run_id = None
        if column_mapping.run_id:
            run_token = evidence_row.raw_fields.get(column_mapping.run_id, "").strip()
            run_id = run_token or None
        rows.append(
            GenericMappedPsmRow(
                run_id=run_id,
                spectrum_id=record.spectrum_id,
                peptide_sequence=record.peptide_sequence or record.peptide,
                peptide=record.peptide,
                modified_peptide=record.modified_peptide,
                canonical_peptide=record.canonical_peptide,
                charge=record.charge,
                score=record.score,
                q_value=record.q_value,
                protein_refs=record.protein_refs,
                target_decoy_label=record.target_decoy_label,
                contaminant_flag=record.contaminant_flag,
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.run_id or "",
                row.spectrum_id,
                row.q_value if row.q_value is not None else float("inf"),
                -row.score,
                row.canonical_peptide,
            ),
        )
    )


def _mapped_source_columns(
    mapping: GenericPsmTableColumnMapping,
) -> set[str]:
    return {
        column_name
        for column_name in (
            mapping.run_id,
            mapping.spectrum_id,
            mapping.peptide,
            mapping.modified_peptide,
            mapping.charge,
            mapping.score,
            mapping.protein_refs,
            mapping.q_value,
            mapping.decoy_label,
            mapping.contaminant_label,
        )
        if column_name is not None
    }
