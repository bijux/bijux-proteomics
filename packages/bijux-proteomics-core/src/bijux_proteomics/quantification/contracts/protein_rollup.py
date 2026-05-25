# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from collections import defaultdict
import csv
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import DocumentSchema, JsonModel

if TYPE_CHECKING:
    pass


from .input_models import (
    MissingValueKind,
    Ms1FeatureRecord,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
)
from .matrix_building import _matrix_value_index, build_label_free_intensity_table
from .matrix_models import QuantMatrixExport
from .normalization_imputation import normalize_label_free_table

class ProteinQuantAssignmentPolicy(StrEnum):
    """Shared-peptide handling policies for protein-level quant rollups."""

    INFERENCE_INCLUSIVE = "inference_inclusive"
    QUANT_UNIQUE_ONLY = "quant_unique_only"
    QUANT_SPLIT_SHARED = "quant_split_shared"

class ProteinQuantPolicyValue(JsonModel):
    """One protein/sample abundance under one explicit assignment policy."""

    model_config = ConfigDict(extra="forbid")

    assignment_policy: ProteinQuantAssignmentPolicy
    abundance: float | None = Field(default=None, ge=0.0)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptide_count: int = Field(..., ge=0)

class ProteinQuantPolicyComparisonEntry(JsonModel):
    """One explicit policy comparison for a protein/sample quant rollup."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    policy_values: tuple[ProteinQuantPolicyValue, ...] = Field(default_factory=tuple)
    max_abundance_difference: float = Field(..., ge=0.0)

class ProteinQuantPolicyComparisonReport(JsonModel):
    """Comparison of protein-level quant outcomes across assignment policies."""

    model_config = ConfigDict(extra="forbid")

    policies: tuple[ProteinQuantAssignmentPolicy, ...] = Field(default_factory=tuple)
    entries: tuple[ProteinQuantPolicyComparisonEntry, ...] = Field(
        default_factory=tuple
    )

class ProteinQuantRollupEvidenceEntry(JsonModel):
    """One protein/sample rollup with explicit contributing peptide and feature evidence."""

    model_config = ConfigDict(extra="forbid")

    protein_ref: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    aggregation_method: QuantRollupMethod
    abundance: float | None = Field(default=None, ge=0.0)
    contributing_feature_ids: tuple[str, ...] = Field(default_factory=tuple)
    contributing_peptides: tuple[str, ...] = Field(default_factory=tuple)
    missing_value_kind: MissingValueKind

class LabelFreeFeatureProvenanceEntry(JsonModel):
    """Feature-level provenance preserved inside an LFQ workflow bundle."""

    model_config = ConfigDict(extra="forbid")

    feature_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    intensity: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind

class LabelFreePeptideProvenanceEntry(JsonModel):
    """Peptide-level LFQ abundance plus contributing raw features."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    missing_value_kind: MissingValueKind
    contributing_feature_ids: tuple[str, ...] = Field(default_factory=tuple)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)

class LabelFreeProvenanceBundle(JsonModel):
    """Reviewable LFQ provenance across features, peptides, and proteins."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    aggregation_method: QuantRollupMethod
    normalization_method: NormalizationMethod
    feature_entries: tuple[LabelFreeFeatureProvenanceEntry, ...] = Field(
        default_factory=tuple
    )
    peptide_entries: tuple[LabelFreePeptideProvenanceEntry, ...] = Field(
        default_factory=tuple
    )
    protein_entries: tuple[ProteinQuantRollupEvidenceEntry, ...] = Field(
        default_factory=tuple
    )

def _protein_quant_assignment_targets(
    record: Ms1FeatureRecord,
    *,
    assignment_policy: ProteinQuantAssignmentPolicy,
) -> tuple[tuple[str, float], ...]:
    if not record.protein_refs or record.intensity is None:
        return ()
    if assignment_policy is ProteinQuantAssignmentPolicy.INFERENCE_INCLUSIVE:
        return tuple(
            (protein_ref, float(record.intensity))
            for protein_ref in record.protein_refs
        )
    if assignment_policy is ProteinQuantAssignmentPolicy.QUANT_UNIQUE_ONLY:
        if len(record.protein_refs) == 1:
            return ((record.protein_refs[0], float(record.intensity)),)
        return ()
    split_intensity = float(record.intensity) / len(record.protein_refs)
    return tuple((protein_ref, split_intensity) for protein_ref in record.protein_refs)

def build_protein_quant_policy_comparison_report(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    policies: tuple[ProteinQuantAssignmentPolicy, ...] = (
        ProteinQuantAssignmentPolicy.INFERENCE_INCLUSIVE,
        ProteinQuantAssignmentPolicy.QUANT_UNIQUE_ONLY,
        ProteinQuantAssignmentPolicy.QUANT_SPLIT_SHARED,
    ),
) -> ProteinQuantPolicyComparisonReport:
    """Compare protein-level quant results under explicit shared-peptide policies."""
    per_policy: dict[
        ProteinQuantAssignmentPolicy,
        dict[tuple[str, str], list[tuple[Ms1FeatureRecord, float]]],
    ] = {}
    proteins: set[str] = set()
    sample_ids: set[str] = set()
    for policy in policies:
        grouped: dict[tuple[str, str], list[tuple[Ms1FeatureRecord, float]]] = (
            defaultdict(list)
        )
        for record in records:
            sample_ids.add(record.sample_id)
            for protein_ref, intensity in _protein_quant_assignment_targets(
                record,
                assignment_policy=policy,
            ):
                proteins.add(protein_ref)
                grouped[(protein_ref, record.sample_id)].append((record, intensity))
        per_policy[policy] = grouped

    entries: list[ProteinQuantPolicyComparisonEntry] = []
    for protein_ref in sorted(proteins):
        for sample_id in sorted(sample_ids):
            values: list[ProteinQuantPolicyValue] = []
            abundances: list[float] = []
            for policy in policies:
                bucket = sorted(
                    per_policy[policy].get((protein_ref, sample_id), ()),
                    key=lambda item: (item[0].canonical_peptide, item[0].feature_id),
                )
                abundance = (
                    float(sum(intensity for _, intensity in bucket)) if bucket else None
                )
                if abundance is not None:
                    abundances.append(abundance)
                values.append(
                    ProteinQuantPolicyValue(
                        assignment_policy=policy,
                        abundance=abundance,
                        contributing_peptides=tuple(
                            dict.fromkeys(
                                record.canonical_peptide for record, _ in bucket
                            )
                        ),
                        shared_peptide_count=sum(
                            1 for record, _ in bucket if len(record.protein_refs) > 1
                        ),
                    )
                )
            entries.append(
                ProteinQuantPolicyComparisonEntry(
                    protein_ref=protein_ref,
                    sample_id=sample_id,
                    policy_values=tuple(values),
                    max_abundance_difference=(
                        max(abundances) - min(abundances) if abundances else 0.0
                    ),
                )
            )
    return ProteinQuantPolicyComparisonReport(
        policies=policies,
        entries=tuple(entries),
    )

def build_protein_quant_rollup_evidence(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    top_n: int = 3,
) -> tuple[ProteinQuantRollupEvidenceEntry, ...]:
    """Build explicit protein rollup evidence from contributing peptide features."""
    table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    entries: list[ProteinQuantRollupEvidenceEntry] = []
    value_lookup = _matrix_value_index(table)
    for protein_ref in table.entity_ids:
        for sample_id in table.sample_ids:
            value = value_lookup[(protein_ref, sample_id)]
            entries.append(
                ProteinQuantRollupEvidenceEntry(
                    protein_ref=protein_ref,
                    sample_id=sample_id,
                    aggregation_method=aggregation_method,
                    abundance=value.abundance,
                    contributing_feature_ids=(
                        ()
                        if value.value_provenance is None
                        else value.value_provenance.source_feature_ids
                    ),
                    contributing_peptides=(
                        ()
                        if value.value_provenance is None
                        else value.value_provenance.source_peptides
                    ),
                    missing_value_kind=value.missing_value_kind,
                )
            )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (entry.protein_ref, entry.sample_id),
        )
    )

def build_label_free_provenance_bundle(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    normalization_method: NormalizationMethod = NormalizationMethod.NONE,
    top_n: int = 3,
) -> LabelFreeProvenanceBundle:
    """Build peptide-level and feature-level provenance for an LFQ workflow."""
    peptide_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PEPTIDE,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    protein_table = build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    if normalization_method is not NormalizationMethod.NONE:
        peptide_table = normalize_label_free_table(
            peptide_table,
            method=normalization_method,
        )
        protein_table = normalize_label_free_table(
            protein_table,
            method=normalization_method,
        )
    peptide_value_lookup = _matrix_value_index(peptide_table)
    protein_value_lookup = _matrix_value_index(protein_table)

    grouped_features: dict[tuple[str, str], list[Ms1FeatureRecord]] = defaultdict(list)
    for record in records:
        grouped_features[(record.canonical_peptide, record.sample_id)].append(record)

    peptide_entries: list[LabelFreePeptideProvenanceEntry] = []
    for canonical_peptide in peptide_table.entity_ids:
        for sample_id in peptide_table.sample_ids:
            value = peptide_value_lookup[(canonical_peptide, sample_id)]
            features = sorted(
                grouped_features.get((canonical_peptide, sample_id), ()),
                key=lambda record: record.feature_id,
            )
            peptide_entries.append(
                LabelFreePeptideProvenanceEntry(
                    sample_id=sample_id,
                    canonical_peptide=canonical_peptide,
                    abundance=value.abundance,
                    missing_value_kind=value.missing_value_kind,
                    contributing_feature_ids=tuple(
                        record.feature_id for record in features
                    ),
                    protein_refs=tuple(
                        dict.fromkeys(
                            protein_ref
                            for record in features
                            for protein_ref in record.protein_refs
                        )
                    ),
                )
            )

    protein_entries = []
    for entry in build_protein_quant_rollup_evidence(
        records,
        aggregation_method=aggregation_method,
        top_n=top_n,
    ):
        protein_entries.append(
            entry.model_copy(
                update={
                    "abundance": protein_value_lookup[
                        (entry.protein_ref, entry.sample_id)
                    ].abundance,
                    "missing_value_kind": protein_value_lookup[
                        (entry.protein_ref, entry.sample_id)
                    ].missing_value_kind,
                }
            )
        )

    bundle = LabelFreeProvenanceBundle(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="label_free_provenance_bundle",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        aggregation_method=aggregation_method,
        normalization_method=normalization_method,
        feature_entries=tuple(
            LabelFreeFeatureProvenanceEntry(
                feature_id=record.feature_id,
                sample_id=record.sample_id,
                canonical_peptide=record.canonical_peptide,
                protein_refs=record.protein_refs,
                intensity=record.intensity,
                missing_value_kind=record.missing_value_kind,
            )
            for record in sorted(
                records,
                key=lambda record: (
                    record.sample_id,
                    record.canonical_peptide,
                    record.feature_id,
                ),
            )
        ),
        peptide_entries=tuple(
            sorted(
                peptide_entries,
                key=lambda entry: (entry.canonical_peptide, entry.sample_id),
            )
        ),
        protein_entries=tuple(
            sorted(
                protein_entries,
                key=lambda entry: (entry.protein_ref, entry.sample_id),
            )
        ),
    )
    return bundle.model_copy(
        update={
            "document_schema": bundle.document_schema.with_content_hash(
                bundle.to_dict()
            )
        }
    )

def export_label_free_provenance_bundle(
    bundle: LabelFreeProvenanceBundle,
    path: Path,
) -> None:
    """Write a stable JSON bundle for LFQ provenance review."""
    path.write_text(bundle.to_stable_json() + "\n", encoding="utf-8")

def export_quant_matrix_tsv(
    matrix_export: QuantMatrixExport,
    path: Path,
) -> None:
    """Write one stable TSV export for a quantification matrix."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "sample_id",
                "condition",
                "replicate",
                "fraction",
                "batch",
                "instrument",
                "search_engine",
                "entity_id",
                "entity_level",
                "measure_kind",
                "aggregation_method",
                "abundance",
                "missing_value_kind",
                "value_origin",
                "source_feature_count",
                "source_feature_ids",
                "source_peptides",
                "source_precursor_ids",
                "excluded_contributor_ids",
                "exclusion_reason_codes",
                "imputation_method",
                "imputation_strategy",
                "imputation_reference_group",
                "imputation_donor_sample_ids",
                "imputation_donor_entity_ids",
                "original_missing_value_kind",
                "protein_refs",
                "member_peptides",
                "normalization_method",
                "normalization_factor",
            ]
        )
        for row in matrix_export.rows:
            writer.writerow(
                [
                    row.sample_metadata.sample_id,
                    row.sample_metadata.condition or "",
                    row.sample_metadata.replicate or "",
                    row.sample_metadata.fraction or "",
                    row.sample_metadata.batch or "",
                    row.sample_metadata.instrument or "",
                    row.sample_metadata.search_engine or "",
                    row.entity_id,
                    row.entity_level.value,
                    row.measure_kind.value,
                    row.aggregation_method.value,
                    "" if row.abundance is None else row.abundance,
                    row.missing_value_kind.value,
                    (
                        ""
                        if row.value_provenance is None
                        else row.value_provenance.value_origin.value
                    ),
                    row.source_feature_count,
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(row.value_provenance.source_feature_ids)
                    ),
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(row.value_provenance.source_peptides)
                    ),
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(row.value_provenance.source_precursor_ids)
                    ),
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(
                            excluded.contributor.contributor_id
                            for excluded in row.value_provenance.excluded_contributors
                        )
                    ),
                    (
                        ""
                        if row.value_provenance is None
                        else ";".join(
                            excluded.reason_code
                            for excluded in row.value_provenance.excluded_contributors
                        )
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else row.imputation_provenance.method.value
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else row.imputation_provenance.strategy
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        or row.imputation_provenance.reference_group is None
                        else row.imputation_provenance.reference_group
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else ";".join(row.imputation_provenance.donor_sample_ids)
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else ";".join(row.imputation_provenance.donor_entity_ids)
                    ),
                    (
                        ""
                        if row.imputation_provenance is None
                        else row.imputation_provenance.original_missing_value_kind.value
                    ),
                    ";".join(row.protein_refs),
                    ";".join(row.member_peptides),
                    matrix_export.normalization_provenance.normalization_method.value,
                    matrix_export.normalization_provenance.normalization_factors.get(
                        row.sample_metadata.sample_id,
                        1.0,
                    ),
                ]
            )
