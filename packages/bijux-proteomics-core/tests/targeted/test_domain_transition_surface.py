# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.targeted.result_import import (
    TargetedResultObservation,
    TargetedResultSourceKind,
)


def test_targeted_observation_converts_to_canonical_transition_record() -> None:
    observation = TargetedResultObservation(
        source_kind=TargetedResultSourceKind.SKYLINE_EXPORT,
        transition_id="y7",
        precursor_id="PEPTIDE/2",
        precursor_charge=2,
        peptide_sequence="PEPTIDE",
        sample_id="sample-a",
        intensity=1200.0,
        retention_time_minutes=14.2,
        quality_flag="borderline",
        protein_ref="P001",
        fragment_label="y7",
        provenance=ImportedEvidenceProvenance.from_single_row(
            source_engine="skyline",
            source_file="skyline.tsv",
            source_row_number=2,
            original_identifiers={
                "transition_id": "y7",
                "precursor_id": "PEPTIDE/2",
                "sample_id": "sample-a",
            },
        ),
    )

    record = observation.to_domain_record()

    assert record.transition_id == "y7"
    assert record.precursor_charge == 2
    assert record.quality_flag == "borderline"
    assert record.metadata["source_contract"] == "targeted.skyline_export"
