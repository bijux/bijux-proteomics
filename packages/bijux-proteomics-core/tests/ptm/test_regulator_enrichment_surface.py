# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    build_ptm_differential_analysis_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.differential_analysis import (
    PtmSiteDifferentialEntry,
    PtmSiteDifferentialReport,
)
from bijux_proteomics.ptm.localization_scoring import PtmLocalizationConfidenceTier
from bijux_proteomics.ptm.regulator_enrichment import (
    PtmRegulatorDirection,
    PtmRegulatorEnrichmentPolicy,
    PtmRegulatorKind,
    build_ptm_regulator_enrichment_report,
)
from bijux_proteomics.ptm.site_annotation_import import (
    PtmMappedSiteAnnotationEntry,
    PtmSiteAnnotationMappingReport,
    PtmSiteAnnotationMappingSummary,
    build_ptm_site_annotation_mapping_report,
    parse_ptm_site_annotation_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
from bijux_proteomics.quantification.contracts import DifferentialAbundanceTestType
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


def test_ptm_regulator_enrichment_reports_exact_supporting_sites_from_real_annotations() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_fixture_path("ptm_features.tsv"))
    site_quantification = build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = parse_experimental_design_table(_fixture_path("ptm.design.tsv"))
    differential = build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
    )
    annotation_report = parse_ptm_site_annotation_tsv(
        _fixture_path("ptm_site_annotations.tsv")
    )
    mapping_report = build_ptm_site_annotation_mapping_report(
        site_table,
        annotation_report.accepted_records,
        target_species="Homo sapiens",
    )

    report = build_ptm_regulator_enrichment_report(
        differential.differential_report,
        mapping_report,
        policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.5,
        ),
    )

    assert report.condition_a == "control"
    assert report.condition_b == "treated"
    assert report.summary.upregulated_site_count >= 1
    kinase_entry = next(
        entry
        for entry in report.entries
        if entry.regulator == "AKT1"
        and entry.regulator_kind is PtmRegulatorKind.KINASE
        and entry.direction is PtmRegulatorDirection.UPREGULATED
    )
    phosphatase_entry = next(
        entry
        for entry in report.entries
        if entry.regulator == "PPP2CA"
        and entry.regulator_kind is PtmRegulatorKind.PHOSPHATASE
        and entry.direction is PtmRegulatorDirection.UPREGULATED
    )

    assert kinase_entry.supporting_sites == ("P11111:S5:Phospho",)
    assert phosphatase_entry.supporting_sites == ("P11111:S5:Phospho",)
    assert kinase_entry.adjusted_p_value is not None
    assert phosphatase_entry.adjusted_p_value is not None


def test_ptm_regulator_enrichment_separates_direction_and_preserves_site_ledgers() -> (
    None
):
    differential_report = PtmSiteDifferentialReport(
        normalization_method=NormalizationMethod.MEDIAN,
        test_type=DifferentialAbundanceTestType.WELCH_T_TEST,
        condition_a="control",
        condition_b="treated",
        entries=(
            PtmSiteDifferentialEntry(
                site_key="P11111:S5:Phospho",
                protein_ref="P11111",
                residue="S",
                position=5,
                modification_name="Phospho",
                localization_tier=PtmLocalizationConfidenceTier.SUPPORTED,
                condition_a="control",
                condition_b="treated",
                observations_a=2,
                observations_b=2,
                mean_log2_abundance_a=1.0,
                mean_log2_abundance_b=2.2,
                log2_fold_change=1.2,
                p_value=0.01,
                adjusted_p_value=0.02,
                protein_correction_status="not_requested",
            ),
            PtmSiteDifferentialEntry(
                site_key="P11111:S9:Phospho",
                protein_ref="P11111",
                residue="S",
                position=9,
                modification_name="Phospho",
                localization_tier=PtmLocalizationConfidenceTier.SUPPORTED,
                condition_a="control",
                condition_b="treated",
                observations_a=2,
                observations_b=2,
                mean_log2_abundance_a=1.1,
                mean_log2_abundance_b=2.5,
                log2_fold_change=1.4,
                p_value=0.015,
                adjusted_p_value=0.03,
                protein_correction_status="not_requested",
            ),
            PtmSiteDifferentialEntry(
                site_key="P22222:Y18:Phospho",
                protein_ref="P22222",
                residue="Y",
                position=18,
                modification_name="Phospho",
                localization_tier=PtmLocalizationConfidenceTier.SUPPORTED,
                condition_a="control",
                condition_b="treated",
                observations_a=2,
                observations_b=2,
                mean_log2_abundance_a=2.4,
                mean_log2_abundance_b=0.8,
                log2_fold_change=-1.6,
                p_value=0.02,
                adjusted_p_value=0.04,
                protein_correction_status="not_requested",
            ),
        ),
        note="synthetic differential report for regulator enrichment coverage",
    )
    mapping_report = PtmSiteAnnotationMappingReport(
        target_species="Homo sapiens",
        matched_annotations=(
            PtmMappedSiteAnnotationEntry(
                site_key="P11111:S5:Phospho",
                annotation_species="Homo sapiens",
                observed_species="Homo sapiens",
                protein_ref="P11111",
                residue="S",
                position=5,
                modification_name="Phospho",
                kinases=("AKT1",),
                phosphatases=("PPP2CA",),
            ),
            PtmMappedSiteAnnotationEntry(
                site_key="P11111:S9:Phospho",
                annotation_species="Homo sapiens",
                observed_species="Homo sapiens",
                protein_ref="P11111",
                residue="S",
                position=9,
                modification_name="Phospho",
                kinases=("AKT1",),
            ),
            PtmMappedSiteAnnotationEntry(
                site_key="P22222:Y18:Phospho",
                annotation_species="Homo sapiens",
                observed_species="Homo sapiens",
                protein_ref="P22222",
                residue="Y",
                position=18,
                modification_name="Phospho",
                phosphatases=("PTPN11",),
            ),
        ),
        summary=PtmSiteAnnotationMappingSummary(
            matched_annotation_count=3,
            matched_site_count=3,
            unmapped_annotation_count=0,
            species_mismatch_count=0,
        ),
        note="synthetic mapping report for regulator enrichment coverage",
    )

    report = build_ptm_regulator_enrichment_report(
        differential_report,
        mapping_report,
        policy=PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=1.0,
        ),
    )

    akt1 = next(
        entry
        for entry in report.entries
        if entry.regulator == "AKT1"
        and entry.regulator_kind is PtmRegulatorKind.KINASE
        and entry.direction is PtmRegulatorDirection.UPREGULATED
    )
    ptpn11 = next(
        entry
        for entry in report.entries
        if entry.regulator == "PTPN11"
        and entry.regulator_kind is PtmRegulatorKind.PHOSPHATASE
        and entry.direction is PtmRegulatorDirection.DOWNREGULATED
    )

    assert akt1.supporting_site_count == 2
    assert akt1.supporting_sites == ("P11111:S5:Phospho", "P11111:S9:Phospho")
    assert ptpn11.supporting_site_count == 1
    assert ptpn11.supporting_sites == ("P22222:Y18:Phospho",)
    assert akt1.adjusted_p_value is not None
    assert ptpn11.adjusted_p_value is not None
