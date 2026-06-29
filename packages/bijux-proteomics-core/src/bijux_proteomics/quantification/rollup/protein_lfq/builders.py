# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Top-level report builders for protein LFQ packages."""

from __future__ import annotations

from collections import defaultdict

from bijux_proteomics.domain.records import (
    QuantMatrix as CanonicalQuantMatrix,
)
from bijux_proteomics.identification import PsmRecord
from bijux_proteomics.quantification.contracts.input_models import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantRollupMethod,
)
from bijux_proteomics.quantification.contracts.missingness import (
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
)
from bijux_proteomics.quantification.matrix.peptide_intensity_matrix import (
    PeptideIntensityMatrixReport,
    PeptideIntensityMatrixRow,
    PeptideMatrixGroupingMode,
    build_peptide_intensity_matrix_from_features,
    build_peptide_intensity_matrix_from_psms,
)
from bijux_proteomics.quantification.matrix.protein_intensity_matrix import (
    ProteinMatrixTargetKind,
)
from bijux_proteomics.quantification.rollup.protein_lfq.models import (
    ProteinLfqDisconnectedComponentEntry,
    ProteinLfqReport,
    ProteinLfqRow,
    ProteinLfqSummary,
    ProteinLfqValue,
)
from bijux_proteomics.quantification.rollup.protein_lfq.row_assembly import (
    build_disconnected_component_entries,
    build_target_lfq_row,
)


def build_protein_lfq_report_from_peptides(
    peptide_matrix: PeptideIntensityMatrixReport | CanonicalQuantMatrix,
    *,
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    unique_only: bool = False,
    minimum_shared_peptides: int = 1,
) -> ProteinLfqReport:
    """Build one MaxLFQ-like protein matrix from a peptide-intensity matrix."""
    if isinstance(peptide_matrix, CanonicalQuantMatrix):
        peptide_matrix = PeptideIntensityMatrixReport.from_quant_matrix(peptide_matrix)
    if minimum_shared_peptides < 1:
        raise ValueError("minimum_shared_peptides must be at least 1")

    grouped_rows: dict[str, list[tuple[PeptideIntensityMatrixRow, bool]]] = defaultdict(
        list
    )
    target_refs: dict[str, tuple[str, ...]] = {}

    for peptide_row in peptide_matrix.rows:
        is_unique = len(peptide_row.protein_refs) == 1
        if unique_only and not is_unique:
            continue
        if not peptide_row.protein_refs:
            continue
        if target_kind is ProteinMatrixTargetKind.PROTEIN:
            target_ids = peptide_row.protein_refs
        else:
            target_ids = (";".join(peptide_row.protein_refs),)
        for target_id in target_ids:
            target_refs.setdefault(
                target_id,
                peptide_row.protein_refs
                if target_kind is ProteinMatrixTargetKind.PROTEIN_GROUP
                else (target_id,),
            )
            grouped_rows[target_id].append((peptide_row, is_unique))

    rows: list[ProteinLfqRow] = []
    missing_entries: list[MissingValueSummaryEntry] = []
    observed_cell_count = 0
    missing_cell_count = 0
    fully_connected_row_count = 0
    disconnected_row_count = 0
    disconnected_component_entries: list[ProteinLfqDisconnectedComponentEntry] = []
    total_pairwise_ratio_count = 0

    ordered_target_ids = tuple(sorted(grouped_rows))
    row_values_by_target: dict[str, dict[str, ProteinLfqValue]] = {}
    for target_id in ordered_target_ids:
        row = build_target_lfq_row(
            target_id,
            grouped_rows[target_id],
            sample_ids=peptide_matrix.sample_ids,
            protein_refs=target_refs[target_id],
            target_kind=target_kind,
            minimum_shared_peptides=minimum_shared_peptides,
        )
        row_values_by_target[target_id] = {
            value.sample_id: value for value in row.values
        }
        rows.append(row)
        total_pairwise_ratio_count += row.pairwise_ratio_count
        if row.fully_connected:
            fully_connected_row_count += 1
        elif row.connected_component_count > 1:
            disconnected_row_count += 1
            disconnected_component_entries.extend(
                build_disconnected_component_entries(
                    row,
                    peptide_rows=grouped_rows[target_id],
                )
            )
        for value in row.values:
            if value.abundance is None:
                missing_cell_count += 1
            else:
                observed_cell_count += 1

    for sample_id in peptide_matrix.sample_ids:
        observed = 0
        zero = 0
        not_observed = 0
        filtered = 0
        for target_id in ordered_target_ids:
            value = row_values_by_target[target_id][sample_id]
            if value.missing_value_kind is MissingValueKind.OBSERVED:
                observed += 1
            elif value.missing_value_kind is MissingValueKind.ZERO:
                zero += 1
            elif value.missing_value_kind is MissingValueKind.FILTERED:
                filtered += 1
            else:
                not_observed += 1
        missing_entries.append(
            MissingValueSummaryEntry(
                sample_id=sample_id,
                observed_count=observed,
                zero_count=zero,
                not_observed_count=not_observed,
                filtered_count=filtered,
            )
        )

    summary = ProteinLfqSummary(
        peptide_row_count=len(peptide_matrix.rows),
        protein_row_count=len(rows),
        sample_count=len(peptide_matrix.sample_ids),
        unique_only=unique_only,
        minimum_shared_peptides=minimum_shared_peptides,
        fully_connected_row_count=fully_connected_row_count,
        disconnected_row_count=disconnected_row_count,
        disconnected_component_entry_count=len(disconnected_component_entries),
        total_pairwise_ratio_count=total_pairwise_ratio_count,
        observed_cell_count=observed_cell_count,
        missing_cell_count=missing_cell_count,
    )
    return ProteinLfqReport(
        source_kind=peptide_matrix.source_kind,
        grouping_mode=peptide_matrix.grouping_mode,
        target_kind=target_kind,
        separate_charge_states=peptide_matrix.separate_charge_states,
        aggregation_method=peptide_matrix.aggregation_method,
        unique_only=unique_only,
        minimum_shared_peptides=minimum_shared_peptides,
        sample_ids=peptide_matrix.sample_ids,
        rows=tuple(rows),
        disconnected_components=tuple(disconnected_component_entries),
        missing_summary=MissingValueSummaryReport(
            entity_level=peptide_matrix.missing_summary.entity_level,
            policy=MissingValueSummaryPolicy(),
            entries=tuple(missing_entries),
            included_entity_ids=tuple(row.entity_id for row in rows),
            excluded_entity_ids=(),
        ),
        summary=summary,
        note=(
            "maxlfq-like protein quantification preserves shared-peptide pairwise log-ratios and solves sample profiles with component-aware least squares"
        ),
    )


def build_protein_lfq_report_from_features(
    records: tuple[Ms1FeatureRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = (
        PeptideMatrixGroupingMode.MODIFIED_PEPTIDE
    ),
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    separate_charge_states: bool = False,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    minimum_shared_peptides: int = 1,
    top_n: int = 3,
) -> ProteinLfqReport:
    """Build one MaxLFQ-like protein matrix from MS1 feature evidence."""
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_protein_lfq_report_from_peptides(
        peptide_matrix,
        target_kind=target_kind,
        unique_only=unique_only,
        minimum_shared_peptides=minimum_shared_peptides,
    )


def build_protein_lfq_report_from_psms(
    records: tuple[PsmRecord, ...],
    *,
    grouping_mode: PeptideMatrixGroupingMode = (
        PeptideMatrixGroupingMode.MODIFIED_PEPTIDE
    ),
    target_kind: ProteinMatrixTargetKind = ProteinMatrixTargetKind.PROTEIN,
    separate_charge_states: bool = False,
    aggregation_method: QuantRollupMethod = QuantRollupMethod.SUM,
    unique_only: bool = False,
    minimum_shared_peptides: int = 1,
    top_n: int = 3,
) -> ProteinLfqReport:
    """Build one MaxLFQ-like protein matrix from intensity-bearing canonical PSM rows."""
    peptide_matrix = build_peptide_intensity_matrix_from_psms(
        records,
        grouping_mode=grouping_mode,
        separate_charge_states=separate_charge_states,
        aggregation_method=aggregation_method,
        top_n=top_n,
    )
    return build_protein_lfq_report_from_peptides(
        peptide_matrix,
        target_kind=target_kind,
        unique_only=unique_only,
        minimum_shared_peptides=minimum_shared_peptides,
    )


__all__ = [
    "build_protein_lfq_report_from_features",
    "build_protein_lfq_report_from_peptides",
    "build_protein_lfq_report_from_psms",
]
