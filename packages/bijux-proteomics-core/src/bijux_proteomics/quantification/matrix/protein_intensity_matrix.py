# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned protein-intensity matrix surfaces over peptide-intensity evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMatrix as CanonicalQuantMatrix,
    QuantMeasureKind,
    SampleMetadata as CanonicalSampleMetadata,
)
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.quantification.contracts import (
    MissingValueKind,
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
    PeptideMatrixGroupingMode,
    PeptideMatrixSourceKind,
    build_peptide_intensity_matrix_from_features,
    build_peptide_intensity_matrix_from_psms,
)
from bijux_proteomics.quantification.matrix.core_matrix import (
    build_numeric_quant_matrix,
)
from bijux_proteomics_foundation import JsonModel


class ProteinMatrixTargetKind(StrEnum):
    """Supported protein-level rollup targets."""

    PROTEIN = "protein"
    PROTEIN_GROUP = "protein_group"


class ProteinSharedPeptidePolicy(StrEnum):
    """Explicit policy for handling peptides shared across protein targets."""

    UNIQUE_ONLY = "unique_only"
    ALL_PEPTIDES = "all_peptides"


class ProteinIntensityMatrixValue(JsonModel):
    """One sample-specific protein-matrix cell."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    shared_peptide_policy: ProteinSharedPeptidePolicy = (
        ProteinSharedPeptidePolicy.ALL_PEPTIDES
    )
    contributing_peptide_count: int = Field(..., ge=0)


class ProteinPeptideContributionEntry(JsonModel):
    """One peptide contribution row under one explicit protein rollup policy."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    target_kind: ProteinMatrixTargetKind
    sample_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    shared_peptide: bool
    eligible_under_shared_peptide_policy: bool
    included_by_policy: bool
    protein_value_abundance: float | None = Field(default=None, ge=0.0)
    abundance_rank: int | None = Field(default=None, ge=1)
    included_abundance_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    abundance_to_protein_value_ratio: float | None = Field(default=None, ge=0.0)
    shared_peptide_policy: ProteinSharedPeptidePolicy


class ProteinIntensityMatrixRow(JsonModel):
    """One protein or protein-group row across all samples."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    target_kind: ProteinMatrixTargetKind
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[ProteinIntensityMatrixValue, ...] = Field(default_factory=tuple)


class ProteinIntensityMatrixSummary(JsonModel):
    """Compact summary over one protein-intensity matrix review."""

    model_config = ConfigDict(extra="forbid")

    peptide_row_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    unique_only: bool = False
    observed_cell_count: int = Field(..., ge=0)
    zero_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)
    filtered_cell_count: int = Field(..., ge=0)


class ProteinIntensityMatrixReport(JsonModel):
    """Owned protein-by-sample intensity matrix with explicit peptide rollup policy."""

    model_config = ConfigDict(extra="forbid")

    source_kind: PeptideMatrixSourceKind
    grouping_mode: PeptideMatrixGroupingMode
    target_kind: ProteinMatrixTargetKind
    separate_charge_states: bool = False
    aggregation_method: QuantRollupMethod
    unique_only: bool = False
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[ProteinIntensityMatrixRow, ...] = Field(default_factory=tuple)
    peptide_contribution_entries: tuple[ProteinPeptideContributionEntry, ...] = Field(
        default_factory=tuple
    )
    quant_matrix: CanonicalQuantMatrix | None = None
    missing_summary: MissingValueSummaryReport
    summary: ProteinIntensityMatrixSummary
    note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _bind_quant_matrix(self) -> ProteinIntensityMatrixReport:
        if self.quant_matrix is None:
            self.quant_matrix = self._build_quant_matrix()
        return self

    def to_quant_matrix(
        self,
        *,
        matrix_id: str = "protein_intensity_matrix",
        sample_metadata: tuple[CanonicalSampleMetadata, ...] = (),
    ) -> CanonicalQuantMatrix:
        """Convert this protein matrix into the canonical matrix contract."""

        if (
            self.quant_matrix is not None
            and self.quant_matrix.matrix_id == matrix_id
            and (
                not sample_metadata
                or self.quant_matrix.sample_metadata == sample_metadata
            )
        ):
            return self.quant_matrix
        return self._build_quant_matrix(
            matrix_id=matrix_id,
            sample_metadata=sample_metadata,
        )

    def _build_quant_matrix(
        self,
        *,
        matrix_id: str = "protein_intensity_matrix",
        sample_metadata: tuple[CanonicalSampleMetadata, ...] = (),
    ) -> CanonicalQuantMatrix:
        entity_kind = (
            QuantEntityKind.PROTEIN
            if self.target_kind is ProteinMatrixTargetKind.PROTEIN
            else QuantEntityKind.PROTEIN_GROUP
        )
        return build_numeric_quant_matrix(
            matrix_id=matrix_id,
            entity_kind=entity_kind,
            measure_kind=QuantMeasureKind.INTENSITY,
            entity_ids=tuple(row.entity_id for row in self.rows),
            sample_ids=self.sample_ids,
            value_lookup={
                (row.entity_id, value.sample_id): value.abundance
                for row in self.rows
                for value in row.values
            },
            missing_state_lookup={
                (row.entity_id, value.sample_id): MissingValueState(
                    value.missing_value_kind.value
                )
                for row in self.rows
                for value in row.values
            },
            support_count_lookup={
                (row.entity_id, value.sample_id): value.contributing_peptide_count
                for row in self.rows
                for value in row.values
            },
            row_metadata_lookup={
                row.entity_id: {
                    "target_kind": row.target_kind.value,
                    "protein_refs": ";".join(row.protein_refs),
                    "peptide_count": str(row.peptide_count),
                    "unique_peptide_count": str(row.unique_peptide_count),
                    "shared_peptide_count": str(row.shared_peptide_count),
                    "contributing_peptides": ";".join(row.contributing_peptides),
                }
                for row in self.rows
            },
            sample_metadata=sample_metadata,
            transformation_history=(
                f"source_kind:{self.source_kind.value}",
                f"grouping_mode:{self.grouping_mode.value}",
                f"target_kind:{self.target_kind.value}",
                f"aggregation_method:{self.aggregation_method.value}",
                f"unique_only:{str(self.unique_only).lower()}",
            ),
            metadata={
                "note": self.note,
                "source_kind": self.source_kind.value,
                "grouping_mode": self.grouping_mode.value,
                "target_kind": self.target_kind.value,
                "aggregation_method": self.aggregation_method.value,
                "unique_only": str(self.unique_only).lower(),
            },
        )


@dataclass(frozen=True)
class _ProteinContributionSource:
    peptide_id: str
    peptide_sequence: str
    value: ProteinIntensityMatrixValue
    is_unique: bool
    eligible_under_shared_peptide_policy: bool


def build_protein_intensity_matrix_from_peptides(
    peptide_matrix: PeptideIntensityMatrixReport | CanonicalQuantMatrix,
    *,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    top_n: int = 3,
) -> ProteinIntensityMatrixReport:
    """Roll one peptide-intensity matrix up to protein or protein-group targets."""
    if isinstance(peptide_matrix, CanonicalQuantMatrix):
        peptide_matrix = PeptideIntensityMatrixReport.from_quant_matrix(peptide_matrix)
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    shared_peptide_policy = (
        ProteinSharedPeptidePolicy.UNIQUE_ONLY
        if unique_only
        else ProteinSharedPeptidePolicy.ALL_PEPTIDES
    )
    target_peptides: dict[str, list[tuple[ProteinIntensityMatrixValue, str, bool]]] = {}
    target_contributions: dict[str, list[_ProteinContributionSource]] = {}
    target_refs: dict[str, tuple[str, ...]] = {}

    for peptide_row in peptide_matrix.rows:
        is_unique = len(peptide_row.protein_refs) == 1
        if not peptide_row.protein_refs:
            continue
        target_ids: tuple[str, ...]
        if target_kind is ProteinMatrixTargetKind.PROTEIN:
            target_ids = peptide_row.protein_refs
        else:
            target_ids = (";".join(peptide_row.protein_refs),)
        for target_id in target_ids:
            target_contributions.setdefault(target_id, [])
            for value in peptide_row.values:
                eligible_under_shared_peptide_policy = is_unique or not unique_only
                target_refs.setdefault(
                    target_id,
                    peptide_row.protein_refs
                    if target_kind is ProteinMatrixTargetKind.PROTEIN_GROUP
                    else (target_id,),
                )
                target_contributions[target_id].append(
                    _ProteinContributionSource(
                        peptide_id=peptide_row.entity_id,
                        peptide_sequence=peptide_row.peptide_sequence,
                        value=ProteinIntensityMatrixValue(
                            sample_id=value.sample_id,
                            abundance=value.abundance,
                            missing_value_kind=value.missing_value_kind,
                            shared_peptide_policy=shared_peptide_policy,
                            contributing_peptide_count=1,
                        ),
                        is_unique=is_unique,
                        eligible_under_shared_peptide_policy=(
                            eligible_under_shared_peptide_policy
                        ),
                    )
                )
                if not eligible_under_shared_peptide_policy:
                    continue
                target_peptides.setdefault(target_id, [])
                target_peptides[target_id].append(
                    (
                        ProteinIntensityMatrixValue(
                            sample_id=value.sample_id,
                            abundance=value.abundance,
                            missing_value_kind=value.missing_value_kind,
                            shared_peptide_policy=shared_peptide_policy,
                            contributing_peptide_count=1,
                        ),
                        peptide_row.entity_id,
                        is_unique,
                    )
                )

    rows: list[ProteinIntensityMatrixRow] = []
    contribution_entries: list[ProteinPeptideContributionEntry] = []
    missing_entries: list[MissingValueSummaryEntry] = []
    observed_cell_count = 0
    zero_cell_count = 0
    missing_cell_count = 0
    filtered_cell_count = 0
    ordered_target_ids = tuple(sorted(target_peptides))

    grouped_lookup: dict[
        tuple[str, str], list[tuple[ProteinIntensityMatrixValue, str, bool]]
    ] = {}
    for target_id, entries in target_peptides.items():
        for matrix_value, peptide_id, is_unique in entries:
            grouped_lookup.setdefault((target_id, matrix_value.sample_id), []).append(
                (matrix_value, peptide_id, is_unique)
            )

    for sample_id in peptide_matrix.sample_ids:
        observed = 0
        zero = 0
        not_observed = 0
        filtered = 0
        for target_id in ordered_target_ids:
            missing_kind = _aggregate_missing_kind(
                tuple(
                    entry.missing_value_kind
                    for entry, _, _ in grouped_lookup.get((target_id, sample_id), [])
                )
                or (MissingValueKind.NOT_OBSERVED,)
            )
            if missing_kind is MissingValueKind.OBSERVED:
                observed += 1
            elif missing_kind is MissingValueKind.ZERO:
                zero += 1
            elif missing_kind is MissingValueKind.FILTERED:
                filtered += 1
            else:
                not_observed += 1
        missing_entries.append(
            MissingValueSummaryEntry(
                sample_id=sample_id,
                observed_count=observed,
                zero_count=zero,
                not_observed_count=not_observed,
                filtered_count=filtered,
            )
        )

    for target_id in ordered_target_ids:
        target_rows = grouped_lookup
        protein_refs = target_refs[target_id]
        peptide_ids = sorted(
            {peptide_id for _, peptide_id, _ in target_peptides[target_id]}
        )
        unique_peptide_ids = sorted(
            {
                peptide_id
                for _, peptide_id, is_unique in target_peptides[target_id]
                if is_unique
            }
        )
        shared_peptide_ids = sorted(
            {
                peptide_id
                for _, peptide_id, is_unique in target_peptides[target_id]
                if not is_unique
            }
        )
        values: list[ProteinIntensityMatrixValue] = []
        sample_contributions: dict[str, tuple[ProteinPeptideContributionEntry, ...]] = {}
        for sample_id in peptide_matrix.sample_ids:
            entries = target_rows.get((target_id, sample_id), [])
            missing_kind = _aggregate_missing_kind(
                tuple(entry.missing_value_kind for entry, _, _ in entries)
                or (MissingValueKind.NOT_OBSERVED,)
            )
            all_sample_contributions = tuple(
                contribution
                for contribution in target_contributions.get(target_id, ())
                if contribution.value.sample_id == sample_id
            )
            observed_entries = tuple(
                contribution
                for contribution in all_sample_contributions
                if _is_observed_contribution(contribution.value)
            )
            eligible_observed_entries = tuple(
                contribution
                for contribution in observed_entries
                if contribution.eligible_under_shared_peptide_policy
            )
            included_entries = _select_rollup_contributions(
                eligible_observed_entries,
                aggregation_method=aggregation_method,
                top_n=top_n,
            )
            observed_values = tuple(
                contribution.value.abundance
                for contribution in included_entries
                if contribution.value.abundance is not None
            )
            abundance: float | None = None
            if observed_values:
                abundance = _aggregate_abundance(
                    tuple(float(value) for value in observed_values),
                    aggregation_method=aggregation_method,
                    top_n=top_n,
                )
                if abundance == 0.0 and missing_kind is not MissingValueKind.OBSERVED:
                    missing_kind = MissingValueKind.ZERO
            if missing_kind is MissingValueKind.OBSERVED:
                observed_cell_count += 1
            elif missing_kind is MissingValueKind.ZERO:
                zero_cell_count += 1
            elif missing_kind is MissingValueKind.FILTERED:
                filtered_cell_count += 1
            else:
                missing_cell_count += 1
            values.append(
                ProteinIntensityMatrixValue(
                    sample_id=sample_id,
                    abundance=abundance,
                    missing_value_kind=missing_kind,
                    shared_peptide_policy=shared_peptide_policy,
                    contributing_peptide_count=len(included_entries),
                )
            )
            sample_contributions[sample_id] = _build_sample_contribution_entries(
                target_id=target_id,
                target_kind=target_kind,
                protein_refs=protein_refs,
                sample_id=sample_id,
                shared_peptide_policy=shared_peptide_policy,
                protein_value_abundance=abundance,
                sample_contributions=all_sample_contributions,
                included_entries=included_entries,
            )
        rows.append(
            ProteinIntensityMatrixRow(
                entity_id=target_id,
                target_kind=target_kind,
                protein_refs=protein_refs,
                peptide_count=len(peptide_ids),
                unique_peptide_count=len(unique_peptide_ids),
                shared_peptide_count=len(shared_peptide_ids),
                contributing_peptides=tuple(peptide_ids),
                values=tuple(values),
            )
        )
        for sample_id in peptide_matrix.sample_ids:
            contribution_entries.extend(sample_contributions[sample_id])

    note = (
        "protein matrix rolls peptide intensities up through one explicit policy "
        "while preserving peptide counts, unique-versus-shared burden, per-value contributor decomposition, and per-sample missingness"
    )
    return ProteinIntensityMatrixReport(
        source_kind=peptide_matrix.source_kind,
        grouping_mode=peptide_matrix.grouping_mode,
        target_kind=target_kind,
        separate_charge_states=peptide_matrix.separate_charge_states,
        aggregation_method=aggregation_method,
        unique_only=unique_only,
        sample_ids=peptide_matrix.sample_ids,
        rows=tuple(rows),
        peptide_contribution_entries=tuple(contribution_entries),
        missing_summary=MissingValueSummaryReport(
            entity_level=QuantEntityLevel.PROTEIN,
            policy=MissingValueSummaryPolicy(),
            entries=tuple(missing_entries),
            included_entity_ids=ordered_target_ids,
            excluded_entity_ids=(),
        ),
        summary=ProteinIntensityMatrixSummary(
            peptide_row_count=len(peptide_matrix.rows),
            protein_row_count=len(rows),
            sample_count=len(peptide_matrix.sample_ids),
            unique_only=unique_only,
            observed_cell_count=observed_cell_count,
            zero_cell_count=zero_cell_count,
            missing_cell_count=missing_cell_count,
            filtered_cell_count=filtered_cell_count,
        ),
        note=note,
    )


def build_protein_intensity_matrix_from_features(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
    separate_charge_states: bool = False,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    top_n: int = 3,
) -> ProteinIntensityMatrixReport:
    """Build one protein-intensity matrix from precursor or feature-table records."""
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_protein_intensity_matrix_from_peptides(
        peptide_matrix,
        target_kind=target_kind,
        aggregation_method=aggregation_method,
        unique_only=unique_only,
        top_n=top_n,
    )


def build_protein_intensity_matrix_from_psms(
    records: tuple[PsmRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = PeptideMatrixGroupingMode.MODIFIED_PEPTIDE,
    separate_charge_states: bool = False,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    top_n: int = 3,
) -> ProteinIntensityMatrixReport:
    """Build one protein-intensity matrix from intensity-bearing canonical PSM rows."""
    peptide_matrix = build_peptide_intensity_matrix_from_psms(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_protein_intensity_matrix_from_peptides(
        peptide_matrix,
        target_kind=target_kind,
        aggregation_method=aggregation_method,
        unique_only=unique_only,
        top_n=top_n,
    )


def render_protein_intensity_matrix_summary_tsv(
    report: ProteinIntensityMatrixReport,
) -> str:
    """Render one compact protein-matrix summary as TSV."""
    header = (
        "source_kind",
        "grouping_mode",
        "target_kind",
        "separate_charge_states",
        "aggregation_method",
        "unique_only",
        "peptide_row_count",
        "protein_row_count",
        "sample_count",
        "observed_cell_count",
        "zero_cell_count",
        "missing_cell_count",
        "filtered_cell_count",
        "note",
    )
    row = (
        report.source_kind.value,
        report.grouping_mode.value,
        report.target_kind.value,
        str(report.separate_charge_states).lower(),
        report.aggregation_method.value,
        str(report.unique_only).lower(),
        str(report.summary.peptide_row_count),
        str(report.summary.protein_row_count),
        str(report.summary.sample_count),
        str(report.summary.observed_cell_count),
        str(report.summary.zero_cell_count),
        str(report.summary.missing_cell_count),
        str(report.summary.filtered_cell_count),
        report.note,
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_protein_intensity_matrix_tsv(report: ProteinIntensityMatrixReport) -> str:
    """Render the protein-by-sample intensity matrix as one wide TSV."""
    ordered_sample_ids = sort_strings(report.sample_ids)
    ordered_rows = sort_rows_by_fields(report.rows, "entity_id")
    header = [
        "entity_id",
        "target_kind",
        "protein_refs",
        "peptide_count",
        "unique_peptide_count",
        "shared_peptide_count",
        "contributing_peptides",
    ]
    header.extend(ordered_sample_ids)
    rows = ["\t".join(header)]
    for row in ordered_rows:
        lookup = {value.sample_id: value for value in row.values}
        matrix_values = []
        for sample_id in ordered_sample_ids:
            value = lookup[sample_id]
            matrix_values.append(
                "" if value.abundance is None else f"{value.abundance:g}"
            )
        rows.append(
            "\t".join(
                (
                    row.entity_id,
                    row.target_kind.value,
                    ";".join(sort_strings(row.protein_refs)),
                    str(row.peptide_count),
                    str(row.unique_peptide_count),
                    str(row.shared_peptide_count),
                    ";".join(sort_strings(row.contributing_peptides)),
                    *matrix_values,
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_protein_intensity_missingness_tsv(
    report: ProteinIntensityMatrixReport,
) -> str:
    """Render one per-sample missingness ledger for a protein matrix."""
    header = (
        "sample_id",
        "observed_count",
        "zero_count",
        "not_observed_count",
        "filtered_count",
    )
    rows = ["\t".join(header)]
    for entry in sort_rows_by_fields(report.missing_summary.entries, "sample_id"):
        rows.append(
            "\t".join(
                (
                    entry.sample_id,
                    str(entry.observed_count),
                    str(entry.zero_count),
                    str(entry.not_observed_count),
                    str(entry.filtered_count),
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_protein_peptide_contribution_tsv(
    report: ProteinIntensityMatrixReport,
) -> str:
    """Render one explicit peptide-contribution ledger for a protein matrix."""

    header = (
        "entity_id",
        "target_kind",
        "sample_id",
        "peptide_id",
        "peptide_sequence",
        "protein_refs",
        "abundance",
        "missing_value_kind",
        "shared_peptide",
        "eligible_under_shared_peptide_policy",
        "included_by_policy",
        "protein_value_abundance",
        "abundance_rank",
        "included_abundance_fraction",
        "abundance_to_protein_value_ratio",
        "shared_peptide_policy",
    )
    rows = ["\t".join(header)]
    for entry in sort_rows_by_fields(
        report.peptide_contribution_entries,
        "entity_id",
        "sample_id",
        "peptide_id",
    ):
        rows.append(
            "\t".join(
                (
                    entry.entity_id,
                    entry.target_kind.value,
                    entry.sample_id,
                    entry.peptide_id,
                    entry.peptide_sequence,
                    ";".join(sort_strings(entry.protein_refs)),
                    "" if entry.abundance is None else f"{entry.abundance:g}",
                    entry.missing_value_kind.value,
                    str(entry.shared_peptide).lower(),
                    str(entry.eligible_under_shared_peptide_policy).lower(),
                    str(entry.included_by_policy).lower(),
                    (
                        ""
                        if entry.protein_value_abundance is None
                        else f"{entry.protein_value_abundance:g}"
                    ),
                    "" if entry.abundance_rank is None else str(entry.abundance_rank),
                    (
                        ""
                        if entry.included_abundance_fraction is None
                        else f"{entry.included_abundance_fraction:.6f}"
                    ),
                    (
                        ""
                        if entry.abundance_to_protein_value_ratio is None
                        else f"{entry.abundance_to_protein_value_ratio:.6f}"
                    ),
                    entry.shared_peptide_policy.value,
                )
            )
        )
    return "\n".join(rows) + "\n"


def _aggregate_missing_kind(kinds: tuple[MissingValueKind, ...]) -> MissingValueKind:
    if any(
        kind in (MissingValueKind.OBSERVED, MissingValueKind.ZERO) for kind in kinds
    ):
        if any(kind is MissingValueKind.ZERO for kind in kinds) and not any(
            kind is MissingValueKind.OBSERVED for kind in kinds
        ):
            return MissingValueKind.ZERO
        return MissingValueKind.OBSERVED
    if any(kind is MissingValueKind.FILTERED for kind in kinds):
        return MissingValueKind.FILTERED
    return MissingValueKind.NOT_OBSERVED


def _aggregate_abundance(
    values: tuple[float, ...],
    *,
    aggregation_method: QuantRollupMethod,
    top_n: int,
) -> float:
    if aggregation_method is QuantRollupMethod.SUM:
        return float(sum(values))
    if aggregation_method is QuantRollupMethod.MEDIAN:
        ordered = sorted(values)
        midpoint = len(ordered) // 2
        if len(ordered) % 2 == 1:
            return float(ordered[midpoint])
        return float((ordered[midpoint - 1] + ordered[midpoint]) / 2.0)
    ordered = sorted(values, reverse=True)
    return float(sum(ordered[:top_n]))


def _is_observed_contribution(value: ProteinIntensityMatrixValue) -> bool:
    return (
        value.abundance is not None
        and value.missing_value_kind
        in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
    )


def _select_rollup_contributions(
    contributions: tuple[_ProteinContributionSource, ...],
    *,
    aggregation_method: QuantRollupMethod,
    top_n: int,
) -> tuple[_ProteinContributionSource, ...]:
    if aggregation_method is not QuantRollupMethod.TOP_N:
        return contributions
    ordered = sorted(
        contributions,
        key=lambda contribution: (
            -(contribution.value.abundance or 0.0),
            contribution.peptide_id,
        ),
    )
    return tuple(ordered[:top_n])


def _build_sample_contribution_entries(
    *,
    target_id: str,
    target_kind: ProteinMatrixTargetKind,
    protein_refs: tuple[str, ...],
    sample_id: str,
    shared_peptide_policy: ProteinSharedPeptidePolicy,
    protein_value_abundance: float | None,
    sample_contributions: tuple[_ProteinContributionSource, ...],
    included_entries: tuple[_ProteinContributionSource, ...],
) -> tuple[ProteinPeptideContributionEntry, ...]:
    included_peptide_ids = {entry.peptide_id for entry in included_entries}
    ranked_entries = sorted(
        (
            contribution
            for contribution in sample_contributions
            if _is_observed_contribution(contribution.value)
        ),
        key=lambda contribution: (
            -(contribution.value.abundance or 0.0),
            contribution.peptide_id,
        ),
    )
    rank_lookup = {
        contribution.peptide_id: index
        for index, contribution in enumerate(ranked_entries, start=1)
    }
    included_total_abundance = sum(
        contribution.value.abundance or 0.0 for contribution in included_entries
    )
    equal_zero_fraction = (
        1.0 / len(included_entries)
        if included_entries and included_total_abundance == 0.0
        else None
    )
    rows: list[ProteinPeptideContributionEntry] = []
    for contribution in sample_contributions:
        included_by_policy = contribution.peptide_id in included_peptide_ids
        included_abundance_fraction: float | None = None
        if included_by_policy and contribution.value.abundance is not None:
            if included_total_abundance > 0.0:
                included_abundance_fraction = (
                    contribution.value.abundance / included_total_abundance
                )
            else:
                included_abundance_fraction = equal_zero_fraction
        abundance_to_protein_value_ratio: float | None = None
        if (
            contribution.value.abundance is not None
            and protein_value_abundance is not None
            and protein_value_abundance > 0.0
        ):
            abundance_to_protein_value_ratio = (
                contribution.value.abundance / protein_value_abundance
            )
        rows.append(
            ProteinPeptideContributionEntry(
                entity_id=target_id,
                target_kind=target_kind,
                sample_id=sample_id,
                peptide_id=contribution.peptide_id,
                peptide_sequence=contribution.peptide_sequence,
                protein_refs=protein_refs,
                abundance=contribution.value.abundance,
                missing_value_kind=contribution.value.missing_value_kind,
                shared_peptide=not contribution.is_unique,
                eligible_under_shared_peptide_policy=(
                    contribution.eligible_under_shared_peptide_policy
                ),
                included_by_policy=included_by_policy,
                protein_value_abundance=protein_value_abundance,
                abundance_rank=rank_lookup.get(contribution.peptide_id),
                included_abundance_fraction=included_abundance_fraction,
                abundance_to_protein_value_ratio=abundance_to_protein_value_ratio,
                shared_peptide_policy=shared_peptide_policy,
            )
        )
    return tuple(rows)
