# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Multiplex matrix and normalization Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    parse_experimental_design_table,
)
from bijux_proteomics.interfaces.support.multiplex_targeted.multiplex import (
    TmtInterferencePolicy,
    TmtNormalizationMethod,
    TmtNormalizationPolicy,
    TmtReporterColumnMapping,
    TmtSearchResultSourceKind,
    build_multiplex_metadata_validation_report,
    build_tmt_interference_report,
    build_tmt_normalization_report,
    build_tmt_reporter_feature_bundle,
    build_tmt_reporter_matrix_report,
    export_multiplex_channel_assignment_tsv,
    export_multiplex_duplicate_assignment_tsv,
    export_multiplex_metadata_summary_tsv,
    export_multiplex_missing_condition_tsv,
    export_tmt_channel_distribution_tsv,
    export_tmt_channel_mapping_tsv,
    export_tmt_channel_totals_tsv,
    export_tmt_filtered_interference_tsv,
    export_tmt_interference_channel_summary_tsv,
    export_tmt_interference_observation_tsv,
    export_tmt_interference_summary_tsv,
    export_tmt_normalization_summary_tsv,
    export_tmt_normalization_transform_tsv,
    export_tmt_normalized_peptide_matrix_tsv,
    export_tmt_normalized_protein_matrix_tsv,
    export_tmt_peptide_matrix_tsv,
    export_tmt_protein_matrix_tsv,
    export_tmt_report_summary_tsv,
    parse_tmt_reporter_table,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
)
from bijux_proteomics.interfaces.support.sequence_support.multiplex_inputs import (
    _parse_tmt_channel_column_specs,
)


def run_multiplex_validate_metadata_command(
    design_path: Path,
    summary_tsv_out: Path | None,
    channel_tsv_out: Path | None,
    duplicate_tsv_out: Path | None,
    missing_condition_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        design_report = parse_experimental_design_table(design_path)
        report = build_multiplex_metadata_validation_report(design_report)
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_multiplex_metadata_summary_tsv(report, summary_tsv_out)
    if channel_tsv_out is not None:
        export_multiplex_channel_assignment_tsv(report, channel_tsv_out)
    if duplicate_tsv_out is not None:
        export_multiplex_duplicate_assignment_tsv(report, duplicate_tsv_out)
    if missing_condition_tsv_out is not None:
        export_multiplex_missing_condition_tsv(report, missing_condition_tsv_out)

    payload = {
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "channel_tsv": None if channel_tsv_out is None else str(channel_tsv_out),
            "duplicate_tsv": (
                None if duplicate_tsv_out is None else str(duplicate_tsv_out)
            ),
            "missing_condition_tsv": (
                None
                if missing_condition_tsv_out is None
                else str(missing_condition_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_tmt_reporter_matrix_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    channel_mapping_tsv_out: Path | None,
    channel_totals_tsv_out: Path | None,
    peptide_matrix_tsv_out: Path | None,
    protein_matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        import_report = parse_tmt_reporter_table(
            input_tsv,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        feature_bundle = build_tmt_reporter_feature_bundle(
            import_report,
            design_entries=tuple(design_report.accepted_entries),
        )
        report = build_tmt_reporter_matrix_report(feature_bundle)
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_report_summary_tsv(report, summary_tsv_out)
    if channel_mapping_tsv_out is not None:
        export_tmt_channel_mapping_tsv(report, channel_mapping_tsv_out)
    if channel_totals_tsv_out is not None:
        export_tmt_channel_totals_tsv(report, channel_totals_tsv_out)
    if peptide_matrix_tsv_out is not None:
        export_tmt_peptide_matrix_tsv(report, peptide_matrix_tsv_out)
    if protein_matrix_tsv_out is not None:
        export_tmt_protein_matrix_tsv(report, protein_matrix_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_report": import_report.to_dict(),
        "feature_bundle": feature_bundle.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "channel_mapping_tsv": (
                None
                if channel_mapping_tsv_out is None
                else str(channel_mapping_tsv_out)
            ),
            "channel_totals_tsv": (
                None if channel_totals_tsv_out is None else str(channel_totals_tsv_out)
            ),
            "peptide_matrix_tsv": (
                None if peptide_matrix_tsv_out is None else str(peptide_matrix_tsv_out)
            ),
            "protein_matrix_tsv": (
                None if protein_matrix_tsv_out is None else str(protein_matrix_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_tmt_interference_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    interference_threshold: float,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    interference_column: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    observation_tsv_out: Path | None,
    filtered_tsv_out: Path | None,
    channel_summary_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        import_report = parse_tmt_reporter_table(
            input_tsv,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                isolation_interference=interference_column,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        report = build_tmt_interference_report(
            import_report,
            design_entries=tuple(design_report.accepted_entries),
            policy=TmtInterferencePolicy(
                interference_fraction_threshold=interference_threshold
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_interference_summary_tsv(report, summary_tsv_out)
    if observation_tsv_out is not None:
        export_tmt_interference_observation_tsv(report, observation_tsv_out)
    if filtered_tsv_out is not None:
        export_tmt_filtered_interference_tsv(report, filtered_tsv_out)
    if channel_summary_tsv_out is not None:
        export_tmt_interference_channel_summary_tsv(report, channel_summary_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "observation_tsv": (
                None if observation_tsv_out is None else str(observation_tsv_out)
            ),
            "filtered_tsv": (
                None if filtered_tsv_out is None else str(filtered_tsv_out)
            ),
            "channel_summary_tsv": (
                None
                if channel_summary_tsv_out is None
                else str(channel_summary_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_tmt_normalize_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    method: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    transform_tsv_out: Path | None,
    distribution_tsv_out: Path | None,
    peptide_matrix_tsv_out: Path | None,
    protein_matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        import_report = parse_tmt_reporter_table(
            input_tsv,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=explicit_channels,
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        feature_bundle = build_tmt_reporter_feature_bundle(
            import_report,
            design_entries=tuple(design_report.accepted_entries),
        )
        report = build_tmt_normalization_report(
            feature_bundle,
            policy=TmtNormalizationPolicy(
                method=TmtNormalizationMethod(method),
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_normalization_summary_tsv(report, summary_tsv_out)
    if transform_tsv_out is not None:
        export_tmt_normalization_transform_tsv(report, transform_tsv_out)
    if distribution_tsv_out is not None:
        export_tmt_channel_distribution_tsv(report, distribution_tsv_out)
    if peptide_matrix_tsv_out is not None:
        export_tmt_normalized_peptide_matrix_tsv(report, peptide_matrix_tsv_out)
    if protein_matrix_tsv_out is not None:
        export_tmt_normalized_protein_matrix_tsv(report, protein_matrix_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "transform_tsv": (
                None if transform_tsv_out is None else str(transform_tsv_out)
            ),
            "distribution_tsv": (
                None if distribution_tsv_out is None else str(distribution_tsv_out)
            ),
            "peptide_matrix_tsv": (
                None if peptide_matrix_tsv_out is None else str(peptide_matrix_tsv_out)
            ),
            "protein_matrix_tsv": (
                None if protein_matrix_tsv_out is None else str(protein_matrix_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_multiplex_validate_metadata_command",
    "run_tmt_reporter_matrix_command",
    "run_tmt_interference_command",
    "run_tmt_normalize_command",
]
