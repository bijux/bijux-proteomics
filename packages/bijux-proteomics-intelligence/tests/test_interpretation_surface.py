# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics import (
    FastaParseMode,
    InstrumentBatchQcReport,
    InstrumentBatchQcRunEntry,
    LabelFreeQuantTable,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    ReplicateCorrelationEntry,
    ReplicateCorrelationReport,
    SearchResultColumnMapping,
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    build_lcms_run_qc_report,
    build_ptm_motif_windows,
    build_ptm_site_fdr,
    build_ptm_site_table,
    build_run_qc_assessment,
    build_spectral_count_table,
    default_qc_threshold_policy,
    estimate_ptm_site_occupancy,
    map_ptm_evidence_to_protein_sites,
    normalize_label_free_table,
    parse_experimental_design_table,
    parse_fasta_document,
    parse_mgf,
    parse_ms1_feature_table,
    parse_psm_tsv,
    parse_ptm_localization_tsv,
)
from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_intelligence import (
    AnalyticalContrastRejectionReason,
    EnrichmentProvenance,
    MissingnessPatternLabel,
    OutlierInterpretationClass,
    PathwayInterpretationCautionCode,
    ProteinAnnotationAssignment,
    QuantQcEvidenceIntegrationReport,
    RankedEntityScore,
    analyze_missingness_patterns,
    build_run_interpretation_summary,
    compute_protein_set_enrichment,
    compute_ranked_enrichment,
    explain_outlier_samples,
    extract_biological_themes,
    integrate_quant_qc_evidence,
    interpret_contaminant_artifacts,
    interpret_differential_abundance,
    interpret_ptm_sites,
    recommend_experimental_contrasts,
)


def _repo_packages_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _core_fixture(package: str, name: str) -> Path:
    return (
        _repo_packages_dir()
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / package
        / name
    )


def _local_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "interpretation" / name


def _annotations() -> tuple[ProteinAnnotationAssignment, ...]:
    payload = json.loads(_local_fixture("annotations.json").read_text())
    return tuple(ProteinAnnotationAssignment.model_validate(item) for item in payload)


def test_run_interpretation_summary_and_artifact_intelligence_use_real_qc_surface() -> (
    None
):
    design = parse_experimental_design_table(
        _core_fixture("production_run", "design.tsv")
    ).accepted_entries[0]
    fasta_report = parse_fasta_document(
        _core_fixture("production_run", "proteins.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    proteins = {
        record.canonical_accession: record.residues
        for record in fasta_report.accepted_records
    }
    spectra = parse_mgf(_core_fixture("production_run", "spectra.mgf")).accepted_spectra
    psms = parse_psm_tsv(
        _core_fixture("production_run", "results.tsv"),
        mapping=SearchResultColumnMapping(
            spectrum_id="spectrum_id",
            peptide="peptide",
            charge="charge",
            score="score",
            protein_refs="proteins",
        ),
    ).accepted_records
    features = parse_ms1_feature_table(
        _core_fixture("production_run", "ms1_features.tsv")
    ).accepted_records
    quant_table = build_label_free_intensity_table(
        features,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    run_report = build_lcms_run_qc_report(
        spectra,
        psms,
        design_entry=design,
        protein_sequences=proteins,
    )
    assessment = build_run_qc_assessment(
        run_report, policy=default_qc_threshold_policy()
    )

    summary = build_run_interpretation_summary(
        run_report, assessment, quant_table=quant_table
    )
    artifacts = interpret_contaminant_artifacts(run_report, assessment)

    assert summary.run_id == "spectra"
    assert summary.quantified_entity_count == 1
    assert any(signal.code == "quant-available" for signal in summary.major_signals)
    assert any(
        finding.code == "mass-calibration-drift" for finding in artifacts.findings
    )


def test_differential_interpretation_and_theme_extraction_surface_signal() -> None:
    feature_report = parse_ms1_feature_table(_core_fixture("quant", "ms1_features.tsv"))
    design_report = parse_experimental_design_table(
        _core_fixture("quant", "quant.design.tsv")
    )
    table = normalize_label_free_table(
        build_label_free_intensity_table(
            feature_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.TOP_N,
            top_n=2,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    differential = apply_benjamini_hochberg(
        build_differential_abundance_report(
            table,
            design_report.accepted_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    annotations = _annotations()

    interpretation = interpret_differential_abundance(differential, annotations)
    themes = extract_biological_themes(
        ("P001", "P003"),
        ("P001", "P002", "P003", "P004"),
        annotations,
    )

    assert interpretation.top_upregulated[0].entity_id == "P001"
    assert interpretation.top_downregulated == ()
    assert interpretation.statistical_provenance.significant_entity_count == 1
    assert (
        interpretation.statistical_provenance.multiple_testing_method
        == "benjamini-hochberg"
    )
    assert interpretation.caution_report.blocked is True
    assert interpretation.caution_report.caution_items[0].code is (
        PathwayInterpretationCautionCode.LOW_SIGNIFICANT_ENTITY_COUNT
    )
    assert interpretation.enriched_terms[0].term_name == "nucleus"
    assert isinstance(themes.enrichment_provenance, EnrichmentProvenance)
    assert themes.enrichment_provenance.background_proteins == (
        "P001",
        "P002",
        "P003",
        "P004",
    )
    assert themes.enrichment_provenance.multiple_testing_method == "benjamini-hochberg"
    assert themes.themes[0].term_name == "MAPK signaling"


def test_ptm_interpretation_surfaces_changed_sites_motifs_and_kinase_advisories() -> (
    None
):
    evidence = parse_ptm_localization_tsv(
        _core_fixture("ptm", "localization_results.tsv")
    )
    fasta = parse_fasta_document(
        _core_fixture("fasta", "ptm_sites.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    proteins = {
        record.canonical_accession: record.residues for record in fasta.accepted_records
    }
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records, protein_sequences=proteins
    )
    site_table = build_ptm_site_table(mappings)
    fdr = build_ptm_site_fdr(site_table, threshold=0.1)
    motifs = build_ptm_motif_windows(
        site_table, protein_sequences=proteins, flank_size=3
    )
    features = parse_ms1_feature_table(_core_fixture("ptm", "ptm_features.tsv"))
    occupancy = estimate_ptm_site_occupancy(
        site_table, feature_records=features.accepted_records
    )

    report = interpret_ptm_sites(
        site_table,
        fdr,
        motif_windows=motifs,
        occupancy=occupancy,
        annotations=_annotations(),
    )

    assert report.accepted_site_count >= 1
    assert any(site.site_key == "P11111:S5:Phospho" for site in report.changed_sites)
    assert "ERK substrate program" in report.advisory_kinases


def test_experimental_contrast_recommender_distinguishes_valid_and_confounded_pairs() -> (
    None
):
    valid_design = parse_experimental_design_table(
        _core_fixture("quant", "quant.design.tsv")
    )
    confounded_design = parse_experimental_design_table(
        _local_fixture("confounded.design.tsv")
    )

    valid = recommend_experimental_contrasts(valid_design.accepted_entries)
    rejected = recommend_experimental_contrasts(confounded_design.accepted_entries)

    assert len(valid.valid_contrasts) == 1
    assert valid.valid_contrasts[0].condition_a == "control"
    assert len(rejected.rejected_contrasts) == 1
    assert (
        AnalyticalContrastRejectionReason.BATCH_CONFOUNDED
        in rejected.rejected_contrasts[0].rejection_reasons
    )


def test_missingness_pattern_analysis_classifies_filtered_and_condition_linked_cases() -> (
    None
):
    feature_report = parse_ms1_feature_table(_core_fixture("quant", "ms1_features.tsv"))
    design_report = parse_experimental_design_table(
        _core_fixture("quant", "quant.design.tsv")
    )
    table: LabelFreeQuantTable = build_spectral_count_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PEPTIDE,
    )

    analysis = analyze_missingness_patterns(table, design_report.accepted_entries)
    by_entity = {entry.entity_id: entry for entry in analysis.entries}

    assert by_entity["FILTERPEP"].label is MissingnessPatternLabel.FILTER_DOMINATED
    assert analysis.overall_label is MissingnessPatternLabel.MIXED


def test_outlier_sample_explainer_uses_batch_and_correlation_signals() -> None:
    batch_report = InstrumentBatchQcReport(
        document_schema=DocumentSchema(
            created_by="test",
            document_kind="instrument_batch_qc_report",
            package_name="test",
            status="generated",
        ),
        batch_id="batch-z",
        instrument="orbitrap-z",
        run_count=3,
        median_spectrum_count=9500.0,
        median_identification_rate=0.21,
        median_abs_mass_error_ppm=6.5,
        median_identified_retention_time_seconds=1800.0,
        outlier_run_ids=("run-t2",),
        runs=(
            InstrumentBatchQcRunEntry(
                run_id="run-c1",
                sample_id="C1",
                batch="batch-z",
                instrument="orbitrap-z",
                spectrum_count=10000,
                identification_rate=0.24,
                median_abs_mass_error_ppm=5.4,
                identified_retention_time_span_seconds=1820.0,
                retention_time_shift_seconds=0.0,
                outlier_reasons=(),
            ),
            InstrumentBatchQcRunEntry(
                run_id="run-t1",
                sample_id="T1",
                batch="batch-z",
                instrument="orbitrap-z",
                spectrum_count=9800,
                identification_rate=0.22,
                median_abs_mass_error_ppm=5.9,
                identified_retention_time_span_seconds=1790.0,
                retention_time_shift_seconds=12.0,
                outlier_reasons=(),
            ),
            InstrumentBatchQcRunEntry(
                run_id="run-t2",
                sample_id="T2",
                batch="batch-z",
                instrument="orbitrap-z",
                spectrum_count=7200,
                identification_rate=0.11,
                median_abs_mass_error_ppm=12.2,
                identified_retention_time_span_seconds=1650.0,
                retention_time_shift_seconds=95.0,
                outlier_reasons=("low_identification_rate", "high_mass_error"),
            ),
        ),
    )
    replicate_report = ReplicateCorrelationReport(
        entity_level=QuantEntityLevel.PROTEIN,
        entries=(
            ReplicateCorrelationEntry(
                sample_a="C1",
                sample_b="T2",
                condition_a="control",
                condition_b="treatment",
                correlation=0.62,
                shared_entity_count=12,
            ),
            ReplicateCorrelationEntry(
                sample_a="T1",
                sample_b="T2",
                condition_a="treatment",
                condition_b="treatment",
                correlation=0.62,
                shared_entity_count=12,
            ),
        ),
        within_condition_mean=None,
        between_condition_mean=0.62,
    )

    explanations = explain_outlier_samples(batch_report, replicate_report)
    by_sample = {entry.sample_id: entry for entry in explanations}

    assert "C1" not in by_sample
    assert "T2" in by_sample
    assert (
        by_sample["T2"].classification
        is OutlierInterpretationClass.TECHNICAL_ANOMALY
    )
    assert "low_identification_rate" in by_sample["T2"].reasons
    assert "low_replicate_correlation" in by_sample["T2"].reasons
    assert by_sample["T2"].technical_reasons


def test_outlier_sample_explainer_preserves_plausible_biological_separation() -> None:
    batch_report = InstrumentBatchQcReport(
        document_schema=DocumentSchema(
            created_by="test",
            document_kind="instrument_batch_qc_report",
            package_name="test",
            status="generated",
        ),
        batch_id="batch-bio",
        instrument="orbitrap-bio",
        run_count=2,
        median_spectrum_count=9900.0,
        median_identification_rate=0.24,
        median_abs_mass_error_ppm=5.4,
        median_identified_retention_time_seconds=1800.0,
        outlier_run_ids=("run-t1",),
        runs=(
            InstrumentBatchQcRunEntry(
                run_id="run-c1",
                sample_id="C1",
                batch="batch-bio",
                instrument="orbitrap-bio",
                spectrum_count=10000,
                identification_rate=0.24,
                median_abs_mass_error_ppm=5.4,
                identified_retention_time_span_seconds=1800.0,
                retention_time_shift_seconds=0.0,
                outlier_reasons=(),
            ),
            InstrumentBatchQcRunEntry(
                run_id="run-t1",
                sample_id="T1",
                batch="batch-bio",
                instrument="orbitrap-bio",
                spectrum_count=10100,
                identification_rate=0.26,
                median_abs_mass_error_ppm=5.0,
                identified_retention_time_span_seconds=1810.0,
                retention_time_shift_seconds=2.0,
                outlier_reasons=(),
            ),
        ),
    )
    replicate_report = ReplicateCorrelationReport(
        entity_level=QuantEntityLevel.PROTEIN,
        entries=(
            ReplicateCorrelationEntry(
                sample_a="C1",
                sample_b="T1",
                condition_a="control",
                condition_b="treatment",
                correlation=0.51,
                shared_entity_count=18,
            ),
        ),
        within_condition_mean=None,
        between_condition_mean=0.51,
    )

    explanations = explain_outlier_samples(batch_report, replicate_report)
    by_sample = {entry.sample_id: entry for entry in explanations}

    assert by_sample["T1"].classification is (
        OutlierInterpretationClass.PLAUSIBLE_BIOLOGICAL_EFFECT
    )
    assert "condition_separation_without_qc_failure" in by_sample["T1"].biological_reasons


def test_integrate_quant_qc_evidence_combines_missingness_and_outliers() -> None:
    feature_report = parse_ms1_feature_table(_core_fixture("quant", "ms1_features.tsv"))
    design_report = parse_experimental_design_table(
        _core_fixture("quant", "quant.design.tsv")
    )
    table = build_spectral_count_table(
        feature_report.accepted_records,
        entity_level=QuantEntityLevel.PEPTIDE,
    )
    batch_report = InstrumentBatchQcReport(
        document_schema=DocumentSchema(
            created_by="test",
            document_kind="instrument_batch_qc_report",
            package_name="test",
            status="generated",
        ),
        batch_id="batch-z",
        instrument="orbitrap-z",
        run_count=2,
        median_spectrum_count=8500.0,
        median_identification_rate=0.19,
        median_abs_mass_error_ppm=7.1,
        median_identified_retention_time_seconds=1740.0,
        outlier_run_ids=("run-t2",),
        runs=(
            InstrumentBatchQcRunEntry(
                run_id="run-c1",
                sample_id="C1",
                batch="batch-z",
                instrument="orbitrap-z",
                spectrum_count=9100,
                identification_rate=0.23,
                median_abs_mass_error_ppm=5.1,
                identified_retention_time_span_seconds=1810.0,
                retention_time_shift_seconds=0.0,
                outlier_reasons=(),
            ),
            InstrumentBatchQcRunEntry(
                run_id="run-t2",
                sample_id="T2",
                batch="batch-z",
                instrument="orbitrap-z",
                spectrum_count=6800,
                identification_rate=0.1,
                median_abs_mass_error_ppm=12.8,
                identified_retention_time_span_seconds=1600.0,
                retention_time_shift_seconds=110.0,
                outlier_reasons=("low_identification_rate",),
            ),
        ),
    )
    replicate_report = ReplicateCorrelationReport(
        entity_level=QuantEntityLevel.PEPTIDE,
        entries=(
            ReplicateCorrelationEntry(
                sample_a="T1",
                sample_b="T2",
                condition_a="treatment",
                condition_b="treatment",
                correlation=0.61,
                shared_entity_count=10,
            ),
        ),
        within_condition_mean=0.61,
        between_condition_mean=None,
    )

    report = integrate_quant_qc_evidence(
        table,
        design_report.accepted_entries,
        batch_report,
        replicate_report,
    )

    assert isinstance(report, QuantQcEvidenceIntegrationReport)
    assert report.missingness.overall_label is MissingnessPatternLabel.MIXED
    assert report.outliers[0].sample_id == "T2"
    assert any("QC-supported outlier behavior" in note for note in report.notes)
    assert any("outliers look technical" in note for note in report.notes)


def test_protein_set_and_ranked_enrichment_reports_are_ordered_and_deterministic() -> (
    None
):
    annotations = _annotations()
    overrepresentation = compute_protein_set_enrichment(
        ("P001", "P003"),
        ("P001", "P002", "P003", "P004"),
        annotations,
    )
    ranked = compute_ranked_enrichment(
        tuple(
            RankedEntityScore.model_validate(item)
            for item in json.loads(_local_fixture("ranked_entities.json").read_text())
        ),
        annotations,
    )

    assert overrepresentation.entries[0].term_name == "MAPK signaling"
    assert ranked.entries[0].term_name == "MAPK signaling"
    assert ranked.entries[0].direction.value == "up"
