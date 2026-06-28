# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""PTM reporting CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.ptm_reporting import (
    run_ptm_report_command,
    run_ptm_summarize_command,
)
from bijux_proteomics.interfaces.support.ptm_quantification import (
    NormalizationMethod,
    PtmMotifRegulationDirection,
    PtmProteinCorrectionMode,
    PtmSiteQuantAmbiguityPolicy,
)
from bijux_proteomics.interfaces.support.sequence_support import _normalization_choice


@click.command("report")
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
    "--fragment-support-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
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
@click.option("--flank-size", default=7, show_default=True, type=int)
@click.option("--max-adjusted-p-value", default=0.1, show_default=True, type=float)
@click.option(
    "--min-absolute-log2-fold-change",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--direction",
    type=click.Choice(
        [direction.value for direction in PtmMotifRegulationDirection],
        case_sensitive=False,
    ),
    default=PtmMotifRegulationDirection.BOTH.value,
    show_default=True,
)
@click.option(
    "--include-ambiguous-regulated-sites/--exclude-ambiguous-regulated-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--include-ambiguous-background-sites/--exclude-ambiguous-background-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--min-frequency-difference",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.5,
    show_default=True,
    type=float,
)
@click.option(
    "--max-reported-term-count",
    default=25,
    show_default=True,
    type=int,
)
@click.option(
    "--annotation-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--species", "target_species", default=None)
@click.option(
    "--card-max-adjusted-p-value",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    required=True,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_report_command(
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
    fragment_support_json: Path | None,
    ambiguity_policy: str,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    protein_correction_mode: str,
    flank_size: int,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    direction: str,
    include_ambiguous_regulated_sites: bool,
    include_ambiguous_background_sites: bool,
    min_frequency_difference: float,
    min_enrichment_ratio: float,
    max_reported_term_count: int,
    annotation_tsv: Path | None,
    target_species: str | None,
    card_max_adjusted_p_value: float,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build one governed PTM report directory over peptide, site, quant, and motif surfaces."""
    return run_ptm_report_command(
        evidence_tsv,
        proteins_fasta,
        feature_tsv,
        design_path,
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
        fragment_support_json,
        ambiguity_policy,
        normalization,
        condition_a,
        condition_b,
        design_batch_field,
        design_pairing_field,
        design_covariates,
        protein_correction_mode,
        flank_size,
        max_adjusted_p_value,
        min_absolute_log2_fold_change,
        direction,
        include_ambiguous_regulated_sites,
        include_ambiguous_background_sites,
        min_frequency_difference,
        min_enrichment_ratio,
        max_reported_term_count,
        annotation_tsv,
        target_species,
        card_max_adjusted_p_value,
        output_dir,
        out_path,
    )


@click.command("summarize")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--features",
    "feature_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
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
@click.option("--threshold", type=float, default=0.05, show_default=True)
@click.option("--flank-size", type=int, default=7, show_default=True)
@click.option(
    "--site-quant-ambiguity-policy",
    type=click.Choice(
        [policy.value for policy in PtmSiteQuantAmbiguityPolicy], case_sensitive=False
    ),
    default=PtmSiteQuantAmbiguityPolicy.PRESERVE.value,
    show_default=True,
)
@click.option(
    "--occupancy-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--occupancy-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--occupancy-counterpart-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_summarize_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    feature_path: Path | None,
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
    threshold: float,
    flank_size: int,
    site_quant_ambiguity_policy: str,
    occupancy_summary_tsv_out: Path | None,
    occupancy_tsv_out: Path | None,
    occupancy_counterpart_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Summarize PTM site evidence from localized peptides and optional feature intensities."""
    return run_ptm_summarize_command(
        evidence_tsv,
        proteins_fasta,
        feature_path,
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
        threshold,
        flank_size,
        site_quant_ambiguity_policy,
        occupancy_summary_tsv_out,
        occupancy_tsv_out,
        occupancy_counterpart_tsv_out,
        out_path,
    )


COMMANDS = (
    ptm_report_command,
    ptm_summarize_command,
)
