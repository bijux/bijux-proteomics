# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Adapter contracts for external evidence ingestion."""

from __future__ import annotations

from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics_knowledge.evidence import (
    EvidenceExtractionMethod,
    EvidenceBundle,
    EvidenceKind,
    EvidenceOrigin,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    QuantitativeSupport,
)
from bijux_proteomics_knowledge.serialization import JsonModel


class NormalizedEvidenceInput(JsonModel):
    """Normalized evidence payload produced by an ingestion adapter."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1, description="Stable evidence identifier.")
    kind: EvidenceKind = Field(..., description="Evidence family.")
    title: str = Field(..., min_length=1, description="Evidence title.")
    source: str = Field(..., min_length=1, description="Source location or system.")
    source_type: EvidenceSourceType = Field(..., description="Source category.")
    claim: str = Field(..., min_length=1, description="Normalized claim text.")
    related_targets: list[str] = Field(
        default_factory=list,
        description="Targets referenced by the payload.",
    )
    decision_tags: list[str] = Field(
        default_factory=list,
        description="Decision dimensions informed by the payload.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score.")
    strength: EvidenceStrength = Field(..., description="Support level.")
    source_uri: str | None = Field(
        default=None,
        description="Optional stable URI or note locator.",
    )
    curator: str | None = Field(
        default=None,
        description="Human or system that prepared the normalized payload.",
    )
    origin: EvidenceOrigin = Field(
        default=EvidenceOrigin.IMPORTED,
        description="Origin classification for the imported payload.",
    )
    extraction_method: EvidenceExtractionMethod = Field(
        default=EvidenceExtractionMethod.AUTOMATED_IMPORT,
        description="How the normalized payload was produced.",
    )
    derived_from: list[str] = Field(
        default_factory=list,
        description="Upstream evidence identifiers or note references.",
    )
    assay_modality: str | None = Field(default=None, description="Assay modality context.")
    biological_system: str | None = Field(default=None, description="Biological system context.")
    species: str | None = Field(default=None, description="Species context.")
    sample_type: str | None = Field(default=None, description="Sample or matrix type.")
    endpoint: str | None = Field(default=None, description="Primary measured endpoint.")
    quantitative_support: QuantitativeSupport | None = Field(
        default=None,
        description="Optional quantitative support for the claim.",
    )


class ManualEvidenceNote(JsonModel):
    """Curated note captured directly from a scientist or reviewer."""

    model_config = ConfigDict(extra="forbid")

    note_id: str = Field(..., min_length=1, description="Stable note identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    title: str = Field(..., min_length=1, description="Short note title.")
    claim: str = Field(..., min_length=1, description="Claim captured by the curator.")
    curator: str = Field(..., min_length=1, description="Person who captured the note.")
    kind: EvidenceKind = Field(..., description="Evidence family represented by the note.")
    decision_tags: list[str] = Field(
        default_factory=list,
        description="Decision dimensions informed by the note.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Curator confidence.")
    strength: EvidenceStrength = Field(..., description="Support level of the note.")
    source_uri: str | None = Field(
        default=None,
        description="Optional note locator in an external system.",
    )


class LiteratureIngestionAdapter(Protocol):
    """Adapter contract for literature-derived evidence."""

    def ingest_literature(self, target_id: str) -> list[NormalizedEvidenceInput]:
        """Return normalized evidence payloads for a target."""


class AssayResultIngestionAdapter(Protocol):
    """Adapter contract for assay-derived evidence."""

    def ingest_assay_results(self, target_id: str) -> list[NormalizedEvidenceInput]:
        """Return normalized assay payloads for a target."""


class StructureAnnotationIngestionAdapter(Protocol):
    """Adapter contract for structure-derived evidence."""

    def ingest_structure_annotations(
        self,
        target_id: str,
    ) -> list[NormalizedEvidenceInput]:
        """Return normalized structural payloads for a target."""


class ManualEvidenceNoteAdapter(Protocol):
    """Adapter contract for curated manual notes."""

    def ingest_manual_notes(self, target_id: str) -> list[ManualEvidenceNote]:
        """Return curated notes for a target."""


class IngestionReport(JsonModel):
    """Summary of one ingestion run into an evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Target evidence bundle identifier.")
    added_records: int = Field(default=0, ge=0, description="Number of records added.")
    skipped_records: int = Field(default=0, ge=0, description="Number of records skipped.")
    duplicate_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers skipped because they already existed.",
    )


def attach_evidence_inputs(
    bundle: EvidenceBundle,
    inputs: list[NormalizedEvidenceInput],
) -> EvidenceBundle:
    """Attach normalized adapter outputs to an existing bundle."""
    records = list(bundle.records)
    for item in inputs:
        records.append(
            EvidenceRecord(
                evidence_id=item.evidence_id,
                kind=item.kind,
                title=item.title,
                source=item.source,
                source_type=item.source_type,
                source_uri=item.source_uri,
                origin=item.origin,
                extraction_method=item.extraction_method,
                curator=item.curator,
                claim=item.claim,
                related_targets=item.related_targets,
                decision_tags=item.decision_tags,
                derived_from=item.derived_from,
                assay_modality=item.assay_modality,
                biological_system=item.biological_system,
                species=item.species,
                sample_type=item.sample_type,
                endpoint=item.endpoint,
                quantitative_support=item.quantitative_support,
                confidence=item.confidence,
                strength=item.strength,
            )
        )
    return bundle.model_copy(update={"records": records})


def attach_manual_notes(
    bundle: EvidenceBundle,
    notes: list[ManualEvidenceNote],
) -> EvidenceBundle:
    """Attach manually curated notes to an existing bundle."""
    return attach_evidence_inputs(
        bundle,
        [
            NormalizedEvidenceInput(
                evidence_id=note.note_id,
                kind=note.kind,
                title=note.title,
                source=f"manual-note:{note.curator}",
                source_type=EvidenceSourceType.CURATED_NOTE,
                source_uri=note.source_uri,
                claim=note.claim,
                related_targets=[note.target_id],
                decision_tags=note.decision_tags,
                confidence=note.confidence,
                strength=note.strength,
                curator=note.curator,
                origin=EvidenceOrigin.OBSERVED,
                extraction_method=EvidenceExtractionMethod.MANUAL_CURATION,
            )
            for note in notes
        ],
    )


def ingest_inputs_with_report(
    bundle: EvidenceBundle,
    inputs: list[NormalizedEvidenceInput],
) -> tuple[EvidenceBundle, IngestionReport]:
    """Attach normalized inputs and return an auditable ingestion report."""
    existing_ids = {record.evidence_id for record in bundle.records}
    accepted: list[NormalizedEvidenceInput] = []
    duplicate_ids: list[str] = []
    for item in inputs:
        if item.evidence_id in existing_ids:
            duplicate_ids.append(item.evidence_id)
            continue
        existing_ids.add(item.evidence_id)
        accepted.append(item)
    updated = attach_evidence_inputs(bundle, accepted)
    report = IngestionReport(
        bundle_id=bundle.bundle_id,
        added_records=len(accepted),
        skipped_records=len(duplicate_ids),
        duplicate_ids=duplicate_ids,
    )
    return updated, report
