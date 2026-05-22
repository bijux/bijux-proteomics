# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned assay-QC surfaces over imported targeted observations."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.targeted.result_import import (
    TargetedResultImportReport,
    build_skyline_result_import_report,
    build_transition_table_result_import_report,
)
from bijux_proteomics_foundation import JsonModel


class TargetedTransitionConsistencyEntry(JsonModel):
    """One sample-level transition consistency record for a targeted precursor."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    detected_transition_count: int = Field(..., ge=0)
    expected_transition_count: int = Field(..., ge=0)
    consistency_fraction: float = Field(..., ge=0.0, le=1.0)


class TargetedFragmentRatioEntry(JsonModel):
    """One transition share inside a targeted precursor for one sample."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    total_target_intensity: float = Field(..., ge=0.0)
    relative_share: float = Field(..., ge=0.0, le=1.0)


class TargetedAssayQcSummary(JsonModel):
    """Compact summary over one targeted assay QC report."""

    model_config = ConfigDict(extra="forbid")

    target_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    transition_consistency_entry_count: int = Field(..., ge=0)
    fragment_ratio_entry_count: int = Field(..., ge=0)


class TargetedAssayQcReport(JsonModel):
    """Targeted assay QC report over transition consistency and fragment ratios."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    transition_consistency: tuple[TargetedTransitionConsistencyEntry, ...] = Field(
        default_factory=tuple
    )
    fragment_ratios: tuple[TargetedFragmentRatioEntry, ...] = Field(default_factory=tuple)
    summary: TargetedAssayQcSummary
    note: str = Field(..., min_length=1)


def build_targeted_assay_qc_report(
    import_report: TargetedResultImportReport,
) -> TargetedAssayQcReport:
    """Build targeted assay QC ledgers over one imported targeted result bundle."""

    target_ids = sorted({item.precursor_id for item in import_report.observations})
    sample_ids = sorted({item.sample_id for item in import_report.observations})
    target_to_transitions = {
        target_id: sorted(
            {
                item.transition_id
                for item in import_report.observations
                if item.precursor_id == target_id
            }
        )
        for target_id in target_ids
    }

    consistency_entries: list[TargetedTransitionConsistencyEntry] = []
    ratio_entries: list[TargetedFragmentRatioEntry] = []
    for target_id in target_ids:
        expected_transition_ids = target_to_transitions[target_id]
        expected_count = len(expected_transition_ids)
        for sample_id in sample_ids:
            sample_observations = [
                item
                for item in import_report.observations
                if item.precursor_id == target_id and item.sample_id == sample_id
            ]
            detected_count = len({item.transition_id for item in sample_observations})
            consistency_entries.append(
                TargetedTransitionConsistencyEntry(
                    target_id=target_id,
                    sample_id=sample_id,
                    detected_transition_count=detected_count,
                    expected_transition_count=expected_count,
                    consistency_fraction=(
                        detected_count / expected_count if expected_count else 0.0
                    ),
                )
            )
            total_target_intensity = sum(item.intensity for item in sample_observations)
            for item in sorted(sample_observations, key=lambda record: record.transition_id):
                ratio_entries.append(
                    TargetedFragmentRatioEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        transition_id=item.transition_id,
                        intensity=item.intensity,
                        total_target_intensity=total_target_intensity,
                        relative_share=(
                            item.intensity / total_target_intensity
                            if total_target_intensity > 0.0
                            else 0.0
                        ),
                    )
                )

    return TargetedAssayQcReport(
        source_name=import_report.source_name,
        transition_consistency=tuple(consistency_entries),
        fragment_ratios=tuple(ratio_entries),
        summary=TargetedAssayQcSummary(
            target_count=len(target_ids),
            sample_count=len(sample_ids),
            transition_consistency_entry_count=len(consistency_entries),
            fragment_ratio_entry_count=len(ratio_entries),
        ),
        note=(
            "targeted assay qc keeps transition consistency and fragment-ion ratio evidence explicit before any sample or target is trusted"
        ),
    )


def build_skyline_targeted_assay_qc_report(path: Path) -> TargetedAssayQcReport:
    """Build targeted assay QC directly from one Skyline-style export."""

    return build_targeted_assay_qc_report(build_skyline_result_import_report(path))


def build_transition_table_targeted_assay_qc_report(path: Path) -> TargetedAssayQcReport:
    """Build targeted assay QC directly from one exported transition table."""

    return build_targeted_assay_qc_report(build_transition_table_result_import_report(path))
