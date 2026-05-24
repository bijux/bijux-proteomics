# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    ImputationMethod,
    MissingValueKind,
    Ms1FeatureRecord,
    QuantEntityLevel,
    QuantRollupMethod,
    build_differential_abundance_report,
    build_label_free_intensity_table,
    classify_missingness,
    impute_label_free_table,
)
from bijux_proteomics.quantification.censored_differential import (
    render_censored_differential_tsv,
    test_censored_two_group,
)


def test_censored_two_group_differs_from_ordinary_low_intensity_imputation() -> None:
    table = build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="cens-001",
                sample_id="case-1",
                peptide="LOWCASE",
                canonical_peptide="LOWCASE",
                intensity=18.0,
                protein_refs=("P_LOW_CASE",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-002",
                sample_id="case-2",
                peptide="LOWCASE",
                canonical_peptide="LOWCASE",
                intensity=20.0,
                protein_refs=("P_LOW_CASE",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-003",
                sample_id="ctrl-1",
                peptide="LOWCASE",
                canonical_peptide="LOWCASE",
                intensity=None,
                protein_refs=("P_LOW_CASE",),
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-004",
                sample_id="ctrl-2",
                peptide="LOWCASE",
                canonical_peptide="LOWCASE",
                intensity=None,
                protein_refs=("P_LOW_CASE",),
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-005",
                sample_id="case-1",
                peptide="STABLE",
                canonical_peptide="STABLE",
                intensity=400.0,
                protein_refs=("P_STABLE",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-006",
                sample_id="case-2",
                peptide="STABLE",
                canonical_peptide="STABLE",
                intensity=420.0,
                protein_refs=("P_STABLE",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-007",
                sample_id="ctrl-1",
                peptide="STABLE",
                canonical_peptide="STABLE",
                intensity=390.0,
                protein_refs=("P_STABLE",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-008",
                sample_id="ctrl-2",
                peptide="STABLE",
                canonical_peptide="STABLE",
                intensity=410.0,
                protein_refs=("P_STABLE",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-009",
                sample_id="case-1",
                peptide="LOWANCHOR",
                canonical_peptide="LOWANCHOR",
                intensity=6.0,
                protein_refs=("P_LOW_ANCHOR",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-010",
                sample_id="case-2",
                peptide="LOWANCHOR",
                canonical_peptide="LOWANCHOR",
                intensity=None,
                protein_refs=("P_LOW_ANCHOR",),
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-011",
                sample_id="ctrl-1",
                peptide="LOWANCHOR",
                canonical_peptide="LOWANCHOR",
                intensity=5.0,
                protein_refs=("P_LOW_ANCHOR",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="cens-012",
                sample_id="ctrl-2",
                peptide="LOWANCHOR",
                canonical_peptide="LOWANCHOR",
                intensity=None,
                protein_refs=("P_LOW_ANCHOR",),
                missing_value_kind=MissingValueKind.NOT_OBSERVED,
            ),
        ),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    design = _design()
    missingness = classify_missingness(table, design)

    censored = test_censored_two_group(
        table,
        missingness,
        design,
        condition_a="control",
        condition_b="case",
    )
    ordinary = build_differential_abundance_report(
        impute_label_free_table(
            table,
            method=ImputationMethod.LOW_INTENSITY,
        ),
        design,
        condition_a="control",
        condition_b="case",
    )
    rendered = render_censored_differential_tsv(censored)

    censored_lookup = {entry.entity_id: entry for entry in censored.entries}
    ordinary_lookup = {entry.entity_id: entry for entry in ordinary.entries}

    assert censored_lookup["P_LOW_CASE"].censoring_status.value in {
        "condition_specific_absence",
        "left_censored_condition_a",
    }
    assert (
        censored_lookup["P_LOW_CASE"].log2fc_estimate
        != round(ordinary_lookup["P_LOW_CASE"].log2_fold_change, 6)
    )
    assert (
        censored_lookup["P_LOW_CASE"].censored_p_value
        != round(ordinary_lookup["P_LOW_CASE"].adjusted_p_value or 1.0, 6)
    )
    assert censored_lookup["P_STABLE"].censoring_status.value == "uncensored"
    assert "entity_id\tlog2fc_estimate\tcensored_p_value\tq_value\tcensoring_status" in rendered


def test_censored_two_group_requires_two_conditions_without_explicit_names() -> None:
    table = build_label_free_intensity_table(
        (
            Ms1FeatureRecord(
                feature_id="three-001",
                sample_id="s1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="three-002",
                sample_id="s2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=120.0,
                protein_refs=("P001",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
            Ms1FeatureRecord(
                feature_id="three-003",
                sample_id="s3",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=140.0,
                protein_refs=("P001",),
                missing_value_kind=MissingValueKind.OBSERVED,
            ),
        ),
        entity_level=QuantEntityLevel.PROTEIN,
        aggregation_method=QuantRollupMethod.SUM,
    )
    design = (
        ExperimentalDesignEntry(
            sample_id="s1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="s1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="s2",
            condition="case",
            replicate=1,
            fraction=1,
            spectra_file="s2.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="s3",
            condition="rescue",
            replicate=1,
            fraction=1,
            spectra_file="s3.mzml",
        ),
    )
    missingness = classify_missingness(table, design)

    with pytest.raises(
        ValueError,
        match="requires exactly two conditions or explicit condition names",
    ):
        test_censored_two_group(table, missingness, design)


def _design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
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
    )
