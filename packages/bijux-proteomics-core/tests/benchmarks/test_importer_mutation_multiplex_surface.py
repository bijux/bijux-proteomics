# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.multiplex import (
    TmtSearchResultSourceKind,
    parse_tmt_reporter_table,
)

from .importer_mutation_fixture_support import get_importer_mutation_fixture


def test_tmt_reporter_negative_intensity_and_malformed_modification_mutation_fixture_rejects_broken_reporter_rows() -> (
    None
):
    fixture = get_importer_mutation_fixture(
        "importer_mutation:tmt_reporter_negative_intensity_and_malformed_modification"
    )

    report = parse_tmt_reporter_table(
        fixture.mutated_path,
        source_kind=TmtSearchResultSourceKind.MAXQUANT,
    )

    assert report.summary.accepted_row_count == fixture.expected_accepted_count
    assert report.summary.rejected_row_count == fixture.expected_rejected_count
    assert {issue.code for row in report.rejected_rows for issue in row.issues} == set(
        fixture.expected_issue_codes
    )
