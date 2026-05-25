# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Multiplex ratio and differential Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.support.workflow import *  # noqa: F401,F403,F405

def run_tmt_ratio_command(
    input_tsv: Path,
    design_path: Path,
    control_channel: str,
    source_kind: str,
    normalization_method: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
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
        normalization_policy = (
            None
            if normalization_method == "none"
            else TmtNormalizationPolicy(
                method=TmtNormalizationMethod(normalization_method),
            )
        )
        report = build_tmt_ratio_report(
            feature_bundle,
            control_channel=control_channel,
            normalization_policy=normalization_policy,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_ratio_summary_tsv(report, summary_tsv_out)
    if peptide_tsv_out is not None:
        export_tmt_peptide_ratio_tsv(report, peptide_tsv_out)
    if protein_tsv_out is not None:
        export_tmt_protein_ratio_tsv(report, protein_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "control_channel": control_channel,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)

def run_tmt_integrate_plexes_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    plex_effect_ratio_threshold: float,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    alignment_tsv_out: Path | None,
    plex_effect_tsv_out: Path | None,
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
        report = build_tmt_plex_integration_report(
            feature_bundle,
            policy=TmtPlexIntegrationPolicy(
                plex_effect_ratio_threshold=plex_effect_ratio_threshold,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_plex_integration_summary_tsv(report, summary_tsv_out)
    if alignment_tsv_out is not None:
        export_tmt_plex_alignment_tsv(report, alignment_tsv_out)
    if plex_effect_tsv_out is not None:
        export_tmt_plex_effect_tsv(report, plex_effect_tsv_out)
    if protein_matrix_tsv_out is not None:
        export_tmt_integrated_protein_matrix_tsv(report, protein_matrix_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "alignment_tsv": (
                None if alignment_tsv_out is None else str(alignment_tsv_out)
            ),
            "plex_effect_tsv": (
                None if plex_effect_tsv_out is None else str(plex_effect_tsv_out)
            ),
            "protein_matrix_tsv": (
                None
                if protein_matrix_tsv_out is None
                else str(protein_matrix_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

def run_tmt_differential_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    raw_matrix_tsv_out: Path | None,
    normalized_matrix_tsv_out: Path | None,
    results_tsv_out: Path | None,
    balance_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    out_path: Path | None,
) -> None:
    try:
        explicit_channels = _parse_tmt_channel_column_specs(channel_columns)
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        report = build_tmt_differential_analysis_report(
            input_tsv,
            tuple(design_report.accepted_entries),
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
            normalization_method=NormalizationMethod(normalization_method),
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=batch_field,
            covariate_fields=tuple(dict.fromkeys(covariate_fields)),
            pairing_field=pairing_field,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    volcano_plot = report.volcano_plot
    volcano_review = None
    if (
        volcano_tsv_out is not None
        or volcano_json_out is not None
        or volcano_svg_out is not None
        or volcano_html_out is not None
    ):
        if report.differential_abundance_report is None:
            raise click.ClickException(
                "volcano export requires a resolvable contrast or exactly two conditions"
            )
        volcano_plot = build_label_based_differential_volcano_plot(
            report.differential_abundance_report,
            protein_refs_by_entity={
                row.entity_id: row.protein_refs for row in report.normalized_matrix.rows
            },
            adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
            absolute_log2_fold_change_threshold=(
                volcano_absolute_log2_fold_change_threshold
            ),
        )
        volcano_review = build_label_based_volcano_review(
            volcano_plot,
            policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
                absolute_log2_fold_change_threshold=(
                    volcano_absolute_log2_fold_change_threshold
                ),
                top_label_count=volcano_top_label_count,
            ),
        )

    if raw_matrix_tsv_out is not None:
        export_label_based_differential_matrix_tsv(
            report.input_report,
            raw_matrix_tsv_out,
        )
    if normalized_matrix_tsv_out is not None:
        export_label_based_differential_matrix_tsv(
            report.normalized_matrix,
            normalized_matrix_tsv_out,
        )
    if results_tsv_out is not None:
        export_label_based_differential_results_tsv(report, results_tsv_out)
    if balance_tsv_out is not None:
        export_label_based_normalization_balance_plot_tsv(
            report.normalization_balance_plot,
            balance_tsv_out,
        )
    if volcano_tsv_out is not None and volcano_plot is not None:
        export_label_based_differential_volcano_plot_tsv(
            volcano_plot,
            volcano_tsv_out,
        )
    if volcano_review is not None:
        _export_volcano_review_assets(
            review_report=volcano_review,
            json_out=volcano_json_out,
            svg_out=volcano_svg_out,
            html_out=volcano_html_out,
        )

    payload = {
        "source_kind": source_kind,
        "report": report.to_dict(),
        "volcano_review": None if volcano_review is None else volcano_review.to_dict(),
        "outputs": {
            "raw_matrix_tsv": (
                None if raw_matrix_tsv_out is None else str(raw_matrix_tsv_out)
            ),
            "normalized_matrix_tsv": (
                None
                if normalized_matrix_tsv_out is None
                else str(normalized_matrix_tsv_out)
            ),
            "results_tsv": (
                None if results_tsv_out is None else str(results_tsv_out)
            ),
            "balance_tsv": (
                None if balance_tsv_out is None else str(balance_tsv_out)
            ),
            "volcano_tsv": (
                None
                if volcano_tsv_out is None or volcano_plot is None
                else str(volcano_tsv_out)
            ),
            "volcano_json": (
                None if volcano_json_out is None else str(volcano_json_out)
            ),
            "volcano_svg": None if volcano_svg_out is None else str(volcano_svg_out),
            "volcano_html": (
                None if volcano_html_out is None else str(volcano_html_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

def run_tmt_report_command(
    input_tsv: Path,
    design_path: Path,
    control_channel: str,
    source_kind: str,
    channel_normalization_method: str,
    differential_normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    output_dir: Path,
    out_path: Path | None,
) -> None:
    result = _run_orchestrated_workflow(
        TmtWorkflowConfig(
            result_tsv_path=input_tsv,
            design_tsv_path=design_path,
            control_channel=control_channel,
            source_kind=TmtSearchResultSourceKind(source_kind),
            mapping=TmtReporterColumnMapping(
                source_row_id=row_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                multiplex_group=multiplex_group_column,
                default_multiplex_group=default_multiplex_group,
                protein_separator=protein_separator,
            ),
            channel_columns=_parse_tmt_channel_column_specs(channel_columns),
            channel_normalization_method=TmtNormalizationMethod(
                channel_normalization_method
            ),
            differential_normalization_method=NormalizationMethod(
                differential_normalization_method
            ),
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=batch_field,
            covariate_fields=tuple(dict.fromkeys(covariate_fields)),
            pairing_field=pairing_field,
            output_dir=output_dir,
        )
    )
    workflow_report = result.report
    workflow_manifest = result.export_manifest
    if workflow_manifest is None:
        raise click.ClickException("workflow export manifest was not produced")

    _emit_json(
        {
            "source_kind": source_kind,
            "control_channel": control_channel,
            "workflow_report": workflow_report.to_dict(),
            "report": workflow_report.report.to_dict(),
            "workflow_export_manifest": workflow_manifest.to_dict(),
            "export_manifest": workflow_manifest.label_based_report_manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )

__all__ = ['run_tmt_ratio_command', 'run_tmt_integrate_plexes_command', 'run_tmt_differential_command', 'run_tmt_report_command']
