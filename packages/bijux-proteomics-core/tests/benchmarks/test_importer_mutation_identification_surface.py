# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification.contracts import (
    SearchResultColumnMapping,
    parse_psm_tsv,
)

from .importer_mutation_fixture_support import get_importer_mutation_fixture


def _psm_mapping() -> SearchResultColumnMapping:
    return SearchResultColumnMapping(
        spectrum_id="SpecID",
        peptide="Sequence",
        charge="Z",
        score="PrimaryScore",
        q_value="PosteriorError",
        protein_refs="Proteins",
        decoy_label="DecoyFlag",
    )


def test_psm_invalid_q_and_malformed_modification_mutation_fixture_rejects_broken_identification_rows() -> (
    None
):
    fixture = get_importer_mutation_fixture(
        "importer_mutation:psm_invalid_q_and_malformed_modification"
    )

    report = parse_psm_tsv(fixture.mutated_path, mapping=_psm_mapping())

    assert len(report.accepted_records) == fixture.expected_accepted_count
    assert len(report.rejected_rows) == fixture.expected_rejected_count
    assert {issue.code for row in report.rejected_rows for issue in row.issues} == set(
        fixture.expected_issue_codes
    )
