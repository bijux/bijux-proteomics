# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Input assembly for labeled differential workflow execution."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.isotope_labeling import (
    SilacColumnMapping,
    SilacProteinRatioEntry,
    SilacQuantificationPolicy,
    SilacRatioReport,
    build_silac_ratio_report,
    parse_silac_feature_table,
)
from bijux_proteomics.multiplex import (
    TmtReporterChannelColumn,
    TmtReporterColumnMapping,
    TmtSearchResultSourceKind,
    build_tmt_plex_integration_report,
    build_tmt_reporter_feature_bundle,
    build_tmt_reporter_matrix_report,
    parse_tmt_reporter_table,
)
from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.protein_intensity_matrix import (
    ProteinIntensityMatrixReport,
)
from bijux_proteomics.study import ExperimentDesign, coerce_experiment_design
from bijux_proteomics.workflow.pipelines.label_based_differential.models import (
    LabelBasedDifferentialInputReport,
    LabelBasedDifferentialMatrixRow,
    LabelBasedDifferentialMatrixSummary,
    LabelBasedDifferentialMatrixValue,
    LabelBasedDifferentialSourceKind,
    LabelBasedMeasurementKind,
)


def build_tmt_differential_input_report(
    result_tsv_path: Path,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    source_kind: TmtSearchResultSourceKind = TmtSearchResultSourceKind.MAXQUANT,
    mapping: TmtReporterColumnMapping | None = None,
    channel_columns: tuple[TmtReporterChannelColumn, ...] = (),
) -> LabelBasedDifferentialInputReport:
    """Build a protein-level labeled differential input packet from TMT evidence."""

    experiment_design = coerce_experiment_design(design_entries)
    import_report = parse_tmt_reporter_table(
        result_tsv_path,
        source_kind=source_kind,
        mapping=mapping,
        channel_columns=channel_columns,
    )
    feature_bundle = build_tmt_reporter_feature_bundle(
        import_report,
        design_entries=experiment_design.entries,
    )
    mapped_groups = {
        entry.multiplex_group
        for entry in feature_bundle.channel_mapping
        if entry.mapped_to_design
    }
    if len(mapped_groups) > 1:
        integration_report = build_tmt_plex_integration_report(feature_bundle)
        protein_matrix = integration_report.integrated_protein_matrix
        note = "labeled differential input preserves a bridge-normalized TMT protein matrix across multiplex groups"
    else:
        matrix_report = build_tmt_reporter_matrix_report(feature_bundle)
        protein_matrix = matrix_report.protein_matrix
        note = "labeled differential input preserves a protein-level TMT reporter matrix for one multiplex group"
    return build_input_report_from_protein_matrix(
        protein_matrix,
        source_kind=LabelBasedDifferentialSourceKind.TMT,
        source_name=source_kind.value,
        measurement_kind=LabelBasedMeasurementKind.INTENSITY,
        note=note,
    )


def build_silac_differential_input_report(
    feature_tsv_path: Path,
    *,
    mapping: SilacColumnMapping | None = None,
    quantification_policy: SilacQuantificationPolicy | None = None,
) -> LabelBasedDifferentialInputReport:
    """Build a protein-level labeled differential input packet from SILAC ratios."""

    import_report = parse_silac_feature_table(
        feature_tsv_path,
        mapping=mapping,
    )
    ratio_report = build_silac_ratio_report(
        import_report,
        policy=quantification_policy,
    )
    return build_input_report_from_silac_ratio_report(ratio_report)


def build_input_report_from_protein_matrix(
    protein_matrix: ProteinIntensityMatrixReport,
    *,
    source_kind: LabelBasedDifferentialSourceKind,
    source_name: str,
    measurement_kind: LabelBasedMeasurementKind,
    note: str,
) -> LabelBasedDifferentialInputReport:
    """Translate one governed protein matrix into labeled differential inputs."""

    rows = tuple(
        LabelBasedDifferentialMatrixRow(
            entity_id=row.entity_id,
            protein_refs=row.protein_refs,
            member_peptides=row.contributing_peptides,
            values=tuple(
                LabelBasedDifferentialMatrixValue(
                    sample_id=value.sample_id,
                    abundance=value.abundance,
                    missing_value_kind=value.missing_value_kind,
                    source_feature_count=value.contributing_peptide_count,
                )
                for value in row.values
            ),
        )
        for row in protein_matrix.rows
    )
    observed_cell_count = sum(
        1 for row in rows for value in row.values if value.abundance is not None
    )
    missing_cell_count = sum(
        1 for row in rows for value in row.values if value.abundance is None
    )
    return LabelBasedDifferentialInputReport(
        source_kind=source_kind,
        source_name=source_name,
        measurement_kind=measurement_kind,
        summary=LabelBasedDifferentialMatrixSummary(
            source_kind=source_kind,
            measurement_kind=measurement_kind,
            entity_count=len(rows),
            sample_count=len(protein_matrix.sample_ids),
            observed_cell_count=observed_cell_count,
            missing_cell_count=missing_cell_count,
        ),
        sample_ids=protein_matrix.sample_ids,
        rows=rows,
        note=note,
    )


def build_input_report_from_silac_ratio_report(
    ratio_report: SilacRatioReport,
) -> LabelBasedDifferentialInputReport:
    """Translate one governed SILAC ratio report into labeled differential inputs."""

    grouped: dict[str, list[SilacProteinRatioEntry]] = {}
    sample_ids: set[str] = set()
    for entry in ratio_report.protein_ratios:
        entity_id = (
            entry.protein_id
            if len(ratio_report.policy.expected_labels) == 2
            else f"{entry.protein_id}:{entry.numerator_label.value}_vs_{entry.reference_label.value}"
        )
        grouped.setdefault(entity_id, []).append(entry)
        sample_ids.add(entry.sample_id)
    rows: list[LabelBasedDifferentialMatrixRow] = []
    for entity_id in sorted(grouped):
        entries = grouped[entity_id]
        first_entry = entries[0]
        rows.append(
            LabelBasedDifferentialMatrixRow(
                entity_id=entity_id,
                protein_refs=first_entry.protein_refs,
                member_peptides=first_entry.contributing_peptide_ids,
                values=tuple(
                    sorted(
                        [
                            LabelBasedDifferentialMatrixValue(
                                sample_id=entry.sample_id,
                                abundance=entry.ratio,
                                missing_value_kind=(
                                    MissingValueKind.ZERO
                                    if entry.ratio == 0.0
                                    else MissingValueKind.OBSERVED
                                ),
                                source_feature_count=len(
                                    entry.contributing_peptide_ids
                                ),
                            )
                            for entry in entries
                        ],
                        key=lambda value: value.sample_id,
                    )
                ),
            )
        )
    observed_cell_count = sum(
        1 for row in rows for value in row.values if value.abundance is not None
    )
    missing_cell_count = sum(
        1 for row in rows for value in row.values if value.abundance is None
    )
    ordered_sample_ids = tuple(sorted(sample_ids))
    rows = [
        row.model_copy(
            update={
                "values": tuple(
                    fill_missing_matrix_values(
                        row.values,
                        sample_ids=ordered_sample_ids,
                    )
                )
            }
        )
        for row in rows
    ]
    return LabelBasedDifferentialInputReport(
        source_kind=LabelBasedDifferentialSourceKind.SILAC,
        source_name="silac",
        measurement_kind=LabelBasedMeasurementKind.RATIO,
        summary=LabelBasedDifferentialMatrixSummary(
            source_kind=LabelBasedDifferentialSourceKind.SILAC,
            measurement_kind=LabelBasedMeasurementKind.RATIO,
            entity_count=len(rows),
            sample_count=len(ordered_sample_ids),
            observed_cell_count=observed_cell_count,
            missing_cell_count=missing_cell_count,
        ),
        sample_ids=ordered_sample_ids,
        rows=tuple(rows),
        note=(
            "labeled differential input preserves protein-level SILAC sample ratios against the governed reference label"
        ),
    )


def fill_missing_matrix_values(
    values: tuple[LabelBasedDifferentialMatrixValue, ...],
    *,
    sample_ids: tuple[str, ...],
) -> tuple[LabelBasedDifferentialMatrixValue, ...]:
    """Materialize explicit missing entries for absent labeled matrix cells."""

    value_lookup = {value.sample_id: value for value in values}
    return tuple(
        value_lookup.get(
            sample_id,
            LabelBasedDifferentialMatrixValue(
                sample_id=sample_id,
                abundance=None,
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
                source_feature_count=0,
            ),
        )
        for sample_id in sample_ids
    )


__all__ = [
    "build_input_report_from_protein_matrix",
    "build_input_report_from_silac_ratio_report",
    "build_silac_differential_input_report",
    "build_tmt_differential_input_report",
    "fill_missing_matrix_values",
]
