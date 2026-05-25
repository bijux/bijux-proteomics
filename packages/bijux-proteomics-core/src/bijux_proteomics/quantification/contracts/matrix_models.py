# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.domain.records import (
    QuantMatrix as CanonicalQuantMatrix,
)
from bijux_proteomics.quantification.core_matrix import (
    build_numeric_quant_matrix,
)
from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    pass


from .input_models import (
    ImputationMethod,
    MissingValueKind,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
)

class QuantValue(JsonModel):
    """One matrix cell in a stable quantification table."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    source_feature_count: int = Field(..., ge=0)
    value_provenance: QuantValueProvenance | None = None
    imputation_provenance: QuantCellImputationProvenance | None = None

class QuantCellImputationProvenance(JsonModel):
    """Per-cell provenance for an imputed quantification abundance."""

    model_config = ConfigDict(extra="forbid")

    method: ImputationMethod
    original_missing_value_kind: MissingValueKind
    strategy: str = Field(..., min_length=1)
    reference_group: str | None = None
    donor_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    donor_entity_ids: tuple[str, ...] = Field(default_factory=tuple)

class QuantValueOrigin(StrEnum):
    """Whether a quantification cell is observed, still missing, or imputed."""

    OBSERVED = "observed"
    MISSING = "missing"
    IMPUTED = "imputed"

class QuantValueContributorKind(StrEnum):
    """Stable contributor categories that can support one quantification value."""

    FEATURE = "feature"
    PRECURSOR = "precursor"

class QuantValueSourceContributor(JsonModel):
    """One selected raw contributor that directly supports a quant value."""

    model_config = ConfigDict(extra="forbid")

    contributor_id: str = Field(..., min_length=1)
    contributor_kind: QuantValueContributorKind
    canonical_peptide: str | None = None
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    imported_provenance: ImportedEvidenceProvenance | None = None

class QuantValueExcludedContributor(JsonModel):
    """One raw contributor excluded from a quant value plus the exclusion reason."""

    model_config = ConfigDict(extra="forbid")

    contributor: QuantValueSourceContributor
    reason_code: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)

class QuantValueProvenance(JsonModel):
    """Stable per-cell provenance that explains one matrix value back to raw support."""

    model_config = ConfigDict(extra="forbid")

    aggregation_method: QuantRollupMethod
    value_origin: QuantValueOrigin
    source_feature_ids: tuple[str, ...] = Field(default_factory=tuple)
    source_peptides: tuple[str, ...] = Field(default_factory=tuple)
    source_precursor_ids: tuple[str, ...] = Field(default_factory=tuple)
    selected_contributors: tuple[QuantValueSourceContributor, ...] = Field(
        default_factory=tuple
    )
    excluded_contributors: tuple[QuantValueExcludedContributor, ...] = Field(
        default_factory=tuple
    )

class LabelFreeQuantTable(JsonModel):
    """Sample-by-entity quantification matrix with stable cell semantics."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    normalization_method: NormalizationMethod = NormalizationMethod.NONE
    imputation_method: ImputationMethod = ImputationMethod.NONE
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    entity_ids: tuple[str, ...] = Field(default_factory=tuple)
    values: tuple[QuantValue, ...] = Field(default_factory=tuple)
    quant_matrix: CanonicalQuantMatrix | None = None
    normalization_factors: dict[str, float] = Field(default_factory=dict)
    entity_protein_refs: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    entity_member_peptides: dict[str, tuple[str, ...]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _bind_canonical_quant_matrix(self) -> LabelFreeQuantTable:
        from .matrix_building import _resolve_quant_value_provenance

        resolved_values: list[QuantValue] = []
        values_changed = False
        for value in self.values:
            resolved_provenance = _resolve_quant_value_provenance(
                value=value,
                entity_level=self.entity_level,
                aggregation_method=self.aggregation_method,
                entity_member_peptides=self.entity_member_peptides,
            )
            if resolved_provenance != value.value_provenance:
                value = value.model_copy(
                    update={"value_provenance": resolved_provenance}
                )
                values_changed = True
            resolved_values.append(value)
        if values_changed:
            self.values = tuple(resolved_values)
        quant_matrix = self.quant_matrix
        if quant_matrix is None:
            quant_matrix = self._build_canonical_quant_matrix()
            self.quant_matrix = quant_matrix
        elif quant_matrix.entity_ids != self.entity_ids:
            raise ValueError("quant_matrix entity_ids must match entity_ids")
        elif quant_matrix.sample_ids != self.sample_ids:
            raise ValueError("quant_matrix sample_ids must match sample_ids")
        return self

    def _build_canonical_quant_matrix(self) -> CanonicalQuantMatrix:
        from .matrix_building import (
            _canonical_entity_kind,
            _canonical_measure_kind,
            _canonical_missing_value_state,
        )

        return build_numeric_quant_matrix(
            matrix_id=f"{self.entity_level.value}_{self.measure_kind.value}_table",
            entity_kind=_canonical_entity_kind(self.entity_level),
            measure_kind=_canonical_measure_kind(self.measure_kind),
            entity_ids=self.entity_ids,
            sample_ids=self.sample_ids,
            value_lookup={
                (value.entity_id, value.sample_id): value.abundance for value in self.values
            },
            missing_state_lookup={
                (value.entity_id, value.sample_id): _canonical_missing_value_state(
                    value.missing_value_kind
                )
                for value in self.values
            },
            support_count_lookup={
                (value.entity_id, value.sample_id): value.source_feature_count
                for value in self.values
            },
            row_metadata_lookup={
                entity_id: {
                    "protein_refs": ";".join(self.entity_protein_refs.get(entity_id, ())),
                    "member_peptides": ";".join(
                        self.entity_member_peptides.get(entity_id, ())
                    ),
                }
                for entity_id in self.entity_ids
            },
            transformation_history=(
                f"entity_level:{self.entity_level.value}",
                f"measure_kind:{self.measure_kind.value}",
                f"aggregation_method:{self.aggregation_method.value}",
                f"normalization_method:{self.normalization_method.value}",
                f"imputation_method:{self.imputation_method.value}",
            ),
            metadata={
                "normalization_method": self.normalization_method.value,
                "imputation_method": self.imputation_method.value,
            },
        )

    def to_quant_matrix(self) -> CanonicalQuantMatrix:
        """Return the canonical numeric matrix that backs this quant table."""

        assert self.quant_matrix is not None
        return self.quant_matrix

    @classmethod
    def from_quant_matrix(
        cls,
        matrix: CanonicalQuantMatrix,
        *,
        entity_level: QuantEntityLevel,
        aggregation_method: QuantRollupMethod,
        normalization_method: NormalizationMethod = NormalizationMethod.NONE,
        imputation_method: ImputationMethod = ImputationMethod.NONE,
        normalization_factors: dict[str, float] | None = None,
        entity_protein_refs: dict[str, tuple[str, ...]] | None = None,
        entity_member_peptides: dict[str, tuple[str, ...]] | None = None,
    ) -> LabelFreeQuantTable:
        """Build one label-free table from a canonical numeric matrix."""

        from .matrix_building import (
            _iter_label_free_quant_cells,
            _missing_value_kind_from_canonical,
            _quant_measure_kind_from_canonical,
            _split_row_metadata_values,
        )

        row_metadata_lookup = {
            entity_id: matrix.row_metadata[index]
            for index, entity_id in enumerate(matrix.entity_ids)
        }
        resolved_protein_refs = (
            entity_protein_refs
            if entity_protein_refs is not None
            else {
                entity_id: _split_row_metadata_values(
                    row_metadata_lookup.get(entity_id, {}).get("protein_refs", "")
                )
                for entity_id in matrix.entity_ids
            }
        )
        resolved_member_peptides = (
            entity_member_peptides
            if entity_member_peptides is not None
            else {
                entity_id: _split_row_metadata_values(
                    row_metadata_lookup.get(entity_id, {}).get("member_peptides", "")
                )
                for entity_id in matrix.entity_ids
            }
        )
        values = tuple(
            QuantValue(
                entity_id=entity_id,
                sample_id=sample_id,
                abundance=abundance,
                missing_value_kind=_missing_value_kind_from_canonical(state),
                source_feature_count=support_count,
            )
            for entity_id, sample_id, abundance, state, support_count in _iter_label_free_quant_cells(
                matrix
            )
        )
        return cls(
            entity_level=entity_level,
            measure_kind=_quant_measure_kind_from_canonical(matrix.measure_kind),
            aggregation_method=aggregation_method,
            normalization_method=normalization_method,
            imputation_method=imputation_method,
            sample_ids=matrix.sample_ids,
            entity_ids=matrix.entity_ids,
            values=values,
            quant_matrix=matrix,
            normalization_factors=(
                dict.fromkeys(matrix.sample_ids, 1.0)
                if normalization_factors is None
                else normalization_factors
            ),
            entity_protein_refs=resolved_protein_refs,
            entity_member_peptides=resolved_member_peptides,
        )

class QuantSampleMetadataEntry(JsonModel):
    """Stable sample metadata attached to exported quantification matrices."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    replicate: int | None = Field(default=None, ge=1)
    fraction: int | None = Field(default=None, ge=1)
    batch: str | None = None
    instrument: str | None = None
    search_engine: str | None = None

class QuantNormalizationProvenance(JsonModel):
    """Normalization context preserved alongside exported quant matrices."""

    model_config = ConfigDict(extra="forbid")

    normalization_method: NormalizationMethod
    normalization_factors: dict[str, float] = Field(default_factory=dict)
    note: str = Field(..., min_length=1)

class QuantImputationProvenance(JsonModel):
    """Imputation context preserved alongside exported quant matrices."""

    model_config = ConfigDict(extra="forbid")

    imputation_method: ImputationMethod = ImputationMethod.NONE
    imputed_value_count: int = Field(default=0, ge=0)
    note: str = Field(..., min_length=1)

class QuantMatrixExportRow(JsonModel):
    """One stable export row from a quantification matrix."""

    model_config = ConfigDict(extra="forbid")

    sample_metadata: QuantSampleMetadataEntry
    entity_id: str = Field(..., min_length=1)
    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    source_feature_count: int = Field(..., ge=0)
    value_provenance: QuantValueProvenance | None = None
    imputation_provenance: QuantCellImputationProvenance | None = None
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    member_peptides: tuple[str, ...] = Field(default_factory=tuple)

class QuantMatrixExport(JsonModel):
    """Export-ready quantification matrix with metadata and provenance."""

    model_config = ConfigDict(extra="forbid")

    entity_level: QuantEntityLevel
    measure_kind: QuantMeasureKind
    aggregation_method: QuantRollupMethod
    rows: tuple[QuantMatrixExportRow, ...] = Field(default_factory=tuple)
    normalization_provenance: QuantNormalizationProvenance
    imputation_provenance: QuantImputationProvenance
