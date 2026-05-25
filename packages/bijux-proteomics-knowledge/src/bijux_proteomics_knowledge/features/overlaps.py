# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein feature overlap resolution over curated region-context records."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field, model_validator

from bijux_proteomics.sequences import canonicalize_protein_reference
from bijux_proteomics.sequences.protein_region_context import (
    ProteinRegionContextImportReport,
    ProteinRegionContextRecord,
)
from bijux_proteomics_foundation import JsonModel


class ProteinFeatureType(StrEnum):
    """Stable feature kinds exposed by the knowledge overlap surface."""

    DOMAIN = "domain"
    SIGNAL_PEPTIDE = "signal_peptide"
    TRANSMEMBRANE_REGION = "transmembrane_region"
    DISORDER_REGION = "disorder_region"
    LOW_COMPLEXITY_REGION = "low_complexity_region"
    ACTIVE_SITE = "active_site"
    BINDING_REGION = "binding_region"
    MOTIF = "motif"


class ProteinFeatureQueryInterval(JsonModel):
    """One inclusive protein-coordinate interval to compare against features."""

    model_config = ConfigDict(extra="forbid")

    start: int = Field(..., ge=1)
    end: int = Field(..., ge=1)

    @model_validator(mode="after")
    def _validate_interval(self) -> ProteinFeatureQueryInterval:
        if self.end < self.start:
            raise ValueError("query interval end must be greater than or equal to start")
        return self


class ProteinFeatureOverlapEntry(JsonModel):
    """One protein feature that overlaps one inclusive query interval."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    query_start: int = Field(..., ge=1)
    query_end: int = Field(..., ge=1)
    feature_id: str = Field(..., min_length=1)
    feature_type: ProteinFeatureType
    overlap_start: int = Field(..., ge=1)
    overlap_end: int = Field(..., ge=1)


def overlap_protein_features(
    protein_id: str,
    intervals: tuple[ProteinFeatureQueryInterval, ...],
    feature_pack: ProteinRegionContextImportReport | tuple[ProteinRegionContextRecord, ...],
) -> tuple[ProteinFeatureOverlapEntry, ...]:
    """Resolve inclusive overlaps between query intervals and curated features."""

    canonical_protein_id = canonicalize_protein_reference(protein_id)
    context_records = _normalize_feature_pack(feature_pack)

    overlaps: list[ProteinFeatureOverlapEntry] = []
    for interval in intervals:
        for record in context_records:
            if canonicalize_protein_reference(record.protein_ref) != canonical_protein_id:
                continue
            overlap_start = max(interval.start, record.start)
            overlap_end = min(interval.end, record.end)
            if overlap_end < overlap_start:
                continue
            for feature_type, label in _feature_labels(record):
                overlaps.append(
                    ProteinFeatureOverlapEntry(
                        protein_id=canonical_protein_id,
                        query_start=interval.start,
                        query_end=interval.end,
                        feature_id=_feature_id(
                            record=record,
                            feature_type=feature_type,
                            label=label,
                        ),
                        feature_type=feature_type,
                        overlap_start=overlap_start,
                        overlap_end=overlap_end,
                    )
                )

    return tuple(
        sorted(
            overlaps,
            key=lambda entry: (
                entry.protein_id,
                entry.query_start,
                entry.query_end,
                entry.overlap_start,
                entry.overlap_end,
                entry.feature_type.value,
                entry.feature_id,
            ),
        )
    )


def render_protein_feature_overlaps_tsv(
    entries: tuple[ProteinFeatureOverlapEntry, ...],
) -> str:
    """Render protein feature overlap rows as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "protein_id",
            "query_start",
            "query_end",
            "feature_id",
            "feature_type",
            "overlap_start",
            "overlap_end",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.protein_id,
                entry.query_start,
                entry.query_end,
                entry.feature_id,
                entry.feature_type.value,
                entry.overlap_start,
                entry.overlap_end,
            )
        )
    return handle.getvalue()


def _normalize_feature_pack(
    feature_pack: ProteinRegionContextImportReport | tuple[ProteinRegionContextRecord, ...],
) -> tuple[ProteinRegionContextRecord, ...]:
    if isinstance(feature_pack, ProteinRegionContextImportReport):
        return feature_pack.accepted_records
    return feature_pack


def _feature_labels(
    record: ProteinRegionContextRecord,
) -> tuple[tuple[ProteinFeatureType, str], ...]:
    labels: list[tuple[ProteinFeatureType, str]] = []
    if record.domain_name is not None:
        labels.append((ProteinFeatureType.DOMAIN, record.domain_name))
    if record.signal_peptide is not None:
        labels.append((ProteinFeatureType.SIGNAL_PEPTIDE, record.signal_peptide))
    if record.transmembrane_region is not None:
        labels.append(
            (ProteinFeatureType.TRANSMEMBRANE_REGION, record.transmembrane_region)
        )
    if record.disorder_region is not None:
        labels.append((ProteinFeatureType.DISORDER_REGION, record.disorder_region))
    if record.low_complexity_region is not None:
        labels.append(
            (ProteinFeatureType.LOW_COMPLEXITY_REGION, record.low_complexity_region)
        )
    if record.active_site_label is not None:
        labels.append((ProteinFeatureType.ACTIVE_SITE, record.active_site_label))
    if record.binding_region is not None:
        labels.append((ProteinFeatureType.BINDING_REGION, record.binding_region))
    if record.motif_name is not None:
        labels.append((ProteinFeatureType.MOTIF, record.motif_name))
    return tuple(labels)


def _feature_id(
    *,
    record: ProteinRegionContextRecord,
    feature_type: ProteinFeatureType,
    label: str,
) -> str:
    identity_root = record.source_accession or canonicalize_protein_reference(
        record.protein_ref
    )
    return (
        f"{identity_root}:{feature_type.value}:{record.start}-{record.end}:{label}"
    )
