# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Interpretation mapping Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


def run_map_orthologs_command(
    protein_tsv: Path,
    ortholog_tsv: Path,
    source_species: str,
    target_species: str,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    ortholog_source_species_column: str,
    ortholog_source_protein_ref_column: str,
    ortholog_target_species_column: str,
    ortholog_target_protein_ref_column: str,
    ortholog_source_gene_symbol_column: str,
    ortholog_target_gene_symbol_column: str,
    ortholog_evidence_column: str,
    summary_tsv_out: Path | None,
    mapped_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    rejected_input_tsv_out: Path | None,
    rejected_ortholog_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        protein_table = parse_protein_reference_table(
            protein_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        ortholog_table = parse_ortholog_table(
            ortholog_tsv,
            mapping=OrthologColumnMapping(
                source_species=ortholog_source_species_column,
                source_protein_ref=ortholog_source_protein_ref_column,
                target_species=ortholog_target_species_column,
                target_protein_ref=ortholog_target_protein_ref_column,
                source_gene_symbol=ortholog_source_gene_symbol_column,
                target_gene_symbol=ortholog_target_gene_symbol_column,
                evidence=ortholog_evidence_column,
            ),
        )
        mapping_report = build_ortholog_mapping_report(
            protein_table.accepted_entries,
            ortholog_table.accepted_records,
            source_species=source_species,
            target_species=target_species,
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(
            summary_tsv_out, render_ortholog_mapping_summary_tsv(mapping_report)
        )
    if mapped_tsv_out is not None:
        write_output_table_tsv(
            mapped_tsv_out, render_mapped_ortholog_tsv(mapping_report)
        )
    if unmapped_tsv_out is not None:
        write_output_table_tsv(
            unmapped_tsv_out, render_unmapped_ortholog_tsv(mapping_report)
        )
    if rejected_input_tsv_out is not None:
        write_output_table_tsv(
            rejected_input_tsv_out, render_rejected_protein_reference_tsv(protein_table)
        )
    if rejected_ortholog_tsv_out is not None:
        write_output_table_tsv(
            rejected_ortholog_tsv_out, render_rejected_ortholog_tsv(ortholog_table)
        )

    payload = {
        "protein_table": protein_table.to_dict(),
        "ortholog_table": ortholog_table.to_dict(),
        "mapping_report": mapping_report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "mapped_tsv": None if mapped_tsv_out is None else str(mapped_tsv_out),
            "unmapped_tsv": None if unmapped_tsv_out is None else str(unmapped_tsv_out),
            "rejected_input_tsv": (
                None if rejected_input_tsv_out is None else str(rejected_input_tsv_out)
            ),
            "rejected_ortholog_tsv": (
                None
                if rejected_ortholog_tsv_out is None
                else str(rejected_ortholog_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_protein_set_score_command(
    input_table: Path,
    protein_set_tsv: Path,
    design_path: Path | None,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    minimum_observed_member_count: int,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    sample_score_tsv_out: Path | None,
    condition_score_tsv_out: Path | None,
    condition_comparison_tsv_out: Path | None,
    unresolved_tsv_out: Path | None,
    rejected_set_tsv_out: Path | None,
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
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        protein_sets = parse_protein_set_table(
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
        report = build_protein_set_scoring_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            protein_sets.accepted_records,
            design_entries=design_entries,
            policy=ProteinSetScoringPolicy(
                minimum_observed_member_count=minimum_observed_member_count,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(
            summary_tsv_out, render_protein_set_scoring_summary_tsv(report)
        )
    if matrix_tsv_out is not None:
        write_output_table_tsv(
            matrix_tsv_out, render_protein_set_score_matrix_tsv(report)
        )
    if sample_score_tsv_out is not None:
        write_output_table_tsv(
            sample_score_tsv_out, render_protein_set_sample_score_tsv(report)
        )
    if condition_score_tsv_out is not None:
        write_output_table_tsv(
            condition_score_tsv_out, render_protein_set_condition_score_tsv(report)
        )
    if condition_comparison_tsv_out is not None:
        write_output_table_tsv(
            condition_comparison_tsv_out,
            render_protein_set_condition_comparison_tsv(report),
        )
    if unresolved_tsv_out is not None:
        write_output_table_tsv(
            unresolved_tsv_out, render_protein_set_unresolved_member_tsv(report)
        )
    if rejected_set_tsv_out is not None:
        write_output_table_tsv(
            rejected_set_tsv_out, render_rejected_protein_set_tsv(protein_sets)
        )

    payload = {
        "accepted_features": len(parse_report.accepted_records),
        "rejected_features": len(parse_report.rejected_rows),
        "protein_sets": protein_sets.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
            "sample_score_tsv": (
                None if sample_score_tsv_out is None else str(sample_score_tsv_out)
            ),
            "condition_score_tsv": (
                None
                if condition_score_tsv_out is None
                else str(condition_score_tsv_out)
            ),
            "condition_comparison_tsv": (
                None
                if condition_comparison_tsv_out is None
                else str(condition_comparison_tsv_out)
            ),
            "unresolved_tsv": (
                None if unresolved_tsv_out is None else str(unresolved_tsv_out)
            ),
            "rejected_set_tsv": (
                None if rejected_set_tsv_out is None else str(rejected_set_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = ["run_map_orthologs_command", "run_protein_set_score_command"]
