# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Stable-isotope labeling Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.io_and_dia import parse_experimental_design_table
from bijux_proteomics.interfaces.support.multiplex_targeted import (
    SilacColumnMapping,
    SilacLabel,
    SilacQuantificationPolicy,
    SilacValidationPolicy,
    TmtReporterColumnMapping,
    TmtSearchResultSourceKind,
    TmtValidationPolicy,
    build_silac_ratio_report,
    build_silac_validation_report,
    build_tmt_reporter_feature_bundle,
    build_tmt_validation_report,
    export_silac_peptide_ratio_tsv,
    export_silac_protein_ratio_tsv,
    export_silac_ratio_summary_tsv,
    export_silac_validation_distribution_tsv,
    export_silac_validation_label_tsv,
    export_silac_validation_summary_tsv,
    export_silac_validation_weak_tsv,
    export_tmt_validation_channel_tsv,
    export_tmt_validation_distribution_tsv,
    export_tmt_validation_summary_tsv,
    export_tmt_validation_weak_tsv,
    parse_silac_feature_table,
    parse_tmt_reporter_table,
)
from bijux_proteomics.interfaces.support.ptm_quantification import NormalizationMethod
from bijux_proteomics.interfaces.support.review_sequences_study import build_label_based_volcano_review
from bijux_proteomics.interfaces.support.workflow import (
    SilacWorkflowConfig,
    build_label_based_differential_volcano_plot,
    build_silac_differential_analysis_report,
    export_label_based_differential_matrix_tsv,
    export_label_based_differential_results_tsv,
    export_label_based_differential_volcano_plot_tsv,
    export_label_based_normalization_balance_plot_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol import (
    _build_volcano_review_policy,
    _emit_json,
    _export_volcano_review_assets,
    _run_orchestrated_workflow,
)
from bijux_proteomics.interfaces.support.sequence_support import (
    _parse_silac_label_spec,
    _parse_tmt_channel_column_specs,
)
from bijux_proteomics.workflow.pipelines.label_based_reporting import (
    LabelBasedReportBundle,
    LabelBasedReportExportManifest,
)


def run_silac_quantify_command(
    input_tsv: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    reference_label: str,
    collapse_charge_states: bool,
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        import_report = parse_silac_feature_table(
            input_tsv,
            mapping=SilacColumnMapping(
                sample_id=sample_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                label=label_column,
                intensity=intensity_column,
                feature_id=feature_id_column,
                protein_separator=protein_separator,
            ),
        )
        report = build_silac_ratio_report(
            import_report,
            policy=SilacQuantificationPolicy(
                expected_labels=_parse_silac_label_spec(labels),
                reference_label=SilacLabel(reference_label),
                separate_charge_states=not collapse_charge_states,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_silac_ratio_summary_tsv(report, summary_tsv_out)
    if peptide_tsv_out is not None:
        export_silac_peptide_ratio_tsv(report, peptide_tsv_out)
    if protein_tsv_out is not None:
        export_silac_protein_ratio_tsv(report, protein_tsv_out)

    payload = {
        "import_report": import_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_silac_differential_command(
    input_tsv: Path,
    design_path: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    reference_label: str,
    collapse_charge_states: bool,
    normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
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
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        report = build_silac_differential_analysis_report(
            input_tsv,
            tuple(design_report.accepted_entries),
            mapping=SilacColumnMapping(
                sample_id=sample_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                label=label_column,
                intensity=intensity_column,
                feature_id=feature_id_column,
                protein_separator=protein_separator,
            ),
            quantification_policy=SilacQuantificationPolicy(
                expected_labels=_parse_silac_label_spec(labels),
                reference_label=SilacLabel(reference_label),
                separate_charge_states=not collapse_charge_states,
            ),
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
            "results_tsv": (None if results_tsv_out is None else str(results_tsv_out)),
            "balance_tsv": (None if balance_tsv_out is None else str(balance_tsv_out)),
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


def run_silac_report_command(
    input_tsv: Path,
    design_path: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    reference_label: str,
    collapse_charge_states: bool,
    differential_normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    result = _run_orchestrated_workflow(
        SilacWorkflowConfig(
            input_tsv_path=input_tsv,
            design_tsv_path=design_path,
            mapping=SilacColumnMapping(
                sample_id=sample_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                label=label_column,
                intensity=intensity_column,
                feature_id=feature_id_column,
                protein_separator=protein_separator,
            ),
            quantification_policy=SilacQuantificationPolicy(
                expected_labels=_parse_silac_label_spec(labels),
                reference_label=SilacLabel(reference_label),
                separate_charge_states=not collapse_charge_states,
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
    report = result.report
    manifest = result.export_manifest
    if not isinstance(report, LabelBasedReportBundle):
        raise click.ClickException(
            "workflow did not produce the expected SILAC workflow bundle"
        )
    if not isinstance(manifest, LabelBasedReportExportManifest):
        raise click.ClickException(
            "workflow did not produce the expected SILAC workflow manifest"
        )
    _emit_json(
        {
            "report": report.to_dict(),
            "export_manifest": manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


def run_silac_validate_command(
    input_tsv: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    collapse_charge_states: bool,
    summary_tsv_out: Path | None,
    label_tsv_out: Path | None,
    distribution_tsv_out: Path | None,
    weak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        import_report = parse_silac_feature_table(
            input_tsv,
            mapping=SilacColumnMapping(
                sample_id=sample_id_column,
                peptide=peptide_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                label=label_column,
                intensity=intensity_column,
                feature_id=feature_id_column,
                protein_separator=protein_separator,
            ),
        )
        report = build_silac_validation_report(
            import_report,
            policy=SilacValidationPolicy(
                expected_labels=_parse_silac_label_spec(labels),
                separate_charge_states=not collapse_charge_states,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_silac_validation_summary_tsv(report, summary_tsv_out)
    if label_tsv_out is not None:
        export_silac_validation_label_tsv(report, label_tsv_out)
    if distribution_tsv_out is not None:
        export_silac_validation_distribution_tsv(report, distribution_tsv_out)
    if weak_tsv_out is not None:
        export_silac_validation_weak_tsv(report, weak_tsv_out)

    payload = {
        "import_report": import_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "label_tsv": None if label_tsv_out is None else str(label_tsv_out),
            "distribution_tsv": (
                None if distribution_tsv_out is None else str(distribution_tsv_out)
            ),
            "weak_tsv": None if weak_tsv_out is None else str(weak_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_tmt_validate_command(
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
    channel_tsv_out: Path | None,
    distribution_tsv_out: Path | None,
    weak_tsv_out: Path | None,
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
        report = build_tmt_validation_report(
            feature_bundle,
            policy=TmtValidationPolicy(),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_tmt_validation_summary_tsv(report, summary_tsv_out)
    if channel_tsv_out is not None:
        export_tmt_validation_channel_tsv(report, channel_tsv_out)
    if distribution_tsv_out is not None:
        export_tmt_validation_distribution_tsv(report, distribution_tsv_out)
    if weak_tsv_out is not None:
        export_tmt_validation_weak_tsv(report, weak_tsv_out)

    payload = {
        "source_kind": import_report.source_kind.value,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "channel_tsv": None if channel_tsv_out is None else str(channel_tsv_out),
            "distribution_tsv": (
                None if distribution_tsv_out is None else str(distribution_tsv_out)
            ),
            "weak_tsv": None if weak_tsv_out is None else str(weak_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_silac_quantify_command",
    "run_silac_differential_command",
    "run_silac_report_command",
    "run_silac_validate_command",
    "run_tmt_validate_command",
]
