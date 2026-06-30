# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""PTM parsing and mapping Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
    json,
)
from bijux_proteomics.interfaces.support.ptm_quantification.ptm import (
    PtmLocalizationColumnMapping,
    PtmPeptideColumnMapping,
    build_ptm_ambiguity_review_report,
    build_ptm_localization_scoring_report,
    build_ptm_protein_site_mapping_report,
    build_ptm_site_coverage_report,
    build_ptm_site_table,
    parse_ptm_localization_tsv,
    parse_ptm_peptide,
    parse_ptm_peptide_tsv,
    render_ptm_coordinate_validation_tsv,
    render_ptm_evidence_site_candidate_tsv,
    render_ptm_localization_scoring_entry_tsv,
    render_ptm_localization_scoring_summary_tsv,
    render_ptm_peptide_record_tsv,
    render_ptm_peptide_rejected_tsv,
    render_ptm_peptide_site_tsv,
    render_ptm_peptide_summary_tsv,
    render_ptm_protein_site_mapping_tsv,
    render_ptm_site_coverage_tsv,
    render_ptm_site_table_tsv,
    render_ptm_unlocalized_group_review_tsv,
    render_ptm_unmapped_peptide_tsv,
    validate_ptm_site_coordinates,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FastaParseMode,
    parse_fasta_document,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
)


def run_ptm_parse_peptide_command(
    modified_peptide: str,
    protein_ref: str | None,
    peptide_start_position: int | None,
    sample_id: str | None,
    spectrum_id: str | None,
    out_path: Path | None,
) -> None:
    try:
        record = parse_ptm_peptide(
            modified_peptide,
            protein_ref=protein_ref,
            peptide_start_position=peptide_start_position,
            sample_id=sample_id,
            spectrum_id=spectrum_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    _emit_json(record.to_dict(), out_path=out_path)


def run_ptm_parse_peptides_command(
    peptide_tsv: Path,
    peptide_column: str,
    protein_ref_column: str | None,
    peptide_start_position_column: str | None,
    sample_id_column: str | None,
    spectrum_id_column: str | None,
    summary_tsv_out: Path | None,
    record_tsv_out: Path | None,
    site_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = parse_ptm_peptide_tsv(
            peptide_tsv,
            mapping=PtmPeptideColumnMapping(
                peptide=peptide_column,
                protein_ref=protein_ref_column,
                peptide_start_position=peptide_start_position_column,
                sample_id=sample_id_column,
                spectrum_id=spectrum_id_column,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(summary_tsv_out, render_ptm_peptide_summary_tsv(report))
    if record_tsv_out is not None:
        write_output_table_tsv(record_tsv_out, render_ptm_peptide_record_tsv(report))
    if site_tsv_out is not None:
        write_output_table_tsv(site_tsv_out, render_ptm_peptide_site_tsv(report))
    if rejected_tsv_out is not None:
        write_output_table_tsv(
            rejected_tsv_out, render_ptm_peptide_rejected_tsv(report)
        )

    _emit_json(report.to_dict(), out_path=out_path)


def run_ptm_map_sites_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
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
    mapping_tsv_out: Path | None,
    exact_mapping_tsv_out: Path | None,
    ambiguous_mapping_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    candidate_tsv_out: Path | None,
    site_table_tsv_out: Path | None,
    ambiguity_tsv_out: Path | None,
    coverage_tsv_out: Path | None,
    validation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
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
        mapping_report = build_ptm_protein_site_mapping_report(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        mappings = mapping_report.mappings
        site_table = build_ptm_site_table(mappings)
        localization = build_ptm_localization_scoring_report(evidence.accepted_records)
        ambiguity_review = build_ptm_ambiguity_review_report(
            site_table,
            localization_scoring_report=localization,
            protein_sequences=protein_sequences,
        )
        coverage = build_ptm_site_coverage_report(mappings)
        validation = validate_ptm_site_coordinates(
            mappings,
            protein_sequences=protein_sequences,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if mapping_tsv_out is not None:
        write_output_table_tsv(
            mapping_tsv_out, render_ptm_protein_site_mapping_tsv(mappings)
        )
    if exact_mapping_tsv_out is not None:
        write_output_table_tsv(
            exact_mapping_tsv_out,
            render_ptm_protein_site_mapping_tsv(mapping_report.exact_mappings),
        )
    if ambiguous_mapping_tsv_out is not None:
        write_output_table_tsv(
            ambiguous_mapping_tsv_out,
            render_ptm_protein_site_mapping_tsv(mapping_report.ambiguous_mappings),
        )
    if unmapped_tsv_out is not None:
        write_output_table_tsv(
            unmapped_tsv_out,
            render_ptm_unmapped_peptide_tsv(mapping_report.unmapped_peptides),
        )
    if candidate_tsv_out is not None:
        write_output_table_tsv(
            candidate_tsv_out, render_ptm_evidence_site_candidate_tsv(evidence)
        )
    if site_table_tsv_out is not None:
        write_output_table_tsv(
            site_table_tsv_out, render_ptm_site_table_tsv(site_table)
        )
    if ambiguity_tsv_out is not None:
        write_output_table_tsv(
            ambiguity_tsv_out, render_ptm_unlocalized_group_review_tsv(ambiguity_review)
        )
    if coverage_tsv_out is not None:
        write_output_table_tsv(coverage_tsv_out, render_ptm_site_coverage_tsv(coverage))
    if validation_tsv_out is not None:
        write_output_table_tsv(
            validation_tsv_out, render_ptm_coordinate_validation_tsv(validation)
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "site_candidate_count": sum(
                len(record.site_candidates) for record in evidence.accepted_records
            ),
            "mapping_count": len(mappings),
            "exact_mapping_count": len(mapping_report.exact_mappings),
            "ambiguous_mapping_count": len(mapping_report.ambiguous_mappings),
            "unmapped_peptide_count": len(mapping_report.unmapped_peptides),
            "site_count": len(site_table),
            "ambiguity_count": len(ambiguity_review.unlocalized_groups),
            "ambiguity_review": ambiguity_review.to_dict(),
            "coverage_count": len(coverage),
            "coordinate_validation": validation.to_dict(),
        },
        out_path=out_path,
    )


def run_ptm_score_localization_command(
    evidence_tsv: Path,
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
    entry_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
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
        report = build_ptm_localization_scoring_report(
            evidence.accepted_records,
            fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        write_output_table_tsv(
            summary_tsv_out, render_ptm_localization_scoring_summary_tsv(report)
        )
    if entry_tsv_out is not None:
        write_output_table_tsv(
            entry_tsv_out, render_ptm_localization_scoring_entry_tsv(report)
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "rejected_rows": len(evidence.rejected_rows),
            "localization_scoring": report.to_dict(),
        },
        out_path=out_path,
    )


__all__ = [
    "run_ptm_parse_peptide_command",
    "run_ptm_parse_peptides_command",
    "run_ptm_map_sites_command",
    "run_ptm_score_localization_command",
]
