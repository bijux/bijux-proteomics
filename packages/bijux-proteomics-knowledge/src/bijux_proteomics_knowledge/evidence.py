# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Evidence bundles for scientific review."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceKind(StrEnum):
    """Evidence families tracked by the platform."""

    LITERATURE = "literature"
    STRUCTURE = "structure"
    ASSAY = "assay"
    PATHWAY = "pathway"
    SAFETY = "safety"


class EvidenceStrength(StrEnum):
    """How strongly an evidence record supports a claim."""

    EXPLORATORY = "exploratory"
    SUPPORTING = "supporting"
    DECISIVE = "decisive"


class EvidenceRecord(BaseModel):
    """Single evidence statement."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(
        ...,
        min_length=1,
        description="Stable evidence identifier.",
    )
    kind: EvidenceKind = Field(..., description="Evidence family.")
    title: str = Field(..., min_length=1, description="Short title.")
    source: str = Field(..., min_length=1, description="Source location or system.")
    claim: str = Field(..., min_length=1, description="Human-readable claim.")
    related_targets: list[str] = Field(
        default_factory=list,
        description="Related target identifiers.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in the record.",
    )
    strength: EvidenceStrength = Field(..., description="Support level.")


class EvidenceBundle(BaseModel):
    """Set of evidence attached to a program or target."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1, description="Stable bundle identifier.")
    target_id: str = Field(..., min_length=1, description="Target identifier.")
    records: list[EvidenceRecord] = Field(
        default_factory=list,
        description="Evidence records in the bundle.",
    )


def summarize_bundle(bundle: EvidenceBundle) -> dict[str, object]:
    """Build a compact evidence summary."""
    by_kind = {kind.value: 0 for kind in EvidenceKind}
    decisive = 0
    for record in bundle.records:
        by_kind[record.kind.value] += 1
        if record.strength is EvidenceStrength.DECISIVE:
            decisive += 1
    return {
        "bundle_id": bundle.bundle_id,
        "target_id": bundle.target_id,
        "record_count": len(bundle.records),
        "decisive_records": decisive,
        "by_kind": by_kind,
    }


def evidence_gaps(bundle: EvidenceBundle, required_kinds: list[str]) -> list[str]:
    """Return required evidence kinds that are still missing."""
    present = {record.kind.value for record in bundle.records}
    return [kind for kind in required_kinds if kind not in present]
