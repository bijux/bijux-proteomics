# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""FDR review CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.fdr_review import run_fdr_command, run_fdr_reference_check_command, run_fdr_levels_command, run_picked_protein_fdr_command

@click.command("fdr")
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
@click.option("--run-id-column", default=None)
@click.option("--modified-peptide-column", default=None)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--pep-column", default=None)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--decoy-prefix", default="DECOY_", show_default=True)
@click.option("--decoy-suffix", default=None)
@click.option(
    "--jsonl-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--entries-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--audit-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--calibration-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--score-separation-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--score-separation-bins-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--error-rate-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--error-rate-entries-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def fdr_command(
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
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    audit_out: Path | None,
    calibration_out: Path | None,
    score_separation_summary_tsv_out: Path | None,
    score_separation_bins_tsv_out: Path | None,
    error_rate_summary_tsv_out: Path | None,
    error_rate_entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Apply basic target-decoy FDR and emit filtered PSM summaries.'
    return run_fdr_command(input_tsv, threshold, score_orientation, spectrum_id_column, peptide_column, run_id_column, modified_peptide_column, charge_column, score_column, q_value_column, pep_column, protein_refs_column, decoy_label_column, contaminant_label_column, protein_separator, decoy_prefix, decoy_suffix, jsonl_out, tsv_out, provenance_out, summary_tsv_out, entries_tsv_out, audit_out, calibration_out, score_separation_summary_tsv_out, score_separation_bins_tsv_out, error_rate_summary_tsv_out, error_rate_entries_tsv_out, out_path)

@click.command("fdr-reference-check")
@click.argument(
    "reference_json", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--entries-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def fdr_reference_check_command(
    reference_json: Path,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Validate curated target-decoy reference cases against the owned FDR surface.'
    return run_fdr_reference_check_command(reference_json, summary_tsv_out, entries_tsv_out, out_path)

@click.command("fdr-levels")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--threshold",
    "thresholds",
    type=float,
    multiple=True,
    default=(0.01, 0.05, 0.1),
    show_default=True,
)
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
    "--entries-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def fdr_levels_command(
    input_tsv: Path,
    thresholds: tuple[float, ...],
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
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Compare PSM, peptide, and protein FDR counts across explicit thresholds.'
    return run_fdr_levels_command(input_tsv, thresholds, score_orientation, spectrum_id_column, peptide_column, run_id_column, modified_peptide_column, charge_column, score_column, q_value_column, protein_refs_column, decoy_label_column, contaminant_label_column, protein_separator, decoy_prefix, decoy_suffix, summary_tsv_out, entries_tsv_out, out_path)

@click.command("picked-protein-fdr")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--threshold",
    "thresholds",
    type=float,
    multiple=True,
    default=(0.01, 0.05, 0.1),
    show_default=True,
)
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
    "--entries-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def picked_protein_fdr_command(
    input_tsv: Path,
    thresholds: tuple[float, ...],
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
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Review picked target-decoy protein FDR across explicit thresholds.'
    return run_picked_protein_fdr_command(input_tsv, thresholds, score_orientation, spectrum_id_column, peptide_column, run_id_column, modified_peptide_column, charge_column, score_column, q_value_column, protein_refs_column, decoy_label_column, contaminant_label_column, protein_separator, decoy_prefix, decoy_suffix, summary_tsv_out, entries_tsv_out, out_path)

COMMANDS = (
    fdr_command,
    fdr_reference_check_command,
    fdr_levels_command,
    picked_protein_fdr_command,
)
