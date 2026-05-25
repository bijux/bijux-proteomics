# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""PTM differential CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

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

def run_ptm_estimate_occupancy_command(
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
    try:
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        feature_report = parse_ms1_feature_table(feature_tsv)
        occupancy_report = build_ptm_site_occupancy_report(
            site_table,
            feature_records=feature_report.accepted_records,
        )
        counterpart_report = build_ptm_occupancy_counterpart_report(
            site_table,
            feature_records=feature_report.accepted_records,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ptm_site_occupancy_summary_tsv(occupancy_report),
            encoding="utf-8",
        )
    if occupancy_tsv_out is not None:
        occupancy_tsv_out.write_text(
            render_ptm_site_occupancy_entry_tsv(occupancy_report),
            encoding="utf-8",
        )
    if counterpart_tsv_out is not None:
        counterpart_tsv_out.write_text(
            render_ptm_occupancy_counterpart_tsv(counterpart_report),
            encoding="utf-8",
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "occupancy_report": occupancy_report.to_dict(),
            "counterpart_report": counterpart_report.to_dict(),
        },
        out_path=out_path,
    )

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

def run_ptm_differential_command(
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
    try:
        evidence = parse_ptm_localization_tsv(
            evidence_tsv,
            mapping=PtmLocalizationColumnMapping(
                sample_id=sample_column,
                spectrum_id=spectrum_id_column,
                peptide=peptide_column,
                charge=charge_column,
                score=score_column,
                protein_refs=protein_refs_column,
                q_value=q_value_column,
                localization_score=localization_score_column,
                localization_probability=localization_probability_column,
                candidate_sites=candidate_sites_column,
                decoy_label=decoy_label_column,
                protein_separator=protein_separator,
                site_separator=site_separator,
            ),
        )
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                record.source_identifier for record in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        feature_report = parse_ms1_feature_table(feature_tsv)
        site_quantification = build_ptm_site_quantification_report(
            site_table,
            feature_records=feature_report.accepted_records,
            ambiguity_policy=PtmSiteQuantAmbiguityPolicy(ambiguity_policy.lower()),
        )
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        report = build_ptm_differential_analysis_report(
            site_quantification,
            design_report.accepted_entries,
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            feature_records=feature_report.accepted_records,
            protein_correction_mode=PtmProteinCorrectionMode(
                protein_correction_mode.lower()
            ),
            batch_field=design_batch_field,
            covariate_fields=tuple(dict.fromkeys(design_covariates)),
            pairing_field=design_pairing_field,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    volcano_plot = report.volcano_plot
    volcano_review = None
    if (
        volcano_tsv_out is not None
        or volcano_json_out is not None
        or volcano_svg_out is not None
        or volcano_html_out is not None
    ):
        volcano_plot = build_ptm_differential_volcano_plot(
            report.differential_report,
            adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
            absolute_log2_fold_change_threshold=(
                volcano_absolute_log2_fold_change_threshold
            ),
        )
        volcano_review = build_ptm_volcano_review(
            volcano_plot,
            policy=_build_volcano_review_policy(
                adjusted_p_value_threshold=volcano_adjusted_p_value_threshold,
                absolute_log2_fold_change_threshold=(
                    volcano_absolute_log2_fold_change_threshold
                ),
                top_label_count=volcano_top_label_count,
            ),
        )

    if results_tsv_out is not None:
        export_ptm_site_differential_tsv(report.differential_report, results_tsv_out)
    if broken_pairs_tsv_out is not None:
        export_ptm_site_differential_broken_pairs_tsv(
            report.differential_report,
            broken_pairs_tsv_out,
        )
    if volcano_tsv_out is not None:
        assert volcano_plot is not None
        export_ptm_differential_volcano_tsv(volcano_plot, volcano_tsv_out)
    if volcano_review is not None:
        _export_volcano_review_assets(
            review_report=volcano_review,
            json_out=volcano_json_out,
            svg_out=volcano_svg_out,
            html_out=volcano_html_out,
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "site_quantification": report.site_quantification.to_dict(),
            "design_matrix": report.design_matrix.to_dict(),
            "design_model_fit": report.design_model_fit.to_dict(),
            "protein_correction_mode": report.protein_correction_mode.value,
            "differential_report": report.differential_report.to_dict(),
            "volcano_plot": None if volcano_plot is None else volcano_plot.to_dict(),
            "volcano_review": (
                None if volcano_review is None else volcano_review.to_dict()
            ),
            "outputs": {
                "results_tsv": None if results_tsv_out is None else str(results_tsv_out),
                "broken_pairs_tsv": (
                    None if broken_pairs_tsv_out is None else str(broken_pairs_tsv_out)
                ),
                "volcano_tsv": None if volcano_tsv_out is None else str(volcano_tsv_out),
                "volcano_json": (
                    None if volcano_json_out is None else str(volcano_json_out)
                ),
                "volcano_svg": (
                    None if volcano_svg_out is None else str(volcano_svg_out)
                ),
                "volcano_html": (
                    None if volcano_html_out is None else str(volcano_html_out)
                ),
            },
        },
        out_path=out_path,
    )

COMMANDS = (
    ptm_estimate_occupancy_command,
    ptm_differential_command,
)
