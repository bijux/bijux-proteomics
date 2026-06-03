# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmDifferentialAnalysisReport,
    PtmEvidenceCardPolicy,
    PtmEvidenceRecord,
    PtmLocalizationConfidenceTier,
    PtmLocalizationProbabilitySource,
    PtmLocalizationScoringEntry,
    PtmLocalizationScoringReport,
    PtmMotifComparisonPolicy,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    PtmSiteDifferentialEntry,
    PtmSiteDifferentialReport,
    PtmSiteEntry,
    build_ptm_differential_analysis_report,
    build_ptm_evidence_card_report,
    build_ptm_localization_scoring_report,
    build_ptm_mechanism_classification_report,
    build_ptm_ortholog_conservation_report,
    build_ptm_phosphosite_motif_enrichment_report,
    build_ptm_regulator_enrichment_report,
    build_ptm_site_annotation_mapping_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    parse_ptm_ortholog_site_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
from bijux_proteomics.sequences import (
    FastaParseMode,
    parse_fasta_document,
    parse_protein_region_context_tsv,
)


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    report = _protein_report()
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _protein_report():
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    return parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)


def _build_evidence_card_report():
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    localization = build_ptm_localization_scoring_report(evidence.accepted_records)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    site_quantification = build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design_entries = tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )
    differential = build_ptm_differential_analysis_report(
        site_quantification,
        design_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        feature_records=features.accepted_records,
    )
    motif_enrichment = build_ptm_phosphosite_motif_enrichment_report(
        differential,
        protein_sequences=_protein_sequences(),
        selection_policy=PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        comparison_policy=PtmMotifComparisonPolicy(),
    )
    annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
    )
    annotation_mapping = build_ptm_site_annotation_mapping_report(
        site_table,
        annotations.accepted_records,
        target_species="Homo sapiens",
    )
    regulator_enrichment = build_ptm_regulator_enrichment_report(
        differential.differential_report,
        annotation_mapping,
        policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
    )
    protein_regions = parse_protein_region_context_tsv(
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "sequences"
        / "protein_region_context.tsv"
    )
    ortholog_sites = parse_ptm_ortholog_site_tsv(_ptm_fixture("ptm_ortholog_sites.tsv"))
    return build_ptm_evidence_card_report(
        evidence.accepted_records,
        site_table,
        localization,
        differential,
        site_quantification=site_quantification,
        motif_enrichment=motif_enrichment,
        regulator_enrichment=regulator_enrichment,
        annotation_mapping_report=annotation_mapping,
        mechanism_classification_report=build_ptm_mechanism_classification_report(
            differential
        ),
        ortholog_conservation_report=build_ptm_ortholog_conservation_report(
            site_table,
            ortholog_sites.accepted_records,
            source_species="Homo sapiens",
            target_species="Mus musculus",
        ),
        protein_records=_protein_report().accepted_records,
        protein_sequences=_protein_sequences(),
        protein_region_context_records=protein_regions.accepted_records,
        policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )


def test_ptm_evidence_cards_preserve_card_ids_claim_links_and_warnings() -> None:
    report = _build_evidence_card_report()

    assert report.summary.card_count == 3
    assert report.summary.narrative_claim_count == 3
    assert all(card.card_id.startswith("ptm-card:") for card in report.cards)
    assert all(card.claim_ids for card in report.cards)
    claim_card_ids = {claim.card_id for claim in report.narrative_claims}
    assert claim_card_ids == {card.card_id for card in report.cards}

    annotated = next(
        card for card in report.cards if card.site_key == "P11111:S5:Phospho"
    )
    low_localization = next(
        card for card in report.cards if card.site_key == "Q9DEC1:S5:Phospho"
    )

    assert annotated.motif_evidence.centered_windows
    assert annotated.functional_regions
    assert annotated.mechanism_classification is not None
    assert annotated.mechanism_classification.mechanism_class.value == "site_specific"
    assert annotated.ortholog_conservation is not None
    assert annotated.ortholog_conservation.status.value == "conserved"
    assert any(
        region.region_kind.value == "signal_peptide"
        for region in annotated.functional_regions
    )
    assert any(
        regulator.regulator == "AKT1" for regulator in annotated.regulator_evidence
    )
    assert annotated.claim_ids
    assert annotated.source_row_refs
    assert annotated.derived_no_source_reason is None
    assert annotated.identity_level.value in {
        "protein_level",
        "gene_level",
        "family_level",
        "ambiguous",
    }
    assert annotated.identity_reason
    assert any(
        warning.code.value == "low_localization"
        for warning in low_localization.warnings
    )
    assert any(
        warning.code.value == "decoy_site" for warning in low_localization.warnings
    )
    assert low_localization.mechanism_classification is not None
    assert (
        low_localization.mechanism_classification.mechanism_class.value == "unsupported"
    )
    assert low_localization.ortholog_conservation is not None
    assert low_localization.ortholog_conservation.status.value == "unmapped"
    assert all(claim.source_row_refs for claim in report.narrative_claims)
    assert all(
        claim.derived_no_source_reason is None for claim in report.narrative_claims
    )


def test_ptm_evidence_cards_do_not_call_exact_isoform_without_unique_peptide() -> None:
    fasta_report = parse_fasta_document(
        ">sp|P11111|GENE_HUMAN Canonical GN=GENE\nMPEPSPEPTIDEKAAA\n"
        ">sp|P11111-2|GENE_HUMAN Isoform 2 GN=GENE\nMPEPSPEPTIDEKAAA\n",
        mode=FastaParseMode.STRICT,
    )
    record = PtmEvidenceRecord(
        spectrum_id="scan=1",
        sample_id="sample-a",
        localized_peptide="PEP[Phospho]TIDEK",
        canonical_peptide="PEPTIDEK",
        sequence="PEPTIDEK",
        charge=2,
        score=42.0,
        q_value=0.01,
        localization_probability=0.98,
        protein_refs=("P11111-2", "P11111"),
        target_decoy_label=TargetDecoyLabel.TARGET,
        localization_score=18.0,
        candidate_site_indices=(3,),
        modification_names=("Phospho",),
        site_candidates=(),
        provenance=ImportedEvidenceProvenance(
            source_engine="ptm-localization",
            source_files=("inline.tsv",),
            source_row_numbers=(2,),
            original_identifiers={"spectrum_id": "scan=1"},
        ),
    )
    site_entry = PtmSiteEntry(
        site_key="P11111-2:P3:Phospho",
        protein_ref="P11111-2",
        residue="P",
        position=3,
        modification_name="Phospho",
        localization_score=18.0,
        best_q_value=0.01,
        spectrum_count=1,
        peptide_count=1,
        localized_peptides=("PEP[Phospho]TIDEK",),
        sample_ids=("sample-a",),
        target_decoy_label=TargetDecoyLabel.TARGET,
        candidate_positions=(3,),
        ambiguous=False,
        shared_peptide=True,
        provenance=record.provenance,
    )
    localization = PtmLocalizationScoringReport(
        entries=(
            PtmLocalizationScoringEntry(
                spectrum_id="scan=1",
                sample_id="sample-a",
                localized_peptide="PEP[Phospho]TIDEK",
                canonical_peptide="PEPTIDEK",
                modification_name="Phospho",
                peptide_site_index=3,
                candidate_site_indices=(3,),
                ambiguity_group="Phospho:3",
                localization_score=18.0,
                localization_probability=0.98,
                probability_source=PtmLocalizationProbabilitySource.REPORTED_PROBABILITY,
                localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                site_determining_ions=(),
                supported_site_determining_ions=(),
                ambiguous=False,
                multi_phosphorylated=False,
                note="reported probability supports the localized site",
            ),
        ),
        ambiguous_entry_count=0,
        confident_entry_count=1,
        high_confidence_entry_count=1,
        supported_entry_count=0,
        refused_entry_count=0,
        multi_phosphorylated_entry_count=0,
        fragment_supported_entry_count=0,
    )
    differential_report = PtmSiteDifferentialReport(
        normalization_method=NormalizationMethod.MEDIAN,
        test_type="welch_t_test",
        condition_a="control",
        condition_b="treated",
        entries=(
            PtmSiteDifferentialEntry(
                site_key="P11111-2:P3:Phospho",
                protein_ref="P11111-2",
                residue="P",
                position=3,
                modification_name="Phospho",
                localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                low_localization=False,
                ambiguous=False,
                shared_peptide=True,
                localized_peptides=("PEP[Phospho]TIDEK",),
                condition_a="control",
                condition_b="treated",
                observations_a=2,
                observations_b=2,
                complete_pair_count=0,
                mean_log2_abundance_a=10.0,
                mean_log2_abundance_b=11.0,
                log2_fold_change=1.0,
                p_value=0.01,
                adjusted_p_value=0.02,
                standard_error=0.1,
                confidence_interval_low=0.8,
                confidence_interval_high=1.2,
                effect_size_cohens_d=1.0,
                protein_log2_fold_change=None,
                protein_adjusted_p_value=None,
                corrected_log2_fold_change=None,
                protein_correction_status="not_requested",
                uncertainty_note=None,
            ),
        ),
        broken_pairs=(),
        note="minimal direct PTM differential report for identity-resolution proof",
    )
    differential = PtmDifferentialAnalysisReport.model_construct(
        protein_correction_mode=PtmProteinCorrectionMode.NONE,
        differential_report=differential_report,
    )

    report = build_ptm_evidence_card_report(
        (record,),
        (site_entry,),
        localization,
        differential,
        protein_records=fasta_report.accepted_records,
    )

    card = report.cards[0]
    assert card.identity_level.value == "protein_level"
    assert "do not isolate one exact isoform" in card.identity_reason


def test_ptm_evidence_cards_preserve_crosstalk_partners_and_summary_counts() -> None:
    site_entries = (
        PtmSiteEntry(
            site_key="P11111:S5:Phospho",
            protein_ref="P11111",
            residue="S",
            position=5,
            modification_name="Phospho",
            localization_score=18.0,
            best_q_value=0.01,
            spectrum_count=1,
            peptide_count=1,
            localized_peptides=("S[Phospho]PEP[Acetyl]TIDEK",),
            sample_ids=("sample-a", "sample-b"),
            target_decoy_label=TargetDecoyLabel.TARGET,
            candidate_positions=(5,),
            ambiguous=False,
            shared_peptide=False,
            provenance=ImportedEvidenceProvenance(
                source_engine="ptm-localization",
                source_files=("inline.tsv",),
                source_row_numbers=(2,),
                original_identifiers={"site_key": "P11111:S5:Phospho"},
            ),
        ),
        PtmSiteEntry(
            site_key="P11111:T9:Acetyl",
            protein_ref="P11111",
            residue="T",
            position=9,
            modification_name="Acetyl",
            localization_score=16.0,
            best_q_value=0.02,
            spectrum_count=1,
            peptide_count=1,
            localized_peptides=("S[Phospho]PEP[Acetyl]TIDEK",),
            sample_ids=("sample-a", "sample-b"),
            target_decoy_label=TargetDecoyLabel.TARGET,
            candidate_positions=(9,),
            ambiguous=False,
            shared_peptide=False,
            provenance=ImportedEvidenceProvenance(
                source_engine="ptm-localization",
                source_files=("inline.tsv",),
                source_row_numbers=(3,),
                original_identifiers={"site_key": "P11111:T9:Acetyl"},
            ),
        ),
    )
    records = (
        PtmEvidenceRecord(
            spectrum_id="scan=1",
            sample_id="sample-a",
            localized_peptide="S[Phospho]PEP[Acetyl]TIDEK",
            canonical_peptide="SPEPTIDEK",
            sequence="SPEPTIDEK",
            charge=2,
            score=42.0,
            q_value=0.01,
            localization_probability=0.98,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            localization_score=18.0,
            candidate_site_indices=(1, 5),
            modification_names=("Phospho", "Acetyl"),
            site_candidates=(),
            provenance=ImportedEvidenceProvenance(
                source_engine="ptm-localization",
                source_files=("inline.tsv",),
                source_row_numbers=(2,),
                original_identifiers={"spectrum_id": "scan=1"},
            ),
        ),
    )
    localization = PtmLocalizationScoringReport(
        entries=(
            PtmLocalizationScoringEntry(
                spectrum_id="scan=1",
                sample_id="sample-a",
                localized_peptide="S[Phospho]PEP[Acetyl]TIDEK",
                canonical_peptide="SPEPTIDEK",
                modification_name="Phospho",
                peptide_site_index=1,
                candidate_site_indices=(1,),
                ambiguity_group="Phospho:1",
                localization_score=18.0,
                localization_probability=0.98,
                probability_source=PtmLocalizationProbabilitySource.REPORTED_PROBABILITY,
                localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                site_determining_ions=(),
                supported_site_determining_ions=(),
                ambiguous=False,
                multi_phosphorylated=False,
                note="reported probability supports the localized site",
            ),
            PtmLocalizationScoringEntry(
                spectrum_id="scan=2",
                sample_id="sample-a",
                localized_peptide="S[Phospho]PEP[Acetyl]TIDEK",
                canonical_peptide="SPEPTIDEK",
                modification_name="Acetyl",
                peptide_site_index=5,
                candidate_site_indices=(5,),
                ambiguity_group="Acetyl:5",
                localization_score=16.0,
                localization_probability=0.96,
                probability_source=PtmLocalizationProbabilitySource.REPORTED_PROBABILITY,
                localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                site_determining_ions=(),
                supported_site_determining_ions=(),
                ambiguous=False,
                multi_phosphorylated=False,
                note="reported probability supports the localized site",
            ),
        ),
        ambiguous_entry_count=0,
        confident_entry_count=2,
        high_confidence_entry_count=2,
        supported_entry_count=0,
        refused_entry_count=0,
        multi_phosphorylated_entry_count=0,
        fragment_supported_entry_count=0,
    )
    differential_report = PtmSiteDifferentialReport(
        normalization_method=NormalizationMethod.MEDIAN,
        test_type="welch_t_test",
        condition_a="control",
        condition_b="treated",
        entries=(
            PtmSiteDifferentialEntry(
                site_key="P11111:S5:Phospho",
                protein_ref="P11111",
                residue="S",
                position=5,
                modification_name="Phospho",
                localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                low_localization=False,
                ambiguous=False,
                shared_peptide=False,
                localized_peptides=("S[Phospho]PEP[Acetyl]TIDEK",),
                condition_a="control",
                condition_b="treated",
                observations_a=2,
                observations_b=2,
                complete_pair_count=0,
                mean_log2_abundance_a=10.0,
                mean_log2_abundance_b=11.0,
                log2_fold_change=1.0,
                p_value=0.01,
                adjusted_p_value=0.02,
                standard_error=0.1,
                confidence_interval_low=0.8,
                confidence_interval_high=1.2,
                effect_size_cohens_d=1.0,
                protein_log2_fold_change=None,
                protein_adjusted_p_value=None,
                corrected_log2_fold_change=None,
                protein_correction_status="not_requested",
                uncertainty_note=None,
            ),
            PtmSiteDifferentialEntry(
                site_key="P11111:T9:Acetyl",
                protein_ref="P11111",
                residue="T",
                position=9,
                modification_name="Acetyl",
                localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                low_localization=False,
                ambiguous=False,
                shared_peptide=False,
                localized_peptides=("S[Phospho]PEP[Acetyl]TIDEK",),
                condition_a="control",
                condition_b="treated",
                observations_a=2,
                observations_b=2,
                complete_pair_count=0,
                mean_log2_abundance_a=10.0,
                mean_log2_abundance_b=10.7,
                log2_fold_change=0.7,
                p_value=0.02,
                adjusted_p_value=0.03,
                standard_error=0.1,
                confidence_interval_low=0.5,
                confidence_interval_high=0.9,
                effect_size_cohens_d=0.8,
                protein_log2_fold_change=None,
                protein_adjusted_p_value=None,
                corrected_log2_fold_change=None,
                protein_correction_status="not_requested",
                uncertainty_note=None,
            ),
        ),
        broken_pairs=(),
        note="minimal direct PTM differential report for crosstalk proof",
    )
    differential = PtmDifferentialAnalysisReport.model_construct(
        protein_correction_mode=PtmProteinCorrectionMode.NONE,
        differential_report=differential_report,
    )
    annotation_mapping = build_ptm_site_annotation_mapping_report(
        site_entries,
        (
            parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
            .accepted_records[0]
            .model_copy(
                update={
                    "protein_ref": "P11111",
                    "residue": "S",
                    "position": 5,
                    "modification_name": "Phospho",
                    "pathways": ("MAPK signaling",),
                }
            ),
            parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
            .accepted_records[0]
            .model_copy(
                update={
                    "protein_ref": "P11111",
                    "residue": "T",
                    "position": 9,
                    "modification_name": "Acetyl",
                    "pathways": ("MAPK signaling",),
                }
            ),
        ),
        target_species=None,
    )

    report = build_ptm_evidence_card_report(
        records,
        site_entries,
        localization,
        differential,
        annotation_mapping_report=annotation_mapping,
        policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )

    assert report.summary.crosstalk_supported_card_count == 2
    assert report.summary.mechanism_classified_card_count == 0
    assert report.summary.ortholog_context_card_count == 0
    first_card = report.cards[0]
    assert first_card.crosstalk_partners
    assert first_card.crosstalk_partners[0].partner_site_key in {
        "P11111:S5:Phospho",
        "P11111:T9:Acetyl",
    }
    assert "MAPK signaling" in first_card.crosstalk_partners[0].evidence_note
