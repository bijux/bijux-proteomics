# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""PTM quantification CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("ambiguity-review")
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
@click.option(
    "--fragment-support-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--localized-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unlocalized-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--group-quant-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--group-quant-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--group-quant-missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_ambiguity_review_command(
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
    fragment_support_json: Path | None,
    summary_tsv_out: Path | None,
    localized_tsv_out: Path | None,
    unlocalized_tsv_out: Path | None,
    group_quant_summary_tsv_out: Path | None,
    group_quant_matrix_tsv_out: Path | None,
    group_quant_missingness_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Review PTM localization ambiguity and optional ambiguity-group quantification.'
    return run_ptm_ambiguity_review_command(evidence_tsv, proteins_fasta, feature_path, sample_column, spectrum_id_column, peptide_column, charge_column, score_column, protein_refs_column, q_value_column, localization_score_column, localization_probability_column, candidate_sites_column, decoy_label_column, protein_separator, site_separator, fragment_support_json, summary_tsv_out, localized_tsv_out, unlocalized_tsv_out, group_quant_summary_tsv_out, group_quant_matrix_tsv_out, group_quant_missingness_tsv_out, out_path)

def run_ptm_ambiguity_review_command(
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
    fragment_support_json: Path | None,
    summary_tsv_out: Path | None,
    localized_tsv_out: Path | None,
    unlocalized_tsv_out: Path | None,
    group_quant_summary_tsv_out: Path | None,
    group_quant_matrix_tsv_out: Path | None,
    group_quant_missingness_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        if feature_path is None and any(
            output is not None
            for output in (
                group_quant_summary_tsv_out,
                group_quant_matrix_tsv_out,
                group_quant_missingness_tsv_out,
            )
        ):
            raise click.ClickException(
                "group quantification TSV outputs require --features because unresolved-site quantification depends on feature intensities"
            )
        fragment_ion_support_by_spectrum: dict[str, tuple[str, ...]] | None = None
        if fragment_support_json is not None:
            raw_fragment_support = json.loads(
                fragment_support_json.read_text(encoding="utf-8")
            )
            if not isinstance(raw_fragment_support, dict):
                raise ValueError("fragment support JSON must be an object keyed by spectrum id")
            fragment_ion_support_by_spectrum = {
                str(spectrum_id): tuple(str(ion) for ion in ions)
                for spectrum_id, ions in raw_fragment_support.items()
            }
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
        localization = build_ptm_localization_scoring_report(
            evidence.accepted_records,
            fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
        )
        ambiguity_review = build_ptm_ambiguity_review_report(
            site_table,
            localization_scoring_report=localization,
            protein_sequences=protein_sequences,
        )
        site_group_quantification = None
        if feature_path is not None:
            feature_report = parse_ms1_feature_table(feature_path)
            site_group_quantification = build_ptm_site_group_quantification_report(
                site_table,
                feature_records=feature_report.accepted_records,
                localization_scoring_report=localization,
                protein_sequences=protein_sequences,
            )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ptm_ambiguity_review_summary_tsv(ambiguity_review),
            encoding="utf-8",
        )
    if localized_tsv_out is not None:
        localized_tsv_out.write_text(
            render_ptm_localized_site_review_tsv(ambiguity_review),
            encoding="utf-8",
        )
    if unlocalized_tsv_out is not None:
        unlocalized_tsv_out.write_text(
            render_ptm_unlocalized_group_review_tsv(ambiguity_review),
            encoding="utf-8",
        )
    if (
        group_quant_summary_tsv_out is not None
        and site_group_quantification is not None
    ):
        group_quant_summary_tsv_out.write_text(
            render_ptm_site_group_quant_summary_tsv(site_group_quantification),
            encoding="utf-8",
        )
    if (
        group_quant_matrix_tsv_out is not None
        and site_group_quantification is not None
    ):
        group_quant_matrix_tsv_out.write_text(
            render_ptm_site_group_quant_matrix_tsv(site_group_quantification),
            encoding="utf-8",
        )
    if (
        group_quant_missingness_tsv_out is not None
        and site_group_quantification is not None
    ):
        group_quant_missingness_tsv_out.write_text(
            render_ptm_site_group_quant_missingness_tsv(site_group_quantification),
            encoding="utf-8",
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "rejected_rows": len(evidence.rejected_rows),
            "ambiguity_review": ambiguity_review.to_dict(),
            "site_group_quantification": None
            if site_group_quantification is None
            else site_group_quantification.to_dict(),
        },
        out_path=out_path,
    )

@click.command("quantify-sites")
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
    "--ambiguity-policy",
    type=click.Choice(
        [policy.value for policy in PtmSiteQuantAmbiguityPolicy], case_sensitive=False
    ),
    default=PtmSiteQuantAmbiguityPolicy.PRESERVE.value,
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
    "--missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguous-group-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguous-group-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguous-group-missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--excluded-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_quantify_sites_command(
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
    ambiguity_policy: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    ambiguous_group_summary_tsv_out: Path | None,
    ambiguous_group_matrix_tsv_out: Path | None,
    ambiguous_group_missingness_tsv_out: Path | None,
    excluded_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Quantify PTM sites across samples from localized evidence and feature intensities.'
    return run_ptm_quantify_sites_command(evidence_tsv, proteins_fasta, feature_tsv, sample_column, spectrum_id_column, peptide_column, charge_column, score_column, protein_refs_column, q_value_column, localization_score_column, localization_probability_column, candidate_sites_column, decoy_label_column, protein_separator, site_separator, ambiguity_policy, summary_tsv_out, matrix_tsv_out, missingness_tsv_out, ambiguous_group_summary_tsv_out, ambiguous_group_matrix_tsv_out, ambiguous_group_missingness_tsv_out, excluded_tsv_out, out_path)

def run_ptm_quantify_sites_command(
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
    ambiguity_policy: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    ambiguous_group_summary_tsv_out: Path | None,
    ambiguous_group_matrix_tsv_out: Path | None,
    ambiguous_group_missingness_tsv_out: Path | None,
    excluded_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        resolved_ambiguity_policy = PtmSiteQuantAmbiguityPolicy(
            ambiguity_policy.lower()
        )
        if (
            resolved_ambiguity_policy is PtmSiteQuantAmbiguityPolicy.EXCLUDE
            and (
                ambiguous_group_summary_tsv_out is not None
                or ambiguous_group_matrix_tsv_out is not None
                or ambiguous_group_missingness_tsv_out is not None
            )
        ):
            raise click.ClickException(
                "ambiguous-group TSV outputs require --ambiguity-policy preserve because excluded ambiguous site rows are not quantified into one group matrix"
            )
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
        report = build_ptm_site_quantification_report(
            site_table,
            feature_records=feature_report.accepted_records,
            ambiguity_policy=resolved_ambiguity_policy,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ptm_site_quant_summary_tsv(report),
            encoding="utf-8",
        )
    if matrix_tsv_out is not None:
        matrix_tsv_out.write_text(
            render_ptm_site_quant_matrix_tsv(report),
            encoding="utf-8",
        )
    if missingness_tsv_out is not None:
        missingness_tsv_out.write_text(
            render_ptm_site_quant_missingness_tsv(report),
            encoding="utf-8",
        )
    if (
        ambiguous_group_summary_tsv_out is not None
        and report.ambiguous_group_quantification is not None
    ):
        ambiguous_group_summary_tsv_out.write_text(
            render_ptm_site_group_quant_summary_tsv(
                report.ambiguous_group_quantification
            ),
            encoding="utf-8",
        )
    if (
        ambiguous_group_matrix_tsv_out is not None
        and report.ambiguous_group_quantification is not None
    ):
        ambiguous_group_matrix_tsv_out.write_text(
            render_ptm_site_group_quant_matrix_tsv(
                report.ambiguous_group_quantification
            ),
            encoding="utf-8",
        )
    if (
        ambiguous_group_missingness_tsv_out is not None
        and report.ambiguous_group_quantification is not None
    ):
        ambiguous_group_missingness_tsv_out.write_text(
            render_ptm_site_group_quant_missingness_tsv(
                report.ambiguous_group_quantification
            ),
            encoding="utf-8",
        )
    if excluded_tsv_out is not None:
        excluded_tsv_out.write_text(
            render_ptm_site_quant_excluded_tsv(report),
            encoding="utf-8",
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "site_quantification": report.to_dict(),
        },
        out_path=out_path,
    )

COMMANDS = (
    ptm_ambiguity_review_command,
    ptm_quantify_sites_command,
)
