# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned missingness analysis for quantitative proteomics tables."""

from __future__ import annotations

import csv
from io import StringIO
from bijux_proteomics.domain.records import QuantMatrix as CanonicalQuantMatrix
from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.contracts.matrix_building import (
    _condition_lookup,
    _matrix_value_index,
    coerce_label_free_quant_table,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.contracts.missingness import (
    MissingDataMechanism,
    MissingDataMechanismEntry,
    MissingDataMechanismReport,
    MissingnessClassifierReport,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
)
from bijux_proteomics.quantification.missingness.models import (
    MissingnessClassificationEntry,
    MissingnessClassificationReport,
    MissingnessLabel,
)
from bijux_proteomics.quantification.missingness.intensity_dependence import (
    build_missingness_intensity_dependence_report,
    low_intensity_cutoff as _low_intensity_cutoff,
)
from bijux_proteomics.quantification.missingness.policy import (
    is_missing_burden as _is_missing_burden,
)
from bijux_proteomics.quantification.missingness.summaries import (
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    summarize_missing_values,
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
                _is_missing_burden(kind) for kind in condition_kinds
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


def build_missingness_classifier_report(
    table: LabelFreeQuantTable,
    *,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    policy: MissingValueSummaryPolicy | None = None,
    bin_count: int = 4,
) -> MissingnessClassifierReport:
    """Bundle owned missingness tables with explicit mechanism labels."""
    return MissingnessClassifierReport(
        sample_summary=summarize_missing_values(table, policy=policy),
        entity_summary=build_missingness_entity_summary_report(table, policy=policy),
        condition_summary=build_missingness_condition_summary_report(
            table,
            design_entries=design_entries,
            policy=policy,
        ),
        intensity_dependence=build_missingness_intensity_dependence_report(
            table,
            bin_count=bin_count,
            policy=policy,
        ),
        mechanism_report=build_missing_data_mechanism_report(
            table,
            design_entries,
        ),
    )


def classify_missingness(
    matrix: LabelFreeQuantTable | CanonicalQuantMatrix,
    design: tuple[ExperimentalDesignEntry, ...],
) -> MissingnessClassificationReport:
    """Classify entity-level missingness into five downstream statistical labels."""

    table = coerce_label_free_quant_table(matrix)
    if not design:
        raise ValueError("design must not be empty")

    sample_summary = summarize_missing_values(table)
    condition_summary = build_missingness_condition_summary_report(
        table,
        design_entries=design,
    )
    intensity_dependence = build_missingness_intensity_dependence_report(table)
    condition_by_sample = _condition_lookup(design)
    lookup = _matrix_value_index(table)

    failed_sample_ids = _failed_sample_ids(sample_summary)
    intensity_lookup = {
        point.entity_id: point.mean_log2_observed_abundance
        for point in intensity_dependence.plot_points
    }
    condition_specific_entity_ids = {
        entity_id
        for entry in condition_summary.entries
        for entity_id in entry.condition_specific_absence_entity_ids
    }
    low_intensity_cutoff = _low_intensity_cutoff(intensity_dependence)

    entries: list[MissingnessClassificationEntry] = []
    for entity_id in table.entity_ids:
        missing_samples = [
            sample_id
            for sample_id in table.sample_ids
            if lookup[(entity_id, sample_id)].missing_value_kind
            in (MissingValueKind.NOT_OBSERVED, MissingValueKind.FILTERED)
        ]
        observed_samples = [
            sample_id
            for sample_id in table.sample_ids
            if lookup[(entity_id, sample_id)].missing_value_kind
            in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
        ]
        missing_fraction = (
            float(len(missing_samples) / len(table.sample_ids))
            if table.sample_ids
            else 0.0
        )
        observed_conditions = {
            condition_by_sample[sample_id]
            for sample_id in observed_samples
            if sample_id in condition_by_sample
        }
        missing_conditions = {
            condition_by_sample[sample_id]
            for sample_id in missing_samples
            if sample_id in condition_by_sample
        }
        mean_log2_observed_abundance = intensity_lookup.get(entity_id)

        label = MissingnessLabel.RANDOM
        note = "missing values are distributed without stronger structural evidence"
        if not observed_samples:
            label = MissingnessLabel.STRUCTURAL_ABSENCE
            note = "entity is missing in every sample under the current study design"
        elif entity_id in condition_specific_entity_ids:
            label = MissingnessLabel.CONDITION_SPECIFIC
            note = (
                "at least one condition is fully missing while another condition retains "
                "observed signal, so this pattern must not be treated as random"
            )
        elif missing_samples and set(missing_samples) <= set(failed_sample_ids):
            label = MissingnessLabel.SAMPLE_FAILURE
            note = "all missing values land in globally failure-prone samples"
        elif (
            intensity_dependence.intensity_dependent_missingness_detected
            and missing_fraction > 0.0
            and mean_log2_observed_abundance is not None
            and mean_log2_observed_abundance <= low_intensity_cutoff
            and len(observed_conditions | missing_conditions) > 1
        ):
            label = MissingnessLabel.INTENSITY_CENSORED
            note = "low observed abundance plus study-wide intensity dependence supports censoring"

        entries.append(
            MissingnessClassificationEntry(
                entity_id=entity_id,
                label=label,
                observed_sample_count=len(observed_samples),
                missing_sample_count=len(missing_samples),
                missing_fraction=missing_fraction,
                mean_log2_observed_abundance=mean_log2_observed_abundance,
                note=note,
            )
        )

    return MissingnessClassificationReport(
        entries=tuple(sorted(entries, key=lambda entry: entry.entity_id)),
        failed_sample_ids=tuple(sorted(failed_sample_ids)),
        note=(
            "missingness classification separates random loss from intensity censoring, "
            "condition-specific absence, sample failure, and structural absence so "
            "downstream statistics can react to mechanism instead of treating every "
            "missing cell the same way"
        ),
    )


def render_missingness_classification_tsv(
    report: MissingnessClassificationReport,
) -> str:
    """Render five-label missingness classifications as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "label",
            "observed_sample_count",
            "missing_sample_count",
            "missing_fraction",
            "mean_log2_observed_abundance",
            "note",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.entity_id,
                entry.label.value,
                str(entry.observed_sample_count),
                str(entry.missing_sample_count),
                f"{entry.missing_fraction:.6f}",
                ""
                if entry.mean_log2_observed_abundance is None
                else f"{entry.mean_log2_observed_abundance:.6f}",
                entry.note,
            )
        )
    return buffer.getvalue()


def _failed_sample_ids(
    sample_summary: MissingValueSummaryReport,
    *,
    minimum_missing_fraction: float = 0.6,
) -> tuple[str, ...]:
    failed: list[str] = []
    for entry in sample_summary.entries:
        total = (
            entry.observed_count
            + entry.zero_count
            + entry.not_observed_count
            + entry.filtered_count
        )
        if total <= 0:
            continue
        missing_fraction = float(
            (entry.not_observed_count + entry.filtered_count) / total
        )
        if missing_fraction >= minimum_missing_fraction:
            failed.append(entry.sample_id)
    return tuple(sorted(failed))
__all__ = [
    "MissingnessClassificationEntry",
    "MissingnessClassificationReport",
    "MissingnessLabel",
    "build_missingness_condition_summary_report",
    "build_missingness_classifier_report",
    "build_missing_data_mechanism_report",
    "build_missingness_entity_summary_report",
    "build_missingness_intensity_dependence_report",
    "classify_missingness",
    "render_missingness_classification_tsv",
    "summarize_missing_values",
]
