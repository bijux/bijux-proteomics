# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Isotope-envelope and adduct annotation contracts (advisory only)."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.contracts.mass_projection import (
    approximate_peptide_isotope_envelope,
)
from bijux_proteomics.chemistry.contracts.models import (
    IsotopeEnvelopeStatus,
)
from bijux_proteomics_foundation import JsonModel


class AdductHypothesis(JsonModel):
    """Adduct hypothesis for one precursor interpretation."""

    model_config = ConfigDict(extra="forbid")

    adduct_name: str = Field(..., min_length=1)
    adduct_mass_delta: float
    charge: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    adjusted_mz: float = Field(..., gt=0.0)
    advisory_only: bool = True


class IsotopeAdductAnnotationReport(JsonModel):
    """Combined isotope/adduct advisory annotation report."""

    model_config = ConfigDict(extra="forbid")

    sequence: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    envelope_status: IsotopeEnvelopeStatus
    adduct_hypotheses: tuple[AdductHypothesis, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


_ADDUCT_DELTAS = {
    "H+": 1.007276466812,
    "Na+": 22.989218,
    "K+": 38.963158,
    "NH4+": 18.033823,
}


def annotate_isotope_and_adduct_hypotheses(
    *,
    sequence: str,
    charge: int,
    adducts: Sequence[str] = ("H+", "Na+", "K+"),
) -> IsotopeAdductAnnotationReport:
    """Annotate isotope/adduct hypotheses without promoting them as IDs."""
    envelope = approximate_peptide_isotope_envelope(
        sequence,
        charge=charge,
        peak_count=4,
    )
    precursor_mz = envelope.peaks[0].mz if envelope.peaks else 0.0
    hypotheses: list[AdductHypothesis] = []
    for adduct in adducts:
        if adduct not in _ADDUCT_DELTAS:
            continue
        delta = _ADDUCT_DELTAS[adduct]
        hypotheses.append(
            AdductHypothesis(
                adduct_name=adduct,
                adduct_mass_delta=delta,
                charge=charge,
                precursor_mz=precursor_mz,
                adjusted_mz=precursor_mz + (delta / charge),
            )
        )
    return IsotopeAdductAnnotationReport(
        sequence=sequence.strip().upper(),
        charge=charge,
        envelope_status=envelope.status,
        adduct_hypotheses=tuple(hypotheses),
        note="isotope and adduct annotations are advisory precursor evidence, not identifications",
    )
