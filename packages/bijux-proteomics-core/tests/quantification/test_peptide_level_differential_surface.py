# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    Ms1FeatureRecord,
    build_peptide_intensity_matrix_from_features,
)
from bijux_proteomics.quantification.peptide_level_differential import (
    render_peptide_level_differential_tsv,
    test_protein_effect_from_peptides,
)


def test_protein_effect_from_peptides_downgrades_conflicted_peptide_behavior() -> None:
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        (
            Ms1FeatureRecord(
                feature_id="clean-001",
                sample_id="control-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="clean-002",
                sample_id="control-2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=110.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="clean-003",
                sample_id="case-1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="clean-004",
                sample_id="case-2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=440.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="clean-005",
                sample_id="control-1",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=400.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="clean-006",
                sample_id="control-2",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=440.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="clean-007",
                sample_id="case-1",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=1600.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="clean-008",
                sample_id="case-2",
                peptide="PEPG",
                canonical_peptide="PEPG",
                intensity=1760.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="conflict-001",
                sample_id="control-1",
                peptide="QLTK",
                canonical_peptide="QLTK",
                intensity=100.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="conflict-002",
                sample_id="control-2",
                peptide="QLTK",
                canonical_peptide="QLTK",
                intensity=110.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="conflict-003",
                sample_id="case-1",
                peptide="QLTK",
                canonical_peptide="QLTK",
                intensity=400.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="conflict-004",
                sample_id="case-2",
                peptide="QLTK",
                canonical_peptide="QLTK",
                intensity=440.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="conflict-005",
                sample_id="control-1",
                peptide="NVKQ",
                canonical_peptide="NVKQ",
                intensity=400.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="conflict-006",
                sample_id="control-2",
                peptide="NVKQ",
                canonical_peptide="NVKQ",
                intensity=440.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="conflict-007",
                sample_id="case-1",
                peptide="NVKQ",
                canonical_peptide="NVKQ",
                intensity=280.0,
                protein_refs=("P002",),
            ),
            Ms1FeatureRecord(
                feature_id="conflict-008",
                sample_id="case-2",
                peptide="NVKQ",
                canonical_peptide="NVKQ",
                intensity=308.0,
                protein_refs=("P002",),
            ),
        )
    )
    design = _two_condition_design()

    report = test_protein_effect_from_peptides(
        peptide_matrix,
        design,
        condition_a="control",
        condition_b="case",
    )
    rendered = render_peptide_level_differential_tsv(report)
    entry_lookup = {entry.protein_id: entry for entry in report.entries}

    assert [entry.protein_id for entry in report.entries] == ["P001", "P002"]
    assert entry_lookup["P001"].peptide_count == 2
    assert entry_lookup["P002"].peptide_count == 2
    assert entry_lookup["P001"].peptide_disagreement_score < 0.05
    assert entry_lookup["P002"].peptide_disagreement_score > 0.5
    assert entry_lookup["P001"].p_value < 0.05
    assert entry_lookup["P002"].p_value > entry_lookup["P001"].p_value
    assert entry_lookup["P002"].q_value > entry_lookup["P001"].q_value
    assert entry_lookup["P001"].log2fc > 1.9
    assert 0.4 < entry_lookup["P002"].log2fc < 1.0
    assert (
        "protein_id\tlog2fc\tp_value\tq_value\tpeptide_count\tpeptide_disagreement_score"
        in rendered
    )


def test_protein_effect_from_peptides_requires_two_conditions_without_explicit_names() -> (
    None
):
    peptide_matrix = build_peptide_intensity_matrix_from_features(
        (
            Ms1FeatureRecord(
                feature_id="multi-001",
                sample_id="s1",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=100.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="multi-002",
                sample_id="s2",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=200.0,
                protein_refs=("P001",),
            ),
            Ms1FeatureRecord(
                feature_id="multi-003",
                sample_id="s3",
                peptide="PEPA",
                canonical_peptide="PEPA",
                intensity=300.0,
                protein_refs=("P001",),
            ),
        )
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

    with pytest.raises(
        ValueError,
        match="requires exactly two conditions or explicit condition names",
    ):
        test_protein_effect_from_peptides(peptide_matrix, design)


def _two_condition_design() -> tuple[ExperimentalDesignEntry, ...]:
    return (
        ExperimentalDesignEntry(
            sample_id="control-1",
            condition="control",
            replicate=1,
            fraction=1,
            spectra_file="control-1.mzml",
        ),
        ExperimentalDesignEntry(
            sample_id="control-2",
            condition="control",
            replicate=2,
            fraction=1,
            spectra_file="control-2.mzml",
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
    )
