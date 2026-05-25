# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""False-localization detection over competing PTM site candidates."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import ModificationRegistryDocument
from bijux_proteomics.io.spectra import SpectrumPeak
from bijux_proteomics.ptm.contracts import PtmEvidenceRecord
from bijux_proteomics.ptm.localization.fragment_scoring import score_ptm_fragments
from bijux_proteomics.ptm.localization.localization_scoring import (
    PtmLocalizationScoringEntry,
    build_ptm_localization_scoring_report,
    normalize_ptm_localization_probability,
)
from bijux_proteomics_foundation import JsonModel


class PtmLocalizationRisk(StrEnum):
    """Risk class for one localized PTM candidate against a competitor."""

    SUPPORTED = "supported"
    COMPETING_SUPPORT = "competing_support"
    LIKELY_FALSE_LOCALIZATION = "likely_false_localization"
    AMBIGUOUS = "ambiguous"


class PtmFalseLocalizationEntry(JsonModel):
    """One candidate-versus-competitor false-localization assessment row."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    candidate_site: str = Field(..., min_length=1)
    site_probability: float = Field(..., ge=0.0, le=1.0)
    site_determining_ions: tuple[str, ...] = Field(default_factory=tuple)
    competing_site: str = Field(..., min_length=1)
    localization_risk: PtmLocalizationRisk


def detect_false_localization(
    candidates: tuple[PtmEvidenceRecord, ...],
    observed_peaks: tuple[SpectrumPeak, ...],
    *,
    tolerance: float = 0.01,
    registry: ModificationRegistryDocument | None = None,
) -> tuple[PtmFalseLocalizationEntry, ...]:
    """Compare competing localized candidates against one observed spectrum."""

    if tolerance <= 0.0:
        raise ValueError("tolerance must be greater than zero")
    if not candidates:
        return ()
    spectrum_ids = {candidate.spectrum_id for candidate in candidates}
    if len(spectrum_ids) != 1:
        raise ValueError("false-localization detection requires one shared spectrum_id")

    scoring_report = build_ptm_localization_scoring_report(candidates, registry=registry)
    probability_by_key = {
        (candidate.spectrum_id, candidate.localized_peptide): candidate.localization_probability
        for candidate in candidates
    }
    support_by_site: dict[str, tuple[float, tuple[str, ...], PtmLocalizationScoringEntry]] = {}
    for entry in scoring_report.entries:
        matched_rows = score_ptm_fragments(
            entry.localized_peptide,
            observed_peaks,
            tolerance,
            registry=registry,
        )
        supported_site_determining_ions = tuple(
            sorted(row.ion_id for row in matched_rows if row.site_determining)
        )
        localization_probability, _ = normalize_ptm_localization_probability(
            localization_score=entry.localization_score,
            reported_probability=probability_by_key.get(
                (entry.spectrum_id, entry.localized_peptide)
            ),
            ambiguous=len(entry.candidate_site_indices) > 1,
            site_determining_ion_count=len(entry.site_determining_ions),
            supported_site_determining_ion_count=len(supported_site_determining_ions),
        )
        support_by_site[_site_label(entry)] = (
            localization_probability,
            supported_site_determining_ions,
            entry,
        )

    rows: list[PtmFalseLocalizationEntry] = []
    ordered_sites = tuple(sorted(support_by_site))
    for candidate_site in ordered_sites:
        candidate_probability, candidate_ions, candidate_entry = support_by_site[candidate_site]
        for competing_site in ordered_sites:
            if candidate_site == competing_site:
                continue
            _, competing_ions, competing_entry = support_by_site[competing_site]
            if not _sites_are_competing(candidate_entry, competing_entry):
                continue
            rows.append(
                PtmFalseLocalizationEntry(
                    spectrum_id=candidate_entry.spectrum_id,
                    candidate_site=candidate_site,
                    site_probability=candidate_probability,
                    site_determining_ions=candidate_ions,
                    competing_site=competing_site,
                    localization_risk=_compare_candidate_support(
                        len(candidate_ions),
                        len(competing_ions),
                    ),
                )
            )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.spectrum_id,
                row.candidate_site,
                row.competing_site,
            ),
        )
    )


def render_false_localization_tsv(
    rows: tuple[PtmFalseLocalizationEntry, ...],
) -> str:
    """Render false-localization assessments as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "spectrum_id",
            "candidate_site",
            "site_probability",
            "site_determining_ions",
            "competing_site",
            "localization_risk",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.spectrum_id,
                row.candidate_site,
                row.site_probability,
                ";".join(row.site_determining_ions),
                row.competing_site,
                row.localization_risk.value,
            )
        )
    return buffer.getvalue()


def _site_label(entry: PtmLocalizationScoringEntry) -> str:
    return f"{entry.modification_name}@{entry.peptide_site_index}"


def _sites_are_competing(
    left: PtmLocalizationScoringEntry,
    right: PtmLocalizationScoringEntry,
) -> bool:
    return (
        left.spectrum_id == right.spectrum_id
        and left.modification_name == right.modification_name
        and bool(set(left.candidate_site_indices) & set(right.candidate_site_indices))
    )


def _compare_candidate_support(
    candidate_support_count: int,
    competing_support_count: int,
) -> PtmLocalizationRisk:
    if candidate_support_count == competing_support_count:
        return PtmLocalizationRisk.AMBIGUOUS
    if candidate_support_count == 0:
        return PtmLocalizationRisk.LIKELY_FALSE_LOCALIZATION
    if candidate_support_count < competing_support_count:
        return PtmLocalizationRisk.COMPETING_SUPPORT
    return PtmLocalizationRisk.SUPPORTED
