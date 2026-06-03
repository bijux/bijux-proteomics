# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""PTM reporting Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.support.workflow import *  # noqa: F401,F403,F405
from bijux_proteomics.workflow.pipelines.ptm_site_workflow import (
    PtmSiteWorkflowBundle,
    PtmSiteWorkflowExportManifest,
)


def run_ptm_report_command(
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
    result = _run_orchestrated_workflow(
        PtmWorkflowConfig(
            evidence_tsv_path=evidence_tsv,
            proteins_fasta_path=proteins_fasta,
            feature_tsv_path=feature_tsv,
            design_tsv_path=design_path,
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
            fragment_support_json_path=fragment_support_json,
            ambiguity_policy=PtmSiteQuantAmbiguityPolicy(ambiguity_policy.lower()),
            normalization_method=NormalizationMethod(normalization),
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=design_batch_field,
            covariate_fields=tuple(dict.fromkeys(design_covariates)),
            pairing_field=design_pairing_field,
            protein_correction_mode=PtmProteinCorrectionMode(
                protein_correction_mode.lower()
            ),
            motif_flank_size=flank_size,
            max_adjusted_p_value=max_adjusted_p_value,
            min_absolute_log2_fold_change=min_absolute_log2_fold_change,
            direction=PtmMotifRegulationDirection(direction.lower()),
            include_ambiguous_regulated_sites=include_ambiguous_regulated_sites,
            include_ambiguous_background_sites=include_ambiguous_background_sites,
            min_frequency_difference=min_frequency_difference,
            min_enrichment_ratio=min_enrichment_ratio,
            max_reported_term_count=max_reported_term_count,
            annotation_tsv_path=annotation_tsv,
            annotation_target_species=target_species,
            card_max_adjusted_p_value=card_max_adjusted_p_value,
            output_dir=output_dir,
        )
    )
    workflow_report = result.report
    workflow_manifest = result.export_manifest
    if not isinstance(workflow_report, PtmSiteWorkflowBundle):
        raise click.ClickException(
            "workflow did not produce the expected PTM report bundle"
        )
    if not isinstance(workflow_manifest, PtmSiteWorkflowExportManifest):
        raise click.ClickException(
            "workflow did not produce the expected PTM report manifest"
        )
    _emit_json(
        {
            "accepted_rows": workflow_report.summary.accepted_evidence_count,
            "rejected_rows": workflow_report.summary.rejected_evidence_count,
            "feature_rows": workflow_report.summary.feature_row_count,
            "design_rows": workflow_report.summary.design_row_count,
            "workflow_report": workflow_report.to_dict(),
            "report": workflow_report.report.to_dict(),
            "workflow_export_manifest": workflow_manifest.to_dict(),
            "export_manifest": workflow_manifest.ptm_report_manifest.to_dict(),
            "outputs": result.outputs,
        },
        out_path=out_path,
    )


def run_ptm_summarize_command(
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
    try:
        if feature_path is None and any(
            output is not None
            for output in (
                occupancy_summary_tsv_out,
                occupancy_tsv_out,
                occupancy_counterpart_tsv_out,
            )
        ):
            raise click.ClickException(
                "occupancy TSV outputs require --features because occupancy depends on feature intensities"
            )
        mapping = PtmLocalizationColumnMapping(
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
        )
        evidence = parse_ptm_localization_tsv(evidence_tsv, mapping=mapping)
        fasta_report = parse_fasta_document(
            proteins_fasta.read_text(), mode=FastaParseMode.STRICT
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
        localization = build_ptm_localization_scoring_report(evidence.accepted_records)
        ambiguity_review = build_ptm_ambiguity_review_report(
            site_table,
            localization_scoring_report=localization,
            protein_sequences=protein_sequences,
        )
        coverage = build_ptm_site_coverage_report(mappings)
        fdr = build_ptm_site_fdr(site_table, threshold=threshold)
        motifs = build_ptm_motif_windows(
            site_table, protein_sequences=protein_sequences, flank_size=flank_size
        )
        enrichment = build_ptm_enrichment_input(
            site_table, protein_sequences=protein_sequences
        )
        occupancy_report = None
        occupancy_counterpart_report = None
        site_quantification = None
        site_group_quantification = None
        if feature_path is not None:
            feature_report = parse_ms1_feature_table(feature_path)
            occupancy_report = build_ptm_site_occupancy_report(
                site_table,
                feature_records=feature_report.accepted_records,
            )
            occupancy_counterpart_report = build_ptm_occupancy_counterpart_report(
                site_table,
                feature_records=feature_report.accepted_records,
            )
            site_quantification = build_ptm_site_quantification_report(
                site_table,
                feature_records=feature_report.accepted_records,
                ambiguity_policy=PtmSiteQuantAmbiguityPolicy(
                    site_quant_ambiguity_policy.lower()
                ),
            )
            site_group_quantification = build_ptm_site_group_quantification_report(
                site_table,
                feature_records=feature_report.accepted_records,
                localization_scoring_report=localization,
                protein_sequences=protein_sequences,
            )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if occupancy_summary_tsv_out is not None and occupancy_report is not None:
        write_output_table_tsv(
            occupancy_summary_tsv_out,
            render_ptm_site_occupancy_summary_tsv(occupancy_report),
        )
    if occupancy_tsv_out is not None and occupancy_report is not None:
        write_output_table_tsv(
            occupancy_tsv_out, render_ptm_site_occupancy_entry_tsv(occupancy_report)
        )
    if (
        occupancy_counterpart_tsv_out is not None
        and occupancy_counterpart_report is not None
    ):
        write_output_table_tsv(
            occupancy_counterpart_tsv_out,
            render_ptm_occupancy_counterpart_tsv(occupancy_counterpart_report),
        )

    payload = {
        "accepted_rows": len(evidence.accepted_records),
        "rejected_rows": len(evidence.rejected_rows),
        "site_table": [entry.to_dict() for entry in site_table],
        "ambiguity_review": ambiguity_review.to_dict(),
        "coverage_report": [entry.to_dict() for entry in coverage],
        "fdr_report": fdr.to_dict(),
        "motif_windows": [entry.to_dict() for entry in motifs],
        "enrichment_input": enrichment.to_dict(),
        "occupancy": [entry.to_dict() for entry in occupancy_report.entries]
        if occupancy_report is not None
        else None,
        "occupancy_report": occupancy_report.to_dict()
        if occupancy_report is not None
        else None,
        "occupancy_counterpart_report": occupancy_counterpart_report.to_dict()
        if occupancy_counterpart_report is not None
        else None,
        "site_quantification": site_quantification.to_dict()
        if site_quantification is not None
        else None,
        "site_group_quantification": site_group_quantification.to_dict()
        if site_group_quantification is not None
        else None,
    }
    _emit_json(payload, out_path=out_path)


__all__ = ["run_ptm_report_command", "run_ptm_summarize_command"]
