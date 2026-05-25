# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation context Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405

def run_compartment_biology_command(
    input_table: Path,
    context_annotation_tsv: Path,
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
    protein_ref_column: str,
    context_id_column: str,
    context_kind_column: str,
    context_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    evidence_column: str,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    min_enrichment_ratio: float,
    minimum_observed_member_count: int,
    summary_tsv_out: Path | None,
    enrichment_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    sample_score_tsv_out: Path | None,
    condition_score_tsv_out: Path | None,
    condition_comparison_tsv_out: Path | None,
    unresolved_member_tsv_out: Path | None,
    unknown_localization_tsv_out: Path | None,
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
            context_annotation_tsv,
            mapping=BiologicalContextColumnMapping(
                protein_ref=protein_ref_column,
                context_id=context_id_column,
                context_kind=context_kind_column,
                context_name=context_name_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
                evidence=evidence_column,
            ),
        )
        report = build_compartment_biology_report(
            normalized_table,
            differential_report,
            context_report.accepted_records,
            design_entries=design_entries,
            policy=CompartmentBiologyPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                min_enrichment_ratio=min_enrichment_ratio,
                minimum_observed_member_count=minimum_observed_member_count,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_compartment_biology_summary_tsv(report),
            encoding="utf-8",
        )
    if enrichment_tsv_out is not None:
        enrichment_tsv_out.write_text(
            render_compartment_enrichment_tsv(report),
            encoding="utf-8",
        )
    if matrix_tsv_out is not None:
        matrix_tsv_out.write_text(
            render_compartment_activity_matrix_tsv(report),
            encoding="utf-8",
        )
    if sample_score_tsv_out is not None:
        sample_score_tsv_out.write_text(
            render_compartment_activity_sample_score_tsv(report),
            encoding="utf-8",
        )
    if condition_score_tsv_out is not None:
        condition_score_tsv_out.write_text(
            render_compartment_activity_condition_score_tsv(report),
            encoding="utf-8",
        )
    if condition_comparison_tsv_out is not None:
        condition_comparison_tsv_out.write_text(
            render_compartment_activity_condition_comparison_tsv(report),
            encoding="utf-8",
        )
    if unresolved_member_tsv_out is not None:
        unresolved_member_tsv_out.write_text(
            render_compartment_activity_unresolved_member_tsv(report),
            encoding="utf-8",
        )
    if unknown_localization_tsv_out is not None:
        unknown_localization_tsv_out.write_text(
            render_unknown_compartment_localization_tsv(report),
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
            "enrichment_tsv": (
                None if enrichment_tsv_out is None else str(enrichment_tsv_out)
            ),
            "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
            "sample_score_tsv": (
                None if sample_score_tsv_out is None else str(sample_score_tsv_out)
            ),
            "condition_score_tsv": (
                None
                if condition_score_tsv_out is None
                else str(condition_score_tsv_out)
            ),
            "condition_comparison_tsv": (
                None
                if condition_comparison_tsv_out is None
                else str(condition_comparison_tsv_out)
            ),
            "unresolved_member_tsv": (
                None
                if unresolved_member_tsv_out is None
                else str(unresolved_member_tsv_out)
            ),
            "unknown_localization_tsv": (
                None
                if unknown_localization_tsv_out is None
                else str(unknown_localization_tsv_out)
            ),
            "rejected_context_tsv": (
                None
                if rejected_context_tsv_out is None
                else str(rejected_context_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

def run_drug_target_command(
    input_table: Path,
    context_tsv: Path,
    design_path: Path,
    pathway_membership_tsv: Path | None,
    fasta: Path | None,
    annotation_tsv: Path | None,
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
    pathway_id_column: str,
    pathway_name_column: str,
    pathway_source_name_column: str,
    pathway_source_accession_column: str,
    pathway_protein_ref_column: str,
    pathway_gene_symbol_column: str,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    summary_tsv_out: Path | None,
    interpretation_tsv_out: Path | None,
    rejected_context_tsv_out: Path | None,
    rejected_pathway_tsv_out: Path | None,
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
        pathway_report = (
            None
            if pathway_membership_tsv is None
            else parse_pathway_membership_table(
                pathway_membership_tsv,
                mapping=PathwayMembershipColumnMapping(
                    pathway_id=pathway_id_column,
                    pathway_name=pathway_name_column,
                    source_name=pathway_source_name_column,
                    source_accession=pathway_source_accession_column,
                    protein_ref=pathway_protein_ref_column,
                    gene_symbol=pathway_gene_symbol_column,
                ),
            )
        )
        fasta_records = ()
        if fasta is not None:
            fasta_report = parse_fasta_document(
                fasta.read_text(encoding="utf-8"),
                mode=FastaParseMode.STRICT,
            )
            if fasta_report.rejected_records:
                raise click.ClickException("FASTA input contains rejected records")
            fasta_records = fasta_report.accepted_records
        custom_annotations = ()
        if annotation_tsv is not None:
            annotation_report = parse_protein_annotation_table(
                annotation_tsv,
                mapping=ProteinAnnotationColumnMapping(
                    protein_ref="protein_ref",
                    gene_symbol="gene_symbol",
                    description="description",
                    organism="organism",
                    annotation_identifier="annotation_identifier",
                ),
            )
            custom_annotations = annotation_report.accepted_records
        differential_reference_entries = tuple(
            ProteinReferenceEntry(
                row_number=index + 2,
                source_row_id=entry.entity_id,
                input_protein_ref=protein_ref,
                protein_ref=protein_ref,
            )
            for index, entry in enumerate(differential_report.entries)
            for protein_ref in normalized_table.entity_protein_refs.get(
                entry.entity_id, (entry.entity_id,)
            )
        )
        annotation_mapping_report = build_protein_annotation_mapping_report(
            differential_reference_entries,
            fasta_records,
            custom_annotations=custom_annotations,
        )
        report = build_drug_target_interpretation_report(
            normalized_table,
            differential_report,
            context_report.accepted_records,
            pathway_records=()
            if pathway_report is None
            else pathway_report.accepted_records,
            annotation_report=annotation_mapping_report,
            policy=DrugTargetInterpretationPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_drug_target_interpretation_summary_tsv(report),
            encoding="utf-8",
        )
    if interpretation_tsv_out is not None:
        interpretation_tsv_out.write_text(
            render_drug_target_interpretation_tsv(report),
            encoding="utf-8",
        )
    if rejected_context_tsv_out is not None:
        rejected_context_tsv_out.write_text(
            render_rejected_biological_context_tsv(context_report),
            encoding="utf-8",
        )
    if rejected_pathway_tsv_out is not None:
        rejected_pathway_tsv_out.write_text(
            ""
            if pathway_report is None
            else render_rejected_pathway_membership_tsv(pathway_report),
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
        "pathway_report": None if pathway_report is None else pathway_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "interpretation_tsv": (
                None if interpretation_tsv_out is None else str(interpretation_tsv_out)
            ),
            "rejected_context_tsv": (
                None
                if rejected_context_tsv_out is None
                else str(rejected_context_tsv_out)
            ),
            "rejected_pathway_tsv": (
                None
                if rejected_pathway_tsv_out is None
                else str(rejected_pathway_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

__all__ = ['run_compartment_biology_command', 'run_drug_target_command']
