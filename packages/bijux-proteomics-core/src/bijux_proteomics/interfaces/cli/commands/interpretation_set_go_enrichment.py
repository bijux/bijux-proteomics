# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation set and GO enrichment CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.interpretation_set_go_enrichment import (
    run_go_enrichment_command,
    run_protein_set_enrichment_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("protein-set-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "protein_set_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--background-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
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
    "--missing-background-policy",
    type=click.Choice(
        [policy.value for policy in ProteinSetEnrichmentMissingBackgroundPolicy]
    ),
    default=ProteinSetEnrichmentMissingBackgroundPolicy.REJECT.value,
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
    "--result-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--universe-gap-tsv-out",
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
def protein_set_enrichment_command(
    foreground_tsv: Path,
    protein_set_tsv: Path,
    background_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    missing_background_policy: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    result_tsv_out: Path | None,
    universe_gap_tsv_out: Path | None,
    rejected_set_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Run generic enrichment over compartment and custom protein-set definitions."
    return run_protein_set_enrichment_command(
        foreground_tsv,
        protein_set_tsv,
        background_tsv,
        protein_ref_column,
        row_id_column,
        protein_separator,
        set_id_column,
        set_name_column,
        set_category_column,
        source_name_column,
        source_accession_column,
        set_protein_ref_column,
        missing_background_policy,
        max_adjusted_p_value,
        min_enrichment_ratio,
        summary_tsv_out,
        result_tsv_out,
        universe_gap_tsv_out,
        rejected_set_tsv_out,
        out_path,
    )


@click.command("go-enrichment")
@click.argument(
    "foreground_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "background_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "go_annotation_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option("--row-id-column", default="row_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--go-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--go-term-id-column", default="go_term_id", show_default=True)
@click.option("--go-term-name-column", default="go_term_name", show_default=True)
@click.option("--go-aspect-column", default="go_aspect", show_default=True)
@click.option("--evidence-code-column", default="evidence_code", show_default=True)
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
    "--term-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unannotated-tsv-out",
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
def go_enrichment_command(
    foreground_tsv: Path,
    background_tsv: Path,
    go_annotation_tsv: Path,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    go_protein_ref_column: str,
    go_term_id_column: str,
    go_term_name_column: str,
    go_aspect_column: str,
    evidence_code_column: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    term_tsv_out: Path | None,
    unannotated_tsv_out: Path | None,
    rejected_annotation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Run GO term enrichment over foreground and background protein sets."
    return run_go_enrichment_command(
        foreground_tsv,
        background_tsv,
        go_annotation_tsv,
        protein_ref_column,
        row_id_column,
        protein_separator,
        go_protein_ref_column,
        go_term_id_column,
        go_term_name_column,
        go_aspect_column,
        evidence_code_column,
        max_adjusted_p_value,
        min_enrichment_ratio,
        summary_tsv_out,
        term_tsv_out,
        unannotated_tsv_out,
        rejected_annotation_tsv_out,
        out_path,
    )


COMMANDS = (
    protein_set_enrichment_command,
    go_enrichment_command,
)
