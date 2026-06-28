# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""PTM context-annotation CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.ptm_context_annotation import (
    run_ptm_annotate_context_command,
)


@click.command("annotate-context")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "context_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option(
    "--localization-score-column", default="localization_score", show_default=True
)
@click.option(
    "--localization-probability-column",
    default="localization_probability",
    show_default=True,
)
@click.option("--candidate-sites-column", default="candidate_sites", show_default=True)
@click.option("--decoy-label-column", default="decoy_label", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--site-separator", default=";", show_default=True)
@click.option("--context-protein-ref-column", default="protein_ref", show_default=True)
@click.option("--context-start-column", default="start", show_default=True)
@click.option("--context-end-column", default="end", show_default=True)
@click.option("--context-domain-column", default="domain_name", show_default=True)
@click.option(
    "--context-disorder-column",
    default="disorder_region",
    show_default=True,
)
@click.option(
    "--context-transmembrane-column",
    default="transmembrane_region",
    show_default=True,
)
@click.option(
    "--context-active-site-column",
    default="active_site_label",
    show_default=True,
)
@click.option("--context-motif-column", default="motif_name", show_default=True)
@click.option(
    "--context-conservation-column",
    default="conservation_score",
    show_default=True,
)
@click.option("--context-source-name-column", default="source_name", show_default=True)
@click.option(
    "--context-source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--context-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_annotate_context_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    context_tsv: Path,
    sample_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    protein_refs_column: str,
    q_value_column: str | None,
    localization_score_column: str,
    localization_probability_column: str | None,
    candidate_sites_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    site_separator: str,
    context_protein_ref_column: str,
    context_start_column: str,
    context_end_column: str,
    context_domain_column: str | None,
    context_disorder_column: str | None,
    context_transmembrane_column: str | None,
    context_active_site_column: str | None,
    context_motif_column: str | None,
    context_conservation_column: str | None,
    context_source_name_column: str | None,
    context_source_accession_column: str | None,
    summary_tsv_out: Path | None,
    context_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Annotate observed PTM sites with provided protein-region context."""
    return run_ptm_annotate_context_command(
        evidence_tsv,
        proteins_fasta,
        context_tsv,
        sample_column,
        spectrum_id_column,
        peptide_column,
        charge_column,
        score_column,
        protein_refs_column,
        q_value_column,
        localization_score_column,
        localization_probability_column,
        candidate_sites_column,
        decoy_label_column,
        protein_separator,
        site_separator,
        context_protein_ref_column,
        context_start_column,
        context_end_column,
        context_domain_column,
        context_disorder_column,
        context_transmembrane_column,
        context_active_site_column,
        context_motif_column,
        context_conservation_column,
        context_source_name_column,
        context_source_accession_column,
        summary_tsv_out,
        context_tsv_out,
        out_path,
    )


COMMANDS = (ptm_annotate_context_command,)
