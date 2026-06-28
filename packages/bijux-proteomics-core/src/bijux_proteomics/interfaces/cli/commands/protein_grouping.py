# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Protein grouping and ambiguity CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.protein_grouping import (
    run_protein_ambiguity_command,
    run_protein_groups_command,
    run_protein_inference_benchmarks_command,
)
from bijux_proteomics.interfaces.support.identification import ScoreOrientation
from bijux_proteomics.interfaces.support.sequence_support import _score_orientation_choice


@click.command("protein-groups")
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
    "--group-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_groups_command(
    input_tsv: Path,
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
    group_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review grouped protein evidence from FDR-filtered PSM rows."""
    return run_protein_groups_command(
        input_tsv,
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
        group_tsv_out,
        out_path,
    )


@click.command("protein-ambiguity")
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
@click.option("--high-q-value", type=float, default=0.01, show_default=True)
@click.option("--medium-q-value", type=float, default=0.05, show_default=True)
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
    "--ambiguity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_ambiguity_command(
    input_tsv: Path,
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
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    ambiguity_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review ambiguous protein groups from FDR-filtered PSM rows."""
    return run_protein_ambiguity_command(
        input_tsv,
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
        q_value_column,
        protein_refs_column,
        decoy_label_column,
        contaminant_label_column,
        protein_separator,
        decoy_prefix,
        decoy_suffix,
        summary_tsv_out,
        ambiguity_tsv_out,
        out_path,
    )


@click.command("protein-inference-benchmarks")
@click.option("--picked-threshold", type=float, default=0.05, show_default=True)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--scenarios-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--assessments-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def protein_inference_benchmarks_command(
    picked_threshold: float,
    summary_tsv_out: Path | None,
    scenarios_tsv_out: Path | None,
    assessments_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review the owned protein-inference benchmark catalog."""
    return run_protein_inference_benchmarks_command(
        picked_threshold,
        summary_tsv_out,
        scenarios_tsv_out,
        assessments_tsv_out,
        out_path,
    )


COMMANDS = (
    protein_groups_command,
    protein_ambiguity_command,
    protein_inference_benchmarks_command,
)
