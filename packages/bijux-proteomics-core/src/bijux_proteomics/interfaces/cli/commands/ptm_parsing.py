# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""PTM parsing and mapping CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("parse-peptide")
@click.argument("modified_peptide")
@click.option("--protein-ref", default=None)
@click.option("--peptide-start-position", type=int, default=None)
@click.option("--sample-id", default=None)
@click.option("--spectrum-id", default=None)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_parse_peptide_command(
    modified_peptide: str,
    protein_ref: str | None,
    peptide_start_position: int | None,
    sample_id: str | None,
    spectrum_id: str | None,
    out_path: Path | None,
) -> None:
    'Parse one PTM peptide into explicit site-local records.'
    return run_ptm_parse_peptide_command(modified_peptide, protein_ref, peptide_start_position, sample_id, spectrum_id, out_path)

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

@click.command("parse-peptides")
@click.argument(
    "peptide_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-ref-column", default="protein_ref", show_default=True)
@click.option(
    "--peptide-start-position-column",
    default="peptide_start_position",
    show_default=True,
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--record-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--site-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_parse_peptides_command(
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
    'Parse a PTM peptide table into peptide and site review ledgers.'
    return run_ptm_parse_peptides_command(peptide_tsv, peptide_column, protein_ref_column, peptide_start_position_column, sample_id_column, spectrum_id_column, summary_tsv_out, record_tsv_out, site_tsv_out, rejected_tsv_out, out_path)

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
        summary_tsv_out.write_text(
            render_ptm_peptide_summary_tsv(report),
            encoding="utf-8",
        )
    if record_tsv_out is not None:
        record_tsv_out.write_text(
            render_ptm_peptide_record_tsv(report),
            encoding="utf-8",
        )
    if site_tsv_out is not None:
        site_tsv_out.write_text(
            render_ptm_peptide_site_tsv(report),
            encoding="utf-8",
        )
    if rejected_tsv_out is not None:
        rejected_tsv_out.write_text(
            render_ptm_peptide_rejected_tsv(report),
            encoding="utf-8",
        )

    _emit_json(report.to_dict(), out_path=out_path)

@click.command("map-sites")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
    "--mapping-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--exact-mapping-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguous-mapping-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unmapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--candidate-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--site-table-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ambiguity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--coverage-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--validation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_map_sites_command(
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
    'Map localized PTM peptides onto protein coordinates and export site tables.'
    return run_ptm_map_sites_command(evidence_tsv, proteins_fasta, sample_column, spectrum_id_column, peptide_column, charge_column, score_column, protein_refs_column, q_value_column, localization_score_column, localization_probability_column, candidate_sites_column, decoy_label_column, protein_separator, site_separator, mapping_tsv_out, exact_mapping_tsv_out, ambiguous_mapping_tsv_out, unmapped_tsv_out, candidate_tsv_out, site_table_tsv_out, ambiguity_tsv_out, coverage_tsv_out, validation_tsv_out, out_path)

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
        localization = build_ptm_localization_scoring_report(
            evidence.accepted_records
        )
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
        mapping_tsv_out.write_text(
            render_ptm_protein_site_mapping_tsv(mappings),
            encoding="utf-8",
        )
    if exact_mapping_tsv_out is not None:
        exact_mapping_tsv_out.write_text(
            render_ptm_protein_site_mapping_tsv(mapping_report.exact_mappings),
            encoding="utf-8",
        )
    if ambiguous_mapping_tsv_out is not None:
        ambiguous_mapping_tsv_out.write_text(
            render_ptm_protein_site_mapping_tsv(mapping_report.ambiguous_mappings),
            encoding="utf-8",
        )
    if unmapped_tsv_out is not None:
        unmapped_tsv_out.write_text(
            render_ptm_unmapped_peptide_tsv(mapping_report.unmapped_peptides),
            encoding="utf-8",
        )
    if candidate_tsv_out is not None:
        candidate_tsv_out.write_text(
            render_ptm_evidence_site_candidate_tsv(evidence),
            encoding="utf-8",
        )
    if site_table_tsv_out is not None:
        site_table_tsv_out.write_text(
            render_ptm_site_table_tsv(site_table),
            encoding="utf-8",
        )
    if ambiguity_tsv_out is not None:
        ambiguity_tsv_out.write_text(
            render_ptm_unlocalized_group_review_tsv(ambiguity_review),
            encoding="utf-8",
        )
    if coverage_tsv_out is not None:
        coverage_tsv_out.write_text(
            render_ptm_site_coverage_tsv(coverage),
            encoding="utf-8",
        )
    if validation_tsv_out is not None:
        validation_tsv_out.write_text(
            render_ptm_coordinate_validation_tsv(validation),
            encoding="utf-8",
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

@click.command("score-localization")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
    "--entry-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_score_localization_command(
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
    'Score PTM localization confidence and export probability review ledgers.'
    return run_ptm_score_localization_command(evidence_tsv, sample_column, spectrum_id_column, peptide_column, charge_column, score_column, protein_refs_column, q_value_column, localization_score_column, localization_probability_column, candidate_sites_column, decoy_label_column, protein_separator, site_separator, fragment_support_json, summary_tsv_out, entry_tsv_out, out_path)

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
        report = build_ptm_localization_scoring_report(
            evidence.accepted_records,
            fragment_ion_support_by_spectrum=fragment_ion_support_by_spectrum,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_ptm_localization_scoring_summary_tsv(report),
            encoding="utf-8",
        )
    if entry_tsv_out is not None:
        entry_tsv_out.write_text(
            render_ptm_localization_scoring_entry_tsv(report),
            encoding="utf-8",
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "rejected_rows": len(evidence.rejected_rows),
            "localization_scoring": report.to_dict(),
        },
        out_path=out_path,
    )

COMMANDS = (
    ptm_parse_peptide_command,
    ptm_parse_peptides_command,
    ptm_map_sites_command,
    ptm_score_localization_command,
)
