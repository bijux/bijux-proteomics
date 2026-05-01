# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Proteoform identity contracts with explicit ambiguity and provenance."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics_foundation import JsonModel


class ProteoformEvidenceLevel(StrEnum):
    """Evidence level over one proteoform identity interpretation."""

    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    ADVISORY = "advisory"
    HYPOTHESIS = "hypothesis"


class ProteoformPtmAssignment(JsonModel):
    """One PTM assignment retained in a proteoform identity."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    site: str = Field(..., min_length=1)
    localization_state: str = Field(default="localized", min_length=1)
    ambiguity_note: str | None = None


class ProteoformIdentity(JsonModel):
    """Stable proteoform identity keyed by sequence, PTM combination, and origin."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    protein_origin: str = Field(..., min_length=1)
    evidence_level: ProteoformEvidenceLevel
    ambiguity_summary: str | None = None
    ptm_assignments: tuple[ProteoformPtmAssignment, ...] = Field(default_factory=tuple)
    canonical_proteoform_key: str = Field(..., min_length=1)

    @field_validator("sequence")
    @classmethod
    def _normalize_sequence(cls, value: str) -> str:
        return value.strip().upper()


def build_proteoform_identity(
    *,
    sequence: str,
    protein_origin: str,
    evidence_level: ProteoformEvidenceLevel = ProteoformEvidenceLevel.ADVISORY,
    ptm_assignments: Sequence[ProteoformPtmAssignment] = (),
    ambiguity_summary: str | None = None,
) -> ProteoformIdentity:
    """Build a proteoform identity with deterministic PTM ordering."""
    normalized_sequence = sequence.strip().upper()
    normalized_assignments = tuple(
        sorted(
            ptm_assignments,
            key=lambda assignment: (
                assignment.site.lower(),
                assignment.name.lower(),
                assignment.localization_state.lower(),
            ),
        )
    )
    assignment_token = "|".join(
        f"{entry.site}:{entry.name}:{entry.localization_state}"
        for entry in normalized_assignments
    )
    canonical_key = f"{normalized_sequence}::{protein_origin.strip()}::{assignment_token or 'unmodified'}"
    return ProteoformIdentity(
        sequence=normalized_sequence,
        protein_origin=protein_origin.strip(),
        evidence_level=evidence_level,
        ambiguity_summary=ambiguity_summary,
        ptm_assignments=normalized_assignments,
        canonical_proteoform_key=canonical_key,
    )
