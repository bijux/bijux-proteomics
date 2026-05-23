# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    BrokenPairDisposition,
    DifferentialAbundanceTestType,
    MissingValueKind,
    Ms1FeatureRecord,
    PairedDifferentialPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    build_quant_design_matrix_report,
)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="c1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="c1.mzml",
            batch="batch-1",
        ),
        ExperimentalDesignEntry(
            sample_id="c2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="c2.mzml",
            batch="batch-2",
        ),
        ExperimentalDesignEntry(
            sample_id="t1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="t1.mzml",
            batch="batch-1",
        ),
        ExperimentalDesignEntry(
            sample_id="t2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="t2.mzml",
            batch="batch-2",
        ),
    )


def _table():
    records = (
        Ms1FeatureRecord(
            feature_id="da-001",
            sample_id="c1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=100.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-002",
            sample_id="c2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=105.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-003",
            sample_id="t1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=220.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-004",
            sample_id="t2",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=230.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-005",
            sample_id="c1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=0.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.ZERO,
        ),
        Ms1FeatureRecord(
            feature_id="da-006",
            sample_id="c2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=None,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.NOT_OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-007",
            sample_id="t1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=60.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="da-008",
            sample_id="t2",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=None,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.FILTERED,
        ),
    )
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def _paired_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="pc1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="pc1.mzml",
            pair_id="pair-1",
        ),
        ExperimentalDesignEntry(
            sample_id="pt1",
            condition="treatment",
            replicate=1,
            fraction=1,
            spectra_file="pt1.mzml",
            pair_id="pair-1",
        ),
        ExperimentalDesignEntry(
            sample_id="pc2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="pc2.mzml",
            pair_id="pair-2",
        ),
        ExperimentalDesignEntry(
            sample_id="pt2",
            condition="treatment",
            replicate=2,
            fraction=1,
            spectra_file="pt2.mzml",
            pair_id="pair-2",
        ),
        ExperimentalDesignEntry(
            sample_id="pc3",
            condition="control",
            replicate=3,
            fraction=1,
            spectra_file="pc3.mzml",
            pair_id="pair-3",
        ),
    )


def _paired_table():
    records = (
        Ms1FeatureRecord(
            feature_id="paired-001",
            sample_id="pc1",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=100.0,
            protein_refs=("PPAIRED",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="paired-002",
            sample_id="pt1",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=180.0,
            protein_refs=("PPAIRED",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="paired-003",
            sample_id="pc2",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=120.0,
            protein_refs=("PPAIRED",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="paired-004",
            sample_id="pt2",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=240.0,
            protein_refs=("PPAIRED",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="paired-005",
            sample_id="pc3",
            peptide="PEPX",
            canonical_peptide="PEPX",
            intensity=90.0,
            protein_refs=("PPAIRED",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )
    return build_label_free_intensity_table(
        records,
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )


def test_differential_abundance_owner_returns_bh_complete_missingness_aware_rows() -> (
    None
):
    report = build_differential_abundance_report(
        _table(),
        _design(),
        condition_a="control",
        condition_b="treatment",
    )

    assert (
        report.assumption_report.test_type
        is DifferentialAbundanceTestType.WELCH_T_TEST
    )
    assert (
        report.assumption_report.multiple_testing_scope
        == "benjamini_hochberg_report_wide_entities"
    )
    assert all(entry.adjusted_p_value is not None for entry in report.entries)

    p1 = next(entry for entry in report.entries if entry.entity_id == "P1")
    p2 = next(entry for entry in report.entries if entry.entity_id == "P2")

    assert p1.log2_fold_change > 0.0
    assert p1.effect_size_cohens_d is not None
    assert p2.zero_values_a == 1
    assert p2.not_observed_values_a == 1
    assert p2.filtered_values_b == 1


def test_differential_abundance_owner_supports_linear_model_contrasts() -> None:
    design = _design()
    design_matrix = build_quant_design_matrix_report(design, batch_field="batch")

    report = build_differential_abundance_report(
        _table(),
        design,
        condition_a="control",
        condition_b="treatment",
        test_type=DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST,
        design_matrix=design_matrix,
    )

    p1 = next(entry for entry in report.entries if entry.entity_id == "P1")

    assert (
        report.assumption_report.test_type
        is DifferentialAbundanceTestType.LINEAR_MODEL_CONTRAST
    )
    assert report.contrast_name == "control_vs_treatment"
    assert report.assumption_report.contrast_name == "control_vs_treatment"
    assert p1.log2_fold_change > 0.0
    assert p1.standard_error is not None
    assert p1.adjusted_p_value is not None


def test_differential_abundance_owner_supports_paired_testing_and_reports_broken_pairs() -> None:
    report = build_differential_abundance_report(
        _paired_table(),
        _paired_design(),
        condition_a="control",
        condition_b="treatment",
        test_type=DifferentialAbundanceTestType.PAIRED_T_TEST,
        paired_policy=PairedDifferentialPolicy(),
    )

    entry = report.entries[0]

    assert (
        report.assumption_report.test_type
        is DifferentialAbundanceTestType.PAIRED_T_TEST
    )
    assert report.assumption_report.paired_policy is not None
    assert entry.entity_id == "PPAIRED"
    assert entry.complete_pair_count == 2
    assert entry.observations_a == 3
    assert entry.observations_b == 2
    assert entry.log2_fold_change > 0.0
    assert entry.effect_size_cohens_d is not None
    assert len(report.broken_pairs) == 1
    assert report.broken_pairs[0].reason_code == "unmatched_pair"
    assert report.broken_pairs[0].pair_id == "pair-3"


def test_differential_abundance_owner_can_block_broken_pairs_under_policy() -> None:
    try:
        build_differential_abundance_report(
            _paired_table(),
            _paired_design(),
            condition_a="control",
            condition_b="treatment",
            test_type=DifferentialAbundanceTestType.PAIRED_T_TEST,
            paired_policy=PairedDifferentialPolicy(
                broken_pair_disposition=BrokenPairDisposition.BLOCK
            ),
        )
    except ValueError as exc:
        assert "blocked" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("paired differential testing should block broken pairs")
