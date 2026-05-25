# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""PTM motif and site-annotation CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("motif-enrichment")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "feature_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
    "--ambiguity-policy",
    type=click.Choice(
        [policy.value for policy in PtmSiteQuantAmbiguityPolicy], case_sensitive=False
    ),
    default=PtmSiteQuantAmbiguityPolicy.PRESERVE.value,
    show_default=True,
)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-pairing-field", default=None)
@click.option("--design-covariate", "design_covariates", multiple=True)
@click.option(
    "--protein-correction-mode",
    type=click.Choice(
        [mode.value for mode in PtmProteinCorrectionMode], case_sensitive=False
    ),
    default=PtmProteinCorrectionMode.NONE.value,
    show_default=True,
)
@click.option("--flank-size", default=7, show_default=True, type=int)
@click.option("--max-adjusted-p-value", default=0.1, show_default=True, type=float)
@click.option(
    "--min-absolute-log2-fold-change",
    default=1.0,
    show_default=True,
    type=float,
)
@click.option(
    "--direction",
    type=click.Choice(
        [direction.value for direction in PtmMotifRegulationDirection],
        case_sensitive=False,
    ),
    default=PtmMotifRegulationDirection.BOTH.value,
    show_default=True,
)
@click.option(
    "--include-ambiguous-regulated-sites/--exclude-ambiguous-regulated-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--include-ambiguous-background-sites/--exclude-ambiguous-background-sites",
    default=False,
    show_default=True,
)
@click.option(
    "--background-mode",
    type=click.Choice(
        [mode.value for mode in PtmMotifBackgroundMode],
        case_sensitive=False,
    ),
    default=PtmMotifBackgroundMode.OBSERVED_SITE_BACKGROUND.value,
    show_default=True,
)
@click.option(
    "--min-frequency-difference",
    default=0.1,
    show_default=True,
    type=float,
)
@click.option(
    "--min-enrichment-ratio",
    default=1.5,
    show_default=True,
    type=float,
)
@click.option(
    "--max-reported-term-count",
    default=25,
    show_default=True,
    type=int,
)
@click.option(
    "--window-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--frequency-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--enriched-term-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--logo-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_motif_enrichment_command(
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
    flank_size: int,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    direction: str,
    include_ambiguous_regulated_sites: bool,
    include_ambiguous_background_sites: bool,
    background_mode: str,
    min_frequency_difference: float,
    min_enrichment_ratio: float,
    max_reported_term_count: int,
    window_tsv_out: Path | None,
    frequency_tsv_out: Path | None,
    enriched_term_tsv_out: Path | None,
    logo_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Compare regulated phosphosite sequence motifs against a PTM background set.'
    return run_ptm_motif_enrichment_command(evidence_tsv, proteins_fasta, feature_tsv, design_path, sample_column, spectrum_id_column, peptide_column, charge_column, score_column, protein_refs_column, q_value_column, localization_score_column, localization_probability_column, candidate_sites_column, decoy_label_column, protein_separator, site_separator, ambiguity_policy, normalization, condition_a, condition_b, design_batch_field, design_pairing_field, design_covariates, protein_correction_mode, flank_size, max_adjusted_p_value, min_absolute_log2_fold_change, direction, include_ambiguous_regulated_sites, include_ambiguous_background_sites, background_mode, min_frequency_difference, min_enrichment_ratio, max_reported_term_count, window_tsv_out, frequency_tsv_out, enriched_term_tsv_out, logo_tsv_out, out_path)

def run_ptm_motif_enrichment_command(
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
    flank_size: int,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
    direction: str,
    include_ambiguous_regulated_sites: bool,
    include_ambiguous_background_sites: bool,
    background_mode: str,
    min_frequency_difference: float,
    min_enrichment_ratio: float,
    max_reported_term_count: int,
    window_tsv_out: Path | None,
    frequency_tsv_out: Path | None,
    enriched_term_tsv_out: Path | None,
    logo_tsv_out: Path | None,
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
        differential = build_ptm_differential_analysis_report(
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
        report = build_ptm_phosphosite_motif_enrichment_report(
            differential,
            protein_sequences=protein_sequences,
            flank_size=flank_size,
            selection_policy=PtmPhosphositeSelectionPolicy(
                max_adjusted_p_value=max_adjusted_p_value,
                min_absolute_log2_fold_change=min_absolute_log2_fold_change,
                direction=PtmMotifRegulationDirection(direction.lower()),
                include_ambiguous_regulated_sites=include_ambiguous_regulated_sites,
                include_ambiguous_background_sites=include_ambiguous_background_sites,
            ),
            comparison_policy=PtmMotifComparisonPolicy(
                background_mode=PtmMotifBackgroundMode(background_mode.lower()),
                min_frequency_difference=min_frequency_difference,
                min_enrichment_ratio=min_enrichment_ratio,
                max_reported_term_count=max_reported_term_count,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if window_tsv_out is not None:
        export_ptm_phosphosite_motif_window_tsv(report, window_tsv_out)
    if frequency_tsv_out is not None:
        export_ptm_phosphosite_motif_frequency_tsv(report, frequency_tsv_out)
    if enriched_term_tsv_out is not None:
        export_ptm_phosphosite_motif_enriched_term_tsv(report, enriched_term_tsv_out)
    if logo_tsv_out is not None:
        export_ptm_phosphosite_motif_logo_tsv(report, logo_tsv_out)

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "feature_rows": len(feature_report.accepted_records),
            "protein_correction_mode": differential.protein_correction_mode.value,
            "motif_enrichment_report": report.to_dict(),
            "outputs": {
                "window_tsv": None if window_tsv_out is None else str(window_tsv_out),
                "frequency_tsv": None
                if frequency_tsv_out is None
                else str(frequency_tsv_out),
                "enriched_term_tsv": None
                if enriched_term_tsv_out is None
                else str(enriched_term_tsv_out),
                "logo_tsv": None if logo_tsv_out is None else str(logo_tsv_out),
            },
        },
        out_path=out_path,
    )

@click.command("annotate-sites")
@click.argument(
    "evidence_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "proteins_fasta", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "annotation_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
@click.option("--annotation-species-column", default="species", show_default=True)
@click.option(
    "--annotation-protein-ref-column",
    default="protein_ref",
    show_default=True,
)
@click.option("--annotation-residue-column", default="residue", show_default=True)
@click.option("--annotation-position-column", default="position", show_default=True)
@click.option(
    "--annotation-modification-column",
    default="modification_name",
    show_default=True,
)
@click.option(
    "--annotation-function-column",
    default="site_function",
    show_default=True,
)
@click.option("--annotation-kinase-column", default="kinases", show_default=True)
@click.option(
    "--annotation-phosphatase-column",
    default="phosphatases",
    show_default=True,
)
@click.option("--annotation-pathway-column", default="pathways", show_default=True)
@click.option("--annotation-source-name-column", default="source_name", show_default=True)
@click.option(
    "--annotation-source-accession-column",
    default="source_accession",
    show_default=True,
)
@click.option("--kinase-separator", default=";", show_default=True)
@click.option("--phosphatase-separator", default=";", show_default=True)
@click.option("--pathway-separator", default=";", show_default=True)
@click.option("--species", "target_species", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--mapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--unmapped-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--function-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--kinase-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--phosphatase-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--pathway-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out", "out_path", type=click.Path(path_type=Path, dir_okay=False), default=None
)
def ptm_annotate_sites_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    annotation_tsv: Path,
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
    annotation_species_column: str,
    annotation_protein_ref_column: str,
    annotation_residue_column: str,
    annotation_position_column: str,
    annotation_modification_column: str,
    annotation_function_column: str,
    annotation_kinase_column: str,
    annotation_phosphatase_column: str,
    annotation_pathway_column: str,
    annotation_source_name_column: str,
    annotation_source_accession_column: str,
    kinase_separator: str,
    phosphatase_separator: str,
    pathway_separator: str,
    target_species: str | None,
    summary_tsv_out: Path | None,
    mapped_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    function_tsv_out: Path | None,
    kinase_tsv_out: Path | None,
    phosphatase_tsv_out: Path | None,
    pathway_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Map imported PTM site annotations onto observed PTM sites.'
    return run_ptm_annotate_sites_command(evidence_tsv, proteins_fasta, annotation_tsv, sample_column, spectrum_id_column, peptide_column, charge_column, score_column, protein_refs_column, q_value_column, localization_score_column, localization_probability_column, candidate_sites_column, decoy_label_column, protein_separator, site_separator, annotation_species_column, annotation_protein_ref_column, annotation_residue_column, annotation_position_column, annotation_modification_column, annotation_function_column, annotation_kinase_column, annotation_phosphatase_column, annotation_pathway_column, annotation_source_name_column, annotation_source_accession_column, kinase_separator, phosphatase_separator, pathway_separator, target_species, summary_tsv_out, mapped_tsv_out, unmapped_tsv_out, function_tsv_out, kinase_tsv_out, phosphatase_tsv_out, pathway_tsv_out, out_path)

def run_ptm_annotate_sites_command(
    evidence_tsv: Path,
    proteins_fasta: Path,
    annotation_tsv: Path,
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
    annotation_species_column: str,
    annotation_protein_ref_column: str,
    annotation_residue_column: str,
    annotation_position_column: str,
    annotation_modification_column: str,
    annotation_function_column: str,
    annotation_kinase_column: str,
    annotation_phosphatase_column: str,
    annotation_pathway_column: str,
    annotation_source_name_column: str,
    annotation_source_accession_column: str,
    kinase_separator: str,
    phosphatase_separator: str,
    pathway_separator: str,
    target_species: str | None,
    summary_tsv_out: Path | None,
    mapped_tsv_out: Path | None,
    unmapped_tsv_out: Path | None,
    function_tsv_out: Path | None,
    kinase_tsv_out: Path | None,
    phosphatase_tsv_out: Path | None,
    pathway_tsv_out: Path | None,
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
        resolved_target_species = target_species
        if resolved_target_species is None:
            observed_species = {
                record.organism for record in fasta_report.accepted_records if record.organism
            }
            if len(observed_species) == 1:
                resolved_target_species = next(iter(observed_species))
        mappings = map_ptm_evidence_to_protein_sites(
            evidence.accepted_records,
            protein_sequences=protein_sequences,
        )
        site_table = build_ptm_site_table(mappings)
        annotation_report = parse_ptm_site_annotation_tsv(
            annotation_tsv,
            mapping=PtmSiteAnnotationColumnMapping(
                species=annotation_species_column,
                protein_ref=annotation_protein_ref_column,
                residue=annotation_residue_column,
                position=annotation_position_column,
                modification_name=annotation_modification_column,
                site_function=annotation_function_column,
                kinases=annotation_kinase_column,
                phosphatases=annotation_phosphatase_column,
                pathways=annotation_pathway_column,
                source_name=annotation_source_name_column,
                source_accession=annotation_source_accession_column,
            ),
            kinase_separator=kinase_separator,
            phosphatase_separator=phosphatase_separator,
            pathway_separator=pathway_separator,
        )
        mapping_report = build_ptm_site_annotation_mapping_report(
            site_table,
            annotation_report.accepted_records,
            target_species=resolved_target_species,
        )
        biology_summary = build_ptm_site_annotation_biology_summary(mapping_report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_ptm_site_annotation_mapping_summary_tsv(
            mapping_report,
            summary_tsv_out,
        )
    if mapped_tsv_out is not None:
        export_ptm_mapped_site_annotation_tsv(mapping_report, mapped_tsv_out)
    if unmapped_tsv_out is not None:
        export_ptm_unmapped_site_annotation_tsv(mapping_report, unmapped_tsv_out)
    if function_tsv_out is not None:
        export_ptm_site_annotation_biology_tsv(
            biology_summary,
            category="function",
            path=function_tsv_out,
        )
    if kinase_tsv_out is not None:
        export_ptm_site_annotation_biology_tsv(
            biology_summary,
            category="kinase",
            path=kinase_tsv_out,
        )
    if phosphatase_tsv_out is not None:
        export_ptm_site_annotation_biology_tsv(
            biology_summary,
            category="phosphatase",
            path=phosphatase_tsv_out,
        )
    if pathway_tsv_out is not None:
        export_ptm_site_annotation_biology_tsv(
            biology_summary,
            category="pathway",
            path=pathway_tsv_out,
        )

    _emit_json(
        {
            "accepted_rows": len(evidence.accepted_records),
            "annotation_rows": annotation_report.summary.accepted_record_count,
            "rejected_annotation_rows": annotation_report.summary.rejected_row_count,
            "target_species": resolved_target_species,
            "mapping_report": mapping_report.to_dict(),
            "biology_summary": biology_summary.to_dict(),
            "outputs": {
                "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
                "mapped_tsv": None if mapped_tsv_out is None else str(mapped_tsv_out),
                "unmapped_tsv": None
                if unmapped_tsv_out is None
                else str(unmapped_tsv_out),
                "function_tsv": None
                if function_tsv_out is None
                else str(function_tsv_out),
                "kinase_tsv": None if kinase_tsv_out is None else str(kinase_tsv_out),
                "phosphatase_tsv": None
                if phosphatase_tsv_out is None
                else str(phosphatase_tsv_out),
                "pathway_tsv": None
                if pathway_tsv_out is None
                else str(pathway_tsv_out),
            },
        },
        out_path=out_path,
    )

COMMANDS = (
    ptm_motif_enrichment_command,
    ptm_annotate_sites_command,
)
