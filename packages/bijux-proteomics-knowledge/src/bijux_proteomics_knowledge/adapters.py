# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Adapter contracts for external evidence ingestion."""

from __future__ import annotations

from typing import Protocol

from pydantic import ConfigDict, Field

from bijux_proteomics_knowledge.evidence import (
    EvidenceBundle,
    EvidenceKind,
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
                claim=item.claim,
                related_targets=item.related_targets,
                decision_tags=item.decision_tags,
                confidence=item.confidence,
                strength=item.strength,
            )
        )
    return bundle.model_copy(update={"records": records})
