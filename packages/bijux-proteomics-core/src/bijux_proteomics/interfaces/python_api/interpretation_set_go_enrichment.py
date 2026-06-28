# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Interpretation set and GO enrichment Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.interpretation import (
    GoAnnotationColumnMapping,
    GoEnrichmentCorrectionPolicy,
    ProteinReferenceColumnMapping,
    ProteinSetColumnMapping,
    ProteinSetEnrichmentMissingBackgroundPolicy,
    ProteinSetEnrichmentPolicy,
    apply_go_enrichment_multiple_testing,
    build_go_enrichment_report,
    build_protein_set_enrichment_report,
    parse_go_annotation_table,
    parse_protein_reference_table,
    parse_protein_set_table,
    render_go_enrichment_summary_tsv,
    render_go_enrichment_term_tsv,
    render_go_enrichment_unannotated_tsv,
    render_protein_set_enrichment_summary_tsv,
    render_protein_set_enrichment_tsv,
    render_protein_set_universe_gap_tsv,
    render_rejected_go_annotation_tsv,
    render_rejected_protein_set_membership_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol import (
    _emit_json,
)


def run_protein_set_enrichment_command(
    foreground_tsv: Path,
    protein_set_tsv: Path,
    background_tsv: Path | None,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    set_id_column: str,
    set_name_column: str,
    set_category_column: str,
    source_name_column: str,
    source_accession_column: str,
    set_protein_ref_column: str,
    missing_background_policy: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    result_tsv_out: Path | None,
    universe_gap_tsv_out: Path | None,
    rejected_set_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = (
            None
            if background_tsv is None
            else parse_protein_reference_table(
                background_tsv,
                mapping=ProteinReferenceColumnMapping(
                    protein_ref=protein_ref_column,
                    row_id=row_id_column,
                ),
                protein_separator=protein_separator,
            )
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
        report = build_protein_set_enrichment_report(
            foreground.accepted_entries,
            protein_sets.accepted_records,
            background_entries=(
                None if background is None else background.accepted_entries
            ),
            policy=ProteinSetEnrichmentPolicy(
                missing_background_policy=ProteinSetEnrichmentMissingBackgroundPolicy(
                    missing_background_policy
                ),
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(
            summary_tsv_out, render_protein_set_enrichment_summary_tsv(report)
        )
    if result_tsv_out is not None:
        write_output_table_tsv(
            result_tsv_out, render_protein_set_enrichment_tsv(report)
        )
    if universe_gap_tsv_out is not None:
        write_output_table_tsv(
            universe_gap_tsv_out, render_protein_set_universe_gap_tsv(report)
        )
    if rejected_set_tsv_out is not None:
        write_output_table_tsv(
            rejected_set_tsv_out,
            render_rejected_protein_set_membership_tsv(protein_sets),
        )

    payload = {
        "foreground": foreground.to_dict(),
        "background": None if background is None else background.to_dict(),
        "protein_sets": protein_sets.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "result_tsv": None if result_tsv_out is None else str(result_tsv_out),
            "universe_gap_tsv": (
                None if universe_gap_tsv_out is None else str(universe_gap_tsv_out)
            ),
            "rejected_set_tsv": (
                None if rejected_set_tsv_out is None else str(rejected_set_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_go_enrichment_command(
    foreground_tsv: Path,
    background_tsv: Path,
    go_annotation_tsv: Path,
    protein_ref_column: str,
    row_id_column: str,
    protein_separator: str,
    go_protein_ref_column: str,
    go_term_id_column: str,
    go_term_name_column: str,
    go_aspect_column: str,
    evidence_code_column: str,
    max_adjusted_p_value: float,
    min_enrichment_ratio: float,
    summary_tsv_out: Path | None,
    term_tsv_out: Path | None,
    unannotated_tsv_out: Path | None,
    rejected_annotation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        foreground = parse_protein_reference_table(
            foreground_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        background = parse_protein_reference_table(
            background_tsv,
            mapping=ProteinReferenceColumnMapping(
                protein_ref=protein_ref_column,
                row_id=row_id_column,
            ),
            protein_separator=protein_separator,
        )
        annotations = parse_go_annotation_table(
            go_annotation_tsv,
            mapping=GoAnnotationColumnMapping(
                protein_ref=go_protein_ref_column,
                go_term_id=go_term_id_column,
                go_term_name=go_term_name_column,
                go_aspect=go_aspect_column,
                evidence_code=evidence_code_column,
            ),
        )
        report = apply_go_enrichment_multiple_testing(
            build_go_enrichment_report(
                foreground.accepted_entries,
                background.accepted_entries,
                annotations.accepted_records,
            ),
            policy=GoEnrichmentCorrectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_enrichment_ratio=min_enrichment_ratio,
            ),
        )
    except click.ClickException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(
            summary_tsv_out, render_go_enrichment_summary_tsv(report)
        )
    if term_tsv_out is not None:
        write_output_table_tsv(term_tsv_out, render_go_enrichment_term_tsv(report))
    if unannotated_tsv_out is not None:
        write_output_table_tsv(
            unannotated_tsv_out, render_go_enrichment_unannotated_tsv(report)
        )
    if rejected_annotation_tsv_out is not None:
        write_output_table_tsv(
            rejected_annotation_tsv_out, render_rejected_go_annotation_tsv(annotations)
        )

    payload = {
        "foreground": foreground.to_dict(),
        "background": background.to_dict(),
        "go_annotations": annotations.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "term_tsv": None if term_tsv_out is None else str(term_tsv_out),
            "unannotated_tsv": (
                None if unannotated_tsv_out is None else str(unannotated_tsv_out)
            ),
            "rejected_annotation_tsv": (
                None
                if rejected_annotation_tsv_out is None
                else str(rejected_annotation_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = ["run_protein_set_enrichment_command", "run_go_enrichment_command"]
