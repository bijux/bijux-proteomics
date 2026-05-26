# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm.evidence_cards import (
    PtmEvidenceCard,
    PtmEvidenceCardClaim,
    PtmEvidenceCardClaimKind,
    PtmEvidenceCardDifferentialResult,
    PtmEvidenceCardLocalization,
    PtmEvidenceCardLocalizationObservation,
    PtmEvidenceCardMechanismClassification,
    PtmEvidenceCardMotifEvidence,
    PtmEvidenceCardPolicy,
    PtmEvidenceCardProteinCorrection,
    PtmEvidenceCardReport,
    PtmEvidenceCardSummary,
)
from bijux_proteomics.ptm.differential_analysis import PtmProteinCorrectionMode
from bijux_proteomics.ptm.localization_scoring import (
    PtmLocalizationConfidenceTier,
    PtmLocalizationProbabilitySource,
)
from bijux_proteomics.ptm.mechanism_classification import (
    PtmMechanismClass,
    PtmMechanismReasonCode,
)
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.sequences import ProteinIdentityLevel
from bijux_proteomics.workflow import (
    ProteinEvidenceCardSelectionPolicy,
    build_biological_result_report_bundle,
    build_biological_result_graph_report,
    build_protein_evidence_card_report,
)
from bijux_proteomics.sequences import parse_protein_region_context_tsv


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _synthetic_ptm_evidence_card_report() -> PtmEvidenceCardReport:
    return PtmEvidenceCardReport(
        condition_a="control",
        condition_b="treatment",
        policy=PtmEvidenceCardPolicy(max_adjusted_p_value=0.1),
        cards=(
            PtmEvidenceCard(
                card_id="ptm-card-P04637-S15",
                site_key="P04637:S15:Phospho",
                protein_ref="P04637",
                residue="S",
                position=15,
                modification_name="Phospho",
                target_decoy_label=TargetDecoyLabel.TARGET,
                identity_level=ProteinIdentityLevel.PROTEIN_LEVEL,
                identity_reason="localized peptide evidence resolves the PTM site to one protein accession",
                peptide_evidence=(),
                localization=PtmEvidenceCardLocalization(
                    localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                    localized_peptides=("PEPAAA",),
                    observations=(
                        PtmEvidenceCardLocalizationObservation(
                            spectrum_id="scan=ptm-001",
                            localized_peptide="PEPAAA[Phospho]",
                            peptide_site_index=3,
                            candidate_site_indices=(3,),
                            ambiguity_group="P04637:S15:Phospho",
                            localization_probability=0.99,
                            probability_source=PtmLocalizationProbabilitySource.REPORTED_PROBABILITY,
                            localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                        ),
                    ),
                    best_localization_probability=0.99,
                ),
                differential_result=PtmEvidenceCardDifferentialResult(
                    condition_a="control",
                    condition_b="treatment",
                    observations_a=3,
                    observations_b=3,
                    complete_pair_count=0,
                    mean_log2_abundance_a=20.0,
                    mean_log2_abundance_b=22.0,
                    log2_fold_change=2.0,
                    p_value=0.001,
                    adjusted_p_value=0.01,
                ),
                motif_evidence=PtmEvidenceCardMotifEvidence(),
                mechanism_classification=PtmEvidenceCardMechanismClassification(
                    mechanism_class=PtmMechanismClass.SITE_SPECIFIC,
                    reason_codes=(PtmMechanismReasonCode.RESIDUAL_SITE_EFFECT_AFTER_CORRECTION,),
                    raw_log2_fold_change=2.0,
                    corrected_log2_fold_change=1.5,
                    note="corrected site effect remains strong after accounting for the protein baseline",
                ),
                protein_correction=PtmEvidenceCardProteinCorrection(
                    mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
                    status="corrected",
                    corrected_log2_fold_change=1.5,
                ),
                source_row_refs=("ptm.tsv:2",),
            ),
            PtmEvidenceCard(
                card_id="ptm-card-Q9Y243-Y77",
                site_key="Q9Y243:Y77:Phospho",
                protein_ref="Q9Y243",
                residue="Y",
                position=77,
                modification_name="Phospho",
                target_decoy_label=TargetDecoyLabel.TARGET,
                identity_level=ProteinIdentityLevel.PROTEIN_LEVEL,
                identity_reason="localized peptide evidence resolves the PTM site to one protein accession",
                peptide_evidence=(),
                localization=PtmEvidenceCardLocalization(
                    localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                    localized_peptides=("PEPDDD",),
                    observations=(
                        PtmEvidenceCardLocalizationObservation(
                            spectrum_id="scan=ptm-002",
                            localized_peptide="PEPDDD[Phospho]",
                            peptide_site_index=4,
                            candidate_site_indices=(4,),
                            ambiguity_group="Q9Y243:Y77:Phospho",
                            localization_probability=0.98,
                            probability_source=PtmLocalizationProbabilitySource.REPORTED_PROBABILITY,
                            localization_tier=PtmLocalizationConfidenceTier.HIGH_CONFIDENCE,
                        ),
                    ),
                    best_localization_probability=0.98,
                ),
                differential_result=PtmEvidenceCardDifferentialResult(
                    condition_a="control",
                    condition_b="treatment",
                    observations_a=3,
                    observations_b=3,
                    complete_pair_count=0,
                    mean_log2_abundance_a=18.0,
                    mean_log2_abundance_b=15.0,
                    log2_fold_change=-3.0,
                    p_value=0.002,
                    adjusted_p_value=0.02,
                ),
                motif_evidence=PtmEvidenceCardMotifEvidence(),
                protein_correction=PtmEvidenceCardProteinCorrection(
                    mode=PtmProteinCorrectionMode.NONE,
                    status="not_corrected",
                ),
                source_row_refs=("ptm.tsv:3",),
            ),
        ),
        narrative_claims=(
            PtmEvidenceCardClaim(
                claim_id="ptm-claim-P04637-S15",
                card_id="ptm-card-P04637-S15",
                site_key="P04637:S15:Phospho",
                claim_kind=PtmEvidenceCardClaimKind.DIFFERENTIAL_SITE,
                text="P04637 S15 phosphorylation rises in treatment.",
                source_row_refs=("ptm.tsv:2",),
            ),
            PtmEvidenceCardClaim(
                claim_id="ptm-claim-Q9Y243-Y77",
                card_id="ptm-card-Q9Y243-Y77",
                site_key="Q9Y243:Y77:Phospho",
                claim_kind=PtmEvidenceCardClaimKind.DIFFERENTIAL_SITE,
                text="Q9Y243 Y77 phosphorylation falls in treatment.",
                source_row_refs=("ptm.tsv:3",),
            ),
        ),
        summary=PtmEvidenceCardSummary(
            significant_site_count=2,
            card_count=2,
            narrative_claim_count=2,
            regulator_supported_card_count=0,
            motif_annotated_card_count=0,
            crosstalk_supported_card_count=0,
            mechanism_classified_card_count=1,
            ortholog_context_card_count=0,
            functional_context_card_count=0,
            warning_card_count=0,
        ),
        note="synthetic PTM evidence cards for protein-card PTM summary tests",
    )


def test_build_protein_evidence_card_report_preserves_one_structured_card_per_final_protein() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    bundle = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        context_annotation_tsv_path=_fixture("biological_report_context.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )
    parse_report = parse_ms1_feature_table(
        _fixture("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
            protein_separator=";",
        ),
    )
    quant_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
        top_n=3,
    )

    report = build_protein_evidence_card_report(
        build_biological_result_graph_report(
            quant_table,
            bundle.differential_report,
            design_entries,
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=1.0,
        ),
        quant_table,
        bundle.differential_report,
        bundle.annotation_report,
        protein_sequences={
            "P04637": "MPEPAAAK",
            "Q9Y243": "MPEPDDDK",
            "O14920": "MPEPCCCK",
        },
        selection_policy=ProteinEvidenceCardSelectionPolicy(),
        sample_conditions={entry.sample_id: entry.condition for entry in design_entries},
        context_mapping_report=bundle.context_mapping_report,
        pathway_enrichment_report=bundle.pathway_enrichment_report,
        complex_enrichment_report=bundle.complex_enrichment_report,
        protein_region_context_records=parse_protein_region_context_tsv(
            _fixture("biological_report_regions.tsv")
        ).accepted_records,
    )

    assert report.summary.protein_result_count == len(bundle.differential_report.entries)
    assert len(report.cards) == bundle.summary.protein_count
    assert all(card.card_id.startswith("protein-card:") for card in report.cards)
    assert all(card.graph_claim_node_id.startswith("statistical_result:") for card in report.cards)
    assert all(card.graph_subject_node_id.startswith("protein:") for card in report.cards)
    assert all(card.peptide_count == len(card.peptides) for card in report.cards)
    assert any(card.pathways for card in report.cards)
    assert any(card.context_terms for card in report.cards)
    assert any(card.identity_level.value == "protein_level" for card in report.cards)
    assert any(card.functional_regions for card in report.cards)
    assert any(
        region.supporting_evidence_refs == ("PEPAAA",)
        for card in report.cards
        for region in card.functional_regions
        if card.representative_protein_ref == "P04637"
    )
    assert any(card.warnings for card in report.cards)


def test_build_protein_evidence_card_report_preserves_ptm_site_keys_when_ptm_cards_are_supplied() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    bundle = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )
    parse_report = parse_ms1_feature_table(
        _fixture("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
            protein_separator=";",
        ),
    )
    quant_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
        top_n=3,
    )

    report = build_protein_evidence_card_report(
        build_biological_result_graph_report(
            quant_table,
            bundle.differential_report,
            design_entries,
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=1.0,
        ),
        quant_table,
        bundle.differential_report,
        bundle.annotation_report,
        protein_sequences={
            "P04637": "MPEPAAAK",
            "Q9Y243": "MPEPDDDK",
            "O14920": "MPEPCCCK",
        },
        selection_policy=ProteinEvidenceCardSelectionPolicy(),
        sample_conditions={entry.sample_id: entry.condition for entry in design_entries},
        ptm_evidence_card_report=_synthetic_ptm_evidence_card_report(),
    )

    ptm_sites_by_protein = {
        card.representative_protein_ref: card.ptm_sites for card in report.cards
    }

    assert ptm_sites_by_protein["P04637"] == ("P04637:S15:Phospho",)
    assert ptm_sites_by_protein["Q9Y243"] == ("Q9Y243:Y77:Phospho",)
    assert ptm_sites_by_protein["O14920"] == ()
    assert report.summary.ptm_annotated_card_count == 2
