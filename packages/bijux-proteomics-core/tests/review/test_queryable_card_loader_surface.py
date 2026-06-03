# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
    parse_ptm_localization_tsv,
    parse_ptm_ortholog_site_tsv,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.ptm.cards.evidence_cards import render_ptm_evidence_card_tsv
from bijux_proteomics.ptm.cards.reporting import (
    PtmReportBundle,
    build_ptm_report_bundle,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
import bijux_proteomics.review as review
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.panel_design import TargetedPanelCandidateKind
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
)
from bijux_proteomics.workflow.cards.pathway_evidence_cards import (
    render_pathway_evidence_card_tsv,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    render_protein_evidence_card_tsv,
)
from bijux_proteomics.workflow.cards.sample_evidence_cards import (
    render_sample_evidence_card_tsv,
)
from bijux_proteomics.workflow.pipelines.advanced_targeted import (
    TargetedValidationWorkflowConfig,
    TargetedValidationWorkflowReport,
    render_advanced_targeted_evidence_cards_tsv,
    run_targeted_validation_workflow,
)
from bijux_proteomics.workflow.reports.biological_report_assembly import (
    build_biological_result_report_bundle,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(
        fasta.read_text(encoding="utf-8"), mode=FastaParseMode.STRICT
    )
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def _build_biological_report() -> BiologicalResultReportBundle:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    return build_biological_result_report_bundle(
        _workflow_fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        condition_a="control",
        condition_b="treatment",
    )


def _build_ptm_report() -> PtmReportBundle:
    evidence = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    annotations = parse_ptm_site_annotation_tsv(
        _ptm_fixture("ptm_site_annotations.tsv")
    )
    ortholog_sites = parse_ptm_ortholog_site_tsv(_ptm_fixture("ptm_ortholog_sites.tsv"))
    design_entries = tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )
    return build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=features.accepted_records,
        design_entries=design_entries,
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
        batch_field="",
        motif_selection_policy=PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        annotation_records=annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        ortholog_site_records=ortholog_sites.accepted_records,
        ortholog_source_species="Homo sapiens",
        ortholog_target_species="Mus musculus",
        evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )


def _write_validation_design(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "sample_id\tcondition\treplicate\tfraction\tspectra_file\tidentifications_file",
                "control_r1\tcontrol\t1\t1\tcontrol_r1.raw\tcontrol_r1.tsv",
                "control_r2\tcontrol\t2\t1\tcontrol_r2.raw\tcontrol_r2.tsv",
                "treat_r1\ttreatment\t1\t1\ttreat_r1.raw\ttreat_r1.tsv",
                "treat_r2\ttreatment\t2\t1\ttreat_r2.raw\ttreat_r2.tsv",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_validation_results(path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "ProteinName\tPeptideModifiedSequence\tPrecursorCharge\tPrecursorMz\tFragmentIon\tProductMz\tReplicateName\tArea\tRetentionTime\tPeakQuality",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r1\t25000\t12.50\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r1\t20000\t12.56\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\tcontrol_r2\t27000\t12.48\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\tcontrol_r2\t21000\t12.55\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r1\t120000\t12.51\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r1\t98000\t12.57\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty7\t789.4\ttreat_r2\t118000\t12.52\tpass",
                "P11111\tPEPTIDER\t2\t501.25\ty8\t902.5\ttreat_r2\t95000\t12.58\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r1\t90000\t18.40\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r1\t87000\t18.47\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\tcontrol_r2\t92000\t18.41\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\tcontrol_r2\t86000\t18.48\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r1\t93000\t18.42\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r1\t85000\t18.46\tpass",
                "P22222\tAAAAK\t2\t451.25\ty3\t360.2\ttreat_r2\t91500\t18.40\tpass",
                "P22222\tAAAAK\t2\t451.25\ty4\t431.2\ttreat_r2\t85500\t18.45\tpass",
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _build_targeted_report(tmp_path: Path) -> TargetedValidationWorkflowReport:
    result_path = tmp_path / "targeted_validation.skyline.tsv"
    design_path = tmp_path / "targeted_validation.design.tsv"
    _write_validation_results(result_path)
    _write_validation_design(design_path)
    return run_targeted_validation_workflow(
        TargetedValidationWorkflowConfig(
            result_tsv_path=result_path,
            design_tsv_path=design_path,
            output_dir=tmp_path / "advanced_targeted",
            discovery_claims=(
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="protein:P11111",
                    candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    display_label="P11111 robust candidate",
                    target_protein_ref="P11111",
                    priority_rank=1,
                    final_score=0.92,
                    penalty_total=0.0,
                    discovery_effect_size=1.3,
                    support_count=4,
                    robustness_score=0.88,
                    assay_feasibility_score=0.91,
                    rank_reason_codes=("assay_ready",),
                    ranking_note="strong discovery support",
                ),
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="protein:P22222",
                    candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    display_label="P22222 flat conflict candidate",
                    target_protein_ref="P22222",
                    priority_rank=2,
                    final_score=0.71,
                    penalty_total=0.0,
                    discovery_effect_size=0.9,
                    support_count=3,
                    robustness_score=0.73,
                    assay_feasibility_score=0.84,
                    rank_reason_codes=("assay_ready",),
                    ranking_note="discovery claimed treatment increase",
                ),
                TargetedValidationDiscoveryClaimInput(
                    candidate_id="ptm_site:P33333:S21",
                    candidate_kind=TargetedPanelCandidateKind.PTM_SITE,
                    display_label="P33333 S21 site candidate",
                    target_protein_ref="P33333",
                    site_key="P33333:S21:phosphorylation",
                    priority_rank=3,
                    final_score=0.67,
                    penalty_total=0.0,
                    discovery_effect_size=0.8,
                    support_count=2,
                    robustness_score=0.66,
                    assay_feasibility_score=0.40,
                    rank_reason_codes=("low_assay_feasibility",),
                    ranking_note="site candidate was not converted into a site-specific assay",
                ),
            ),
            panel_assays=(
                TargetedValidationPanelAssayInput(
                    assay_entry_id="assay:P11111:PEPTIDER",
                    biomarker_candidate_id="protein:P11111",
                    biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    biomarker_display_label="P11111 robust candidate",
                    biomarker_priority_rank=1,
                    target_protein_ref="P11111",
                    target_protein_group_id="protein_group_1",
                    gene_symbol="GENE1",
                    peptide_sequence="PEPTIDER",
                    canonical_peptide="PEPTIDER",
                    uniqueness_class=PeptideUniquenessClass.UNIQUE,
                    precursor_charge=2,
                    selected_transition_count=3,
                    exported_transition_count=3,
                    warning_note="assay retained for panel export",
                ),
                TargetedValidationPanelAssayInput(
                    assay_entry_id="assay:P22222:AAAAK",
                    biomarker_candidate_id="protein:P22222",
                    biomarker_candidate_kind=TargetedPanelCandidateKind.PROTEIN,
                    biomarker_display_label="P22222 flat conflict candidate",
                    biomarker_priority_rank=2,
                    target_protein_ref="P22222",
                    target_protein_group_id="protein_group_2",
                    gene_symbol="GENE2",
                    peptide_sequence="AAAAK",
                    canonical_peptide="AAAAK",
                    uniqueness_class=PeptideUniquenessClass.UNIQUE,
                    precursor_charge=2,
                    selected_transition_count=3,
                    exported_transition_count=3,
                    warning_note="assay retained for panel export",
                ),
            ),
            case_condition="treatment",
            control_condition="control",
        )
    )


def test_review_loader_reads_all_governed_card_families(tmp_path: Path) -> None:
    biological_report = _build_biological_report()
    ptm_report = _build_ptm_report()
    targeted_report = _build_targeted_report(tmp_path)

    protein_path = tmp_path / "biological_protein_cards.tsv"
    protein_path.write_text(
        render_protein_evidence_card_tsv(biological_report.protein_cards),
        encoding="utf-8",
    )
    pathway_path = tmp_path / "biological_pathway_cards.tsv"
    pathway_path.write_text(
        render_pathway_evidence_card_tsv(biological_report.pathway_activity_report),
        encoding="utf-8",
    )
    sample_path = tmp_path / "biological_sample_cards.tsv"
    sample_path.write_text(
        render_sample_evidence_card_tsv(biological_report.sample_exploration_report),
        encoding="utf-8",
    )
    assert ptm_report.evidence_cards is not None
    ptm_path = tmp_path / "ptm_evidence_cards.tsv"
    ptm_path.write_text(
        render_ptm_evidence_card_tsv(ptm_report.evidence_cards),
        encoding="utf-8",
    )
    biomarker_path = tmp_path / "advanced_targeted_evidence_cards.tsv"
    biomarker_path.write_text(
        render_advanced_targeted_evidence_cards_tsv(targeted_report.evidence_cards),
        encoding="utf-8",
    )

    loaded = {
        "protein": review.load_standard_card_tsv(protein_path),
        "pathway": review.load_standard_card_tsv(pathway_path),
        "sample": review.load_standard_card_tsv(sample_path),
        "ptm": review.load_standard_card_tsv(ptm_path),
        "biomarker": review.load_standard_card_tsv(biomarker_path),
    }

    assert loaded["protein"]
    assert loaded["pathway"]
    assert loaded["sample"]
    assert loaded["ptm"]
    assert loaded["biomarker"]
    assert all(
        entry.card_kind is review.StandardCardKind.PROTEIN
        for entry in loaded["protein"]
    )
    assert all(
        entry.card_kind is review.StandardCardKind.PATHWAY
        for entry in loaded["pathway"]
    )
    assert all(
        entry.card_kind is review.StandardCardKind.SAMPLE for entry in loaded["sample"]
    )
    assert all(
        entry.card_kind is review.StandardCardKind.PTM for entry in loaded["ptm"]
    )
    assert all(
        entry.card_kind is review.StandardCardKind.BIOMARKER
        for entry in loaded["biomarker"]
    )
    assert all(
        entry.subject_kind is review.StandardCardSubjectKind.BIOMARKER_CANDIDATE
        for entry in loaded["biomarker"]
    )
    assert all(entry.claim for entries in loaded.values() for entry in entries)
    assert all(entry.evidence_for for entries in loaded.values() for entry in entries)
    assert all(
        entry.evidence_against for entries in loaded.values() for entry in entries
    )


def test_review_loader_indexes_cards_by_card_subject_and_source_ids(
    tmp_path: Path,
) -> None:
    biological_report = _build_biological_report()
    protein_path = tmp_path / "biological_protein_cards.tsv"
    protein_path.write_text(
        render_protein_evidence_card_tsv(biological_report.protein_cards),
        encoding="utf-8",
    )

    card_index = review.load_standard_card_index(protein_path)
    representative = card_index.entries[0]

    assert (
        review.find_standard_card_by_card_id(card_index, representative.card_id)
        == representative
    )
    assert representative in review.find_standard_cards_by_subject_id(
        card_index,
        representative.subject_id,
    )
    assert all(
        representative in review.find_standard_cards_by_source_id(card_index, source_id)
        for source_id in representative.source_ids
    )
