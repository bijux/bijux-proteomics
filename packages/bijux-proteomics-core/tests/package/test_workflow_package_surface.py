# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.targeted as targeted
from bijux_proteomics import workflow
from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    calculate_fragment_ions,
    calculate_peptide_mz,
)
from bijux_proteomics.identification.contracts import (
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
)
from bijux_proteomics.identification.cross_run_reproducibility import (
    CrossRunReproducibilityClass,
)
from bijux_proteomics.identification.peptide_evidence import (
    PeptideEvidenceClass,
    PeptideEvidenceEntry,
)
from bijux_proteomics.interpretation import OrthologRecord, PathwayMemberKind
from bijux_proteomics.io import SpectralLibraryEntry, SpectralLibraryFormat, SpectrumModel, SpectrumPeak
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.quantification import (
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_label_free_intensity_table,
)
from bijux_proteomics.sequences import PeptideUniquenessClass, parse_fasta_document
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics_foundation import DocumentSchema
import yaml


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _write_public_descriptor_copy(
    *,
    source_name: str,
    benchmark_root: Path,
    dataset_id: str,
    accession: str,
) -> None:
    source_path = (
        workflow.public_benchmark_root() / source_name / "dataset.yml"
    )
    payload = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    payload["dataset_id"] = dataset_id
    payload["accession"] = accession
    target_dir = benchmark_root / dataset_id
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "dataset.yml").write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def test_workflow_package_exports_protein_evidence_card_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = workflow.build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )

    assert hasattr(workflow, "build_protein_evidence_card_report")
    assert hasattr(workflow, "build_biological_result_graph_report")
    assert "card_id" in workflow.render_protein_evidence_card_tsv(report.protein_cards)
    assert "graph_claim_node_id" in workflow.render_protein_evidence_card_tsv(
        report.protein_cards
    )
    assert "proteogenomic_support_class" in workflow.render_protein_evidence_card_tsv(
        report.protein_cards
    )
    assert report.protein_cards.summary.protein_result_count == report.summary.protein_count
    assert report.experiment_confidence_report.summary.component_count == 7


def test_workflow_package_exports_protein_mechanism_card_surface(tmp_path: Path) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
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
    report = workflow.build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=fasta_path,
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        protein_region_context_tsv_path=_fixture("biological_report_regions.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    assert hasattr(workflow, "build_protein_mechanism_card_report")
    assert "evidence_tier" in workflow.render_protein_mechanism_card_tsv(
        report.protein_mechanism_cards
    )
    assert report.evidence_aware_ranking_report is not None
    assert "graph_claim_node_id" in workflow.render_protein_mechanism_card_tsv(
        report.protein_mechanism_cards
    )
    assert (
        report.protein_mechanism_cards.summary.card_count
        == report.summary.protein_count
    )
    assert report.protein_mechanism_cards.summary.domain_annotated_card_count >= 1
    assert report.evidence_aware_ranking_report.summary.pathway_entry_count >= 1


def test_workflow_package_exports_core_orchestrator_surface() -> None:
    assert hasattr(workflow, "run_proteomics_workflow")
    assert hasattr(workflow, "export_targeted_assay_qc_workflow_artifacts")
    assert workflow.WorkflowMode.FRAGPIPE.value == "fragpipe"
    assert workflow.TargetedWorkflowStage.ASSAY_QC.value == "assay_qc"


def test_workflow_package_exports_proteomics_study_result_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("diann_biological.design.tsv")
        ).accepted_entries
    )
    diann_workflow = workflow.build_diann_biological_workflow_bundle(
        _fixture("diann_biological_report.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )
    tmt_workflow = workflow.build_tmt_experiment_workflow_bundle(
        Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / "maxquant_tmt_evidence.tsv",
        Path(__file__).resolve().parent.parent / "fixtures" / "multiplex" / "tmt.design.tsv",
        control_channel="126",
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )

    diann_study = workflow.build_proteomics_study_result(diann_workflow)
    tmt_study = workflow.build_proteomics_study_result(tmt_workflow)

    assert hasattr(workflow, "build_proteomics_study_result")
    assert workflow.ProteomicsStudyKind.DIA.value == "dia"
    assert diann_study.design.sample_count == 6
    assert tmt_study.design.sample_count == 8
    assert diann_study.summary.matrix_surface_count == 3
    assert tmt_study.summary.statistic_surface_count == 1


def test_workflow_package_exports_result_manifest_surface() -> None:
    report = workflow.ResultManifestReport(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="result_manifest",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        summary=workflow.ResultManifestSummary(
            schema_version="1.0.0",
            source_report_count=1,
            input_count=1,
            command_count=1,
            file_count=1,
            existing_file_count=1,
            missing_required_file_count=0,
            warning_count=0,
            sample_count=1,
            protein_count=1,
            peptide_count=0,
            ptm_site_count=0,
            pathway_count=0,
            qc_entry_count=0,
            card_count=0,
            graph_node_count=0,
            graph_edge_count=0,
            plot_count=0,
        ),
        source_reports=(
            workflow.ResultManifestSourceReport(
                source_kind=workflow.ResultManifestSourceKind.BIOLOGICAL_REPORT,
                report_dir="biological_report",
                manifest_json="biological_report_manifest.json",
                artifact_count=1,
                required_artifact_count=1,
            ),
        ),
        inputs=(
            workflow.ResultManifestInput(
                input_id="input:1",
                input_kind=workflow.ResultManifestInputKind.ADDITIONAL_INPUT,
                path="features.tsv",
                sha256="abc123",
                byte_size=12,
                note="test input",
            ),
        ),
        commands=(
            workflow.ResultManifestCommand(
                command_id="command:1",
                command_text="biological-report features.tsv design.tsv reference.fasta",
                note="test command",
            ),
        ),
        files=(
            workflow.ResultManifestFileEntry(
                file_id="biological_report:summary_tsv",
                source_kind=workflow.ResultManifestSourceKind.BIOLOGICAL_REPORT,
                artifact_key="summary_tsv",
                relative_path="biological_report_summary.tsv",
                required=True,
                exists=True,
                media_type="text/tab-separated-values",
                byte_size=32,
                sha256="def456",
                row_count=1,
                note="test file",
            ),
        ),
        warnings=(),
        note="test manifest",
    )

    assert hasattr(workflow, "build_result_manifest_from_artifacts")
    assert workflow.ResultManifestSourceKind.PTM_REPORT.value == "ptm_report"
    assert "artifact_key" in workflow.render_result_manifest_file_tsv(report)
    assert "schema_version" in workflow.render_result_manifest_summary_tsv(report)


def test_workflow_package_exports_result_archive_surface() -> None:
    assert hasattr(workflow, "load_result_archive")
    assert workflow.ProteomicsStudyKind.ARCHIVED.value == "archived"


def test_workflow_package_exports_advanced_diann_surface(tmp_path: Path) -> None:
    report = workflow.run_advanced_diann_workflow(
        workflow.AdvancedDiannWorkflowConfig(
            result_tsv_path=_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_package_surface",
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert hasattr(workflow, "run_advanced_diann_workflow")
    assert hasattr(workflow, "render_advanced_diann_protein_decisions_tsv")
    assert report.summary.rejected_evidence_count == 1
    assert report.summary.downgraded_protein_count >= 1
    assert "representative_protein_ref" in workflow.render_advanced_diann_protein_decisions_tsv(
        report.accepted_protein_decisions
    )
    assert workflow.ProteomicsStudyQcKind.ARCHIVED_RESULT.value == "archived_result"


def test_workflow_package_exports_advanced_maxquant_surface(tmp_path: Path) -> None:
    report = workflow.run_advanced_maxquant_workflow(
        workflow.AdvancedMaxquantWorkflowConfig(
            evidence_txt_path=_fixture("maxquant_biological/evidence.txt"),
            peptides_txt_path=_fixture("maxquant_biological/peptides.txt"),
            protein_groups_txt_path=_fixture("maxquant_biological/proteinGroups.txt"),
            design_tsv_path=_fixture("maxquant_biological/design.tsv"),
            proteins_fasta_path=_fixture("biological_report_reference.fasta"),
            output_dir=tmp_path / "advanced_maxquant_package_surface",
            config_path=_fixture("maxquant_biological/maxquant_settings.txt"),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert hasattr(workflow, "run_advanced_maxquant_workflow")
    assert hasattr(workflow, "render_advanced_maxquant_peptide_contributions_tsv")
    assert report.summary.excluded_reverse_or_contaminant_count == 2
    assert "peptide_sequence" in workflow.render_advanced_maxquant_peptide_contributions_tsv(
        report.peptide_contributions
    )


def test_workflow_package_exports_advanced_fragpipe_surface(tmp_path: Path) -> None:
    report = workflow.run_advanced_fragpipe_workflow(
        workflow.AdvancedFragpipeWorkflowConfig(
            psm_tsv_path=_fixture("fragpipe_biological_psms.tsv"),
            design_tsv_path=_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_fixture("biological_report_reference.fasta"),
            output_dir=tmp_path / "advanced_fragpipe_package_surface",
            philosopher_protein_tsv_path=_fixture("fragpipe_biological_proteins.tsv"),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert hasattr(workflow, "run_advanced_fragpipe_workflow")
    assert hasattr(workflow, "render_advanced_fragpipe_discrepancy_tsv")
    assert report.summary.protein_group_discrepancy_count == 2
    assert "discrepancy_reason" in workflow.render_advanced_fragpipe_discrepancy_tsv(
        report.discrepancy_reasons
    )


def test_workflow_package_exports_advanced_ptm_surface(tmp_path: Path) -> None:
    report = workflow.run_advanced_ptm_workflow(
        workflow.AdvancedPtmWorkflowConfig(
            evidence_tsv_path=(
                Path(__file__).resolve().parent.parent
                / "fixtures"
                / "ptm"
                / "localization_results.tsv"
            ),
            proteins_fasta_path=(
                Path(__file__).resolve().parent.parent
                / "fixtures"
                / "fasta"
                / "ptm_sites.fasta"
            ),
            feature_tsv_path=(
                Path(__file__).resolve().parent.parent
                / "fixtures"
                / "ptm"
                / "ptm_features.tsv"
            ),
            design_tsv_path=(
                Path(__file__).resolve().parent.parent
                / "fixtures"
                / "ptm"
                / "ptm.design.tsv"
            ),
            output_dir=tmp_path / "advanced_ptm_package_surface",
            batch_field="",
            condition_a="control",
            condition_b="treated",
        )
    )

    assert hasattr(workflow, "run_advanced_ptm_workflow")
    assert hasattr(workflow, "render_advanced_ptm_excluded_ambiguity_tsv")
    assert report.summary.ambiguous_group_row_count == 2
    assert "group_key" in workflow.render_advanced_ptm_excluded_ambiguity_tsv(
        report.exact_site_exclusion_audit
    )


def test_workflow_package_exports_advanced_tmt_surface(tmp_path: Path) -> None:
    report = workflow.run_advanced_tmt_workflow(
        workflow.AdvancedTmtWorkflowConfig(
            result_tsv_path=(
                Path(__file__).resolve().parent.parent
                / "fixtures"
                / "multiplex"
                / "maxquant_tmt_interference.tsv"
            ),
            design_tsv_path=(
                Path(__file__).resolve().parent.parent
                / "fixtures"
                / "multiplex"
                / "tmt.design.tsv"
            ),
            output_dir=tmp_path / "advanced_tmt_package_surface",
            control_channel="126",
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert hasattr(workflow, "run_advanced_tmt_workflow")
    assert hasattr(workflow, "render_advanced_tmt_evidence_cards_tsv")
    assert report.summary.excluded_protein_count == 1
    assert report.summary.high_interference_peptide_count == 2
    assert "confidence_status" in workflow.render_advanced_tmt_evidence_cards_tsv(
        report.evidence_cards
    )


def test_workflow_package_exports_targeted_validation_workflow_surface(
    tmp_path: Path,
) -> None:
    skyline_path = tmp_path / "targeted_validation.skyline.tsv"
    skyline_path.write_text(
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
            )
        )
        + "\n",
        encoding="utf-8",
    )
    design_path = tmp_path / "targeted_validation.design.tsv"
    design_path.write_text(
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

    report = workflow.run_targeted_validation_workflow(
        workflow.TargetedValidationWorkflowConfig(
            result_tsv_path=skyline_path,
            design_tsv_path=design_path,
            output_dir=tmp_path / "advanced_targeted_package_surface",
            discovery_claims=(
                targeted.TargetedValidationDiscoveryClaimInput(
                    candidate_id="protein:P11111",
                    candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                    display_label="P11111 robust candidate",
                    target_protein_ref="P11111",
                    priority_rank=1,
                    final_score=0.91,
                    penalty_total=0.0,
                    discovery_effect_size=1.0,
                    support_count=4,
                    robustness_score=0.85,
                    assay_feasibility_score=0.92,
                    rank_reason_codes=("assay_ready",),
                    ranking_note="strong validation-ready candidate",
                ),
            ),
            panel_assays=(
                targeted.TargetedValidationPanelAssayInput(
                    assay_entry_id="assay:P11111:PEPTIDER",
                    biomarker_candidate_id="protein:P11111",
                    biomarker_candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
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
            ),
            case_condition="treatment",
            control_condition="control",
        )
    )

    assert hasattr(workflow, "run_targeted_validation_workflow")
    assert hasattr(workflow, "render_advanced_targeted_evidence_cards_tsv")
    assert report.summary.confirmed_count == 1
    assert report.summary.evidence_card_count == 1
    assert "assay_reliability_status" in workflow.render_advanced_targeted_evidence_cards_tsv(
        report.evidence_cards
    )


def test_workflow_package_exports_discovery_to_assay_surface() -> None:
    proteins = parse_fasta_document(
        ">sp|P00001|KIN1 GN=KIN1\nPEPTIDERAAASHALEDKAAAMMMWNQK\n"
    ).accepted_records
    peptide_evidence_entries = (
        PeptideEvidenceEntry(
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            primary_class=PeptideEvidenceClass.STRONG,
            peptide_q_value=0.001,
            accepted=True,
            psm_count=6,
            spectrum_count=6,
            run_count=4,
            detection_frequency=1.0,
            replicate_consistency=0.95,
            condition_specificity=0.1,
            detected_condition_count=2,
            reproducibility_class=CrossRunReproducibilityClass.REPRODUCIBLE,
            best_score=125.0,
            charge_states=(2,),
            run_ids=("run1", "run2", "run3", "run4"),
            protein_refs=("P00001",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            target_decoy_contaminant_class=TargetDecoyContaminantClass.TARGET,
            explanation="strong observed peptide support",
        ),
    )
    precursor_mz = calculate_peptide_mz("PEPTIDER", charge=2)
    fragments = calculate_fragment_ions(
        "PEPTIDER",
        charges=(1,),
        series=(FragmentIonSeries.Y, FragmentIonSeries.B),
    )
    mz_by_label = {
        f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}": fragment.mz_monoisotopic
        for fragment in fragments
    }
    spectral_library_entries = (
        SpectralLibraryEntry(
            library_entry_id="library:PEPTIDER",
            source_format=SpectralLibraryFormat.MGF,
            spectrum_id="library:PEPTIDER",
            precursor_mz=precursor_mz,
            precursor_charge=2,
            peptide_sequence="PEPTIDER",
            canonical_peptide="PEPTIDER",
            modification_count=0,
            protein_refs=("P00001",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            spectrum=SpectrumModel(
                spectrum_id="library:PEPTIDER",
                precursor_mz=precursor_mz,
                precursor_charge=2,
                retention_time_seconds=12.5 * 60.0,
                peaks=(
                    SpectrumPeak(mz=mz_by_label["y7+1"], intensity=1000.0),
                    SpectrumPeak(mz=mz_by_label["y6+1"], intensity=850.0),
                    SpectrumPeak(mz=mz_by_label["y5+1"], intensity=700.0),
                    SpectrumPeak(mz=mz_by_label["b5+1"], intensity=250.0),
                ),
            ),
        ),
    )

    report = workflow.design_assay_from_discovery(
        workflow.DiscoveryAssaySourceResult(
            peptide_evidence_entries=peptide_evidence_entries,
            protein_records=proteins,
            spectral_library_entries=spectral_library_entries,
        ),
        (
            workflow.DiscoveryAssayTargetInput(
                candidate_id="protein:P00001",
                candidate_kind=targeted.TargetedPanelCandidateKind.PROTEIN,
                display_label="KIN1 discovery target",
                target_protein_ref="P00001",
                target_protein_group_id="protein_group_1",
                protein_refs=("P00001",),
                gene_symbol="KIN1",
                priority_rank=1,
                final_score=0.91,
                penalty_total=0.0,
                rank_reason_codes=("assay_ready",),
                discovery_peptides=("PEPTIDER",),
            ),
        ),
        top_peptides_per_target=1,
    )

    assert hasattr(workflow, "design_assay_from_discovery")
    assert hasattr(workflow, "render_discovery_to_assay_targets_tsv")
    assert report.summary.target_count == 1
    assert report.summary.assay_ready_target_count == 1
    assert "assay_feasibility" in workflow.render_discovery_to_assay_targets_tsv(report)


def test_workflow_package_exports_cross_study_protein_harmonization_surface() -> None:
    report = workflow.build_cross_study_protein_harmonization_report_from_observations(
        (
            workflow.CrossStudyProteinObservation(
                observation_id="study_a:card_1",
                study_id="study_a",
                study_label="study a",
                study_kind=workflow.ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="STAT1",
                note="study a card",
            ),
            workflow.CrossStudyProteinObservation(
                observation_id="study_b:card_2",
                study_id="study_b",
                study_label="study b",
                study_kind=workflow.ProteomicsStudyKind.DIA,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="card_2",
                representative_protein_ref="A0A0HUMAN1",
                protein_refs=("A0A0HUMAN1",),
                accession_aliases=("P11111",),
                gene_symbol="STAT1",
                note="study b alias-backed card",
            ),
        )
    )

    assert hasattr(workflow, "build_cross_study_protein_harmonization_report")
    assert workflow.CrossStudyProteinMatchBasis.EXACT_ACCESSION.value == "exact_accession"
    assert report.summary.harmonized_group_count == 1
    assert report.unresolved_entries == ()
    assert "harmonized_id" in workflow.render_cross_study_protein_harmonization_tsv(report)


def test_workflow_package_exports_cross_study_effect_comparison_surface() -> None:
    report = workflow.build_cross_study_effect_comparison_report_from_observations(
        (
            workflow.CrossStudyProteinEffectObservation(
                observation_id="study_a:protein_1",
                study_id="study_a",
                study_label="study a",
                study_kind=workflow.ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="STAT1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.2,
                direction=workflow.CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.8,
                significant=True,
                note="study a effect",
            ),
            workflow.CrossStudyProteinEffectObservation(
                observation_id="study_b:protein_1",
                study_id="study_b",
                study_label="study b",
                study_kind=workflow.ProteomicsStudyKind.DIA,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="A0A0HUMAN1",
                protein_refs=("A0A0HUMAN1",),
                accession_aliases=("P11111",),
                gene_symbol="STAT1",
                condition_a="control",
                condition_b="treated",
                log2_fold_change=-1.1,
                direction=workflow.CrossStudyEffectDirection.DOWN,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.7,
                significant=True,
                note="study b reversed-order effect",
            ),
        )
    )

    assert hasattr(workflow, "build_cross_study_effect_comparison_report")
    assert workflow.CrossStudyEffectComparisonStatus.REPLICATED_HIT.value == "replicated_hit"
    assert report.summary.replicated_hit_count == 1
    assert report.comparisons[0].replicated_hit is True
    assert "comparison_status" in workflow.render_cross_study_effect_comparison_tsv(report)
    assert "replicated_hit" in workflow.render_cross_study_replicated_hit_tsv(report)


def test_workflow_package_exports_cross_study_meta_analysis_surface() -> None:
    report = workflow.build_cross_study_meta_analysis_report_from_observations(
        (
            workflow.CrossStudyProteinEffectObservation(
                observation_id="study_a:protein_1",
                study_id="study_a",
                study_label="study a",
                study_kind=workflow.ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="STAT1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.2,
                direction=workflow.CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                standard_error=0.2,
                confidence_interval_low=0.808,
                confidence_interval_high=1.592,
                robustness_score=0.8,
                significant=True,
                note="study a effect",
            ),
            workflow.CrossStudyProteinEffectObservation(
                observation_id="study_b:protein_1",
                study_id="study_b",
                study_label="study b",
                study_kind=workflow.ProteomicsStudyKind.DIA,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="A0A0HUMAN1",
                protein_refs=("A0A0HUMAN1",),
                accession_aliases=("P11111",),
                gene_symbol="STAT1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=0.8,
                direction=workflow.CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                standard_error=0.4,
                confidence_interval_low=0.016,
                confidence_interval_high=1.584,
                robustness_score=0.7,
                significant=True,
                note="study b effect",
            ),
        )
    )

    assert hasattr(workflow, "build_cross_study_meta_analysis_report")
    assert (
        workflow.CrossStudyMetaAnalysisEffectModel.FIXED_INVERSE_VARIANCE.value
        == "fixed_inverse_variance"
    )
    assert report.summary.combined_entry_count == 1
    assert report.combined_entries[0].combined_log2_fold_change > 0.0
    assert (
        "combined_log2_fold_change"
        in workflow.render_cross_study_meta_analysis_tsv(report)
    )
    assert (
        "fixed_weight_fraction"
        in workflow.render_cross_study_meta_analysis_study_weight_tsv(report)
    )


def test_workflow_package_exports_cross_study_pathway_comparison_surface() -> None:
    report = workflow.build_cross_study_pathway_comparison_report_from_observations(
        (
            workflow.CrossStudyPathwayObservation(
                observation_id="study_a:enrichment:stress_response",
                study_id="study_a",
                study_label="study a",
                study_kind=workflow.ProteomicsStudyKind.LABEL_FREE,
                signal_kind=workflow.CrossStudyPathwaySignalKind.ENRICHMENT,
                pathway_id="reactome:stress_response",
                pathway_name="Stress response",
                source_name="reactome",
                source_accession="R-HSA-123",
                member_kind=PathwayMemberKind.PROTEIN,
                p_value=0.001,
                adjusted_p_value=0.01,
                enrichment_ratio=2.0,
                significant=True,
                total_member_count=20,
                foreground_overlap_count=9,
                background_member_count=10,
                coverage_fraction=0.9,
                note="study a enrichment",
            ),
            workflow.CrossStudyPathwayObservation(
                observation_id="study_b:enrichment:stress_response",
                study_id="study_b",
                study_label="study b",
                study_kind=workflow.ProteomicsStudyKind.DIA,
                signal_kind=workflow.CrossStudyPathwaySignalKind.ENRICHMENT,
                pathway_id="reactome:stress_response",
                pathway_name="Stress response",
                source_name="reactome",
                source_accession="R-HSA-123",
                member_kind=PathwayMemberKind.PROTEIN,
                p_value=0.003,
                adjusted_p_value=0.02,
                enrichment_ratio=1.7,
                significant=True,
                total_member_count=18,
                foreground_overlap_count=5,
                background_member_count=10,
                coverage_fraction=0.5,
                note="study b enrichment",
            ),
        )
    )

    assert hasattr(workflow, "build_cross_study_pathway_comparison_report")
    assert workflow.CrossStudyPathwayComparisonStatus.SHARED_SIGNAL.value == "shared_signal"
    assert report.summary.shared_signal_count == 1
    assert report.comparisons[0].coverage_fraction_range == 0.4
    assert "comparison_status" in workflow.render_cross_study_pathway_comparison_tsv(report)
    assert "shared_signal" in workflow.render_cross_study_shared_pathway_signal_tsv(report)


def test_workflow_package_exports_multi_study_comparison_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    biological_report = workflow.build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        build_experiment_design(design_entries),
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    report = workflow.compare_studies(
        (
            workflow.CrossStudyProteinStudyInput(
                study_id="study_a",
                study_result=workflow.build_proteomics_study_result(biological_report),
                species="Homo sapiens",
            ),
            workflow.CrossStudyProteinStudyInput(
                study_id="study_b",
                study_result=workflow.build_proteomics_study_result(biological_report),
                species="Homo sapiens",
            ),
        )
    )

    assert hasattr(workflow, "compare_studies")
    assert hasattr(workflow, "render_multi_study_comparison_summary_tsv")
    assert report.summary.harmonized_protein_group_count >= 1
    assert report.summary.shared_effect_count >= 1
    assert "harmonized_protein_group_count" in workflow.render_multi_study_comparison_summary_tsv(
        report
    )
    assert "harmonized_id" in workflow.render_multi_study_harmonized_proteins_tsv(report)


def test_workflow_package_exports_cross_species_effect_comparison_surface() -> None:
    report = workflow.build_cross_species_effect_comparison_report_from_observations(
        (
            workflow.CrossStudyProteinEffectObservation(
                observation_id="human:protein_1",
                study_id="human",
                study_label="human study",
                study_kind=workflow.ProteomicsStudyKind.LABEL_FREE,
                species="Homo sapiens",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="P11111",
                protein_refs=("P11111",),
                accession_aliases=(),
                gene_symbol="STAT1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=1.2,
                direction=workflow.CrossStudyEffectDirection.UP,
                p_value=0.001,
                adjusted_p_value=0.01,
                robustness_score=0.8,
                significant=True,
                note="human effect",
            ),
            workflow.CrossStudyProteinEffectObservation(
                observation_id="mouse:protein_1",
                study_id="mouse",
                study_label="mouse study",
                study_kind=workflow.ProteomicsStudyKind.DDA,
                species="Mus musculus",
                source_kind=workflow.CrossStudyProteinObservationSourceKind.PROTEIN_EVIDENCE_CARD,
                source_surface="protein_cards",
                source_entity_id="protein_1",
                representative_protein_ref="Q9MOUSE1",
                protein_refs=("Q9MOUSE1",),
                accession_aliases=(),
                gene_symbol="Stat1",
                condition_a="treated",
                condition_b="control",
                log2_fold_change=0.9,
                direction=workflow.CrossStudyEffectDirection.UP,
                p_value=0.002,
                adjusted_p_value=0.02,
                robustness_score=0.7,
                significant=True,
                note="mouse effect",
            ),
        ),
        ortholog_records=(
            OrthologRecord(
                source_species="Homo sapiens",
                source_protein_ref="P11111",
                target_species="Mus musculus",
                target_protein_ref="Q9MOUSE1",
            ),
        ),
    )

    assert hasattr(workflow, "build_cross_species_effect_comparison_report")
    assert (
        workflow.CrossSpeciesEffectEvidenceStatus.CONSERVED_EFFECT.value
        == "conserved_effect"
    )
    assert report.summary.conserved_effect_count == 1
    assert report.comparisons[0].target_protein_ref == "Q9MOUSE1"
    assert "evidence_status" in workflow.render_cross_species_effect_comparison_tsv(report)


def test_workflow_package_exports_cohort_stratification_surface() -> None:
    report = workflow.build_cohort_stratification_report(
        build_label_free_intensity_table(
            tuple(
                Ms1FeatureRecord(
                    feature_id=f"pkg-001-{sample_id.lower()}",
                    sample_id=sample_id,
                    peptide="PEP01",
                    canonical_peptide="PEP01",
                    intensity=abundance,
                    protein_refs=("P04637",),
                    missing_value_kind=MissingValueKind.OBSERVED,
                )
                for sample_id, abundance in {
                    "MC1": 100.0,
                    "MC2": 110.0,
                    "MT1": 1000.0,
                    "MT2": 1100.0,
                    "FC1": 200.0,
                    "FC2": 210.0,
                    "FT1": 205.0,
                    "FT2": 215.0,
                }.items()
            )
            + tuple(
                Ms1FeatureRecord(
                    feature_id=f"pkg-002-{sample_id.lower()}",
                    sample_id=sample_id,
                    peptide="PEP02",
                    canonical_peptide="PEP02",
                    intensity=abundance,
                    protein_refs=("P62993",),
                    missing_value_kind=MissingValueKind.OBSERVED,
                )
                for sample_id, abundance in {
                    "MC1": 500.0,
                    "MC2": 520.0,
                    "MT1": 1100.0,
                    "MT2": 1120.0,
                    "FC1": 600.0,
                    "FC2": 620.0,
                    "FT1": 180.0,
                    "FT2": 190.0,
                }.items()
            ),
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        (
            ExperimentalDesignEntry(
                sample_id="MC1",
                condition="control",
                replicate=1,
                fraction=1,
                spectra_file="mc1.mzml",
                batch="batch-a",
                metadata={"sex": "male"},
            ),
            ExperimentalDesignEntry(
                sample_id="MC2",
                condition="control",
                replicate=2,
                fraction=1,
                spectra_file="mc2.mzml",
                batch="batch-b",
                metadata={"sex": "male"},
            ),
            ExperimentalDesignEntry(
                sample_id="MT1",
                condition="treatment",
                replicate=1,
                fraction=1,
                spectra_file="mt1.mzml",
                batch="batch-a",
                metadata={"sex": "male"},
            ),
            ExperimentalDesignEntry(
                sample_id="MT2",
                condition="treatment",
                replicate=2,
                fraction=1,
                spectra_file="mt2.mzml",
                batch="batch-b",
                metadata={"sex": "male"},
            ),
            ExperimentalDesignEntry(
                sample_id="FC1",
                condition="control",
                replicate=3,
                fraction=1,
                spectra_file="fc1.mzml",
                batch="batch-c",
                metadata={"sex": "female"},
            ),
            ExperimentalDesignEntry(
                sample_id="FC2",
                condition="control",
                replicate=4,
                fraction=1,
                spectra_file="fc2.mzml",
                batch="batch-d",
                metadata={"sex": "female"},
            ),
            ExperimentalDesignEntry(
                sample_id="FT1",
                condition="treatment",
                replicate=3,
                fraction=1,
                spectra_file="ft1.mzml",
                batch="batch-c",
                metadata={"sex": "female"},
            ),
            ExperimentalDesignEntry(
                sample_id="FT2",
                condition="treatment",
                replicate=4,
                fraction=1,
                spectra_file="ft2.mzml",
                batch="batch-d",
                metadata={"sex": "female"},
            ),
        ),
        condition_a="control",
        condition_b="treatment",
    )

    assert hasattr(workflow, "build_cohort_stratification_report")
    assert (
        workflow.CohortStratumStatus.BLOCKED_LOW_SUBGROUP_SAMPLE_COUNT.value
        == "blocked_low_subgroup_sample_count"
    )
    assert report.summary.supported_stratum_count == 2
    assert "interaction_delta" in workflow.render_cohort_interaction_candidate_tsv(report)


def test_workflow_package_exports_public_benchmark_runner_surface() -> None:
    descriptor = workflow.load_public_benchmark_descriptor(
        workflow.public_benchmark_root()
        / "ptm_localization_review_package"
        / "dataset.yml"
    )

    assert hasattr(workflow, "run_public_benchmark_descriptor_suite")
    assert descriptor.dataset_id == "ptm_localization_review_package"
    assert descriptor.sample_metadata[0].sample_id == "C1"
    assert descriptor.expected_biological_signals[0].subject_id == "P11111:S5:Phospho"
    assert workflow.resolve_public_benchmark_root(Path("benchmarks/public")) == (
        workflow.public_benchmark_root()
    )
    assert hasattr(workflow, "render_public_benchmark_suite_signal_assessments_tsv")


def test_workflow_package_exports_public_benchmark_subset_surface() -> None:
    descriptor = workflow.load_public_benchmark_descriptor(
        workflow.public_benchmark_root()
        / "lfq_cohort_review_package"
        / "dataset.yml"
    )
    report = workflow.build_public_benchmark_subset(
        descriptor,
        max_samples=2,
        max_entities=1,
    )

    assert hasattr(workflow, "build_public_benchmark_subset")
    assert report.selected_sample_ids == ("C1", "T1")
    assert report.expected_count_ranges


def test_workflow_package_exports_synthetic_quant_truth_surface() -> None:
    report = workflow.generate_quant_truth_dataset(
        workflow.SyntheticQuantTruthConfig(
            dataset_id="workflow_synthetic_quant_truth_fixture",
            reference_condition="control",
            effect_condition="treatment",
            samples=(
                workflow.SyntheticQuantSample(
                    sample_id="C1",
                    condition="control",
                    replicate=1,
                    batch_id="batch_a",
                ),
                workflow.SyntheticQuantSample(
                    sample_id="T1",
                    condition="treatment",
                    replicate=1,
                    batch_id="batch_b",
                ),
            ),
            changed_proteins=(
                workflow.SyntheticQuantChangedProteinSpec(
                    protein_id="P_UP",
                    peptide_ids=("P_UP_P1", "P_UP_P2"),
                    baseline_log2_intensity=10.0,
                    effect_log2_fold_change=1.25,
                ),
            ),
            unchanged_proteins=(
                workflow.SyntheticQuantProteinSpec(
                    protein_id="P_STABLE",
                    peptide_ids=("P_STABLE_P1",),
                    baseline_log2_intensity=9.0,
                ),
            ),
        )
    )

    assert hasattr(workflow, "generate_quant_truth_dataset")
    assert hasattr(workflow, "render_synthetic_quant_truth_tsv")
    assert report.truth_records[0].truth_kind == "changed_protein"
    assert "truth_kind" in workflow.render_synthetic_quant_truth_tsv(report)


def test_workflow_package_exports_trust_bundle_surface(tmp_path: Path) -> None:
    report = workflow.build_public_benchmark_trust_bundle(
        workflow.public_benchmark_root(),
        output_dir=tmp_path / "trust_bundle",
    )

    assert hasattr(workflow, "build_public_benchmark_trust_bundle")
    assert report.suite_report.passed_count == 8
    assert report.evidence_graph_artifacts
    assert Path(report.html_index_path).exists()


def test_workflow_package_exports_public_dataset_comparison_surface(
    tmp_path: Path,
) -> None:
    report = workflow.build_public_dataset_comparison_report(
        workflow.public_benchmark_root(),
        run_output_root=tmp_path / "public_dataset_runs",
    )

    assert hasattr(workflow, "build_public_dataset_comparison_report")
    assert workflow.PublicDatasetComparisonDatasetStatus.PASSED.value == "passed"
    assert report.summary.descriptor_count == 11
    assert report.summary.passed_dataset_count == 8
    assert report.summary.failed_dataset_count == 3
    assert report.summary.successful_study_count == 7
    assert report.summary.effect_support_study_count == 6
    assert report.summary.meta_analysis_entry_count == 6
    assert "failure_entry_count" in workflow.render_public_dataset_combined_summary_tsv(
        report
    )


def test_workflow_package_exports_cross_study_evidence_card_surface(
    tmp_path: Path,
) -> None:
    benchmark_root = tmp_path / "benchmarks"
    _write_public_descriptor_copy(
        source_name="lfq_cohort_review_package",
        benchmark_root=benchmark_root,
        dataset_id="lfq_question_a",
        accession="flagship_public_package:lfq_question_a",
    )
    _write_public_descriptor_copy(
        source_name="lfq_cohort_review_package",
        benchmark_root=benchmark_root,
        dataset_id="lfq_question_b",
        accession="flagship_public_package:lfq_question_b",
    )
    _write_public_descriptor_copy(
        source_name="dda_maxquant_review_snapshot",
        benchmark_root=benchmark_root,
        dataset_id="maxquant_missing_bundle",
        accession="flagship_public_package:maxquant_missing_bundle",
    )
    report = workflow.build_public_dataset_evidence_card_report(
        benchmark_root,
        run_output_root=tmp_path / "public_dataset_evidence_card_runs",
    )

    assert hasattr(workflow, "build_cross_study_evidence_card_report")
    assert (
        workflow.CrossStudyEvidenceCardStatus.CONSISTENT_REPLICATION.value
        == "consistent_replication"
    )
    assert report.summary.card_count > 0
    assert "final_status" in workflow.render_cross_study_evidence_card_tsv(report)
    assert "dataset_state" in workflow.render_cross_study_evidence_dataset_tsv(report)


def test_workflow_package_exports_interactive_result_bundle_surface() -> None:
    bundle = workflow.InteractiveResultBundle(
        summary=workflow.InteractiveResultBundleSummary(
            biological_report_available=False,
            ptm_report_available=False,
            run_qc_input_count=0,
            sample_count=0,
            protein_count=0,
            peptide_count=0,
            ptm_site_count=0,
            pathway_count=0,
            qc_entry_count=0,
            card_count=0,
            graph_node_count=0,
            graph_edge_count=0,
            plot_count=0,
        ),
        note="package surface smoke test",
    )

    assert hasattr(workflow, "build_interactive_result_bundle_from_artifacts")
    assert hasattr(workflow, "render_interactive_result_bundle_summary_tsv")
    assert "sample_count" in workflow.render_interactive_result_bundle_summary_tsv(
        bundle
    )


def test_workflow_package_exports_interactive_result_comparison_surface() -> None:
    payload = workflow.InteractiveResultComparisonPayload(
        left_source_reports=(),
        right_source_reports=(),
        left_summary={"protein_count": 1, "ptm_site_count": 1},
        right_summary={"protein_count": 1, "ptm_site_count": 1},
        changed_proteins=(
            workflow.InteractiveResultProteinComparisonEntry(
                object_id="protein:pg-P04637",
                status=workflow.InteractiveResultComparisonStatus.CHANGED,
                representative_protein_ref="P04637",
                gene_symbol="SIGA",
                left_protein=None,
                right_protein=None,
                reasons=(
                    workflow.InteractiveResultComparisonReason(
                        code=workflow.InteractiveResultComparisonReasonCode.EVIDENCE_TIER_CHANGED,
                        field_name="evidence_tier",
                        left_value="supported",
                        right_value="exploratory",
                        message="evidence tier changed between the two result bundles",
                    ),
                ),
                note="protein changed because evidence_tier_changed",
            ),
        ),
        changed_ptm_sites=(),
        changed_qc_entries=(),
        changed_pathways=(),
        summary=workflow.InteractiveResultComparisonSummary(
            left_source_count=1,
            right_source_count=1,
            changed_protein_count=1,
            changed_ptm_site_count=0,
            changed_qc_entry_count=0,
            changed_pathway_count=0,
            total_change_count=1,
            total_reason_count=1,
        ),
        note="package surface smoke test",
    )

    assert hasattr(workflow, "build_interactive_result_comparison_from_artifacts")
    assert "changed_protein_count" in (
        workflow.render_interactive_result_comparison_summary_tsv(payload)
    )
    assert "representative_protein_ref" in (
        workflow.render_interactive_result_comparison_protein_tsv(payload)
    )


def test_workflow_package_exports_result_search_index_surface() -> None:
    report = workflow.ResultSearchReport(
        query_text="P04637",
        summary=workflow.ResultSearchReportSummary(
            query_text="P04637",
            indexed_document_count=1,
            indexed_token_count=3,
            hit_count=1,
            truncated=False,
        ),
        hits=(
            workflow.ResultSearchHit(
                document_id="protein:protein:pg-P04637",
                object_id="protein:pg-P04637",
                document_kind=workflow.ResultSearchDocumentKind.PROTEIN,
                title="SIGA",
                matched_fields=(workflow.ResultSearchField.ACCESSION,),
                evidence_snippets=(
                    workflow.ResultSearchSnippet(
                        field=workflow.ResultSearchField.ACCESSION,
                        text="P04637",
                    ),
                ),
                graph_node_ids=(),
                score=9,
            ),
        ),
        normalized_tokens=("p04637",),
        note="package surface smoke test",
    )

    assert hasattr(workflow, "build_result_search_index_from_artifacts")
    assert hasattr(workflow, "search_result_index")
    assert "indexed_document_count" in workflow.render_result_search_summary_tsv(report)
    assert "evidence_snippets" in workflow.render_result_search_hit_tsv(report)
