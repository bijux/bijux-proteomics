# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from .importer_mutation_fixture_support import (
    ImporterMutationKind,
    build_importer_mutation_fixture_catalog,
)


def test_importer_mutation_fixture_catalog_keeps_unique_file_backed_owners() -> None:
    fixtures = build_importer_mutation_fixture_catalog()

    assert len({fixture.fixture_id for fixture in fixtures}) == len(fixtures)
    assert len({fixture.mutated_repo_relative_path for fixture in fixtures}) == len(
        fixtures
    )

    for fixture in fixtures:
        assert fixture.source_path.is_file(), fixture.source_repo_relative_path
        assert fixture.mutated_path.is_file(), fixture.mutated_repo_relative_path
        assert fixture.source_path != fixture.mutated_path
        assert fixture.expected_rejected_count >= 1
        assert fixture.mutation_kinds
        assert fixture.expected_issue_codes or fixture.expected_reason_fragments


def test_importer_mutation_fixture_catalog_covers_required_invalid_science_families() -> (
    None
):
    fixtures = build_importer_mutation_fixture_catalog()

    covered_kinds = {
        mutation_kind
        for fixture in fixtures
        for mutation_kind in fixture.mutation_kinds
    }

    assert covered_kinds == {
        ImporterMutationKind.MISSING_COLUMN,
        ImporterMutationKind.INVALID_Q_VALUE,
        ImporterMutationKind.NEGATIVE_INTENSITY,
        ImporterMutationKind.DUPLICATE_IDENTIFIER,
        ImporterMutationKind.MALFORMED_MODIFICATION,
    }


def test_importer_mutation_fixture_catalog_covers_owned_importer_surfaces() -> None:
    fixtures = build_importer_mutation_fixture_catalog()

    assert {fixture.owner_surface for fixture in fixtures} == {
        "io.formats.parse_experimental_design_table",
        "io.transition_table.parse_transition_table",
        "quantification.parse_ms1_feature_table",
        "identification.contracts.parse_psm_tsv",
        "ptm.parse_ptm_localization_tsv",
        "multiplex.parse_tmt_reporter_table",
    }
