# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.targeted as targeted
from bijux_proteomics.identification.peptide_evidence import (
    PeptideEvidenceClass,
    PeptideEvidenceEntry,
)
from bijux_proteomics.identification.contracts import (
    TargetDecoyContaminantClass,
    TargetDecoyLabel,
)
from bijux_proteomics.identification.cross_run_reproducibility import (
    CrossRunReproducibilityClass,
)
from bijux_proteomics.io import parse_experimental_design_table
from bijux_proteomics.sequences import parse_fasta_document


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def _protein_records():
    return parse_fasta_document(
        ">sp|P00001|KIN1 GN=KIN1\nPEPTIDER\n"
    ).accepted_records


def test_targeted_package_exports_target_matrix_owner_surface() -> None:
    report = targeted.build_skyline_targeted_matrix_report(
        _format_fixture("skyline_targeted_results.tsv")
    )
    rendered = targeted.render_targeted_matrix_missingness_tsv(report)

    assert hasattr(targeted, "build_targeted_matrix_report")
    assert hasattr(targeted, "render_targeted_matrix_retained_transition_tsv")
    assert hasattr(targeted, "render_targeted_matrix_excluded_transition_tsv")
    assert hasattr(targeted, "render_targeted_matrix_missingness_tsv")
    assert report.summary.retained_transition_count == 4
    assert report.rows[1].total_intensity == 273000.0
    assert "no_observation" in rendered


def test_targeted_package_exports_assay_qc_owner_surface() -> None:
    import_report = targeted.build_skyline_result_import_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    design_entries = parse_experimental_design_table(
        _format_fixture("skyline_targeted_qc.design.tsv")
    ).accepted_entries
    report = targeted.build_targeted_assay_qc_report(import_report, design_entries)
    rendered = targeted.render_targeted_assay_qc_target_tsv(report)

    assert hasattr(targeted, "build_targeted_assay_qc_report")
    assert hasattr(targeted, "render_targeted_assay_qc_coelution_tsv")
    assert hasattr(targeted, "render_targeted_assay_qc_transition_coelution_tsv")
    assert hasattr(targeted, "render_targeted_assay_qc_target_tsv")
    assert hasattr(targeted, "render_targeted_assay_qc_transition_qc_tsv")
    assert report.summary.target_qc_entry_count == 8
    assert report.summary.reliable_target_entry_count == 1
    assert "fewer than two coeluting transitions support the target" in rendered


def test_targeted_package_exports_transition_coelution_owner_surface() -> None:
    report = targeted.build_skyline_targeted_transition_coelution_report(
        _format_fixture("skyline_targeted_qc_results.tsv")
    )
    rendered = targeted.render_targeted_transition_coelution_target_tsv(report)

    assert hasattr(targeted, "build_targeted_transition_coelution_report")
    assert hasattr(targeted, "render_targeted_transition_coelution_target_tsv")
    assert hasattr(targeted, "render_targeted_transition_coelution_transition_tsv")
    assert report.summary.target_entry_count == 8
    assert report.summary.flagged_target_entry_count == 3
    assert "fewer than two coeluting transitions support the target" in rendered


def test_targeted_package_exports_carryover_owner_surface() -> None:
    import_report = targeted.build_skyline_result_import_report(
        _format_fixture("skyline_targeted_carryover_results.tsv")
    )
    design_entries = parse_experimental_design_table(
        _format_fixture("skyline_targeted_carryover.design.tsv")
    ).accepted_entries
    report = targeted.build_targeted_carryover_report(import_report, design_entries)
    summary_tsv = targeted.render_targeted_carryover_summary_tsv(report)
    candidate_tsv = targeted.render_targeted_carryover_candidates_tsv(report)

    assert hasattr(targeted, "build_targeted_carryover_report")
    assert hasattr(targeted, "render_targeted_carryover_summary_tsv")
    assert hasattr(targeted, "render_targeted_carryover_candidates_tsv")
    assert report.summary.candidate_entry_count == 2
    assert "Skyline\t4\t2\t2\t2\t1" in summary_tsv
    assert "CARRYPEP/2" in candidate_tsv


def test_targeted_package_exports_discovery_peptide_selection_surface() -> None:
    report = targeted.build_discovery_targeted_peptide_selection_report(
        (
            targeted.DiscoveryTargetProteinEntry(
                protein_group_id="protein_group_1",
                representative_protein_ref="P00001",
                protein_refs=("P00001",),
                gene_symbol="KIN1",
                discovery_peptides=("PEPTIDER",),
            ),
        ),
        (
            PeptideEvidenceEntry(
                peptide="PEPTIDER",
                canonical_peptide="PEPTIDER",
                primary_class=PeptideEvidenceClass.STRONG,
                peptide_q_value=0.001,
                accepted=True,
                psm_count=5,
                spectrum_count=5,
                run_count=3,
                detection_frequency=1.0,
                replicate_consistency=0.9,
                condition_specificity=0.1,
                detected_condition_count=2,
                reproducibility_class=CrossRunReproducibilityClass.REPRODUCIBLE,
                best_score=120.0,
                charge_states=(2,),
                run_ids=("run1", "run2", "run3"),
                protein_refs=("P00001",),
                target_decoy_label=TargetDecoyLabel.TARGET,
                target_decoy_contaminant_class=TargetDecoyContaminantClass.TARGET,
                explanation="strong observed peptide support",
            ),
        ),
        _protein_records(),
        top_peptides_per_target=1,
    )
    rendered = targeted.render_discovery_targeted_peptide_selection_selected_tsv(report)

    assert hasattr(targeted, "build_discovery_targeted_peptide_selection_report")
    assert hasattr(targeted, "render_discovery_targeted_peptide_selection_summary_tsv")
    assert hasattr(targeted, "render_discovery_targeted_peptide_selection_selected_tsv")
    assert hasattr(targeted, "render_discovery_targeted_peptide_selection_rejected_tsv")
    assert report.summary.selected_entry_count == 1
    assert "P00001\tprotein_group_1\tKIN1\t1\tobserved_discovery\tPEPTIDER" in rendered
