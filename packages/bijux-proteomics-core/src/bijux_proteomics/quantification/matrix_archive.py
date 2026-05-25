# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable archive persistence for canonical quantitative matrices."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantMatrix,
    SampleMetadata,
)
from bijux_proteomics.tabular import render_tsv_rows
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class QuantMatrixArchive(JsonModel):
    """Persisted archive form for one canonical quantitative matrix."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    matrix_id: str = Field(..., min_length=1)
    entity_kind: str = Field(..., min_length=1)
    measure_kind: str = Field(..., min_length=1)
    entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[tuple[float | None, ...], ...] = Field(default_factory=tuple)
    missing_value_states: tuple[tuple[MissingValueState, ...], ...] = Field(
        default_factory=tuple
    )
    missing_mask: tuple[tuple[bool, ...], ...] = Field(default_factory=tuple)
    imputation_mask: tuple[tuple[bool, ...], ...] = Field(default_factory=tuple)
    support_counts: tuple[tuple[int, ...], ...] = Field(default_factory=tuple)
    row_metadata: tuple[dict[str, str], ...] = Field(default_factory=tuple)
    sample_metadata: tuple[SampleMetadata, ...] = Field(default_factory=tuple)
    transformation_history: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)

    def to_quant_matrix(self) -> QuantMatrix:
        """Rebuild the canonical matrix without archive-only derived masks."""

        return QuantMatrix(
            matrix_id=self.matrix_id,
            entity_kind=self.entity_kind,
            measure_kind=self.measure_kind,
            entity_ids=self.entity_ids,
            sample_ids=self.sample_ids,
            values=self.values,
            missing_value_states=self.missing_value_states,
            support_counts=self.support_counts,
            row_metadata=self.row_metadata,
            sample_metadata=self.sample_metadata,
            transformation_history=self.transformation_history,
            metadata=self.metadata,
        )


def save_matrix_archive(
    matrix: QuantMatrix | QuantMatrixArchive,
    path: Path,
) -> QuantMatrixArchive:
    """Persist one canonical matrix as a stable archive document."""

    archive = (
        matrix
        if isinstance(matrix, QuantMatrixArchive)
        else _build_matrix_archive(matrix)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(archive.to_stable_json() + "\n", encoding="utf-8")
    return archive


def load_matrix_archive(path: Path) -> QuantMatrixArchive:
    """Load one stable archive document from disk."""

    return QuantMatrixArchive.model_validate_json(path.read_text(encoding="utf-8"))


def render_quant_matrix_archive_tsv(matrix: QuantMatrix | QuantMatrixArchive) -> str:
    """Render one stable cell ledger for matrix round-trip comparisons."""

    quant_matrix = matrix.to_quant_matrix() if isinstance(matrix, QuantMatrixArchive) else matrix
    row_metadata_lookup = {
        entity_id: (
            {}
            if row_index >= len(quant_matrix.row_metadata)
            else dict(quant_matrix.row_metadata[row_index])
        )
        for row_index, entity_id in enumerate(quant_matrix.entity_ids)
    }
    sample_metadata_lookup = {
        sample.sample_id: sample
        for sample in quant_matrix.sample_metadata
    }
    return render_tsv_rows(
        fieldnames=(
            "entity_id",
            "sample_id",
            "abundance",
            "missing_value_state",
            "missing_mask",
            "imputation_mask",
            "support_count",
            "row_metadata",
            "condition",
            "replicate",
            "fraction",
            "batch",
            "instrument",
            "search_engine",
        ),
        rows=tuple(
            {
                "abundance": (
                    ""
                    if quant_matrix.values[row_index][column_index] is None
                    else quant_matrix.values[row_index][column_index]
                ),
                "entity_id": entity_id,
                "sample_id": sample_id,
                "missing_value_state": quant_matrix.missing_value_states[row_index][
                    column_index
                ].value,
                "missing_mask": str(
                    _is_missing(
                        quant_matrix.missing_value_states[row_index][column_index]
                    )
                ).lower(),
                "imputation_mask": str(
                    _is_imputed(
                        value=quant_matrix.values[row_index][column_index],
                        state=quant_matrix.missing_value_states[row_index][column_index],
                    )
                ).lower(),
                "support_count": (
                    0
                    if row_index >= len(quant_matrix.support_counts)
                    else quant_matrix.support_counts[row_index][column_index]
                ),
                "row_metadata": _render_metadata_map(
                    row_metadata_lookup.get(entity_id, {})
                ),
                "condition": _sample_condition(sample_metadata_lookup, sample_id),
                "replicate": _sample_replicate(sample_metadata_lookup, sample_id),
                "fraction": _sample_fraction(sample_metadata_lookup, sample_id),
                "batch": _sample_batch(sample_metadata_lookup, sample_id),
                "instrument": _sample_instrument(sample_metadata_lookup, sample_id),
                "search_engine": _sample_search_engine(
                    sample_metadata_lookup,
                    sample_id,
                ),
            }
            for row_index, entity_id in enumerate(quant_matrix.entity_ids)
            for column_index, sample_id in enumerate(quant_matrix.sample_ids)
        ),
    )


def _build_matrix_archive(matrix: QuantMatrix) -> QuantMatrixArchive:
    archive = QuantMatrixArchive(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="quant_matrix_archive",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        matrix_id=matrix.matrix_id,
        entity_kind=matrix.entity_kind.value,
        measure_kind=matrix.measure_kind.value,
        entity_ids=matrix.entity_ids,
        sample_ids=matrix.sample_ids,
        values=matrix.values,
        missing_value_states=matrix.missing_value_states,
        missing_mask=tuple(
            tuple(_is_missing(state) for state in row)
            for row in matrix.missing_value_states
        ),
        imputation_mask=tuple(
            tuple(
                _is_imputed(value=value, state=state)
                for value, state in zip(value_row, state_row, strict=False)
            )
            for value_row, state_row in zip(
                matrix.values,
                matrix.missing_value_states,
                strict=False,
            )
        ),
        support_counts=matrix.support_counts,
        row_metadata=matrix.row_metadata,
        sample_metadata=matrix.sample_metadata,
        transformation_history=matrix.transformation_history,
        metadata=matrix.metadata,
    )
    payload = archive.to_dict()
    return archive.model_copy(
        update={"document_schema": archive.document_schema.with_content_hash(payload)}
    )


def _is_missing(state: MissingValueState) -> bool:
    return state in {
        MissingValueState.NOT_OBSERVED,
        MissingValueState.FILTERED,
    }


def _is_imputed(*, value: float | None, state: MissingValueState) -> bool:
    return value is not None and _is_missing(state)


def _render_metadata_map(metadata: dict[str, str]) -> str:
    if not metadata:
        return ""
    return ";".join(f"{key}={metadata[key]}" for key in sorted(metadata))


def _sample_condition(
    sample_metadata_lookup: dict[str, SampleMetadata], sample_id: str
) -> str:
    sample = sample_metadata_lookup.get(sample_id)
    if sample is None:
        return ""
    return sample.condition


def _sample_replicate(
    sample_metadata_lookup: dict[str, SampleMetadata], sample_id: str
) -> str | int:
    sample = sample_metadata_lookup.get(sample_id)
    if sample is None or sample.replicate is None:
        return ""
    return sample.replicate


def _sample_fraction(
    sample_metadata_lookup: dict[str, SampleMetadata], sample_id: str
) -> str | int:
    sample = sample_metadata_lookup.get(sample_id)
    if sample is None or sample.fraction is None:
        return ""
    return sample.fraction


def _sample_batch(
    sample_metadata_lookup: dict[str, SampleMetadata], sample_id: str
) -> str:
    sample = sample_metadata_lookup.get(sample_id)
    if sample is None or sample.batch is None:
        return ""
    return sample.batch


def _sample_instrument(
    sample_metadata_lookup: dict[str, SampleMetadata], sample_id: str
) -> str:
    sample = sample_metadata_lookup.get(sample_id)
    if sample is None or sample.instrument is None:
        return ""
    return sample.instrument


def _sample_search_engine(
    sample_metadata_lookup: dict[str, SampleMetadata], sample_id: str
) -> str:
    sample = sample_metadata_lookup.get(sample_id)
    if sample is None or sample.search_engine is None:
        return ""
    return sample.search_engine


__all__ = [
    "QuantMatrixArchive",
    "load_matrix_archive",
    "render_quant_matrix_archive_tsv",
    "save_matrix_archive",
]
