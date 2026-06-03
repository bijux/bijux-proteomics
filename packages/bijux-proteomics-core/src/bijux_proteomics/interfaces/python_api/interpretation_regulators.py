# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation regulator Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405

def run_regulator_inference_command(
    input_table: Path,
    regulator_evidence_tsv: Path,
    design_path: Path,
    fasta: Path | None,
    annotation_tsv: Path | None,
    pathway_membership_tsv: Path | None,
    site_differential_tsv: Path | None,
    condition_a: str | None,
    condition_b: str | None,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    regulator_column: str,
    evidence_type_column: str,
    target_protein_ref_column: str,
    target_gene_symbol_column: str,
    target_pathway_id_column: str,
    target_site_key_column: str,
    source_name_column: str,
    source_accession_column: str,
    pathway_id_column: str,
    pathway_name_column: str,
    pathway_source_name_column: str,
    pathway_source_accession_column: str,
    pathway_protein_ref_column: str,
    pathway_gene_symbol_column: str,
    site_key_column: str,
    site_protein_ref_column: str,
    site_log2_fold_change_column: str,
    site_adjusted_p_value_column: str,
    summary_tsv_out: Path | None,
    inference_tsv_out: Path | None,
    unresolved_target_tsv_out: Path | None,
    rejected_evidence_tsv_out: Path | None,
    rejected_site_signal_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(input_table, mapping=mapping)
        design_report = parse_experimental_design_table(design_path)
        if design_report.rejected_rows:
            raise click.ClickException("design table contains rejected rows")
        design_entries = design_report.accepted_entries
        resolved_condition_a, resolved_condition_b = _resolve_cli_contrast(
            design_entries,
            condition_a=condition_a,
            condition_b=condition_b,
        )
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        normalized_table = normalize_label_free_table(
            raw_table,
            method=NormalizationMethod(normalization),
        )
        differential_report = apply_benjamini_hochberg(
            build_differential_abundance_report(
                normalized_table,
                design_entries,
                condition_a=resolved_condition_a,
                condition_b=resolved_condition_b,
            )
        )
        regulator_evidence_report = parse_regulator_evidence_table(
            regulator_evidence_tsv,
            mapping=RegulatorEvidenceColumnMapping(
                regulator=regulator_column,
                evidence_type=evidence_type_column,
                protein_ref=target_protein_ref_column,
                gene_symbol=target_gene_symbol_column,
                pathway_id=target_pathway_id_column,
                site_key=target_site_key_column,
                source_name=source_name_column,
                source_accession=source_accession_column,
            ),
        )
        site_signal_report = (
            None
            if site_differential_tsv is None
            else parse_regulator_site_signal_table(
                site_differential_tsv,
                mapping=RegulatorSiteSignalColumnMapping(
                    site_key=site_key_column,
                    protein_ref=site_protein_ref_column,
                    log2_fold_change=site_log2_fold_change_column,
                    adjusted_p_value=site_adjusted_p_value_column,
                ),
            )
        )
        fasta_records: tuple[NormalizedProteinRecord, ...] = ()
        if fasta is not None:
            fasta_report = parse_fasta_document(
                fasta.read_text(encoding="utf-8"),
                mode=FastaParseMode.STRICT,
            )
            if fasta_report.rejected_records:
                raise click.ClickException("FASTA input contains rejected records")
            fasta_records = fasta_report.accepted_records
        custom_annotations = ()
        if annotation_tsv is not None:
            annotation_report = parse_protein_annotation_table(
                annotation_tsv,
                mapping=ProteinAnnotationColumnMapping(
                    protein_ref="protein_ref",
                    gene_symbol="gene_symbol",
                    description="description",
                    organism="organism",
                    annotation_identifier="annotation_identifier",
                ),
            )
            custom_annotations = annotation_report.accepted_records
        differential_reference_entries = tuple(
            ProteinReferenceEntry(
                row_number=index + 2,
                source_row_id=entry.entity_id,
                input_protein_ref=protein_ref,
                protein_ref=protein_ref,
            )
            for index, entry in enumerate(differential_report.entries)
            for protein_ref in normalized_table.entity_protein_refs.get(
                entry.entity_id, (entry.entity_id,)
            )
        )
        annotation_mapping_report = build_protein_annotation_mapping_report(
            differential_reference_entries,
            fasta_records,
            custom_annotations=custom_annotations,
        )
        pathway_activity_report = None
        pathway_membership_report = None
        if pathway_membership_tsv is not None:
            pathway_membership_report = parse_pathway_membership_table(
                pathway_membership_tsv,
                mapping=PathwayMembershipColumnMapping(
                    pathway_id=pathway_id_column,
                    pathway_name=pathway_name_column,
                    source_name=pathway_source_name_column,
                    source_accession=pathway_source_accession_column,
                    protein_ref=pathway_protein_ref_column,
                    gene_symbol=pathway_gene_symbol_column,
                ),
            )
            pathway_activity_report = build_pathway_activity_report(
                normalized_table,
                pathway_membership_report.accepted_records,
                design_entries=design_entries,
                fasta_records=fasta_records,
                custom_annotations=custom_annotations,
            )
        report = build_regulator_inference_report(
            regulator_evidence_report.accepted_records,
            differential_report,
            protein_refs_by_entity=normalized_table.entity_protein_refs,
            annotation_report=annotation_mapping_report,
            pathway_activity_report=pathway_activity_report,
            site_signal_entries=()
            if site_signal_report is None
            else site_signal_report.accepted_entries,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(summary_tsv_out, render_regulator_inference_summary_tsv(report))
    if inference_tsv_out is not None:
        write_output_table_tsv(inference_tsv_out, render_regulator_inference_tsv(report))
    if unresolved_target_tsv_out is not None:
        write_output_table_tsv(unresolved_target_tsv_out, render_unresolved_regulator_target_tsv(report))
    if rejected_evidence_tsv_out is not None:
        write_output_table_tsv(rejected_evidence_tsv_out, render_rejected_regulator_evidence_tsv(regulator_evidence_report))
    if rejected_site_signal_tsv_out is not None:
        rejected_site_signal_tsv_out.write_text(
            ""
            if site_signal_report is None
            else render_rejected_regulator_site_signal_tsv(site_signal_report),
            encoding="utf-8",
        )

    payload = {
        "accepted_features": len(parse_report.accepted_records),
        "rejected_features": len(parse_report.rejected_rows),
        "contrast": {
            "condition_a": resolved_condition_a,
            "condition_b": resolved_condition_b,
        },
        "regulator_evidence": regulator_evidence_report.to_dict(),
        "pathway_memberships": (
            None if pathway_membership_report is None else pathway_membership_report.to_dict()
        ),
        "site_signal_report": (
            None if site_signal_report is None else site_signal_report.to_dict()
        ),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "inference_tsv": (
                None if inference_tsv_out is None else str(inference_tsv_out)
            ),
            "unresolved_target_tsv": (
                None
                if unresolved_target_tsv_out is None
                else str(unresolved_target_tsv_out)
            ),
            "rejected_evidence_tsv": (
                None
                if rejected_evidence_tsv_out is None
                else str(rejected_evidence_tsv_out)
            ),
            "rejected_site_signal_tsv": (
                None
                if rejected_site_signal_tsv_out is None
                else str(rejected_site_signal_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

def run_ppi_modules_command(
    significant_tsv: Path,
    ppi_edge_tsv: Path,
    protein_set_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    edge_protein_ref_a_column: str,
    edge_protein_ref_b_column: str,
    edge_source_name_column: str,
    edge_source_accession_column: str,
    edge_score_column: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    summary_tsv_out: Path | None,
    edge_tsv_out: Path | None,
    module_tsv_out: Path | None,
    isolated_tsv_out: Path | None,
    module_enrichment_tsv_out: Path | None,
    rejected_edge_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        significant = parse_protein_reference_table(
            significant_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
        )
        edge_report = parse_ppi_edge_table(
            ppi_edge_tsv,
            mapping=PpiEdgeColumnMapping(
                protein_ref_a=edge_protein_ref_a_column,
                protein_ref_b=edge_protein_ref_b_column,
                source_name=edge_source_name_column,
                source_accession=edge_source_accession_column,
                interaction_score=edge_score_column,
            ),
        )
        protein_sets = (
            None
            if protein_set_tsv is None
            else parse_protein_set_table(
                protein_set_tsv,
                mapping=ProteinSetColumnMapping(
                    set_id=set_id_column,
                    protein_ref=set_protein_ref_column,
                    set_name=set_name_column,
                    set_category=set_category_column,
                    source_name=source_name_column,
                    source_accession=source_accession_column,
                ),
            )
        )
        report = build_ppi_network_module_report(
            significant.accepted_entries,
            edge_report.accepted_records,
            protein_set_records=(
                () if protein_sets is None else protein_sets.accepted_records
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(summary_tsv_out, render_ppi_network_module_summary_tsv(report))
    if edge_tsv_out is not None:
        write_output_table_tsv(edge_tsv_out, render_ppi_network_edge_tsv(report))
    if module_tsv_out is not None:
        write_output_table_tsv(module_tsv_out, render_ppi_module_tsv(report))
    if isolated_tsv_out is not None:
        write_output_table_tsv(isolated_tsv_out, render_ppi_isolated_protein_tsv(report))
    if module_enrichment_tsv_out is not None:
        write_output_table_tsv(module_enrichment_tsv_out, render_ppi_module_enrichment_tsv(report))
    if rejected_edge_tsv_out is not None:
        write_output_table_tsv(rejected_edge_tsv_out, render_rejected_ppi_edge_tsv(edge_report))

    payload = {
        "significant": significant.to_dict(),
        "ppi_edges": edge_report.to_dict(),
        "protein_sets": None if protein_sets is None else protein_sets.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "edge_tsv": None if edge_tsv_out is None else str(edge_tsv_out),
            "module_tsv": None if module_tsv_out is None else str(module_tsv_out),
            "isolated_tsv": None if isolated_tsv_out is None else str(isolated_tsv_out),
            "module_enrichment_tsv": (
                None
                if module_enrichment_tsv_out is None
                else str(module_enrichment_tsv_out)
            ),
            "rejected_edge_tsv": (
                None
                if rejected_edge_tsv_out is None
                else str(rejected_edge_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

__all__ = ['run_regulator_inference_command', 'run_ppi_modules_command']
