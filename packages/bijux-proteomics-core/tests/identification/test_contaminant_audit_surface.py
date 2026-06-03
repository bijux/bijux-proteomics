# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.confidence import ProteinInferenceStrategyKind
from bijux_proteomics.identification.contaminant_audit import (
    build_contaminant_aware_protein_inference_audit,
    build_contaminant_peptide_match_report,
)
from bijux_proteomics.identification.contracts import PsmRecord, TargetDecoyLabel


def test_contaminant_aware_protein_inference_audit_shows_posture_shift() -> None:
    records = (
        PsmRecord(
            spectrum_id="s001",
            peptide="TARGETK",
            canonical_peptide="TARGETK",
            charge=2,
            score=130.0,
            q_value=0.001,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="s002",
            peptide="KERATINP",
            canonical_peptide="KERATINP",
            charge=2,
            score=120.0,
            q_value=0.002,
            protein_refs=("CON__KERATIN",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )

    audit = build_contaminant_aware_protein_inference_audit(records)

    assert audit.contaminant_psm_count == 1
    assert audit.unresolved_contaminant_promotion is True
    grouped = next(
        entry
        for entry in audit.strategy_shifts
        if entry.strategy_kind is ProteinInferenceStrategyKind.GROUPED
    )
    assert grouped.removed_contaminant_proteins == ("CON__KERATIN",)
    assert "CON__KERATIN" not in grouped.filtered_selected_proteins


def test_contaminant_peptide_match_report_separates_pure_and_mixed_matches() -> None:
    records = (
        PsmRecord(
            spectrum_id="s001",
            peptide="TARGETK",
            canonical_peptide="TARGETK",
            charge=2,
            score=130.0,
            q_value=0.001,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="s002",
            peptide="KERATINP",
            canonical_peptide="KERATINP",
            charge=2,
            score=120.0,
            q_value=0.002,
            protein_refs=("CON__KERATIN",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="s003",
            peptide="TRYPSINP",
            canonical_peptide="TRYPSINP",
            charge=2,
            score=118.0,
            q_value=0.003,
            protein_refs=("CON__TRYP_PIG", "P11111"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )

    report = build_contaminant_peptide_match_report(records)

    assert report.contaminant_psm_count == 2
    assert report.pure_contaminant_psm_count == 1
    assert report.mixed_reference_psm_count == 1
    assert report.contaminant_peptide_count == 2
    assert report.contaminant_protein_counts == {
        "CON__KERATIN": 1,
        "CON__TRYP_PIG": 1,
    }
    assert report.entries[0].mixed_reference is False
    assert report.entries[1].mixed_reference is True
    assert report.entries[0].pure_contaminant is True
    assert report.entries[1].pure_contaminant is False
