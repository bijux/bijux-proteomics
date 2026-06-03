# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Oxidation artifact detection over sample-level peptide evidence."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class PtmOxidationSiteConfidence(StrEnum):
    """Stable confidence outcomes for site-specific oxidation claims."""

    SUPPORTED = "supported"
    CAUTION = "caution"
    DOWNGRADED = "downgraded"


class PtmOxidizedPeptideObservation(JsonModel):
    """One sample-level methionine-bearing peptide observation."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    methionine_count: int = Field(..., ge=1)
    oxidized_methionine_count: int = Field(..., ge=0)
    site_localized: bool = False

    def model_post_init(self, __context: object) -> None:
        if self.oxidized_methionine_count > self.methionine_count:
            raise ValueError(
                "oxidized peptide observations require oxidized_methionine_count <= methionine_count"
            )


class PtmOxidationSampleQcEntry(JsonModel):
    """One QC entry used to temper oxidation artifact interpretation."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    qc_score: float = Field(..., ge=0.0, le=1.0)
    blocked: bool = False


class PtmOxidationArtifactEntry(JsonModel):
    """One sample-level oxidation artifact assessment."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    methionine_oxidation_fraction: float = Field(..., ge=0.0, le=1.0)
    global_oxidation_warning: bool
    site_specific_confidence: PtmOxidationSiteConfidence


def detect_oxidation_artifacts(
    oxidized_peptides: tuple[PtmOxidizedPeptideObservation, ...],
    sample_qc: tuple[PtmOxidationSampleQcEntry, ...],
) -> tuple[PtmOxidationArtifactEntry, ...]:
    """Detect sample-level oxidation burden and downgrade fragile site claims."""

    qc_by_sample: dict[str, PtmOxidationSampleQcEntry] = {}
    for entry in sample_qc:
        if entry.sample_id in qc_by_sample:
            raise ValueError(
                "oxidation artifact detection requires unique sample_qc rows"
            )
        qc_by_sample[entry.sample_id] = entry

    observations_by_sample: dict[str, list[PtmOxidizedPeptideObservation]] = {}
    for oxidized_observation in oxidized_peptides:
        observations_by_sample.setdefault(oxidized_observation.sample_id, []).append(
            oxidized_observation
        )

    detected: list[PtmOxidationArtifactEntry] = []
    for sample_id in sorted(observations_by_sample):
        observations = observations_by_sample[sample_id]
        total_methionines = sum(entry.methionine_count for entry in observations)
        oxidized_methionines = sum(
            entry.oxidized_methionine_count for entry in observations
        )
        oxidation_fraction = oxidized_methionines / total_methionines
        localized_claim_count = sum(
            1
            for entry in observations
            if entry.site_localized and entry.oxidized_methionine_count > 0
        )
        qc_entry = qc_by_sample.get(sample_id)
        detected.append(
            PtmOxidationArtifactEntry(
                sample_id=sample_id,
                methionine_oxidation_fraction=round(oxidation_fraction, 6),
                global_oxidation_warning=oxidation_fraction >= 0.2,
                site_specific_confidence=_site_specific_confidence(
                    oxidation_fraction=oxidation_fraction,
                    localized_claim_count=localized_claim_count,
                    qc_entry=qc_entry,
                ),
            )
        )
    return tuple(detected)


def render_ptm_oxidation_artifact_tsv(
    entries: tuple[PtmOxidationArtifactEntry, ...],
) -> str:
    """Render oxidation artifact rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "sample_id",
            "methionine_oxidation_fraction",
            "global_oxidation_warning",
            "site_specific_confidence",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.sample_id,
                f"{entry.methionine_oxidation_fraction:.6f}",
                str(entry.global_oxidation_warning).lower(),
                entry.site_specific_confidence.value,
            )
        )
    return buffer.getvalue()


def _site_specific_confidence(
    *,
    oxidation_fraction: float,
    localized_claim_count: int,
    qc_entry: PtmOxidationSampleQcEntry | None,
) -> PtmOxidationSiteConfidence:
    if localized_claim_count == 0:
        return PtmOxidationSiteConfidence.DOWNGRADED
    if qc_entry is not None and (qc_entry.blocked or qc_entry.qc_score < 0.5):
        return PtmOxidationSiteConfidence.DOWNGRADED
    if oxidation_fraction >= 0.35:
        return PtmOxidationSiteConfidence.DOWNGRADED

    confidence = (
        PtmOxidationSiteConfidence.SUPPORTED
        if localized_claim_count >= 2
        else PtmOxidationSiteConfidence.CAUTION
    )
    if qc_entry is not None and qc_entry.qc_score < 0.75:
        confidence = PtmOxidationSiteConfidence.CAUTION
    if oxidation_fraction >= 0.2:
        confidence = PtmOxidationSiteConfidence.CAUTION
    return confidence


__all__ = [
    "PtmOxidationArtifactEntry",
    "PtmOxidationSampleQcEntry",
    "PtmOxidationSiteConfidence",
    "PtmOxidizedPeptideObservation",
    "detect_oxidation_artifacts",
    "render_ptm_oxidation_artifact_tsv",
]
