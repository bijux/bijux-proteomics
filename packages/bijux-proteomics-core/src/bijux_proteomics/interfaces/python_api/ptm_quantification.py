# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""PTM quantification Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


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
                raise ValueError(
                    "fragment support JSON must be an object keyed by spectrum id"
                )
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
        write_output_table_tsv(
            summary_tsv_out, render_ptm_ambiguity_review_summary_tsv(ambiguity_review)
        )
    if localized_tsv_out is not None:
        write_output_table_tsv(
            localized_tsv_out, render_ptm_localized_site_review_tsv(ambiguity_review)
        )
    if unlocalized_tsv_out is not None:
        write_output_table_tsv(
            unlocalized_tsv_out,
            render_ptm_unlocalized_group_review_tsv(ambiguity_review),
        )
    if (
        group_quant_summary_tsv_out is not None
        and site_group_quantification is not None
    ):
        write_output_table_tsv(
            group_quant_summary_tsv_out,
            render_ptm_site_group_quant_summary_tsv(site_group_quantification),
        )
    if group_quant_matrix_tsv_out is not None and site_group_quantification is not None:
        write_output_table_tsv(
            group_quant_matrix_tsv_out,
            render_ptm_site_group_quant_matrix_tsv(site_group_quantification),
        )
    if (
        group_quant_missingness_tsv_out is not None
        and site_group_quantification is not None
    ):
        write_output_table_tsv(
            group_quant_missingness_tsv_out,
            render_ptm_site_group_quant_missingness_tsv(site_group_quantification),
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
        if resolved_ambiguity_policy is PtmSiteQuantAmbiguityPolicy.EXCLUDE and (
            ambiguous_group_summary_tsv_out is not None
            or ambiguous_group_matrix_tsv_out is not None
            or ambiguous_group_missingness_tsv_out is not None
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
        write_output_table_tsv(
            summary_tsv_out, render_ptm_site_quant_summary_tsv(report)
        )
    if matrix_tsv_out is not None:
        write_output_table_tsv(matrix_tsv_out, render_ptm_site_quant_matrix_tsv(report))
    if missingness_tsv_out is not None:
        write_output_table_tsv(
            missingness_tsv_out, render_ptm_site_quant_missingness_tsv(report)
        )
    if (
        ambiguous_group_summary_tsv_out is not None
        and report.ambiguous_group_quantification is not None
    ):
        write_output_table_tsv(
            ambiguous_group_summary_tsv_out,
            render_ptm_site_group_quant_summary_tsv(
                report.ambiguous_group_quantification
            ),
        )
    if (
        ambiguous_group_matrix_tsv_out is not None
        and report.ambiguous_group_quantification is not None
    ):
        write_output_table_tsv(
            ambiguous_group_matrix_tsv_out,
            render_ptm_site_group_quant_matrix_tsv(
                report.ambiguous_group_quantification
            ),
        )
    if (
        ambiguous_group_missingness_tsv_out is not None
        and report.ambiguous_group_quantification is not None
    ):
        write_output_table_tsv(
            ambiguous_group_missingness_tsv_out,
            render_ptm_site_group_quant_missingness_tsv(
                report.ambiguous_group_quantification
            ),
        )
    if excluded_tsv_out is not None:
        write_output_table_tsv(
            excluded_tsv_out, render_ptm_site_quant_excluded_tsv(report)
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "site_quantification": report.to_dict(),
        },
        out_path=out_path,
    )


__all__ = ["run_ptm_ambiguity_review_command", "run_ptm_quantify_sites_command"]
