# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation pathway and complex enrichment Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405

def run_pathway_enrichment_command(
    foreground_tsv: Path,
    background_tsv: Path,
    pathway_tsv: Path,
    proteins_fasta: Path | None,
    annotation_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    pathway_id_column: str,
    pathway_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    pathway_protein_ref_column: str,
    gene_symbol_column: str,
    annotation_protein_ref_column: str,
    annotation_gene_symbol_column: str,
    annotation_description_column: str,
    annotation_organism_column: str,
    annotation_identifier_column: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    pathway_tsv_out: Path | None,
    unresolved_tsv_out: Path | None,
    rejected_pathway_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = parse_protein_reference_table(
            background_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        pathway_memberships = parse_pathway_membership_table(
            pathway_tsv,
            mapping=PathwayMembershipColumnMapping(
                pathway_id=pathway_id_column,
                pathway_name=pathway_name_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
                protein_ref=pathway_protein_ref_column,
                gene_symbol=gene_symbol_column,
            ),
        )
        fasta_report = (
            None
            if proteins_fasta is None
            else parse_fasta_document(
                proteins_fasta.read_text(encoding="utf-8"),
                mode=FastaParseMode.STRICT,
            )
        )
        if fasta_report is not None and fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        annotation_report = (
            None
            if annotation_tsv is None
            else parse_protein_annotation_table(
                annotation_tsv,
                mapping=ProteinAnnotationColumnMapping(
                    protein_ref=annotation_protein_ref_column,
                    gene_symbol=annotation_gene_symbol_column,
                    description=annotation_description_column,
                    organism=annotation_organism_column,
                    annotation_identifier=annotation_identifier_column,
                ),
            )
        )
        report = apply_pathway_enrichment_multiple_testing(
            build_pathway_enrichment_report(
                foreground.accepted_entries,
                background.accepted_entries,
                pathway_memberships.accepted_records,
                fasta_records=()
                if fasta_report is None
                else fasta_report.accepted_records,
                custom_annotations=()
                if annotation_report is None
                else annotation_report.accepted_records,
            ),
            policy=PathwayEnrichmentCorrectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(summary_tsv_out, render_pathway_enrichment_summary_tsv(report))
    if pathway_tsv_out is not None:
        write_output_table_tsv(pathway_tsv_out, render_pathway_enrichment_entry_tsv(report))
    if unresolved_tsv_out is not None:
        write_output_table_tsv(unresolved_tsv_out, render_pathway_unresolved_member_tsv(report))
    if rejected_pathway_tsv_out is not None:
        write_output_table_tsv(rejected_pathway_tsv_out, render_rejected_pathway_membership_tsv(pathway_memberships))

    payload = {
        "foreground": foreground.to_dict(),
        "background": background.to_dict(),
        "pathway_memberships": pathway_memberships.to_dict(),
        "annotation_table": (
            None if annotation_report is None else annotation_report.to_dict()
        ),
        "fasta_report": None if fasta_report is None else fasta_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "pathway_tsv": None if pathway_tsv_out is None else str(pathway_tsv_out),
            "unresolved_tsv": (
                None if unresolved_tsv_out is None else str(unresolved_tsv_out)
            ),
            "rejected_pathway_tsv": (
                None
                if rejected_pathway_tsv_out is None
                else str(rejected_pathway_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

def run_complex_enrichment_command(
    foreground_tsv: Path,
    background_tsv: Path,
    complex_tsv: Path,
    proteins_fasta: Path | None,
    annotation_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    complex_id_column: str,
    complex_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    complex_protein_ref_column: str,
    gene_symbol_column: str,
    annotation_protein_ref_column: str,
    annotation_gene_symbol_column: str,
    annotation_description_column: str,
    annotation_organism_column: str,
    annotation_identifier_column: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    complex_tsv_out: Path | None,
    unresolved_tsv_out: Path | None,
    rejected_complex_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = parse_protein_reference_table(
            background_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        complex_memberships = parse_complex_membership_table(
            complex_tsv,
            mapping=ComplexMembershipColumnMapping(
                complex_id=complex_id_column,
                complex_name=complex_name_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
                protein_ref=complex_protein_ref_column,
                gene_symbol=gene_symbol_column,
            ),
        )
        fasta_report = (
            None
            if proteins_fasta is None
            else parse_fasta_document(
                proteins_fasta.read_text(encoding="utf-8"),
                mode=FastaParseMode.STRICT,
            )
        )
        if fasta_report is not None and fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        annotation_report = (
            None
            if annotation_tsv is None
            else parse_protein_annotation_table(
                annotation_tsv,
                mapping=ProteinAnnotationColumnMapping(
                    protein_ref=annotation_protein_ref_column,
                    gene_symbol=annotation_gene_symbol_column,
                    description=annotation_description_column,
                    organism=annotation_organism_column,
                    annotation_identifier=annotation_identifier_column,
                ),
            )
        )
        report = apply_complex_enrichment_multiple_testing(
            build_complex_enrichment_report(
                foreground.accepted_entries,
                background.accepted_entries,
                complex_memberships.accepted_records,
                fasta_records=()
                if fasta_report is None
                else fasta_report.accepted_records,
                custom_annotations=()
                if annotation_report is None
                else annotation_report.accepted_records,
            ),
            policy=ComplexEnrichmentCorrectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(summary_tsv_out, render_complex_enrichment_summary_tsv(report))
    if complex_tsv_out is not None:
        write_output_table_tsv(complex_tsv_out, render_complex_enrichment_entry_tsv(report))
    if unresolved_tsv_out is not None:
        write_output_table_tsv(unresolved_tsv_out, render_complex_unresolved_member_tsv(report))
    if rejected_complex_tsv_out is not None:
        write_output_table_tsv(rejected_complex_tsv_out, render_rejected_complex_membership_tsv(complex_memberships))

    payload = {
        "foreground": foreground.to_dict(),
        "background": background.to_dict(),
        "complex_memberships": complex_memberships.to_dict(),
        "annotation_table": (
            None if annotation_report is None else annotation_report.to_dict()
        ),
        "fasta_report": None if fasta_report is None else fasta_report.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "complex_tsv": None if complex_tsv_out is None else str(complex_tsv_out),
            "unresolved_tsv": (
                None if unresolved_tsv_out is None else str(unresolved_tsv_out)
            ),
            "rejected_complex_tsv": (
                None
                if rejected_complex_tsv_out is None
                else str(rejected_complex_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

__all__ = ['run_pathway_enrichment_command', 'run_complex_enrichment_command']
