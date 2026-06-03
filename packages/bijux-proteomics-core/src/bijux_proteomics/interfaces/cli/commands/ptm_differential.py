# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""PTM differential CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.ptm_differential import run_ptm_estimate_occupancy_command, run_ptm_differential_command

@click.command("estimate-occupancy")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "feature_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--occupancy-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--counterpart-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_estimate_occupancy_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_tsv: Path,
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
    summary_tsv_out: Path | None,
    occupancy_tsv_out: Path | None,
    counterpart_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Estimate PTM occupancy and export counterpart-coverage review ledgers.'
    return run_ptm_estimate_occupancy_command(evidence_tsv, proteins_fasta, feature_tsv, sample_column, spectrum_id_column, peptide_column, charge_column, score_column, protein_refs_column, q_value_column, localization_score_column, localization_probability_column, candidate_sites_column, decoy_label_column, protein_separator, site_separator, summary_tsv_out, occupancy_tsv_out, counterpart_tsv_out, out_path)

@click.command("differential")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "feature_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
@click.option(
    "--ambiguity-policy",
    type=click.Choice(
        [policy.value for policy in PtmSiteQuantAmbiguityPolicy], case_sensitive=False
    ),
    default=PtmSiteQuantAmbiguityPolicy.PRESERVE.value,
    show_default=True,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-pairing-field", default=None)
@click.option("--design-covariate", "design_covariates", multiple=True)
@click.option(
    "--protein-correction-mode",
    type=click.Choice(
        [mode.value for mode in PtmProteinCorrectionMode], case_sensitive=False
    ),
    default=PtmProteinCorrectionMode.NONE.value,
    show_default=True,
)
@click.option(
    "--results-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--broken-pairs-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-json-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-svg-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-html-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--volcano-adjusted-p-value-threshold",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--volcano-absolute-log2-fold-change-threshold",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_differential_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_tsv: Path,
    design_path: Path,
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
    ambiguity_policy: str,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    protein_correction_mode: str,
    results_tsv_out: Path | None,
    broken_pairs_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    out_path: Path | None,
) -> None:
    'Test PTM site changes across conditions from localized evidence and feature intensities.'
    return run_ptm_differential_command(evidence_tsv, proteins_fasta, feature_tsv, design_path, sample_column, spectrum_id_column, peptide_column, charge_column, score_column, protein_refs_column, q_value_column, localization_score_column, localization_probability_column, candidate_sites_column, decoy_label_column, protein_separator, site_separator, ambiguity_policy, normalization, condition_a, condition_b, design_batch_field, design_pairing_field, design_covariates, protein_correction_mode, results_tsv_out, broken_pairs_tsv_out, volcano_tsv_out, volcano_json_out, volcano_svg_out, volcano_html_out, volcano_adjusted_p_value_threshold, volcano_absolute_log2_fold_change_threshold, volcano_top_label_count, out_path)

COMMANDS = (
    ptm_estimate_occupancy_command,
    ptm_differential_command,
)
