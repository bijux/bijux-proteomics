# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Schema-backed validation for governed scientific TSV and CSV tables."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.records import ContrastKind
from bijux_proteomics._tabular import (
    AcceptedDelimitedRow,
    DelimitedColumnSpec,
    DelimitedColumnValueType,
    DelimitedTableIssue,
    parse_delimited_table,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.identification.contracts import SearchResultColumnMapping
    from bijux_proteomics.isotope_labeling.silac_quantification import SilacColumnMapping
    from bijux_proteomics.ptm.contracts import PtmLocalizationColumnMapping


class ScientificTableValidationIssue(JsonModel):
    """One stable schema-validation issue over a governed scientific table."""

    model_config = ConfigDict(extra="forbid")

    table_kind: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    row_number: int = Field(..., ge=1)
    column: str | None = None


class ScientificTableRejectedRow(JsonModel):
    """One rejected scientific-table row plus its explicit validation issues."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    raw_values: dict[str, str] = Field(default_factory=dict)
    issues: tuple[ScientificTableValidationIssue, ...] = Field(default_factory=tuple)


class ScientificTableValidationReport(JsonModel):
    """Stable validation report for one governed scientific table."""

    model_config = ConfigDict(extra="forbid")

    table_kind: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    accepted_rows: tuple[AcceptedDelimitedRow, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[ScientificTableRejectedRow, ...] = Field(default_factory=tuple)

    @property
    def valid(self) -> bool:
        """Return whether the scientific table passed validation without issues."""

        return not self.rejected_rows


class ScientificTableValidationError(ValueError):
    """Structured exception raised when a governed scientific table is invalid."""

    def __init__(self, report: ScientificTableValidationReport) -> None:
        self.report = report
        first_issue = (
            report.rejected_rows[0].issues[0]
            if report.rejected_rows and report.rejected_rows[0].issues
            else None
        )
        message = (
            f"{report.table_kind} validation failed"
            if first_issue is None
            else f"{report.table_kind} validation failed: {first_issue.message}"
        )
        super().__init__(message)


class ScientificTableValidationContext(JsonModel):
    """Optional context for validators that depend on study-level state."""

    model_config = ConfigDict(extra="forbid")

    known_conditions: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("known_conditions", mode="before")
    @classmethod
    def _normalize_known_conditions(cls, value: object) -> tuple[str, ...]:
        if value in (None, ""):
            return ()
        if isinstance(value, str):
            iterable: Iterable[object] = (value,)
        elif isinstance(value, Sequence):
            iterable = value
        else:
            raise TypeError("known_conditions must be a string or a sequence of values")
        items = tuple(str(item) for item in iterable)
        normalized = tuple(item.strip() for item in items if item.strip())
        return tuple(dict.fromkeys(normalized))


class ScientificTableSchema(JsonModel):
    """One durable schema object for a governed scientific table kind."""

    model_config = ConfigDict(extra="forbid")

    table_kind: str = Field(..., min_length=1)
    column_specs: tuple[DelimitedColumnSpec, ...] = Field(default_factory=tuple)
    unique_key_columns: tuple[str, ...] = Field(default_factory=tuple)
    q_value_columns: tuple[str, ...] = Field(default_factory=tuple)
    nonnegative_numeric_columns: tuple[str, ...] = Field(default_factory=tuple)
    nonnegative_column_prefixes: tuple[str, ...] = Field(default_factory=tuple)
    allowed_values_by_column: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    linked_required_columns: tuple[tuple[str, str], ...] = Field(default_factory=tuple)
    contrast_left_column: str | None = None
    contrast_right_column: str | None = None


def validate_scientific_table(
    path: Path,
    *,
    schema: ScientificTableSchema,
    context: ScientificTableValidationContext | None = None,
) -> ScientificTableValidationReport:
    """Validate one scientific table against a durable schema object."""

    active_context = context or ScientificTableValidationContext()
    table_report = parse_delimited_table(path, column_specs=schema.column_specs)
    rejected_rows = [
        ScientificTableRejectedRow(
            row_number=row.row_number,
            raw_values=row.raw_values,
            issues=_translate_delimited_issues(
                table_kind=schema.table_kind,
                issues=row.issues,
            ),
        )
        for row in table_report.rejected_rows
    ]
    if not table_report.accepted_rows and not rejected_rows:
        rejected_rows.append(
            ScientificTableRejectedRow(
                row_number=1,
                raw_values={},
                issues=(
                    ScientificTableValidationIssue(
                        table_kind=schema.table_kind,
                        code="empty_table",
                        message="scientific table must contain at least one data row",
                        row_number=1,
                    ),
                ),
            )
        )

    candidate_rows: list[AcceptedDelimitedRow] = []
    duplicate_row_numbers = _duplicate_row_numbers(table_report.accepted_rows, schema=schema)
    for row in table_report.accepted_rows:
        issues = _schema_row_issues(
            table_kind=schema.table_kind,
            row=row,
            schema=schema,
            context=active_context,
        )
        issues += duplicate_row_numbers.get(row.row_number, ())
        if issues:
            rejected_rows.append(
                ScientificTableRejectedRow(
                    row_number=row.row_number,
                    raw_values=row.raw_values,
                    issues=issues,
                )
            )
            continue
        candidate_rows.append(row)

    return ScientificTableValidationReport(
        table_kind=schema.table_kind,
        source_path=str(path),
        accepted_rows=tuple(candidate_rows),
        rejected_rows=tuple(sorted(rejected_rows, key=lambda row: row.row_number)),
    )


def require_valid_scientific_table(
    path: Path,
    *,
    schema: ScientificTableSchema,
    context: ScientificTableValidationContext | None = None,
) -> ScientificTableValidationReport:
    """Validate one scientific table and raise a structured error on failure."""

    report = validate_scientific_table(path, schema=schema, context=context)
    if not report.valid:
        raise ScientificTableValidationError(report)
    return report


def build_psm_table_schema(
    mapping: SearchResultColumnMapping | Any,
) -> ScientificTableSchema:
    """Build the governed schema for one generic PSM table."""

    column_specs = [
            DelimitedColumnSpec(
                name="spectrum_id",
                source_columns=_required_mapping_source_columns(mapping, "spectrum_id"),
                required=True,
            ),
            DelimitedColumnSpec(
                name="peptide",
                source_columns=_required_mapping_source_columns(mapping, "peptide"),
                required=True,
            ),
            DelimitedColumnSpec(
                name="charge",
                source_columns=_required_mapping_source_columns(mapping, "charge"),
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(
                name="score",
                source_columns=_required_mapping_source_columns(mapping, "score"),
                required=True,
                value_type=DelimitedColumnValueType.FLOAT,
            ),
    ]
    q_value_columns: list[str] = []
    nonnegative_numeric_columns: list[str] = []
    q_value_column = _mapping_value(mapping, "q_value")
    if q_value_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="q_value",
                source_columns=(q_value_column,),
                value_type=DelimitedColumnValueType.FLOAT,
            )
        )
        q_value_columns.append("q_value")
    posterior_error_probability_column = _mapping_value(
        mapping,
        "posterior_error_probability",
    )
    if posterior_error_probability_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="posterior_error_probability",
                source_columns=(posterior_error_probability_column,),
                value_type=DelimitedColumnValueType.FLOAT,
            )
        )
        q_value_columns.append("posterior_error_probability")
    intensity_column = _mapping_value(mapping, "intensity")
    if intensity_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="intensity",
                source_columns=(intensity_column,),
                value_type=DelimitedColumnValueType.FLOAT,
            )
        )
        nonnegative_numeric_columns.append("intensity")
    run_id_column = _mapping_value(mapping, "run_id")
    if run_id_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="run_id",
                source_columns=(run_id_column,),
            )
        )
    modified_peptide_column = _mapping_value(mapping, "modified_peptide")
    if modified_peptide_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="modified_peptide",
                source_columns=(modified_peptide_column,),
            )
        )
    protein_refs_column = _mapping_value(mapping, "protein_refs")
    if protein_refs_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="protein_refs",
                source_columns=(protein_refs_column,),
            )
        )
    decoy_label_column = _mapping_value(mapping, "decoy_label")
    if decoy_label_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="decoy_label",
                source_columns=(decoy_label_column,),
            )
        )
    return ScientificTableSchema(
        table_kind="psm_table",
        column_specs=tuple(column_specs),
        q_value_columns=tuple(q_value_columns),
        nonnegative_numeric_columns=tuple(nonnegative_numeric_columns),
    )


def build_diann_report_schema() -> ScientificTableSchema:
    """Build the governed schema for one DIA-NN report table."""

    return ScientificTableSchema(
        table_kind="diann_report",
        column_specs=(
            DelimitedColumnSpec(name="precursor_id", source_columns=("Precursor.Id",), required=True),
            DelimitedColumnSpec(
                name="peptide_sequence",
                source_columns=("Stripped.Sequence",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="modified_peptide",
                source_columns=("Modified.Sequence",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="charge",
                source_columns=("Precursor.Charge",),
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(
                name="q_value",
                source_columns=("Q.Value",),
                required=True,
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="protein_group_id",
                source_columns=("Protein.Group",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="protein_refs",
                source_columns=("Protein.Ids",),
                required=True,
            ),
            DelimitedColumnSpec(name="run_name", source_columns=("Run",), required=True),
            DelimitedColumnSpec(
                name="sample_name",
                source_columns=("Sample",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="precursor_quantity",
                source_columns=("Precursor.Quantity",),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="protein_group_quantity",
                source_columns=("PG.Quantity",),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
        ),
        unique_key_columns=("precursor_id", "run_name"),
        q_value_columns=("q_value",),
        nonnegative_numeric_columns=("precursor_quantity", "protein_group_quantity"),
    )


def build_maxquant_peptides_schema() -> ScientificTableSchema:
    """Build the governed schema for one MaxQuant peptides table."""

    return ScientificTableSchema(
        table_kind="maxquant_peptides",
        column_specs=(
            DelimitedColumnSpec(name="sequence", source_columns=("Sequence",), required=True),
            DelimitedColumnSpec(name="modified_sequence", source_columns=("Modified sequence",)),
            DelimitedColumnSpec(name="proteins", source_columns=("Proteins",), required=True),
            DelimitedColumnSpec(
                name="score",
                source_columns=("Score",),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="posterior_error_probability",
                source_columns=("PEP",),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="intensity",
                source_columns=("Intensity",),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="msms_count",
                source_columns=("MS/MS Count",),
                value_type=DelimitedColumnValueType.INTEGER,
            ),
        ),
        unique_key_columns=("sequence",),
        q_value_columns=("posterior_error_probability",),
        nonnegative_numeric_columns=("intensity",),
    )


def build_maxquant_protein_groups_schema() -> ScientificTableSchema:
    """Build the governed schema for one MaxQuant protein-groups table."""

    return ScientificTableSchema(
        table_kind="maxquant_protein_groups",
        column_specs=(
            DelimitedColumnSpec(name="protein_ids", source_columns=("Protein IDs",), required=True),
            DelimitedColumnSpec(
                name="majority_protein_ids",
                source_columns=("Majority protein IDs",),
            ),
            DelimitedColumnSpec(
                name="peptide_count",
                source_columns=("Peptides",),
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(
                name="razor_unique_peptide_count",
                source_columns=("Razor + unique peptides",),
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(
                name="msms_count",
                source_columns=("MS/MS count",),
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(
                name="sequence_coverage_percent",
                source_columns=("Sequence coverage [%]",),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
        ),
        unique_key_columns=("protein_ids",),
        nonnegative_column_prefixes=("LFQ intensity ",),
    )


def build_experimental_design_schema() -> ScientificTableSchema:
    """Build the governed schema for one full experimental-design table."""

    return ScientificTableSchema(
        table_kind="experimental_design",
        column_specs=(
            DelimitedColumnSpec(name="sample_id", required=True),
            DelimitedColumnSpec(name="cohort"),
            DelimitedColumnSpec(name="condition", required=True),
            DelimitedColumnSpec(
                name="replicate",
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(
                name="fraction",
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(name="spectra_file", required=True),
            DelimitedColumnSpec(name="identifications_file"),
            DelimitedColumnSpec(name="batch"),
            DelimitedColumnSpec(name="instrument"),
            DelimitedColumnSpec(name="search_engine"),
            DelimitedColumnSpec(name="pair_id"),
            DelimitedColumnSpec(
                name="run_order",
                source_columns=("run_order", "injection_order", "acquisition_order"),
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(name="technical_replicate_id"),
            DelimitedColumnSpec(name="multiplex_group"),
            DelimitedColumnSpec(name="multiplex_channel"),
            DelimitedColumnSpec(name="sample_role"),
        ),
        unique_key_columns=("sample_id", "spectra_file"),
        allowed_values_by_column={
            "sample_role": (
                "sample",
                "pooled_reference",
                "qc_bridge",
            )
        },
        linked_required_columns=(("multiplex_group", "multiplex_channel"),),
    )


def build_samples_table_schema() -> ScientificTableSchema:
    """Build the governed schema for one minimal study samples table."""

    return ScientificTableSchema(
        table_kind="sample_metadata",
        column_specs=(
            DelimitedColumnSpec(name="sample_id", required=True),
            DelimitedColumnSpec(name="run_id", required=True),
            DelimitedColumnSpec(name="condition", required=True),
            DelimitedColumnSpec(name="batch"),
            DelimitedColumnSpec(name="pair_id"),
            DelimitedColumnSpec(name="timepoint"),
            DelimitedColumnSpec(name="plex_id"),
            DelimitedColumnSpec(name="channel"),
        ),
        unique_key_columns=("sample_id",),
        linked_required_columns=(("plex_id", "channel"),),
    )


def build_tmt_channel_map_schema() -> ScientificTableSchema:
    """Build the governed schema for one TMT channel-map table."""

    return ScientificTableSchema(
        table_kind="tmt_channel_map",
        column_specs=build_experimental_design_schema().column_specs,
        unique_key_columns=("multiplex_group", "multiplex_channel"),
        allowed_values_by_column={
            "sample_role": (
                "sample",
                "pooled_reference",
                "qc_bridge",
            )
        },
        linked_required_columns=(("multiplex_group", "multiplex_channel"),),
    )


def build_contrast_table_schema() -> ScientificTableSchema:
    """Build the governed schema for one study-contrast table."""

    return ScientificTableSchema(
        table_kind="contrast_table",
        column_specs=(
            DelimitedColumnSpec(name="contrast_id", required=True),
            DelimitedColumnSpec(name="kind", required=True),
            DelimitedColumnSpec(name="left_condition"),
            DelimitedColumnSpec(name="right_condition"),
            DelimitedColumnSpec(name="condition_set"),
            DelimitedColumnSpec(name="pair_id_field"),
            DelimitedColumnSpec(name="timepoint_field"),
        ),
        unique_key_columns=("contrast_id",),
        allowed_values_by_column={
            "kind": tuple(kind.value for kind in ContrastKind),
        },
        contrast_left_column="left_condition",
        contrast_right_column="right_condition",
    )


def build_lab_protocol_context_schema() -> ScientificTableSchema:
    """Build the governed schema for one experiment-level lab protocol table."""

    return ScientificTableSchema(
        table_kind="lab_protocol_context",
        column_specs=(
            DelimitedColumnSpec(
                name="protocol_id",
                source_columns=("protocol_id",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="digestion_enzyme",
                source_columns=("digestion_enzyme",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="acquisition_type",
                source_columns=("acquisition_type",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="labeling_method",
                source_columns=("labeling_method",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="enrichment_type",
                source_columns=("enrichment_type",),
                required=True,
                missing_tokens=("", "na", "n/a", "null", "nan"),
            ),
            DelimitedColumnSpec(
                name="fractionation_mode",
                source_columns=("fractionation_mode",),
                required=True,
                missing_tokens=("", "na", "n/a", "null", "nan"),
            ),
            DelimitedColumnSpec(
                name="depletion_mode",
                source_columns=("depletion_mode",),
                required=True,
                missing_tokens=("", "na", "n/a", "null", "nan"),
            ),
            DelimitedColumnSpec(
                name="instrument_platform",
                source_columns=("instrument_platform",),
                required=True,
            ),
        ),
        unique_key_columns=("protocol_id",),
        allowed_values_by_column={
            "digestion_enzyme": (
                "trypsin",
                "lysc",
                "trypsin_lysc",
                "gluc",
                "chymotrypsin",
                "aspn",
                "other",
            ),
            "acquisition_type": ("dda", "dia", "targeted"),
            "labeling_method": ("label_free", "tmt", "silac", "other"),
            "enrichment_type": (
                "none",
                "phospho",
                "acetyl",
                "ubiquitin",
                "glyco",
                "other",
            ),
            "fractionation_mode": (
                "none",
                "offline_high_ph",
                "gel",
                "sax",
                "other",
            ),
            "depletion_mode": (
                "none",
                "plasma_high_abundance",
                "ribosomal",
                "other",
            ),
        },
    )


def build_ptm_evidence_schema(
    mapping: PtmLocalizationColumnMapping | Any,
) -> ScientificTableSchema:
    """Build the governed schema for one PTM evidence table."""

    column_specs = [
        DelimitedColumnSpec(name="spectrum_id", source_columns=_required_mapping_source_columns(mapping, "spectrum_id"), required=True),
        DelimitedColumnSpec(name="peptide", source_columns=_required_mapping_source_columns(mapping, "peptide"), required=True),
        DelimitedColumnSpec(
            name="charge",
            source_columns=_required_mapping_source_columns(mapping, "charge"),
            required=True,
            value_type=DelimitedColumnValueType.INTEGER,
        ),
        DelimitedColumnSpec(
            name="score",
            source_columns=_required_mapping_source_columns(mapping, "score"),
            required=True,
            value_type=DelimitedColumnValueType.FLOAT,
        ),
        DelimitedColumnSpec(
            name="protein_refs",
            source_columns=_required_mapping_source_columns(mapping, "protein_refs"),
            required=True,
        ),
        DelimitedColumnSpec(
            name="localization_score",
            source_columns=_required_mapping_source_columns(mapping, "localization_score"),
            required=True,
            value_type=DelimitedColumnValueType.FLOAT,
        ),
    ]
    q_value_columns: list[str] = []
    q_value_column = _mapping_value(mapping, "q_value")
    if q_value_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="q_value",
                source_columns=(q_value_column,),
                value_type=DelimitedColumnValueType.FLOAT,
            )
        )
        q_value_columns.append("q_value")
    localization_probability_column = _mapping_value(
        mapping,
        "localization_probability",
    )
    if localization_probability_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="localization_probability",
                source_columns=(localization_probability_column,),
                value_type=DelimitedColumnValueType.FLOAT,
            )
        )
        q_value_columns.append("localization_probability")
    sample_id_column = _mapping_value(mapping, "sample_id")
    if sample_id_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="sample_id",
                source_columns=(sample_id_column,),
            )
        )
    candidate_sites_column = _mapping_value(mapping, "candidate_sites")
    if candidate_sites_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="candidate_sites",
                source_columns=(candidate_sites_column,),
            )
        )
    decoy_label_column = _mapping_value(mapping, "decoy_label")
    if decoy_label_column:
        column_specs.append(
            DelimitedColumnSpec(
                name="decoy_label",
                source_columns=(decoy_label_column,),
            )
        )
    return ScientificTableSchema(
        table_kind="ptm_evidence",
        column_specs=tuple(column_specs),
        unique_key_columns=("spectrum_id",),
        q_value_columns=tuple(q_value_columns),
    )


def build_silac_feature_table_schema(
    mapping: SilacColumnMapping | Any,
) -> ScientificTableSchema:
    """Build the governed schema for one SILAC feature table."""

    return ScientificTableSchema(
        table_kind="silac_feature_table",
        column_specs=(
            DelimitedColumnSpec(name="feature_id", source_columns=_required_mapping_source_columns(mapping, "feature_id"), required=True),
            DelimitedColumnSpec(name="sample_id", source_columns=_required_mapping_source_columns(mapping, "sample_id"), required=True),
            DelimitedColumnSpec(name="peptide", source_columns=_required_mapping_source_columns(mapping, "peptide"), required=True),
            DelimitedColumnSpec(name="protein_refs", source_columns=_required_mapping_source_columns(mapping, "protein_refs"), required=True),
            DelimitedColumnSpec(
                name="charge",
                source_columns=_required_mapping_source_columns(mapping, "charge"),
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(name="label", source_columns=_required_mapping_source_columns(mapping, "label"), required=True),
            DelimitedColumnSpec(
                name="intensity",
                source_columns=_required_mapping_source_columns(mapping, "intensity"),
                required=True,
                value_type=DelimitedColumnValueType.FLOAT,
            ),
        ),
        unique_key_columns=("feature_id",),
        nonnegative_numeric_columns=("intensity",),
        allowed_values_by_column={"label": ("light", "medium", "heavy")},
    )


def build_transition_table_schema() -> ScientificTableSchema:
    """Build the governed schema for one transition quantification table."""

    return ScientificTableSchema(
        table_kind="transition_table",
        column_specs=(
            DelimitedColumnSpec(
                name="transition_id",
                source_columns=("transition", "fragment_id"),
                required=True,
            ),
            DelimitedColumnSpec(
                name="precursor_id",
                source_columns=("precursor",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="precursor_charge",
                source_columns=("charge", "precursor_charge"),
                required=True,
                value_type=DelimitedColumnValueType.INTEGER,
            ),
            DelimitedColumnSpec(
                name="sample_id",
                source_columns=("sample",),
                required=True,
            ),
            DelimitedColumnSpec(
                name="intensity",
                source_columns=("area", "peak_area"),
                required=True,
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(name="run_id", source_columns=("run",)),
            DelimitedColumnSpec(name="peptide_sequence", source_columns=("peptide",)),
            DelimitedColumnSpec(name="protein_ref", source_columns=("protein",)),
            DelimitedColumnSpec(
                name="fragment_label",
                source_columns=("fragment", "product_ion"),
            ),
            DelimitedColumnSpec(
                name="retention_time_minutes",
                source_columns=("retention_time_minutes", "retention_time", "rt"),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="precursor_mz",
                source_columns=("q1",),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="fragment_mz",
                source_columns=("product_mz", "q3"),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
            DelimitedColumnSpec(
                name="q_value",
                source_columns=("qvalue",),
                value_type=DelimitedColumnValueType.FLOAT,
            ),
        ),
        unique_key_columns=("transition_id", "precursor_id", "sample_id"),
        q_value_columns=("q_value",),
        nonnegative_numeric_columns=("intensity",),
    )


def _translate_delimited_issues(
    *,
    table_kind: str,
    issues: tuple[DelimitedTableIssue, ...],
) -> tuple[ScientificTableValidationIssue, ...]:
    translated: list[ScientificTableValidationIssue] = []
    for issue in issues:
        code = issue.code
        if code == "missing_required_column":
            code = "missing_column"
        elif code == "missing_required_value":
            code = "missing_value"
        elif code in {
            "invalid_integer_value",
            "invalid_float_value",
            "invalid_boolean_value",
            "invalid_value",
        }:
            code = "wrong_type"
        translated.append(
            ScientificTableValidationIssue(
                table_kind=table_kind,
                code=code,
                message=issue.message,
                row_number=issue.row_number,
                column=issue.column,
            )
        )
    return tuple(translated)


def _schema_row_issues(
    *,
    table_kind: str,
    row: AcceptedDelimitedRow,
    schema: ScientificTableSchema,
    context: ScientificTableValidationContext,
) -> tuple[ScientificTableValidationIssue, ...]:
    issues: list[ScientificTableValidationIssue] = []
    for column in schema.q_value_columns:
        value = row.values.get(column)
        if value is None:
            continue
        numeric = float(value)
        if numeric < 0.0 or numeric > 1.0:
            issues.append(
                ScientificTableValidationIssue(
                    table_kind=table_kind,
                    code="invalid_q_value",
                    message=f"row has invalid q-value for {column!r}",
                    row_number=row.row_number,
                    column=column,
                )
            )
    for column in schema.nonnegative_numeric_columns:
        value = row.values.get(column)
        if value is None:
            continue
        numeric = float(value)
        if numeric < 0.0:
            issues.append(
                ScientificTableValidationIssue(
                    table_kind=table_kind,
                    code=(
                        "negative_intensity"
                        if "intensity" in column or "quantity" in column
                        else "negative_value"
                    ),
                    message=f"row has negative numeric value for {column!r}",
                    row_number=row.row_number,
                    column=column,
                )
            )
    for prefix in schema.nonnegative_column_prefixes:
        for column_name, raw_value in row.raw_values.items():
            if not column_name.startswith(prefix):
                continue
            stripped = raw_value.strip()
            if not stripped:
                continue
            try:
                numeric = float(stripped)
            except ValueError:
                issues.append(
                    ScientificTableValidationIssue(
                        table_kind=table_kind,
                        code="wrong_type",
                        message=f"row has invalid float value for {column_name!r}",
                        row_number=row.row_number,
                        column=column_name,
                    )
                )
                continue
            if numeric < 0.0:
                issues.append(
                    ScientificTableValidationIssue(
                        table_kind=table_kind,
                        code="negative_intensity",
                        message=f"row has negative intensity value for {column_name!r}",
                        row_number=row.row_number,
                        column=column_name,
                    )
                )
    for column, allowed_values in schema.allowed_values_by_column.items():
        value = row.values.get(column)
        if value is None:
            continue
        normalized = str(value).strip().lower()
        if normalized and normalized not in allowed_values:
            issues.append(
                ScientificTableValidationIssue(
                    table_kind=table_kind,
                    code="invalid_label" if column in {"label", "sample_role"} else "invalid_value",
                    message=f"row has unsupported value {value!r} for {column!r}",
                    row_number=row.row_number,
                    column=column,
                )
            )
    for left_column, right_column in schema.linked_required_columns:
        left_value = _present_value(row.values.get(left_column))
        right_value = _present_value(row.values.get(right_column))
        if left_value != right_value:
            issues.append(
                ScientificTableValidationIssue(
                    table_kind=table_kind,
                    code="incomplete_linked_fields",
                    message=(
                        f"row must provide {left_column!r} and {right_column!r} together"
                    ),
                    row_number=row.row_number,
                    column=left_column if left_value else right_column,
                )
            )
    if schema.contrast_left_column and schema.contrast_right_column:
        left = str(row.values.get(schema.contrast_left_column) or "").strip()
        right = str(row.values.get(schema.contrast_right_column) or "").strip()
        if left and right and left == right:
            issues.append(
                ScientificTableValidationIssue(
                    table_kind=table_kind,
                    code="impossible_contrast",
                    message="contrast must compare two distinct conditions",
                    row_number=row.row_number,
                    column=schema.contrast_left_column,
                )
            )
        if context.known_conditions:
            known_conditions = set(context.known_conditions)
            if left and left not in known_conditions:
                issues.append(
                    ScientificTableValidationIssue(
                        table_kind=table_kind,
                        code="impossible_contrast",
                        message=f"contrast references unknown condition {left!r}",
                        row_number=row.row_number,
                        column=schema.contrast_left_column,
                    )
                )
            if right and right not in known_conditions:
                issues.append(
                    ScientificTableValidationIssue(
                        table_kind=table_kind,
                        code="impossible_contrast",
                        message=f"contrast references unknown condition {right!r}",
                        row_number=row.row_number,
                        column=schema.contrast_right_column,
                    )
                )
    return tuple(issues)


def _duplicate_row_numbers(
    rows: Sequence[AcceptedDelimitedRow],
    *,
    schema: ScientificTableSchema,
) -> dict[int, tuple[ScientificTableValidationIssue, ...]]:
    if not schema.unique_key_columns:
        return {}
    grouped: dict[tuple[str, ...], list[AcceptedDelimitedRow]] = defaultdict(list)
    for row in rows:
        if not all(_present_value(row.values.get(column)) for column in schema.unique_key_columns):
            continue
        key = tuple(str(row.values.get(column)) for column in schema.unique_key_columns)
        grouped[key].append(row)
    duplicates: dict[int, tuple[ScientificTableValidationIssue, ...]] = {}
    for key, duplicate_rows in grouped.items():
        if len(duplicate_rows) < 2:
            continue
        message = (
            "row duplicates identifier defined by "
            + ", ".join(repr(column) for column in schema.unique_key_columns)
            + f": {key!r}"
        )
        for row in duplicate_rows:
            duplicates[row.row_number] = (
                ScientificTableValidationIssue(
                    table_kind=schema.table_kind,
                    code="duplicate_identifier",
                    message=message,
                    row_number=row.row_number,
                    column=schema.unique_key_columns[0],
                ),
            )
    return duplicates


def _present_value(value: object) -> bool:
    if value is None:
        return False
    return bool(str(value).strip())


def _mapping_value(mapping: object, field_name: str) -> str | None:
    value = getattr(mapping, field_name, None)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_mapping_source_columns(
    mapping: object,
    field_name: str,
) -> tuple[str, ...]:
    value = _mapping_value(mapping, field_name)
    if value is None:
        raise ValueError(f"mapping must define column for {field_name!r}")
    return (value,)
