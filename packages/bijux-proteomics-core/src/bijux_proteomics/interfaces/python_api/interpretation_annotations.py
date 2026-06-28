# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Interpretation annotation Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.interpretation import (
    BiologicalContextColumnMapping,
    BiologicalContextKind,
    ProteinAnnotationColumnMapping,
    ProteinReferenceColumnMapping,
    build_biological_context_mapping_report,
    build_protein_annotation_mapping_report,
    parse_biological_context_table,
    parse_protein_annotation_table,
    parse_protein_reference_table,
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_protein_annotation_summary_tsv,
    render_protein_annotation_tsv,
    render_rejected_biological_context_tsv,
    render_rejected_protein_annotation_tsv,
    render_rejected_protein_reference_tsv,
    render_unmapped_biological_context_tsv,
    render_unmapped_protein_annotation_tsv,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FastaParseMode,
    parse_fasta_document,
)
from bijux_proteomics.interfaces.support.output_protocol import (
    _emit_json,
)


def run_annotate_proteins_command(
    protein_tsv: Path,
    proteins_fasta: Path,
    annotation_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    annotation_protein_ref_column: str,
    annotation_gene_symbol_column: str,
    annotation_description_column: str,
    annotation_organism_column: str,
    annotation_identifier_column: str,
    summary_tsv_out: Path | None,
    annotated_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    rejected_input_tsv_out: Path | None,
    rejected_annotation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        protein_table = parse_protein_reference_table(
            protein_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(encoding="utf-8"),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
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
        mapping_report = build_protein_annotation_mapping_report(
            protein_table.accepted_entries,
            fasta_report.accepted_records,
            custom_annotations=()
            if annotation_report is None
            else annotation_report.accepted_records,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(
            summary_tsv_out, render_protein_annotation_summary_tsv(mapping_report)
        )
    if annotated_tsv_out is not None:
        write_output_table_tsv(
            annotated_tsv_out, render_protein_annotation_tsv(mapping_report)
        )
    if unmapped_tsv_out is not None:
        write_output_table_tsv(
            unmapped_tsv_out, render_unmapped_protein_annotation_tsv(mapping_report)
        )
    if rejected_input_tsv_out is not None:
        write_output_table_tsv(
            rejected_input_tsv_out, render_rejected_protein_reference_tsv(protein_table)
        )
    if rejected_annotation_tsv_out is not None and annotation_report is not None:
        write_output_table_tsv(
            rejected_annotation_tsv_out,
            render_rejected_protein_annotation_tsv(annotation_report),
        )

    payload = {
        "protein_table": protein_table.to_dict(),
        "annotation_table": (
            None if annotation_report is None else annotation_report.to_dict()
        ),
        "mapping_report": mapping_report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "annotated_tsv": (
                None if annotated_tsv_out is None else str(annotated_tsv_out)
            ),
            "unmapped_tsv": None if unmapped_tsv_out is None else str(unmapped_tsv_out),
            "rejected_input_tsv": (
                None if rejected_input_tsv_out is None else str(rejected_input_tsv_out)
            ),
            "rejected_annotation_tsv": (
                None
                if rejected_annotation_tsv_out is None or annotation_report is None
                else str(rejected_annotation_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_map_context_command(
    protein_tsv: Path,
    context_tsv: Path,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    context_protein_ref_column: str,
    context_id_column: str,
    context_kind_column: str,
    context_name_column: str,
    source_name_column: str,
    source_accession_column: str,
    evidence_column: str,
    fixed_context_kind: str | None,
    summary_tsv_out: Path | None,
    mapped_tsv_out: Path | None,
    term_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    rejected_input_tsv_out: Path | None,
    rejected_context_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        protein_table = parse_protein_reference_table(
            protein_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        context_table = parse_biological_context_table(
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
            fixed_context_kind=(
                None
                if fixed_context_kind is None
                else BiologicalContextKind(fixed_context_kind)
            ),
        )
        mapping_report = build_biological_context_mapping_report(
            protein_table.accepted_entries,
            context_table.accepted_records,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(
            summary_tsv_out,
            render_biological_context_mapping_summary_tsv(mapping_report),
        )
    if mapped_tsv_out is not None:
        write_output_table_tsv(
            mapped_tsv_out, render_biological_context_mapping_tsv(mapping_report)
        )
    if term_tsv_out is not None:
        write_output_table_tsv(
            term_tsv_out, render_biological_context_term_tsv(mapping_report)
        )
    if unmapped_tsv_out is not None:
        write_output_table_tsv(
            unmapped_tsv_out, render_unmapped_biological_context_tsv(mapping_report)
        )
    if rejected_input_tsv_out is not None:
        write_output_table_tsv(
            rejected_input_tsv_out, render_rejected_protein_reference_tsv(protein_table)
        )
    if rejected_context_tsv_out is not None:
        write_output_table_tsv(
            rejected_context_tsv_out,
            render_rejected_biological_context_tsv(context_table),
        )

    payload = {
        "protein_table": protein_table.to_dict(),
        "context_table": context_table.to_dict(),
        "mapping_report": mapping_report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "mapped_tsv": None if mapped_tsv_out is None else str(mapped_tsv_out),
            "term_tsv": None if term_tsv_out is None else str(term_tsv_out),
            "unmapped_tsv": None if unmapped_tsv_out is None else str(unmapped_tsv_out),
            "rejected_input_tsv": (
                None if rejected_input_tsv_out is None else str(rejected_input_tsv_out)
            ),
            "rejected_context_tsv": (
                None
                if rejected_context_tsv_out is None
                else str(rejected_context_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = ["run_annotate_proteins_command", "run_map_context_command"]
