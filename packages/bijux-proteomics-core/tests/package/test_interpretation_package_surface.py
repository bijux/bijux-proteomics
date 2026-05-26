# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics import interpretation
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.quantification import (
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    QuantEntityLevel,
    QuantRollupMethod,
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    normalize_label_free_table,
    parse_ms1_feature_table,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def _fasta_fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def _quant_fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "quant" / name


def _workflow_fixture_path(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _build_protein_fixture_table():
    parse_report = parse_ms1_feature_table(
        _quant_fixture_path("ms1_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
        ),
    )
    protein_table = build_label_free_intensity_table(
        parse_report.accepted_records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.TOP_N,
        top_n=2,
    )
    return normalize_label_free_table(
        protein_table,
        method=NormalizationMethod.MEDIAN,
    )


def test_interpretation_package_exports_complete_protein_annotation_surface() -> None:
    protein_table = interpretation.parse_protein_reference_table(
        _fixture_path("protein_annotation_input.tsv")
    )
    custom_table = interpretation.parse_protein_annotation_table(
        _fixture_path("protein_annotation_custom.tsv")
    )
    fasta_report = parse_fasta_document(
        _fasta_fixture_path("valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    mapping_report = interpretation.build_protein_annotation_mapping_report(
        protein_table.accepted_entries
        + (
            interpretation.ProteinReferenceEntry(
                row_number=99,
                source_row_id="row-missing",
                input_protein_ref="UNKNOWN123",
                protein_ref="UNKNOWN123",
            ),
        ),
        fasta_report.accepted_records,
        custom_annotations=custom_table.accepted_records
        + (
            interpretation.ProteinAnnotationRecord(
                protein_ref="Q99999",
                gene_symbol="CUST1",
            ),
        ),
    )

    assert hasattr(interpretation, "render_protein_annotation_tsv")
    rendered = interpretation.render_protein_annotation_tsv(mapping_report)

    assert "annotation_status" in rendered.splitlines()[0]
    assert "UNKNOWN123" in rendered
    assert "unmapped" in rendered


def test_interpretation_package_exports_protein_set_enrichment_surface() -> None:
    foreground = interpretation.parse_protein_reference_table(
        _fixture_path("protein_set_enrichment_foreground.tsv")
    )
    protein_sets = interpretation.parse_protein_set_table(
        _fixture_path("protein_set_enrichment.tsv")
    )
    report = interpretation.build_protein_set_enrichment_report(
        foreground.accepted_entries,
        protein_sets.accepted_records,
        policy=interpretation.ProteinSetEnrichmentPolicy(
            missing_background_policy=(
                interpretation.ProteinSetEnrichmentMissingBackgroundPolicy.MEMBERSHIP_UNIVERSE
            ),
            max_adjusted_p_value=1.0,
            min_enrichment_ratio=0.0,
        ),
    )

    assert hasattr(interpretation, "render_protein_set_enrichment_tsv")
    rendered = interpretation.render_protein_set_enrichment_tsv(report)

    assert "set_category" in rendered.splitlines()[0]
    assert "nucleus" in rendered


def test_interpretation_package_exports_protein_set_scoring_surface() -> None:
    design_report = parse_experimental_design_table(_quant_fixture_path("quant.design.tsv"))
    protein_sets = interpretation.parse_protein_set_table(_fixture_path("protein_sets.tsv"))
    report = interpretation.build_protein_set_scoring_report(
        _build_protein_fixture_table(),
        protein_sets.accepted_records,
        design_entries=design_report.accepted_entries,
    )

    assert hasattr(interpretation, "render_protein_set_sample_score_tsv")
    rendered = interpretation.render_protein_set_sample_score_tsv(report)

    assert "confidence_status" in rendered.splitlines()[0]
    assert "low" in rendered


def test_interpretation_package_exports_ppi_network_module_surface() -> None:
    significant = interpretation.parse_protein_reference_table(
        _fixture_path("ppi_significant.tsv")
    )
    edges = interpretation.parse_ppi_edge_table(_fixture_path("ppi_edges.tsv"))
    protein_sets = interpretation.parse_protein_set_table(
        _fixture_path("protein_set_enrichment.tsv")
    )
    report = interpretation.build_ppi_network_module_report(
        significant.accepted_entries,
        edges.accepted_records,
        protein_set_records=protein_sets.accepted_records,
    )

    assert hasattr(interpretation, "render_ppi_module_tsv")
    rendered = interpretation.render_ppi_module_tsv(report)

    assert "module_id" in rendered.splitlines()[0]
    assert "ppi_module:P001,P002,P003" in rendered


def test_interpretation_package_exports_biological_context_mapping_surface() -> None:
    protein_table = interpretation.parse_protein_reference_table(
        _fixture_path("biological_context_input.tsv")
    )
    context_table = interpretation.parse_biological_context_table(
        _fixture_path("biological_context_annotations.tsv")
    )
    report = interpretation.build_biological_context_mapping_report(
        protein_table.accepted_entries,
        context_table.accepted_records,
    )

    assert hasattr(interpretation, "render_biological_context_term_tsv")
    rendered = interpretation.render_biological_context_term_tsv(report)

    assert "supporting_protein_refs" in rendered.splitlines()[0]
    assert "P04637" in rendered


def test_interpretation_package_exports_foreground_background_model_surface() -> None:
    model = interpretation.build_biological_foreground_background_model(
        (
            interpretation.ProteinReferenceEntry(
                row_number=2,
                source_row_id="foreground:1",
                input_protein_ref="P04637",
                protein_ref="P04637",
            ),
        ),
        (
            interpretation.ProteinReferenceEntry(
                row_number=2,
                source_row_id="background:1",
                input_protein_ref="P04637",
                protein_ref="P04637",
            ),
            interpretation.ProteinReferenceEntry(
                row_number=3,
                source_row_id="background:2",
                input_protein_ref="Q9Y243",
                protein_ref="Q9Y243",
            ),
        ),
        foreground_source_kind=(
            interpretation.BiologicalSetSourceKind.DIFFERENTIAL_SIGNIFICANT_RESULTS
        ),
        background_source_kind=interpretation.BiologicalSetSourceKind.MEASURED_QUANT_MATRIX,
        foreground_policy=interpretation.BiologicalSetFilteringPolicy(
            policy_name="significant proteins",
            max_adjusted_p_value=0.1,
            min_absolute_log2_fold_change=1.0,
            note="foreground keeps significant proteins from the contrast",
        ),
        background_policy=interpretation.BiologicalSetFilteringPolicy(
            policy_name="measured matrix",
            note="background keeps all measured proteins",
        ),
    )

    assert hasattr(interpretation, "build_biological_foreground_background_model")
    assert hasattr(interpretation, "render_biological_foreground_background_summary_tsv")
    assert model.summary.valid_for_enrichment is True
    assert "foreground_source_kind" in (
        interpretation.render_biological_foreground_background_summary_tsv(model)
    )


def test_interpretation_package_exports_pathway_activity_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture_path("biological_report.design.tsv")
        ).accepted_entries
    )
    parse_report = parse_ms1_feature_table(
        _workflow_fixture_path("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
        ),
    )
    protein_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    pathway_records = interpretation.parse_pathway_membership_table(
        _workflow_fixture_path("biological_report_pathways.tsv")
    )
    report = interpretation.build_pathway_activity_report(
        protein_table,
        pathway_records.accepted_records,
        design_entries=design_entries,
    )

    assert hasattr(interpretation, "build_pathway_activity_report")
    assert hasattr(interpretation, "PathwayActivityPolicy")
    assert hasattr(interpretation, "render_pathway_activity_matrix_tsv")
    assert report.summary.pathway_count == 1
    assert "pathway_id" in interpretation.render_pathway_activity_matrix_tsv(report)


def test_interpretation_package_exports_tissue_cell_type_context_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture_path("biological_report_tissue_context.design.tsv")
        ).accepted_entries
    )
    context_import = interpretation.parse_biological_context_table(
        _workflow_fixture_path("biological_report_tissue_markers.tsv")
    )
    parse_report = parse_ms1_feature_table(
        _workflow_fixture_path("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
        ),
    )
    protein_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    report = interpretation.build_tissue_cell_type_context_report(
        protein_table,
        design_entries,
        context_import.accepted_records,
    )

    assert hasattr(interpretation, "build_tissue_cell_type_context_report")
    assert hasattr(interpretation, "render_tissue_cell_type_sample_consistency_tsv")
    rendered = interpretation.render_tissue_cell_type_sample_consistency_tsv(report)

    assert "warning_code" in rendered.splitlines()[0]
    assert "unexpected_marker_context_dominates" in rendered


def test_interpretation_package_exports_complex_activity_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture_path("biological_report.design.tsv")
        ).accepted_entries
    )
    parse_report = parse_ms1_feature_table(
        _workflow_fixture_path("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
        ),
    )
    protein_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    complex_records = interpretation.parse_complex_membership_table(
        _workflow_fixture_path("biological_report_complexes.tsv")
    )
    report = interpretation.build_complex_activity_report(
        protein_table,
        complex_records.accepted_records,
        design_entries=design_entries,
    )

    assert hasattr(interpretation, "build_complex_activity_report")
    assert hasattr(interpretation, "render_complex_activity_matrix_tsv")
    assert report.summary.complex_count == 1
    assert "complex_id" in interpretation.render_complex_activity_matrix_tsv(report)


def test_interpretation_package_exports_compartment_biology_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture_path("biological_report.design.tsv")
        ).accepted_entries
    )
    parse_report = parse_ms1_feature_table(
        _workflow_fixture_path("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
        ),
    )
    protein_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    context_report = interpretation.parse_biological_context_table(
        _workflow_fixture_path("biological_report_compartments.tsv")
    )
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            protein_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    report = interpretation.build_compartment_biology_report(
        protein_table,
        differential_report,
        context_report.accepted_records,
        design_entries=design_entries,
        policy=interpretation.CompartmentBiologyPolicy(max_adjusted_p_value=1.0),
    )

    assert hasattr(interpretation, "build_compartment_biology_report")
    assert hasattr(interpretation, "render_compartment_enrichment_tsv")
    assert report.summary.compartment_count == 2
    assert "compartment_id" in interpretation.render_compartment_enrichment_tsv(report)


def test_interpretation_package_exports_disease_phenotype_interpretation_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture_path("biological_report.design.tsv")
        ).accepted_entries
    )
    parse_report = parse_ms1_feature_table(
        _workflow_fixture_path("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
        ),
    )
    protein_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    context_report = interpretation.parse_biological_context_table(
        _workflow_fixture_path("biological_report_disease_phenotype.tsv")
    )
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            protein_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    report = interpretation.build_disease_phenotype_interpretation_report(
        protein_table,
        differential_report,
        context_report.accepted_records,
        policy=interpretation.DiseasePhenotypeInterpretationPolicy(
            max_adjusted_p_value=1.0,
        ),
    )

    assert hasattr(interpretation, "build_disease_phenotype_interpretation_report")
    assert hasattr(interpretation, "render_disease_phenotype_interpretation_tsv")
    assert report.summary.term_count == 4
    assert "context_kind" in interpretation.render_disease_phenotype_interpretation_tsv(
        report
    )


def test_interpretation_package_exports_drug_target_interpretation_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture_path("biological_report.design.tsv")
        ).accepted_entries
    )
    parse_report = parse_ms1_feature_table(
        _workflow_fixture_path("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
        ),
    )
    protein_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    context_report = interpretation.parse_biological_context_table(
        _workflow_fixture_path("biological_report_drug_targets.tsv")
    )
    pathway_report = interpretation.parse_pathway_membership_table(
        _workflow_fixture_path("biological_report_pathways.tsv")
    )
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            protein_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    annotation_report = interpretation.build_protein_annotation_mapping_report(
        tuple(
            interpretation.ProteinReferenceEntry(
                row_number=index + 2,
                source_row_id=entry.entity_id,
                input_protein_ref=protein_ref,
                protein_ref=protein_ref,
            )
            for index, entry in enumerate(differential_report.entries)
            for protein_ref in protein_table.entity_protein_refs.get(
                entry.entity_id, (entry.entity_id,)
            )
        ),
        parse_fasta_document(
            _workflow_fixture_path("biological_report_reference.fasta").read_text(),
            mode=FastaParseMode.STRICT,
        ).accepted_records,
    )
    report = interpretation.build_drug_target_interpretation_report(
        protein_table,
        differential_report,
        context_report.accepted_records,
        pathway_records=pathway_report.accepted_records,
        annotation_report=annotation_report,
        policy=interpretation.DrugTargetInterpretationPolicy(max_adjusted_p_value=1.0),
    )

    assert hasattr(interpretation, "build_drug_target_interpretation_report")
    assert hasattr(interpretation, "render_drug_target_interpretation_tsv")
    assert report.summary.direct_target_entry_count == 1
    assert "relationship" in interpretation.render_drug_target_interpretation_tsv(report)


def test_interpretation_package_exports_regulator_inference_surface() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _workflow_fixture_path("biological_report.design.tsv")
        ).accepted_entries
    )
    parse_report = parse_ms1_feature_table(
        _workflow_fixture_path("biological_report_features.tsv"),
        mapping=Ms1FeatureColumnMapping(
            sample_id="sample_id",
            feature_id="feature_id",
            peptide="peptide",
            intensity="intensity",
            protein_refs="proteins",
            charge="charge",
            mz="mz",
            retention_time_seconds="retention_time_seconds",
            missing_reason="missing_reason",
        ),
    )
    protein_table = normalize_label_free_table(
        build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel.PROTEIN,
            aggregation_method=QuantRollupMethod.SUM,
        ),
        method=NormalizationMethod.MEDIAN,
    )
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            protein_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    annotation_report = interpretation.build_protein_annotation_mapping_report(
        tuple(
            interpretation.ProteinReferenceEntry(
                row_number=index + 2,
                source_row_id=entry.entity_id,
                input_protein_ref=entry.entity_id,
                protein_ref=entry.entity_id,
            )
            for index, entry in enumerate(differential_report.entries)
        ),
        parse_fasta_document(
            _workflow_fixture_path("biological_report_reference.fasta").read_text(),
            mode=FastaParseMode.STRICT,
        ).accepted_records,
    )
    pathway_report = interpretation.build_pathway_activity_report(
        protein_table,
        interpretation.parse_pathway_membership_table(
            _workflow_fixture_path("biological_report_pathways.tsv")
        ).accepted_records,
        design_entries=design_entries,
    )
    report = interpretation.build_regulator_inference_report(
        interpretation.parse_regulator_evidence_table(
            _workflow_fixture_path("biological_report_regulator_evidence.tsv")
        ).accepted_records,
        differential_report,
        annotation_report=annotation_report,
        pathway_activity_report=pathway_report,
        site_signal_entries=interpretation.parse_regulator_site_signal_table(
            _workflow_fixture_path("biological_report_regulator_sites.tsv")
        ).accepted_entries,
    )

    assert hasattr(interpretation, "build_regulator_inference_report")
    assert hasattr(interpretation, "RegulatorInferencePolicy")
    assert hasattr(interpretation, "render_regulator_inference_tsv")
    rendered = interpretation.render_regulator_inference_tsv(report)
    assert "signal_surface" in rendered.splitlines()[0]
    assert "MAPK14\tkinase_substrate\tsite_regulation" in rendered


def test_interpretation_package_exports_annotation_pack_surface(tmp_path: Path) -> None:
    pack_path = tmp_path / "annotation_pack.json"
    pack_path.write_text(
        json.dumps(
            {
                "pack_name": "public-annotations",
                "protein_features": [
                    {
                        "protein_ref": "sp|P04637|P53_HUMAN",
                        "gene_symbol": "TP53",
                    }
                ],
                "pathways": [
                    {
                        "pathway_id": "pathway:stress_response",
                        "protein_ref": "P04637",
                    }
                ],
                "orthologs": [
                    {
                        "source_species": "human",
                        "source_protein_ref": "P04637",
                        "target_species": "mouse",
                        "target_protein_ref": "P02340",
                    }
                ],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    assert hasattr(interpretation, "load_annotation_pack")
    assert hasattr(interpretation, "render_annotation_pack_json")
    assert hasattr(interpretation, "AnnotationPackValidationError")

    pack = interpretation.load_annotation_pack(pack_path)
    exported = interpretation.render_annotation_pack_json(pack)

    assert pack.pack_name == "public-annotations"
    assert pack.protein_features[0].protein_ref == "P04637"
    assert pack.pathways[0].member_id == "P04637"
    assert pack.orthologs[0].target_protein_ref == "P02340"
    assert '"pack_name": "public-annotations"' in exported
