# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable MaxLFQ-like protein report models."""

from __future__ import annotations

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.domain.records import (
    MissingValueState,
    QuantEntityKind,
    QuantMeasureKind,
)
from bijux_proteomics.domain.records import (
    QuantMatrix as CanonicalQuantMatrix,
)
from bijux_proteomics.domain.records import (
    SampleMetadata as CanonicalSampleMetadata,
)
from bijux_proteomics.quantification.contracts.input_models import (
    MissingValueKind,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.contracts.missingness import (
    MissingValueSummaryReport,
)
from bijux_proteomics.quantification.matrix.core_matrix import (
    build_numeric_quant_matrix,
)
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideMatrixGroupingMode,
    PeptideMatrixSourceKind,
)
from bijux_proteomics.quantification.matrix.protein_intensity_matrix import (
    ProteinMatrixTargetKind,
)
from bijux_proteomics_foundation import JsonModel


class ProteinLfqValue(JsonModel):
    """One sample-specific MaxLFQ-like protein estimate."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    log2_abundance: float | None = None
    missing_value_kind: MissingValueKind
    contributing_peptide_count: int = Field(..., ge=0)
    component_id: int | None = Field(default=None, ge=1)


class ProteinLfqPairwiseRatio(JsonModel):
    """One pairwise peptide-ratio constraint contributing to a protein solution."""

    model_config = ConfigDict(extra="forbid")

    sample_a: str = Field(..., min_length=1)
    sample_b: str = Field(..., min_length=1)
    shared_peptide_count: int = Field(..., ge=1)
    median_log2_ratio: float
    median_ratio: float = Field(..., gt=0.0)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ProteinLfqDisconnectedComponentEntry(JsonModel):
    """One disconnected sample component that cannot be compared across LFQ scales."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    target_kind: ProteinMatrixTargetKind
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    component_id: int = Field(..., ge=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    disconnected_from_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_count: int = Field(..., ge=1)
    pairwise_ratio_count: int = Field(..., ge=0)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)


class ProteinLfqRow(JsonModel):
    """One protein or exact protein-group LFQ row across all samples."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    target_kind: ProteinMatrixTargetKind
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    peptide_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    shared_peptide_count: int = Field(..., ge=0)
    pairwise_ratio_count: int = Field(..., ge=0)
    connected_component_count: int = Field(..., ge=0)
    fully_connected: bool
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)
    pairwise_ratios: tuple[ProteinLfqPairwiseRatio, ...] = Field(default_factory=tuple)
    values: tuple[ProteinLfqValue, ...] = Field(default_factory=tuple)


class ProteinLfqSummary(JsonModel):
    """Compact summary over one MaxLFQ-like protein quantification review."""

    model_config = ConfigDict(extra="forbid")

    peptide_row_count: int = Field(..., ge=0)
    protein_row_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    unique_only: bool = False
    minimum_shared_peptides: int = Field(..., ge=1)
    fully_connected_row_count: int = Field(..., ge=0)
    disconnected_row_count: int = Field(..., ge=0)
    disconnected_component_entry_count: int = Field(default=0, ge=0)
    total_pairwise_ratio_count: int = Field(..., ge=0)
    observed_cell_count: int = Field(..., ge=0)
    missing_cell_count: int = Field(..., ge=0)


class ProteinLfqReport(JsonModel):
    """Owned MaxLFQ-like protein quantification matrix with explicit diagnostics."""

    model_config = ConfigDict(extra="forbid")

    source_kind: PeptideMatrixSourceKind
    grouping_mode: PeptideMatrixGroupingMode
    target_kind: ProteinMatrixTargetKind
    separate_charge_states: bool = False
    aggregation_method: QuantRollupMethod
    unique_only: bool = False
    minimum_shared_peptides: int = Field(..., ge=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    rows: tuple[ProteinLfqRow, ...] = Field(default_factory=tuple)
    disconnected_components: tuple[ProteinLfqDisconnectedComponentEntry, ...] = Field(
        default_factory=tuple
    )
    quant_matrix: CanonicalQuantMatrix | None = None
    missing_summary: MissingValueSummaryReport
    summary: ProteinLfqSummary
    note: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _bind_quant_matrix(self) -> ProteinLfqReport:
        if self.quant_matrix is None:
            self.quant_matrix = self._build_quant_matrix()
        return self

    def to_quant_matrix(
        self,
        *,
        matrix_id: str = "protein_lfq_matrix",
        sample_metadata: tuple[CanonicalSampleMetadata, ...] = (),
    ) -> CanonicalQuantMatrix:
        """Convert this MaxLFQ-like report into the canonical quant matrix."""

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
        matrix_id: str = "protein_lfq_matrix",
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
                    "pairwise_ratio_count": str(row.pairwise_ratio_count),
                    "connected_component_count": str(row.connected_component_count),
                    "fully_connected": str(row.fully_connected).lower(),
                    "contributing_peptides": ";".join(row.contributing_peptides),
                }
                for row in self.rows
            },
            sample_metadata=sample_metadata,
            transformation_history=(
                "maxlfq_like",
                f"source_kind:{self.source_kind.value}",
                f"grouping_mode:{self.grouping_mode.value}",
                f"target_kind:{self.target_kind.value}",
                f"unique_only:{str(self.unique_only).lower()}",
                f"minimum_shared_peptides:{self.minimum_shared_peptides}",
            ),
            metadata={
                "note": self.note,
                "source_kind": self.source_kind.value,
                "grouping_mode": self.grouping_mode.value,
                "target_kind": self.target_kind.value,
                "unique_only": str(self.unique_only).lower(),
                "minimum_shared_peptides": str(self.minimum_shared_peptides),
            },
        )


__all__ = [
    "ProteinLfqDisconnectedComponentEntry",
    "ProteinLfqPairwiseRatio",
    "ProteinLfqReport",
    "ProteinLfqRow",
    "ProteinLfqSummary",
    "ProteinLfqValue",
]
