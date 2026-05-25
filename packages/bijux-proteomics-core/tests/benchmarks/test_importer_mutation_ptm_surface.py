# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.ptm import parse_ptm_localization_tsv

from .importer_mutation_fixture_support import get_importer_mutation_fixture


def test_ptm_invalid_q_and_malformed_modification_mutation_fixture_rejects_broken_site_evidence() -> (
    None
):
    fixture = get_importer_mutation_fixture(
        "importer_mutation:ptm_invalid_q_and_malformed_modification"
    )

    report = parse_ptm_localization_tsv(fixture.mutated_path)

    assert len(report.accepted_records) == fixture.expected_accepted_count
    assert len(report.rejected_rows) == fixture.expected_rejected_count
    assert {
        issue.code for row in report.rejected_rows for issue in row.issues
    } == set(fixture.expected_issue_codes)
