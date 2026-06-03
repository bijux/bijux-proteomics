# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain import TargetDecoyState
from bijux_proteomics.identification import (
    PeptideEvidenceEntry,
    ProteinGroupEntry,
    PsmRecord,
    RejectedPsmRow,
    SearchResultValidationIssue,
    TargetDecoyLabel,
)
from bijux_proteomics.identification.contracts.evidence import (
    ProteinEvidenceEntry,
)


def test_identification_records_convert_to_canonical_domain_records() -> None:
    psm = PsmRecord(
        run_id="run-a",
        spectrum_id="scan=1",
        peptide="PEPTIDE",
        canonical_peptide="PEPTIDE",
        charge=2,
        score=42.0,
        intensity=1500.0,
        q_value=0.01,
        protein_refs=("P001",),
        target_decoy_label=TargetDecoyLabel.TARGET,
    )

    domain_psm = psm.to_domain_record()
    modified_peptide = psm.to_modified_peptide_record()

    assert domain_psm.spectrum_id == "scan=1"
    assert domain_psm.target_decoy_state is TargetDecoyState.TARGET
    assert modified_peptide.record_id == "scan=1"
    assert modified_peptide.modified_peptide == "PEPTIDE"


def test_identification_rollups_and_rejections_convert_to_domain_records() -> None:
    peptide = PeptideEvidenceEntry(
        peptide="PEPTIDE",
        canonical_peptide="PEPTIDE",
        psm_count=3,
        spectrum_count=3,
        best_score=55.0,
        best_q_value=0.02,
        charge_states=(2, 3),
        protein_refs=("P001", "P002"),
        target_decoy_label=TargetDecoyLabel.MIXED,
    )
    protein = ProteinEvidenceEntry(
        protein_ref="P001",
        peptide_count=3,
        unique_peptide_count=2,
        shared_peptide_count=1,
        best_score=70.0,
        best_q_value=0.01,
        peptides=("PEPTIDE", "SECOND"),
        spectrum_count=5,
        target_decoy_label=TargetDecoyLabel.TARGET,
    )
    protein_group = ProteinGroupEntry(
        group_id="group-1",
        representative_protein="P001",
        protein_refs=("P001", "P002"),
        peptides=("PEPTIDE",),
        unique_peptide_count=1,
        shared_peptide_count=1,
        best_score=63.0,
        best_q_value=0.03,
        target_decoy_label=TargetDecoyLabel.UNKNOWN,
    )
    rejected = RejectedPsmRow(
        row_number=9,
        raw_fields={"spectrum_id": "scan=9"},
        issues=(
            SearchResultValidationIssue(
                code="missing_score",
                message="score is required",
                row_number=9,
            ),
        ),
    )

    assert peptide.to_domain_record().target_decoy_state is TargetDecoyState.MIXED
    assert protein.to_domain_record().primary_protein_ref == "P001"
    assert protein_group.to_domain_record().group_id == "group-1"
    assert rejected.to_domain_record().row_number == 9
