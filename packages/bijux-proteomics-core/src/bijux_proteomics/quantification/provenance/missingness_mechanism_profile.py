# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Missingness mechanism classification for quantification provenance review."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import LabelFreeQuantTable
from bijux_proteomics_foundation import JsonModel


class MissingnessMechanismKind(StrEnum):
    """Missingness classes required for quantification decision briefs."""

    TECHNICAL_FAILURE = "technical_failure"
    SPARSE_BIOLOGY_CANDIDATE = "sparse_biology_candidate"
    BATCH_OR_CHANNEL_ISSUE = "batch_or_channel_issue"
    MISSING_COMPLETELY_AT_RANDOM = "missing_completely_at_random"
    UNKNOWN = "unknown"


class MissingnessMechanismProfileEntry(JsonModel):
    """Classification entry for one quantified entity's missingness pattern."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    mechanism: MissingnessMechanismKind
    observed_samples: tuple[str, ...] = Field(default_factory=tuple)
    missing_samples: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class MissingnessMechanismProfileReport(JsonModel):
    """Missingness mechanism profile across entities with summary counts."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[MissingnessMechanismProfileEntry, ...] = Field(default_factory=tuple)
    summary_counts: dict[MissingnessMechanismKind, int] = Field(default_factory=dict)


def build_missingness_mechanism_profile_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> MissingnessMechanismProfileReport:
    """Classify entity-level missingness into review-oriented mechanism categories."""

    lookup = {(value.entity_id, value.sample_id): value for value in table.values}
    condition_by_sample = {entry.sample_id: entry.condition for entry in design_entries}
    batch_by_sample = {
        entry.sample_id: entry.batch for entry in design_entries if entry.batch
    }
    channel_by_sample = {
        entry.sample_id: (entry.multiplex_group, entry.multiplex_channel)
        for entry in design_entries
        if entry.multiplex_group and entry.multiplex_channel
    }
    entries: list[MissingnessMechanismProfileEntry] = []
    summary = dict.fromkeys(MissingnessMechanismKind, 0)
    for entity_id in table.entity_ids:
        observed: list[str] = []
        missing: list[str] = []
        for sample_id in table.sample_ids:
            cell = lookup[(entity_id, sample_id)]
            if cell.abundance is None:
                missing.append(sample_id)
            else:
                observed.append(sample_id)
        if not missing:
            mechanism = MissingnessMechanismKind.UNKNOWN
            note = "entity has no missing values under the current table snapshot"
        else:
            observed_conditions = {
                condition_by_sample.get(sample_id, "unknown") for sample_id in observed
            }
            missing_conditions = {
                condition_by_sample.get(sample_id, "unknown") for sample_id in missing
            }
            missing_batches = {
                batch_by_sample.get(sample_id)
                for sample_id in missing
                if batch_by_sample.get(sample_id)
            }
            missing_channels = {
                channel_by_sample.get(sample_id)
                for sample_id in missing
                if channel_by_sample.get(sample_id)
            }
            if (
                len(observed_conditions) == 1
                and len(missing_conditions) >= 1
                and not missing_conditions.issubset(observed_conditions)
            ):
                mechanism = MissingnessMechanismKind.SPARSE_BIOLOGY_CANDIDATE
                note = (
                    "signal appears condition-confined while other conditions remain "
                    "missing"
                )
            elif len(missing) == 1:
                mechanism = MissingnessMechanismKind.TECHNICAL_FAILURE
                note = "single isolated missing value suggests localized technical loss"
            elif len(missing_batches) == 1 or (
                len(missing_channels) == 1 and len(missing) >= 2
            ):
                mechanism = MissingnessMechanismKind.BATCH_OR_CHANNEL_ISSUE
                note = "missingness aligns with one batch or one multiplex channel grouping"
            elif len(missing_conditions) > 1:
                mechanism = MissingnessMechanismKind.MISSING_COMPLETELY_AT_RANDOM
                note = (
                    "missing values are distributed across conditions without a "
                    "dominant structured pattern"
                )
            else:
                mechanism = MissingnessMechanismKind.UNKNOWN
                note = (
                    "missingness pattern is unresolved under current metadata context"
                )
        summary[mechanism] += 1
        entries.append(
            MissingnessMechanismProfileEntry(
                entity_id=entity_id,
                mechanism=mechanism,
                observed_samples=tuple(sorted(observed)),
                missing_samples=tuple(sorted(missing)),
                note=note,
            )
        )
    return MissingnessMechanismProfileReport(
        entries=tuple(entries),
        summary_counts=summary,
    )
