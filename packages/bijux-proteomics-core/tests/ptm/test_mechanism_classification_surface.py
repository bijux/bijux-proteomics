# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmDifferentialAnalysisReport,
    PtmMechanismClass,
    PtmProteinCorrectionMode,
    build_ptm_differential_analysis_report,
    build_ptm_mechanism_classification_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    render_ptm_mechanism_classification_tsv,
)
from bijux_proteomics.quantification import NormalizationMethod, parse_ms1_feature_table
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


def _build_differential_analysis_report() -> PtmDifferentialAnalysisReport:
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
    design_entries = tuple(
        entry.model_copy(update={"batch": None})
        for entry in parse_experimental_design_table(
            _fixture_path("ptm.design.tsv")
        ).accepted_entries
    )
    return build_ptm_differential_analysis_report(
        site_quantification,
        design_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
        feature_records=features.accepted_records,
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
    )


def test_ptm_mechanism_classification_distinguishes_site_specific_ambiguous_and_unsupported() -> (
    None
):
    differential = _build_differential_analysis_report()

    report = build_ptm_mechanism_classification_report(differential)

    entries = {entry.site_key: entry for entry in report.entries}
    assert (
        entries["P11111:S5:Phospho"].mechanism_class is PtmMechanismClass.SITE_SPECIFIC
    )
    assert entries["P22222:Y18:Phospho"].mechanism_class is PtmMechanismClass.AMBIGUOUS
    assert entries["Q9DEC1:S5:Phospho"].mechanism_class is PtmMechanismClass.UNSUPPORTED
    assert report.summary.site_specific_count == 1
    assert report.summary.ambiguous_count == 1
    assert report.summary.unsupported_count == 1


def test_ptm_mechanism_classification_marks_abundance_driven_when_protein_explains_raw_effect() -> (
    None
):
    differential = _build_differential_analysis_report()
    target_entry = next(
        entry
        for entry in differential.differential_report.entries
        if entry.site_key == "P11111:S5:Phospho"
    )
    target_row = next(
        row
        for row in differential.site_quantification.rows
        if row.site_key == "P11111:S5:Phospho"
    )
    abundance_driven_entry = target_entry.model_copy(
        update={
            "log2_fold_change": 1.2,
            "protein_log2_fold_change": 1.05,
            "corrected_log2_fold_change": 0.1,
            "protein_adjusted_p_value": 0.01,
            "protein_correction_status": "high_confidence_corrected",
            "low_localization": False,
        }
    )
    synthetic = differential.model_copy(
        update={
            "differential_report": differential.differential_report.model_copy(
                update={"entries": (abundance_driven_entry,)}
            ),
            "site_quantification": differential.site_quantification.model_copy(
                update={"rows": (target_row,)}
            ),
        }
    )

    report = build_ptm_mechanism_classification_report(synthetic)

    assert report.summary.abundance_driven_count == 1
    assert report.entries[0].mechanism_class is PtmMechanismClass.ABUNDANCE_DRIVEN
    assert "protein_tracks_raw_site_effect" in {
        reason.value for reason in report.entries[0].reason_codes
    }


def test_render_ptm_mechanism_classification_tsv_preserves_raw_and_corrected_effects() -> (
    None
):
    differential = _build_differential_analysis_report()

    report = build_ptm_mechanism_classification_report(differential)
    header = render_ptm_mechanism_classification_tsv(report).splitlines()[0]

    assert "raw_log2_fold_change" in header
    assert "corrected_log2_fold_change" in header
    assert "mechanism_class" in header
