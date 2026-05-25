# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import parse_ms1_feature_table

from .importer_mutation_fixture_support import get_importer_mutation_fixture


def test_ms1_feature_negative_intensity_mutation_fixture_rejects_impossible_abundance() -> (
    None
):
    fixture = get_importer_mutation_fixture(
        "importer_mutation:ms1_feature_negative_intensity"
    )

    report = parse_ms1_feature_table(fixture.mutated_path)

    assert len(report.accepted_records) == fixture.expected_accepted_count
    assert len(report.rejected_rows) == fixture.expected_rejected_count
    assert {
        issue.code for row in report.rejected_rows for issue in row.issues
    } == set(fixture.expected_issue_codes)
