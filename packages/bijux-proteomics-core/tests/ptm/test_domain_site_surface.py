# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm.contracts import (
    PtmSiteEntry,
    PtmValidationIssue,
    RejectedPtmEvidenceRow,
)


def test_ptm_site_and_rejection_convert_to_canonical_domain_records() -> None:
    provenance = ImportedEvidenceProvenance(
        source_engine="synthetic-ptm",
        source_files=("ptm.tsv",),
        source_row_numbers=(2,),
        original_identifiers={"site_key": "P001:S15:Phospho"},
    )
    site = PtmSiteEntry(
        site_key="P001:S15:Phospho",
        protein_ref="P001",
        residue="S",
        position=15,
        modification_name="Phospho",
        localization_score=0.95,
        best_q_value=0.01,
        spectrum_count=3,
        peptide_count=2,
        localized_peptides=("AA[Phospho]SPEPTIDE",),
        sample_ids=("sample-a",),
        target_decoy_label=TargetDecoyLabel.TARGET,
        candidate_positions=(15,),
        ambiguous=False,
        shared_peptide=False,
        provenance=provenance,
    )
    rejected = RejectedPtmEvidenceRow(
        row_number=5,
        raw_fields={"spectrum_id": "scan=5"},
        issues=(
            PtmValidationIssue(
                code="missing_probability",
                message="localization probability is required",
                row_number=5,
            ),
        ),
    )

    domain_site = site.to_domain_record()
    domain_rejected = rejected.to_domain_record()

    assert domain_site.position == 15
    assert domain_site.metadata["target_decoy_state"] == "target"
    assert domain_rejected.record_kind == "ptm_evidence"
