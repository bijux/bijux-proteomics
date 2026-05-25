# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM site-level abundance correction against matched protein changes."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PtmSiteProteinCorrectionStatus(StrEnum):
    """Stable correction outcomes for site-level protein abundance adjustment."""

    HIGH_CONFIDENCE_CORRECTED = "high_confidence_corrected"
    CORRECTED_LOW_LOCALIZATION = "corrected_low_localization"
    MISSING_PROTEIN_BASELINE = "missing_protein_baseline"


class PtmSiteCorrectionCandidate(JsonModel):
    """One site-level differential effect eligible for protein abundance correction."""

    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    protein_id: str = Field(..., min_length=1)
    raw_site_log2fc: float
    low_localization: bool = False


class PtmProteinCorrectionReference(JsonModel):
    """One protein-level differential reference used for PTM site correction."""

    model_config = ConfigDict(extra="forbid")

    protein_id: str = Field(..., min_length=1)
    protein_log2fc: float


class PtmSiteProteinCorrectionEntry(JsonModel):
    """One corrected PTM site differential row against matched protein abundance."""

    model_config = ConfigDict(extra="forbid")

    site_id: str = Field(..., min_length=1)
    raw_site_log2fc: float
    protein_log2fc: float | None = None
    corrected_site_log2fc: float | None = None
    correction_status: PtmSiteProteinCorrectionStatus


def correct_site_by_protein(
    site_matrix: tuple[PtmSiteCorrectionCandidate, ...],
    protein_matrix: tuple[PtmProteinCorrectionReference, ...],
) -> tuple[PtmSiteProteinCorrectionEntry, ...]:
    """Correct PTM site fold changes by matched protein-level abundance shifts."""

    protein_lookup: dict[str, PtmProteinCorrectionReference] = {}
    for entry in protein_matrix:
        if entry.protein_id in protein_lookup:
            raise ValueError("protein abundance correction requires unique protein_id rows")
        protein_lookup[entry.protein_id] = entry

    site_ids: set[str] = set()
    corrected: list[PtmSiteProteinCorrectionEntry] = []
    for candidate in site_matrix:
        if candidate.site_id in site_ids:
            raise ValueError("protein abundance correction requires unique site_id rows")
        site_ids.add(candidate.site_id)
        reference = protein_lookup.get(candidate.protein_id)
        if reference is None:
            corrected.append(
                PtmSiteProteinCorrectionEntry(
                    site_id=candidate.site_id,
                    raw_site_log2fc=candidate.raw_site_log2fc,
                    correction_status=PtmSiteProteinCorrectionStatus.MISSING_PROTEIN_BASELINE,
                )
            )
            continue
        corrected.append(
            PtmSiteProteinCorrectionEntry(
                site_id=candidate.site_id,
                raw_site_log2fc=candidate.raw_site_log2fc,
                protein_log2fc=reference.protein_log2fc,
                corrected_site_log2fc=round(
                    candidate.raw_site_log2fc - reference.protein_log2fc,
                    10,
                ),
                correction_status=(
                    PtmSiteProteinCorrectionStatus.CORRECTED_LOW_LOCALIZATION
                    if candidate.low_localization
                    else PtmSiteProteinCorrectionStatus.HIGH_CONFIDENCE_CORRECTED
                ),
            )
        )
    return tuple(corrected)


def render_site_protein_correction_tsv(
    entries: tuple[PtmSiteProteinCorrectionEntry, ...],
) -> str:
    """Render site-level protein correction rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "site_id",
            "raw_site_log2fc",
            "protein_log2fc",
            "corrected_site_log2fc",
            "correction_status",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.site_id,
                entry.raw_site_log2fc,
                "" if entry.protein_log2fc is None else entry.protein_log2fc,
                (
                    ""
                    if entry.corrected_site_log2fc is None
                    else entry.corrected_site_log2fc
                ),
                entry.correction_status.value,
            )
        )
    return buffer.getvalue()


__all__ = [
    "PtmProteinCorrectionReference",
    "PtmSiteCorrectionCandidate",
    "PtmSiteProteinCorrectionEntry",
    "PtmSiteProteinCorrectionStatus",
    "correct_site_by_protein",
    "render_site_protein_correction_tsv",
]
