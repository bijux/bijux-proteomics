# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Flagship PTM pressure corpora tied to public localization benchmark packages."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.ptm.benchmarks import (
    PtmAmbiguityPropagationBenchmarkReport,
    PtmFamilyCredibilityTrackReport,
    PtmLabTargetingRubricReport,
    PtmLocalizationConfidenceBenchmarkReport,
    PtmOccupancyStressBenchmarkReport,
    PtmRawSpectrumValidationLaneReport,
)
from bijux_proteomics_foundation import JsonModel


class PtmPressureCorpusReport(JsonModel):
    """Flagship PTM pressure corpus over localization, ambiguity, and lab consequence."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    benchmark_package_id: str = Field(..., min_length=1)
    supporting_identity_paths: tuple[str, ...] = Field(default_factory=tuple)
    localization_confidence: PtmLocalizationConfidenceBenchmarkReport
    ambiguity_propagation: PtmAmbiguityPropagationBenchmarkReport
    occupancy_stress: PtmOccupancyStressBenchmarkReport
    raw_spectrum_validation: PtmRawSpectrumValidationLaneReport
    family_credibility: PtmFamilyCredibilityTrackReport
    lab_targeting: PtmLabTargetingRubricReport
    ready_for_broad_ptm_claim: bool
    note: str = Field(..., min_length=1)


def build_ptm_pressure_corpus_report(
    *,
    benchmark_package_id: str,
    supporting_identity_paths: tuple[str, ...],
    localization_confidence: PtmLocalizationConfidenceBenchmarkReport,
    ambiguity_propagation: PtmAmbiguityPropagationBenchmarkReport,
    occupancy_stress: PtmOccupancyStressBenchmarkReport,
    raw_spectrum_validation: PtmRawSpectrumValidationLaneReport,
    family_credibility: PtmFamilyCredibilityTrackReport,
    lab_targeting: PtmLabTargetingRubricReport,
) -> PtmPressureCorpusReport:
    """Build the flagship PTM pressure corpus."""

    ready = (
        localization_confidence.ready_for_site_level_claims
        and raw_spectrum_validation.ready_for_rescoring_follow_up
        and ambiguity_propagation.interpretive_only_count == 0
        and occupancy_stress.stable_under_replicate_variability
        and not family_credibility.interpretive_only_families
        and not family_credibility.refused_families
        and lab_targeting.interpretive_only_count == 0
    )
    return PtmPressureCorpusReport(
        corpus_id="flagship_ptm_pressure:localization_bundle",
        benchmark_package_id=benchmark_package_id,
        supporting_identity_paths=tuple(sorted(supporting_identity_paths)),
        localization_confidence=localization_confidence,
        ambiguity_propagation=ambiguity_propagation,
        occupancy_stress=occupancy_stress,
        raw_spectrum_validation=raw_spectrum_validation,
        family_credibility=family_credibility,
        lab_targeting=lab_targeting,
        ready_for_broad_ptm_claim=ready,
        note=(
            "The flagship PTM pressure corpus keeps localization, ambiguity, occupancy, raw-spectrum validation, and lab-targeting consequence together before broader PTM claims travel."
        ),
    )


__all__ = [
    "PtmPressureCorpusReport",
    "build_ptm_pressure_corpus_report",
]
