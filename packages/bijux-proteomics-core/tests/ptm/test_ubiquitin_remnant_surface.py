# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.ptm import PtmSiteEntry
from bijux_proteomics.ptm.review import (
    build_ubiquitin_remnant_workflow_report,
)
from bijux_proteomics.quantification import MissingValueKind, Ms1FeatureRecord


def _provenance(site_key: str) -> ImportedEvidenceProvenance:
    return ImportedEvidenceProvenance(
        source_engine="synthetic-ptm",
        source_files=("ubiquitin.tsv",),
        source_row_numbers=(2,),
        original_identifiers={"site_key": site_key},
    )


def test_ubiquitin_remnant_workflow_report_captures_kgg_assumptions_and_quant_links() -> (
    None
):
    site_entries = (
        PtmSiteEntry(
            site_key="P2:K48:GlyGly",
            protein_ref="P2",
            residue="K",
            position=48,
            modification_name="GlyGly",
            localization_score=0.97,
            best_q_value=0.01,
            spectrum_count=4,
            peptide_count=2,
            localized_peptides=("PEPTIDEK[GG]",),
            sample_ids=("S1", "S2"),
            target_decoy_label=TargetDecoyLabel.TARGET,
            candidate_positions=(48,),
            ambiguous=False,
            provenance=_provenance("P2:K48:GlyGly"),
        ),
        PtmSiteEntry(
            site_key="P2:S52:K-GG",
            protein_ref="P2",
            residue="S",
            position=52,
            modification_name="K-GG",
            localization_score=0.8,
            best_q_value=0.04,
            spectrum_count=1,
            peptide_count=1,
            localized_peptides=("PEPTIDES[GG]",),
            sample_ids=("S2",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            candidate_positions=(52, 53),
            ambiguous=True,
            provenance=_provenance("P2:S52:K-GG"),
        ),
    )
    feature_records = (
        Ms1FeatureRecord(
            feature_id="q1",
            sample_id="S1",
            peptide="PEPTIDEK[GG]",
            canonical_peptide="PEPTIDEK[GG]",
            intensity=1200.0,
            protein_refs=("P2",),
            charge=2,
            mz=555.1,
            retention_time_seconds=800.0,
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="q2",
            sample_id="S2",
            peptide="PEPTIDEK[GG]",
            canonical_peptide="PEPTIDEK[GG]",
            intensity=950.0,
            protein_refs=("P2",),
            charge=2,
            mz=555.2,
            retention_time_seconds=801.0,
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )

    report = build_ubiquitin_remnant_workflow_report(
        site_entries,
        feature_records=feature_records,
    )

    assert len(report.entries) == 2
    assert report.ambiguous_entry_count == 1
    assert report.non_lysine_entry_count == 1
    kgg = next(entry for entry in report.entries if entry.site_key == "P2:K48:GlyGly")
    non_lysine = next(
        entry for entry in report.entries if entry.site_key == "P2:S52:K-GG"
    )
    assert kgg.lysine_consistent is True
    assert kgg.quantified_sample_ids == ("S1", "S2")
    assert non_lysine.lysine_consistent is False
    assert "not lysine" in " ".join(non_lysine.caveats)
