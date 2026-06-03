# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    DifferentialAbundanceTestType,
    LabelFreeQuantTable,
    MissingValueKind,
    Ms1FeatureRecord,
    PairedDifferentialPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    build_multi_condition_differential_abundance_report,
    export_differential_abundance_tsv,
    export_differential_broken_pairs_tsv,
    export_multi_condition_differential_abundance_tsv,
    render_differential_abundance_tsv,
    render_differential_broken_pairs_tsv,
    render_multi_condition_differential_abundance_tsv,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="tsv-001",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="tsv-002",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="tsv-003",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=400.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="tsv-004",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=420.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="tsv-005",
            sample_id="rescue-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=250.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="tsv-006",
            sample_id="rescue-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=255.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="rescue-1",
            condition="rescue",
            replicate=1,
            fraction=1,
            spectra_file="rescue-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="rescue-2",
            condition="rescue",
            replicate=2,
            fraction=1,
            spectra_file="rescue-2.mzml",
        ),
    )


def _table() -> LabelFreeQuantTable:
    return build_label_free_intensity_table(
        _records(),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def _paired_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="ctrl-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="ctrl-1.mzml",
            pair_id="pair-1",
        ),
        ExperimentalDesignEntry(
            sample_id="case-1",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="case-1.mzml",
            pair_id="pair-1",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="ctrl-2.mzml",
            pair_id="pair-2",
        ),
        ExperimentalDesignEntry(
            sample_id="case-2",
            condition="case",
            replicate=2,
            fraction=1,
            spectra_file="case-2.mzml",
            pair_id="pair-2",
        ),
        ExperimentalDesignEntry(
            sample_id="ctrl-3",
            condition="control",
            replicate=3,
            fraction=1,
            spectra_file="ctrl-3.mzml",
            pair_id="pair-3",
        ),
    )


def _paired_table() -> LabelFreeQuantTable:
    records = (
        Ms1FeatureRecord(
            feature_id="paired-tsv-001",
            sample_id="ctrl-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="paired-tsv-002",
            sample_id="case-1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=180.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="paired-tsv-003",
            sample_id="ctrl-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=110.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="paired-tsv-004",
            sample_id="case-2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=220.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="paired-tsv-005",
            sample_id="ctrl-3",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=95.0,
            protein_refs=("P001",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_render_differential_abundance_tsv_emits_adjusted_statistics() -> None:
    report = build_differential_abundance_report(
        _table(),
        _design(),
        condition_a="case",
        condition_b="control",
    )

    tsv = render_differential_abundance_tsv(report)

    assert "entity_id\tcondition_a\tcondition_b" in tsv
    assert "adjusted_p_value" in tsv
    assert "contrast_name" in tsv
    assert "zero_values_a" in tsv
    assert "robustness_score" in tsv
    assert "robustness_reason_codes" in tsv
    assert "no_impute_adjusted_p_value" in tsv
    assert "imputed_adjusted_p_value" in tsv
    assert "imputation_significance_change_reason" in tsv
    assert "imputation_dependent_hit" in tsv
    assert "P001\tcase\tcontrol" in tsv


def test_render_multi_condition_differential_abundance_tsv_flattens_contrasts() -> None:
    report = build_multi_condition_differential_abundance_report(_table(), _design())

    tsv = render_multi_condition_differential_abundance_tsv(report)

    assert "P001\tcase\tcontrol" in tsv
    assert "P001\tcase\trescue" in tsv
    assert "P001\tcontrol\trescue" in tsv


def test_export_differential_abundance_tsv_writes_table() -> None:
    report = build_differential_abundance_report(
        _table(),
        _design(),
        condition_a="case",
        condition_b="control",
    )
    path = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "quant"
        / "differential_abundance.tsv"
    )

    try:
        export_differential_abundance_tsv(report, path)
        assert "P001\tcase\tcontrol" in path.read_text(encoding="utf-8")
    finally:
        path.unlink(missing_ok=True)


def test_export_multi_condition_differential_abundance_tsv_writes_flattened_table() -> (
    None
):
    report = build_multi_condition_differential_abundance_report(_table(), _design())
    path = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "quant"
        / "multi_condition_differential_abundance.tsv"
    )

    try:
        export_multi_condition_differential_abundance_tsv(report, path)
        text = path.read_text(encoding="utf-8")
        assert "P001\tcase\tcontrol" in text
        assert "P001\tcontrol\trescue" in text
    finally:
        path.unlink(missing_ok=True)


def test_render_and_export_differential_broken_pairs_tsv() -> None:
    report = build_differential_abundance_report(
        _paired_table(),
        _paired_design(),
        condition_a="case",
        condition_b="control",
        test_type=DifferentialAbundanceTestType.PAIRED_T_TEST,
        paired_policy=PairedDifferentialPolicy(),
    )
    path = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "quant"
        / "differential_broken_pairs.tsv"
    )

    try:
        tsv = render_differential_broken_pairs_tsv(report)
        assert "pair_id" in tsv
        assert "pair-3" in tsv
        export_differential_broken_pairs_tsv(report, path)
        assert "pair-3" in path.read_text(encoding="utf-8")
    finally:
        path.unlink(missing_ok=True)
