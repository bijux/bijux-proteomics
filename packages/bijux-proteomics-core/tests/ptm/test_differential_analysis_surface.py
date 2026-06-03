# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.ptm import (
    PtmSiteQuantificationReport,
    build_ptm_differential_analysis_report,
    build_ptm_site_quantification_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.quantification import (
    DifferentialImputationSignificanceChangeReason,
    NormalizationMethod,
    parse_ms1_feature_table,
)
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


def _site_quantification() -> PtmSiteQuantificationReport:
    evidence = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        evidence.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_table = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(_fixture_path("ptm_features.tsv"))
    return build_ptm_site_quantification_report(
        site_table,
        feature_records=features.accepted_records,
    )


def _analysis_design() -> tuple[ExperimentalDesignEntry, ...]:
    design = parse_experimental_design_table(_fixture_path("ptm.design.tsv"))
    return tuple(
        entry.model_copy(update={"batch": None}) for entry in design.accepted_entries
    )


def test_ptm_differential_analysis_reports_regulated_site_changes() -> None:
    site_quantification = _site_quantification()

    report = build_ptm_differential_analysis_report(
        site_quantification,
        _analysis_design(),
        normalization_method=NormalizationMethod.MEDIAN,
        condition_a="control",
        condition_b="treated",
        batch_field="",
    )

    assert report.design_matrix.sample_count == 4
    assert report.differential_report.condition_a == "control"
    assert report.differential_report.condition_b == "treated"
    target = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "P11111:S5:Phospho"
    )

    assert target.observations_a == 2
    assert target.observations_b == 2
    assert target.log2_fold_change > 0.0
    assert target.adjusted_p_value is not None
    assert target.no_impute_adjusted_p_value == target.adjusted_p_value
    assert target.imputed_adjusted_p_value is None
    assert target.imputation_significance_change_reason is (
        DifferentialImputationSignificanceChangeReason.NOT_IMPUTED
    )
    assert target.imputation_dependent_hit is False
    assert target.localization_tier.value == "supported"
    assert target.low_localization is False
    assert target.localized_peptides == ("S[Phospho]PEPTIDEK",)
    low_localization = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "Q9DEC1:S5:Phospho"
    )
    assert low_localization.localization_tier.value == "refused"
    assert low_localization.low_localization is True
    assert low_localization.uncertainty_note is not None
    assert "low-localization site" in low_localization.uncertainty_note
    volcano_target = next(
        point
        for point in report.volcano_plot.points
        if point.site_key == "P11111:S5:Phospho"
    )
    assert report.volcano_plot.condition_a == "control"
    assert report.volcano_plot.condition_b == "treated"
    assert volcano_target.raw_log2_fold_change == target.log2_fold_change
    assert volcano_target.plotted_log2_fold_change == target.log2_fold_change
    assert volcano_target.negative_log10_adjusted_p_value >= 0.0


def test_ptm_differential_analysis_supports_pairwise_site_testing() -> None:
    site_quantification = _site_quantification()
    paired_design = (
        _analysis_design()[0].model_copy(update={"pair_id": "pair-1"}),
        _analysis_design()[1].model_copy(update={"pair_id": "pair-2"}),
        _analysis_design()[2].model_copy(update={"pair_id": "pair-1"}),
        _analysis_design()[3].model_copy(update={"pair_id": "pair-2"}),
    )

    report = build_ptm_differential_analysis_report(
        site_quantification,
        paired_design,
        normalization_method=NormalizationMethod.MEDIAN,
        condition_a="control",
        condition_b="treated",
        batch_field="",
        pairing_field="pair_id",
    )

    target = next(
        entry
        for entry in report.differential_report.entries
        if entry.site_key == "P11111:S5:Phospho"
    )

    assert report.design_matrix.pairing_field == "pair_id"
    assert target.complete_pair_count == 2
    assert target.effect_size_cohens_d is not None
    assert report.differential_report.broken_pairs == ()
