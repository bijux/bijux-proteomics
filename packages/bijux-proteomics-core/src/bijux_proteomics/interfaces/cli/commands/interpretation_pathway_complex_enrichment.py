# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation pathway and complex enrichment CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.interpretation_pathway_complex_enrichment import run_pathway_enrichment_command, run_complex_enrichment_command

@click.command("pathway-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "background_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "pathway_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--fasta",
    "proteins_fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--pathway-id-column", default="pathway_id", show_default=True)
@click.option("--pathway-name-column", default="pathway_name", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--pathway-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--gene-symbol-column", default="gene_symbol", show_default=True)
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
    "--max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--pathway-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unresolved-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-pathway-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def pathway_enrichment_command(
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
    'Run pathway enrichment over foreground and background protein sets.'
    return run_pathway_enrichment_command(foreground_tsv, background_tsv, pathway_tsv, proteins_fasta, annotation_tsv, protein_ref_column, row_id_column, protein_separator, pathway_id_column, pathway_name_column, source_name_column, source_accession_column, pathway_protein_ref_column, gene_symbol_column, annotation_protein_ref_column, annotation_gene_symbol_column, annotation_description_column, annotation_organism_column, annotation_identifier_column, max_adjusted_p_value, min_enrichment_ratio, summary_tsv_out, pathway_tsv_out, unresolved_tsv_out, rejected_pathway_tsv_out, out_path)

@click.command("complex-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "background_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "complex_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--fasta",
    "proteins_fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--complex-id-column", default="complex_id", show_default=True)
@click.option("--complex-name-column", default="complex_name", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--complex-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--gene-symbol-column", default="gene_symbol", show_default=True)
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
    "--max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--complex-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unresolved-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-complex-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def complex_enrichment_command(
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
    'Run protein complex enrichment over foreground and background protein sets.'
    return run_complex_enrichment_command(foreground_tsv, background_tsv, complex_tsv, proteins_fasta, annotation_tsv, protein_ref_column, row_id_column, protein_separator, complex_id_column, complex_name_column, source_name_column, source_accession_column, complex_protein_ref_column, gene_symbol_column, annotation_protein_ref_column, annotation_gene_symbol_column, annotation_description_column, annotation_organism_column, annotation_identifier_column, max_adjusted_p_value, min_enrichment_ratio, summary_tsv_out, complex_tsv_out, unresolved_tsv_out, rejected_complex_tsv_out, out_path)

COMMANDS = (
    pathway_enrichment_command,
    complex_enrichment_command,
)
