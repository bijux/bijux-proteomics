# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Interpretation annotation CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.interpretation_annotations import (
    run_annotate_proteins_command,
    run_map_context_command,
)
from bijux_proteomics.interfaces.support.interpretation import BiologicalContextKind


@click.command("annotate-proteins")
@click.argument(
    "protein_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--annotation-protein-ref-column",
    default="protein_ref",
    show_default=True,
)
@click.option(
    "--annotation-gene-symbol-column",
    default="gene_symbol",
    show_default=True,
)
@click.option(
    "--annotation-description-column",
    default="description",
    show_default=True,
)
@click.option(
    "--annotation-organism-column",
    default="organism",
    show_default=True,
)
@click.option(
    "--annotation-identifier-column",
    default="annotation_identifier",
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--annotated-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unmapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-input-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-annotation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def annotate_proteins_command(
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
    """Map protein tables onto FASTA and optional custom biological annotations."""
    return run_annotate_proteins_command(
        protein_tsv,
        proteins_fasta,
        annotation_tsv,
        protein_ref_column,
        row_id_column,
        protein_separator,
        annotation_protein_ref_column,
        annotation_gene_symbol_column,
        annotation_description_column,
        annotation_organism_column,
        annotation_identifier_column,
        summary_tsv_out,
        annotated_tsv_out,
        unmapped_tsv_out,
        rejected_input_tsv_out,
        rejected_annotation_tsv_out,
        out_path,
    )


@click.command("map-context")
@click.argument(
    "protein_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "context_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--context-protein-ref-column",
    default="protein_ref",
    show_default=True,
)
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
    "--fixed-context-kind",
    type=click.Choice([kind.value for kind in BiologicalContextKind]),
    default=None,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--mapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--term-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unmapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-input-tsv-out",
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
def map_context_command(
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
    """Map protein tables onto user-supplied drug, disease, phenotype, or compartment context."""
    return run_map_context_command(
        protein_tsv,
        context_tsv,
        protein_ref_column,
        row_id_column,
        protein_separator,
        context_protein_ref_column,
        context_id_column,
        context_kind_column,
        context_name_column,
        source_name_column,
        source_accession_column,
        evidence_column,
        fixed_context_kind,
        summary_tsv_out,
        mapped_tsv_out,
        term_tsv_out,
        unmapped_tsv_out,
        rejected_input_tsv_out,
        rejected_context_tsv_out,
        out_path,
    )


COMMANDS = (
    annotate_proteins_command,
    map_context_command,
)
