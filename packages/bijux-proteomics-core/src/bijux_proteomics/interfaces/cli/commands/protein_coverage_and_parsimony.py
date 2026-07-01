# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein coverage and parsimony CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.protein_coverage_and_parsimony import (
    run_infer_proteins_command,
    run_protein_coverage_command,
    run_protein_coverage_plot_command,
    run_protein_parsimony_command,
)
from bijux_proteomics.interfaces.support.identification import (
    ParsimonyVariant,
    ScoreOrientation,
)
from bijux_proteomics.interfaces.support.sequence_support.cli_choices import (
    _score_orientation_choice,
)


@click.command("protein-coverage")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--fasta",
    "fasta_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--coverage-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--regions-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--uncovered-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--peptide-coordinate-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_coverage_command(
    input_tsv: Path,
    fasta_path: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    coverage_tsv_out: Path | None,
    regions_tsv_out: Path | None,
    uncovered_tsv_out: Path | None,
    peptide_coordinate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review protein sequence coverage from accepted peptide evidence."""
    return run_protein_coverage_command(
        input_tsv,
        fasta_path,
        threshold,
        score_orientation,
        spectrum_id_column,
        peptide_column,
        run_id_column,
        modified_peptide_column,
        charge_column,
        score_column,
        q_value_column,
        protein_refs_column,
        decoy_label_column,
        contaminant_label_column,
        protein_separator,
        decoy_prefix,
        decoy_suffix,
        summary_tsv_out,
        coverage_tsv_out,
        regions_tsv_out,
        uncovered_tsv_out,
        peptide_coordinate_tsv_out,
        out_path,
    )


@click.command("protein-coverage-plot")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--fasta",
    "fasta_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--high-q-value", type=float, default=0.01, show_default=True)
@click.option("--medium-q-value", type=float, default=0.05, show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--intensity-column", default=None)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--positions-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--svg-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--html-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_coverage_plot_command(
    input_tsv: Path,
    fasta_path: Path,
    threshold: float,
    score_orientation: str,
    high_q_value: float,
    medium_q_value: float,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    intensity_column: str | None,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    positions_tsv_out: Path | None,
    svg_out: Path | None,
    html_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build plot-ready peptide-to-protein coverage payloads and static plots."""
    return run_protein_coverage_plot_command(
        input_tsv,
        fasta_path,
        threshold,
        score_orientation,
        high_q_value,
        medium_q_value,
        spectrum_id_column,
        peptide_column,
        run_id_column,
        modified_peptide_column,
        charge_column,
        score_column,
        intensity_column,
        q_value_column,
        protein_refs_column,
        decoy_label_column,
        contaminant_label_column,
        protein_separator,
        decoy_prefix,
        decoy_suffix,
        positions_tsv_out,
        svg_out,
        html_out,
        out_path,
    )


@click.command("protein-parsimony")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option(
    "--variant",
    type=click.Choice([variant.value for variant in ParsimonyVariant]),
    default=ParsimonyVariant.GREEDY_COVERAGE.value,
    show_default=True,
)
@click.option(
    "--review-variant",
    "review_variants",
    type=click.Choice([variant.value for variant in ParsimonyVariant]),
    multiple=True,
    default=tuple(variant.value for variant in ParsimonyVariant),
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--protein-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_parsimony_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    variant: str,
    review_variants: tuple[str, ...],
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    ambiguity_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review one parsimony-selected protein set and its remaining ambiguity."""
    return run_protein_parsimony_command(
        input_tsv,
        threshold,
        score_orientation,
        variant,
        review_variants,
        spectrum_id_column,
        peptide_column,
        run_id_column,
        modified_peptide_column,
        charge_column,
        score_column,
        q_value_column,
        protein_refs_column,
        decoy_label_column,
        contaminant_label_column,
        protein_separator,
        decoy_prefix,
        decoy_suffix,
        summary_tsv_out,
        protein_tsv_out,
        ambiguity_tsv_out,
        out_path,
    )


@click.command("infer-proteins")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--threshold", type=float, default=0.01, show_default=True)
@click.option(
    "--score-orientation",
    type=_score_orientation_choice(),
    default=ScoreOrientation.HIGHER_BETTER.value,
    show_default=True,
)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--fasta",
    "fasta_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def infer_proteins_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    fasta_path: Path | None,
    out_path: Path | None,
) -> None:
    """Infer proteins, group evidence, and emit multi-level FDR artifacts."""
    return run_infer_proteins_command(
        input_tsv,
        threshold,
        score_orientation,
        spectrum_id_column,
        peptide_column,
        charge_column,
        score_column,
        q_value_column,
        protein_refs_column,
        decoy_label_column,
        protein_separator,
        decoy_prefix,
        decoy_suffix,
        fasta_path,
        out_path,
    )


COMMANDS = (
    protein_coverage_command,
    protein_coverage_plot_command,
    protein_parsimony_command,
    infer_proteins_command,
)
