# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""DIA and targeted pressure corpora grounded in reviewable import surfaces."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.dia.benchmarks import (
    DiaWorkflowScientificSupportReport,
    TargetedRawToReviewedBundleReport,
    TargetedWorkflowBenchmarkReport,
)
from bijux_proteomics_foundation import JsonModel


class DiaPressureCorpusReport(JsonModel):
    """DIA pressure corpus over library dependence, missing peptides, and interpretation."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    benchmark_surface_id: str = Field(..., min_length=1)
    supporting_identity_paths: tuple[str, ...] = Field(default_factory=tuple)
    support_report: DiaWorkflowScientificSupportReport
    library_conditioned_partial: bool
    biological_interpretation_blocked: bool
    note: str = Field(..., min_length=1)


class TargetedPressureCorpusReport(JsonModel):
    """Targeted pressure corpus over calibration, interference, and reviewed handoff honesty."""

    model_config = ConfigDict(extra="forbid")

    corpus_id: str = Field(..., min_length=1)
    benchmark_surface_id: str = Field(..., min_length=1)
    supporting_identity_paths: tuple[str, ...] = Field(default_factory=tuple)
    workflow_benchmark: TargetedWorkflowBenchmarkReport
    raw_to_reviewed_bundle: TargetedRawToReviewedBundleReport
    transition_handoff_blocked: bool
    note: str = Field(..., min_length=1)


def build_dia_pressure_corpus_report(
    *,
    benchmark_surface_id: str,
    supporting_identity_paths: tuple[str, ...],
    support_report: DiaWorkflowScientificSupportReport,
) -> DiaPressureCorpusReport:
    """Build the DIA pressure corpus from a tiered support report."""

    library_conditioned = next(
        entry
        for entry in support_report.entries
        if entry.surface == "library_conditioned_import"
    )
    return DiaPressureCorpusReport(
        corpus_id="flagship_dia_pressure:library_conditioned_import",
        benchmark_surface_id=benchmark_surface_id,
        supporting_identity_paths=tuple(sorted(supporting_identity_paths)),
        support_report=support_report,
        library_conditioned_partial=library_conditioned.support_tier.value == "partial",
        biological_interpretation_blocked=not support_report.ready_for_biological_interpretation,
        note=(
            "The DIA pressure corpus keeps library conditioning, missing expected peptides, and blocked biological interpretation visible as one import-conditioned scientific surface."
        ),
    )


def build_targeted_pressure_corpus_report(
    *,
    benchmark_surface_id: str,
    supporting_identity_paths: tuple[str, ...],
    workflow_benchmark: TargetedWorkflowBenchmarkReport,
    raw_to_reviewed_bundle: TargetedRawToReviewedBundleReport,
) -> TargetedPressureCorpusReport:
    """Build the targeted pressure corpus from calibration and handoff evidence."""

    return TargetedPressureCorpusReport(
        corpus_id="flagship_targeted_pressure:reviewed_transition_bundle",
        benchmark_surface_id=benchmark_surface_id,
        supporting_identity_paths=tuple(sorted(supporting_identity_paths)),
        workflow_benchmark=workflow_benchmark,
        raw_to_reviewed_bundle=raw_to_reviewed_bundle,
        transition_handoff_blocked=not raw_to_reviewed_bundle.ready_for_reviewed_handoff,
        note=(
            "The targeted pressure corpus keeps calibration failure, interference, QC, handoff honesty, and outcome reconciliation together before any execution-ready transition claim is promoted."
        ),
    )


__all__ = [
    "DiaPressureCorpusReport",
    "TargetedPressureCorpusReport",
    "build_dia_pressure_corpus_report",
    "build_targeted_pressure_corpus_report",
]
