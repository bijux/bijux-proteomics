# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Open-search unknown modification boundaries and advisory hypotheses."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class UnknownModificationHypothesis(JsonModel):
    """Unknown mass-shift hypothesis retained as advisory evidence."""

    model_config = ConfigDict(extra="forbid")

    mass_shift_da: float
    site_index: int | None = Field(default=None, ge=1)
    residue: str | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    advisory_only: bool = True
    promoted_as_identification: bool = False
    note: str = Field(..., min_length=1)


class OpenSearchUnknownModificationReport(JsonModel):
    """Boundary report for open-search unknown mass-shift outputs."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    hypotheses: tuple[UnknownModificationHypothesis, ...] = Field(default_factory=tuple)
    has_unknown_mass_shift: bool
    note: str = Field(..., min_length=1)


def build_open_search_unknown_mod_report(
    peptide_sequence: str,
    *,
    mass_shifts: Sequence[UnknownModificationHypothesis],
) -> OpenSearchUnknownModificationReport:
    """Build an advisory-only unknown modification report for open search."""
    normalized = peptide_sequence.strip().upper()
    hypotheses = tuple(mass_shifts)
    note = (
        "unknown mass shifts are advisory hypotheses and must not be promoted as confirmed identifications"
        if hypotheses
        else "no unknown mass-shift hypotheses were provided"
    )
    return OpenSearchUnknownModificationReport(
        peptide_sequence=normalized,
        hypotheses=hypotheses,
        has_unknown_mass_shift=bool(hypotheses),
        note=note,
    )
