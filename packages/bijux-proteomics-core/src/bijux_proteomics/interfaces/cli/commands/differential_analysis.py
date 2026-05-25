# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Differential review CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("dia-differential")
@click.argument("input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in DiaDifferentialSourceKind]),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--max-q-value", type=float, default=0.01, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-pairing-field", default=None)
@click.option("--design-covariate", "design_covariates", multiple=True)
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--normalized-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--differential-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--qc-summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--design-matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--design-coefficients-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--volcano-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-json-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-svg-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-html-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--volcano-adjusted-p-value-threshold",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--volcano-absolute-log2-fold-change-threshold",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--sample-balance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def dia_differential_command(
    input_path: Path,
    design_path: Path,
    source_kind: str,
    config_path: Path | None,
    max_q_value: float,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    matrix_tsv_out: Path | None,
    normalized_matrix_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    qc_summary_tsv_out: Path | None,
    design_matrix_tsv_out: Path | None,
    design_coefficients_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    sample_balance_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Run DIA-native differential analysis from DIA-NN or Spectronaut evidence.'
    return run_dia_differential_command(input_path, design_path, source_kind, config_path, max_q_value, normalization, condition_a, condition_b, design_batch_field, design_pairing_field, design_covariates, matrix_tsv_out, normalized_matrix_tsv_out, differential_tsv_out, qc_summary_tsv_out, design_matrix_tsv_out, design_coefficients_tsv_out, volcano_tsv_out, volcano_json_out, volcano_svg_out, volcano_html_out, volcano_adjusted_p_value_threshold, volcano_absolute_log2_fold_change_threshold, volcano_top_label_count, sample_balance_tsv_out, out_path)

def run_dia_differential_command(
    input_path: Path,
    design_path: Path,
    source_kind: str,
    config_path: Path | None,
    max_q_value: float,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    matrix_tsv_out: Path | None,
    normalized_matrix_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    qc_summary_tsv_out: Path | None,
    design_matrix_tsv_out: Path | None,
    design_coefficients_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    sample_balance_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        selected_source = DiaDifferentialSourceKind(source_kind)
        if selected_source is DiaDifferentialSourceKind.DIANN:
            report = build_diann_differential_analysis_report(
                input_path,
                design_report.accepted_entries,
                config_path=config_path,
                max_q_value=max_q_value,
                normalization_method=NormalizationMethod(normalization),
                condition_a=condition_a,
                condition_b=condition_b,
                batch_field=design_batch_field,
                covariate_fields=tuple(dict.fromkeys(design_covariates)),
                pairing_field=design_pairing_field,
            )
        else:
            report = build_spectronaut_differential_analysis_report(
                input_path,
                design_report.accepted_entries,
                config_path=config_path,
                max_q_value=max_q_value,
                normalization_method=NormalizationMethod(normalization),
                condition_a=condition_a,
                condition_b=condition_b,
                batch_field=design_batch_field,
                covariate_fields=tuple(dict.fromkeys(design_covariates)),
                pairing_field=design_pairing_field,
            )
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
        volcano_plot = build_dia_differential_volcano_plot(
            report.differential_abundance_report,
            protein_refs_by_entity=report.input_report.table.entity_protein_refs,
            adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
            absolute_log2_fold_change_threshold=(
                volcano_absolute_log2_fold_change_threshold
            ),
        )
        volcano_review = build_dia_volcano_review(
            volcano_plot,
            policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
                absolute_log2_fold_change_threshold=(
                    volcano_absolute_log2_fold_change_threshold
                ),
                top_label_count=volcano_top_label_count,
            ),
        )

    if matrix_tsv_out is not None:
        export_dia_differential_matrix_tsv(report.input_report.table, matrix_tsv_out)
    if normalized_matrix_tsv_out is not None:
        export_dia_differential_matrix_tsv(report.normalized_table, normalized_matrix_tsv_out)
    if differential_tsv_out is not None:
        export_dia_differential_results_tsv(report, differential_tsv_out)
    if qc_summary_tsv_out is not None:
        export_dia_differential_qc_summary_tsv(report, qc_summary_tsv_out)
    if design_matrix_tsv_out is not None:
        export_quant_design_matrix_tsv(report.design_matrix, design_matrix_tsv_out)
    if design_coefficients_tsv_out is not None:
        export_quant_design_model_coefficients_tsv(
            report.design_model_fit,
            design_coefficients_tsv_out,
        )
    if sample_balance_tsv_out is not None:
        export_dia_normalization_balance_plot_tsv(
            report.normalization_balance_plot,
            sample_balance_tsv_out,
        )
    if volcano_tsv_out is not None:
        assert volcano_plot is not None
        export_dia_differential_volcano_plot_tsv(volcano_plot, volcano_tsv_out)
    if volcano_review is not None:
        _export_volcano_review_assets(
            review_report=volcano_review,
            json_out=volcano_json_out,
            svg_out=volcano_svg_out,
            html_out=volcano_html_out,
        )

    payload = {
        "source_kind": report.input_report.source_kind.value,
        "source_name": report.input_report.source_name,
        "matrix_summary": report.input_report.matrix_summary.to_dict(),
        "table": report.input_report.table.to_dict(),
        "normalized_table": report.normalized_table.to_dict(),
        "normalization_comparison": report.normalization_comparison.to_dict(),
        "design_matrix": report.design_matrix.to_dict(),
        "design_model_fit": report.design_model_fit.to_dict(),
        "qc_summary": report.qc_summary.to_dict(),
        "differential_abundance": (
            report.differential_abundance_report.to_dict()
            if report.differential_abundance_report is not None
            else None
        ),
        "differential_abundance_multi_condition": (
            report.differential_abundance_multi_condition_report.to_dict()
            if report.differential_abundance_multi_condition_report is not None
            else None
        ),
        "normalization_balance_plot": report.normalization_balance_plot.to_dict(),
        "volcano_plot": None if volcano_plot is None else volcano_plot.to_dict(),
        "volcano_review": (
            None if volcano_review is None else volcano_review.to_dict()
        ),
        "note": report.note,
        "outputs": {
            "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
            "normalized_matrix_tsv": (
                None if normalized_matrix_tsv_out is None else str(normalized_matrix_tsv_out)
            ),
            "differential_tsv": (
                None if differential_tsv_out is None else str(differential_tsv_out)
            ),
            "qc_summary_tsv": (
                None if qc_summary_tsv_out is None else str(qc_summary_tsv_out)
            ),
            "design_matrix_tsv": (
                None if design_matrix_tsv_out is None else str(design_matrix_tsv_out)
            ),
            "design_coefficients_tsv": (
                None
                if design_coefficients_tsv_out is None
                else str(design_coefficients_tsv_out)
            ),
            "volcano_tsv": None if volcano_tsv_out is None else str(volcano_tsv_out),
            "volcano_json": (
                None if volcano_json_out is None else str(volcano_json_out)
            ),
            "volcano_svg": None if volcano_svg_out is None else str(volcano_svg_out),
            "volcano_html": (
                None if volcano_html_out is None else str(volcano_html_out)
            ),
            "sample_balance_tsv": (
                None if sample_balance_tsv_out is None else str(sample_balance_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

@click.command("dia-dda-compare")
@click.argument(
    "diann_report_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "dda_psm_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--max-q-value", type=float, default=0.05, show_default=True)
@click.option(
    "--dia-differential-tsv",
    "dia_differential_tsv_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--dda-differential-tsv",
    "dda_differential_tsv_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--differential-significance-threshold",
    type=float,
    default=0.05,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-overlap-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-overlap-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--correlation-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--exclusive-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--conflicts-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--differential-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def dia_dda_compare_command(
    diann_report_path: Path,
    dda_psm_path: Path,
    max_q_value: float,
    dia_differential_tsv_path: Path | None,
    dda_differential_tsv_path: Path | None,
    differential_significance_threshold: float,
    summary_tsv_out: Path | None,
    protein_overlap_tsv_out: Path | None,
    peptide_overlap_tsv_out: Path | None,
    correlation_tsv_out: Path | None,
    exclusive_tsv_out: Path | None,
    conflicts_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Compare DIA-NN and DDA evidence, conflicts, and optional differential results.'
    return run_dia_dda_compare_command(diann_report_path, dda_psm_path, max_q_value, dia_differential_tsv_path, dda_differential_tsv_path, differential_significance_threshold, summary_tsv_out, protein_overlap_tsv_out, peptide_overlap_tsv_out, correlation_tsv_out, exclusive_tsv_out, conflicts_tsv_out, differential_tsv_out, out_path)

def run_dia_dda_compare_command(
    diann_report_path: Path,
    dda_psm_path: Path,
    max_q_value: float,
    dia_differential_tsv_path: Path | None,
    dda_differential_tsv_path: Path | None,
    differential_significance_threshold: float,
    summary_tsv_out: Path | None,
    protein_overlap_tsv_out: Path | None,
    peptide_overlap_tsv_out: Path | None,
    correlation_tsv_out: Path | None,
    exclusive_tsv_out: Path | None,
    conflicts_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        comparison_report = build_diann_vs_dda_psm_comparison_report(
            diann_report_path,
            dda_psm_path,
            max_q_value=max_q_value,
            dia_differential_tsv_path=dia_differential_tsv_path,
            dda_differential_tsv_path=dda_differential_tsv_path,
            differential_significance_threshold=differential_significance_threshold,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_dda_comparison_summary_tsv(comparison_report),
        )
    if protein_overlap_tsv_out is not None:
        _write_text_output(
            protein_overlap_tsv_out,
            render_dia_dda_protein_overlap_tsv(comparison_report),
        )
    if peptide_overlap_tsv_out is not None:
        _write_text_output(
            peptide_overlap_tsv_out,
            render_dia_dda_peptide_overlap_tsv(comparison_report),
        )
    if correlation_tsv_out is not None:
        _write_text_output(
            correlation_tsv_out,
            render_dia_dda_shared_intensity_correlation_tsv(comparison_report),
        )
    if exclusive_tsv_out is not None:
        _write_text_output(
            exclusive_tsv_out,
            render_dia_dda_exclusive_evidence_tsv(comparison_report),
        )
    if conflicts_tsv_out is not None:
        _write_text_output(
            conflicts_tsv_out,
            render_dia_dda_conflicting_evidence_tsv(comparison_report),
        )
    if differential_tsv_out is not None:
        _write_text_output(
            differential_tsv_out,
            render_dia_dda_differential_comparison_tsv(comparison_report),
        )

    payload = {
        "dia_source_name": comparison_report.dia_source_name,
        "dda_source_name": comparison_report.dda_source_name,
        "summary": comparison_report.summary.to_dict(),
        "protein_overlap": [entry.to_dict() for entry in comparison_report.protein_overlap],
        "peptide_overlap": [entry.to_dict() for entry in comparison_report.peptide_overlap],
        "shared_intensity_correlation": [
            entry.to_dict() for entry in comparison_report.shared_intensity_correlation
        ],
        "exclusive_evidence": [
            entry.to_dict() for entry in comparison_report.exclusive_evidence
        ],
        "conflicting_evidence": [
            entry.to_dict() for entry in comparison_report.conflicting_evidence
        ],
        "differential_comparison": [
            entry.to_dict() for entry in comparison_report.differential_comparison
        ],
        "note": comparison_report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "protein_overlap_tsv": (
                None
                if protein_overlap_tsv_out is None
                else str(protein_overlap_tsv_out)
            ),
            "peptide_overlap_tsv": (
                None
                if peptide_overlap_tsv_out is None
                else str(peptide_overlap_tsv_out)
            ),
            "correlation_tsv": (
                None if correlation_tsv_out is None else str(correlation_tsv_out)
            ),
            "exclusive_tsv": (
                None if exclusive_tsv_out is None else str(exclusive_tsv_out)
            ),
            "conflicts_tsv": (
                None if conflicts_tsv_out is None else str(conflicts_tsv_out)
            ),
            "differential_tsv": (
                None
                if differential_tsv_out is None
                else str(differential_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

@click.command("target-panel-review")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "panel_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetPanelSourceKind]),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--target-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--missing-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--intensity-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def target_panel_review_command(
    input_path: Path,
    panel_path: Path,
    source_kind: str,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    summary_tsv_out: Path | None,
    target_tsv_out: Path | None,
    missing_tsv_out: Path | None,
    intensity_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Review a user-defined peptide or protein panel against DIA or LFQ matrices.'
    return run_target_panel_review_command(input_path, panel_path, source_kind, config_path, include_decoys, max_q_value, summary_tsv_out, target_tsv_out, missing_tsv_out, intensity_tsv_out, matrix_tsv_out, out_path)

def run_target_panel_review_command(
    input_path: Path,
    panel_path: Path,
    source_kind: str,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    summary_tsv_out: Path | None,
    target_tsv_out: Path | None,
    missing_tsv_out: Path | None,
    intensity_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        selected_source = TargetPanelSourceKind(source_kind)
        if selected_source is TargetPanelSourceKind.DIA_PEPTIDE:
            report = build_diann_peptide_target_panel_report(
                input_path,
                panel_path,
                config_path=config_path,
                include_decoys=include_decoys,
                max_q_value=max_q_value,
            )
        elif selected_source is TargetPanelSourceKind.DIA_PROTEIN:
            report = build_diann_protein_target_panel_report(
                input_path,
                panel_path,
                config_path=config_path,
                include_decoys=include_decoys,
                max_q_value=max_q_value,
            )
        elif selected_source is TargetPanelSourceKind.LFQ_PEPTIDE:
            report = build_lfq_peptide_target_panel_report(input_path, panel_path)
        elif selected_source is TargetPanelSourceKind.LFQ_PROTEIN:
            report = build_lfq_protein_target_panel_report(input_path, panel_path)
        else:
            report = build_lfq_protein_lfq_target_panel_report(input_path, panel_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_target_panel_summary_tsv(report))
    if target_tsv_out is not None:
        _write_text_output(target_tsv_out, render_target_panel_target_tsv(report))
    if missing_tsv_out is not None:
        _write_text_output(missing_tsv_out, render_target_panel_missing_tsv(report))
    if intensity_tsv_out is not None:
        _write_text_output(
            intensity_tsv_out,
            render_target_panel_intensity_tsv(report),
        )
    if matrix_tsv_out is not None:
        _write_text_output(matrix_tsv_out, render_target_panel_matrix_tsv(report))

    payload = {
        "source_kind": report.source_kind.value,
        "source_name": report.source_name,
        "sample_ids": list(report.sample_ids),
        "summary": report.summary.to_dict(),
        "matched_targets": [entry.to_dict() for entry in report.matched_targets],
        "missing_targets": [entry.to_dict() for entry in report.missing_targets],
        "filtered_rows": [row.to_dict() for row in report.filtered_rows],
        "intensity_entries": [entry.to_dict() for entry in report.intensity_entries],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "target_tsv": None if target_tsv_out is None else str(target_tsv_out),
            "missing_tsv": None if missing_tsv_out is None else str(missing_tsv_out),
            "intensity_tsv": (
                None if intensity_tsv_out is None else str(intensity_tsv_out)
            ),
            "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)

COMMANDS = (
    dia_differential_command,
    dia_dda_compare_command,
    target_panel_review_command,
)
