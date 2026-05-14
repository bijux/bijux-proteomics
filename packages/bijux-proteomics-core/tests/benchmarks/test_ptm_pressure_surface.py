# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.benchmarks.flagship_public_packages import (
    build_flagship_ptm_public_benchmark_package,
)
from bijux_proteomics.benchmarks.ptm_pressure import (
    build_ptm_pressure_corpus_report,
)
from bijux_proteomics.ptm import (
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.benchmarks import (
    build_ptm_ambiguity_propagation_benchmark_report,
    build_ptm_family_credibility_track_report,
    build_ptm_lab_targeting_rubric_report,
    build_ptm_localization_confidence_benchmark_report,
    build_ptm_occupancy_stress_benchmark_report,
    build_ptm_raw_spectrum_validation_lane_report,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_pressure_corpus_report_anchors_public_localization_bundle() -> None:
    package = build_flagship_ptm_public_benchmark_package()
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    sites = build_ptm_site_table(mappings)
    feature_records = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records
    localization_confidence = build_ptm_localization_confidence_benchmark_report(
        parsed.accepted_records,
        mappings,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y6", "y7"),
            "scan=ptm-002": ("b4",),
        },
    )
    ambiguity = build_ptm_ambiguity_propagation_benchmark_report(
        sites,
        feature_records=feature_records,
    )
    occupancy = build_ptm_occupancy_stress_benchmark_report(
        sites,
        baseline_feature_records=feature_records,
        stressed_feature_records=tuple(
            row
            for row in feature_records
            if not (row.sample_id == "T2" and row.intensity is not None)
        ),
    )
    raw_validation = build_ptm_raw_spectrum_validation_lane_report(
        parsed.accepted_records,
        raw_spectrum_artifact_path="packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y6"),
        },
    )
    family_credibility = build_ptm_family_credibility_track_report(
        sites,
        feature_records=feature_records,
        protein_sequences=_protein_sequences(),
    )
    lab_targeting = build_ptm_lab_targeting_rubric_report(
        parsed.accepted_records,
        mappings,
        sites,
        feature_records=feature_records,
    )

    report = build_ptm_pressure_corpus_report(
        benchmark_package_id=package.package_id,
        supporting_identity_paths=tuple(asset.path for asset in package.source_assets),
        localization_confidence=localization_confidence,
        ambiguity_propagation=ambiguity,
        occupancy_stress=occupancy,
        raw_spectrum_validation=raw_validation,
        family_credibility=family_credibility,
        lab_targeting=lab_targeting,
    )

    assert report.benchmark_package_id == package.package_id
    assert any(
        path.endswith("evidence/localization_results.tsv")
        for path in report.supporting_identity_paths
    )
    assert report.localization_confidence.ambiguous_count >= 1
    assert report.ambiguity_propagation.interpretive_only_count >= 1
    assert report.ready_for_broad_ptm_claim is False
    assert "raw-spectrum validation" in report.note
