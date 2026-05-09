# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cross-family atlas of public scientific failure and refusal boundaries."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.benchmarks.dia_targeted_pressure import (
    DiaPressureCorpusReport,
    TargetedPressureCorpusReport,
)
from bijux_proteomics.benchmarks.flagship_public_packages import (
    FlagshipPublicBenchmarkPackage,
)
from bijux_proteomics.benchmarks.identification_pressure import (
    CalibrationPressureCorpusReport,
    ProteinInferencePressureCorpusReport,
)
from bijux_proteomics.benchmarks.ptm_pressure import PtmPressureCorpusReport
from bijux_proteomics.benchmarks.quantification_pressure import (
    QuantificationPressureCorpusReport,
)
from bijux_proteomics_foundation import JsonModel


class ScientificFailureSeverity(StrEnum):
    """Severity of a public failure or refusal boundary."""

    MODERATE = "moderate"
    HIGH = "high"


class ScientificFailureAtlasEntry(JsonModel):
    """One workflow-family failure surface in the flagship public atlas."""

    model_config = ConfigDict(extra="forbid")

    workflow_family: str = Field(..., min_length=1)
    benchmark_surface_id: str = Field(..., min_length=1)
    severity: ScientificFailureSeverity
    blocking_findings: tuple[str, ...] = Field(default_factory=tuple)
    blocked_claims: tuple[str, ...] = Field(default_factory=tuple)
    supporting_identity_paths: tuple[str, ...] = Field(default_factory=tuple)


class ScientificFailureAtlasReport(JsonModel):
    """Atlas of strongest public scientific failure boundaries across workflow families."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ScientificFailureAtlasEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def build_scientific_failure_atlas_report(
    *,
    dda_package: FlagshipPublicBenchmarkPackage,
    lfq_package: FlagshipPublicBenchmarkPackage,
    ptm_package: FlagshipPublicBenchmarkPackage,
    calibration_pressure: CalibrationPressureCorpusReport,
    protein_inference_pressure: ProteinInferencePressureCorpusReport,
    quantification_pressure: QuantificationPressureCorpusReport,
    ptm_pressure: PtmPressureCorpusReport,
    dia_pressure: DiaPressureCorpusReport,
    targeted_pressure: TargetedPressureCorpusReport,
) -> ScientificFailureAtlasReport:
    """Build the cross-family atlas of strongest public scientific failure boundaries."""

    entries = (
        ScientificFailureAtlasEntry(
            workflow_family="identification",
            benchmark_surface_id=dda_package.package_id,
            severity=(
                ScientificFailureSeverity.HIGH
                if not protein_inference_pressure.ready_for_broad_identification_claim
                else ScientificFailureSeverity.MODERATE
            ),
            blocking_findings=tuple(
                filter(
                    None,
                    (
                        "calibration follow-up still required"
                        if calibration_pressure.requires_follow_up
                        else None,
                        "protein-inference trust rubric still refuses broad promotion"
                        if not protein_inference_pressure.claim_review.accepted
                        else None,
                        "contaminant promotion remains unresolved"
                        if protein_inference_pressure.unresolved_contaminant_promotion
                        else None,
                    ),
                )
            ),
            blocked_claims=(
                "broad DDA identification parity",
                "unqualified protein-inference promotion",
            ),
            supporting_identity_paths=tuple(
                sorted(
                    {
                        *calibration_pressure.imported_result_identity_paths,
                        *protein_inference_pressure.supporting_identity_paths,
                    }
                )
            ),
        ),
        ScientificFailureAtlasEntry(
            workflow_family="quantification",
            benchmark_surface_id=lfq_package.package_id,
            severity=(
                ScientificFailureSeverity.HIGH
                if not quantification_pressure.ready_for_broad_quant_claim
                else ScientificFailureSeverity.MODERATE
            ),
            blocking_findings=tuple(
                filter(
                    None,
                    (
                        "missingness still blocks broad quant claims"
                        if quantification_pressure.missingness_blocks_broad_claims
                        else None,
                        "normalization policy changes the primary narrative"
                        if quantification_pressure.normalization_changes_primary_narrative
                        else None,
                        "effect-size ranking remains unstable"
                        if quantification_pressure.unstable_effect_size_narrative
                        else None,
                    ),
                )
            ),
            blocked_claims=(
                "broad LFQ differential interpretation",
                "decision-grade abundance biology",
            ),
            supporting_identity_paths=quantification_pressure.supporting_identity_paths,
        ),
        ScientificFailureAtlasEntry(
            workflow_family="ptm",
            benchmark_surface_id=ptm_package.package_id,
            severity=(
                ScientificFailureSeverity.HIGH
                if not ptm_pressure.ready_for_broad_ptm_claim
                else ScientificFailureSeverity.MODERATE
            ),
            blocking_findings=tuple(
                filter(
                    None,
                    (
                        "site ambiguity still propagates into PTM quant"
                        if ptm_pressure.ambiguity_propagation.interpretive_only_count
                        > 0
                        else None,
                        "raw-spectrum validation still leaves unsupported spectra"
                        if not ptm_pressure.raw_spectrum_validation.ready_for_rescoring_follow_up
                        else None,
                        "family credibility still includes interpretive-only or refused PTM lanes"
                        if ptm_pressure.family_credibility.interpretive_only_families
                        or ptm_pressure.family_credibility.refused_families
                        else None,
                    ),
                )
            ),
            blocked_claims=(
                "broad PTM site certainty",
                "broad PTM lab-targeting readiness",
            ),
            supporting_identity_paths=ptm_pressure.supporting_identity_paths,
        ),
        ScientificFailureAtlasEntry(
            workflow_family="dia",
            benchmark_surface_id=dia_pressure.benchmark_surface_id,
            severity=(
                ScientificFailureSeverity.HIGH
                if dia_pressure.biological_interpretation_blocked
                else ScientificFailureSeverity.MODERATE
            ),
            blocking_findings=tuple(
                filter(
                    None,
                    (
                        "library-conditioned import remains only partial"
                        if dia_pressure.library_conditioned_partial
                        else None,
                        "biological interpretation remains blocked by missing expected peptides or incomplete coverage"
                        if dia_pressure.biological_interpretation_blocked
                        else None,
                    ),
                )
            ),
            blocked_claims=(
                "broad DIA biological interpretation",
                "library-independent DIA confidence",
            ),
            supporting_identity_paths=dia_pressure.supporting_identity_paths,
        ),
        ScientificFailureAtlasEntry(
            workflow_family="targeted",
            benchmark_surface_id=targeted_pressure.benchmark_surface_id,
            severity=(
                ScientificFailureSeverity.HIGH
                if targeted_pressure.transition_handoff_blocked
                else ScientificFailureSeverity.MODERATE
            ),
            blocking_findings=tuple(
                filter(
                    None,
                    (
                        "calibration, pairing, or interference still block transition handoff"
                        if not targeted_pressure.workflow_benchmark.ready_for_transition_handoff
                        else None,
                        "reviewed handoff still contains inflated claims or unreconciled failures"
                        if targeted_pressure.transition_handoff_blocked
                        else None,
                    ),
                )
            ),
            blocked_claims=(
                "execution-ready targeted transition handoff",
                "broad targeted follow-up promotion",
            ),
            supporting_identity_paths=targeted_pressure.supporting_identity_paths,
        ),
    )
    return ScientificFailureAtlasReport(
        entries=entries,
        note=(
            "The scientific failure atlas turns flagship public package weaknesses into one cross-family refusal surface so blocked claims are visible without reading each subsystem in isolation."
        ),
    )


__all__ = [
    "ScientificFailureAtlasEntry",
    "ScientificFailureAtlasReport",
    "ScientificFailureSeverity",
    "build_scientific_failure_atlas_report",
]
