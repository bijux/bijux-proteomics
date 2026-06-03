# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import csv
from io import StringIO

from bijux_proteomics.workflow.public_benchmark_descriptors import (
    load_public_benchmark_descriptor,
    public_benchmark_root,
)
from bijux_proteomics.workflow.public_benchmark_subset import (
    PublicBenchmarkSubsetReport,
    build_public_benchmark_subset,
)


def _subset_input_rows(
    report: PublicBenchmarkSubsetReport, source_id: str
) -> tuple[dict[str, str], ...]:
    subset_input = next(
        item for item in report.subset_inputs if item.source_id == source_id
    )
    reader = csv.DictReader(StringIO(subset_input.content), delimiter="\t")
    if reader.fieldnames is None:
        raise AssertionError(f"subset input {source_id!r} is missing a header row")
    return tuple(
        {str(key or "").strip(): str(value or "").strip() for key, value in row.items()}
        for row in reader
    )


def test_public_benchmark_subset_preserves_conditions_signal_and_integrity_rows() -> (
    None
):
    descriptor = load_public_benchmark_descriptor(
        public_benchmark_root() / "maxquant_lfq_benchmark_dataset" / "dataset.yml"
    )

    report = build_public_benchmark_subset(
        descriptor,
        max_samples=4,
        max_entities=5,
    )

    assert report.dataset_id == "maxquant_lfq_benchmark_dataset_subset"
    assert report.selected_sample_ids == ("C1", "T1", "C2", "T2")
    assert {group.group_id: group.sample_ids for group in report.sample_groups} == {
        "control": ("C1", "C2"),
        "treatment": ("T1", "T2"),
    }
    assert "maxquant_sig_a_up" in report.preserved_signal_ids
    assert report.preserved_decoy_entity_ids == ("REV__P77777",)
    assert report.preserved_contaminant_entity_ids == ("CON__KRT1",)

    evidence_rows = _subset_input_rows(report, "maxquant_evidence")
    assert {row["Experiment"] for row in evidence_rows} == {"C1", "C2", "T1", "T2"}
    assert any(row["Proteins"] == "P04637" for row in evidence_rows)
    assert any(
        row["Proteins"] == "REV__P77777" and row["Reverse"] == "+"
        for row in evidence_rows
    )

    protein_group_rows = _subset_input_rows(report, "maxquant_protein_groups")
    assert any(row["Protein IDs"] == "P04637" for row in protein_group_rows)
    assert any(row["Protein IDs"] == "REV__P77777" for row in protein_group_rows)
    assert any(row["Protein IDs"] == "CON__KRT1" for row in protein_group_rows)
    assert set(protein_group_rows[0]) == {
        "Protein IDs",
        "Majority protein IDs",
        "Gene names",
        "Fasta headers",
        "Peptides",
        "Razor + unique peptides",
        "Sequence coverage [%]",
        "MS/MS count",
        "Reverse",
        "Potential contaminant",
        "Only identified by site",
        "LFQ intensity C1",
        "LFQ intensity C2",
        "LFQ intensity T1",
        "LFQ intensity T2",
    }

    expected_ranges = {
        item.metric_id: (item.min_expected, item.max_expected)
        for item in report.expected_count_ranges
    }
    assert expected_ranges["lfq_experiment_count"] == (4, 4)
    assert expected_ranges["significant_protein_count"] == (2, 3)


def test_public_benchmark_subset_preserves_ptm_signal_and_decoy_support() -> None:
    descriptor = load_public_benchmark_descriptor(
        public_benchmark_root() / "ptm_localization_review_package" / "dataset.yml"
    )

    report = build_public_benchmark_subset(
        descriptor,
        max_samples=2,
        max_entities=2,
    )

    assert report.selected_sample_ids == ("C1", "T1")
    assert "ptm_site_p11111_s5_up" in report.preserved_signal_ids
    assert report.preserved_decoy_entity_ids == ("Q9DEC1",)

    localization_rows = _subset_input_rows(report, "ptm_localization_results")
    assert {row["sample_id"] for row in localization_rows} == {"C1", "T1"}
    assert any(row["proteins"] == "P11111" for row in localization_rows)
    assert any(
        row["decoy_label"] == "decoy" and row["proteins"] == "Q9DEC1"
        for row in localization_rows
    )

    annotation_rows = _subset_input_rows(report, "ptm_site_annotations")
    assert any(
        row["protein_ref"] == "P11111"
        and row["residue"] == "S"
        and row["position"] == "5"
        and row["modification_name"] == "Phospho"
        for row in annotation_rows
    )
