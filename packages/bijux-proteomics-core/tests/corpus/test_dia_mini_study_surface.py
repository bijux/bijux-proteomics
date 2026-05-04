# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.corpus import (
    CorpusAssetEntry,
    CorpusLicenseStatus,
    build_complete_dia_mini_study_bundle,
)


def test_build_complete_dia_mini_study_bundle_tracks_quant_rows() -> None:
    bundle = build_complete_dia_mini_study_bundle(
        study_id="dia-mini-01",
        asset_entries=(
            CorpusAssetEntry(
                role="library",
                path="inputs/lib.tsv",
                sha256="a" * 64,
                license_status=CorpusLicenseStatus.REFERENCED,
                caveat="external library reference",
            ),
            CorpusAssetEntry(
                role="result_matrix",
                path="inputs/result.tsv",
                sha256="b" * 64,
                license_status=CorpusLicenseStatus.BUNDLED,
                caveat="dia quant fixture",
            ),
            CorpusAssetEntry(
                role="design_metadata",
                path="inputs/design.tsv",
                sha256="c" * 64,
                license_status=CorpusLicenseStatus.BUNDLED,
                caveat="design mapping",
            ),
            CorpusAssetEntry(
                role="qc",
                path="outputs/qc.json",
                sha256="d" * 64,
                license_status=CorpusLicenseStatus.BUNDLED,
                caveat="qc snapshot",
            ),
            CorpusAssetEntry(
                role="evidence",
                path="outputs/evidence.json",
                sha256="e" * 64,
                license_status=CorpusLicenseStatus.BUNDLED,
                caveat="review evidence",
            ),
        ),
        precursor_quantity_rows=128,
        protein_quantity_rows=42,
        evidence_pointers=("evidence:dia-run-1",),
    )

    assert bundle.study_id == "dia-mini-01"
    assert bundle.precursor_quantity_rows == 128
    assert bundle.protein_quantity_rows == 42
