# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation disease CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("disease-phenotype")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "context_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--design-path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--aggregation",
    type=click.Choice([method.value for method in QuantRollupMethod]),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=click.Choice([method.value for method in NormalizationMethod]),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--context-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--context-id-column", default="context_id", show_default=True)
@click.option("--context-kind-column", default="context_kind", show_default=True)
@click.option("--context-name-column", default="context_name", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--evidence-column", default="evidence", show_default=True)
@click.option(
    "--max-adjusted-p-value",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--min-absolute-log2-fold-change",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--min-enrichment-ratio",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--high-confidence-min-supporting-protein-count",
    type=int,
    default=2,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--interpretation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unknown-annotation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-context-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def disease_phenotype_command(
    input_table: Path,
    context_tsv: Path,
    design_path: Path,
    condition_a: str | None,
    condition_b: str | None,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    context_protein_ref_column: str,
    context_id_column: str,
    context_kind_column: str,
    context_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    evidence_column: str,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    min_enrichment_ratio: float,
    high_confidence_min_supporting_protein_count: int,
    summary_tsv_out: Path | None,
    interpretation_tsv_out: Path | None,
    unknown_annotation_tsv_out: Path | None,
    rejected_context_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Interpret changed proteins through explicit disease and phenotype annotation.'
    return run_disease_phenotype_command(input_table, context_tsv, design_path, condition_a, condition_b, sample_column, feature_id_column, peptide_column, intensity_column, protein_refs_column, charge_column, mz_column, retention_time_column, missing_reason_column, protein_separator, aggregation, top_n, normalization, context_protein_ref_column, context_id_column, context_kind_column, context_name_column, source_name_column, source_accession_column, evidence_column, max_adjusted_p_value, min_absolute_log2_fold_change, min_enrichment_ratio, high_confidence_min_supporting_protein_count, summary_tsv_out, interpretation_tsv_out, unknown_annotation_tsv_out, rejected_context_tsv_out, out_path)

def run_disease_phenotype_command(
    input_table: Path,
    context_tsv: Path,
    design_path: Path,
    condition_a: str | None,
    condition_b: str | None,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    context_protein_ref_column: str,
    context_id_column: str,
    context_kind_column: str,
    context_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    evidence_column: str,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    min_enrichment_ratio: float,
    high_confidence_min_supporting_protein_count: int,
    summary_tsv_out: Path | None,
    interpretation_tsv_out: Path | None,
    unknown_annotation_tsv_out: Path | None,
    rejected_context_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(input_table, mapping=mapping)
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        design_entries = design_report.accepted_entries
        resolved_condition_a, resolved_condition_b = _resolve_cli_contrast(
            design_entries,
            condition_a=condition_a,
            condition_b=condition_b,
        )
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        normalized_table = normalize_label_free_table(
            raw_table,
            method=NormalizationMethod(normalization),
        )
        differential_report = apply_benjamini_hochberg(
            build_differential_abundance_report(
                normalized_table,
                design_entries,
                condition_a=resolved_condition_a,
                condition_b=resolved_condition_b,
            )
        )
        context_report = parse_biological_context_table(
            context_tsv,
            mapping=BiologicalContextColumnMapping(
                protein_ref=context_protein_ref_column,
                context_id=context_id_column,
                context_kind=context_kind_column,
                context_name=context_name_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
                evidence=evidence_column,
            ),
        )
        report = build_disease_phenotype_interpretation_report(
            normalized_table,
            differential_report,
            context_report.accepted_records,
            policy=DiseasePhenotypeInterpretationPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                min_enrichment_ratio=min_enrichment_ratio,
                high_confidence_min_supporting_protein_count=(
                    high_confidence_min_supporting_protein_count
                ),
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_disease_phenotype_interpretation_summary_tsv(report),
            encoding="utf-8",
        )
    if interpretation_tsv_out is not None:
        interpretation_tsv_out.write_text(
            render_disease_phenotype_interpretation_tsv(report),
            encoding="utf-8",
        )
    if unknown_annotation_tsv_out is not None:
        unknown_annotation_tsv_out.write_text(
            render_unknown_disease_phenotype_annotation_tsv(report),
            encoding="utf-8",
        )
    if rejected_context_tsv_out is not None:
        rejected_context_tsv_out.write_text(
            render_rejected_biological_context_tsv(context_report),
            encoding="utf-8",
        )

    payload = {
        "accepted_features": len(parse_report.accepted_records),
        "rejected_features": len(parse_report.rejected_rows),
        "contrast": {
            "condition_a": resolved_condition_a,
            "condition_b": resolved_condition_b,
        },
        "context_report": context_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "interpretation_tsv": (
                None if interpretation_tsv_out is None else str(interpretation_tsv_out)
            ),
            "unknown_annotation_tsv": (
                None
                if unknown_annotation_tsv_out is None
                else str(unknown_annotation_tsv_out)
            ),
            "rejected_context_tsv": (
                None
                if rejected_context_tsv_out is None
                else str(rejected_context_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

COMMANDS = (
    disease_phenotype_command,
)
