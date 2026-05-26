# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.interpretation.pathway_activity import build_pathway_activity_report
from bijux_proteomics.interpretation.pathway_enrichment import parse_pathway_membership_table
from bijux_proteomics.interpretation.protein_annotation_mapping import (
    ProteinReferenceEntry,
    build_protein_annotation_mapping_report,
)
from bijux_proteomics.interpretation.regulator_inference import (
    RegulatorEvidenceType,
    RegulatorInferencePolicy,
    RegulatorEvidenceRecord,
    RegulatorSignalSurface,
    build_regulator_inference_report,
    parse_regulator_evidence_table,
    parse_regulator_site_signal_table,
    render_regulator_inference_tsv,
    render_unresolved_regulator_target_tsv,
)
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


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _build_fixture_table():
    parse_report = parse_ms1_feature_table(
        _fixture("biological_report_features.tsv"),
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
        aggregation_method=QuantRollupMethod.SUM,
    )
    return normalize_label_free_table(
        protein_table,
        method=NormalizationMethod.MEDIAN,
    )


def _build_annotation_report(differential_report):
    fasta_report = parse_fasta_document(
        _fixture("biological_report_reference.fasta").read_text(encoding="utf-8"),
        mode=FastaParseMode.STRICT,
    )
    reference_entries = tuple(
        ProteinReferenceEntry(
            row_number=index + 2,
            source_row_id=entry.entity_id,
            input_protein_ref=entry.entity_id,
            protein_ref=entry.entity_id,
        )
        for index, entry in enumerate(differential_report.entries)
    )
    return build_protein_annotation_mapping_report(
        reference_entries,
        fasta_report.accepted_records,
    )


def test_build_regulator_inference_report_separates_site_and_abundance_support() -> None:
    design_entries = tuple(
        parse_experimental_design_table(_fixture("biological_report.design.tsv")).accepted_entries
    )
    protein_table = _build_fixture_table()
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            protein_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    annotation_report = _build_annotation_report(differential_report)
    pathway_report = build_pathway_activity_report(
        protein_table,
        parse_pathway_membership_table(_fixture("biological_report_pathways.tsv")).accepted_records,
        design_entries=design_entries,
        fasta_records=parse_fasta_document(
            _fixture("biological_report_reference.fasta").read_text(encoding="utf-8"),
            mode=FastaParseMode.STRICT,
        ).accepted_records,
    )
    evidence_import = parse_regulator_evidence_table(
        _fixture("biological_report_regulator_evidence.tsv")
    )
    site_signal_import = parse_regulator_site_signal_table(
        _fixture("biological_report_regulator_sites.tsv")
    )

    report = build_regulator_inference_report(
        evidence_import.accepted_records,
        differential_report,
        annotation_report=annotation_report,
        pathway_activity_report=pathway_report,
        site_signal_entries=site_signal_import.accepted_entries,
    )

    assert report.summary.entry_count == 5
    assert report.summary.site_regulation_entry_count == 1
    assert report.summary.protein_abundance_entry_count == 3
    assert report.summary.pathway_activity_entry_count == 1
    assert report.summary.unresolved_target_count == 1
    by_regulator = {entry.regulator: entry for entry in report.entries}
    kinase_entry = by_regulator["MAPK14"]
    assert kinase_entry.evidence_type is RegulatorEvidenceType.KINASE_SUBSTRATE
    assert kinase_entry.signal_surface is RegulatorSignalSurface.SITE_REGULATION
    assert kinase_entry.supporting_site_keys == ("P04637:S15:Phospho",)
    assert kinase_entry.supporting_protein_refs == ("P04637",)
    assert kinase_entry.direction.value == "up"
    assert kinase_entry.score > 0.7
    tf_entry = by_regulator["STAT3"]
    assert tf_entry.signal_surface is RegulatorSignalSurface.PROTEIN_ABUNDANCE
    assert tf_entry.supporting_protein_refs == ("O14920", "P04637")
    assert tf_entry.direction.value == "up"
    ppi_entry = by_regulator["GRB2"]
    assert ppi_entry.direction.value == "down"
    pathway_entry = by_regulator["Stress commander"]
    assert pathway_entry.signal_surface is RegulatorSignalSurface.PATHWAY_ACTIVITY
    assert pathway_entry.supporting_pathway_ids == ("custom:response",)
    assert pathway_entry.supporting_protein_refs == ("O14920", "P04637", "Q9Y243")
    assert pathway_entry.mean_activity_score_delta is not None
    orphan_entry = by_regulator["OrphanTF"]
    assert orphan_entry.direction.value == "unsupported"
    assert orphan_entry.score == 0.0
    assert report.unresolved_targets[0].target_value == "UNSEEN"


def test_regulator_inference_renderers_expose_supporting_targets_and_unresolved_rows() -> None:
    design_entries = tuple(
        parse_experimental_design_table(_fixture("biological_report.design.tsv")).accepted_entries
    )
    protein_table = _build_fixture_table()
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            protein_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    annotation_report = _build_annotation_report(differential_report)
    pathway_report = build_pathway_activity_report(
        protein_table,
        parse_pathway_membership_table(_fixture("biological_report_pathways.tsv")).accepted_records,
        design_entries=design_entries,
    )
    report = build_regulator_inference_report(
        parse_regulator_evidence_table(
            _fixture("biological_report_regulator_evidence.tsv")
        ).accepted_records,
        differential_report,
        annotation_report=annotation_report,
        pathway_activity_report=pathway_report,
        site_signal_entries=parse_regulator_site_signal_table(
            _fixture("biological_report_regulator_sites.tsv")
        ).accepted_entries,
    )

    inference_tsv = render_regulator_inference_tsv(report)
    unresolved_tsv = render_unresolved_regulator_target_tsv(report)

    assert inference_tsv.splitlines()[0].startswith(
        "regulator\tevidence_type\tsignal_surface\tsource_name"
    )
    assert "supporting_site_keys" in inference_tsv.splitlines()[0]
    assert "MAPK14\tkinase_substrate\tsite_regulation" in inference_tsv
    assert "STAT3\ttranscription_factor_target\tprotein_abundance" in inference_tsv
    assert "Stress commander\tpathway\tpathway_activity" in inference_tsv
    assert unresolved_tsv.splitlines()[0] == (
        "regulator\tevidence_type\ttarget_field\ttarget_value\tsource_name\t"
        "source_accession\treason"
    )
    assert "OrphanTF\ttranscription_factor_target\tgene_symbol\tUNSEEN" in unresolved_tsv


def test_build_regulator_inference_report_downgrades_low_target_coverage() -> None:
    design_entries = tuple(
        parse_experimental_design_table(_fixture("biological_report.design.tsv")).accepted_entries
    )
    protein_table = _build_fixture_table()
    differential_report = apply_benjamini_hochberg(
        build_differential_abundance_report(
            protein_table,
            design_entries,
            condition_a="control",
            condition_b="treatment",
        )
    )
    evidence_records = (
        RegulatorEvidenceRecord(
            regulator="SparseTF",
            evidence_type=RegulatorEvidenceType.TRANSCRIPTION_FACTOR_TARGET,
            protein_ref="P04637",
            source_name="custom",
            source_accession="TF-01",
        ),
        RegulatorEvidenceRecord(
            regulator="SparseTF",
            evidence_type=RegulatorEvidenceType.TRANSCRIPTION_FACTOR_TARGET,
            protein_ref="Q99999",
            source_name="custom",
            source_accession="TF-01",
        ),
    )

    permissive = build_regulator_inference_report(
        evidence_records,
        differential_report,
        policy=RegulatorInferencePolicy(
            minimum_target_coverage_fraction=0.5,
            low_coverage_score_cap=0.6,
        ),
    )
    strict = build_regulator_inference_report(
        evidence_records,
        differential_report,
        policy=RegulatorInferencePolicy(
            minimum_target_coverage_fraction=0.75,
            low_coverage_score_cap=0.4,
        ),
    )

    permissive_entry = permissive.entries[0]
    strict_entry = strict.entries[0]

    assert permissive_entry.coverage_fraction == 0.5
    assert strict_entry.coverage_fraction == 0.5
    assert permissive_entry.score > strict_entry.score
    assert strict_entry.score == 0.4
    assert strict_entry.note.endswith("target coverage 0.5 was below minimum 0.75")
