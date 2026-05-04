# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.chemistry import (
    AppliedModification,
    ModificationPosition,
    ParsedModifiedPeptide,
)
from bijux_proteomics.modified_peptide_conflicts import (
    validate_advanced_modified_peptide_conflicts,
)


def test_validate_advanced_modified_peptide_conflicts_rejects_terminal_collisions() -> (
    None
):
    peptide = ParsedModifiedPeptide(
        sequence="PEPTIDEK",
        canonical_notation="[Acetyl][TMT6plex]-PEPTIDEK",
        modifications=(
            AppliedModification(
                name="Acetyl",
                token="Acetyl",
                site=ModificationPosition.PEPTIDE_N_TERM,
                mass_delta_monoisotopic=42.010565,
                mass_delta_average=42.0367,
            ),
            AppliedModification(
                name="TMT6plex",
                token="TMT6plex",
                site=ModificationPosition.PEPTIDE_N_TERM,
                mass_delta_monoisotopic=229.162932,
                mass_delta_average=229.2634,
            ),
        ),
    )
    report = validate_advanced_modified_peptide_conflicts(peptide)

    assert report.valid is False
    assert any(
        issue.code == "multiple_n_terminal_modifications" for issue in report.issues
    )
    assert any(issue.code == "terminal_label_collision" for issue in report.issues)
