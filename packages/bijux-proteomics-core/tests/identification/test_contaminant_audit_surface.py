# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.confidence import ProteinInferenceStrategyKind
from bijux_proteomics.identification.contaminant_audit import (
    build_contaminant_aware_protein_inference_audit,
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
