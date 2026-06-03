# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Guarded proteoform quantification over uniquely attributable feature evidence."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import (
    MissingValueState,
)
from bijux_proteomics.domain.records import (
    QuantMatrix as CanonicalQuantMatrix,
)
from bijux_proteomics.proteoforms.assembly import ProteoformCandidateEntry
from bijux_proteomics_foundation import JsonModel


class ProteoformQuantificationConfidence(StrEnum):
    """Stable confidence tiers for guarded proteoform abundance calls."""

    SITE_SPECIFIC_UNIQUE_SUPPORT = "site_specific_unique_support"
    PEPTIDE_SPECIFIC_UNIQUE_SUPPORT = "peptide_specific_unique_support"
    INSUFFICIENT_UNIQUE_SUPPORT = "insufficient_unique_support"


class ProteoformQuantificationEntry(JsonModel):
    """One per-sample proteoform abundance row with explicit support guardrails."""

    model_config = ConfigDict(extra="forbid")

    proteoform_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    abundance: float | None = Field(default=None, ge=0.0)
    unique_support_count: int = Field(..., ge=0)
    quantification_confidence: ProteoformQuantificationConfidence


class ProteoformQuantificationReport(JsonModel):
    """Proteoform quantification report over one canonical feature matrix."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteoformQuantificationEntry, ...] = Field(default_factory=tuple)
    quantified_entry_count: int = Field(..., ge=0)
    withheld_entry_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class _FeatureEvidenceRow(JsonModel):
    """One parsed matrix row with the exact evidence relevant to proteoform support."""

    model_config = ConfigDict(extra="forbid")

    row_index: int = Field(..., ge=0)
    entity_id: str = Field(..., min_length=1)
    protein_id: str | None = None
    peptide_ids: tuple[str, ...] = Field(default_factory=tuple)
    site_ids: tuple[str, ...] = Field(default_factory=tuple)


def quantify_supported_proteoforms(
    candidates: tuple[ProteoformCandidateEntry, ...],
    feature_matrix: CanonicalQuantMatrix,
) -> ProteoformQuantificationReport:
    """Quantify proteoforms only when one sample has unique supporting evidence."""

    candidate_ids = tuple(candidate.proteoform_id for candidate in candidates)
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("proteoform quantification requires unique proteoform_id rows")

    feature_rows = tuple(
        _coerce_feature_row(feature_matrix, row_index)
        for row_index in range(len(feature_matrix.entity_ids))
    )
    candidate_lookup_by_protein: dict[str, list[ProteoformCandidateEntry]] = {}
    for candidate in candidates:
        candidate_lookup_by_protein.setdefault(candidate.protein_id, []).append(
            candidate
        )

    compatible_candidates_by_row = tuple(
        _compatible_candidates(
            row=row,
            candidates=tuple(candidate_lookup_by_protein.get(row.protein_id or "", ())),
        )
        for row in feature_rows
    )

    entries: list[ProteoformQuantificationEntry] = []
    for candidate in candidates:
        for sample_index, sample_id in enumerate(feature_matrix.sample_ids):
            unique_support_rows = [
                feature_rows[row_index]
                for row_index, compatible in enumerate(compatible_candidates_by_row)
                if len(compatible) == 1
                and compatible[0].proteoform_id == candidate.proteoform_id
                and _cell_is_observed_positive(
                    feature_matrix=feature_matrix,
                    row_index=row_index,
                    sample_index=sample_index,
                )
            ]
            unique_support_count = len(unique_support_rows)
            abundance = None
            if unique_support_rows:
                abundance = float(
                    sum(
                        feature_matrix.values[row.row_index][sample_index] or 0.0
                        for row in unique_support_rows
                    )
                )
            confidence = _confidence_from_support_rows(unique_support_rows)
            entries.append(
                ProteoformQuantificationEntry(
                    proteoform_id=candidate.proteoform_id,
                    sample_id=sample_id,
                    abundance=abundance,
                    unique_support_count=unique_support_count,
                    quantification_confidence=confidence,
                )
            )

    ordered_entries = tuple(
        sorted(entries, key=lambda entry: (entry.proteoform_id, entry.sample_id))
    )
    return ProteoformQuantificationReport(
        entries=ordered_entries,
        quantified_entry_count=sum(
            1 for entry in ordered_entries if entry.abundance is not None
        ),
        withheld_entry_count=sum(
            1 for entry in ordered_entries if entry.abundance is None
        ),
        note=(
            "proteoform abundance is emitted only from sample-level feature rows that "
            "support exactly one candidate within the same protein boundary"
        ),
    )


def render_proteoform_quantification_tsv(
    report: ProteoformQuantificationReport,
) -> str:
    """Render guarded proteoform quantification rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "proteoform_id",
            "sample_id",
            "abundance",
            "unique_support_count",
            "quantification_confidence",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.proteoform_id,
                entry.sample_id,
                "" if entry.abundance is None else f"{entry.abundance:.6f}",
                entry.unique_support_count,
                entry.quantification_confidence.value,
            )
        )
    return buffer.getvalue()


def _coerce_feature_row(
    feature_matrix: CanonicalQuantMatrix,
    row_index: int,
) -> _FeatureEvidenceRow:
    entity_id = feature_matrix.entity_ids[row_index]
    metadata = (
        {}
        if row_index >= len(feature_matrix.row_metadata)
        else feature_matrix.row_metadata[row_index]
    )
    protein_id = _resolve_unique_protein_id(metadata)
    peptide_ids = _split_metadata_tokens(
        metadata,
        primary_key="peptide_ids",
        fallback_keys=("peptide_id",),
    )
    site_ids = _split_metadata_tokens(
        metadata,
        primary_key="site_ids",
        fallback_keys=("site_id",),
    )
    return _FeatureEvidenceRow(
        row_index=row_index,
        entity_id=entity_id,
        protein_id=protein_id,
        peptide_ids=peptide_ids,
        site_ids=site_ids,
    )


def _resolve_unique_protein_id(metadata: dict[str, str]) -> str | None:
    if protein_id := metadata.get("protein_id"):
        normalized = protein_id.strip()
        return normalized or None
    if protein_ref := metadata.get("protein_ref"):
        normalized = protein_ref.strip()
        return normalized or None
    protein_refs = _split_metadata_tokens(
        metadata,
        primary_key="protein_refs",
        fallback_keys=(),
    )
    if len(protein_refs) == 1:
        return protein_refs[0]
    return None


def _split_metadata_tokens(
    metadata: dict[str, str],
    *,
    primary_key: str,
    fallback_keys: tuple[str, ...],
) -> tuple[str, ...]:
    raw_value = metadata.get(primary_key)
    if raw_value is None:
        for key in fallback_keys:
            raw_value = metadata.get(key)
            if raw_value is not None:
                break
    if raw_value is None:
        return ()
    return tuple(
        token for token in (part.strip() for part in str(raw_value).split(";")) if token
    )


def _compatible_candidates(
    *,
    row: _FeatureEvidenceRow,
    candidates: tuple[ProteoformCandidateEntry, ...],
) -> tuple[ProteoformCandidateEntry, ...]:
    if row.protein_id is None:
        return ()
    compatible: list[ProteoformCandidateEntry] = []
    for candidate in candidates:
        if candidate.protein_id != row.protein_id:
            continue
        if row.peptide_ids and not set(row.peptide_ids).issubset(
            candidate.required_peptides
        ):
            continue
        if row.site_ids and not set(row.site_ids).issubset(candidate.required_sites):
            continue
        excluded_labels = set(candidate.excluded_by_evidence)
        if excluded_labels.intersection(
            row.peptide_ids
        ) or excluded_labels.intersection(row.site_ids):
            continue
        if not row.peptide_ids and not row.site_ids:
            continue
        compatible.append(candidate)
    return tuple(compatible)


def _cell_is_observed_positive(
    *,
    feature_matrix: CanonicalQuantMatrix,
    row_index: int,
    sample_index: int,
) -> bool:
    value = feature_matrix.values[row_index][sample_index]
    state = feature_matrix.missing_value_states[row_index][sample_index]
    return state is MissingValueState.OBSERVED and value is not None and value > 0.0


def _confidence_from_support_rows(
    rows: list[_FeatureEvidenceRow],
) -> ProteoformQuantificationConfidence:
    if not rows:
        return ProteoformQuantificationConfidence.INSUFFICIENT_UNIQUE_SUPPORT
    if any(row.site_ids for row in rows):
        return ProteoformQuantificationConfidence.SITE_SPECIFIC_UNIQUE_SUPPORT
    return ProteoformQuantificationConfidence.PEPTIDE_SPECIFIC_UNIQUE_SUPPORT


__all__ = [
    "ProteoformQuantificationConfidence",
    "ProteoformQuantificationEntry",
    "ProteoformQuantificationReport",
    "quantify_supported_proteoforms",
    "render_proteoform_quantification_tsv",
]
