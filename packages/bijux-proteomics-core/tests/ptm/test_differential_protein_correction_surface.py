# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.ptm import (
    PtmProteinCorrectionMode,
    build_ptm_differential_analysis_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
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


def test_ptm_differential_analysis_can_apply_unmodified_protein_correction() -> None:
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

    report = build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
        feature_records=features.accepted_records,
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
    )

    target = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "P11111:S5:Phospho"
    )

    assert (
        report.protein_correction_mode
        is PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN
    )
    assert target.protein_correction_status == "high_confidence_corrected"
    assert target.protein_log2_fold_change is not None
    assert target.corrected_log2_fold_change is not None
    assert target.corrected_log2_fold_change > target.log2_fold_change
    unresolved = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "P22222:Y18:Phospho"
    )
    assert unresolved.protein_correction_status == "missing_protein_baseline"
    assert unresolved.corrected_log2_fold_change is None


def test_ptm_differential_analysis_marks_low_localization_correction_as_review_only() -> (
    None
):
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_fixture_path("ptm_features.tsv"))
    baseline_template_records = tuple(
        record
        for record in features.accepted_records
        if record.protein_refs == ("P11111",) and record.peptide == "SPEPTIDEK"
    )
    correction_ready_features = features.accepted_records + tuple(
        record.model_copy(
            update={
                "feature_id": f"{record.feature_id}.q9-baseline",
                "protein_refs": ("Q9DEC1",),
            }
        )
        for record in baseline_template_records
    )
    site_quantification = build_ptm_site_quantification_report(
        site_table,
        feature_records=correction_ready_features,
    )
    design = parse_experimental_design_table(_fixture_path("ptm.design.tsv"))

    report = build_ptm_differential_analysis_report(
        site_quantification,
        design.accepted_entries,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
        feature_records=correction_ready_features,
        protein_correction_mode=PtmProteinCorrectionMode.SUBTRACT_UNMODIFIED_PROTEIN,
    )

    low_localization = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "Q9DEC1:S5:Phospho"
    )

    assert low_localization.localization_tier.value == "refused"
    assert low_localization.protein_correction_status == "corrected_low_localization"
    assert low_localization.protein_log2_fold_change is not None
    assert low_localization.corrected_log2_fold_change is not None


def test_ptm_differential_analysis_blocks_broken_pairs_before_statistics() -> None:
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
    paired_design = tuple(
        entry.model_copy(
            update={
                "pair_id": (
                    f"pair-{entry.replicate}" if entry.sample_id != "T2" else None
                )
            }
        )
        for entry in design.accepted_entries
    )

    try:
        build_ptm_differential_analysis_report(
            site_quantification,
            paired_design,
            normalization_method=NormalizationMethod.MEDIAN,
            batch_field="",
            pairing_field="pair_id",
            feature_records=features.accepted_records,
        )
    except ValueError as exc:
        assert "broken_pair" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected broken PTM pairs to be rejected")


def test_ptm_differential_analysis_uses_paired_test_for_paired_designs() -> None:
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
    paired_design = tuple(
        entry.model_copy(update={"pair_id": f"pair-{entry.replicate}"})
        for entry in design.accepted_entries
    )

    report = build_ptm_differential_analysis_report(
        site_quantification,
        paired_design,
        normalization_method=NormalizationMethod.MEDIAN,
        batch_field="",
        feature_records=features.accepted_records,
    )

    assert report.differential_report.test_type.value == "paired_t_test"
