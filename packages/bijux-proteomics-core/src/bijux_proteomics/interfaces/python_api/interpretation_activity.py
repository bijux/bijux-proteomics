# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Interpretation activity Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.interpretation import (
    ComplexActivityPolicy,
    ComplexMembershipColumnMapping,
    PathwayActivityPolicy,
    PathwayMembershipColumnMapping,
    ProteinAnnotationColumnMapping,
    build_complex_activity_report,
    build_pathway_activity_report,
    parse_complex_membership_table,
    parse_pathway_membership_table,
    parse_protein_annotation_table,
    render_complex_activity_condition_comparison_tsv,
    render_complex_activity_condition_score_tsv,
    render_complex_activity_matrix_tsv,
    render_complex_activity_sample_score_tsv,
    render_complex_activity_summary_tsv,
    render_complex_activity_unresolved_member_tsv,
    render_complex_member_contribution_tsv,
    render_pathway_activity_condition_comparison_tsv,
    render_pathway_activity_condition_score_tsv,
    render_pathway_activity_matrix_tsv,
    render_pathway_activity_sample_score_tsv,
    render_pathway_activity_summary_tsv,
    render_pathway_activity_unresolved_member_tsv,
    render_pathway_member_contribution_tsv,
    render_rejected_complex_membership_tsv,
    render_rejected_pathway_membership_tsv,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.interfaces.support.ptm_quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FastaParseMode,
    NormalizedProteinRecord,
    parse_fasta_document,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
)


def run_pathway_activity_command(
    input_table: Path,
    pathway_membership_tsv: Path,
    design_path: Path | None,
    fasta: Path | None,
    annotation_tsv: Path | None,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str,
    charge_column: str,
    mz_column: str,
    retention_time_column: str,
    missing_reason_column: str,
    protein_separator: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    pathway_id_column: str,
    pathway_name_column: str,
    pathway_source_name_column: str,
    pathway_source_accession_column: str,
    pathway_protein_ref_column: str,
    pathway_gene_symbol_column: str,
    minimum_observed_member_count: int,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    sample_score_tsv_out: Path | None,
    condition_score_tsv_out: Path | None,
    condition_comparison_tsv_out: Path | None,
    member_contribution_tsv_out: Path | None,
    unresolved_member_tsv_out: Path | None,
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
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        pathway_memberships = parse_pathway_membership_table(
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
        fasta_records: tuple[NormalizedProteinRecord, ...] = ()
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
        report = build_pathway_activity_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            pathway_memberships.accepted_records,
            design_entries=design_entries,
            fasta_records=fasta_records,
            custom_annotations=custom_annotations,
            policy=PathwayActivityPolicy(
                minimum_observed_member_count=minimum_observed_member_count,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(
            summary_tsv_out, render_pathway_activity_summary_tsv(report)
        )
    if matrix_tsv_out is not None:
        write_output_table_tsv(
            matrix_tsv_out, render_pathway_activity_matrix_tsv(report)
        )
    if sample_score_tsv_out is not None:
        write_output_table_tsv(
            sample_score_tsv_out, render_pathway_activity_sample_score_tsv(report)
        )
    if condition_score_tsv_out is not None:
        write_output_table_tsv(
            condition_score_tsv_out, render_pathway_activity_condition_score_tsv(report)
        )
    if condition_comparison_tsv_out is not None:
        write_output_table_tsv(
            condition_comparison_tsv_out,
            render_pathway_activity_condition_comparison_tsv(report),
        )
    if member_contribution_tsv_out is not None:
        write_output_table_tsv(
            member_contribution_tsv_out, render_pathway_member_contribution_tsv(report)
        )
    if unresolved_member_tsv_out is not None:
        write_output_table_tsv(
            unresolved_member_tsv_out,
            render_pathway_activity_unresolved_member_tsv(report),
        )
    if rejected_pathway_tsv_out is not None:
        write_output_table_tsv(
            rejected_pathway_tsv_out,
            render_rejected_pathway_membership_tsv(pathway_memberships),
        )

    payload = {
        "accepted_features": len(parse_report.accepted_records),
        "rejected_features": len(parse_report.rejected_rows),
        "pathway_memberships": pathway_memberships.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
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
            "member_contribution_tsv": (
                None
                if member_contribution_tsv_out is None
                else str(member_contribution_tsv_out)
            ),
            "unresolved_member_tsv": (
                None
                if unresolved_member_tsv_out is None
                else str(unresolved_member_tsv_out)
            ),
            "rejected_pathway_tsv": (
                None
                if rejected_pathway_tsv_out is None
                else str(rejected_pathway_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_complex_activity_command(
    input_table: Path,
    complex_membership_tsv: Path,
    design_path: Path | None,
    fasta: Path | None,
    annotation_tsv: Path | None,
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
    normalization: str,
    top_n: int | None,
    complex_id_column: str,
    complex_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    complex_protein_ref_column: str,
    gene_symbol_column: str,
    minimum_observed_member_count: int,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    sample_score_tsv_out: Path | None,
    condition_score_tsv_out: Path | None,
    condition_comparison_tsv_out: Path | None,
    member_contribution_tsv_out: Path | None,
    unresolved_member_tsv_out: Path | None,
    rejected_complex_tsv_out: Path | None,
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
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        complex_memberships = parse_complex_membership_table(
            complex_membership_tsv,
            mapping=ComplexMembershipColumnMapping(
                complex_id=complex_id_column,
                complex_name=complex_name_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
                protein_ref=complex_protein_ref_column,
                gene_symbol=gene_symbol_column,
            ),
        )
        fasta_records: tuple[NormalizedProteinRecord, ...] = ()
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
        report = build_complex_activity_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            complex_memberships.accepted_records,
            design_entries=design_entries,
            fasta_records=fasta_records,
            custom_annotations=custom_annotations,
            policy=ComplexActivityPolicy(
                minimum_observed_member_count=minimum_observed_member_count,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(
            summary_tsv_out, render_complex_activity_summary_tsv(report)
        )
    if matrix_tsv_out is not None:
        write_output_table_tsv(
            matrix_tsv_out, render_complex_activity_matrix_tsv(report)
        )
    if sample_score_tsv_out is not None:
        write_output_table_tsv(
            sample_score_tsv_out, render_complex_activity_sample_score_tsv(report)
        )
    if condition_score_tsv_out is not None:
        write_output_table_tsv(
            condition_score_tsv_out, render_complex_activity_condition_score_tsv(report)
        )
    if condition_comparison_tsv_out is not None:
        write_output_table_tsv(
            condition_comparison_tsv_out,
            render_complex_activity_condition_comparison_tsv(report),
        )
    if member_contribution_tsv_out is not None:
        write_output_table_tsv(
            member_contribution_tsv_out, render_complex_member_contribution_tsv(report)
        )
    if unresolved_member_tsv_out is not None:
        write_output_table_tsv(
            unresolved_member_tsv_out,
            render_complex_activity_unresolved_member_tsv(report),
        )
    if rejected_complex_tsv_out is not None:
        write_output_table_tsv(
            rejected_complex_tsv_out,
            render_rejected_complex_membership_tsv(complex_memberships),
        )

    payload = {
        "accepted_features": len(parse_report.accepted_records),
        "rejected_features": len(parse_report.rejected_rows),
        "complex_memberships": complex_memberships.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
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
            "member_contribution_tsv": (
                None
                if member_contribution_tsv_out is None
                else str(member_contribution_tsv_out)
            ),
            "unresolved_member_tsv": (
                None
                if unresolved_member_tsv_out is None
                else str(unresolved_member_tsv_out)
            ),
            "rejected_complex_tsv": (
                None
                if rejected_complex_tsv_out is None
                else str(rejected_complex_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = ["run_pathway_activity_command", "run_complex_activity_command"]
