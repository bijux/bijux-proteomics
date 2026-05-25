# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import bijux_proteomics.ptm as ptm
from bijux_proteomics.chemistry import (
    FragmentIonSeries,
    calculate_fragment_ions,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.io.spectra import SpectrumPeak
from bijux_proteomics.ptm.contracts import PtmEvidenceRecord
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingValueKind,
    QuantEntityLevel,
    QuantMeasureKind,
    QuantRollupMethod,
    QuantValue,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _protein_sequences() -> dict[str, str]:
    report = parse_fasta_document(
        _fasta_fixture("ptm_sites.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_package_exports_protein_site_mapping_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    report = ptm.build_ptm_protein_site_mapping_report(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    rendered = ptm.render_ptm_unmapped_peptide_tsv(report.unmapped_peptides)

    assert hasattr(ptm, "build_ptm_protein_site_mapping_report")
    assert hasattr(ptm, "render_ptm_unmapped_peptide_tsv")
    assert len(report.ambiguous_mappings) == 4
    assert rendered.splitlines()[0].startswith(
        "spectrum_id\tsample_id\tlocalized_peptide"
    )


def test_ptm_package_exports_site_group_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    entries = ptm.build_site_groups(mappings)
    rendered = ptm.render_ptm_site_group_tsv(entries)

    assert hasattr(ptm, "build_site_groups")
    assert hasattr(ptm, "render_ptm_site_group_tsv")
    ambiguous = next(
        entry
        for entry in entries
        if entry.site_group_id == "P11111:Phospho:17|18|19"
    )
    assert ambiguous.localized_site is None
    assert ambiguous.candidate_sites == (17, 18, 19)
    assert ambiguous.ambiguity_class.value == "ambiguous_site_group"
    assert "ambiguity_class" in rendered.splitlines()[0]


def test_ptm_package_exports_abundance_correction_owner_surface() -> None:
    rows = ptm.correct_site_by_protein(
        (
            ptm.PtmSiteCorrectionCandidate(
                site_id="P11111:S5:Phospho",
                protein_id="P11111",
                raw_site_log2fc=1.8,
            ),
            ptm.PtmSiteCorrectionCandidate(
                site_id="P22222:Y18:Phospho",
                protein_id="P22222",
                raw_site_log2fc=0.9,
            ),
        ),
        (
            ptm.PtmProteinCorrectionReference(
                protein_id="P11111",
                protein_log2fc=0.5,
            ),
        ),
    )
    rendered = ptm.render_site_protein_correction_tsv(rows)

    assert hasattr(ptm, "correct_site_by_protein")
    assert hasattr(ptm, "render_site_protein_correction_tsv")
    corrected = next(row for row in rows if row.site_id == "P11111:S5:Phospho")
    missing = next(row for row in rows if row.site_id == "P22222:Y18:Phospho")
    assert corrected.corrected_site_log2fc == 1.3
    assert corrected.correction_status.value == "high_confidence_corrected"
    assert missing.corrected_site_log2fc is None
    assert missing.correction_status.value == "missing_protein_baseline"
    assert "correction_status" in rendered.splitlines()[0]


def test_ptm_package_exports_localization_scoring_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(
        _ptm_fixture("localization_probability_results.tsv")
    )
    report = ptm.build_ptm_localization_scoring_report(evidence.accepted_records)
    rendered = ptm.render_ptm_localization_scoring_entry_tsv(report)

    assert hasattr(ptm, "build_ptm_localization_scoring_report")
    assert hasattr(ptm, "render_ptm_localization_scoring_summary_tsv")
    assert hasattr(ptm, "PtmLocalizationConfidenceTier")
    assert report.high_confidence_entry_count == 1
    assert "localization_tier" in rendered.splitlines()[0]


def test_ptm_package_exports_fragment_scoring_owner_surface() -> None:
    peptide = parse_modified_peptide("AS[Phospho]TYK")
    ions = calculate_fragment_ions(
        peptide,
        charges=(1,),
        series=(FragmentIonSeries.B,),
        include_neutral_losses=True,
    )
    b2 = next(
        ion
        for ion in ions
        if ion.series is FragmentIonSeries.B and ion.ordinal == 2 and ion.neutral_loss is None
    )
    b2_neutral_loss = next(
        ion
        for ion in ions
        if ion.series is FragmentIonSeries.B
        and ion.ordinal == 2
        and ion.neutral_loss == "phosphoric_acid"
    )
    report = ptm.score_ptm_fragments(
        "AS[Phospho]TYK",
        (
            SpectrumPeak(mz=b2.mz_monoisotopic, intensity=120.0),
            SpectrumPeak(mz=b2_neutral_loss.mz_monoisotopic, intensity=95.0),
        ),
        tolerance=0.01,
    )
    rendered = ptm.render_ptm_fragment_scores_tsv(report)

    assert hasattr(ptm, "score_ptm_fragments")
    assert hasattr(ptm, "render_ptm_fragment_scores_tsv")
    assert any(row.site_determining for row in report)
    assert any(row.neutral_loss == "phosphoric_acid" for row in report)
    assert "site_determining" in rendered


def test_ptm_package_exports_kinase_inference_owner_surface() -> None:
    rows = ptm.infer_kinases(
        (
            ptm.PtmKinaseSiteResult(
                site_id="P11111:S5:Phospho",
                protein_id="P11111",
                signed_effect=1.6,
            ),
            ptm.PtmKinaseSiteResult(
                site_id="P11111:T8:Phospho",
                protein_id="P11111",
                signed_effect=1.1,
            ),
        ),
        (
            ptm.PtmKinaseMotifMatch(
                kinase="MAPK1",
                site_id="P11111:S5:Phospho",
                motif_score=0.93,
            ),
            ptm.PtmKinaseMotifMatch(
                kinase="PKA",
                site_id="P11111:T8:Phospho",
                motif_score=0.95,
            ),
        ),
        (
            ptm.PtmKinaseSubstrateMatch(
                kinase="MAPK1",
                site_id="P11111:S5:Phospho",
            ),
        ),
    )
    rendered = ptm.render_ptm_kinase_inference_tsv(rows)

    assert hasattr(ptm, "infer_kinases")
    assert hasattr(ptm, "render_ptm_kinase_inference_tsv")
    assert rows[0].kinase == "MAPK1"
    assert rows[0].combined_score > rows[1].combined_score
    assert rows[0].confidence_tier.value == "motif_plus_substrate"
    assert "confidence_tier" in rendered


def test_ptm_package_exports_phosphatase_inference_owner_surface() -> None:
    rows = ptm.infer_phosphatases(
        (
            ptm.PtmPhosphataseSiteResult(
                site_id="P11111:S5:Phospho",
                protein_id="P11111",
                signed_effect=-1.4,
            ),
        ),
        (
            ptm.PtmPhosphataseSubstrateAnnotation(
                phosphatase="PPP2CA",
                site_id="P11111:S5:Phospho",
                substrate_protein_id="P11111",
            ),
            ptm.PtmPhosphataseSubstrateAnnotation(
                phosphatase="PTPN11",
                substrate_protein_id="P11111",
            ),
        ),
    )
    rendered = ptm.render_ptm_phosphatase_inference_tsv(rows)

    assert hasattr(ptm, "infer_phosphatases")
    assert hasattr(ptm, "render_ptm_phosphatase_inference_tsv")
    assert len(rows) == 1
    assert rows[0].phosphatase == "PPP2CA"
    assert rows[0].site_directions[0].value == "downregulated"
    assert "annotation_coverage" in rendered


def test_ptm_package_exports_localization_risk_owner_surface() -> None:
    localization_candidates = (
        PtmEvidenceRecord(
            spectrum_id="scan=ptm-risk",
            sample_id="C1",
            localized_peptide="AS[Phospho]YTK",
            canonical_peptide="AS[Phospho]YTK",
            sequence="ASYTK",
            charge=2,
            score=95.0,
            q_value=0.02,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            localization_score=25.0,
            candidate_site_indices=(2, 4),
            modification_names=("Phospho",),
            provenance=ImportedEvidenceProvenance(
                source_engine="ptm-localization",
                source_files=("inline",),
            ),
        ),
        PtmEvidenceRecord(
            spectrum_id="scan=ptm-risk",
            sample_id="C1",
            localized_peptide="ASYT[Phospho]K",
            canonical_peptide="ASYT[Phospho]K",
            sequence="ASYTK",
            charge=2,
            score=92.0,
            q_value=0.02,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
            localization_score=18.0,
            candidate_site_indices=(2, 4),
            modification_names=("Phospho",),
            provenance=ImportedEvidenceProvenance(
                source_engine="ptm-localization",
                source_files=("inline",),
            ),
        ),
    )
    rows = ptm.detect_false_localization(
        localization_candidates,
        (SpectrumPeak(mz=50.0, intensity=80.0),),
    )
    rendered = ptm.render_false_localization_tsv(rows)

    assert hasattr(ptm, "detect_false_localization")
    assert hasattr(ptm, "render_false_localization_tsv")
    assert any(row.localization_risk.value == "ambiguous" for row in rows)
    assert "competing_site" in rendered


def test_ptm_package_exports_site_quantification_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    report = ptm.build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )

    assert hasattr(ptm, "build_ptm_site_quantification_report")
    assert hasattr(ptm, "render_ptm_site_quant_matrix_tsv")
    assert report.summary.site_row_count == 3
    assert report.summary.ambiguous_group_row_count == 2
    assert report.ambiguous_group_quantification is not None


def test_ptm_package_exports_occupancy_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    report = ptm.build_ptm_site_occupancy_report(
        site_table,
        feature_records=features.accepted_records,
    )

    assert hasattr(ptm, "build_ptm_site_occupancy_report")
    assert hasattr(ptm, "PtmOccupancyConfidenceTier")
    target = next(
        entry
        for entry in report.entries
        if entry.site_key == "P11111:S5:Phospho" and entry.sample_id == "C1"
    )
    assert target.confidence_tier.value == "high_confidence"
    assert target.unmodified_feature_count == 1


def test_ptm_package_exports_occupancy_contrast_surface() -> None:
    report = ptm.test_occupancy_contrast(
        _occupancy_matrix(
            {
                "P11111:S5:Phospho": {
                    "ctrl-1": 10.0,
                    "ctrl-2": 12.0,
                    "case-1": 80.0,
                    "case-2": 84.0,
                },
                "P22222:Y18:Phospho": {
                    "ctrl-1": 20.0,
                    "ctrl-2": 25.0,
                    "case-1": 35.0,
                    "case-2": 40.0,
                },
            }
        ),
        _occupancy_matrix(
            {
                "P11111:S5:Phospho": {
                    "ctrl-1": 90.0,
                    "ctrl-2": 88.0,
                    "case-1": 20.0,
                    "case-2": 16.0,
                },
            }
        ),
        _occupancy_design(),
    )
    rendered = ptm.render_ptm_occupancy_contrast_tsv(report)

    assert hasattr(ptm, "test_occupancy_contrast")
    assert hasattr(ptm, "render_ptm_occupancy_contrast_tsv")
    high_confidence = next(
        entry for entry in report.entries if entry.site_id == "P11111:S5:Phospho"
    )
    missing_unmodified = next(
        entry for entry in report.entries if entry.site_id == "P22222:Y18:Phospho"
    )
    assert high_confidence.occupancy_delta == 0.71
    assert high_confidence.confidence_tier.value == "high_confidence"
    assert missing_unmodified.confidence_tier.value == "missing_unmodified_evidence"
    assert "confidence_tier" in rendered.splitlines()[0]


def test_ptm_package_exports_hotspot_owner_surface() -> None:
    entries = ptm.detect_ptm_hotspots(
        (
            ptm.PtmHotspotSiteResult(
                site_id="P11111:S5:Phospho",
                protein_id="P11111",
                position=5,
                signed_effect=1.8,
            ),
            ptm.PtmHotspotSiteResult(
                site_id="P11111:T8:Phospho",
                protein_id="P11111",
                position=8,
                signed_effect=1.4,
            ),
            ptm.PtmHotspotSiteResult(
                site_id="P11111:Y30:Phospho",
                protein_id="P11111",
                position=30,
                signed_effect=1.6,
            ),
        ),
        protein_length=120,
        max_distance=3,
    )
    rendered = ptm.render_ptm_hotspots_tsv(entries)

    assert hasattr(ptm, "detect_ptm_hotspots")
    assert hasattr(ptm, "render_ptm_hotspots_tsv")
    assert len(entries) == 1
    assert entries[0].cluster_start == 5
    assert entries[0].cluster_end == 8
    assert "direction_consistency" in rendered.splitlines()[0]


def test_ptm_package_exports_motif_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    site_quantification = ptm.build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = parse_experimental_design_table(_ptm_fixture("ptm.design.tsv"))
    differential = ptm.build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        batch_field="",
    )
    report = ptm.build_ptm_phosphosite_motif_enrichment_report(
        differential,
        protein_sequences=_protein_sequences(),
        flank_size=3,
        selection_policy=ptm.PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.5,
            direction=ptm.PtmMotifRegulationDirection.UPREGULATED,
        ),
        comparison_policy=ptm.PtmMotifComparisonPolicy(
            background_mode=ptm.PtmMotifBackgroundMode.WHOLE_PROTEOME_BACKGROUND,
        ),
    )

    assert hasattr(ptm, "build_ptm_phosphosite_motif_enrichment_report")
    assert hasattr(ptm, "PtmMotifBackgroundMode")
    assert report.background_mode is ptm.PtmMotifBackgroundMode.WHOLE_PROTEOME_BACKGROUND
    assert report.background_site_count > report.regulated_site_count


def test_ptm_package_exports_differential_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    site_quantification = ptm.build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = parse_experimental_design_table(_ptm_fixture("ptm.design.tsv"))
    report = ptm.build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        batch_field="",
    )

    assert hasattr(ptm, "build_ptm_differential_analysis_report")
    assert hasattr(ptm, "render_ptm_site_differential_tsv")
    corrected = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "P11111:S5:Phospho"
    )
    low_localization = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "Q9DEC1:S5:Phospho"
    )
    assert corrected.protein_correction_status == "not_requested"
    assert low_localization.localization_tier.value == "refused"
    assert low_localization.low_localization is True


def test_ptm_package_exports_regulator_enrichment_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    site_quantification = ptm.build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = parse_experimental_design_table(_ptm_fixture("ptm.design.tsv"))
    differential = ptm.build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        batch_field="",
    )
    annotations = ptm.parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
    mapping_report = ptm.build_ptm_site_annotation_mapping_report(
        site_table,
        annotations.accepted_records,
        target_species="Homo sapiens",
    )
    report = ptm.build_ptm_regulator_enrichment_report(
        differential.differential_report,
        mapping_report,
        policy=ptm.PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.5,
        ),
    )

    assert hasattr(ptm, "build_ptm_regulator_enrichment_report")
    assert hasattr(ptm, "render_ptm_regulator_enrichment_tsv")
    assert any(entry.regulator == "AKT1" for entry in report.entries)
    assert "supporting_sites" in ptm.render_ptm_regulator_enrichment_tsv(report)


def test_ptm_package_exports_context_annotation_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    context = ptm.parse_ptm_site_context_tsv(_ptm_fixture("ptm_site_context.tsv"))
    report = ptm.build_ptm_site_context_report(site_table, context.accepted_records)

    assert hasattr(ptm, "build_ptm_site_context_report")
    assert hasattr(ptm, "render_ptm_site_context_tsv")
    outside = next(
        entry for entry in report.entries if entry.site_key == "Q9DEC1:S5:Phospho"
    )
    assert outside.context_status.value == "outside_provided_annotations"
    assert "context_status" in ptm.render_ptm_site_context_tsv(report)


def test_ptm_package_exports_crosstalk_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    site_quantification = ptm.build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = parse_experimental_design_table(_ptm_fixture("ptm.design.tsv"))
    differential = ptm.build_ptm_differential_analysis_report(
        site_quantification,
        tuple(entry.model_copy(update={"batch": None}) for entry in design.accepted_entries),
        batch_field="",
    )
    annotations = ptm.parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
    annotation_mapping = ptm.build_ptm_site_annotation_mapping_report(
        site_table,
        annotations.accepted_records,
        target_species="Homo sapiens",
    )
    report = ptm.build_ptm_crosstalk_report(
        site_table,
        differential.differential_report,
        annotation_mapping_report=annotation_mapping,
    )

    assert hasattr(ptm, "build_ptm_crosstalk_report")
    assert hasattr(ptm, "render_ptm_crosstalk_pair_tsv")
    assert report.summary.differential_site_count == 3
    assert "pair_key" in ptm.render_ptm_crosstalk_pair_tsv(report)


def test_ptm_package_exports_ortholog_site_conservation_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    ortholog_sites = ptm.parse_ptm_ortholog_site_tsv(_ptm_fixture("ptm_ortholog_sites.tsv"))
    report = ptm.build_ptm_ortholog_conservation_report(
        site_table,
        ortholog_sites.accepted_records,
        source_species="Homo sapiens",
        target_species="Mus musculus",
    )

    assert hasattr(ptm, "build_ptm_ortholog_conservation_report")
    assert hasattr(ptm, "render_ptm_ortholog_conservation_tsv")
    assert report.summary.unmapped_site_count == 2
    assert "status" in ptm.render_ptm_ortholog_conservation_tsv(report)


def test_ptm_package_exports_mechanism_classification_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = ptm.map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = ptm.build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    site_quantification = ptm.build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )
    design = tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _ptm_fixture("ptm.design.tsv")
        ).accepted_entries
    )
    differential = ptm.build_ptm_differential_analysis_report(
        site_quantification,
        design,
        batch_field="",
        feature_records=features.accepted_records,
        protein_correction_mode=ptm.PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
    )
    report = ptm.build_ptm_mechanism_classification_report(differential)

    assert hasattr(ptm, "build_ptm_mechanism_classification_report")
    assert hasattr(ptm, "render_ptm_mechanism_classification_tsv")
    assert report.summary.site_specific_count == 1
    assert "corrected_log2_fold_change" in ptm.render_ptm_mechanism_classification_tsv(report)


def test_ptm_package_exports_evidence_card_owner_surface() -> None:
    evidence = ptm.parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    features = parse_ms1_feature_table(_ptm_fixture("ptm_features.tsv"))
    design = parse_experimental_design_table(_ptm_fixture("ptm.design.tsv"))
    annotations = ptm.parse_ptm_site_annotation_tsv(_ptm_fixture("ptm_site_annotations.tsv"))
    ortholog_sites = ptm.parse_ptm_ortholog_site_tsv(_ptm_fixture("ptm_ortholog_sites.tsv"))
    report = ptm.build_ptm_report_bundle(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
        feature_records=features.accepted_records,
        design_entries=tuple(
            entry.model_copy(update={"batch": None}) for entry in design.accepted_entries
        ),
        batch_field="",
        motif_selection_policy=ptm.PtmPhosphositeSelectionPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        annotation_records=annotations.accepted_records,
        annotation_target_species="Homo sapiens",
        regulator_enrichment_policy=ptm.PtmRegulatorEnrichmentPolicy(
            max_adjusted_p_value=1.0,
            min_absolute_log2_fold_change=0.0,
        ),
        ortholog_site_records=ortholog_sites.accepted_records,
        ortholog_source_species="Homo sapiens",
        ortholog_target_species="Mus musculus",
        evidence_card_policy=ptm.PtmEvidenceCardPolicy(max_adjusted_p_value=1.0),
    )

    assert hasattr(ptm, "build_ptm_evidence_card_report")
    assert hasattr(ptm, "render_ptm_evidence_card_tsv")
    assert report.evidence_cards is not None
    assert report.evidence_aware_ranking_report is not None
    assert report.evidence_cards.summary.card_count == 3
    assert report.evidence_cards.summary.mechanism_classified_card_count == 3
    assert report.evidence_cards.summary.ortholog_context_card_count == 3
    assert "card_id" in ptm.render_ptm_evidence_card_tsv(report.evidence_cards)
    assert report.evidence_aware_ranking_report.summary.ptm_site_entry_count == 3


def _occupancy_matrix(
    site_values: dict[str, dict[str, float | None]],
) -> LabelFreeQuantTable:
    sample_ids = tuple(
        sorted({sample_id for values in site_values.values() for sample_id in values})
    )
    entity_ids = tuple(sorted(site_values))
    values: list[QuantValue] = []
    for entity_id in entity_ids:
        row = site_values[entity_id]
        for sample_id in sample_ids:
            abundance = row.get(sample_id)
            values.append(
                QuantValue(
                    sample_id=sample_id,
                    entity_id=entity_id,
                    abundance=abundance,
                    missing_value_kind=(
                        MissingValueKind.OBSERVED
                        if abundance is not None
                        else MissingValueKind.NOT_OBSERVED
                    ),
                    source_feature_count=0 if abundance is None else 1,
                )
            )
    return LabelFreeQuantTable(
        entity_level=QuantEntityLevel.PEPTIDE,
        measure_kind=QuantMeasureKind.INTENSITY,
        aggregation_method=QuantRollupMethod.SUM,
        sample_ids=sample_ids,
        entity_ids=entity_ids,
        values=tuple(values),
    )


def _occupancy_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.raw",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.raw",
        ),
    )
