# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation mapping CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.interpretation_mapping import run_map_orthologs_command, run_protein_set_score_command

@click.command("map-orthologs")
@click.argument(
    "protein_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "ortholog_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--source-species", required=True)
@click.option("--target-species", required=True)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--ortholog-source-species-column",
    default="source_species",
    show_default=True,
)
@click.option(
    "--ortholog-source-protein-ref-column",
    default="source_protein_ref",
    show_default=True,
)
@click.option(
    "--ortholog-target-species-column",
    default="target_species",
    show_default=True,
)
@click.option(
    "--ortholog-target-protein-ref-column",
    default="target_protein_ref",
    show_default=True,
)
@click.option(
    "--ortholog-source-gene-symbol-column",
    default="source_gene_symbol",
    show_default=True,
)
@click.option(
    "--ortholog-target-gene-symbol-column",
    default="target_gene_symbol",
    show_default=True,
)
@click.option(
    "--ortholog-evidence-column",
    default="evidence",
    show_default=True,
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
    "--rejected-ortholog-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def map_orthologs_command(
    protein_tsv: Path,
    ortholog_tsv: Path,
    source_species: str,
    target_species: str,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    ortholog_source_species_column: str,
    ortholog_source_protein_ref_column: str,
    ortholog_target_species_column: str,
    ortholog_target_protein_ref_column: str,
    ortholog_source_gene_symbol_column: str,
    ortholog_target_gene_symbol_column: str,
    ortholog_evidence_column: str,
    summary_tsv_out: Path | None,
    mapped_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    rejected_input_tsv_out: Path | None,
    rejected_ortholog_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Map input proteins onto a selected ortholog species pair.'
    return run_map_orthologs_command(protein_tsv, ortholog_tsv, source_species, target_species, protein_ref_column, row_id_column, protein_separator, ortholog_source_species_column, ortholog_source_protein_ref_column, ortholog_target_species_column, ortholog_target_protein_ref_column, ortholog_source_gene_symbol_column, ortholog_target_gene_symbol_column, ortholog_evidence_column, summary_tsv_out, mapped_tsv_out, unmapped_tsv_out, rejected_input_tsv_out, rejected_ortholog_tsv_out, out_path)

@click.command("protein-set-score")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "protein_set_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
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
@click.option("--set-id-column", default="set_id", show_default=True)
@click.option("--set-name-column", default="set_name", show_default=True)
@click.option("--set-category-column", default="set_category", show_default=True)
@click.option("--source-name-column", default="source_name", show_default=True)
@click.option(
    "--source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--set-protein-ref-column", default="protein_ref", show_default=True)
@click.option(
    "--minimum-observed-member-count",
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
    "--matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--sample-score-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--condition-score-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--condition-comparison-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unresolved-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-set-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def protein_set_score_command(
    input_table: Path,
    protein_set_tsv: Path,
    design_path: Path | None,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    minimum_observed_member_count: int,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    sample_score_tsv_out: Path | None,
    condition_score_tsv_out: Path | None,
    condition_comparison_tsv_out: Path | None,
    unresolved_tsv_out: Path | None,
    rejected_set_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Score user-defined protein sets across normalized study samples.'
    return run_protein_set_score_command(input_table, protein_set_tsv, design_path, aggregation, top_n, normalization, sample_column, feature_id_column, peptide_column, intensity_column, protein_refs_column, charge_column, mz_column, retention_time_column, missing_reason_column, protein_separator, set_id_column, set_name_column, set_category_column, source_name_column, source_accession_column, set_protein_ref_column, minimum_observed_member_count, summary_tsv_out, matrix_tsv_out, sample_score_tsv_out, condition_score_tsv_out, condition_comparison_tsv_out, unresolved_tsv_out, rejected_set_tsv_out, out_path)

COMMANDS = (
    map_orthologs_command,
    protein_set_score_command,
)
