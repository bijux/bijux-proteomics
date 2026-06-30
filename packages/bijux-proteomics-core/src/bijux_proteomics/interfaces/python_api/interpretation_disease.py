# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Interpretation disease Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.interpretation import (
    BiologicalContextColumnMapping,
    DiseasePhenotypeInterpretationPolicy,
    build_disease_phenotype_interpretation_report,
    parse_biological_context_table,
    render_disease_phenotype_interpretation_summary_tsv,
    render_disease_phenotype_interpretation_tsv,
    render_rejected_biological_context_tsv,
    render_unknown_disease_phenotype_annotation_tsv,
)
from bijux_proteomics.interfaces.support.io_and_dia import parse_experimental_design_table
from bijux_proteomics.interfaces.support.ptm_quantification.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
)
from bijux_proteomics.interfaces.support.contrast_resolution import _resolve_cli_contrast


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
        write_output_table_tsv(
            summary_tsv_out, render_disease_phenotype_interpretation_summary_tsv(report)
        )
    if interpretation_tsv_out is not None:
        write_output_table_tsv(
            interpretation_tsv_out, render_disease_phenotype_interpretation_tsv(report)
        )
    if unknown_annotation_tsv_out is not None:
        write_output_table_tsv(
            unknown_annotation_tsv_out,
            render_unknown_disease_phenotype_annotation_tsv(report),
        )
    if rejected_context_tsv_out is not None:
        write_output_table_tsv(
            rejected_context_tsv_out,
            render_rejected_biological_context_tsv(context_report),
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


__all__ = ["run_disease_phenotype_command"]
