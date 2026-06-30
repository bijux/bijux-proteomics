# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""PTM differential Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.io_and_dia import parse_experimental_design_table
from bijux_proteomics.interfaces.support.ptm_quantification import (
    NormalizationMethod,
    PtmLocalizationColumnMapping,
    PtmProteinCorrectionMode,
    PtmSiteQuantAmbiguityPolicy,
    build_ptm_differential_analysis_report,
    build_ptm_differential_volcano_plot,
    build_ptm_occupancy_counterpart_report,
    build_ptm_site_occupancy_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    export_ptm_differential_volcano_tsv,
    export_ptm_site_differential_broken_pairs_tsv,
    export_ptm_site_differential_tsv,
    map_ptm_evidence_to_protein_sites,
    parse_ms1_feature_table,
    parse_ptm_localization_tsv,
    render_ptm_occupancy_counterpart_tsv,
    render_ptm_site_occupancy_entry_tsv,
    render_ptm_site_occupancy_summary_tsv,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FastaParseMode,
    build_ptm_volcano_review,
    parse_fasta_document,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
)
from bijux_proteomics.interfaces.support.output_protocol.volcano_review import (
    _build_volcano_review_policy,
    _export_volcano_review_assets,
)


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
        write_output_table_tsv(
            summary_tsv_out, render_ptm_site_occupancy_summary_tsv(occupancy_report)
        )
    if occupancy_tsv_out is not None:
        write_output_table_tsv(
            occupancy_tsv_out, render_ptm_site_occupancy_entry_tsv(occupancy_report)
        )
    if counterpart_tsv_out is not None:
        write_output_table_tsv(
            counterpart_tsv_out,
            render_ptm_occupancy_counterpart_tsv(counterpart_report),
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
        if volcano_plot is None:
            raise RuntimeError(
                "PTM volcano TSV export requires a generated volcano plot surface"
            )
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
                "results_tsv": None
                if results_tsv_out is None
                else str(results_tsv_out),
                "broken_pairs_tsv": (
                    None if broken_pairs_tsv_out is None else str(broken_pairs_tsv_out)
                ),
                "volcano_tsv": None
                if volcano_tsv_out is None
                else str(volcano_tsv_out),
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


__all__ = ["run_ptm_estimate_occupancy_command", "run_ptm_differential_command"]
