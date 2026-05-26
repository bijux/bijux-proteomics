# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from bijux_proteomics.domain.semantic_ids import build_matrix_id
from bijux_proteomics.domain.records import (
    MissingValueState as CanonicalMissingValueState,
    QuantEntityKind as CanonicalQuantEntityKind,
    QuantMatrix as CanonicalQuantMatrix,
    QuantMeasureKind as CanonicalQuantMeasureKind,
)
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    ExperimentalDesignSampleRole,
)
from bijux_proteomics.quantification.core_matrix import (
    iter_quant_matrix_cells,
    quant_matrix_to_dense_array,
    rebuild_quant_matrix_from_dense_array,
)

if TYPE_CHECKING:
    pass


from .input_models import (
    ImputationMethod,
    LabelBasedChannelRole,
    MissingValueKind,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)
from .matrix_models import (
    LabelFreeQuantTable,
    QuantCellImputationProvenance,
    QuantImputationProvenance,
    QuantMatrixExport,
    QuantMatrixExportRow,
    QuantNormalizationProvenance,
    QuantSampleMetadataEntry,
    QuantValue,
    QuantValueContributorKind,
    QuantValueExcludedContributor,
    QuantValueOrigin,
    QuantValueProvenance,
    QuantValueSourceContributor,
)

def _canonical_entity_kind(
    entity_level: QuantEntityLevel,
) -> CanonicalQuantEntityKind:
    if entity_level is QuantEntityLevel.PEPTIDE:
        return CanonicalQuantEntityKind.PEPTIDE
    return CanonicalQuantEntityKind.PROTEIN

def _canonical_measure_kind(
    measure_kind: QuantMeasureKind,
) -> CanonicalQuantMeasureKind:
    if measure_kind is QuantMeasureKind.SPECTRAL_COUNT:
        return CanonicalQuantMeasureKind.SPECTRAL_COUNT
    return CanonicalQuantMeasureKind.INTENSITY

def _quant_measure_kind_from_canonical(
    measure_kind: CanonicalQuantMeasureKind,
) -> QuantMeasureKind:
    if measure_kind is CanonicalQuantMeasureKind.SPECTRAL_COUNT:
        return QuantMeasureKind.SPECTRAL_COUNT
    return QuantMeasureKind.INTENSITY

def _canonical_missing_value_state(
    missing_value_kind: MissingValueKind,
) -> CanonicalMissingValueState:
    return CanonicalMissingValueState(missing_value_kind.value)

def _missing_value_kind_from_canonical(
    missing_value_state: CanonicalMissingValueState,
) -> MissingValueKind:
    return MissingValueKind(missing_value_state.value)

def _split_row_metadata_values(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(token for token in value.split(";") if token)

def _iter_label_free_quant_cells(
    matrix: CanonicalQuantMatrix,
) -> tuple[tuple[str, str, float | None, CanonicalMissingValueState, int], ...]:
    base_cells = iter_quant_matrix_cells(matrix)
    rows: list[tuple[str, str, float | None, CanonicalMissingValueState, int]] = []
    for row_index, cell in enumerate(base_cells):
        entity_id, sample_id, abundance, state = cell
        support_row_index = row_index // len(matrix.sample_ids)
        support_column_index = row_index % len(matrix.sample_ids)
        support_count = (
            0
            if not matrix.support_counts
            else matrix.support_counts[support_row_index][support_column_index]
        )
        rows.append((entity_id, sample_id, abundance, state, support_count))
    return tuple(rows)

def _quant_matrix_setting(
    matrix: CanonicalQuantMatrix,
    key: str,
    default: str,
) -> str:
    if key in matrix.metadata:
        return matrix.metadata[key]
    prefix = f"{key}:"
    for entry in matrix.transformation_history:
        if entry.startswith(prefix):
            return entry.removeprefix(prefix)
    return default

def coerce_label_free_quant_table(
    table: LabelFreeQuantTable | CanonicalQuantMatrix,
) -> LabelFreeQuantTable:
    """Accept one canonical matrix wherever label-free table semantics are needed."""

    if isinstance(table, LabelFreeQuantTable):
        return table
    if table.entity_kind is CanonicalQuantEntityKind.PEPTIDE:
        entity_level = QuantEntityLevel.PEPTIDE
    elif table.entity_kind is CanonicalQuantEntityKind.PROTEIN:
        entity_level = QuantEntityLevel.PROTEIN
    else:
        raise ValueError(
            "label-free quantification requires peptide or protein entity matrices"
        )
    return LabelFreeQuantTable.from_quant_matrix(
        table,
        entity_level=entity_level,
        aggregation_method=QuantRollupMethod(
            _quant_matrix_setting(table, "aggregation_method", QuantRollupMethod.SUM.value)
        ),
        normalization_method=NormalizationMethod(
            _quant_matrix_setting(
                table,
                "normalization_method",
                NormalizationMethod.NONE.value,
            )
        ),
        imputation_method=ImputationMethod(
            _quant_matrix_setting(
                table,
                "imputation_method",
                ImputationMethod.NONE.value,
            )
        ),
        normalization_factors=dict.fromkeys(table.sample_ids, 1.0),
    )

def _matrix_value_index(
    table: LabelFreeQuantTable,
) -> dict[tuple[str, str], QuantValue]:
    return {(value.entity_id, value.sample_id): value for value in table.values}


def _log2_values(table: LabelFreeQuantTable, sample_id: str) -> np.ndarray:
    lookup = _matrix_value_index(table)
    values: list[float] = []
    for entity_id in table.entity_ids:
        cell = lookup[(entity_id, sample_id)]
        if cell.abundance is None:
            continue
        values.append(math.log2(cell.abundance + 1.0))
    return np.array(values, dtype=float)

def _condition_lookup(entries: tuple[ExperimentalDesignEntry, ...]) -> dict[str, str]:
    return {entry.sample_id: entry.condition for entry in entries}

def _batch_lookup(entries: tuple[ExperimentalDesignEntry, ...]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in entries:
        if entry.batch:
            mapping[entry.sample_id] = entry.batch
        elif entry.instrument:
            mapping[entry.sample_id] = entry.instrument
    return mapping

def _sample_metadata_lookup(
    entries: tuple[ExperimentalDesignEntry, ...],
) -> dict[str, QuantSampleMetadataEntry]:
    return {
        entry.sample_id: QuantSampleMetadataEntry(
            sample_id=entry.sample_id,
            condition=entry.condition,
            replicate=entry.replicate,
            fraction=entry.fraction,
            batch=entry.batch,
            instrument=entry.instrument,
            search_engine=entry.search_engine,
        )
        for entry in entries
    }

def _default_label_channel_role(
    entry: ExperimentalDesignEntry,
) -> LabelBasedChannelRole:
    if entry.sample_role is ExperimentalDesignSampleRole.POOLED_REFERENCE:
        return LabelBasedChannelRole.REFERENCE
    if entry.sample_role is ExperimentalDesignSampleRole.QC_BRIDGE:
        return LabelBasedChannelRole.QC_BRIDGE
    return LabelBasedChannelRole.SAMPLE

def _multiplex_channel_lookup(
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> dict[str, tuple[str, str, LabelBasedChannelRole]]:
    lookup: dict[str, tuple[str, str, LabelBasedChannelRole]] = {}
    for entry in design_entries:
        if not entry.multiplex_group or not entry.multiplex_channel:
            continue
        lookup[entry.sample_id] = (
            entry.multiplex_group,
            entry.multiplex_channel,
            _default_label_channel_role(entry),
        )
    return lookup

def _feature_entity_ids(
    record: Ms1FeatureRecord,
    *,
    entity_level: QuantEntityLevel,
) -> tuple[str, ...]:
    if entity_level is QuantEntityLevel.PEPTIDE:
        return (record.canonical_peptide,)
    if record.protein_refs:
        return record.protein_refs
    return ()

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
    measure_kind: QuantMeasureKind,
    aggregation_method: QuantRollupMethod,
    top_n: int,
) -> float:
    if measure_kind is QuantMeasureKind.SPECTRAL_COUNT:
        return float(len(values))
    if aggregation_method is QuantRollupMethod.SUM:
        return float(sum(values))
    if aggregation_method is QuantRollupMethod.MEDIAN:
        return float(np.median(np.array(values, dtype=float)))
    sorted_values = sorted(values, reverse=True)
    return float(sum(sorted_values[:top_n]))

def _quant_value_origin(
    *,
    abundance: float | None,
    imputation_provenance: QuantCellImputationProvenance | None,
) -> QuantValueOrigin:
    if imputation_provenance is not None:
        return QuantValueOrigin.IMPUTED
    if abundance is None:
        return QuantValueOrigin.MISSING
    return QuantValueOrigin.OBSERVED

def _quant_value_source_contributor(
    record: Ms1FeatureRecord,
) -> QuantValueSourceContributor:
    return QuantValueSourceContributor(
        contributor_id=record.feature_id,
        contributor_kind=QuantValueContributorKind.FEATURE,
        canonical_peptide=record.canonical_peptide,
        protein_refs=record.protein_refs,
        abundance=None if record.intensity is None else float(record.intensity),
        missing_value_kind=record.missing_value_kind,
        imported_provenance=record.provenance,
    )

def _quant_value_exclusion_reason(
    *,
    record: Ms1FeatureRecord,
    reason_code: str,
) -> str:
    if reason_code == "excluded_by_top_n_rollup":
        return "contributor falls outside the selected top-n rollup window"
    if reason_code == "missing_value_filtered":
        return "contributor was marked filtered before matrix aggregation"
    if reason_code == "missing_value_not_observed":
        return "contributor was not observed in this sample before matrix aggregation"
    return f"contributor was excluded from the quant value: {record.feature_id}"

def _build_quant_value_provenance(
    *,
    aggregation_method: QuantRollupMethod,
    abundance: float | None,
    selected_records: tuple[Ms1FeatureRecord, ...],
    excluded_records: tuple[tuple[Ms1FeatureRecord, str], ...],
    imputation_provenance: QuantCellImputationProvenance | None = None,
) -> QuantValueProvenance:
    selected_contributors = tuple(
        _quant_value_source_contributor(record) for record in selected_records
    )
    excluded_contributors = tuple(
        QuantValueExcludedContributor(
            contributor=_quant_value_source_contributor(record),
            reason_code=reason_code,
            reason=_quant_value_exclusion_reason(
                record=record,
                reason_code=reason_code,
            ),
        )
        for record, reason_code in excluded_records
    )
    return QuantValueProvenance(
        aggregation_method=aggregation_method,
        value_origin=_quant_value_origin(
            abundance=abundance,
            imputation_provenance=imputation_provenance,
        ),
        source_feature_ids=tuple(
            contributor.contributor_id
            for contributor in selected_contributors
            if contributor.contributor_kind is QuantValueContributorKind.FEATURE
        ),
        source_peptides=tuple(
            dict.fromkeys(
                contributor.canonical_peptide
                for contributor in selected_contributors
                if contributor.canonical_peptide is not None
            )
        ),
        source_precursor_ids=tuple(
            contributor.contributor_id
            for contributor in selected_contributors
            if contributor.contributor_kind is QuantValueContributorKind.PRECURSOR
        ),
        selected_contributors=selected_contributors,
        excluded_contributors=excluded_contributors,
    )

def _fallback_quant_value_provenance(
    *,
    value: QuantValue,
    entity_level: QuantEntityLevel,
    aggregation_method: QuantRollupMethod,
    entity_member_peptides: dict[str, tuple[str, ...]],
) -> QuantValueProvenance:
    source_peptides = (
        (value.entity_id,)
        if entity_level is QuantEntityLevel.PEPTIDE
        else entity_member_peptides.get(value.entity_id, ())
    )
    return QuantValueProvenance(
        aggregation_method=aggregation_method,
        value_origin=_quant_value_origin(
            abundance=value.abundance,
            imputation_provenance=value.imputation_provenance,
        ),
        source_peptides=source_peptides,
    )

def _resolve_quant_value_provenance(
    *,
    value: QuantValue,
    entity_level: QuantEntityLevel,
    aggregation_method: QuantRollupMethod,
    entity_member_peptides: dict[str, tuple[str, ...]],
) -> QuantValueProvenance:
    provenance = value.value_provenance or _fallback_quant_value_provenance(
        value=value,
        entity_level=entity_level,
        aggregation_method=aggregation_method,
        entity_member_peptides=entity_member_peptides,
    )
    updates: dict[str, object] = {}
    if provenance.aggregation_method is not aggregation_method:
        updates["aggregation_method"] = aggregation_method
    resolved_origin = _quant_value_origin(
        abundance=value.abundance,
        imputation_provenance=value.imputation_provenance,
    )
    if provenance.value_origin is not resolved_origin:
        updates["value_origin"] = resolved_origin
    if (
        not provenance.source_peptides
        and entity_level is QuantEntityLevel.PEPTIDE
        and value.entity_id
    ):
        updates["source_peptides"] = (value.entity_id,)
    if updates:
        return provenance.model_copy(update=updates)
    return provenance

def _build_table(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    entity_level: QuantEntityLevel,
    measure_kind: QuantMeasureKind,
    aggregation_method: QuantRollupMethod,
    top_n: int,
) -> LabelFreeQuantTable:
    sample_ids = tuple(sorted({record.sample_id for record in records}))
    grouped: dict[tuple[str, str], list[float]] = {}
    records_by_key: dict[tuple[str, str], list[Ms1FeatureRecord]] = {}
    feature_counts: dict[tuple[str, str], int] = {}
    missing_kinds: dict[tuple[str, str], list[MissingValueKind]] = {}
    protein_refs_by_entity: dict[str, tuple[str, ...]] = {}
    peptides_by_entity: dict[str, set[str]] = {}

    for record in records:
        entity_ids = _feature_entity_ids(record, entity_level=entity_level)
        if not entity_ids:
            continue
        for entity_id in entity_ids:
            key = (entity_id, record.sample_id)
            records_by_key.setdefault(key, []).append(record)
            missing_kinds.setdefault(key, []).append(record.missing_value_kind)
            peptides_by_entity.setdefault(entity_id, set()).add(
                record.canonical_peptide
            )
            if entity_level is QuantEntityLevel.PEPTIDE:
                protein_refs_by_entity.setdefault(entity_id, record.protein_refs)
            else:
                protein_refs_by_entity.setdefault(entity_id, (entity_id,))
            if record.missing_value_kind in (
                MissingValueKind.OBSERVED,
                MissingValueKind.ZERO,
            ):
                grouped.setdefault(key, []).append(float(record.intensity or 0.0))
                feature_counts[key] = feature_counts.get(key, 0) + 1

    entity_ids = tuple(sorted(peptides_by_entity))
    values: list[QuantValue] = []
    for entity_id in entity_ids:
        for sample_id in sample_ids:
            key = (entity_id, sample_id)
            observed_values = tuple(grouped.get(key, ()))
            bucket = tuple(
                sorted(
                    records_by_key.get(key, ()),
                    key=lambda record: (
                        -(record.intensity or 0.0),
                        record.canonical_peptide,
                        record.feature_id,
                    ),
                )
            )
            candidate_records = tuple(
                record
                for record in bucket
                if record.missing_value_kind
                in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
            )
            kinds = tuple(missing_kinds.get(key, (MissingValueKind.NOT_OBSERVED,)))
            missing_kind = _aggregate_missing_kind(kinds)
            abundance: float | None
            count = feature_counts.get(key, 0)
            if observed_values:
                abundance = _aggregate_abundance(
                    observed_values,
                    measure_kind=measure_kind,
                    aggregation_method=aggregation_method,
                    top_n=top_n,
                )
                if abundance == 0.0 and missing_kind is not MissingValueKind.OBSERVED:
                    missing_kind = MissingValueKind.ZERO
            else:
                abundance = None
            selected_records = candidate_records
            excluded_records: list[tuple[Ms1FeatureRecord, str]] = []
            if (
                measure_kind is QuantMeasureKind.INTENSITY
                and aggregation_method is QuantRollupMethod.TOP_N
                and len(candidate_records) > top_n
            ):
                selected_records = candidate_records[:top_n]
                excluded_records.extend(
                    (record, "excluded_by_top_n_rollup")
                    for record in candidate_records[top_n:]
                )
            excluded_records.extend(
                (record, "missing_value_filtered")
                for record in bucket
                if record.missing_value_kind is MissingValueKind.FILTERED
            )
            excluded_records.extend(
                (record, "missing_value_not_observed")
                for record in bucket
                if record.missing_value_kind is MissingValueKind.NOT_OBSERVED
            )
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=missing_kind,
                    source_feature_count=count,
                    value_provenance=_build_quant_value_provenance(
                        aggregation_method=aggregation_method,
                        abundance=abundance,
                        selected_records=selected_records,
                        excluded_records=tuple(excluded_records),
                    ),
                )
            )

    return LabelFreeQuantTable(
        entity_level=entity_level,
        measure_kind=measure_kind,
        aggregation_method=aggregation_method,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=sample_ids,
        entity_ids=entity_ids,
        values=tuple(values),
        entity_protein_refs=protein_refs_by_entity,
        entity_member_peptides={
            entity_id: tuple(sorted(peptides))
            for entity_id, peptides in sorted(peptides_by_entity.items())
        },
    )

def _table_matrix(
    table: LabelFreeQuantTable,
) -> tuple[np.ndarray, list[tuple[str, str]]]:
    matrix = quant_matrix_to_dense_array(table.to_quant_matrix())
    rows = list(table.entity_ids)
    cols = list(table.sample_ids)
    return matrix, [(entity_id, sample_id) for entity_id in rows for sample_id in cols]

def _rebuild_table_from_matrix(
    table: LabelFreeQuantTable,
    matrix: np.ndarray,
    *,
    normalization_method: NormalizationMethod,
    normalization_factors: dict[str, float],
) -> LabelFreeQuantTable:
    sample_index = {
        sample_id: index for index, sample_id in enumerate(table.sample_ids)
    }
    entity_index = {
        entity_id: index for index, entity_id in enumerate(table.entity_ids)
    }
    values: list[QuantValue] = []
    for value in table.values:
        rebuilt = value
        if value.abundance is not None:
            abundance = float(
                matrix[entity_index[value.entity_id], sample_index[value.sample_id]]
            )
            rebuilt = value.model_copy(update={"abundance": max(abundance, 0.0)})
        values.append(rebuilt)
    canonical_matrix = rebuild_quant_matrix_from_dense_array(
        table.to_quant_matrix(),
        matrix,
        transformation_step=f"normalization:{normalization_method.value}",
        metadata_updates={"normalization_method": normalization_method.value},
    ).model_copy(
        update={
            "matrix_id": build_matrix_id(
                table.entity_level.value,
                table.measure_kind.value,
                aggregation_method=table.aggregation_method.value,
                normalization_method=normalization_method.value,
                imputation_method=table.imputation_method.value,
            )
        }
    )
    return table.model_copy(
        update={
            "values": tuple(values),
            "quant_matrix": canonical_matrix,
            "normalization_method": normalization_method,
            "normalization_factors": normalization_factors,
        }
    )

def build_quant_matrix_export(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
) -> QuantMatrixExport:
    """Build a stable quant matrix export with sample metadata and normalization context."""
    metadata_lookup = _sample_metadata_lookup(design_entries)
    rows: list[QuantMatrixExportRow] = []
    for value in table.values:
        sample_metadata = metadata_lookup.get(
            value.sample_id,
            QuantSampleMetadataEntry(sample_id=value.sample_id),
        )
        rows.append(
            QuantMatrixExportRow(
                sample_metadata=sample_metadata,
                entity_id=value.entity_id,
                entity_level=table.entity_level,
                measure_kind=table.measure_kind,
                aggregation_method=table.aggregation_method,
                abundance=value.abundance,
                missing_value_kind=value.missing_value_kind,
                source_feature_count=value.source_feature_count,
                value_provenance=value.value_provenance,
                imputation_provenance=value.imputation_provenance,
                protein_refs=table.entity_protein_refs.get(value.entity_id, ()),
                member_peptides=table.entity_member_peptides.get(value.entity_id, ()),
            )
        )
    note = (
        "table is unnormalized"
        if table.normalization_method is NormalizationMethod.NONE
        else "table preserves explicit sample normalization factors"
    )
    imputation_note = (
        "table preserves only observed abundances"
        if table.imputation_method is ImputationMethod.NONE
        else "table includes explicit imputed abundances for downstream statistical use"
    )
    imputed_value_count = sum(
        1 for value in table.values if value.imputation_provenance is not None
    )
    return QuantMatrixExport(
        entity_level=table.entity_level,
        measure_kind=table.measure_kind,
        aggregation_method=table.aggregation_method,
        rows=tuple(
            sorted(
                rows,
                key=lambda row: (row.entity_id, row.sample_metadata.sample_id),
            )
        ),
        normalization_provenance=QuantNormalizationProvenance(
            normalization_method=table.normalization_method,
            normalization_factors=table.normalization_factors,
            note=note,
        ),
        imputation_provenance=QuantImputationProvenance(
            imputation_method=table.imputation_method,
            imputed_value_count=imputed_value_count,
            note=imputation_note,
        ),
    )

def build_label_free_intensity_table(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    entity_level: QuantEntityLevel = QuantEntityLevel.PEPTIDE,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
) -> LabelFreeQuantTable:
    """Build a stable label-free intensity matrix from parsed MS1 features."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")
    return _build_table(
        records,
        entity_level=entity_level,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )

def build_spectral_count_table(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    entity_level: QuantEntityLevel = QuantEntityLevel.PEPTIDE,
) -> LabelFreeQuantTable:
    """Build a stable spectral-count matrix from parsed MS1 features."""
    return _build_table(
        records,
        entity_level=entity_level,
        measure_kind=QuantMeasureKind.SPECTRAL_COUNT,
        aggregation_method=QuantRollupMethod.SUM,
        top_n=1,
    )
