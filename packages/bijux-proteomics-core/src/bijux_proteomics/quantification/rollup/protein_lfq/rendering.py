# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable rendering owners for protein LFQ reports."""

from __future__ import annotations

from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics.quantification.rollup.protein_lfq.models import ProteinLfqReport


def render_protein_lfq_summary_tsv(report: ProteinLfqReport) -> str:
    """Render one compact MaxLFQ-like summary as TSV."""
    header = (
        "source_kind",
        "grouping_mode",
        "target_kind",
        "separate_charge_states",
        "aggregation_method",
        "unique_only",
        "minimum_shared_peptides",
        "peptide_row_count",
        "protein_row_count",
        "sample_count",
        "fully_connected_row_count",
        "disconnected_row_count",
        "disconnected_component_entry_count",
        "total_pairwise_ratio_count",
        "observed_cell_count",
        "missing_cell_count",
        "note",
    )
    row = (
        report.source_kind.value,
        report.grouping_mode.value,
        report.target_kind.value,
        str(report.separate_charge_states).lower(),
        report.aggregation_method.value,
        str(report.unique_only).lower(),
        str(report.minimum_shared_peptides),
        str(report.summary.peptide_row_count),
        str(report.summary.protein_row_count),
        str(report.summary.sample_count),
        str(report.summary.fully_connected_row_count),
        str(report.summary.disconnected_row_count),
        str(report.summary.disconnected_component_entry_count),
        str(report.summary.total_pairwise_ratio_count),
        str(report.summary.observed_cell_count),
        str(report.summary.missing_cell_count),
        report.note,
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_protein_lfq_matrix_tsv(report: ProteinLfqReport) -> str:
    """Render the protein LFQ matrix as one wide TSV."""
    ordered_sample_ids = sort_strings(report.sample_ids)
    ordered_rows = sort_rows_by_fields(report.rows, "entity_id")
    header = [
        "entity_id",
        "target_kind",
        "protein_refs",
        "peptide_count",
        "unique_peptide_count",
        "shared_peptide_count",
        "pairwise_ratio_count",
        "connected_component_count",
        "contributing_peptides",
    ]
    header.extend(ordered_sample_ids)
    rows = ["\t".join(header)]
    for row in ordered_rows:
        value_lookup = {value.sample_id: value for value in row.values}
        matrix_values = []
        for sample_id in ordered_sample_ids:
            value = value_lookup[sample_id]
            matrix_values.append(
                "" if value.abundance is None else f"{value.abundance:g}"
            )
        rows.append(
            "\t".join(
                (
                    row.entity_id,
                    row.target_kind.value,
                    ";".join(sort_strings(row.protein_refs)),
                    str(row.peptide_count),
                    str(row.unique_peptide_count),
                    str(row.shared_peptide_count),
                    str(row.pairwise_ratio_count),
                    str(row.connected_component_count),
                    ";".join(sort_strings(row.contributing_peptides)),
                    *matrix_values,
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_protein_lfq_pairwise_ratios_tsv(report: ProteinLfqReport) -> str:
    """Render one pairwise-ratio ledger for all protein LFQ rows."""
    ordered_rows = sort_rows_by_fields(report.rows, "entity_id")
    header = (
        "entity_id",
        "target_kind",
        "sample_a",
        "sample_b",
        "shared_peptide_count",
        "median_log2_ratio",
        "median_ratio",
        "contributing_peptides",
    )
    rows = ["\t".join(header)]
    for row in ordered_rows:
        for ratio in sort_rows_by_fields(row.pairwise_ratios, "sample_a", "sample_b"):
            rows.append(
                "\t".join(
                    (
                        row.entity_id,
                        row.target_kind.value,
                        ratio.sample_a,
                        ratio.sample_b,
                        str(ratio.shared_peptide_count),
                        f"{ratio.median_log2_ratio:g}",
                        f"{ratio.median_ratio:g}",
                        ";".join(sort_strings(ratio.contributing_peptides)),
                    )
                )
            )
    return "\n".join(rows) + "\n"


def render_protein_lfq_missingness_tsv(report: ProteinLfqReport) -> str:
    """Render one per-sample missingness ledger for a protein LFQ matrix."""
    header = (
        "sample_id",
        "observed_count",
        "zero_count",
        "not_observed_count",
        "filtered_count",
        "imputed_count",
        "censored_count",
        "excluded_count",
        "not_applicable_count",
    )
    rows = ["\t".join(header)]
    for entry in sort_rows_by_fields(report.missing_summary.entries, "sample_id"):
        rows.append(
            "\t".join(
                (
                    entry.sample_id,
                    str(entry.observed_count),
                    str(entry.zero_count),
                    str(entry.not_observed_count),
                    str(entry.filtered_count),
                    str(entry.imputed_count),
                    str(entry.censored_count),
                    str(entry.excluded_count),
                    str(entry.not_applicable_count),
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_protein_lfq_missingness_mask_tsv(report: ProteinLfqReport) -> str:
    """Render one protein-LFQ missingness mask beside the wide LFQ matrix."""

    ordered_sample_ids = sort_strings(report.sample_ids)
    ordered_rows = sort_rows_by_fields(report.rows, "entity_id")
    header = [
        "entity_id",
        "target_kind",
        "protein_refs",
        "peptide_count",
        "unique_peptide_count",
        "shared_peptide_count",
        "pairwise_ratio_count",
        "connected_component_count",
        "contributing_peptides",
    ]
    header.extend(ordered_sample_ids)
    rows = ["\t".join(header)]
    for row in ordered_rows:
        value_lookup = {value.sample_id: value for value in row.values}
        rows.append(
            "\t".join(
                (
                    row.entity_id,
                    row.target_kind.value,
                    ";".join(sort_strings(row.protein_refs)),
                    str(row.peptide_count),
                    str(row.unique_peptide_count),
                    str(row.shared_peptide_count),
                    str(row.pairwise_ratio_count),
                    str(row.connected_component_count),
                    ";".join(sort_strings(row.contributing_peptides)),
                    *[
                        value_lookup[sample_id].missing_value_kind.value
                        for sample_id in ordered_sample_ids
                    ],
                )
            )
        )
    return "\n".join(rows) + "\n"


def render_protein_lfq_disconnected_components_tsv(report: ProteinLfqReport) -> str:
    """Render one ledger of LFQ sample components that remain disconnected."""

    header = (
        "entity_id",
        "target_kind",
        "protein_refs",
        "component_id",
        "sample_ids",
        "disconnected_from_sample_ids",
        "sample_count",
        "pairwise_ratio_count",
        "contributing_peptides",
    )
    rows = ["\t".join(header)]
    for entry in sort_rows_by_fields(
        report.disconnected_components,
        "entity_id",
        "component_id",
    ):
        rows.append(
            "\t".join(
                (
                    entry.entity_id,
                    entry.target_kind.value,
                    ";".join(sort_strings(entry.protein_refs)),
                    str(entry.component_id),
                    ";".join(sort_strings(entry.sample_ids)),
                    ";".join(sort_strings(entry.disconnected_from_sample_ids)),
                    str(entry.sample_count),
                    str(entry.pairwise_ratio_count),
                    ";".join(sort_strings(entry.contributing_peptides)),
                )
            )
        )
    return "\n".join(rows) + "\n"


__all__ = [
    "render_protein_lfq_disconnected_components_tsv",
    "render_protein_lfq_matrix_tsv",
    "render_protein_lfq_missingness_mask_tsv",
    "render_protein_lfq_missingness_tsv",
    "render_protein_lfq_pairwise_ratios_tsv",
    "render_protein_lfq_summary_tsv",
]
