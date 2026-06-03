# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.ptm import (
    PtmSiteEntry,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.benchmarks import (
    ProteoformBenchmarkScenario,
    PtmFamilyCredibilityTrackReport,
    PtmLabTargetingDisposition,
    PtmLocalizationBenchmarkConfidenceTier,
    PtmMotifCredibilityDisposition,
    build_glycopeptide_support_roadmap_report,
    build_proteoform_benchmark_report,
    build_ptm_ambiguity_propagation_benchmark_report,
    build_ptm_family_credibility_track_report,
    build_ptm_lab_targeting_rubric_report,
    build_ptm_localization_confidence_benchmark_report,
    build_ptm_motif_credibility_benchmark_report,
    build_ptm_occupancy_stress_benchmark_report,
    build_ptm_raw_spectrum_validation_lane_report,
)
from bijux_proteomics.ptm.proteoforms import (
    ProteoformEvidenceLevel,
    ProteoformPtmAssignment,
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


def test_ptm_localization_confidence_benchmark_report_scores_decisive_and_ambiguous_sites() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )

    report = build_ptm_localization_confidence_benchmark_report(
        parsed.accepted_records,
        mappings,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y6", "y7"),
            "scan=ptm-002": ("b4",),
        },
    )

    supported = next(
        entry
        for entry in report.entries
        if entry.confidence_tier is PtmLocalizationBenchmarkConfidenceTier.SUPPORTED
    )
    ambiguous = next(
        entry
        for entry in report.entries
        if entry.confidence_tier is PtmLocalizationBenchmarkConfidenceTier.AMBIGUOUS
    )

    assert supported.localization_probability >= 0.95
    assert supported.fragment_ion_count >= 2
    assert ambiguous.ambiguity_present is True
    assert report.ambiguous_count >= 1


def test_ptm_raw_spectrum_validation_lane_report_requires_fragment_linkage() -> None:
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))

    report = build_ptm_raw_spectrum_validation_lane_report(
        parsed.accepted_records,
        raw_spectrum_artifact_path="packages/bijux-proteomics-core/tests/fixtures/production_run/spectra.mgf",
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y6"),
        },
    )

    assert report.localized_spectrum_count >= 1
    assert report.fragment_supported_spectrum_count == 1
    assert report.unsupported_spectrum_ids
    assert report.ready_for_rescoring_follow_up is False


def test_ptm_ambiguity_propagation_benchmark_report_downgrades_ambiguous_sites() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    sites = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records

    report = build_ptm_ambiguity_propagation_benchmark_report(
        sites,
        feature_records=features,
    )

    propagated = next(entry for entry in report.entries if entry.propagated_to_quant)
    interpretive_only = next(
        entry for entry in report.entries if entry.interpretive_only
    )

    assert propagated.localization_ambiguous is True
    assert propagated.ambiguous_occupancy_count >= 1
    assert interpretive_only.missing_counterpart_count >= 0
    assert report.interpretive_only_count >= 1


def test_ptm_family_credibility_track_report_separates_supported_interpretive_and_refused() -> (
    None
):
    provenance = ImportedEvidenceProvenance(
        source_engine="ptm-benchmark",
        source_files=("inline",),
    )
    site_entries = (
        PtmSiteEntry(
            site_key="P1:S5:Phospho",
            protein_ref="P1",
            residue="S",
            position=5,
            modification_name="Phospho",
            localization_score=0.98,
            best_q_value=0.01,
            spectrum_count=2,
            peptide_count=1,
            localized_peptides=("AAASPEP",),
            sample_ids=("C1", "T1"),
            ambiguous=True,
            provenance=provenance,
        ),
        PtmSiteEntry(
            site_key="P2:K1:Acetyl",
            protein_ref="P2",
            residue="K",
            position=1,
            modification_name="Acetyl",
            localization_score=0.97,
            best_q_value=0.01,
            spectrum_count=1,
            peptide_count=1,
            localized_peptides=("KPEPTIDE",),
            sample_ids=("C1",),
            ambiguous=False,
            provenance=provenance,
        ),
        PtmSiteEntry(
            site_key="P3:K12:GlyGly",
            protein_ref="P3",
            residue="K",
            position=12,
            modification_name="GlyGly",
            localization_score=0.95,
            best_q_value=0.02,
            spectrum_count=1,
            peptide_count=1,
            localized_peptides=("PEPTIDEK",),
            sample_ids=("T1",),
            ambiguous=False,
            provenance=provenance,
        ),
    )
    feature_records = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records

    report = build_ptm_family_credibility_track_report(
        site_entries,
        feature_records=feature_records,
        protein_sequences=_protein_sequences(),
    )

    assert isinstance(report, PtmFamilyCredibilityTrackReport)
    assert "glyco_adjacent" in report.refused_families
    assert "phosphorylation" in report.interpretive_only_families
    assert any(track.family_name == "acetylation" for track in report.tracks)


def test_proteoform_benchmark_report_marks_isoform_and_combinatorial_pressure() -> None:
    report = build_proteoform_benchmark_report(
        (
            ProteoformBenchmarkScenario(
                scenario_id="clean",
                sequence="PEPTIDE",
                protein_origin="P11111-1",
                evidence_level=ProteoformEvidenceLevel.PROBABLE,
                ptm_assignments=(ProteoformPtmAssignment(name="Phospho", site="S5"),),
            ),
            ProteoformBenchmarkScenario(
                scenario_id="ambiguous",
                sequence="PEPTIDE",
                protein_origin="P11111-2",
                evidence_level=ProteoformEvidenceLevel.ADVISORY,
                ptm_assignments=(
                    ProteoformPtmAssignment(name="Phospho", site="S5"),
                    ProteoformPtmAssignment(name="Acetyl", site="K2"),
                    ProteoformPtmAssignment(name="GlyGly", site="K7"),
                ),
                isoform_ambiguous=True,
                shared_peptide_pressure=True,
            ),
        )
    )

    assert report.interpretive_only_count == 1
    ambiguous = next(
        entry for entry in report.entries if entry.scenario_id == "ambiguous"
    )
    assert ambiguous.interpretive_only is True
    clean = next(entry for entry in report.entries if entry.scenario_id == "clean")
    assert clean.interpretive_only is False


def test_ptm_occupancy_stress_benchmark_report_tracks_missing_feature_pressure() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    sites = build_ptm_site_table(mappings)
    baseline = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records
    stressed = tuple(
        row
        for row in baseline
        if not (row.sample_id == "T2" and row.intensity is not None)
    )

    report = build_ptm_occupancy_stress_benchmark_report(
        sites,
        baseline_feature_records=baseline,
        stressed_feature_records=stressed,
    )

    assert report.missing_counterpart_count >= 1
    assert report.occupancy_shift_fraction >= 0.0


def test_glycopeptide_support_roadmap_report_names_exact_future_work() -> None:
    report = build_glycopeptide_support_roadmap_report(
        requested_workflow="n_glycopeptide_localization"
    )

    assert report.current_disposition == "refused"
    assert report.required_scientific_work
    assert report.required_engineering_work
    assert "glycosite_localization" in report.blocking_evidence_fields


def test_ptm_motif_credibility_benchmark_report_blocks_small_ambiguous_motif_claims() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    sites = build_ptm_site_table(mappings)

    report = build_ptm_motif_credibility_benchmark_report(
        sites,
        protein_sequences=_protein_sequences(),
        modification_name="Phospho",
    )

    assert report.disposition is PtmMotifCredibilityDisposition.INTERPRETIVE_ONLY
    assert report.foreground_site_count >= 1
    assert report.caveats


def test_ptm_lab_targeting_rubric_report_preserves_interpretive_only_boundaries() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    sites = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records

    report = build_ptm_lab_targeting_rubric_report(
        parsed.accepted_records,
        mappings,
        sites,
        feature_records=features,
        fragment_ion_support_by_spectrum={
            "scan=ptm-001": ("b5", "y6", "y7"),
            "scan=ptm-002": ("b4",),
        },
    )

    assert all(
        entry.disposition is PtmLabTargetingDisposition.INTERPRETIVE_ONLY
        for entry in report.entries
    )
    assert report.targetable_count == 0
    assert report.interpretive_only_count == len(report.entries)
    assert any(
        entry.localization_confidence_tier
        is PtmLocalizationBenchmarkConfidenceTier.SUPPORTED
        and entry.occupancy_complete is True
        for entry in report.entries
    )
    assert all(entry.rationale for entry in report.entries)
