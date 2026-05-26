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
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingValueKind,
    NormalizationMethod,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
)
from bijux_proteomics.review import (
    EvidenceGraphConfidenceTier,
    EvidenceGraphDowngradeReason,
    FinalClaimEvidenceTier,
)
from bijux_proteomics.sequences import ProteinIdentityLevel
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle_from_quant_table,
)
from bijux_proteomics_lab.handoffs.qc_feedback import (
    LabRunQcObservation,
    build_lab_run_qc_feedback_report,
)
from bijux_proteomics_lab.outcomes.observations import AssayObservationRecord, QcState
from bijux_proteomics.workflow.protein_mechanism_cards import (
    ProteinMechanismDirection,
    build_protein_mechanism_card_report,
    render_protein_mechanism_card_tsv,
)


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
                claim_ids=("ptm-claim-P04637-S15",),
                source_row_refs=("ptm.tsv:2",),
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
        ),
        summary=PtmEvidenceCardSummary(
            significant_site_count=1,
            card_count=1,
            narrative_claim_count=1,
            regulator_supported_card_count=0,
            motif_annotated_card_count=0,
            crosstalk_supported_card_count=0,
            mechanism_classified_card_count=1,
            ortholog_context_card_count=0,
            functional_context_card_count=0,
            warning_card_count=0,
        ),
        note="synthetic PTM evidence for protein mechanism cards",
    )


def test_build_protein_mechanism_card_report_summarizes_graph_backed_abundance_ptms_and_context(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    values: list[QuantValue] = []
    abundances = {
        "PG001": {
            "C1": 200.0,
            "C2": 220.0,
            "C3": 210.0,
            "T1": 1600.0,
            "T2": 1550.0,
            "T3": 1650.0,
        },
        "PG002": {
            "C1": 1800.0,
            "C2": 1750.0,
            "C3": 1850.0,
            "T1": 200.0,
            "T2": 220.0,
            "T3": 210.0,
        },
        "PG003": {
            "C1": 150.0,
            "C2": 160.0,
            "C3": 140.0,
            "T1": 1400.0,
            "T2": 1450.0,
            "T3": 1500.0,
        },
    }
    for entity_id, entity_values in abundances.items():
        for sample_id, abundance in entity_values.items():
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=MissingValueKind.OBSERVED,
                    source_feature_count=1,
                )
            )
    quant_table = LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=("C1", "C2", "C3", "T1", "T2", "T3"),
        entity_ids=("PG001", "PG002", "PG003"),
        values=tuple(values),
        entity_protein_refs={
            "PG001": ("P04637",),
            "PG002": ("Q9Y243",),
            "PG003": ("O14920",),
        },
        entity_member_peptides={
            "PG001": ("PEPAAA",),
            "PG002": ("PEPDDD",),
            "PG003": ("PEPCCC",),
        },
    )
    fasta_path = tmp_path / "matching_regions.fasta"
    fasta_path.write_text(
        (
            ">sp|P04637|SIGA_HUMAN Signaling protein A\nMPEPAAAK\n"
            ">sp|Q9Y243|SIGB_HUMAN Signaling protein B\nMPEPDDDK\n"
            ">sp|O14920|SIGC_HUMAN Signaling protein C\nMPEPCCCK\n"
        ),
        encoding="utf-8",
    )
    report_bundle = build_biological_result_report_bundle_from_quant_table(
        quant_table,
        design_entries,
        proteins_fasta_path=fasta_path,
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        protein_region_context_tsv_path=_fixture("biological_report_regions.tsv"),
        ptm_evidence_card_report=_synthetic_ptm_evidence_card_report(),
        condition_a="control",
        condition_b="treatment",
    )

    mechanism_report = build_protein_mechanism_card_report(
        report_bundle.graph_report,
        report_bundle.protein_cards,
        ptm_evidence_card_report=_synthetic_ptm_evidence_card_report(),
    )

    card_by_ref = {
        card.representative_protein_ref: card for card in mechanism_report.cards
    }
    p04637_card = card_by_ref["P04637"]
    q9y243_card = card_by_ref["Q9Y243"]

    assert mechanism_report.summary.card_count == report_bundle.summary.protein_count
    assert p04637_card.abundance_change.direction is ProteinMechanismDirection.INCREASED
    assert p04637_card.abundance_change.adjusted_p_value is not None
    assert p04637_card.ptms[0].site_key == "P04637:S15:Phospho"
    assert p04637_card.ptms[0].mechanism_class is PtmMechanismClass.SITE_SPECIFIC
    assert p04637_card.source_row_refs
    assert p04637_card.derived_no_source_reason is None
    assert any(domain.label == "cell_cycle_core" for domain in p04637_card.domains)
    assert any(entry.entry_id == "custom:response" for entry in q9y243_card.pathways)
    assert any(entry.entry_id == "custom:triad" for entry in q9y243_card.complexes)
    assert p04637_card.peptide_support.graph_support_edge_count >= 2
    assert p04637_card.evidence_tier.value == "high_confidence"
    assert "ptm_site_keys" in render_protein_mechanism_card_tsv(mechanism_report)
    assert "source_row_refs" in render_protein_mechanism_card_tsv(mechanism_report)
    assert mechanism_report.summary.ptm_annotated_card_count == 1
    assert mechanism_report.summary.domain_annotated_card_count >= 1
    assert mechanism_report.summary.pathway_annotated_card_count >= 1
    assert mechanism_report.summary.complex_annotated_card_count >= 1


def test_build_protein_mechanism_card_report_keeps_shared_peptide_only_results_distinct_from_strong_cards() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    values: list[QuantValue] = []
    abundances = {
        "PG_UNIQUE": {
            "C1": 120.0,
            "C2": 125.0,
            "C3": 122.0,
            "T1": 520.0,
            "T2": 510.0,
            "T3": 530.0,
        },
        "PG_SHARED_A": {
            "C1": 300.0,
            "C2": 310.0,
            "C3": 305.0,
            "T1": 90.0,
            "T2": 85.0,
            "T3": 88.0,
        },
        "PG_SHARED_B": {
            "C1": 280.0,
            "C2": 285.0,
            "C3": 290.0,
            "T1": 95.0,
            "T2": 92.0,
            "T3": 91.0,
        },
    }
    for entity_id, entity_values in abundances.items():
        for sample_id, abundance in entity_values.items():
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=MissingValueKind.OBSERVED,
                    source_feature_count=1,
                )
            )
    quant_table = LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=("C1", "C2", "C3", "T1", "T2", "T3"),
        entity_ids=("PG_UNIQUE", "PG_SHARED_A", "PG_SHARED_B"),
        values=tuple(values),
        entity_protein_refs={
            "PG_UNIQUE": ("P04637",),
            "PG_SHARED_A": ("Q9Y243",),
            "PG_SHARED_B": ("Q8N158",),
        },
        entity_member_peptides={
            "PG_UNIQUE": ("UNIQUEPEPK",),
            "PG_SHARED_A": ("SHAREDPEPK",),
            "PG_SHARED_B": ("SHAREDPEPK",),
        },
    )

    report_bundle = build_biological_result_report_bundle_from_quant_table(
        quant_table,
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )
    mechanism_report = build_protein_mechanism_card_report(
        report_bundle.graph_report,
        report_bundle.protein_cards,
    )

    by_group = {card.protein_group_id: card for card in mechanism_report.cards}
    unique_card = by_group["PG_UNIQUE"]
    shared_card = by_group["PG_SHARED_A"]

    assert unique_card.evidence_tier.value == "high_confidence"
    assert shared_card.evidence_tier.value == "ambiguous"
    assert shared_card.peptide_support.shared_peptide_count == 1
    assert "shared_peptide_only" in {
        reason.value for reason in shared_card.downgrade_reasons
    }
    assert unique_card.evidence_tier is not shared_card.evidence_tier
    assert mechanism_report.summary.weak_evidence_card_count >= 1


def test_build_protein_mechanism_card_report_downgrades_card_confidence_from_lab_run_qc(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    values: list[QuantValue] = []
    abundances = {
        "PG001": {
            "C1": 200.0,
            "C2": 220.0,
            "C3": 210.0,
            "T1": 1600.0,
            "T2": 1550.0,
            "T3": 1650.0,
        },
        "PG002": {
            "C1": 1800.0,
            "C2": 1750.0,
            "C3": 1850.0,
            "T1": 200.0,
            "T2": 220.0,
            "T3": 210.0,
        },
        "PG003": {
            "C1": 150.0,
            "C2": 160.0,
            "C3": 140.0,
            "T1": 1400.0,
            "T2": 1450.0,
            "T3": 1500.0,
        },
    }
    for entity_id, entity_values in abundances.items():
        for sample_id, abundance in entity_values.items():
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=MissingValueKind.OBSERVED,
                    source_feature_count=1,
                )
            )
    quant_table = LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=("C1", "C2", "C3", "T1", "T2", "T3"),
        entity_ids=("PG001", "PG002", "PG003"),
        values=tuple(values),
        entity_protein_refs={
            "PG001": ("P04637",),
            "PG002": ("Q9Y243",),
            "PG003": ("O14920",),
        },
        entity_member_peptides={
            "PG001": ("PEPAAA",),
            "PG002": ("PEPDDD",),
            "PG003": ("PEPCCC",),
        },
    )
    fasta_path = tmp_path / "lab_qc_confidence.fasta"
    fasta_path.write_text(
        (
            ">sp|P04637|SIGA_HUMAN Signaling protein A\nMPEPAAAK\n"
            ">sp|Q9Y243|SIGB_HUMAN Signaling protein B\nMPEPDDDK\n"
            ">sp|O14920|SIGC_HUMAN Signaling protein C\nMPEPCCCK\n"
        ),
        encoding="utf-8",
    )
    clean_bundle = build_biological_result_report_bundle_from_quant_table(
        quant_table,
        design_entries,
        proteins_fasta_path=fasta_path,
        condition_a="control",
        condition_b="treatment",
    )
    feedback = build_lab_run_qc_feedback_report(
        (
            LabRunQcObservation(
                run_id=design_entries[0].spectra_file,
                sample_id=design_entries[0].sample_id,
                observation=AssayObservationRecord(
                    assay_id="assay_cv_screen",
                    metric="coefficient_of_variation",
                    value=0.35,
                    replicate_values=[0.33, 0.35, 0.37],
                    qc_state=QcState.FAILED,
                    qc_passed=False,
                    dispersion=0.35,
                    normalization_method="median",
                    interpretation_confidence=0.75,
                ),
            ),
        )
    )
    qc_bundle = build_biological_result_report_bundle_from_quant_table(
        quant_table,
        design_entries,
        proteins_fasta_path=fasta_path,
        condition_a="control",
        condition_b="treatment",
        lab_run_qc_feedback_report=feedback,
    )

    clean_card = next(
        card
        for card in clean_bundle.protein_mechanism_cards.cards
        if card.representative_protein_ref == "P04637"
    )
    qc_card = next(
        card
        for card in qc_bundle.protein_mechanism_cards.cards
        if card.representative_protein_ref == "P04637"
    )

    assert clean_card.confidence_tier.value == "high"
    assert qc_card.confidence_tier.value == "moderate"
    assert "poor_run_qc" in {reason.value for reason in qc_card.downgrade_reasons}
    assert qc_card.evidence_tier.value == "moderate"


def test_build_protein_mechanism_card_report_propagates_severe_contradiction_downgrades(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    values: list[QuantValue] = []
    abundances = {
        "PG001": {
            "C1": 200.0,
            "C2": 220.0,
            "C3": 210.0,
            "T1": 1600.0,
            "T2": 1550.0,
            "T3": 1650.0,
        },
        "PG002": {
            "C1": 1800.0,
            "C2": 1750.0,
            "C3": 1850.0,
            "T1": 200.0,
            "T2": 220.0,
            "T3": 210.0,
        },
        "PG003": {
            "C1": 150.0,
            "C2": 160.0,
            "C3": 140.0,
            "T1": 1400.0,
            "T2": 1450.0,
            "T3": 1500.0,
        },
    }
    for entity_id, entity_values in abundances.items():
        for sample_id, abundance in entity_values.items():
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=MissingValueKind.OBSERVED,
                    source_feature_count=1,
                )
            )
    quant_table = LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PROTEIN,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        normalization_method=NormalizationMethod.NONE,
        sample_ids=("C1", "C2", "C3", "T1", "T2", "T3"),
        entity_ids=("PG001", "PG002", "PG003"),
        values=tuple(values),
        entity_protein_refs={
            "PG001": ("P04637",),
            "PG002": ("Q9Y243",),
            "PG003": ("O14920",),
        },
        entity_member_peptides={
            "PG001": ("PEPAAA",),
            "PG002": ("PEPDDD",),
            "PG003": ("PEPCCC",),
        },
    )
    fasta_path = tmp_path / "contradiction_confidence.fasta"
    fasta_path.write_text(
        (
            ">sp|P04637|SIGA_HUMAN Signaling protein A\nMPEPAAAK\n"
            ">sp|Q9Y243|SIGB_HUMAN Signaling protein B\nMPEPDDDK\n"
            ">sp|O14920|SIGC_HUMAN Signaling protein C\nMPEPCCCK\n"
        ),
        encoding="utf-8",
    )
    clean_bundle = build_biological_result_report_bundle_from_quant_table(
        quant_table,
        design_entries,
        proteins_fasta_path=fasta_path,
        condition_a="control",
        condition_b="treatment",
    )
    contradictory_entries = tuple(
        entry
        if entry.subject_node_ref != "PG001"
        else entry.model_copy(
            update={
                "confidence_tier": EvidenceGraphConfidenceTier.LOW,
                "evidence_tier": FinalClaimEvidenceTier.WEAK,
                "downgrade_reasons": (
                    EvidenceGraphDowngradeReason.SEVERE_CONTRADICTION,
                ),
                "rationale": (
                    "graph confidence starts at high and downgrades to weak because "
                    "severe_contradiction"
                ),
            }
        )
        for entry in clean_bundle.graph_report.final_results.entries
    )
    contradictory_graph_report = clean_bundle.graph_report.model_copy(
        update={
            "final_results": clean_bundle.graph_report.final_results.model_copy(
                update={"entries": contradictory_entries}
            )
        }
    )

    clean_card = next(
        card
        for card in build_protein_mechanism_card_report(
            clean_bundle.graph_report,
            clean_bundle.protein_cards,
        ).cards
        if card.representative_protein_ref == "P04637"
    )
    contradictory_card = next(
        card
        for card in build_protein_mechanism_card_report(
            contradictory_graph_report,
            clean_bundle.protein_cards,
        ).cards
        if card.representative_protein_ref == "P04637"
    )

    assert clean_card.confidence_tier.value == "high"
    assert clean_card.evidence_tier.value == "high_confidence"
    assert contradictory_card.confidence_tier.value == "low"
    assert contradictory_card.evidence_tier.value == "weak"
    assert "severe_contradiction" in {
        reason.value for reason in contradictory_card.downgrade_reasons
    }
