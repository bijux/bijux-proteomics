# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.sequences.protein_region_context import (
    ProteinRegionContextImportReport,
    ProteinRegionContextImportSummary,
    ProteinRegionContextRecord,
)
from bijux_proteomics_knowledge.features.overlaps import (
    ProteinFeatureOverlapEntry,
    ProteinFeatureQueryInterval,
    ProteinFeatureType,
    overlap_protein_features,
    render_protein_feature_overlaps_tsv,
)


def test_overlap_protein_features_preserves_first_and_last_residue_boundaries() -> None:
    overlaps = overlap_protein_features(
        "P11111",
        (
            ProteinFeatureQueryInterval(start=1, end=1),
            ProteinFeatureQueryInterval(start=20, end=20),
            ProteinFeatureQueryInterval(start=8, end=10),
        ),
        (
            ProteinRegionContextRecord(
                protein_ref="P11111",
                start=1,
                end=3,
                signal_peptide="leader",
                source_name="UniProt",
                source_accession="UP:P11111-1-3",
            ),
            ProteinRegionContextRecord(
                protein_ref="P11111",
                start=18,
                end=20,
                domain_name="carboxyl_tail",
                motif_name="tail_switch",
                source_name="InterPro",
                source_accession="IPR:P11111-18-20",
            ),
            ProteinRegionContextRecord(
                protein_ref="Q99999",
                start=1,
                end=20,
                binding_region="foreign_protein_region",
                source_name="Curator",
                source_accession="CUR:Q99999-1-20",
            ),
        ),
    )

    assert overlaps == (
        ProteinFeatureOverlapEntry(
            protein_id="P11111",
            query_start=1,
            query_end=1,
            feature_id="UP:P11111-1-3:signal_peptide:1-3:leader",
            feature_type=ProteinFeatureType.SIGNAL_PEPTIDE,
            overlap_start=1,
            overlap_end=1,
        ),
        ProteinFeatureOverlapEntry(
            protein_id="P11111",
            query_start=20,
            query_end=20,
            feature_id="IPR:P11111-18-20:domain:18-20:carboxyl_tail",
            feature_type=ProteinFeatureType.DOMAIN,
            overlap_start=20,
            overlap_end=20,
        ),
        ProteinFeatureOverlapEntry(
            protein_id="P11111",
            query_start=20,
            query_end=20,
            feature_id="IPR:P11111-18-20:motif:18-20:tail_switch",
            feature_type=ProteinFeatureType.MOTIF,
            overlap_start=20,
            overlap_end=20,
        ),
    )


def test_overlap_protein_features_accepts_import_reports_and_renders_tsv() -> None:
    report = ProteinRegionContextImportReport(
        total_rows=2,
        accepted_records=(
            ProteinRegionContextRecord(
                protein_ref="P22222",
                start=4,
                end=6,
                binding_region="substrate_dock",
                source_name="Literature",
                source_accession="PMID:P22222-4-6",
            ),
            ProteinRegionContextRecord(
                protein_ref="P22222",
                start=5,
                end=8,
                disorder_region="mobile_loop",
                source_name="Curator",
                source_accession="CUR:P22222-5-8",
            ),
        ),
        rejected_rows=(),
        column_mapping={
            "protein_ref": "protein_ref",
            "start": "start",
            "end": "end",
        },
        summary=ProteinRegionContextImportSummary(
            accepted_record_count=2,
            rejected_row_count=0,
            distinct_protein_ref_count=1,
            domain_record_count=0,
            signal_peptide_record_count=0,
            transmembrane_record_count=0,
            disorder_record_count=1,
            low_complexity_record_count=0,
            active_site_record_count=0,
            binding_region_record_count=1,
            motif_record_count=0,
            conservation_record_count=0,
        ),
        note="test report",
    )

    overlaps = overlap_protein_features(
        "P22222",
        (ProteinFeatureQueryInterval(start=5, end=5),),
        report,
    )

    assert overlaps == (
        ProteinFeatureOverlapEntry(
            protein_id="P22222",
            query_start=5,
            query_end=5,
            feature_id="PMID:P22222-4-6:binding_region:4-6:substrate_dock",
            feature_type=ProteinFeatureType.BINDING_REGION,
            overlap_start=5,
            overlap_end=5,
        ),
        ProteinFeatureOverlapEntry(
            protein_id="P22222",
            query_start=5,
            query_end=5,
            feature_id="CUR:P22222-5-8:disorder_region:5-8:mobile_loop",
            feature_type=ProteinFeatureType.DISORDER_REGION,
            overlap_start=5,
            overlap_end=5,
        ),
    )

    rendered = render_protein_feature_overlaps_tsv(overlaps)

    assert rendered.splitlines() == [
        "protein_id\tquery_start\tquery_end\tfeature_id\tfeature_type\toverlap_start\toverlap_end",
        "P22222\t5\t5\tPMID:P22222-4-6:binding_region:4-6:substrate_dock\tbinding_region\t5\t5",
        "P22222\t5\t5\tCUR:P22222-5-8:disorder_region:5-8:mobile_loop\tdisorder_region\t5\t5",
    ]
