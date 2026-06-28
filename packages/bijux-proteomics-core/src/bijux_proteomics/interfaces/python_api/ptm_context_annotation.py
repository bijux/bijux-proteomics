# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""PTM context-annotation Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.ptm_quantification import (
    PtmLocalizationColumnMapping,
    PtmSiteContextColumnMapping,
    build_ptm_site_context_report,
    build_ptm_site_table,
    export_ptm_site_context_summary_tsv,
    export_ptm_site_context_tsv,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    parse_ptm_site_context_tsv,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FastaParseMode,
    parse_fasta_document,
)
from bijux_proteomics.interfaces.support.output_protocol import _emit_json


def run_ptm_annotate_context_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    context_tsv: Path,
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
    context_protein_ref_column: str,
    context_start_column: str,
    context_end_column: str,
    context_domain_column: str | None,
    context_disorder_column: str | None,
    context_transmembrane_column: str | None,
    context_active_site_column: str | None,
    context_motif_column: str | None,
    context_conservation_column: str | None,
    context_source_name_column: str | None,
    context_source_accession_column: str | None,
    summary_tsv_out: Path | None,
    context_tsv_out: Path | None,
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
        context_import_report = parse_ptm_site_context_tsv(
            context_tsv,
            mapping=PtmSiteContextColumnMapping(
                protein_ref=context_protein_ref_column,
                start=context_start_column,
                end=context_end_column,
                domain_name=context_domain_column,
                disorder_region=context_disorder_column,
                transmembrane_region=context_transmembrane_column,
                active_site_label=context_active_site_column,
                motif_name=context_motif_column,
                conservation_score=context_conservation_column,
                source_name=context_source_name_column,
                source_accession=context_source_accession_column,
            ),
        )
        context_report = build_ptm_site_context_report(
            site_table,
            context_import_report.accepted_records,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_ptm_site_context_summary_tsv(context_report, summary_tsv_out)
    if context_tsv_out is not None:
        export_ptm_site_context_tsv(context_report, context_tsv_out)

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "context_rows": context_import_report.summary.accepted_record_count,
            "rejected_context_rows": context_import_report.summary.rejected_row_count,
            "context_report": context_report.to_dict(),
            "outputs": {
                "summary_tsv": None
                if summary_tsv_out is None
                else str(summary_tsv_out),
                "context_tsv": None
                if context_tsv_out is None
                else str(context_tsv_out),
            },
        },
        out_path=out_path,
    )


__all__ = ["run_ptm_annotate_context_command"]
