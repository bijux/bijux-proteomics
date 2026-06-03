# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.io.transition_table import parse_transition_table

from .importer_mutation_fixture_support import get_importer_mutation_fixture


def test_experimental_design_missing_column_mutation_fixture_rejects_missing_study_shape() -> (
    None
):
    fixture = get_importer_mutation_fixture(
        "importer_mutation:experimental_design_missing_column"
    )

    report = parse_experimental_design_table(fixture.mutated_path)

    assert fixture.source_path.is_file()
    assert fixture.mutated_path.is_file()
    assert len(report.accepted_entries) == fixture.expected_accepted_count
    assert len(report.rejected_rows) == fixture.expected_rejected_count
    assert {issue.code for row in report.rejected_rows for issue in row.issues} == set(
        fixture.expected_issue_codes
    )


def test_transition_duplicate_and_invalid_q_mutation_fixture_rejects_row_level_science_failures() -> (
    None
):
    fixture = get_importer_mutation_fixture(
        "importer_mutation:transition_duplicate_and_invalid_q"
    )

    report = parse_transition_table(fixture.mutated_path)

    assert len(report.accepted_entries) == fixture.expected_accepted_count
    assert len(report.rejected_rows) == fixture.expected_rejected_count
    reasons = tuple(row.reason for row in report.rejected_rows)
    assert any("duplicate" in reason.lower() for reason in reasons)
    assert any("invalid q-value" in reason for reason in reasons)


def test_experimental_design_duplicate_identifier_mutation_fixture_rejects_duplicate_design_identity() -> (
    None
):
    fixture = get_importer_mutation_fixture(
        "importer_mutation:experimental_design_duplicate_identifier"
    )

    report = parse_experimental_design_table(fixture.mutated_path)

    assert len(report.accepted_entries) == fixture.expected_accepted_count
    assert len(report.rejected_rows) == fixture.expected_rejected_count
    assert {issue.code for row in report.rejected_rows for issue in row.issues} == set(
        fixture.expected_issue_codes
    )
