# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Protein coverage and parsimony Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.identification import (
    ParsimonyVariant,
    assign_confidence_labels,
    assign_razor_peptides,
    build_parsimony_review_report,
    build_peptide_uniqueness_across_database,
    build_protein_coverage_map,
    build_protein_coverage_plot_report,
    build_protein_coverage_review_report,
    build_protein_groups,
    calculate_grouped_fdr,
    calculate_level_specific_fdr,
    calculate_picked_protein_fdr,
    filter_psms_by_fdr,
    infer_proteins_by_parsimony,
    parse_psm_tsv,
    render_parsimony_review_ambiguities_tsv,
    render_parsimony_review_proteins_tsv,
    render_parsimony_review_summary_tsv,
    render_protein_coverage_entries_tsv,
    render_protein_coverage_peptide_coordinates_tsv,
    render_protein_coverage_plot_html,
    render_protein_coverage_plot_positions_tsv,
    render_protein_coverage_plot_svg,
    render_protein_coverage_regions_tsv,
    render_protein_coverage_summary_tsv,
    render_protein_coverage_uncovered_regions_tsv,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FastaParseMode,
    parse_fasta_document,
)
from bijux_proteomics.interfaces.support.output_protocol import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.sequence_support import (
    _build_decoy_policy,
    _build_psm_mapping,
    _filter_review_psms,
)


def run_protein_coverage_command(
    input_tsv: Path,
    fasta_path: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    coverage_tsv_out: Path | None,
    regions_tsv_out: Path | None,
    uncovered_tsv_out: Path | None,
    peptide_coordinate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        accepted_records = filter_psms_by_fdr(
            report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        fasta_report = parse_fasta_document(
            fasta_path.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                row.source_identifier for row in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        review = build_protein_coverage_review_report(
            accepted_records,
            protein_sequences=protein_sequences,
            threshold=threshold,
            score_orientation=score_orientation,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_coverage_summary_tsv(review),
        )
    if coverage_tsv_out is not None:
        _write_text_output(
            coverage_tsv_out,
            render_protein_coverage_entries_tsv(review),
        )
    if regions_tsv_out is not None:
        _write_text_output(
            regions_tsv_out,
            render_protein_coverage_regions_tsv(review),
        )
    if uncovered_tsv_out is not None:
        _write_text_output(
            uncovered_tsv_out,
            render_protein_coverage_uncovered_regions_tsv(review),
        )
    if peptide_coordinate_tsv_out is not None:
        _write_text_output(
            peptide_coordinate_tsv_out,
            render_protein_coverage_peptide_coordinates_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(accepted_records)
    payload["rejected_rows"] = len(report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "coverage_tsv": None if coverage_tsv_out is None else str(coverage_tsv_out),
        "regions_tsv": None if regions_tsv_out is None else str(regions_tsv_out),
        "uncovered_tsv": None if uncovered_tsv_out is None else str(uncovered_tsv_out),
        "peptide_coordinate_tsv": (
            None
            if peptide_coordinate_tsv_out is None
            else str(peptide_coordinate_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)


def run_protein_coverage_plot_command(
    input_tsv: Path,
    fasta_path: Path,
    threshold: float,
    score_orientation: str,
    high_q_value: float,
    medium_q_value: float,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    intensity_column: str | None,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    positions_tsv_out: Path | None,
    svg_out: Path | None,
    html_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
            intensity_column=intensity_column,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        accepted_records = _filter_review_psms(
            report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        fasta_report = parse_fasta_document(
            fasta_path.read_text(),
            mode=FastaParseMode.STRICT,
        )
        if fasta_report.rejected_records:
            rejected = ", ".join(
                row.source_identifier for row in fasta_report.rejected_records
            )
            raise click.ClickException(
                f"FASTA input contains rejected records under strict mode: {rejected}"
            )
        protein_sequences = {
            record.canonical_accession: record.residues
            for record in fasta_report.accepted_records
        }
        plot = build_protein_coverage_plot_report(
            accepted_records,
            protein_sequences=protein_sequences,
            threshold=threshold,
            score_orientation=score_orientation,
            high_q_value=high_q_value,
            medium_q_value=medium_q_value,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if positions_tsv_out is not None:
        _write_text_output(
            positions_tsv_out,
            render_protein_coverage_plot_positions_tsv(plot),
        )
    if svg_out is not None:
        _write_text_output(svg_out, render_protein_coverage_plot_svg(plot))
    if html_out is not None:
        _write_text_output(html_out, render_protein_coverage_plot_html(plot))

    payload = plot.to_dict()
    payload["accepted_rows"] = len(accepted_records)
    payload["rejected_rows"] = len(report.rejected_rows)
    payload["outputs"] = {
        "positions_tsv": None if positions_tsv_out is None else str(positions_tsv_out),
        "svg": None if svg_out is None else str(svg_out),
        "html": None if html_out is None else str(html_out),
    }
    _emit_json(payload, out_path=out_path)


def run_protein_parsimony_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    variant: str,
    review_variants: tuple[str, ...],
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    ambiguity_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=modified_peptide_column,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        filtered_records = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        review = build_parsimony_review_report(
            filtered_records,
            variant=ParsimonyVariant(variant),
            review_variants=tuple(
                ParsimonyVariant(review_variant) for review_variant in review_variants
            ),
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_parsimony_review_summary_tsv(review),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_parsimony_review_proteins_tsv(review),
        )
    if ambiguity_tsv_out is not None:
        _write_text_output(
            ambiguity_tsv_out,
            render_parsimony_review_ambiguities_tsv(review),
        )

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "accepted_rows": len(parse_report.accepted_records),
        "rejected_rows": len(parse_report.rejected_rows),
        "grouped_rows": len(filtered_records),
        **review.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "ambiguity_tsv": None
            if ambiguity_tsv_out is None
            else str(ambiguity_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_infer_proteins_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    fasta_path: Path | None,
    out_path: Path | None,
) -> None:
    try:
        mapping = _build_psm_mapping(
            run_id_column=None,
            spectrum_id_column=spectrum_id_column,
            peptide_column=peptide_column,
            modified_peptide_column=None,
            charge_column=charge_column,
            score_column=score_column,
            q_value_column=q_value_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=None,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        accepted_records = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        level_fdr = calculate_level_specific_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        grouped_charge = calculate_grouped_fdr(
            parse_report.accepted_records,
            group_by="charge_state",
            threshold=threshold,
            score_orientation=score_orientation,
        )
        grouped_modification = calculate_grouped_fdr(
            parse_report.accepted_records,
            group_by="modification_state",
            threshold=threshold,
            score_orientation=score_orientation,
        )
        protein_groups = build_protein_groups(accepted_records)
        confidence_labels = assign_confidence_labels(
            calculate_picked_protein_fdr(
                accepted_records,
                threshold=threshold,
                score_orientation=score_orientation,
                decoy_policy=decoy_policy,
            )
        )
        parsimony = infer_proteins_by_parsimony(accepted_records)
        picked_fdr = calculate_picked_protein_fdr(
            accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
            decoy_policy=decoy_policy,
        )
        protein_sequences: dict[str, str] | None = None
        coverage_payload = None
        uniqueness_payload = None
        if fasta_path is not None:
            fasta_report = parse_fasta_document(
                fasta_path.read_text(), mode=FastaParseMode.STRICT
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
            coverage_payload = [
                entry.to_dict()
                for entry in build_protein_coverage_map(
                    accepted_records,
                    protein_sequences=protein_sequences,
                )
            ]
            uniqueness_payload = [
                entry.to_dict()
                for entry in build_peptide_uniqueness_across_database(
                    tuple(
                        dict.fromkeys(
                            record.canonical_peptide for record in accepted_records
                        )
                    ),
                    protein_records=fasta_report.accepted_records,
                )
            ]
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "input_psms": len(parse_report.accepted_records),
        "accepted_psms": len(accepted_records),
        "level_fdr": level_fdr.to_dict(),
        "grouped_fdr": {
            "charge_state": grouped_charge.to_dict(),
            "modification_state": grouped_modification.to_dict(),
        },
        "protein_groups": [entry.to_dict() for entry in protein_groups],
        "parsimony_proteins": [entry.to_dict() for entry in parsimony],
        "picked_protein_fdr": [entry.to_dict() for entry in picked_fdr],
        "confidence_labels": [entry.to_dict() for entry in confidence_labels],
        "razor_assignments": [
            entry.to_dict() for entry in assign_razor_peptides(accepted_records)
        ],
        "protein_coverage": coverage_payload,
        "database_uniqueness": uniqueness_payload,
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_protein_coverage_command",
    "run_protein_coverage_plot_command",
    "run_protein_parsimony_command",
    "run_infer_proteins_command",
]
