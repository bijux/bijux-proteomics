# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm import PtmSiteEntry
from bijux_proteomics.ptm.review import (
    build_acetyl_specific_review_fixture_report,
)
from bijux_proteomics.quantification import MissingValueKind, Ms1FeatureRecord


def _provenance(site_key: str) -> ImportedEvidenceProvenance:
    return ImportedEvidenceProvenance(
        source_engine="synthetic-ptm",
        source_files=("acetyl.tsv",),
        source_row_numbers=(2,),
        original_identifiers={"site_key": site_key},
    )


def test_acetyl_review_fixture_report_tracks_terminal_and_residue_placements() -> None:
    site_entries = (
        PtmSiteEntry(
            site_key="P1:A1:Acetyl",
            protein_ref="P1",
            residue="A",
            position=1,
            modification_name="Acetyl",
            localization_score=0.99,
            best_q_value=0.005,
            spectrum_count=3,
            peptide_count=2,
            localized_peptides=("[Acetyl]-APEPTIDE",),
            sample_ids=("S1",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            candidate_positions=(1,),
            ambiguous=False,
            provenance=_provenance("P1:A1:Acetyl"),
        ),
        PtmSiteEntry(
            site_key="P1:K8:Acetyl",
            protein_ref="P1",
            residue="K",
            position=8,
            modification_name="Acetyl",
            localization_score=0.95,
            best_q_value=0.01,
            spectrum_count=2,
            peptide_count=1,
            localized_peptides=("[Acetyl]-PEPTIDEK",),
            sample_ids=("S1",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            candidate_positions=(8,),
            ambiguous=False,
            provenance=_provenance("P1:K8:Acetyl"),
        ),
    )
    feature_records = (
        Ms1FeatureRecord(
            feature_id="f1",
            sample_id="S1",
            peptide="[Acetyl]-APEPTIDE",
            canonical_peptide="[Acetyl]-APEPTIDE",
            intensity=400.0,
            protein_refs=("P1",),
            charge=2,
            mz=500.1,
            retention_time_seconds=1000.0,
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="f2",
            sample_id="S1",
            peptide="APEPTIDE",
            canonical_peptide="APEPTIDE",
            intensity=600.0,
            protein_refs=("P1",),
            charge=2,
            mz=499.9,
            retention_time_seconds=998.0,
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="f3",
            sample_id="S1",
            peptide="[Acetyl]-PEPTIDEK",
            canonical_peptide="[Acetyl]-PEPTIDEK",
            intensity=250.0,
            protein_refs=("P1",),
            charge=2,
            mz=620.4,
            retention_time_seconds=1100.0,
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="f4",
            sample_id="S1",
            peptide="PEPTIDEK",
            canonical_peptide="PEPTIDEK",
            intensity=750.0,
            protein_refs=("P1",),
            charge=2,
            mz=619.9,
            retention_time_seconds=1098.0,
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    report = build_acetyl_specific_review_fixture_report(
        site_entries,
        feature_records=feature_records,
        protein_sequences={"P1": "APEPTIDEKGGGG"},
    )

    assert report.acetyl_site_keys == ("P1:A1:Acetyl", "P1:K8:Acetyl")
    assert report.protein_terminal_site_keys == ("P1:A1:Acetyl",)
    assert report.residue_site_keys == ("P1:K8:Acetyl",)
    assert report.quantified_sample_ids == ("S1",)
    assert report.motif_window_count == 2
