# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Generic lab-local PSM mapping over explicit YAML or JSON column maps."""

from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path

from pydantic import ConfigDict, Field, field_validator, model_validator
import yaml

from bijux_proteomics.domain import ImportedEvidenceProvenance
from bijux_proteomics.identification.contracts import (
    RejectedPsmRow,
    SearchResultColumnMapping,
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics.identification.psm.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
    build_rejected_evidence_rows_from_psm_rows,
)
from bijux_proteomics.identification.search_adapters import (
    ScoreOrientation,
    SearchAdapterDialectManifest,
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchResultFamily,
    SearchScoreFamily,
    normalize_search_results_with_adapter,
)
from bijux_proteomics_foundation import JsonModel


class GenericPsmTableColumnMapping(JsonModel):
    """Explicit lab-local PSM column map with optional run identity."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    spectrum_id: str = Field(..., min_length=1)
    peptide: str | None = None
    modified_peptide: str | None = None
    charge: str = Field(..., min_length=1)
    score: str = Field(..., min_length=1)
    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    intensity: str | None = None
    protein_refs: str = Field(..., min_length=1)
    q_value: str | None = None
    decoy_label: str | None = None
    contaminant_label: str | None = None
    decoy_prefix: str | None = "DECOY_"
    decoy_suffix: str | None = None
    explicit_decoy_values: tuple[str, ...] = ("decoy", "true", "1")
    explicit_target_values: tuple[str, ...] = ("target", "false", "0")
    protein_separator: str = ";"

    @field_validator("explicit_decoy_values", "explicit_target_values", mode="before")
    @classmethod
    def _normalize_values(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, str):
            values: tuple[str, ...] = (value,)
        else:
            if not isinstance(value, Iterable):
                raise ValueError("explicit decoy/target values must be iterable")
            values = tuple(str(token) for token in value)
        return tuple(token.strip().lower() for token in values if token.strip())

    @model_validator(mode="after")
    def _require_generic_mapper_semantics(self) -> GenericPsmTableColumnMapping:
        if self.peptide is None and self.modified_peptide is None:
            raise ValueError(
                "generic PSM mapping requires a peptide or modified_peptide column"
            )
        if self.decoy_label is None and not self.decoy_prefix and not self.decoy_suffix:
            raise ValueError(
                "generic PSM mapping requires a decoy label column or decoy naming rule"
            )
        return self

    def to_search_result_mapping(self) -> SearchResultColumnMapping:
        """Convert the generic mapper config into the base search-result mapping."""
        return SearchResultColumnMapping(
            run_id=self.run_id,
            spectrum_id=self.spectrum_id,
            peptide=self.peptide or self.modified_peptide or self.spectrum_id,
            modified_peptide=self.modified_peptide,
            charge=self.charge,
            score=self.score,
            intensity=self.intensity,
            protein_refs=self.protein_refs,
            q_value=self.q_value,
            decoy_label=self.decoy_label,
            contaminant_label=self.contaminant_label,
            protein_separator=self.protein_separator,
        )

    def to_target_decoy_policy(self) -> TargetDecoyLabelPolicy:
        """Build the explicit decoy policy requested by one generic mapping."""

        return TargetDecoyLabelPolicy(
            protein_prefix=self.decoy_prefix,
            protein_suffix=self.decoy_suffix,
            explicit_decoy_values=self.explicit_decoy_values,
            explicit_target_values=self.explicit_target_values,
        )

    def to_score_orientation(self) -> ScoreOrientation:
        """Convert the declared score orientation into the shared contract."""

        return ScoreOrientation(self.score_orientation)


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
    intensity: float | None = Field(default=None, ge=0.0)
    q_value: float | None = Field(default=None, ge=0.0)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel
    target_decoy_contaminant_class: TargetDecoyContaminantClass
    contaminant_flag: bool = False
    provenance: ImportedEvidenceProvenance | None = None


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
    rejected_evidence_rows: tuple[RejectedEvidenceTableEntry, ...] = Field(
        default_factory=tuple
    )
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
    dialect = _build_generic_mapper_dialect(column_mapping)
    normalization = normalize_search_results_with_adapter(
        source_path=source_path,
        adapter_kind=SearchAdapterKind.GENERIC,
        dialect_id=dialect.dialect_id,
        mapping=column_mapping.to_search_result_mapping(),
        decoy_policy=decoy_policy or column_mapping.to_target_decoy_policy(),
        additional_dialects=(dialect,),
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
        rejected_evidence_rows=build_rejected_evidence_rows_from_psm_rows(
            normalization.parse_report.rejected_rows,
            source_file=source_path.name,
            entity_type="psm",
            entity_id_columns=tuple(
                column_name
                for column_name in (
                    column_mapping.spectrum_id,
                    column_mapping.modified_peptide,
                    column_mapping.peptide,
                )
                if column_name is not None
            ),
        ),
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
                "intensity",
                "q_value",
                "protein_refs",
                "target_decoy_label",
                "target_decoy_contaminant_class",
                "contaminant_flag",
                *ImportedEvidenceProvenance.tsv_header(),
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
                    "" if row.intensity is None else f"{row.intensity:.6g}",
                    "" if row.q_value is None else f"{row.q_value:.6g}",
                    ";".join(row.protein_refs),
                    row.target_decoy_label.value,
                    row.target_decoy_contaminant_class.value,
                    "true" if row.contaminant_flag else "false",
                    *(
                        row.provenance.to_tsv_cells()
                        if row.provenance is not None
                        else ("", "", "", "")
                    ),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_generic_psm_rejected_row_tsv(rows: tuple[RejectedPsmRow, ...]) -> str:
    """Render rejected generic PSM rows as TSV."""

    ordered_rows = tuple(sorted(rows, key=lambda row: row.row_number))
    lines = [
        "\t".join(
            (
                "row_number",
                "issue_codes",
                "issue_messages",
                "raw_fields_json",
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    str(row.row_number),
                    ";".join(issue.code for issue in row.issues),
                    ";".join(issue.message for issue in row.issues),
                    json.dumps(row.raw_fields, sort_keys=True, separators=(",", ":")),
                )
            )
        )
    return "\n".join(lines) + "\n"


def _build_generic_mapper_dialect(
    mapping: GenericPsmTableColumnMapping,
) -> SearchAdapterDialectManifest:
    return SearchAdapterDialectManifest(
        adapter_kind=SearchAdapterKind.GENERIC,
        dialect_id="mapped-generic-psm-table",
        display_name="Mapped generic search table",
        description=(
            "Normalize a user-mapped generic search-result table with explicit score "
            "orientation and target-decoy semantics."
        ),
        score_orientation=mapping.to_score_orientation(),
        score_family=SearchScoreFamily.GENERIC_NUMERIC,
        result_family=SearchResultFamily.DATABASE_TARGET_DECOY,
        native_columns=tuple(sorted(_mapped_source_columns(mapping))),
        mapping=mapping.to_search_result_mapping(),
    )


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
                intensity=record.intensity,
                q_value=record.q_value,
                protein_refs=record.protein_refs,
                target_decoy_label=record.target_decoy_label,
                target_decoy_contaminant_class=record.target_decoy_contaminant_class,
                contaminant_flag=record.contaminant_flag,
                provenance=record.provenance,
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
            mapping.intensity,
            mapping.protein_refs,
            mapping.q_value,
            mapping.decoy_label,
            mapping.contaminant_label,
        )
        if column_name is not None
    }
