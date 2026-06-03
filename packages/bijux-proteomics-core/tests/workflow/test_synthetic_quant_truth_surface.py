# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.workflow.synthetic_quant_truth import (
    SyntheticQuantBatchEffectSpec,
    SyntheticQuantChangedProteinSpec,
    SyntheticQuantContaminationSpec,
    SyntheticQuantMissingnessSpec,
    SyntheticQuantPeptideOutlierSpec,
    SyntheticQuantPeptideObservation,
    SyntheticQuantProteinSpec,
    SyntheticQuantSample,
    SyntheticQuantTruthConfig,
    SyntheticQuantTruthDataset,
    generate_quant_truth_dataset,
    render_synthetic_quant_peptide_observation_tsv,
    render_synthetic_quant_truth_tsv,
)


def _config() -> SyntheticQuantTruthConfig:
    return SyntheticQuantTruthConfig(
        dataset_id="synthetic_quant_truth_fixture",
        reference_condition="control",
        effect_condition="treatment",
        samples=(
            SyntheticQuantSample(
                sample_id="C1",
                condition="control",
                replicate=1,
                batch_id="batch_a",
            ),
            SyntheticQuantSample(
                sample_id="C2",
                condition="control",
                replicate=2,
                batch_id="batch_b",
            ),
            SyntheticQuantSample(
                sample_id="T1",
                condition="treatment",
                replicate=1,
                batch_id="batch_a",
            ),
            SyntheticQuantSample(
                sample_id="T2",
                condition="treatment",
                replicate=2,
                batch_id="batch_b",
            ),
        ),
        changed_proteins=(
            SyntheticQuantChangedProteinSpec(
                protein_id="P_UP",
                peptide_ids=("P_UP_P1", "P_UP_P2"),
                baseline_log2_intensity=10.0,
                effect_log2_fold_change=1.5,
            ),
        ),
        unchanged_proteins=(
            SyntheticQuantProteinSpec(
                protein_id="P_STABLE",
                peptide_ids=("P_STABLE_P1", "P_STABLE_P2"),
                baseline_log2_intensity=9.5,
            ),
            SyntheticQuantProteinSpec(
                protein_id="P_BATCH",
                peptide_ids=("P_BATCH_P1", "P_BATCH_P2"),
                baseline_log2_intensity=8.0,
            ),
            SyntheticQuantProteinSpec(
                protein_id="P_MISS",
                peptide_ids=("P_MISS_P1", "P_MISS_P2"),
                baseline_log2_intensity=7.5,
            ),
            SyntheticQuantProteinSpec(
                protein_id="P_OUT",
                peptide_ids=("P_OUT_P1", "P_OUT_P2"),
                baseline_log2_intensity=8.5,
            ),
        ),
        batch_effects=(
            SyntheticQuantBatchEffectSpec(
                protein_id="P_BATCH",
                batch_id="batch_b",
                log2_shift=0.75,
            ),
        ),
        missingness=(
            SyntheticQuantMissingnessSpec(
                protein_id="P_MISS",
                sample_ids=("T2",),
                reason="left_censored_dropout",
            ),
        ),
        peptide_outliers=(
            SyntheticQuantPeptideOutlierSpec(
                protein_id="P_OUT",
                peptide_id="P_OUT_P2",
                sample_id="T1",
                log2_shift=2.0,
            ),
        ),
        contamination=(
            SyntheticQuantContaminationSpec(
                protein_id="CON__KRT1",
                peptide_ids=("CON__KRT1_P1",),
                baseline_log2_intensity=6.0,
                sample_ids=("C2", "T2"),
                contaminant_class="keratin",
            ),
        ),
    )


def _truth_rows(dataset: SyntheticQuantTruthDataset) -> tuple[dict[str, str], ...]:
    reader = csv.DictReader(
        StringIO(render_synthetic_quant_truth_tsv(dataset)), delimiter="\t"
    )
    if reader.fieldnames is None:
        raise AssertionError("synthetic quant truth TSV is missing a header row")
    return tuple(
        {str(key): str(value or "") for key, value in row.items()} for row in reader
    )


def _observation(
    dataset: SyntheticQuantTruthDataset,
    protein_id: str,
    peptide_id: str,
    sample_id: str,
) -> SyntheticQuantPeptideObservation:
    return next(
        row
        for row in dataset.peptide_observations
        if row.protein_id == protein_id
        and row.peptide_id == peptide_id
        and row.sample_id == sample_id
    )


def test_generate_quant_truth_dataset_matches_injected_truth_signals() -> None:
    dataset = generate_quant_truth_dataset(_config())

    assert dataset.dataset_id == "synthetic_quant_truth_fixture"
    assert {sample.sample_id for sample in dataset.samples} == {"C1", "C2", "T1", "T2"}
    assert {
        (
            row.truth_kind,
            row.protein_id,
            row.peptide_id,
            row.sample_ids,
            row.batch_ids,
        )
        for row in dataset.truth_records
    } == {
        ("changed_protein", "P_UP", None, (), ()),
        ("unchanged_protein", "P_STABLE", None, (), ()),
        ("unchanged_protein", "P_BATCH", None, (), ()),
        ("unchanged_protein", "P_MISS", None, (), ()),
        ("unchanged_protein", "P_OUT", None, (), ()),
        ("batch_effect", "P_BATCH", None, (), ("batch_b",)),
        ("missingness", "P_MISS", None, ("T2",), ()),
        ("peptide_outlier", "P_OUT", "P_OUT_P2", ("T1",), ()),
        ("contamination", "CON__KRT1", None, ("C2", "T2"), ()),
    }

    up_row = _observation(dataset, "P_UP", "P_UP_P1", "T1")
    assert up_row.applied_condition_log2_effect == 1.5
    assert up_row.log2_intensity is not None

    batch_row = _observation(dataset, "P_BATCH", "P_BATCH_P1", "C2")
    assert batch_row.applied_batch_log2_shift == 0.75

    missing_row = _observation(dataset, "P_MISS", "P_MISS_P1", "T2")
    assert missing_row.is_missing is True
    assert missing_row.log2_intensity is None

    outlier_row = _observation(dataset, "P_OUT", "P_OUT_P2", "T1")
    assert outlier_row.applied_outlier_log2_shift == 2.0

    contaminant_samples = {
        row.sample_id
        for row in dataset.peptide_observations
        if row.protein_id == "CON__KRT1"
    }
    assert contaminant_samples == {"C2", "T2"}


def test_generate_quant_truth_dataset_renders_exact_truth_table() -> None:
    dataset = generate_quant_truth_dataset(_config())

    truth_rows = _truth_rows(dataset)
    observation_tsv = render_synthetic_quant_peptide_observation_tsv(dataset)

    assert len(truth_rows) == 9
    assert any(
        row["truth_kind"] == "contamination"
        and row["protein_id"] == "CON__KRT1"
        and row["sample_ids"] == "C2,T2"
        and row["contaminant_class"] == "keratin"
        for row in truth_rows
    )
    assert any(
        row["truth_kind"] == "changed_protein"
        and row["protein_id"] == "P_UP"
        and row["effect_log2_fold_change"] == "1.5000"
        for row in truth_rows
    )
    assert "applied_batch_log2_shift" in observation_tsv
    assert "left_censored_dropout" in render_synthetic_quant_truth_tsv(dataset)
