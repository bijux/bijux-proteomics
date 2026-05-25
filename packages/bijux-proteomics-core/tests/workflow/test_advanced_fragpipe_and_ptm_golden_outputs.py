# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    PtmEvidenceCardPolicy,
    PtmPhosphositeSelectionPolicy,
    PtmProteinCorrectionMode,
    PtmRegulatorEnrichmentPolicy,
)
from bijux_proteomics.workflow import (
    AdvancedFragpipeWorkflowConfig,
    run_advanced_fragpipe_workflow,
)
from bijux_proteomics.workflow.advanced_ptm import (
    AdvancedPtmWorkflowConfig,
    run_advanced_ptm_workflow,
)

from .workflow_golden_support import assert_workflow_golden_outputs_match


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def test_advanced_fragpipe_workflow_matches_reviewed_golden_outputs(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "advanced_fragpipe"
    run_advanced_fragpipe_workflow(
        AdvancedFragpipeWorkflowConfig(
            psm_tsv_path=_workflow_fixture("fragpipe_biological_psms.tsv"),
            design_tsv_path=_workflow_fixture("biological_report.design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            output_dir=output_dir,
            philosopher_protein_tsv_path=_workflow_fixture(
                "fragpipe_biological_proteins.tsv"
            ),
            go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
            pathway_membership_tsv_path=_workflow_fixture(
                "biological_report_pathways.tsv"
            ),
            complex_membership_tsv_path=_workflow_fixture(
                "biological_report_complexes.tsv"
            ),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert_workflow_golden_outputs_match("advanced_fragpipe", output_dir)


def test_advanced_ptm_workflow_matches_reviewed_golden_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "advanced_ptm"
    run_advanced_ptm_workflow(
        AdvancedPtmWorkflowConfig(
            evidence_tsv_path=_ptm_fixture("localization_results.tsv"),
            proteins_fasta_path=_fasta_fixture("ptm_sites.fasta"),
            feature_tsv_path=_ptm_fixture("ptm_features.tsv"),
            design_tsv_path=_ptm_fixture("ptm.design.tsv"),
            output_dir=output_dir,
            annotation_tsv_path=_ptm_fixture("ptm_site_annotations.tsv"),
            annotation_target_species="Homo sapiens",
            protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
            batch_field="",
            condition_a="control",
            condition_b="treated",
            motif_selection_policy=PtmPhosphositeSelectionPolicy(
                max_adjusted_p_value=1.0,
                min_absolute_log2_fold_change=0.0,
            ),
            regulator_enrichment_policy=PtmRegulatorEnrichmentPolicy(
                max_adjusted_p_value=1.0,
                min_absolute_log2_fold_change=0.0,
            ),
            evidence_card_policy=PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
        )
    )

    assert_workflow_golden_outputs_match("advanced_ptm", output_dir)
