# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Missingness classifier assembly and downstream label assignment."""

from __future__ import annotations

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
    MissingnessClassifierReport,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
)
from bijux_proteomics.quantification.missingness.intensity_dependence import (
    build_missingness_intensity_dependence_report,
    low_intensity_cutoff,
)
from bijux_proteomics.quantification.missingness.mechanism_report import (
    build_missing_data_mechanism_report,
)
from bijux_proteomics.quantification.missingness.models import (
    MissingnessClassificationEntry,
    MissingnessClassificationReport,
    MissingnessLabel,
)
from bijux_proteomics.quantification.missingness.summaries import (
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    summarize_missing_values,
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
    low_abundance_cutoff = low_intensity_cutoff(intensity_dependence)

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
            and mean_log2_observed_abundance <= low_abundance_cutoff
            and len(observed_conditions | missing_conditions) > 1
        ):
            label = MissingnessLabel.INTENSITY_CENSORED
            note = (
                "low observed abundance plus study-wide intensity dependence "
                "supports censoring"
            )

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
    "build_missingness_classifier_report",
    "classify_missingness",
]
