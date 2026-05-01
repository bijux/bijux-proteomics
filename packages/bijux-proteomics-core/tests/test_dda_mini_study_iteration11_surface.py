# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.corpus_iteration11 import (
    CorpusAssetEntry,
    CorpusLicenseStatus,
    build_complete_dda_mini_study_bundle,
)


def test_build_complete_dda_mini_study_bundle_requires_core_asset_roles() -> None:
    bundle = build_complete_dda_mini_study_bundle(
        study_id="dda-mini-01",
        asset_entries=(
            CorpusAssetEntry(role="spectra", path="inputs/run1.mzml", sha256="a" * 64, license_status=CorpusLicenseStatus.BUNDLED, caveat="research fixture"),
            CorpusAssetEntry(role="engine_output", path="inputs/engine.tsv", sha256="b" * 64, license_status=CorpusLicenseStatus.BUNDLED, caveat="fake engine export"),
            CorpusAssetEntry(role="fasta", path="inputs/db.fasta", sha256="c" * 64, license_status=CorpusLicenseStatus.BUNDLED, caveat="truncated reference"),
            CorpusAssetEntry(role="design_metadata", path="inputs/design.tsv", sha256="d" * 64, license_status=CorpusLicenseStatus.BUNDLED, caveat="two-condition design"),
            CorpusAssetEntry(role="identification", path="outputs/identification.json", sha256="e" * 64, license_status=CorpusLicenseStatus.BUNDLED, caveat="expected ids snapshot"),
            CorpusAssetEntry(role="protein_inference", path="outputs/protein.json", sha256="f" * 64, license_status=CorpusLicenseStatus.BUNDLED, caveat="expected protein groups"),
            CorpusAssetEntry(role="qc", path="outputs/qc.json", sha256="1" * 64, license_status=CorpusLicenseStatus.BUNDLED, caveat="qc threshold fixture"),
            CorpusAssetEntry(role="evidence", path="outputs/evidence.json", sha256="2" * 64, license_status=CorpusLicenseStatus.BUNDLED, caveat="review evidence graph"),
        ),
        expected_outputs=("outputs/identification.json", "outputs/qc.json"),
        evidence_pointers=("evidence:run1",),
    )

    assert bundle.study_id == "dda-mini-01"
    assert len(bundle.asset_entries) == 8
