# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


class ImporterMutationKind(StrEnum):
    """Stable mutation families that importer fixtures must cover."""

    MISSING_COLUMN = "missing_column"
    INVALID_Q_VALUE = "invalid_q_value"
    NEGATIVE_INTENSITY = "negative_intensity"
    DUPLICATE_IDENTIFIER = "duplicate_identifier"
    MALFORMED_MODIFICATION = "malformed_modification"


@dataclass(frozen=True)
class ImporterMutationFixture:
    """One file-backed invalid importer case derived from a valid source asset."""

    fixture_id: str
    owner_surface: str
    source_repo_relative_path: str
    mutated_repo_relative_path: str
    mutation_kinds: tuple[ImporterMutationKind, ...]
    expected_accepted_count: int
    expected_rejected_count: int
    expected_issue_codes: tuple[str, ...] = ()
    expected_reason_fragments: tuple[str, ...] = ()
    note: str = ""

    @property
    def source_path(self) -> Path:
        return REPO_ROOT / self.source_repo_relative_path

    @property
    def mutated_path(self) -> Path:
        return REPO_ROOT / self.mutated_repo_relative_path


def build_importer_mutation_fixture_catalog() -> tuple[ImporterMutationFixture, ...]:
    """Return the owned file-backed importer mutation fixtures."""

    return (
        ImporterMutationFixture(
            fixture_id="importer_mutation:experimental_design_missing_column",
            owner_surface="io.formats.parse_experimental_design_table",
            source_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/formats/"
                "skyline_targeted_carryover.design.tsv"
            ),
            mutated_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/importer_mutations/"
                "formats/experimental_design_missing_spectra.tsv"
            ),
            mutation_kinds=(ImporterMutationKind.MISSING_COLUMN,),
            expected_accepted_count=0,
            expected_rejected_count=1,
            expected_issue_codes=("missing_design_column",),
            note=(
                "drops the spectra_file column from the valid carryover design so the"
                " parser must refuse a structurally incomplete study design"
            ),
        ),
        ImporterMutationFixture(
            fixture_id="importer_mutation:experimental_design_duplicate_identifier",
            owner_surface="io.formats.parse_experimental_design_table",
            source_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/formats/"
                "skyline_targeted_carryover.design.tsv"
            ),
            mutated_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/importer_mutations/"
                "formats/experimental_design_duplicate_identifier.tsv"
            ),
            mutation_kinds=(ImporterMutationKind.DUPLICATE_IDENTIFIER,),
            expected_accepted_count=1,
            expected_rejected_count=2,
            expected_issue_codes=("duplicate_design_identifier",),
            note=(
                "duplicates one sample_id and spectra_file identity from the valid"
                " carryover design so scientific-table duplicate protection stays active"
            ),
        ),
        ImporterMutationFixture(
            fixture_id="importer_mutation:transition_duplicate_and_invalid_q",
            owner_surface="io.transition_table.parse_transition_table",
            source_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/formats/"
                "transition_quant.tsv"
            ),
            mutated_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/importer_mutations/"
                "formats/transition_duplicate_and_invalid_q.tsv"
            ),
            mutation_kinds=(
                ImporterMutationKind.DUPLICATE_IDENTIFIER,
                ImporterMutationKind.INVALID_Q_VALUE,
            ),
            expected_accepted_count=1,
            expected_rejected_count=3,
            expected_reason_fragments=("duplicate", "invalid q-value"),
            note=(
                "reuses one valid transition row, then mutates one q-value and one"
                " sample-precursor-transition identity pair so row-level refusal stays"
                " explicit"
            ),
        ),
        ImporterMutationFixture(
            fixture_id="importer_mutation:ms1_feature_negative_intensity",
            owner_surface="quantification.parse_ms1_feature_table",
            source_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/quant/"
                "ms1_features.tsv"
            ),
            mutated_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/importer_mutations/"
                "quant/ms1_feature_negative_intensity.tsv"
            ),
            mutation_kinds=(ImporterMutationKind.NEGATIVE_INTENSITY,),
            expected_accepted_count=1,
            expected_rejected_count=1,
            expected_issue_codes=("negative_intensity",),
            note=(
                "copies two valid MS1 feature rows and mutates one quantitative value"
                " below zero so the importer refuses impossible abundance evidence"
            ),
        ),
        ImporterMutationFixture(
            fixture_id="importer_mutation:psm_invalid_q_and_malformed_modification",
            owner_surface="identification.contracts.parse_psm_tsv",
            source_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/psm/"
                "engine_mapped_results.tsv"
            ),
            mutated_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/importer_mutations/"
                "psm/psm_invalid_q_and_malformed_modification.tsv"
            ),
            mutation_kinds=(
                ImporterMutationKind.INVALID_Q_VALUE,
                ImporterMutationKind.MALFORMED_MODIFICATION,
            ),
            expected_accepted_count=1,
            expected_rejected_count=2,
            expected_issue_codes=("invalid_q_value", "invalid_peptide_notation"),
            note=(
                "keeps one valid mapped PSM row, mutates one posterior-error value"
                " beyond one, and breaks one modified peptide token so structured"
                " identification rejection stays explicit"
            ),
        ),
        ImporterMutationFixture(
            fixture_id="importer_mutation:ptm_invalid_q_and_malformed_modification",
            owner_surface="ptm.parse_ptm_localization_tsv",
            source_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/ptm/"
                "localization_results.tsv"
            ),
            mutated_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/importer_mutations/"
                "ptm/ptm_invalid_q_and_malformed_modification.tsv"
            ),
            mutation_kinds=(
                ImporterMutationKind.INVALID_Q_VALUE,
                ImporterMutationKind.MALFORMED_MODIFICATION,
            ),
            expected_accepted_count=1,
            expected_rejected_count=2,
            expected_issue_codes=("invalid_q_value", "invalid_modified_peptide"),
            note=(
                "copies one valid PTM localization row, mutates one q-value outside"
                " range, and corrupts one localized modification token so site-level"
                " evidence parsing refuses both rows with explicit issues"
            ),
        ),
        ImporterMutationFixture(
            fixture_id="importer_mutation:tmt_reporter_negative_intensity_and_malformed_modification",
            owner_surface="multiplex.parse_tmt_reporter_table",
            source_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/multiplex/"
                "maxquant_tmt_evidence.tsv"
            ),
            mutated_repo_relative_path=(
                "packages/bijux-proteomics-core/tests/fixtures/importer_mutations/"
                "multiplex/tmt_reporter_negative_intensity_and_malformed_modification.tsv"
            ),
            mutation_kinds=(
                ImporterMutationKind.NEGATIVE_INTENSITY,
                ImporterMutationKind.MALFORMED_MODIFICATION,
            ),
            expected_accepted_count=1,
            expected_rejected_count=2,
            expected_issue_codes=("invalid_peptide", "negative_reporter_intensity"),
            note=(
                "keeps one valid reporter row, corrupts one modified peptide token,"
                " and flips one reporter channel below zero while the rest of the row"
                " stays intact"
            ),
        ),
    )


def get_importer_mutation_fixture(fixture_id: str) -> ImporterMutationFixture:
    """Look up one owned importer mutation fixture by durable identifier."""

    for fixture in build_importer_mutation_fixture_catalog():
        if fixture.fixture_id == fixture_id:
            return fixture
    raise KeyError(f"unknown importer mutation fixture {fixture_id!r}")
