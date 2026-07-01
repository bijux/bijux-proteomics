# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Entity-level missing-data mechanism heuristics."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.contracts.missingness import (
    MissingDataMechanism,
    MissingDataMechanismEntry,
    MissingDataMechanismReport,
)
from bijux_proteomics.quantification.missingness.policy import (
    is_missing_burden,
)


def build_missing_data_mechanism_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> MissingDataMechanismReport:
    """Classify entity missingness with explicit condition and randomness labels."""
    lookup = _matrix_value_index(table)
    condition_by_sample = _condition_lookup(design_entries)
    batch_by_sample = {
        entry.sample_id: entry.batch for entry in design_entries if entry.batch
    }
    channel_by_sample = {
        entry.sample_id: (entry.multiplex_group, entry.multiplex_channel)
        for entry in design_entries
        if entry.multiplex_group and entry.multiplex_channel
    }
    sample_ids_by_condition_lists: dict[str, list[str]] = {}
    for entry in design_entries:
        sample_ids_by_condition_lists.setdefault(entry.condition, []).append(
            entry.sample_id
        )
    sample_ids_by_condition = {
        condition: tuple(sample_ids)
        for condition, sample_ids in sample_ids_by_condition_lists.items()
    }
    entries: list[MissingDataMechanismEntry] = []
    summary_counts = dict.fromkeys(MissingDataMechanism, 0)
    for entity_id in table.entity_ids:
        observed_conditions: set[str] = set()
        missing_samples: list[str] = []
        observed_samples: list[str] = []
        missing_conditions: set[str] = set()
        fully_missing_conditions: set[str] = set()
        for sample_id in table.sample_ids:
            cell = lookup[(entity_id, sample_id)]
            condition = condition_by_sample.get(sample_id, "unknown")
            if cell.missing_value_kind in (
                MissingValueKind.OBSERVED,
                MissingValueKind.ZERO,
                MissingValueKind.IMPUTED,
            ):
                observed_conditions.add(condition)
                observed_samples.append(sample_id)
                continue
            missing_samples.append(sample_id)
            missing_conditions.add(condition)
        for condition, sample_ids in sample_ids_by_condition.items():
            condition_kinds = {
                lookup[(entity_id, sample_id)].missing_value_kind
                for sample_id in sample_ids
            }
            if condition_kinds and all(
                is_missing_burden(kind) for kind in condition_kinds
            ):
                fully_missing_conditions.add(condition)

        missing_batches = {
            batch_by_sample.get(sample_id)
            for sample_id in missing_samples
            if batch_by_sample.get(sample_id)
        }
        missing_channels = {
            channel_by_sample.get(sample_id)
            for sample_id in missing_samples
            if channel_by_sample.get(sample_id)
        }

        mechanism = MissingDataMechanism.MIXED_OR_UNRESOLVED
        note = (
            "missingness mixes structured and unstructured patterns or lacks enough "
            "metadata support"
        )
        if not missing_samples:
            mechanism = MissingDataMechanism.NO_MISSING_VALUES
            note = "entity is observed in every sample under the current table snapshot"
        elif fully_missing_conditions and observed_conditions:
            mechanism = MissingDataMechanism.CONDITION_SPECIFIC_ABSENCE
            note = (
                "one or more conditions are fully absent while another condition retains "
                "observed signal"
            )
        elif len(missing_samples) == 1 and len(observed_samples) >= 2:
            mechanism = MissingDataMechanism.LIKELY_TECHNICAL_FAILURE
            note = "one isolated missing sample breaks an otherwise observed pattern"
        elif len(missing_conditions) > 1:
            mechanism = MissingDataMechanism.MISSING_COMPLETELY_AT_RANDOM
            note = (
                "missing values are distributed across conditions without a condition-wide "
                "absence pattern"
            )
        elif len(missing_batches) == 1 or (
            len(missing_channels) == 1 and len(missing_samples) >= 2
        ):
            mechanism = MissingDataMechanism.BATCH_OR_CHANNEL_ISSUE
            note = "missingness aligns with one batch or one multiplex channel grouping"

        summary_counts[mechanism] += 1
        entries.append(
            MissingDataMechanismEntry(
                entity_id=entity_id,
                mechanism=mechanism,
                observed_conditions=tuple(sorted(observed_conditions)),
                missing_conditions=tuple(
                    sorted(fully_missing_conditions or missing_conditions)
                ),
                missing_samples=tuple(sorted(missing_samples)),
                note=note,
            )
        )
    return MissingDataMechanismReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
        summary_counts=summary_counts,
    )
