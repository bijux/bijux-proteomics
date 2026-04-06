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
