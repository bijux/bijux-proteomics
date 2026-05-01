# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia_iteration12 import (
    SpectralLibraryIdentityEntry,
    validate_spectral_library_identity_entries,
)


def test_validate_spectral_library_identity_entries_reports_duplicates_and_missing_decoys() -> (
    None
):
    report = validate_spectral_library_identity_entries(
        (
            SpectralLibraryIdentityEntry(
                library_source="lib-a",
                library_version="v1",
                spectrum_id="sp-1",
                peptide_sequence="PEPTIDEK",
                charge=2,
                modifications=("Oxidation[M]",),
                decoy=False,
            ),
            SpectralLibraryIdentityEntry(
                library_source="lib-a",
                library_version="v1",
                spectrum_id="sp-1",
                peptide_sequence="PEPTIDER",
                charge=2,
                modifications=("badtoken",),
                decoy=False,
            ),
        )
    )

    assert report.valid is False
    codes = {issue.code for issue in report.issues}
    assert "duplicate_spectrum_id" in codes
    assert "missing_decoy_entries" in codes
    assert "invalid_modification_token" in codes
