# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.dia_iteration12 import (
    SpectralLibraryIdentityEntry,
    build_spectral_library_identity_ledger,
)


def test_build_spectral_library_identity_ledger_counts_sources() -> None:
    ledger = build_spectral_library_identity_ledger(
        (
            SpectralLibraryIdentityEntry(
                library_source="pan-human",
                library_version="v1",
                spectrum_id="sp-1",
                peptide_sequence="PEPTIDEK",
                charge=2,
                modifications=("Oxidation[M]",),
                decoy=False,
            ),
            SpectralLibraryIdentityEntry(
                library_source="pan-human",
                library_version="v1",
                spectrum_id="sp-2",
                peptide_sequence="ACDMPEP",
                charge=3,
                modifications=(),
                decoy=True,
            ),
        )
    )

    assert ledger.library_source_count == 1
    assert ledger.entries[0].spectrum_id == "sp-1"
